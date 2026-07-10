## ADDED Requirements

### Requirement: Human-readable display name
The Samsung Tizen adapter SHALL expose a human-readable display name, "Samsung Tizen", distinct from its platform identifier, so the UI can present the platform without encoding brand knowledge.

#### Scenario: Display name exposed
- **WHEN** the adapter's display name is read
- **THEN** it is "Samsung Tizen"
- **AND** the platform identifier remains "samsung-tizen"
