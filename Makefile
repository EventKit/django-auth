black:
	black --check --diff .

black-format:
	black .

pylint:
	pylint --load-plugins pylint_django --django-settings-module=django_auth.settings django_auth auth

flake8:
	flake8

lint: black flake8 pylint

test:
	coverage run -m pytest

install-hooks:
ifeq ($(detected_OS),Windows)
	cp hooks/pre-commit .git/hooks/pre-commit
else
	ln -s -f ${CURDIR}/hooks/pre-commit ${CURDIR}/.git/hooks/pre-commit
endif
