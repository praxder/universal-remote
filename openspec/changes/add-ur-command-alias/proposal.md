## Why

`universal-remote` is a long name to type at a terminal for a tool meant to be
launched constantly. A short `ur` alias makes the everyday invocation two
keystrokes, and shipping it with the package means every user gets it without
hand-editing a shell profile.

## What Changes

- Add a `ur` console-script entry point alongside `universal-remote` so
  pip/uv installs put both names on `PATH`.
- Create a `ur` symlink beside the frozen-binary launcher during the packaging
  build, so the release tarball (and thus any direct-download or Homebrew user)
  carries the alias.
- Point the Homebrew formula at a second `bin.install_symlink` for `ur`
  (in the separate `praxder/homebrew-tap` repo).
- Update `README.md` install sections to show `ur` as the short form across all
  three channels.

No behavior change to the program itself — `ur` and `universal-remote` are the
same entry point.

## Capabilities

### New Capabilities

<!-- none -->

### Modified Capabilities

- `homebrew-distribution`: the standalone-binary and Homebrew-formula
  requirements now also provide the `ur` alias — the frozen bundle ships a `ur`
  symlink, and the formula links both `ur` and `universal-remote` onto `PATH`.

## Impact

- `pyproject.toml` — `[project.scripts]` gains `ur`.
- `packaging/build_binary.sh` — adds the in-bundle `ur` symlink.
- `README.md` — install docs.
- `praxder/homebrew-tap` `Formula/universal-remote.rb` (external repo) — extra
  `bin.install_symlink` for `ur`.
- No new dependencies; no runtime behavior change.
