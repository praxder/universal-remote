## MODIFIED Requirements

### Requirement: Homebrew tap formula

The project repository SHALL itself serve as the Homebrew tap, providing a
`universal-remote` formula that installs the released binary, pinned by version
and SHA-256, and guarded to the supported architecture. The formula SHALL live on
the repository's default branch, since Homebrew reads a tap from that branch and
offers users no way to tap another. The formula SHALL place both the
`universal-remote` and the short `ur` command onto the `PATH`, each resolving to
the same installed executable.

Because the repository is not named `homebrew-<tap>`, Homebrew's shorthand cannot
resolve it; the documented install SHALL therefore tap the repository by its
explicit URL before installing.

#### Scenario: Install via the tap
- **WHEN** a user on an arm64 Mac taps the repository by URL (`brew tap rightnowministries/universal-remote https://github.com/RightNowMinistries/universal-remote`) and then runs `brew install rightnowministries/universal-remote/universal-remote`
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

## ADDED Requirements

### Requirement: Formula discoverable inside the application repository

The formula SHALL sit in a directory Homebrew scans for a tap, so that a
repository holding the application's own source tree still resolves as a valid
tap.

#### Scenario: Tapped repository resolves the formula
- **WHEN** the repository is tapped by URL
- **THEN** Homebrew finds the `universal-remote` formula in the repository's formula directory, ignoring the application source tree alongside it
