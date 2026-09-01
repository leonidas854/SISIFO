.PHONY: build install test test-go test-py doctor limpiar

GO ?= go
VENV := .venv/bin/python
BINDIR := bin
BINARY := $(BINDIR)/sisifo
LEGACY_BINARY := $(BINDIR)/taller

build:
	mkdir -p $(BINDIR)
	$(GO) build -o $(BINARY) ./cmd/sisifo
	ln -sfn sisifo $(LEGACY_BINARY)

install:
	./install.sh

test: test-go test-py

test-go:
	$(GO) vet ./...
	$(GO) test ./...

test-py:
	cd py && ../$(VENV) -m pytest tests/ -q

doctor: build
	$(BINARY) doctor

limpiar:
	rm -f $(BINARY) $(LEGACY_BINARY)
	find py -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf py/.pytest_cache
