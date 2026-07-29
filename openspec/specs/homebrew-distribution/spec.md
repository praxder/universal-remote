# homebrew-distribution Specification

## Purpose
Package the app as a standalone macOS arm64 binary installable via the praxder/homebrew-tap formula, with non-interactive `--version`/`--help` and a short `ur` alias.
## Requirements
### Requirement: Non-interactive version and help flags

The CLI entry point (`universal_remote.cli:main`) SHALL handle `--version` and
`--help` and exit successfully **before** the Textual application is started, so the
binary is usable in a non-TTY environment (CI, the Homebrew formula test). The
`--version` output MUST include the package version resolved at runtime.

#### Scenario: Version flag prints and exits without launching the TUI
- **WHEN** the binary is invoked as `universal-remote --version` with no controlling terminal
- **THEN** it prints a line containing the current version (e.g. `universal-remote 0.2.0`) to stdout and exits with status 0 without constructing or running the Textual app

#### Scenario: Help flag prints usage and exits
- **WHEN** the binary is invoked as `universal-remote --help`
- **THEN** it prints usage text and exits with status 0 without launching the TUI

#### Scenario: No arguments launches the remote
- **WHEN** the binary is invoked with no arguments in a terminal
- **THEN** it registers the adapters and launches the Textual app as before

### Requirement: Standalone macOS arm64 binary

The project SHALL be packaged into a self-contained application directory (a
PyInstaller `--onedir` bundle) for macOS on Apple Silicon (arm64), whose
executable runs without a user-provided Python interpreter or `uv`, and that
retains full runtime behavior — device discovery, pairing, and remote control
across all bundled adapters. The bundle SHALL run directly from its unpacked
directory and MUST NOT extract itself to a temporary directory on each launch.
The bundle SHALL also provide a `ur` symlink beside the `universal-remote`
launcher, resolving to the same executable, and this symlink MUST survive
packaging into the release tarball.

#### Scenario: Binary runs on a clean machine
- **WHEN** the binary is executed on an arm64 Mac with no Python toolchain installed
- **THEN** the app launches, discovers devices on the local network, and can pair and control a TV, identical to the `uv run` behavior

#### Scenario: Bundled framework and dynamic-import dependencies are present
- **WHEN** the binary performs discovery and pairing
- **THEN** no missing-module or missing-data-file error occurs for Textual CSS or for the dynamic-import dependencies (`zeroconf`, `pyatv`, `protobuf`, `androidtvremote2`, `adb-shell`)

#### Scenario: Launch does not unpack a bundle to a temporary directory
- **WHEN** the frozen binary is launched from its installed application directory
- **THEN** it runs the code in place, without creating a new per-launch temporary extraction directory, so startup does not pay a bundle-unpacking cost on every run

#### Scenario: The `ur` alias launches the same program
- **WHEN** the bundle's `ur` symlink is invoked (e.g. `./ur --version`)
- **THEN** it resolves `_internal/` via its real target and behaves identically to invoking `universal-remote`, printing the same version output

### Requirement: Homebrew tap formula

A Homebrew tap `praxder/homebrew-tap` SHALL provide a `universal-remote` formula
that installs the released binary, pinned by version and SHA-256, and guarded to the
supported architecture. The formula SHALL place both the `universal-remote` and
the short `ur` command onto the `PATH`, each resolving to the same installed
executable.

#### Scenario: Install via the tap
- **WHEN** a user runs `brew install praxder/tap/universal-remote` on an arm64 Mac
- **THEN** Homebrew downloads the pinned release asset, verifies its SHA-256, installs the executable onto the PATH, and `universal-remote --version` reports the installed version

#### Scenario: Short alias is installed onto the PATH
- **WHEN** the formula finishes installing on an arm64 Mac
- **THEN** `ur --version` reports the installed version, identical to `universal-remote --version`

#### Scenario: Unsupported architecture is rejected clearly
- **WHEN** a user on an Intel (x86_64) Mac attempts to install the formula
- **THEN** Homebrew refuses with a clear architecture error rather than installing a non-functional binary

#### Scenario: Formula self-test passes
- **WHEN** Homebrew runs the formula `test do` block
- **THEN** the installed binary responds to `--version` with output matching the formula's version, without requiring a TTY

