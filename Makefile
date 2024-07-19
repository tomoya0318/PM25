.PHONY: test

format:
	poetry run black src/

lint:
	poetry run flake8 src/

test:
	poetry run pytest test/pattern