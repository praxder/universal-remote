## 1. Build the onedir binary

- [x] 1.1 In `packaging/build_binary.sh`, change the PyInstaller flag from `--onefile` to `--onedir`; update the trailing `echo` to reference the directory output (`dist/universal-remote/`).
- [x] 1.2 Run `./packaging/build_binary.sh` locally and confirm the output is `dist/universal-remote/` with the launcher at `dist/universal-remote/universal-remote` (and an `_internal/` directory alongside it).
- [x] 1.3 Confirm `./dist/universal-remote/universal-remote --version` prints the version, and that a launch does not create a per-run temp `_MEI*` extraction directory (contrast with the old onefile behavior).

## 2. Remove dead config

- [x] 2.1 Delete `universal-remote.spec` (unreferenced; its `--onefile`/`upx=True` settings are not used by `build_binary.sh`).

## 3. Update the release workflow

- [x] 3.1 In `.github/workflows/release.yml`, change the smoke-test invocation to `./dist/universal-remote/universal-remote --version` (keep the version-match grep).
- [x] 3.2 Confirm the `tar -C dist -czf "$asset" universal-remote` step needs no change (it archives the `universal-remote` directory as-is) and that the extracted tarball contains the onedir tree.

## 4. Update the Homebrew tap formula (external repo `praxder/homebrew-tap`)

- [x] 4.1 In `Formula/universal-remote.rb`, change the `install` block to install the onedir tree into the formula prefix (e.g. `libexec.install Dir["*"]`) and symlink the launcher onto the PATH (e.g. `bin.install_symlink libexec/"universal-remote"`).
- [x] 4.2 Verify the `sed`-based rewrite in the `release.yml` `tap` job still matches (it edits `version`, `url`, and `sha256` lines only — not the `install` block).
- [x] 4.3 Confirm the formula `test do` block still passes: installed `universal-remote --version` matches the formula version without a TTY.

## 5. Verify end to end

- [x] 5.1 Install from the tap on a clean arm64 Mac (or a fresh prefix) and confirm `universal-remote` launches the TUI, discovers/pairs/controls a device, and starts at roughly `uv run` speed rather than ~4s.
- [x] 5.2 Run the existing test suite (`uv run pytest`) to confirm no regressions from the packaging change.
- [x] 5.3 Run `openspec validate switch-frozen-build-to-onedir` and confirm the change validates.
