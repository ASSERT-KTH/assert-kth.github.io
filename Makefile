# targets that aren't filenames
.PHONY: all clean deploy build serve

all: build

BIBBLE = bibble

# use system bundler if present, otherwise the copy vendored in vendor/bundle
BUNDLE ?= $(shell command -v bundle 2>/dev/null || echo ruby $(wildcard vendor/bundle/ruby/*/bin/bundle))

_includes/pubs.html: bib/pubs.bib bib/publications.tmpl
	mkdir -p _includes
	$(BIBBLE) $+ > $@

build: _includes/pubs.html
	$(BUNDLE) exec jekyll build

# you can configure these at the shell, e.g.:
# SERVE_PORT=5001 make serve
SERVE_HOST ?= 127.0.0.1
SERVE_PORT ?= 5000

serve: _includes/pubs.html
	$(BUNDLE) exec jekyll serve --port $(SERVE_PORT) --host $(SERVE_HOST)

clean:
	$(RM) -r _site _includes/pubs.html

DEPLOY_HOST ?= yourwebpage.com
DEPLOY_PATH ?= www/
RSYNC := rsync --compress --recursive --checksum --itemize-changes --delete -e ssh

deploy: clean build
	$(RSYNC) _site/ $(DEPLOY_HOST):$(DEPLOY_PATH)
