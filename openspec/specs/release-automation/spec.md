# release-automation Specification

## Purpose
Publish releases automatically on merge to main — deriving the semantic version and notes from conventional commits, building and smoke-testing the macOS arm64 binary, and bumping the Homebrew tap formula.
## Requirements
### Requirement: Release triggered by merge to main

A GitHub Actions workflow SHALL run on every push to `main` (the result of merging
`development` → `main`) and SHALL publish a release only when the newly merged
commits contain releasable conventional-commit types.

#### Scenario: Releasable commits produce a release
- **WHEN** `development` is merged into `main` with at least one `feat:` or `fix:` (or breaking-change) commit since the last tag
- **THEN** the workflow creates a new version tag and a corresponding GitHub Release

#### Scenario: No releasable commits is a no-op
- **WHEN** a push to `main` contains only non-releasable commits (e.g. `docs:`, `chore:`) since the last tag
- **THEN** the workflow completes without creating a tag, release, or binary

#### Scenario: The version-bump commit does not re-trigger a release
- **WHEN** the workflow pushes its own version-bump commit back to `main`
- **THEN** that push does not start another release run

### Requirement: Semantic version and notes from conventional commits

The workflow SHALL derive the next semantic version and the release notes from the
conventional commit messages since the last release tag, with no manual version
entry.

#### Scenario: Bump type follows commit types
- **WHEN** the releasable commits since the last tag are `fix:` only
- **THEN** the patch version is incremented; a `feat:` yields a minor increment and a breaking change yields a major increment

#### Scenario: Notes summarize what changed
- **WHEN** a release is published
- **THEN** its notes list the changes grouped by type (features, fixes, etc.), generated from the commit messages rather than hand-written

#### Scenario: First release has a deterministic version
- **WHEN** the workflow runs for the first time with no prior tag
- **THEN** it produces a deterministic initial version tag rather than failing or no-oping

### Requirement: Binary built and attached to the release

When a release is published, the workflow SHALL build the macOS arm64 binary on a
native arm64 runner, verify it, and attach it to the GitHub Release as a
downloadable asset.

#### Scenario: Binary asset is attached
- **WHEN** a release for version `vX.Y.Z` is created
- **THEN** a macOS arm64 binary archive for that version is uploaded as an asset on that release

#### Scenario: Built binary is smoke-tested before publish
- **WHEN** the binary is built in CI
- **THEN** the workflow runs it with `--version` and fails the job if the output does not match the release version

### Requirement: Tap formula updated automatically

After the binary asset is published, the workflow SHALL update the
`universal-remote` formula in `praxder/homebrew-tap` to point at the new version and
its SHA-256, using a scoped credential.

#### Scenario: Formula bumped after release
- **WHEN** a release with its binary asset is published for version `vX.Y.Z`
- **THEN** the workflow commits an updated `Formula/universal-remote.rb` (new `version`, `url`, `sha256`) to `praxder/homebrew-tap`, so `brew upgrade` picks up the new version

#### Scenario: Scoped credential used for cross-repo push
- **WHEN** the workflow pushes to the tap repository
- **THEN** it authenticates with a fine-grained token limited to contents-write on the tap repo, not the default `GITHUB_TOKEN`
