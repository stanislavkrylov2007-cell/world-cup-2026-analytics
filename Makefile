.PHONY: install check test

install:
	pip install -e .[dev]

check:
	wca-check-config

test:
	pytest

