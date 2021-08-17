#
#   netchat
#
#   MIT Licensed
#
#   git@github.com/rstms/tzc
#   mkrueger@rstms.net
#

PROJECT:=$(shell echo $$(basename $$(pwd)))
PYTHON_SOURCES:=$(shell find setup.py ${PROJECT} tests -name '*.py')

testo:
	echo ${PROJECT}

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
	pytest tests/test_*.py

define bump
bumpversion $1;
dotenv set VERSION $$(cat VERSION);
sed -e "s/\(__version__\).*$$/\\1='$$VERSION'/" -i ${PROJECT}/__init__.py
endef

bump-patch:
	$(call bump,patch)

bump-minor:
	$(call bump,minor)

bump-major:
	$(call bump,major)

fmt: .fmt  
.fmt: ${PYTHON_SOURCES}
	@$(foreach s,$?,yapf -i -vv ${s};) 
	@touch $@

