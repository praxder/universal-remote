## Context

`universal-remote` is a Python 3.13 Textual TUI, uv-managed, hatchling-built, on
GitHub at `praxder/universal-remote`. Entry point `universal-remote =
universal_remote.cli:main`; `main()` currently is just `build_app().run()` — it
launches the TUI unconditionally with no argument handling. Direct deps include
several with native builds and/or runtime dynamic imports: `zeroconf` (Cython),
`aiohttp` (C), `cryptography` (Rust), `protobuf`, `pyatv`, `androidtvremote2`,
`adb-shell`. There is no LICENSE, no CI, no tagged release, and the project is not
on PyPI.

The goal (from the proposal): one-command install via a Homebrew tap, fed by a
release that fires automatically when `development` merges into `main`, with
version and notes derived from conventional commits. Decision inputs already fixed
by the user: **macOS arm64 only**, **auto-versioning from conventional commits**,
**separate `praxder/homebrew-tap` repo**.

## Goals / Non-Goals

**Goals:**
- `brew install praxder/tap/universal-remote` installs a working binary on Apple
  Silicon with no user Python/uv.
- Merging `development` → `main` produces a versioned GitHub Release whose notes
  reflect what actually changed, with the binary attached and the tap formula
  bumped — hands-off.
- The distributed binary is verifiable non-interactively (`--version`).

**Non-Goals:**
- Homebrew *core* submission (notability bar; out of scope).
- Intel macOS, Linux, or Windows binaries (arm64 only for now).
- Code signing / notarization with a paid Apple Developer ID (rely on ad-hoc
  signing + Homebrew's non-quarantined download; revisit only if Gatekeeper blocks).
- Publishing to PyPI (orthogonal; not required for the binary path).

## Decisions

### D1: PyInstaller `--onefile` for the binary
Textual documents PyInstaller support; it is the most battle-tested freezer for
TUI + async apps. `--onefile` yields a single executable that maps cleanly to
Homebrew's `bin.install`. Framework CSS and dynamic-import deps are pulled in with
`--collect-all textual` and `--collect-all`/`--hidden-import` for `zeroconf`,
`pyatv`, `androidtvremote2`, `adb-shell`, `protobuf` (and `--collect-submodules`
for `universal_remote` so all adapter modules are bundled).
- *Alternatives:* Nuitka (kept as the fallback if PyInstaller misses imports it
  can't be told about); `shiv`/`pex` (rejected — need Python present at runtime,
  defeating the purpose).

### D2: python-semantic-release (PSR) for version + notes
PSR fires the release **immediately** on push to `main` — analyze conventional
commits since the last tag, bump the version, update the changelog, create the tag
and GitHub Release with generated notes, in one run. This matches "merge →
release" exactly.
- *Alternatives:* release-please (rejected — inserts a release-PR gate, so a merge
  to `main` does not release directly); git-cliff + hand-rolled shell (more moving
  parts than PSR gives for a Python project). PSR also bumps `version` in
  `pyproject.toml` for us.

### D3: `--version`/`--help` handled before `.run()`
`main()` parses args (stdlib `argparse` — no new dep) and, for `--version`/`--help`,
prints and `sys.exit(0)` **before** constructing/running the Textual app. Required
because CI and the formula `test do` have no TTY; calling `.run()` there hangs or
crashes. `--version` reads the package version via
`importlib.metadata.version("universal-remote")`.

### D4: Three-job pipeline on `push: main`
```
release  (ubuntu)   PSR → new version, tag vX.Y.Z, GitHub Release + notes
   │  outputs: released? (bool), version
   ▼  if released
build    (macos-14) uv sync → pyinstaller → tar.gz + sha256
   │                upload asset to release vX.Y.Z
   ▼
tap      (ubuntu)   checkout praxder/homebrew-tap (PAT) → render Formula → push
```
`macos-14` runners are arm64, so the build is native (no cross-compile).

### D5: Binary formula in a separate tap, arch-guarded
`Formula/universal-remote.rb` in `praxder/homebrew-tap` (tap id `praxder/tap`).
The formula pins `version`, `url` (release asset), `sha256`; `depends_on arch:
:arm64` so an Intel user gets a clear error instead of a broken binary; `test do`
asserts `--version` output. Cross-repo push uses a fine-grained PAT
(`HOMEBREW_TAP_TOKEN`, contents:write on the tap repo only).

## Risks / Trade-offs

- **[Freeze failure — highest risk]** PyInstaller may silently omit dynamic
  imports (`zeroconf`, `pyatv`, `protobuf`, `androidtvremote2`, `adb-shell`) or
  Textual's CSS, producing a binary that launches but fails at discovery/pairing. →
  **Mitigation:** a local freeze spike is task #1 — build, then exercise real
  discovery + a pairing flow on the frozen binary — *before* any pipeline YAML is
  written. Add missing `--hidden-import`/`--collect-*` until it works; fall back to
  Nuitka if PyInstaller can't be coaxed.
- **[Squash merge breaks versioning]** A squash-merge of `development` → `main`
  collapses the cycle into one commit → PSR computes the wrong bump and a one-line
  changelog. → **Mitigation:** mandate a merge commit for `development` → `main`
  (documented in README + repo settings); the current history already uses `--no-ff`
  merges.
- **[Non-interactive entry point]** If `--version`/`--help` doesn't exit before
  `.run()`, both the CI smoke check and the formula test hang. → **Mitigation:**
  D3, plus a smoke-test step in the build job that runs the frozen binary with
  `--version` and asserts the version string.
- **[Gatekeeper on unsigned arm64]** The binary is only ad-hoc signed (PyInstaller
  default). It may run fine via Homebrew (brew doesn't quarantine its downloads) but
  "works on the build machine" is not evidence. → **Mitigation:** verify with a real
  `brew install` on an arm64 Mac that did **not** build it; only add Developer-ID
  signing if that fails.
- **[First release has no prior tag]** PSR bumps "since last tag"; run #1 has none.
  → **Mitigation:** set PSR config (`allow_zero_version` / an explicit initial
  version) so the first run yields a deterministic `vX.Y.Z`.
- **[PSR commit re-triggers workflow]** PSR pushes the version bump back to `main`,
  which could loop the workflow. → **Mitigation:** `[skip ci]` in PSR's commit
  message and/or an actor guard on the trigger.
