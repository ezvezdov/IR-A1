.PHONY: setup clean make_run_executable download_external_resources make_eval

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# default
setup: $(VENV)/bin/activate make_run_executable download_external_resources make_eval

# Create venv
$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	touch $(VENV)/bin/activate

# Make run file executable
make_run_executable:
	chmod +x run

# Download external resources
download_external_resources:
	chmod +x download_external.sh
	./download_external.sh

# Make evaluator executable
make_eval:
	cd eval && make && cd ..

# Remove venv
clean:
	rm -rf $(VENV)
