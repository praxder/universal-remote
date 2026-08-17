## MODIFIED Requirements

### Requirement: Text entry through the device keyboard
The Fire TV adapter SHALL enter text on a Fire TV whose properties do not report the
native platform type by setting the contents of its focused text field, without requiring
the caller to escape any character, and SHALL support characters outside the ASCII range.
It SHALL report text as unsupported when no text field is focused, rather than reporting
success for text the device discarded. Because the device reports success for a write it
discarded, the adapter SHALL confirm a send by reading the field's contents back, and
SHALL NOT decide whether a field can be written to from the device's reported keyboard
state alone. A Fire TV whose properties report the native platform type is covered by the
Vega text-entry requirement instead, and the adapter SHALL NOT apply this path to such a
device.

#### Scenario: Text entered into a focused field
- **WHEN** text is sent over a session to a device that is not the Vega platform, while the device has a focused text field
- **THEN** the field contains that text

#### Scenario: A field that has never been typed into still accepts text
- **WHEN** text is sent to a text field that holds focus but that nothing has yet been typed into, such as the device's search field immediately after it opens
- **THEN** the field contains that text
- **AND** the send is reported as successful

#### Scenario: Success is confirmed from the field, not the reply
- **WHEN** the device answers a text write with a success status but the field does not contain the text
- **THEN** the session reports text-unsupported rather than treating the status as success

#### Scenario: Characters needing no caller escaping
- **WHEN** text containing spaces, punctuation, or non-ASCII characters is sent to a device that is not the Vega platform
- **THEN** the field contains exactly the characters that were sent

#### Scenario: No focused field reports text unsupported
- **WHEN** text is sent while a device that is not the Vega platform has no focused text field
- **THEN** the session reports text-unsupported so the caller can inform the user
- **AND** it does not report the send as successful

#### Scenario: An absent field value reads as empty text
- **WHEN** the device answers a keyboard-state read with the field's contents reported as null rather than as a string
- **THEN** the adapter treats the contents as empty text
- **AND** no caller of the read fails with a type error

## ADDED Requirements

### Requirement: Fire TV platform detection at connect
The Fire TV adapter SHALL determine, once while connecting, whether a Fire TV runs the
Vega platform, so the session it returns holds the text path that device actually
answers. It SHALL read the device's properties route only when the device's own info
reports that route exists, and SHALL treat a reported native platform type as Vega.
Detection SHALL NOT be repeated per keypress, and a properties read that fails SHALL NOT
fail the connection — the session falls back to the keyboard text path, leaving every
key working on a device whose platform could not be established.

#### Scenario: Native platform type selects the Vega text path
- **WHEN** a device's info reports that the properties route exists and that route reports a native platform type
- **THEN** the session entered text through the Vega text path

#### Scenario: A device without the properties route keeps the keyboard path
- **WHEN** a device's info does not report the properties route
- **THEN** the adapter does not request properties
- **AND** the session enters text through the keyboard path

#### Scenario: A failed properties read still yields a session
- **WHEN** a device reports the properties route exists but the read of it fails
- **THEN** connecting still succeeds
- **AND** the session enters text through the keyboard path

### Requirement: Text entry on a Vega Fire TV
The Fire TV adapter SHALL enter text on a Vega by typing it one character at a time over
the device's single-character text route, which appends to the focused field. Because
that route appends, the adapter SHALL type each character at most once: it SHALL make
the remote service ready before the first character rather than re-waking mid-string,
and a failure part-way through a string SHALL be reported as a failure that says part of
the text may already have been typed. The adapter SHALL refuse the whole send, before
typing any character, when the text holds a character the route cannot accept, so a
refused send leaves the field untouched. Because a Vega reports neither which field has
focus nor what a field holds, the adapter SHALL NOT claim a confirmation it cannot
obtain, and SHALL NOT report text as unsupported on the basis of the keyboard state a
Vega reports.

#### Scenario: Text is typed one character at a time
- **WHEN** text is sent over a session to a Vega with a focused text field
- **THEN** the adapter issues one single-character request per character, in the order the characters were given
- **AND** the field contains the characters appended to whatever it already held

#### Scenario: Text the route cannot accept is refused before anything is typed
- **WHEN** text containing a character outside the accepted range is sent to a Vega
- **THEN** the session reports text-unsupported, naming the limitation
- **AND** no character of that text was typed

#### Scenario: A failure part-way through a string is reported as partial
- **WHEN** the device stops answering after some characters of a string have been typed
- **THEN** the session reports the send as failed
- **AND** the failure says part of the text may already have been typed
- **AND** no character is typed a second time

#### Scenario: A Vega send is not gated on the reported keyboard state
- **WHEN** text is sent to a Vega that reports its keyboard state as hidden and its field contents as absent
- **THEN** the send is attempted rather than refused as unsupported
- **AND** a send the device accepts is reported as successful without a read-back

### Requirement: Digit keys on a Vega Fire TV
The Fire TV adapter SHALL send a digit key to a Vega as one character over the
single-character text route, rather than by reading the focused field's contents and
writing them back with the digit appended. A Vega reports no field contents to read
back, so the read-modify-write path cannot serve it.

#### Scenario: A digit key is typed as a single character
- **WHEN** a digit key is sent over a session to a Vega
- **THEN** the adapter issues one single-character request for that digit
- **AND** it does not read the field's contents first

#### Scenario: A digit key on a device reporting no contents does not fail with a type error
- **WHEN** a digit key is sent to a device that reports its field contents as absent
- **THEN** the session either types the digit or reports a domain failure
- **AND** it does not raise a type error out of the adapter
