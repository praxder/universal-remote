## 1. Console script (pip/uv)

- [x] 1.1 Add `ur = "universal_remote.cli:main"` to `[project.scripts]` in `pyproject.toml`
- [x] 1.2 `uv sync` and verify `uv run ur --version` prints the version

## 2. Frozen binary bundle

- [x] 2.1 Add `ln -sf universal-remote dist/universal-remote/ur` after the PyInstaller call in `packaging/build_binary.sh`
- [x] 2.2 Verify a symlinked launcher resolves `_internal/` (`./ur --version` in the built bundle)

## 3. Homebrew formula (external repo `praxder/homebrew-tap`)

- [x] 3.1 Add `bin.install_symlink libexec/"universal-remote" => "ur"` to the formula's `install` block
- [x] 3.2 Commit + push to the tap repo

## 4. Docs

- [x] 4.1 Update `README.md` install sections (Homebrew, Releases download, from source) to show `ur`

## 5. Verify

- [x] 5.1 `uv run ruff check` and `uv run ruff format --check` pass
- [ ] 5.2 After next release, confirm `ur --version` works from a fresh `brew install`
