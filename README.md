# Projeto Back-End 

**Código da Disciplina**: IBM8936<br>

## Sobre 
Descreva o seu projeto em linhas gerais. 

## Instalação 
**Linguagens**: Python, Django<br>
**Tecnologias**: Github, Visual Studio Code<br>
 os pré-requisitos para rodar o seu projeto são UX, Engenharia de Dados, POO.

## Como rodar o back-end

```bash
python3 -m venv venv
source venv/bin/activate            # no Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
cd backend
python manage.py migrate
python manage.py popular_demo       # dados de exemplo (senha de todos: senha12345)
python manage.py runserver
```

Site: http://127.0.0.1:8000 · Painel do administrador: http://127.0.0.1:8000/admin

```bash
python manage.py test estrutura pessoas agenda   # testes automáticos
python manage.py rotinas_da_agenda               # vence vagas não confirmadas e envia lembretes
```

Em produção, a rotina roda sozinha a cada 5 minutos (cron do servidor) e o banco é PostgreSQL.

## Organização do código

| App | O que tem |
| -- | -- |
| `estrutura` | Especialidade, Espaço (salas ligadas às especialidades), Serviço (duração e vagas), Configuração |
| `pessoas` | Funcionário, Papel (abstrata), Profissional, Recepção, Administrador, Atleta, Responsável, Consentimento LGPD |
| `agenda` | Disponibilidade, Bloqueio, Aula (grade de aulas em grupo), Agendamento, Lista de espera, Aviso, telas do site |

A dependência vai num sentido só: `agenda` usa `pessoas` e `estrutura`; `pessoas` usa `estrutura`.
