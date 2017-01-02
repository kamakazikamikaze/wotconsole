init:
	pip install -r requirements.txt

init dev:
	pip install -r requirements-dev.txt

install:
	python setup.py install

test:
	py.test tests

.PHONY: init test