.PHONY: run test lint type format docker-up docker-down

run:
	uvicorn src.service.api:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -q

lint:
	ruff check .

type:
	mypy --ignore-missing-imports .

format:
	ruff format .

docker-up:
	docker-compose up -d --build

docker-down:
	docker-compose down
