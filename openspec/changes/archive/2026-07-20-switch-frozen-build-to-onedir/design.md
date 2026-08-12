## Context

The frozen macOS binary is built with PyInstaller `--onefile` via
`packaging/build_binary.sh`, published as a `.tar.gz` GitHub Release asset by
`.github/workflows/release.yml`, and installed by the `universal-remote` formula
in the external `praxder/homebrew-tap` repo.

A `--onefile` binary is a self-extracting archive: on every launch its bootloader
unpacks the whole bundle (~29MB here) into a fresh temporary directory
(`_MEIxxxxxx`), runs from there, then deletes it. Measured cost is ~4s cold and
dominated by I/O, not CPU (imports total ~0.3s; the Textual app mount is already
non-blocking). Because each launch writes the extracted Mach-O files to new temp
inodes, a quarantined download (GitHub/Homebrew) also incurs a Gatekeeper/XProtect
re-scan of those files on **every** launch, not just the first — which is why a
downloaded binary (~4s) is slower than a locally built, unquarantined one.

The committed `universal-remote.spec` is dead: `build_binary.sh` invokes
`pyinstaller` with CLI flags and never passes the spec, so the spec's `--onefile`
and `upx=True` settings have no effect on the shipped artifact.

## Goals / Non-Goals

**Goals:**
- Frozen startup at roughly `uv run` speed (~0.3–1s) instead of ~4s.
- Eliminate the per-launch bundle extraction and the resulting per-launch
  Gatekeeper re-scan on quarantined downloads.
- Keep the release/distribution surface as close to today as possible (same
  `.tar.gz` asset shape, same `sed` rewrite in the tap job).

**Non-Goals:**
- Code signing with a Developer ID or Apple notarization (separate concern; only
  reduces the first-launch Gatekeeper cost, not the base extraction cost, and
  carries an annual-account dependency).
- Reducing import time or lazy-loading adapters (imports are ~0.3s — not the
  bottleneck).
- Any application/runtime behavior change.

## Decisions

**Decision: Use PyInstaller `--onedir` instead of `--onefile`.**
`--onedir` produces `dist/universal-remote/` containing the launcher executable
plus an `_internal/` directory of dependencies. The launcher runs the code in
place — no per-launch extraction, and stable inodes so Gatekeeper assesses the
files once (on first launch / install) and caches the result.
- *Alternative — codesign + notarize onefile:* removes only the Gatekeeper delta,
  not the ~seconds of per-launch extraction, and requires a paid Apple Developer
  account. Rejected: higher cost, smaller win.
- *Alternative — lazy imports / trimmed deps:* imports are ~0.3s; even eliminated
  entirely this cannot explain or fix the ~4s. Rejected as ineffective.

**Decision: Keep the `.tar.gz` asset and the existing tar step.**
`tar -C dist -czf "$asset" universal-remote` archives whatever `universal-remote`
is under `dist/` — a file today, a directory after this change — so the packaging
step needs no change. The consumer (Homebrew) already unpacks a tarball.

**Decision: Homebrew formula installs the directory and symlinks the executable.**
The prebuilt-bundle idiom: install the onedir tree into the formula prefix (e.g.
`libexec`) and symlink the launcher onto the `PATH` (`bin`). This preserves the
observable contract (`universal-remote` on `PATH`, `--version` works, arch guard),
so no `homebrew-distribution` scenario for the tap changes. The formula lives in
the external `praxder/homebrew-tap` repo; the release workflow's `sed`-based
version/url/sha256 rewrite does not touch the `install` block, so it keeps working.

**Decision: Delete `universal-remote.spec`.**
It is unreferenced dead config whose `--onefile`/`upx=True` values contradict this
change and could mislead a future reader into thinking they drive the build.

## Risks / Trade-offs

- **The tap formula lives in a separate repo** → the `install`-block edit must be
  made in `praxder/homebrew-tap`, not this repo. This change proposal covers the
  reasoning and the required shape; the actual formula edit is a task performed
  against that repo. The CI `tap` job's `sed` rewrite is unaffected.
- **Exact onedir top-level layout is PyInstaller-version-specific** (6.x nests
  dependencies under `_internal/` with the launcher at the directory root) → verify
  the built layout before finalizing the formula's `install`/symlink and the CI
  smoke-test path; anchor both on the launcher at
  `dist/universal-remote/universal-remote`.
- **First launch of a quarantined onedir still pays a one-time Gatekeeper scan** →
  acceptable; it is amortized across all later launches (the whole point). An
  optional `xattr`-strip in the formula could remove even the first-launch cost but
  is out of scope here.
- **Larger extracted footprint on disk** (unpacked tree vs single file) → negligible
  for a dev CLI; the download size is comparable since both are gzip-compressed.

## Migration Plan

No user-data or config migration. The change is build/packaging only:
1. Flip `build_binary.sh` to `--onedir`; delete `universal-remote.spec`.
2. Update the CI smoke-test path in `release.yml`.
3. Update the `praxder/homebrew-tap` formula `install` block (external repo).
Rollback is reverting the flag and formula edit; no released artifacts need
recall — a subsequent release supersedes the prior onefile asset.

## Open Questions

- Confirm the built onedir top-level layout on the CI PyInstaller version so the
  formula's `install`/symlink lines and the smoke-test path are exact.
