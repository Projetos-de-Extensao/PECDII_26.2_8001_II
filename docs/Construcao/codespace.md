---
id: ambiente
title: Ambiente e servidor
---

## Introdução

<p align="justify">
Esta página mostra como o grupo roda o projeto na própria máquina e como funciona o servidor de demonstração na AWS, que o professor e o PKZ LAB usam para testar a API sem instalar nada.
</p>

## Ambiente de desenvolvimento

Cada integrante roda o projeto na própria máquina, com Python 3.12 e um ambiente virtual:

```bash
python3 -m venv venv
source venv/bin/activate              # no Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
cd backend
python manage.py migrate              # cria o banco SQLite
python manage.py popular_demo         # dados de exemplo (senha senha12345)
python manage.py runserver            # http://127.0.0.1:8000/api/docs/
```

| Comando | Para que serve |
| -- | -- |
| `python manage.py test` | Roda todos os testes, igual ao GitHub Actions |
| `python manage.py makemigrations --check --dry-run` | Confere se alguma mudança nos models ficou sem migração |
| `python manage.py rotinas_da_agenda` | Vence as ofertas da lista de espera e envia os lembretes de 24 horas |
| `mkdocs serve -a 127.0.0.1:8001` (na raiz, depois de `pip install -r requirements.txt`) | Mostra esta documentação em http://127.0.0.1:8001, sem brigar pela porta do Django |

Sem servidor de e-mail configurado, os e-mails do sistema (avisos e recuperação de senha) aparecem no terminal do `runserver`.

## Servidor de demonstração

| Item | Como está |
| -- | -- |
| Máquina | Instância EC2 da AWS chamada "Os fofos", na região de Ohio (`us-east-2`) |
| Endereço | http://3.148.241.152:8000/api/docs/ (Swagger) e http://3.148.241.152:8000/admin/ |
| Aplicação | Django rodando como serviço do sistema (`pkzlab`), na porta 8000 |
| Banco | SQLite, carregado com o `popular_demo` |
| Logins de exemplo | Os do README (ex.: `carla@pkzlab.demo`, senha `senha12345`) |

O servidor é atualizado pelo AWS Systems Manager, que roda os comandos na máquina sem precisar de SSH:

1. Copia o banco (`db.sqlite3.antes-deploy-<data>`), para poder voltar atrás.
2. `git pull` da `main`.
3. `pip install -r requirements.txt`, `manage.py check` e `manage.py migrate`.
4. Reinicia o serviço `pkzlab` e confere se ele voltou.

É um servidor de demonstração, sem dados reais: roda com `DEBUG` ligado e o `runserver` do Django. O que muda para produção (PostgreSQL, HTTPS, gunicorn, chave secreta e rotinas no cron) está no [Plano de Transição](../Transicao/plano_de_transicao.md).

## Autor(es)

| Data | Versão | Descrição | Autor(es) |
| -- | -- | -- | -- |
| 11/11/2026 | 1.0 | Ambiente de desenvolvimento do grupo e servidor de demonstração na AWS | Vitor Magalhães |
