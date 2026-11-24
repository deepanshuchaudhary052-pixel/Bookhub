# Bookhub

Bookhub is a Django-based library management application. It provides book and
author catalogs, member accounts, book-borrow requests, and loan tracking.

## Features

- Browse and manage books, authors, and categories
- Register and sign in as a library user
- Request books and review borrow requests
- Manage members and track book loans and returns
- Django admin interface

## Requirements

- Python 3.9 or later
- Microsoft SQL Server
- Microsoft ODBC Driver 18 for SQL Server

## Setup on Windows

Open PowerShell in the project directory and create a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Configure the database before running migrations. Bookhub uses SQL Server by
default. The connection settings can be supplied through these environment
variables:

| Variable | Purpose | Default |
| --- | --- | --- |
| `BOOKHUB_DB_NAME` | Database name | `bookHubDB` |
| `BOOKHUB_DB_USER` | Database user | Empty |
| `BOOKHUB_DB_PASSWORD` | Database password | Empty |
| `BOOKHUB_DB_HOST` | SQL Server host or instance | `DESKTOP-MAH9LAU\SQLEXPRESS` |
| `BOOKHUB_DB_PORT` | SQL Server port | Empty |
| `BOOKHUB_DB_EXTRA_PARAMS` | Additional ODBC connection parameters | `Encrypt=yes;TrustServerCertificate=yes` |

For example, set values for the current PowerShell session with
`$env:BOOKHUB_DB_HOST = "localhost\SQLEXPRESS"`. Do not commit database
passwords or other secrets to the repository.

Bookhub also supports the following Django settings:

| Variable | Purpose | Default |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Django signing key | Local-development placeholder |
| `DJANGO_DEBUG` | Enable Django debug mode (`True`, `1`, or `yes`) | `False` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed host names | `127.0.0.1,localhost,testserver` |

Set a unique `DJANGO_SECRET_KEY` for deployments; never use the local
development fallback in production. Set `DJANGO_ALLOWED_HOSTS` to the host
names used by your deployment.

After configuring the database, create its tables and an administrator:

```powershell
python manage.py migrate
python manage.py createsuperuser
```

Start the development server:

```powershell
python manage.py runserver
```

Open <http://127.0.0.1:8000/> in a browser. The Django admin is available at
<http://127.0.0.1:8000/admin/>.

## Tests

Run the test suite with:

```powershell
python manage.py test
```

The project uses MSSQL for Django test runs; normal application runs use the
configured SQL Server database.
