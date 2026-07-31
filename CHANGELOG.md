# CHANGELOG

<!-- version list -->

## v2.0.0 (2026-07-31)

### Bug Fixes

- **androidtv**: Send text over Remote v2, drop ADB
  ([`45dba31`](https://github.com/praxder/universal-remote/commit/45dba31779a0437f80d1f72fe019e5f1d5cc87f4))

- **androidtv**: Stop reporting discarded text as sent
  ([`bcb64b4`](https://github.com/praxder/universal-remote/commit/bcb64b49fb6a3e35b11454070849ccacb2135210))

- **firetv**: Confirm a text send from the field, not its state
  ([`744c18e`](https://github.com/praxder/universal-remote/commit/744c18e76c5902c2199bbc830fa3360ccf3c0891))

- **firetv**: Name the client when requesting a pairing PIN
  ([`a0c2bdd`](https://github.com/praxder/universal-remote/commit/a0c2bdd37ccfda56af3bed57c910f1434b9b8fcb))

### Documentation

- Name the Fire TV transport as Amazon's private API
  ([`5ab22a5`](https://github.com/praxder/universal-remote/commit/5ab22a50621e7969ffec07e0f969a56b0079215c))

- Show the reorder buttons in the device list screenshot
  ([`41b29c3`](https://github.com/praxder/universal-remote/commit/41b29c3bd2ea3cab5dd9698ac9f249185f889a36))

- Tie the ADB text path to Fire TV only
  ([`3ef4a4a`](https://github.com/praxder/universal-remote/commit/3ef4a4a796ae12b2c1395b57f444712bab5a782f))

- **openspec**: Archive the Android TV Remote v2 text fix
  ([`fff24ae`](https://github.com/praxder/universal-remote/commit/fff24ae25bb2f2a845dce7e74fc87a9b0e68c308))

- **openspec**: Archive the device list reordering change
  ([`23ecbf0`](https://github.com/praxder/universal-remote/commit/23ecbf0e53f288d4fa55a2c801f531e6d78fc8ef))

- **openspec**: Archive the Fire TV REST transport change
  ([`1b42759`](https://github.com/praxder/universal-remote/commit/1b427593c4c71136cfedf6a24b677b7fdee6ecd5))

- **openspec**: Complete Android TV Remote v2 text verification
  ([`b442b96`](https://github.com/praxder/universal-remote/commit/b442b96cc7135df9eff93a31ae5f6e1dc292318b))

- **openspec**: Drop the withdrawn ADB opt-in store scenario
  ([`ecafde5`](https://github.com/praxder/universal-remote/commit/ecafde5a53de87f349bd2db0928d6a9339bf49e4))

- **openspec**: Propose Android TV Remote v2 text fix
  ([`ba7a46f`](https://github.com/praxder/universal-remote/commit/ba7a46f5bf6727c9376b99148cfd8f4fca6bf21a))

- **openspec**: Propose device list reordering
  ([`6e55cb7`](https://github.com/praxder/universal-remote/commit/6e55cb7f842ab802001c478ab3b3ad0ee030fa1d))

- **openspec**: Propose Fire TV REST transport
  ([`327dc01`](https://github.com/praxder/universal-remote/commit/327dc01004caa5e59c22563829d22aa0fe29028f))

- **openspec**: Record the verified focus-loss text failure
  ([`14e6070`](https://github.com/praxder/universal-remote/commit/14e6070d2ca5d1c829b532a4c873ef5f72bbf3c0))

### Features

- **devices**: Reorder saved devices from the list
  ([`519de7b`](https://github.com/praxder/universal-remote/commit/519de7b86a81b19f1d2d680123c78bdf0ecfe53c))

- **firetv**: Drive the REST remote API, drop ADB
  ([`d216555`](https://github.com/praxder/universal-remote/commit/d216555bfbcad7d4b6dd65e57c92e0282ed6df7a))


## v1.4.0 (2026-07-29)

### Bug Fixes

- **tui**: Bound Android TV connect and handle unsupported-platform devices
  ([`3c9d8a6`](https://github.com/praxder/universal-remote/commit/3c9d8a60b6ee431d5d180d02b2e19324d5151fc0))

- **tui**: Make delete buttons use default styling
  ([`33feccf`](https://github.com/praxder/universal-remote/commit/33feccf59cd6e2d2de73b67234c5696bccefb030))

- **tui**: Reject lone-modifier keyboard shortcuts
  ([`e50aa4a`](https://github.com/praxder/universal-remote/commit/e50aa4ae0a844f9625489913012214d4a638c57d))

- **tui**: Stop the docked settings bar from swallowing menu clicks
  ([`4f1a864`](https://github.com/praxder/universal-remote/commit/4f1a8642bcbf8bc70daf17673d43b23ffc127865))

### Chores

- **openspec**: Archive reject-lone-modifier-shortcuts and sync specs
  ([`2973455`](https://github.com/praxder/universal-remote/commit/2973455a214153cb22ba9b93865cff43fc6823a8))

### Documentation

- **macros**: Promote macros spec deltas and archive the change
  ([`ae5f3b1`](https://github.com/praxder/universal-remote/commit/ae5f3b11dc8665dcb18600143523a017db6f2cd9))

- **macros**: Updated docs and screenshots for macros
  ([`4d7fd94`](https://github.com/praxder/universal-remote/commit/4d7fd942ffc3bd0b815157a61ef2607c778c5548))

- **openspec**: Abort macro playback on a failed step
  ([`a7b8b8f`](https://github.com/praxder/universal-remote/commit/a7b8b8ffb3fa837e578dd86b1f96d5d9a29aadef))

- **openspec**: Propose macros capability
  ([`aadf3b1`](https://github.com/praxder/universal-remote/commit/aadf3b16a50f9dcb3813d08ffaa849fea61e8293))

- **openspec**: Propose rejecting lone-modifier shortcuts
  ([`1f2b95f`](https://github.com/praxder/universal-remote/commit/1f2b95f286f7e351ab58638adb5422c945c9a264))

- **openspec**: Reconcile specs with implementation and fill Purpose stubs
  ([`cd2b9d1`](https://github.com/praxder/universal-remote/commit/cd2b9d1d27db355f7ba58a0732f0378fd124b147))

### Features

- **tui**: Confirm before deleting a macro
  ([`55cc648`](https://github.com/praxder/universal-remote/commit/55cc64816abb6c8ebaa1dc056029c9a7d7bbd6dd))

- **tui**: Explain the recording state before it starts
  ([`b31e466`](https://github.com/praxder/universal-remote/commit/b31e466c77b10004f14a257672dd89f394681cee))

- **tui**: Give the macro detail modal room to breathe
  ([`ea75e17`](https://github.com/praxder/universal-remote/commit/ea75e171f693d7f074d75c27fe98b97759b115f8))

- **tui**: Mark Macros as an app control, not a key
  ([`d52159a`](https://github.com/praxder/universal-remote/commit/d52159a51239bdd099f3dc0f26976aa1ff5c46df))

- **tui**: Name the step in the playback progress line
  ([`ad082b3`](https://github.com/praxder/universal-remote/commit/ad082b31223c47ab89c67609981b853190d28a52))

- **tui**: Pace each macro with its own default pause
  ([`e2b4f47`](https://github.com/praxder/universal-remote/commit/e2b4f47f311ae035cbf28418f4f60cbeccaa2bf4))

- **tui**: Pulse the recording indicator while a macro records
  ([`e834611`](https://github.com/praxder/universal-remote/commit/e834611945067789691e9b680f8d69683baa8be2))

- **tui**: Record and replay macros
  ([`6ffc81d`](https://github.com/praxder/universal-remote/commit/6ffc81df15feab35a1de022ca6b84018c4f82564))

- **tui**: Run a macro from its detail modal
  ([`35b9f41`](https://github.com/praxder/universal-remote/commit/35b9f41914d27f5785ae184e09de075e7fee4d85))


## v1.3.0 (2026-07-24)

### Bug Fixes

- **tui**: Center settings rows, pad home button, add vim nav
  ([`519f791`](https://github.com/praxder/universal-remote/commit/519f7913dabb11d19b520adb4920e29b2f678f19))

- **tui**: Refine custom button actions after first-pass review
  ([`2f40881`](https://github.com/praxder/universal-remote/commit/2f40881b87a79f7f1ba9359642f349cbf79175dc))

- **tui**: Refine custom button edit-mode and action prefill
  ([`f7b841b`](https://github.com/praxder/universal-remote/commit/f7b841b468381244f4635c8c61232e5c335bc810))

### Chores

- **openspec**: Archive add-custom-button-actions and sync specs
  ([`ed390c0`](https://github.com/praxder/universal-remote/commit/ed390c0a4cc76b4d826c61829f5f96191bd85964))

- **openspec**: Archive add-custom-keyboard-shortcuts and sync specs
  ([`320f646`](https://github.com/praxder/universal-remote/commit/320f6468b33146f0ebd1554f95d250b4416e724f))

- **openspec**: Archive add-custom-remote-buttons and sync specs
  ([`20a64e7`](https://github.com/praxder/universal-remote/commit/20a64e740a3fbf4d3b941f38e3171508309eb5b6))

### Code Style

- **settings**: Minor padding update
  ([`ef0daf7`](https://github.com/praxder/universal-remote/commit/ef0daf7bfefcf39e3b055b188e9b5e25caac0247))

### Documentation

- Add Settings screenshot and refresh home screenshot
  ([`cd9e275`](https://github.com/praxder/universal-remote/commit/cd9e275133e214d079927542ee92759fcccd1f73))

- **openspec**: Archive add-settings-page
  ([`0fcd598`](https://github.com/praxder/universal-remote/commit/0fcd59891d02abb123b6fa784e6842cf88c6493a))

- **openspec**: Propose add-settings-page
  ([`ee2c6db`](https://github.com/praxder/universal-remote/commit/ee2c6dbed45ea2ccde6ae09beb79af3ca0dca198))

- **openspec**: Propose custom button actions (phase 2)
  ([`526faf9`](https://github.com/praxder/universal-remote/commit/526faf9b31cdbc36c3621dfc9a2c00f6a7e3c782))

- **openspec**: Propose custom keyboard shortcuts change
  ([`7357527`](https://github.com/praxder/universal-remote/commit/7357527042c30537abc109237694e604bf714feb))

- **openspec**: Propose custom remote buttons (phase 1)
  ([`9ae8f4e`](https://github.com/praxder/universal-remote/commit/9ae8f4ed4a188e3cd8780f6dac85492d77bb995e))

- **openspec**: Refine custom remote buttons before archive
  ([`ed8cff0`](https://github.com/praxder/universal-remote/commit/ed8cff0b74ac74c87c3b56b568ff96f90388385e))

- **openspec**: Refresh custom-button-actions after phase 1 archive
  ([`747a75c`](https://github.com/praxder/universal-remote/commit/747a75c9d099290aba762e1a6c5d6a09949f74ed))

- **openspec**: Resolve open questions for custom-button-actions
  ([`a2343dd`](https://github.com/praxder/universal-remote/commit/a2343ddbc804b08b3d28d2495a8a1a1dad1331bf))

- **openspec**: Resolve open questions in keyboard shortcuts proposal
  ([`50cb3db`](https://github.com/praxder/universal-remote/commit/50cb3dbf67879fd8e83624a8f9474aa9c2d8a65f))

- **openspec**: Scope custom button action jointly with title
  ([`c451465`](https://github.com/praxder/universal-remote/commit/c4514650dc097116884140a4937a57ebe6917945))

- **readme**: Document keyboard shortcuts screen and refresh screenshots
  ([`e83c6c3`](https://github.com/praxder/universal-remote/commit/e83c6c302ac0b3b2be249edc877f634375ed488c))

- **readme**: Refresh remote screenshots for custom buttons
  ([`2e630cc`](https://github.com/praxder/universal-remote/commit/2e630cc8e5ae5415752486987ab37c6fa0d1b2bd))

### Features

- Add Settings page with persisted theme preference
  ([`fc029e6`](https://github.com/praxder/universal-remote/commit/fc029e604e19e726839f11c00ed5320f343db2c7))

- **tui**: Add custom remote buttons and modal text entry
  ([`1e4ba2c`](https://github.com/praxder/universal-remote/commit/1e4ba2c866553802859cabf969561d089aab9c75))

- **tui**: Add customizable keyboard shortcuts
  ([`3da95f9`](https://github.com/praxder/universal-remote/commit/3da95f90f21807d93f4d6f2b7a117182a740b09b))

- **tui**: Add j/k row navigation to shortcuts screen and palette view
  ([`f3336d1`](https://github.com/praxder/universal-remote/commit/f3336d1c1d5d4c9ccef9704a14ab26dbd2cbef48))

- **tui**: Add Run Custom Script action for custom buttons
  ([`a67abd5`](https://github.com/praxder/universal-remote/commit/a67abd5e89724825813ebf72213c89bc6d2fe115))

- **tui**: Global shortcuts, ESC-assignable capture, palette view
  ([`f26d97e`](https://github.com/praxder/universal-remote/commit/f26d97eb6cdbd92f87b6eb70be6288cdde3e2bd2))

- **tui**: Group shortcuts table by surface; tidy capture modal copy
  ([`259ddd8`](https://github.com/praxder/universal-remote/commit/259ddd8164a35e5f50f93b47e1b043a6400d3815))

- **tui**: Refine custom remote buttons (shortcuts, fixes)
  ([`0ae90d6`](https://github.com/praxder/universal-remote/commit/0ae90d6a3ef47d7c8463ba0befb5c8b4a1330e84))


## v1.2.0 (2026-07-21)

### Documentation

- **openspec**: Archive add-edit-device-delete-button
  ([`0502edd`](https://github.com/praxder/universal-remote/commit/0502edd7a02f9c7e2397ac0978f861e1d15c383a))

- **openspec**: Archive add-ur-command-alias
  ([`59cb267`](https://github.com/praxder/universal-remote/commit/59cb2671fe42c0d03daf87fce3cd19bccb5d8f26))

- **openspec**: Archive switch-frozen-build-to-onedir
  ([`a12ddfd`](https://github.com/praxder/universal-remote/commit/a12ddfd3c3a18eacca775100ba7995904afff8b3))

- **openspec**: Archive switch-samsung-discovery-to-mdns
  ([`528ad61`](https://github.com/praxder/universal-remote/commit/528ad61f3e88f0438adf0b1a38094ecab183ece4))

- **openspec**: Archive update-remote-status-bar
  ([`5bf7542`](https://github.com/praxder/universal-remote/commit/5bf75426a2f3373238c815adda7834c25fb4588a))

- **openspec**: Propose add-ur-command-alias
  ([`5d2257a`](https://github.com/praxder/universal-remote/commit/5d2257a420d8287a6263906bfdad5a1788d3054a))

- **openspec**: Propose delete button on edit device screen
  ([`ae2fb09`](https://github.com/praxder/universal-remote/commit/ae2fb097246e79ac2980e92443b482ba3d3982a0))

- **openspec**: Propose switching Samsung discovery to mDNS
  ([`e1c99c5`](https://github.com/praxder/universal-remote/commit/e1c99c500b0af12da94ce3a7f207231f2632b634))

- **openspec**: Propose update remote status bar text
  ([`c672470`](https://github.com/praxder/universal-remote/commit/c6724705486c79fb768773f336b4da17d1aa0faa))

### Features

- Add `ur` command alias for universal-remote
  ([`3da11db`](https://github.com/praxder/universal-remote/commit/3da11db08cbbcb8a64b730dd9833ce6ee420c0bd))

- **samsung**: Discover Tizen TVs via mDNS _airplay._tcp
  ([`e30a838`](https://github.com/praxder/universal-remote/commit/e30a838415a909b33c5037053c024c4ab7e2a80a))

- **tui**: Add delete button on edit device screen
  ([`276eb25`](https://github.com/praxder/universal-remote/commit/276eb25818a1d61fb2cb941d36bffa69033daa6f))

- **tui**: Show name, type, and IP in remote status bar
  ([`f92aa4d`](https://github.com/praxder/universal-remote/commit/f92aa4dbdc87fd9f8f803687c9495d4844c3122d))


## v1.1.1 (2026-07-20)

### Bug Fixes

- **adb-text**: Preserve a literal "%s" in device text input
  ([`910b0da`](https://github.com/praxder/universal-remote/commit/910b0da992722dbc50ae1238b8e759fc66a64113))

- **firetv**: Escape text before device-side input text
  ([`b77eb52`](https://github.com/praxder/universal-remote/commit/b77eb528ad327a90b26d1c307a1b25890a4bcb05))

- **tui**: Align add-form save, add vim h/l, harden mount gate
  ([`ef9ef3a`](https://github.com/praxder/universal-remote/commit/ef9ef3af98dd3e63339bef8f995841635841b955))

### Build System

- **packaging**: Switch frozen binary to onedir
  ([`7d9c40d`](https://github.com/praxder/universal-remote/commit/7d9c40de44337c56642d6c2a7eba544ed2e91be7))

### Chores

- **openspec**: Archive add-homebrew-distribution and sync specs
  ([`ee6cbf7`](https://github.com/praxder/universal-remote/commit/ee6cbf7ed8db2b4db19876b2a3573697f1dd7eeb))

### Documentation

- **openspec**: Propose switching frozen build to onedir
  ([`39764b3`](https://github.com/praxder/universal-remote/commit/39764b3c20e962451ca66609aac054d903332f37))

- **readme**: Restructure into summary, install, features, limitations
  ([`36cb42b`](https://github.com/praxder/universal-remote/commit/36cb42b25ef736d2a4f478b788962b7965302e62))


## v1.1.0 (2026-07-20)

### Chores

- **spec**: Marked a task as complete
  ([`6bb3535`](https://github.com/praxder/universal-remote/commit/6bb3535f5c43b65fe139a116439c2ce4a4cfee69))

### Documentation

- **openspec**: Mark add-homebrew-distribution tasks complete
  ([`aed60c1`](https://github.com/praxder/universal-remote/commit/aed60c123c16a8229ff0e7daa9a980226fbeea27))

### Features

- **useless**: Trigger ci as a test
  ([`0b4d5ce`](https://github.com/praxder/universal-remote/commit/0b4d5ce190a9d792f6f8d7eff81f9f73863b030e))

### Refactoring

- **ci**: Split release into version / build / tap jobs
  ([`3d6e594`](https://github.com/praxder/universal-remote/commit/3d6e5941e4258c8efb810383d97d8b2cf01c230a))


## v1.0.0 (2026-07-20)

- Initial Release
