"""Autenticação pela API (issue #31): login por token (UC01), cadastro (UC02) e recuperação de senha (UC03).

Fica no app `pessoas` porque usa só `pessoas.cadastros`: a dependência continua indo num sentido só.
As regras (LGPD, menor de idade, e-mail único) NÃO são repetidas aqui: o cadastro delega para
cadastrar_atleta e cadastrar_responsavel.
"""
import logging

from django.conf import settings
from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.db.models import Q
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .cadastros import VERSAO_TERMOS_ATUAL, cadastrar_atleta, cadastrar_responsavel

log = logging.getLogger(__name__)

MENSAGEM_RECUPERACAO = "Se o e-mail estiver cadastrado, enviaremos um link para redefinir a senha."
LINK_INVALIDO = "Link inválido ou expirado. Peça a recuperação de senha de novo."


def _erro_da_api(erro):
    return serializers.ValidationError(erro.message_dict if hasattr(erro, "error_dict") else erro.messages)


def _validar_senha(senha, usuario=None):
    try:
        password_validation.validate_password(senha, usuario)
    except DjangoValidationError as e:
        raise serializers.ValidationError(list(e.messages))
    return senha


# ---------------------------------------------------------------- UC01: login por token

class TokenPorEmailSerializer(TokenObtainPairSerializer):
    """Aceita `email` (ou `username`) sem diferenciar maiúsculas de minúsculas.

    O cadastro compara o e-mail com username__iexact; o login precisa fazer o mesmo, senão quem se
    cadastrou como Maria@x.com não entra digitando maria@x.com. Senha errada e conta inativa dão a
    mesma resposta (401), sem dizer qual falhou (RNF05).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"] = serializers.CharField(write_only=True, required=False)
        self.fields[self.username_field].required = False

    def validate(self, attrs):
        login = (attrs.pop("email", None) or attrs.get(self.username_field) or "").strip()
        if not login:
            raise serializers.ValidationError({"email": "Informe o e-mail."})
        usuario = User.objects.filter(username__iexact=login).first()
        attrs[self.username_field] = usuario.username if usuario else login
        return super().validate(attrs)


class TokenPorEmailView(TokenObtainPairView):
    serializer_class = TokenPorEmailSerializer


# ---------------------------------------------------------------- UC02: cadastro

class CadastroSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=["atleta", "responsavel"])
    nome = serializers.CharField()
    sobrenome = serializers.CharField(required=False, allow_blank=True, default="")
    email = serializers.EmailField()
    senha = serializers.CharField(write_only=True)
    aceitou_termos = serializers.BooleanField()
    versao_termos = serializers.CharField(required=False, default=VERSAO_TERMOS_ATUAL)
    data_nascimento = serializers.DateField(required=False, help_text="Obrigatória para atleta.")
    cpf = serializers.CharField(required=False, allow_blank=True, default="")
    telefone = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_senha(self, valor):
        return _validar_senha(valor)

    def validate(self, attrs):
        if attrs["tipo"] == "atleta" and not attrs.get("data_nascimento"):
            raise serializers.ValidationError({"data_nascimento": "Informe a data de nascimento do atleta."})
        return attrs


class CadastroRespostaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    tipo = serializers.CharField()
    nome_completo = serializers.CharField()
    email = serializers.EmailField()


class CadastroView(APIView):
    # Autocadastro de quem ainda não tem conta. Cadastrar um dependente continua em POST /api/atletas/
    # (responsável logado). authentication_classes vazio: um token vencido não pode barrar um visitante.
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(request=CadastroSerializer, responses={201: CadastroRespostaSerializer}, summary="Cadastro de atleta ou responsável (UC02)")
    def post(self, request):
        dados = CadastroSerializer(data=request.data)
        dados.is_valid(raise_exception=True)
        d = dados.validated_data
        comuns = dict(email=d["email"], nome=d["nome"], sobrenome=d["sobrenome"], senha=d["senha"],
                      aceitou_termos=d["aceitou_termos"], versao_termos=d["versao_termos"])
        try:
            if d["tipo"] == "atleta":
                pessoa = cadastrar_atleta(data_nascimento=d["data_nascimento"], **comuns)
            else:
                pessoa = cadastrar_responsavel(cpf=d["cpf"], telefone=d["telefone"], **comuns)
        except DjangoValidationError as e:
            raise _erro_da_api(e)
        corpo = {"id": pessoa.pk, "tipo": d["tipo"], "nome_completo": pessoa.nome, "email": pessoa.usuario.email}
        return Response(corpo, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------- UC03: recuperar senha

class RecuperarSenhaThrottle(AnonRateThrottle):
    scope = "recuperar_senha"  # a taxa fica em REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]


class SolicitarRecuperacaoSerializer(serializers.Serializer):
    email = serializers.EmailField()


class RedefinirSenhaSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    senha = serializers.CharField(write_only=True)


class MensagemSerializer(serializers.Serializer):
    detail = serializers.CharField()


class SolicitarRecuperacaoView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [RecuperarSenhaThrottle]

    @extend_schema(request=SolicitarRecuperacaoSerializer, responses={200: MensagemSerializer},
                   summary="Envia o link de redefinição de senha por e-mail (UC03)")
    def post(self, request):
        dados = SolicitarRecuperacaoSerializer(data=request.data)
        dados.is_valid(raise_exception=True)
        email = dados.validated_data["email"]
        # Busca à mão (e não PasswordResetForm): o form do Django ignora quem tem senha inutilizável,
        # como os responsáveis criados pela migração 0003.
        usuario = User.objects.filter(Q(username__iexact=email) | Q(email__iexact=email), is_active=True).first()
        if usuario:
            self._enviar(usuario)
        # mesma resposta exista o e-mail ou não (UC03 A1, RNF05)
        return Response({"detail": MENSAGEM_RECUPERACAO})

    @staticmethod
    def _enviar(usuario):
        uid = urlsafe_base64_encode(force_bytes(usuario.pk))
        token = default_token_generator.make_token(usuario)
        link = f"{settings.URL_REDEFINICAO_SENHA}?uid={uid}&token={token}"
        try:
            send_mail("PKZ LAB: redefinição de senha",
                      f"Olá, {usuario.first_name or usuario.username}.\n\n"
                      f"Para criar uma nova senha, acesse:\n{link}\n\n"
                      "O link vale por 1 hora. Se não foi você quem pediu, ignore este e-mail.",
                      settings.DEFAULT_FROM_EMAIL, [usuario.email or usuario.username])
        except Exception:  # falha de e-mail não pode revelar nada a quem pediu
            log.exception("Falha ao enviar e-mail de recuperação para o usuário %s", usuario.pk)


class RedefinirSenhaView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [RecuperarSenhaThrottle]

    @extend_schema(request=RedefinirSenhaSerializer, responses={200: MensagemSerializer},
                   summary="Define a nova senha com o uid e o token recebidos por e-mail (UC03)")
    def post(self, request):
        dados = RedefinirSenhaSerializer(data=request.data)
        dados.is_valid(raise_exception=True)
        d = dados.validated_data
        try:
            usuario = User.objects.get(pk=force_str(urlsafe_base64_decode(d["uid"])), is_active=True)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            usuario = None
        if usuario is None or not default_token_generator.check_token(usuario, d["token"]):
            raise serializers.ValidationError({"token": LINK_INVALIDO})
        _validar_senha(d["senha"], usuario)
        usuario.set_password(d["senha"])
        usuario.save(update_fields=["password"])  # trocar a senha já invalida o token (ele usa o hash)
        return Response({"detail": "Senha alterada. Entre com a nova senha."})