.PHONY: venv

venv:
	python -m venv venv
	venv/bin/pip install -r requirements.txt -r dev-requirements.txt
