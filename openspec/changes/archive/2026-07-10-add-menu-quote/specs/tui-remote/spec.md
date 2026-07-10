## ADDED Requirements

### Requirement: Landing menu shows a movie/TV quote

The entry menu SHALL display one famous movie or TV quote with attribution beneath the two mode buttons. The attribution SHALL read `— <character>, <source>`. A quote provider selects the quote once per launch. When no quote is available, the menu MUST render without a quote row and MUST NOT fail.

#### Scenario: Quote shown beneath the mode buttons

- **WHEN** the application starts and a quote is available
- **THEN** the menu displays the quote text with an attribution reading `— <character>, <source>` beneath the Manage Devices and Use Remote buttons

#### Scenario: No quote available

- **WHEN** the application starts and no quote is available
- **THEN** the menu renders the mode buttons without a quote row and does not fail

#### Scenario: Quote chosen once per launch

- **WHEN** the menu is shown for the current session
- **THEN** the quote provider is consulted once and the same quote remains for that session
