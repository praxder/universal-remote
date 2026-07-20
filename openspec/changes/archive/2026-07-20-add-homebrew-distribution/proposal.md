## Why

Today the only way to install `universal-remote` is to clone the repo and run it
through `uv` — a Python-3.13-plus-`uv` toolchain the target user (someone who just
wants a TV remote in their terminal) should not need. Shipping a self-contained
binary through a Homebrew tap turns installation into a single `brew install`, and
automating it on every merge to `main` means releases stay effortless and their
notes stay honest — generated from the conventional commits that actually shipped.

## What Changes

- Add a `--version` and `--help` path to the CLI entry point that prints and exits
  **before** the Textual app starts, so the binary is verifiable in a non-TTY
  environment (CI, the Homebrew formula `test do` block).
- Freeze the app into a **single standalone macOS arm64 binary** (PyInstaller
  `--onefile`) that runs with no user-provided Python or `uv`. Requires bundling
  Textual's framework CSS and the dynamic-import deps (`zeroconf`, `pyatv`,
  `protobuf`, `androidtvremote2`, `adb-shell`).
- Add a **GitHub Actions release pipeline** triggered on push to `main`
  (i.e. merging `development` → `main`). It auto-derives the next semantic version
  and release notes from conventional commits (python-semantic-release), builds the
  binary, publishes a GitHub Release with the notes and the binary asset, and pushes
  the updated formula to the tap.
- Publish and maintain a **Homebrew tap** (`praxder/homebrew-tap`) whose
  `universal-remote` formula downloads the released binary by version + SHA-256 so
  users install with `brew install praxder/tap/universal-remote`.
- Add an OSI `LICENSE` (recommended: MIT) — a practical prerequisite for a public
  formula.
- **Process requirement (not code):** `development` → `main` must use a **merge
  commit** (not squash), or PSR sees one collapsed message and produces the wrong
  version bump and a one-line changelog.

## Capabilities

### New Capabilities
- `homebrew-distribution`: The shippable artifacts and their contract — a
  standalone macOS arm64 binary, the non-interactive `--version`/`--help` CLI
  behavior that makes it verifiable, and the Homebrew tap formula users install
  from.
- `release-automation`: The merge-to-`main` CI pipeline — conventional-commit
  version derivation, release-notes/changelog generation, binary build, GitHub
  Release publication, and tap-formula update.

### Modified Capabilities
<!-- None: no existing spec's requirements change. -->

## Impact

- **Code:** `src/universal_remote/cli.py` (`main()` gains argument handling before
  `.run()`).
- **New files:** `.github/workflows/release.yml`, a PyInstaller spec/build script,
  PSR config in `pyproject.toml` (`[tool.semantic_release]`), `LICENSE`, README
  install-via-Homebrew section.
- **New external repo:** `praxder/homebrew-tap` holding `Formula/universal-remote.rb`.
- **Secrets/config:** a fine-grained PAT (`HOMEBREW_TAP_TOKEN`, contents:write on the
  tap repo) stored as an Actions secret; repo default merge method set to allow
  merge commits for `development` → `main`.
- **Dependencies:** dev-group additions — `pyinstaller`, `python-semantic-release`.
- **Runtime risk:** freezing this native/dynamic-import dep set is the make-or-break
  unknown and unsigned-arm64 Gatekeeper behavior must be verified on a Mac that did
  not build the binary. Both are addressed as early tasks in `tasks.md`.
