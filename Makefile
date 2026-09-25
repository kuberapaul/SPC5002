# SPC5002. One Makefile, and it grows with the repository.
#
# Each week's zip replaces this file with a longer version of itself. Every
# target you have ever been given still works, which is the point: the Week 12
# check clones your repository and runs `make setup && make run`, and `make run`
# was a Week 1 target.
#
# If you cannot say what a target does, ask on the Friday.

PY := python

# `python` only exists once the virtual environment is activated. Without this
# check, make prints "python: No such file or directory", which does not tell
# you that the fix is `source .venv/bin/activate`.
ifeq (,$(shell command -v $(PY) 2>/dev/null))
  ifneq (,$(shell command -v python3 2>/dev/null))
    PY := python3
  endif
endif

.PHONY: help setup test clean verify run

help:
	@echo "make run          run the Week 1 script, write outputs/metrics.json"
	@echo ""
	@echo "make test         run every contract test in the repository"
	@echo "make verify       run the current week's entry point twice and compare"
	@echo "make clean        delete outputs and caches"

setup:
	$(PY) -m pip install -r requirements.txt

test:
	$(PY) -m pytest -q

clean:
	rm -rf outputs .pytest_cache
	find . -name '__pycache__' -type d -exec rm -rf {} +
	find . -name '.ipynb_checkpoints' -type d -exec rm -rf {} +

run:
	$(PY) src/run.py

# the one that matters. It compares, and it exits non-zero when they differ:
# a check you cannot fail is not a check.
verify:
	@$(PY) src/run.py > /dev/null
	@A=$$(shasum -a 256 outputs/metrics.json 2>/dev/null || sha256sum outputs/metrics.json); \
	 $(PY) src/run.py > /dev/null; \
	 B=$$(shasum -a 256 outputs/metrics.json 2>/dev/null || sha256sum outputs/metrics.json); \
	 echo "$$A"; echo "$$B"; \
	 if [ "$$A" = "$$B" ]; then \
	   echo "the two hashes match"; \
	 else \
	   echo "THE TWO HASHES DIFFER. Something in your code is not seeded,"; \
	   echo "or depends on the order a set or dict happened to be in,"; \
	   echo "or on a file you wrote earlier."; \
	   exit 1; \
	 fi
