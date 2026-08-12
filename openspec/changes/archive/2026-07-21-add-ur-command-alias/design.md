## Context

`universal-remote` ships through three channels: the pip/uv console script, a
frozen PyInstaller `--onedir` macOS bundle distributed as a tarball, and a
Homebrew formula (in the external `praxder/homebrew-tap` repo) that installs that
bundle. A `ur` alias must reach users of all three, and "survive publishing" —
i.e. be produced by the build/release pipeline, not a per-user shell edit.

## Goals / Non-Goals

**Goals:**
- `ur` invokes the same program as `universal-remote` in every channel.
- The alias is produced by the packaging/build pipeline, not hand-maintained.
- Zero runtime behavior change; one entry point, two names.

**Non-Goals:**
- No new binary or duplicated bootloader.
- No shell-profile aliasing (does not survive publishing; not per-user automatic).
- No cross-platform packaging beyond the existing arm64 macOS target.

## Decisions

**Console script (pip/uv): second `[project.scripts]` entry.**
Add `ur = "universal_remote.cli:main"` alongside the existing name. Both map to
the same callable, so hatchling generates two wrappers. Alternative — a shell
alias in docs — rejected: not installed automatically.

**Frozen binary: symlink in the bundle, created in `build_binary.sh`.**
`ln -sf universal-remote dist/universal-remote/ur`. The onedir bootloader
resolves `_internal/` via the symlink's real target, so `./ur` works identically
(verified empirically). Placed in `build_binary.sh` rather than `release.yml` so
local `./packaging/build_binary.sh` builds also get the alias; `tar` preserves
the symlink into the release asset. Alternative — a second `EXE()` target in the
`.spec` — rejected: duplicates the ~megabyte bootloader for no benefit.

**Homebrew: a second `bin.install_symlink` pointing at the real launcher.**
`bin.install_symlink libexec/"universal-remote" => "ur"`. Points at the real
launcher name, not the in-bundle `ur` symlink, so the formula is self-contained
and does not depend on the tarball carrying the symlink. Lives in the external
tap repo, so it is a separate commit from the rest of this change.

## Risks / Trade-offs

- [`ur` name collision on a user's `PATH`] → It is a common enough short name to
  clash with a local script. Accepted: Homebrew/console-script installs are
  explicit user actions, and the full `universal-remote` name remains available.
- [Tap edit lives in a separate repo] → The formula change can lag the code
  change. Mitigation: land it in the same session; the alias in channels ① and ②
  is independent and ships regardless.
- [Symlink not preserved by some extraction tool] → `tar`/`brew` preserve
  symlinks; the formula's own `bin.install_symlink` is the authoritative source
  for Homebrew users, so the in-bundle symlink is not load-bearing for that path.
