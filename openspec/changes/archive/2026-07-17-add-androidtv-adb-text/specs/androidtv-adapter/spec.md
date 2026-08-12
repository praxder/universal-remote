## ADDED Requirements

### Requirement: Opt-in ADB text routing

The Android TV adapter SHALL support an optional, per-device ADB text path. When a device is opted into ADB text, the adapter SHALL send text by invoking the system `adb` binary's `input text` command against that device rather than over Remote v2. When a device is not opted in, the adapter SHALL continue to send text over Remote v2. Text sent over the ADB path SHALL be escaped so that spaces and shell-special characters are preserved as typed.

#### Scenario: Opted-in device sends text over ADB

- **WHEN** a device opted into ADB text sends text through its session
- **THEN** the adapter invokes the `adb` binary's `input text` command with the escaped text and does not use Remote v2 for that send

#### Scenario: Non-opted-in device sends text over Remote v2

- **WHEN** a device that is not opted into ADB text sends text through its session
- **THEN** the adapter sends the text over Remote v2 as before

#### Scenario: Text with spaces and special characters is preserved

- **WHEN** an opted-in device sends text containing spaces or shell-special characters
- **THEN** the escaped `input text` argument reproduces the intended string on the device

### Requirement: ADB target resolution via mDNS

Because a device's wireless-debugging connect port is ephemeral, the adapter SHALL resolve the device's current ADB address each session by querying mDNS and matching the entry by the device's IP address, then connect to the resolved address before sending text. Resolution SHALL NOT depend on any previously stored port.

#### Scenario: Current address resolved before sending

- **WHEN** an opted-in device sends text and its ADB address has not yet been resolved this session
- **THEN** the adapter resolves the device's current address from mDNS by IP and connects to it before sending

### Requirement: ADB text fallback when unavailable

When a device is opted into ADB text but the ADB path is unavailable — the `adb` binary is missing, or the device cannot be reached over ADB (for example, wireless debugging is off) — the adapter SHALL fall back to sending the text over Remote v2 and SHALL signal that the ADB text path was unavailable, rather than silently discarding the text.

#### Scenario: adb binary missing falls back to Remote v2

- **WHEN** an opted-in device sends text and the `adb` binary cannot be found
- **THEN** the adapter sends the text over Remote v2 and signals that the ADB text path was unavailable

#### Scenario: Device unreachable over ADB falls back to Remote v2

- **WHEN** an opted-in device sends text and the device cannot be reached over ADB
- **THEN** the adapter sends the text over Remote v2 and signals that the ADB text path was unavailable

### Requirement: One-time ADB wireless-debugging pairing

The Android TV adapter SHALL support a one-time ADB pairing over wireless debugging, taking a pairing address and a pairing code and performing the pairing via the `adb` binary. This pairing is distinct from Remote v2 PIN pairing and establishes the trust the `adb` server persists for later connections. A failed pairing SHALL be reported rather than silently marking the device as opted in.

#### Scenario: Successful ADB pairing

- **WHEN** the adapter is given a valid pairing address and code and the `adb` pairing succeeds
- **THEN** the adapter reports success so the device can be recorded as opted into ADB text

#### Scenario: Failed ADB pairing is reported

- **WHEN** the adapter is given a pairing address and code and the `adb` pairing fails
- **THEN** the adapter reports the failure and the device is not marked as opted into ADB text
