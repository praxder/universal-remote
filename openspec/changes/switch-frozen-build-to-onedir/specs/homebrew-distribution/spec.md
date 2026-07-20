## MODIFIED Requirements

### Requirement: Standalone macOS arm64 binary

The project SHALL be packaged into a self-contained application directory (a
PyInstaller `--onedir` bundle) for macOS on Apple Silicon (arm64), whose
executable runs without a user-provided Python interpreter or `uv`, and that
retains full runtime behavior — device discovery, pairing, and remote control
across all bundled adapters. The bundle SHALL run directly from its unpacked
directory and MUST NOT extract itself to a temporary directory on each launch.

#### Scenario: Binary runs on a clean machine
- **WHEN** the binary is executed on an arm64 Mac with no Python toolchain installed
- **THEN** the app launches, discovers devices on the local network, and can pair and control a TV, identical to the `uv run` behavior

#### Scenario: Bundled framework and dynamic-import dependencies are present
- **WHEN** the binary performs discovery and pairing
- **THEN** no missing-module or missing-data-file error occurs for Textual CSS or for the dynamic-import dependencies (`zeroconf`, `pyatv`, `protobuf`, `androidtvremote2`, `adb-shell`)

#### Scenario: Launch does not unpack a bundle to a temporary directory
- **WHEN** the frozen binary is launched from its installed application directory
- **THEN** it runs the code in place, without creating a new per-launch temporary extraction directory, so startup does not pay a bundle-unpacking cost on every run
