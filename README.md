# Concurso Study Manager

Aplicação web local para gerenciamento de estudos para concursos, com suporte a múltiplos concursos, disciplinas, edital verticalizado, cronogramas, questões, revisões e dashboards.

## Stack inicial

- Python 3.12
- Django 6.1
- SQLite
- Docker + Docker Compose
- Django Templates
- Bootstrap (interface inicial)

## Rodar localmente com Docker

Pré-requisitos: Docker com o plugin `docker compose`.

Opcionalmente, copie as variáveis locais:

```bash
cp .env.example .env
```

Suba a aplicação:

```bash
docker compose up --build
```

A aplicação ficará disponível em:

```text
http://127.0.0.1:8000
```

O container executa as migrations automaticamente antes de iniciar o servidor.

### Comandos úteis

Executar as verificações do Django:

```bash
docker compose run --rm web python manage.py check
```

Executar os testes:

```bash
docker compose run --rm web python manage.py test
```

Criar um superusuário para o Django Admin:

```bash
docker compose exec web python manage.py createsuperuser
```

Abrir um shell Django:

```bash
docker compose exec web python manage.py shell
```

Parar os containers:

```bash
docker compose down
```

Apagar também o volume local do banco de dados e começar com uma base vazia:

```bash
docker compose down -v
```

> Atenção: `docker compose down -v` apaga o banco SQLite persistido no volume Docker.

## Persistência dos dados

O SQLite não é versionado no Git. Dentro do Docker, o arquivo fica em `/data/db.sqlite3`, armazenado no volume nomeado `concurso_study_data`. Assim, rebuilds da imagem não apagam os dados.

## Desenvolvimento

O código-fonte fica no GitHub; o banco local, arquivos `.env` e outros artefatos de execução permanecem fora do versionamento.

> Projeto em desenvolvimento.
