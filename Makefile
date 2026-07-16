PYTHON = python3
VENV_PYTHON = fly_venv/bin/python
PIP = fly_venv/bin/pip

ROXO = $(shell printf '\033[35m')
RESET = $(shell printf '\033[0m')

MYPY_FLAGS = --warn-return-any \
			 --warn-unused-ignores \
			 --ignore-missing-imports \
			 --disallow-untyped-defs \
			 --check-untyped-defs

install:
	@$(PIP) install --upgrade pip 
	@$(VENV_PYTHON) -m pip install -r requirements.txt

run:
	$(VENV_PYTHON) gui.py level.txt

debug:
	$(VENV_PYTHON) -m pdb gui.py

venv:
	@$(PYTHON) -m venv fly_venv
	@make install
	@echo "$(ROXO) Run: 'source fly_venv/bin/activate' for activate the venv$(RESET)"

clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@echo "\n=== Arquivos apagados com sucesso! ===\n"

lint:
	-$(PYTHON) -m flake8
	-$(PYTHON) -m mypy $(MYPY_FLAGS) .

lint-strict:
	-$(PYTHON) -m flake8
	-$(PYTHON) -m mypy --strict .
