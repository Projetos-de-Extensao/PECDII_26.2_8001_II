"""Correções da revisão do back-end: política de senha, grupos de papéis e configuração do servidor."""
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from pkzlab.testes_comuns import recarregar, usuario_com_papel

from .cadastros import cadastrar_funcionario
from .permissoes import tem_permissao


class SenhaEmTodoCadastro(TestCase):
    def test_cadastro_de_atleta_recusa_senha_fraca(self):
        r = APIClient().post("/api/atletas/", {"nome": "X", "email": "x@x.com", "senha": "1",
                                               "data_nascimento": "2000-01-01", "aceitou_termos": True})
        self.assertEqual(r.status_code, 400)
        self.assertIn("senha", r.data)

    def test_cadastro_de_responsavel_recusa_senha_fraca(self):
        r = APIClient().post("/api/responsaveis/", {"nome": "X", "email": "x@x.com", "senha": "12345678",
                                                    "aceitou_termos": True})
        self.assertEqual(r.status_code, 400)
        self.assertIn("senha", r.data)

    def test_senha_parecida_com_o_email_e_recusada(self):
        r = APIClient().post("/api/atletas/", {"nome": "Mariana", "email": "mariana.souza@x.com",
                                               "senha": "mariana.souza", "data_nascimento": "2000-01-01",
                                               "aceitou_termos": True})
        self.assertEqual(r.status_code, 400)
        self.assertIn("senha", r.data)

    def test_senha_boa_continua_entrando(self):
        r = APIClient().post("/api/atletas/", {"nome": "X", "email": "x@x.com", "senha": "trilha-azul-42",
                                               "data_nascimento": "2000-01-01", "aceitou_termos": True})
        self.assertEqual(r.status_code, 201, r.data)

    def test_funcionario_tambem_segue_a_politica(self):
        with self.assertRaises(ValidationError) as erro:
            cadastrar_funcionario(email="f@ct.com", nome="F", sobrenome="", senha_provisoria="123",
                                  matricula="X1", data_admissao=date(2026, 1, 5))
        self.assertIn("senha_provisoria", erro.exception.message_dict)


class GrupoApagadoNoAdmin(TestCase):
    def test_volta_com_as_permissoes_do_papel(self):
        Group.objects.filter(name="Recepção").delete()
        rita = recarregar(usuario_com_papel("rita", "recepcao"))
        self.assertTrue(tem_permissao(rita, "gerenciar_agenda"))
        self.assertTrue(tem_permissao(rita, "gerenciar_cadastros"))
        self.assertFalse(tem_permissao(rita, "administrar_sistema"))


class ConfiguracaoDoServidor(SimpleTestCase):
    def importar_settings(self, **ambiente):
        env = {chave: valor for chave, valor in os.environ.items() if not chave.startswith("DJANGO_")}
        env.update(ambiente)
        return subprocess.run([sys.executable, "-c", "import pkzlab.settings as s; print(s.DEBUG, s.ALLOWED_HOSTS)"],
                              cwd=Path(__file__).resolve().parent.parent, env=env, capture_output=True, text=True)

    def test_sem_debug_exige_a_chave_secreta(self):
        r = self.importar_settings(DJANGO_DEBUG="0")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", r.stderr)

    def test_servidor_configurado_pelo_ambiente(self):
        r = self.importar_settings(DJANGO_DEBUG="0", DJANGO_SECRET_KEY="x" * 50, DJANGO_ALLOWED_HOSTS="pkz.lab")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "False ['pkz.lab']")

    def test_sem_nada_vale_o_desenvolvimento(self):
        r = self.importar_settings()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.startswith("True"))
