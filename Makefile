# netchat

uninstall:
	pip uninstall -y netchat 

install:
	pip install --use-feature=in-tree-build --upgrade .

devinstall: uninstall
	$(shell [ -e pyproject.toml ] && mv pyproject.toml .pyproject.toml)
	pip install --use-feature=in-tree-build --upgrade -e .[test,docs]
	$(shell [ -e .pyproject.toml ] && mv .pyproject.toml pyproject.toml)

clean:
	rm -rf .pytest_cache
	rm -rf ./build
	find . -type d -name __pycache__ | xargs -r rm -rf
	find . -type d -name \*.egg-info | xargs -r rm -rf
	find . -type f -name \*.pyc | xargs -r rm

TESTS=$(wildcard tests/test_*.py)
test:
	pytest tests/test_*.py
