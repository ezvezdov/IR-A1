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

zip:
	zip -r A1.zip Makefile README.md download_external.sh main.py parser.py process_wordnet_cs.py report.pdf requirements.txt run run-0_test_cs.res run-0_test_en.res run-0_train_cs.res run-0_train_en.res run-1_test_cs.res run-1_test_en.res run-1_train_cs.res run-1_train_en.res slides.pdf
