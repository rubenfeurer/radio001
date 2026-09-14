# auto-update — Delta Specification

## ADDED Requirements

### Requirement: Watchtower Image Pinning
The Watchtower service SHALL reference a version-pinned image (`containrrr/watchtower:1.7.1`), and the pin SHALL be identical in `docker/compose.prod.yml` and the compose file written by `scripts/install.sh`.

#### Scenario: Watchtower pinned in both compose sources
- **WHEN** `docker/compose.prod.yml` and the compose heredoc in `scripts/install.sh` are inspected
- **THEN** both SHALL specify `containrrr/watchtower:1.7.1` (or a later deliberately bumped pin, identical in both files)
- **AND** neither SHALL reference `containrrr/watchtower` without a version tag

#### Scenario: Watchtower version bumps are deliberate
- **WHEN** the Watchtower version is changed
- **THEN** both compose sources SHALL be updated in the same commit
