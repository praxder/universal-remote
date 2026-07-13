## MODIFIED Requirements

### Requirement: Use Remote entry, selection, and pairing
Entering Use Remote SHALL let the user choose a target device, then connect to it. When the chosen device has no stored credential, the application MUST run pairing first, showing on-screen guidance and allowing the user to cancel. When a credential is already stored, it SHALL connect directly. Whenever the application is connecting to a device — whether directly with a stored credential or after pairing — it SHALL display a modal loading spinner overlaid on the device selection, run the connection off the input handler so the interface stays responsive, and allow the user to cancel the connection while it is in progress. When a connection fails, the application SHALL present an error state that names the device and offers Retry and Back, rather than freezing or crashing; choosing Retry SHALL attempt the connection again and choosing Back SHALL return to device selection. With no saved devices, the mode MUST guide the user toward adding one rather than showing an empty remote. The user MUST be able to leave Use Remote and return to the menu.

#### Scenario: Select among multiple devices
- **WHEN** the user opens Use Remote and more than one device is saved
- **THEN** the application presents the devices for selection before showing a remote

#### Scenario: Pair when no credential
- **WHEN** the chosen device has no stored credential
- **THEN** the application runs pairing with on-screen guidance and, on success, stores the credential and connects, opening the remote

#### Scenario: Pairing cancellable
- **WHEN** the user cancels during pairing
- **THEN** the application returns without opening the remote and without storing a credential

#### Scenario: Connect directly with stored credential
- **WHEN** the chosen device already has a stored credential
- **THEN** the application connects and opens the remote without re-pairing

#### Scenario: Loading spinner shown while connecting
- **WHEN** the application is connecting to the chosen device
- **THEN** a modal loading spinner is shown over the device selection until the connection resolves
- **AND** the interface remains responsive rather than appearing frozen

#### Scenario: Connecting is cancellable
- **WHEN** the user cancels while the connection is in progress
- **THEN** the connect attempt stops and the application returns to device selection without opening a remote

#### Scenario: Connect failure offers retry
- **WHEN** connecting to the chosen device fails
- **THEN** the modal shows an error state naming the device with Retry and Back actions
- **AND** no remote is opened

#### Scenario: Retry re-attempts the connection
- **WHEN** the user chooses Retry after a failed connection
- **THEN** the application attempts to connect to the same device again, showing the loading spinner

#### Scenario: Back after failure returns to selection
- **WHEN** the user chooses Back after a failed connection
- **THEN** the application returns to device selection without opening a remote

#### Scenario: No saved devices
- **WHEN** the user opens Use Remote and no devices are saved
- **THEN** the application guides the user to add a device instead of showing a remote

#### Scenario: Exit back to menu
- **WHEN** the user leaves Use Remote
- **THEN** the application returns to the entry menu
