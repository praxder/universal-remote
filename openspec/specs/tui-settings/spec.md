# tui-settings Specification

## Purpose
TBD - created by syncing change add-settings-page. Update Purpose after archive.
## Requirements
### Requirement: Settings screen with a banner
The application SHALL provide a Settings screen reached from the home menu. The screen SHALL present a "Settings" ASCII-art banner styled consistently with the other screens' banners (accent-colored, same banner treatment). The user MUST be able to return from the Settings screen to the home menu. Every interactive row on the screen MUST be reachable both by keyboard and by mouse, consistent with the rest of the application.

#### Scenario: Settings screen shows a banner
- **WHEN** the user opens the Settings screen
- **THEN** it displays a "Settings" ASCII-art banner in the accent color

#### Scenario: Return to the menu
- **WHEN** the user leaves the Settings screen
- **THEN** the application returns to the home menu

### Requirement: Theme picker row
The Settings screen SHALL present a Theme row that, when activated, opens the same theme picker the command palette offers, letting the user select any registered theme. The selection SHALL take effect immediately and SHALL be persisted (see the app-preferences capability).

#### Scenario: Theme row opens the picker
- **WHEN** the user activates the Theme row
- **THEN** the built-in theme picker opens listing the available themes

#### Scenario: Selecting a theme applies it
- **WHEN** the user selects a theme from the picker
- **THEN** the application's theme changes immediately

### Requirement: Key Bindings placeholder row
The Settings screen SHALL present a Key Bindings row as a placeholder for a future key-rebinding feature. In this version the row SHALL NOT open a working rebind page; it SHALL make clear that the feature is not yet available (for example, disabled or labeled as coming later).

#### Scenario: Key Bindings row is a placeholder
- **WHEN** the user views the Settings screen
- **THEN** a Key Bindings row is shown that indicates the rebinding feature is not yet available

### Requirement: Third-party licenses link
The Settings screen SHALL present a Third-party licenses row that, when activated, opens the project's generated `THIRD_PARTY_LICENSES.md` on GitHub (the `main` branch) in the user's default web browser.

#### Scenario: Licenses row opens the licenses file
- **WHEN** the user activates the Third-party licenses row
- **THEN** the default browser opens the `THIRD_PARTY_LICENSES.md` file on GitHub's `main` branch

### Requirement: GitHub repository link
The Settings screen SHALL present a row that, when activated, opens the project's GitHub repository homepage (`https://github.com/praxder/universal-remote`) in the user's default web browser.

#### Scenario: Repo row opens the repository
- **WHEN** the user activates the GitHub repository row
- **THEN** the default browser opens the repository homepage

### Requirement: Version label
The Settings screen SHALL display the application's current version, read from the installed package metadata. The version SHALL be shown as a static, non-interactive label that cannot be focused or activated.

#### Scenario: Version is displayed
- **WHEN** the user views the Settings screen
- **THEN** the current application version is shown

#### Scenario: Version is not interactive
- **WHEN** the user navigates the Settings screen by keyboard or mouse
- **THEN** the version label cannot be focused or activated
