## ADDED Requirements

### Requirement: In-repo formula updated automatically

After the binary asset is published, the workflow SHALL update the
`universal-remote` formula **in this repository** to point at the new version and
its SHA-256, committing it to the branch Homebrew reads the tap from (the
repository's default branch) so `brew upgrade` picks the new version up.

#### Scenario: Formula bumped after release
- **WHEN** a release with its binary asset is published for version `vX.Y.Z`
- **THEN** the workflow commits an updated `Formula/universal-remote.rb` (new `version`, `url`, `sha256`) to the repository's default branch

#### Scenario: Formula points at this repository's release
- **WHEN** the formula is rewritten for version `vX.Y.Z`
- **THEN** its download URL names this repository's release assets, not the previous personal repository's

#### Scenario: The formula-bump commit does not re-trigger a release
- **WHEN** the workflow pushes its own formula-bump commit back to the default branch
- **THEN** that push does not start another release run

### Requirement: Releases publish without a human approval step

The release pipeline SHALL complete end to end — version, tag, GitHub Release,
binary asset, and formula bump — with no person approving a pull request in the
middle of the run, even though the branch it writes to requires reviewed pull
requests for ordinary contributions.

#### Scenario: Release completes unattended
- **WHEN** releasable commits reach the default branch
- **THEN** the version-bump commit, the tag, the release, the asset, and the formula bump all land without any manual approval

#### Scenario: Ordinary contributions still require review
- **WHEN** a person pushes to a review-protected branch outside the release pipeline
- **THEN** the repository's review requirements apply to that push as normal

### Requirement: Scoped credential for the pipeline's protected-branch pushes

The credential the pipeline pushes with SHALL be a short-lived installation token
scoped to contents-write on this repository alone, minted per run. It SHALL NOT
be a long-lived organization-wide or account-wide token, even though bypassing
the branch's review requirement demands more privilege than the default workflow
token carries.

#### Scenario: Credential is limited to this repository
- **WHEN** the workflow pushes the version bump, the tag, or the formula bump
- **THEN** it authenticates with an installation token minted for that run whose write access covers this repository only, and which expires when the run ends

#### Scenario: Credential is not reused for the release upload
- **WHEN** the workflow creates the GitHub Release and uploads the binary asset
- **THEN** it uses the default workflow token, since publishing a release needs no branch-protection bypass

## REMOVED Requirements

### Requirement: Tap formula updated automatically

**Reason**: The Homebrew tap is no longer a separate repository. The formula now
lives in this repository, so there is no cross-repo push and no scoped
cross-repo credential to describe. Replaced by "In-repo formula updated
automatically".

**Migration**: `praxder/homebrew-tap` is deprecated rather than deleted; its
formula stops being updated once the first release is cut from this repository.
Existing users re-tap this repository by URL — see the `homebrew-distribution`
capability for the install commands.
