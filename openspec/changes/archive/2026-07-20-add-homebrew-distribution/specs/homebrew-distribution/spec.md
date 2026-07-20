## ADDED Requirements

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

The project SHALL be packaged into a single self-contained executable for macOS on
Apple Silicon (arm64) that runs without a user-provided Python interpreter or `uv`,
and that retains full runtime behavior — device discovery, pairing, and remote
control across all bundled adapters.

#### Scenario: Binary runs on a clean machine
- **WHEN** the binary is executed on an arm64 Mac with no Python toolchain installed
- **THEN** the app launches, discovers devices on the local network, and can pair and control a TV, identical to the `uv run` behavior

#### Scenario: Bundled framework and dynamic-import dependencies are present
- **WHEN** the binary performs discovery and pairing
- **THEN** no missing-module or missing-data-file error occurs for Textual CSS or for the dynamic-import dependencies (`zeroconf`, `pyatv`, `protobuf`, `androidtvremote2`, `adb-shell`)

### Requirement: Homebrew tap formula

A Homebrew tap `praxder/homebrew-tap` SHALL provide a `universal-remote` formula
that installs the released binary, pinned by version and SHA-256, and guarded to the
supported architecture.

#### Scenario: Install via the tap
- **WHEN** a user runs `brew install praxder/tap/universal-remote` on an arm64 Mac
- **THEN** Homebrew downloads the pinned release asset, verifies its SHA-256, installs the executable onto the PATH, and `universal-remote --version` reports the installed version

#### Scenario: Unsupported architecture is rejected clearly
- **WHEN** a user on an Intel (x86_64) Mac attempts to install the formula
- **THEN** Homebrew refuses with a clear architecture error rather than installing a non-functional binary

#### Scenario: Formula self-test passes
- **WHEN** Homebrew runs the formula `test do` block
- **THEN** the installed binary responds to `--version` with output matching the formula's version, without requiring a TTY
