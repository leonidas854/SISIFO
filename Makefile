.PHONY: build install test test-go test-py doctor limpiar

VENV := .venv/bin/python

build:
	go build -o bin/taller ./cmd/taller

install:
	./install.sh

test: test-go test-py

test-go:
	go vet ./...
	go test ./... 

test-py:
	cd py && ../$(VENV) -m pytest tests/ -q

doctor: build
	./bin/taller doctor

limpiar:
	rm -rf bin/ py/**/__pycache__ py/.pytest_cache
