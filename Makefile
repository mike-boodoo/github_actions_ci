install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	pytest -v

lint:
	ruff check .

format-check:
	ruff format --check .

typecheck:
	mypy app

security:
	pip-audit

build:
	docker build -t ci-cd-demo:local .

run:
	docker compose up --build

check: lint format-check typecheck test

ci: check build
