## Why

The frozen macOS binary shipped via GitHub Releases and Homebrew takes ~4s to
open, versus ~0.3–1s for a `uv run` source launch. The cost is not the app: the
TUI mount is already non-blocking and imports total ~0.3s. It is PyInstaller
`--onefile`, which self-extracts ~29MB to a temp directory on **every** launch —
and, because those extracted Mach-O files land on fresh temp inodes each time, a
quarantined download (GitHub/Homebrew) makes macOS Gatekeeper re-scan them on
every launch rather than once. Switching to `--onedir` removes the per-launch
extraction and gives stable inodes (Gatekeeper assesses once, then caches),
dropping frozen startup to roughly source-launch speed.

## What Changes

- Build the frozen binary with PyInstaller `--onedir` instead of `--onefile`, so
  the distributable is an unpacked application directory (`dist/universal-remote/`
  with the executable at `dist/universal-remote/universal-remote`) rather than a
  self-extracting single file.
- The release asset stays a `.tar.gz`; it now archives the onedir directory. The
  CI smoke test runs the executable at its new in-directory path.
- The Homebrew tap formula installs the onedir tree (into the formula prefix) and
  symlinks the executable onto the `PATH`, instead of installing a single file.
- Delete the unused `universal-remote.spec` (its `--onefile` / `upx=True` config
  is dead — `packaging/build_binary.sh` drives the build via CLI flags and never
  references the spec).

## Capabilities

### New Capabilities

<!-- none -->

### Modified Capabilities

- `homebrew-distribution`: the standalone binary requirement changes from "a
  single self-contained executable" to a self-contained onedir application
  directory, and gains a startup guarantee (runs directly from its unpacked
  directory, no per-launch extraction to a temp directory). The tap-formula
  requirement is unchanged at the spec level — the formula still puts
  `universal-remote` on the `PATH` and passes `--version`; only its install
  mechanism (dir + symlink) changes, which is captured in design/tasks.

## Impact

- `packaging/build_binary.sh` — `--onefile` → `--onedir`.
- `.github/workflows/release.yml` — smoke-test path becomes
  `./dist/universal-remote/universal-remote --version`; the `tar -C dist ...
  universal-remote` step already archives whatever `universal-remote` is (file or
  directory), so it needs no change.
- `praxder/homebrew-tap` `Formula/universal-remote.rb` (external repo) — `install`
  block must install the onedir tree and symlink the executable into `bin`. The
  release workflow's `sed`-based version/url/sha256 rewrite is unaffected.
- `universal-remote.spec` — deleted.
- No application/runtime code changes; no dependency changes.
