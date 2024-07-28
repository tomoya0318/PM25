.PHONY: test

format:
	poetry run black src/ test/

lint:
	poetry run flake8 src/

test:
	poetry run pytest -vv

test_pt:
	poetry run pytest -s