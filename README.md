# StraitAI

**Academic Learning Outcome & Program Outcome Assessment System**

StraitAI is a university team project for **CSE 311 (Software Engineering)** and **CSE 321 (Data Systems)**. It helps evaluate student achievement by calculating **Learning Outcome (LO)** and **Program Outcome (PO)** scores from assessment grades.

## Core Features

- Manage courses, students, enrollments, LOs and POs.
- Record assessments and grades.
- Calculate weighted LO and PO achievement scores.
- Provide role-based views for **Students**, **Instructors** and **Department Heads**.
- Visualize academic performance.

## Technology Stack

| Area | Technology |
| --- | --- |
| Backend | Python 3.12+, Django (MVT) |
| Database | PostgreSQL, Django ORM |
| Project & dependency management | uv (`pyproject.toml`, `uv.lock`) |
| Frontend | Django Templates, HTML, Tailwind CSS |
| Charts | Chart.js or ApexCharts (planned) |
| Testing | Django TestCase / pytest |
| CI/CD | GitHub Actions (planned) |
| Version control & planning | Git, GitHub, GitHub Projects |
| Development & design tools | PyCharm / VSCode, pgAdmin / DBeaver, Postman, Draw.io / Mermaid, Figma |

> **Status:** This is the intended stack; individual components will be configured as development progresses.

## Project Structure (Planned)

```text
StraitAI/
├── config/          # Django configuration
├── accounts/        # Authentication and roles
├── academics/       # Courses, LOs and POs
├── assessments/     # Assessments, grades and calculations
├── dashboard/       # Role-based views
├── templates/
├── static/
├── docs/
├── manage.py
├── pyproject.toml
├── uv.lock
└── README.md
```

## Local Setup

**Requirements:** Python 3.12+, PostgreSQL, Git and [uv](https://docs.astral.sh/uv/).

Install `uv` by following the [official installation instructions](https://docs.astral.sh/uv/getting-started/installation/), then set up the project:

```bash
git clone <REPOSITORY_URL>
cd <REPOSITORY_DIRECTORY>
uv sync
cp .env.example .env
```

`uv sync` creates the project's `.venv` environment and installs the dependencies declared in `pyproject.toml`, using `uv.lock` for reproducible versions. You do not need to activate the virtual environment manually; use `uv run` for project commands.

Configure your local PostgreSQL connection in `.env` according to the project's settings, then run:

```bash
uv run python manage.py migrate
uv run python manage.py runserver
```

To add or update dependencies, use `uv add` and commit the resulting changes to `pyproject.toml` and `uv.lock`:

```bash
uv add <package-name>
uv lock
```

Run tests with:

```bash
uv run python manage.py test
```

> Setup commands apply once the Django configuration, dependencies and `.env.example` have been added to the repository.

## Development Workflow

We use **GitHub Projects** to track the product backlog, tasks and two-week development iterations. You can see and follow development status and planned work from there.

**Priority:** `0` High · `1` Medium · `2` Low  
**Workflow:** Backlog → To Do → In Progress → In Review → Done

## Team

- Zümrüt İpek Ertürk
- Begüm Uzuner
- Faruk Emre Afşar
- Berkay Bıyık

## Academic Context

Developed for **CSE 311** and **CSE 321**. This repository contains the application code and project documentation.
