# ANÁLISE COMPARATIVA DE FRAMEWORKS WEB PYTHON
## Um estudo sobre FastAPI, Flask e Django na construção de APIs REST

Resumo curto
----------
Este repositório contém três implementações de uma API de e‑commerce — usando Django (Django REST Framework), FastAPI e Flask — com foco em aplicar padrões de projeto e comparar estrutura, desempenho e testabilidade entre os frameworks.

Estrutura do repositório
------------------------
- djangoApp/      — aplicação Django (manage.py, apps, testes, locustfile)
- fastapiApp/     — aplicação FastAPI (fastapi_ecommerce, testes, locustfile)
- flaskApp/       — aplicação Flask (flask_ecommerce, rotas, locustfile)
- requirements.txt

Pré-requisitos
--------------
- Python 3.11 (ou compatível)
- Git (opcional)
- Ambiente virtual recomendado (venv)
- Drivers de banco conforme uso (ex: PyMySQL, psycopg2)

Instalação geral (Windows)
--------------------------
1. Abra terminal na raiz do repositório (comparasion).
2. Crie/ative venv:
   - python -m venv venv
   - .\venv\Scripts\activate
3. Instale dependências:
   - python -m pip install -r requirements.txt

Executando a aplicação Django
-----------------------------
1. Vá para a pasta do projeto Django:
   - cd djangoApp
2. Ative venv (se necessário) e instale dependências (já feito na raiz).
3. Migre o banco:
   - python manage.py migrate
4. Rode o servidor:
   - python manage.py runserver
5. URL padrão:
   - http://127.0.0.1:8000

Executando a aplicação FastAPI
------------------------------
1. Entre na pasta FastAPI:
   - cd fastapiApp
2. Ative venv (se necessário).
3. Rode com Uvicorn (assumindo o módulo fastapi_ecommerce.main:app):
   - uvicorn fastapi_ecommerce.main:app --reload --host 127.0.0.1 --port 8000
4. Docs interativos:
   - http://127.0.0.1:8000/docs

Executando a aplicação Flask
----------------------------
1. Entre na pasta Flask:
   - cd flaskApp
2. Ative venv (se necessário).
3. Se a app usa factory `create_app` em `flask_ecommerce.app`, rode:
   - set FLASK_APP=flask_ecommerce.app:create_app
   - set FLASK_ENV=development
   - flask run --host=127.0.0.1 --port=5000
   Ou simplesmente:
   - python -m flask --app flask_ecommerce.app --debug run
4. URL padrão:
   - http://127.0.0.1:5000

Rodando testes
--------------
- Django (a partir de djangoApp):
  - python manage.py test
- FastAPI (a partir de fastapiApp):
  - set PYTHONPATH=%CD%
  - pytest
- Flask (a partir de flaskApp):
  - pytest  (ou configure/execute testes específicos conforme a suite)

Load testing com Locust
-----------------------
- Locust files:
  - djangoApp/locustfile.py
  - fastapiApp/fastapi_ecommerce/locustfile.py
  - flaskApp/flask_ecommerce/locustfile.py
- Exemplo (FastAPI):
  - cd fastapiApp
  - locust -f fastapi_ecommerce/locustfile.py --host=http://127.0.0.1:8000
- Abra UI:
  - http://127.0.0.1:8089

Boas práticas e observações
---------------------------
- Use variáveis de ambiente para credenciais e URIs de banco (DATABASE_URL).
- Ative o driver de BD correto se usar MySQL/Postgres (PyMySQL, psycopg2).
- Mantenha testes pequenos e independentes; use bases de teste isoladas.
- Para comparação de desempenho, documente cenários (payloads, número de usuários, métricas).

Contato / Autor
---------------
Trabalho de conclusão (TCC) — implementação para análise comparativa entre FastAPI, Flask e Django.
