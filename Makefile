PY ?= python

.PHONY: all data figures map test

all: data figures map

data:
	$(PY) src/prepare.py

figures:
	$(PY) src/analyze.py

map:
	$(PY) src/make_map.py

test:
	$(PY) -m pytest -q
