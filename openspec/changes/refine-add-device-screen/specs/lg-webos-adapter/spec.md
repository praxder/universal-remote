## ADDED Requirements

### Requirement: Human-readable display name
The LG WebOS adapter SHALL expose a human-readable display name, "LG WebOS", distinct from its platform identifier, so the UI can present the platform without encoding brand knowledge.

#### Scenario: Display name exposed
- **WHEN** the adapter's display name is read
- **THEN** it is "LG WebOS"
- **AND** the platform identifier remains "lg-webos"
