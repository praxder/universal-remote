## ADDED Requirements

### Requirement: Lone modifier keys cannot be assigned

A shortcut MUST combine any modifier with a base key; a lone modifier press SHALL NOT be assignable. When the capture modal receives a bare modifier key — a left or right Shift, Control, Alt, Super, Hyper, or Meta press, or an ISO level-3 / level-5 shift — the assignment SHALL be refused with an error toast and the action's existing shortcut SHALL be left unchanged. A modifier combined with a base key (for example `ctrl+b`) is a normal candidate shortcut and SHALL be assignable subject to the conflict and reserved-key rules. The set of lone-modifier keys SHALL match the key names the terminal keyboard protocol delivers when a modifier is pressed on its own, so the check matches what the modal actually receives rather than a shorthand the terminal never sends.

#### Scenario: A lone modifier press is refused

- **WHEN** the user activates a row and presses only a modifier key (such as Alt or Shift) in the capture modal
- **THEN** the assignment is refused, the action keeps its previous shortcut, and a toast explains the key cannot be assigned on its own

#### Scenario: A modifier combined with a base key is accepted

- **WHEN** the user activates a row and presses a modifier-plus-key combination such as `ctrl+b` that no other action uses
- **THEN** the combination becomes the action's shortcut, the modal closes, and the row shows it

#### Scenario: The check matches the protocol's delivered names

- **WHEN** the terminal reports a modifier-only press as its protocol key name (such as `left_alt` or `iso_level3_shift`)
- **THEN** that name is recognized as a lone modifier and refused, not treated as an ordinary assignable key

### Requirement: Stale lone-modifier overrides are dropped on load

A lone-modifier key MAY have been persisted as an override before it was rejected — the earlier guard used key names the terminal never delivers, so bare modifiers were assignable and could be saved. When saved shortcut overrides are loaded, any override whose key is a lone modifier SHALL be dropped so it cannot bind a modifier press to an action, and the affected action SHALL revert to its default key. Every override whose key is not a lone modifier SHALL load unchanged. When pruning removes any override, the cleaned override set SHALL be persisted so the stale binding does not reappear on the next run.

#### Scenario: A stale lone-modifier override is dropped

- **WHEN** the application loads saved overrides that bind an action to a lone modifier key
- **THEN** that override is dropped and the action reverts to its default key

#### Scenario: Non-modifier overrides are preserved

- **WHEN** the application loads saved overrides where some keys are lone modifiers and others are ordinary keys or modifier combinations
- **THEN** the ordinary and combination overrides are kept and only the lone-modifier overrides are dropped

#### Scenario: The cleaned set is persisted

- **WHEN** loading drops one or more lone-modifier overrides
- **THEN** the pruned override set is written back so the dropped bindings stay gone on the next run
