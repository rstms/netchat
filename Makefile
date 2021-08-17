#
#   netchat
#
#   MIT Licensed
#
#   git@github.com/rstms/tzc
#   mkrueger@rstms.net
#

PROJECT:=$(shell echo $$(basename $$(pwd)))


uninstall:
	pip uninstall -y ${PROJECT}

install:
	pip install --use-feature=in-tree-build --upgrade .

devinstall: uninstall
	$(shell [ -e pyproject.toml ] && mv pyproject.toml .pyproject.toml)
	pip install --use-feature=in-tree-build --upgrade -e .[dev,test,docs]
	$(shell [ -e .pyproject.toml ] && mv .pyproject.toml pyproject.toml)

clean:
	rm -rf .pytest_cache
	rm -rf ./build
	find . -type d -name __pycache__ | xargs -r rm -rf
	find . -type d -name \*.egg-info | xargs -r rm -rf
	find . -type f -name \*.pyc | xargs -r rm
	rm .fmt

TESTS=$(wildcard tests/test_*.py)
test:
	pytest $$(dotenv get PYTEST_OPTIONS) tests/test_*.py

test-full-trace:
	dotenv set -- PYTEST_OPTIONS '--full-trace'
	${MAKE} test

test-debug:
	dotenv set -- PYTEST_OPTIONS '--pdb'
	${MAKE} test

bump-patch:
	bumpversion patch

bump-minor:
	bumpversion minor 

bump-major:
	bumpversion major 


PYTHON_SOURCES:=$(shell find setup.py ${PROJECT} tests -name '*.py')
OTHER_SOURCES:=LICENSE Makefile README.md VERSION pyproject.toml setup.cfg setup.py tox.ini
SOURCES:=${PYTHON_SOURCES} ${OTHER_SOURCES}

fmt: .fmt  
.fmt: ${PYTHON_SOURCES}
	@$(foreach s,$?,yapf -i -vv ${s};) 
	@touch $@

gitclean:
	$(if $(shell git status --porcelain),$(error "git status dirty, commit and push first"))

# test with tox if sources have changed
.PHONY: tox
tox: .tox
.tox: ${SOURCES} VERSION
	@echo Changed files: $?
	tox
	@touch $@

# create distributable files if sources have changed
dist: .dist
.dist:	${SOURCES} .tox
	@echo Changed files: $?
	@echo Building ${PROJECT}
	python setup.py sdist bdist_wheel
	@touch $@

# set a git release tag and push it to github
release: gitclean .dist 
	@echo pushing Release ${PROJECT} v`cat VERSION` to github...
	TAG="v`cat VERSION`"; git tag -a $$TAG -m "Release $$TAG"; git push origin $$TAG

LOCAL_VERSION=$(shell cat VERSION)
PYPI_VERSION=$(shell scripts/pypi_version ${PROJECT})

pypi: release
	$(if $(wildcard ~/.pypirc),,$(error publish failed; ~/.pypirc required))
	@if [ "${LOCAL_VERSION}" != "${PYPI_VERSION}" ]; then \
	  echo publishing ${PROJECT} `cat VERSION` to PyPI...;\
	  python -m twine upload dist/*;\
	else \
	  echo ${PROJECT} ${LOCAL_VERSION} is up-to-date on PyPI;\
	fi

publish: pypi
