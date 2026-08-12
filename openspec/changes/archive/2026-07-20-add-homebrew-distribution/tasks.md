## 1. Freeze spike — prove the binary is possible (do this FIRST)

- [x] 1.1 Add `pyinstaller` to the `dev` dependency group and `uv sync`
- [x] 1.2 Build a local `--onefile` binary with `--collect-all textual`, `--collect-submodules universal_remote`, and hidden-import/collect flags for `zeroconf`, `pyatv`, `protobuf`, `androidtvremote2`, `adb-shell`
- [x] 1.3 Run the frozen binary and exercise **real device discovery** — confirm TVs appear (no missing-module / missing-data-file errors)
- [x] 1.4 Run the frozen binary and exercise a **real pairing + control** flow against an actual TV
- [x] 1.5 Iterate flags until discovery + pairing work cleanly; capture the final flags in a committed build script (e.g. `packaging/build_binary.sh` or a `.spec` file). If PyInstaller cannot be coaxed, switch to the Nuitka fallback and record why

## 2. Non-interactive CLI entry point (code prerequisite)

- [x] 2.1 Write failing tests: `main()` with `--version` exits 0, prints a line containing the version, and never constructs/runs the app; `--help` exits 0 without launching (red)
- [x] 2.2 Implement `argparse` short-circuit in `cli.main()` before `build_app().run()`; resolve version via `importlib.metadata.version("universal-remote")` (green)
- [x] 2.3 Preflight: `ruff` format + check, full `pytest` suite passes

## 3. Project prerequisites

- [x] 3.1 Add a `LICENSE` file (MIT) and set `license` in `pyproject.toml`
- [x] 3.2 Add `python-semantic-release` to the `dev` group and a `[tool.semantic_release]` config: version in `pyproject.toml`, deterministic first version (`allow_zero_version`/initial version), changelog on, and `[skip ci]` in the bump commit message
- [x] 3.3 Set the repo's `development` → `main` flow to use a **merge commit** (not squash); document "merge, don't squash, into main" in README/CONTRIBUTING

## 4. Homebrew tap repository

- [x] 4.1 Create public repo `praxder/homebrew-tap`
- [x] 4.2 Add `Formula/universal-remote.rb`: `desc`/`homepage`/`license`, `version` + `url` (release asset) + `sha256`, `depends_on arch: :arm64`, `bin.install "universal-remote"`, and a `test do` asserting `--version` matches the version
- [x] 4.3 Create a fine-grained PAT scoped to contents-write on `homebrew-tap` only; store it as the `HOMEBREW_TAP_TOKEN` secret in the `universal-remote` repo

## 5. Release pipeline (`.github/workflows/release.yml`, trigger `push: main`)

- [x] 5.1 `release` job: run python-semantic-release → outputs `released` (bool) + `version`; on a releasable diff, tag `vX.Y.Z` and create the GitHub Release with grouped notes; guard against re-triggering on the bump commit
- [x] 5.2 `build` job (`macos-14`, `needs: release`, `if: released`): `uv sync`, run the task-1.5 build, `tar.gz` + compute `sha256`, smoke-test the binary with `--version` (fail on mismatch), upload the archive as a release asset
- [x] 5.3 `tap` job (`needs: build`): checkout `praxder/homebrew-tap` with `HOMEBREW_TAP_TOKEN`, rewrite `Formula/universal-remote.rb` with the new `version`/`url`/`sha256`, commit and push

## 6. End-to-end verification

- [x] 6.1 Merge to `main` and confirm: a release is created, version bump matches the commit types, notes are grouped by type, and the binary asset is attached
- [x] 6.2 Confirm the tap formula was bumped to the new version + sha256
- [x] 6.3 Run `brew install praxder/tap/universal-remote` on an arm64 Mac that did **not** build the binary; confirm it installs past Gatekeeper, launches, discovers, and `--version` matches
- [x] 6.4 Confirm a no-releasable-commits push to `main` produces no release (no-op)

## 7. Documentation

- [x] 7.1 Add an "Install via Homebrew" section to README (`brew install praxder/tap/universal-remote`) and note the manual/`uv` path as the dev alternative
