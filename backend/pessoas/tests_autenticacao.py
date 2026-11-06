import re

from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from pkzlab.testes_comuns import atleta as criar_atleta

from .models import Atleta, ConsentimentoLGPD, Responsavel

SENHA_FORTE = "Sup3r-senha-9271"


class Base(TestCase):
    def setUp(self):
        cache.clear()  # o throttle guarda a contagem no cache
        self.api = APIClient()


class LoginPorToken(Base):
    def setUp(self):
        super().setUp()
        self.joao = criar_atleta("joao", "João")  # login joao@x.com, senha senha12345

    def entrar(self, **dados):
        return self.api.post("/api/token/", dados, format="json")

    def test_login_devolve_access_e_refresh(self):
        r = self.entrar(email="joao@x.com", password="senha12345")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertIn("access", r.data)
        self.assertIn("refresh", r.data)

    def test_email_em_outra_caixa_entra(self):
        self.assertEqual(self.entrar(email="JOAO@X.com", password="senha12345").status_code, 200)

    def test_campo_username_tambem_funciona(self):
        self.assertEqual(self.entrar(username="joao@x.com", password="senha12345").status_code, 200)

    def test_senha_errada_e_conta_inativa_dao_a_mesma_resposta(self):
        errada = self.entrar(email="joao@x.com", password="outra")
        self.joao.usuario.is_active = False
        self.joao.usuario.save()
        inativa = self.entrar(email="joao@x.com", password="senha12345")
        self.assertEqual(errada.status_code, 401)
        self.assertEqual(inativa.status_code, 401)
        self.assertEqual(errada.data["detail"], inativa.data["detail"])

    def test_sem_email_e_400(self):
        self.assertEqual(self.entrar(password="senha12345").status_code, 400)

    def test_refresh_gera_novo_access(self):
        refresh = self.entrar(email="joao@x.com", password="senha12345").data["refresh"]
        r = self.api.post("/api/token/refresh/", {"refresh": refresh}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertIn("access", r.data)

    def test_token_abre_a_api(self):
        access = self.entrar(email="joao@x.com", password="senha12345").data["access"]
        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        r = self.api.get("/api/atletas/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual({a["id"] for a in r.data["results"]}, {self.joao.pk})

    def test_token_invalido_nao_abre_a_api(self):
        self.api.credentials(HTTP_AUTHORIZATION="Bearer lixo")
        self.assertEqual(self.api.get("/api/atletas/").status_code, 401)

    def test_token_vencido_nao_barra_o_cadastro(self):
        self.api.credentials(HTTP_AUTHORIZATION="Bearer lixo")
        r = self.api.post("/api/cadastro/", self.dados_atleta(), format="json")
        self.assertEqual(r.status_code, 201, r.data)

    @staticmethod
    def dados_atleta():
        return {"tipo": "atleta", "nome": "Bia", "email": "bia@x.com", "senha": SENHA_FORTE,
                "data_nascimento": "2001-08-15", "aceitou_termos": True}


class Cadastro(Base):
    def cadastrar(self, **mudancas):
        dados = {"tipo": "atleta", "nome": "Bia", "sobrenome": "Costa", "email": "bia@x.com",
                 "senha": SENHA_FORTE, "data_nascimento": "2001-08-15", "aceitou_termos": True}
        dados.update(mudancas)
        return self.api.post("/api/cadastro/", dados, format="json")

    def test_atleta_maior_de_idade(self):
        r = self.cadastrar()
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["tipo"], "atleta")
        self.assertNotIn("senha", r.data)
        self.assertTrue(Atleta.objects.filter(usuario__username="bia@x.com").exists())
        self.assertTrue(ConsentimentoLGPD.objects.filter(usuario__username="bia@x.com").exists())

    def test_responsavel(self):
        r = self.cadastrar(tipo="responsavel", email="maria@x.com", telefone="21999999999")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertTrue(Responsavel.objects.filter(usuario__username="maria@x.com").exists())

    def test_recem_cadastrado_ja_entra(self):
        self.cadastrar()
        r = self.api.post("/api/token/", {"email": "bia@x.com", "password": SENHA_FORTE}, format="json")
        self.assertEqual(r.status_code, 200)

    def test_menor_sem_responsavel_e_400_e_nao_sobra_login(self):
        r = self.cadastrar(data_nascimento="2015-04-10")
        self.assertEqual(r.status_code, 400)
        self.assertIn("responsavel", r.data)
        self.assertFalse(User.objects.filter(username="bia@x.com").exists())

    def test_sem_aceite_lgpd(self):
        r = self.cadastrar(aceitou_termos=False)
        self.assertEqual(r.status_code, 400)
        self.assertIn("aceitou_termos", r.data)
        self.assertFalse(User.objects.exists())

    def test_email_repetido_em_outra_caixa(self):
        self.cadastrar()
        r = self.cadastrar(email="BIA@x.com")
        self.assertEqual(r.status_code, 400)
        self.assertIn("email", r.data)

    def test_atleta_exige_data_de_nascimento(self):
        r = self.cadastrar(data_nascimento=None)
        self.assertEqual(r.status_code, 400)
        self.assertIn("data_nascimento", r.data)

    def test_tipo_invalido(self):
        self.assertEqual(self.cadastrar(tipo="profissional").status_code, 400)

    def test_senha_fraca(self):
        r = self.cadastrar(senha="123")
        self.assertEqual(r.status_code, 400)
        self.assertIn("senha", r.data)


class RecuperarSenha(Base):
    def setUp(self):
        super().setUp()
        self.joao = criar_atleta("joao", "João")

    def pedir(self, email="joao@x.com"):
        return self.api.post("/api/senha/recuperar/", {"email": email}, format="json")

    def link_do_email(self):
        corpo = mail.outbox[-1].body
        achou = re.search(r"uid=([^&\s]+)&token=(\S+)", corpo)
        return achou.group(1), achou.group(2)

    def redefinir(self, uid, token, senha=SENHA_FORTE):
        return self.api.post("/api/senha/redefinir/", {"uid": uid, "token": token, "senha": senha}, format="json")

    def test_email_existente_recebe_o_link(self):
        r = self.pedir()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["joao@x.com"])

    def test_email_inexistente_tem_a_mesma_resposta_e_nao_envia(self):
        existente, inexistente = self.pedir(), self.pedir("ninguem@x.com")
        self.assertEqual(inexistente.status_code, 200)
        self.assertEqual(existente.data, inexistente.data)
        self.assertEqual(len(mail.outbox), 1)  # só o do e-mail que existe

    def test_conta_inativa_nao_recebe(self):
        self.joao.usuario.is_active = False
        self.joao.usuario.save()
        self.assertEqual(self.pedir().status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_fluxo_completo_e_login_com_a_senha_nova(self):
        self.pedir()
        uid, token = self.link_do_email()
        self.assertEqual(self.redefinir(uid, token).status_code, 200)
        r = self.api.post("/api/token/", {"email": "joao@x.com", "password": SENHA_FORTE}, format="json")
        self.assertEqual(r.status_code, 200)
        r = self.api.post("/api/token/", {"email": "joao@x.com", "password": "senha12345"}, format="json")
        self.assertEqual(r.status_code, 401)

    def test_link_so_vale_uma_vez(self):
        self.pedir()
        uid, token = self.link_do_email()
        self.assertEqual(self.redefinir(uid, token).status_code, 200)
        self.assertEqual(self.redefinir(uid, token, "Outra-senha-5538").status_code, 400)

    def test_token_invalido(self):
        self.pedir()
        uid, _ = self.link_do_email()
        r = self.redefinir(uid, "token-falso")
        self.assertEqual(r.status_code, 400)
        self.assertIn("token", r.data)

    def test_uid_invalido(self):
        self.assertEqual(self.redefinir("@@@", "x").status_code, 400)

    def test_senha_fraca_e_recusada_e_a_antiga_continua(self):
        self.pedir()
        uid, token = self.link_do_email()
        self.assertEqual(self.redefinir(uid, token, "123").status_code, 400)
        self.joao.usuario.refresh_from_db()
        self.assertTrue(self.joao.usuario.check_password("senha12345"))

    def test_responsavel_sem_senha_tambem_consegue_recuperar(self):
        # os responsáveis criados pela migração 0003 têm senha inutilizável ("!")
        u = User.objects.create(username="maria@x.com", email="maria@x.com", password="!")
        Responsavel.objects.create(usuario=u)
        self.pedir("maria@x.com")
        self.assertEqual(len(mail.outbox), 1)
        uid, token = self.link_do_email()
        self.assertEqual(self.redefinir(uid, token).status_code, 200)
        u.refresh_from_db()
        self.assertTrue(u.check_password(SENHA_FORTE))

    def test_limite_de_pedidos(self):
        from rest_framework.throttling import AnonRateThrottle
        from .autenticacao import RecuperarSenhaThrottle
        RecuperarSenhaThrottle.THROTTLE_RATES = {**AnonRateThrottle.THROTTLE_RATES, "recuperar_senha": "2/hour"}
        try:
            codigos = [self.pedir().status_code for _ in range(3)]
        finally:
            RecuperarSenhaThrottle.THROTTLE_RATES = AnonRateThrottle.THROTTLE_RATES
        self.assertEqual(codigos, [200, 200, 429])