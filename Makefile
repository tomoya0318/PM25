.PHONY: test

format:
	poetry run black src/ test/

lint:
	poetry run flake8 src/

test:
	poetry run pytest -vv

test_pt:
	poetry run pytest -s

up:
	docker compose build
	docker compose up -d

exec:
	docker exec -it pm25 sh

down:
	docker compose down

build_gumtree:
	docker build -t tomoya0318/gumtree --progress=plain ./gumtree