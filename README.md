# github_actions_ci

A FastAPI demonstration project with CI/CD configurations for GitHub Actions,
CircleCI, and Harness.

The project includes an API, automated tests, code-quality checks, dependency
auditing, and Docker packaging. Deployment and verification steps are
demonstration placeholders—not complete production integrations.

## Project structure

```text
github_actions_ci/
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── .circleci/
│   └── config.yml
├── harness/
│   └── pipeline.yaml
├── app/
│   └── main.py
├── tests/
│   └── test_main.py
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

The folder is named `github_actions_ci`, but the supplied application,
container tags, and project metadata retain the original name `ci-cd-demo`.

## Requirements

- Python 3.12 for the documented local setup.
- pip for installing dependencies.
- Docker and Docker Compose for container workflows.
- Make, optionally, for the included shortcut commands.
- A GitHub repository for running GitHub Actions.
- CircleCI or Harness accounts if using those optional configurations.

The GitHub Actions test matrix also includes Python 3.11, although
`pyproject.toml` declares Python 3.12 or newer.

## Local setup

From the extracted project directory:

```bash
cd github_actions_ci
python -m venv .venv
```

Activate the virtual environment on macOS or Linux:

```bash
source .venv/bin/activate
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

Start the API:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/` | Returns the service name and a greeting. |
| GET | `/health` | Returns health status, application version, and environment. |
| GET | `/ready` | Returns a readiness flag and a timestamp. |

Example request:

```bash
curl http://127.0.0.1:8000/health
```

Default response:

```json
{
  "status": "healthy",
  "version": "development",
  "environment": "local"
}
```

The readiness endpoint always reports `true`. It does not check external
services or other dependencies.

## Environment variables

| Variable | Purpose | Application default |
| --- | --- | --- |
| `APP_ENV` | Environment reported by `/health`. | `local` |
| `APP_VERSION` | Version reported by `/health`. | `development` |

The Compose configuration sets `APP_ENV=development` and `APP_VERSION=local`.

Example local configuration:

```bash
APP_ENV=staging APP_VERSION=1.0.0 uvicorn app.main:app
```

## Tests and quality checks

Run the endpoint tests:

```bash
pytest -v
```

The included tests check successful responses from `/`, `/health`, and `/ready`.

Run the other checks individually:

```bash
ruff check .
ruff format --check .
mypy app
pip-audit
```

Or use Make:

```bash
make install
make check
make security
```

Available targets:

| Target | Action |
| --- | --- |
| `install` | Installs runtime and development dependencies. |
| `test` | Runs pytest. |
| `lint` | Runs Ruff lint checks. |
| `format-check` | Checks formatting without changing files. |
| `typecheck` | Runs MyPy against `app`. |
| `security` | Runs pip-audit. |
| `build` | Builds the local Docker image. |
| `run` | Starts the application with Docker Compose. |
| `check` | Runs lint, formatting, type checking, and tests. |
| `ci` | Runs `check`, then builds the image. |

`make check` and `make ci` do not include the dependency audit. Run
`make security` separately.

## Docker

The supplied Dockerfile uses Python 3.12, runs the application as a non-root
user, exposes port 8000, and defines a health check.

Before building, correct the supplied multiline `CMD` instruction to:

```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and start the container:

```bash
docker build -t ci-cd-demo:local .
docker run --rm -p 8000:8000 \
  -e APP_ENV=development \
  -e APP_VERSION=local \
  ci-cd-demo:local
```

Alternatively, use Docker Compose:

```bash
docker compose up --build
```

Stop the Compose application:

```bash
docker compose down
```

## GitHub Actions

The workflow is defined in `.github/workflows/ci-cd.yml`.

It runs on:

- Pushes to `main` and `develop`.
- Pull requests targeting `main`.
- Manual workflow dispatch.

The pipeline contains these jobs:

| Job | Purpose |
| --- | --- |
| `lint` | Runs Ruff lint and formatting checks. |
| `typecheck` | Runs MyPy. |
| `test` | Runs pytest on Python 3.11 and 3.12. |
| `security` | Audits installed dependencies with pip-audit. |
| `docker` | Builds and pushes a container image after all checks pass. |
| `staging` | Runs a placeholder deployment for `develop`. |
| `production` | Runs a placeholder deployment for `main`. |
| `verify` | Runs placeholder verification after production. |

The container job authenticates to GitHub Container Registry using
`GITHUB_TOKEN` and publishes these tags:

```text
ghcr.io/<owner>/<repository>:<commit-sha>
ghcr.io/<owner>/<repository>:latest
```

The workflow references GitHub environments named `staging` and `production`.
Configure any required approvals and environment protection rules in the
repository settings.

The supplied deployment and verification jobs only print messages. Replace
them with commands for your actual deployment platform and health checks.

## CircleCI

The configuration is defined in `.circleci/config.yml`.

Its workflow includes linting, formatting, type checking, tests, dependency
auditing, and a Docker build.

- The `develop` branch has a placeholder staging deployment.
- The `main` branch has an approval job before a placeholder production deployment.
- The Docker build does not publish an image to a registry.
- The test-results step references `test-results`, but the supplied pytest
  command does not generate a report there.

Connect the repository to CircleCI and adapt deployment commands and reporting
before relying on this pipeline.

## Harness

The example pipeline is defined in `harness/pipeline.yaml`.

It includes CI checks, a container build, Kubernetes deployment stages,
production approval, and a placeholder verification step.

The configuration references organization-specific resources, including:

- Organization: `engineering`
- Project: `platform`
- GitHub connector: `github`
- Repository: `ci-cd-demo`
- Service: `ci_cd_demo`
- Environments and infrastructure identifiers: `staging` and `production`
- Approver group: `platform-engineers`

Replace these references with resources from your Harness account and configure
the required execution infrastructure, connectors, services, and deployment
settings.

## Known limitations

This repository was extracted from the supplied HTML artifact. It has not been
validated as a working production pipeline.

Before relying on it:

- Fix the multiline Dockerfile `CMD` shown above.
- Add return type annotations to application functions to satisfy strict MyPy.
- Resolve import-order and formatting issues reported by Ruff.
- Align the Python support declaration with the GitHub Actions test matrix.
- Review and update pinned dependencies based on audit results.
- Restrict registry publishing appropriately. The supplied Docker job attempts
  to authenticate and push on pull-request runs as well as branch pushes.
- Review `latest` tagging: the supplied workflow uses it for both `main` and
  `develop` builds.
- Replace placeholder deployments and verification commands.
- Configure real deployment credentials and approval policies.
- Generate test reports if structured CI test reporting is required.
- Validate the Harness configuration against your account and infrastructure.

The supplied GitHub Actions test artifact contains `.pytest_cache`, not a
JUnit test report.

## Chatbot-driven branches and pull requests

`.github/workflows/chatbot-auto-branch.yml` listens for a `repository_dispatch`
event of type `chatbot-code-update`, writes the supplied file on a new
`chatbot/feature-<task_id>` branch, commits it (author set from `chatbot_id`
and `user_handle`), and opens a pull request against the default branch.

Payload (`client_payload`): `task_id`, `file_path`, `file_content`,
`content_encoding` (`raw` or `base64`), `description`, and optional
`chatbot_id`, `session_id`, `user_handle`, `interface_source`.
See `scripts/trigger_chatbot_update.py` for a sender example.

Only recognised chatbots are accepted:

- `.github/chatbot-allowlist.json` lists permitted `chatbot_id`s and the path
  prefixes each may write to. Unknown IDs are rejected. Chatbots cannot edit
  this file because `.github/` is blocked.
- Each payload must include `signature`: hex HMAC-SHA256 of
  `task_id\nfile_path\nfile_content` (content exactly as sent), keyed with that
  chatbot's secret. Store the keys in one repo secret `CHATBOT_KEYS`, e.g.
  `{"claude": "<key>", "internal-slack-bot": "<key>"}`. Without this, `chatbot_id`
  is self-declared and anyone holding a dispatch token could impersonate a bot.

Setup and security notes:

- Send the dispatch with a fine-grained PAT or GitHub App token with
  `contents: write` on this repo (`POST /repos/{owner}/{repo}/dispatches`).
- Enable **Settings → Actions → General → Allow GitHub Actions to create and
  approve pull requests**.
- PRs opened with `GITHUB_TOKEN` do not trigger other workflows; use a PAT or
  App token in the workflow if CI must run on these PRs.
- Payload values are passed through env vars and validated (`task_id` charset,
  path must stay in the repo and outside `.github/`) to prevent script
  injection and workflow tampering.
