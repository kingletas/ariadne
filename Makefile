SHELL := /usr/bin/env bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

ROOT_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
PREFIX ?= $(HOME)/bin
UV ?= uv

.PHONY: help
help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

# --- the environment ---

.PHONY: venv
venv: ## Build the virtualenv. --system-site-packages so the host GTK bindings are visible
	@test -d .venv || $(UV) venv --python /usr/bin/python3 --system-site-packages
	@$(UV) sync --all-extras

# --- running it ---

.PHONY: page
page: ## Render a reader page: make page BOOK=path/to/book.epub OUT=page.html
	@test -n "$(BOOK)" || { echo "BOOK= is required, e.g. make page BOOK=~/Books/moby.epub"; exit 2; }
	@$(UV) run ariadne "$(BOOK)" -o "$(or $(OUT),page.html)"

.PHONY: app
app: ## Open the desktop reader against BOOK=
	@test -n "$(BOOK)" || { echo "BOOK= is required, e.g. make app BOOK=~/Books/moby.epub"; exit 2; }
	@$(UV) run ariadne --app "$(BOOK)"

.PHONY: inspect
inspect: ## Say what ariadne detects in BOOK= without writing anything
	@test -n "$(BOOK)" || { echo "BOOK= is required"; exit 2; }
	@$(UV) run ariadne "$(BOOK)" --inspect

# --- the gate ---

.PHONY: lint
lint: ## Static checks: the linter, the formatter, and the shell
	@$(UV) run ruff check .
	@$(UV) run ruff format --check .
	@shellcheck -S style $(shell grep -rl '^#!/usr/bin/env bash' scripts packaging 2>/dev/null)

.PHONY: format
format: ## Apply the formatter
	@$(UV) run ruff format .
	@$(UV) run ruff check --fix .

.PHONY: test
test: ## The unit suite, the layering check and the goldens
	@$(UV) run pytest -q

.PHONY: smoke
smoke: venv ## Drive the real window and save a PNG of each view
	@$(UV) run python scripts/gui-smoke.py $(if $(MODEL),"$(MODEL)",)

.PHONY: snapshot
snapshot: ## Re-record the ingest baseline. Only after a deliberate change, and read the diff
	@$(UV) run python tests/golden/snapshot_ingest.py

.PHONY: metadata
metadata: ## Validate the desktop entry, the icon and the AppStream metadata
	@$(ROOT_DIR)/scripts/validate-metadata

.PHONY: doctor
doctor: ## Say whether the desktop reader can open on this machine
	@$(UV) run ariadne --doctor

.PHONY: check
check: lint test metadata ## Everything a commit has to pass

# --- packaging ---

.PHONY: deb
deb: ## Build the .deb into dist/
	@$(ROOT_DIR)/packaging/deb/build.sh $(ROOT_DIR)/dist

.PHONY: version
version: ## Print the version this tree builds as
	@$(ROOT_DIR)/packaging/version.sh

.PHONY: release
release: ## Bump to a release: make release VERSION=0.2.0 (add DRY_RUN=1 to preview)
	@test -n "$(VERSION)" || { echo "VERSION= is required, e.g. make release VERSION=0.2.0"; exit 2; }
	@$(ROOT_DIR)/scripts/release $(if $(DRY_RUN),-n,) "$(VERSION)"

.PHONY: clean
clean: ## Remove caches and build products; the virtualenv stays
	@rm -rf dist build .pytest_cache .ruff_cache
	@find . -name __pycache__ -type d -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	@echo "cleaned"

.PHONY: flatpak
flatpak: ## Build and install the Flatpak locally (needs the GNOME 50 runtime and SDK)
	@flatpak-builder --user --install --force-clean --disable-rofiles-fuse \
		build $(ROOT_DIR)/data/flatpak/com.kingletas.Ariadne.yaml

.PHONY: bundle
bundle: ## Build a single-file .flatpak into dist/, the way the release does
	@mkdir -p $(ROOT_DIR)/dist
	@flatpak-builder --disable-rofiles-fuse --force-clean \
		--repo=$(ROOT_DIR)/repo build $(ROOT_DIR)/data/flatpak/com.kingletas.Ariadne.yaml
	@flatpak build-bundle $(ROOT_DIR)/repo \
		"$(ROOT_DIR)/dist/ariadne_$(shell $(ROOT_DIR)/packaging/version.sh).flatpak" \
		com.kingletas.Ariadne
	@echo "built dist/ariadne_$(shell $(ROOT_DIR)/packaging/version.sh).flatpak"

.PHONY: notes
notes: ## Print a version's release notes: make notes VERSION=0.1.0
	@test -n "$(VERSION)" || { echo "VERSION= is required, e.g. make notes VERSION=0.1.0"; exit 2; }
	@$(ROOT_DIR)/packaging/release-notes.sh "$(VERSION)"

# --- installing ---

.PHONY: install
install: ## Copy this tool into ~/bin (PREFIX= to change)
	@$(ROOT_DIR)/scripts/install "$(PREFIX)"

.PHONY: uninstall
uninstall: ## Remove the installed copy
	@$(ROOT_DIR)/scripts/uninstall "$(PREFIX)"
