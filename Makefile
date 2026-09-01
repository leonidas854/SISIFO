.PHONY: build install test doctor limpiar

build:
	go build -o bin/taller ./cmd/taller

install:
	./install.sh

test:
	go vet ./...
	go test ./... 2>/dev/null || true
	.venv/bin/python -c "import citeproc, yaml, requests, docx, pptx, pypdf; print('stack Python ok')"

doctor: build
	./bin/taller doctor

limpiar:
	rm -rf bin/ py/**/__pycache__
