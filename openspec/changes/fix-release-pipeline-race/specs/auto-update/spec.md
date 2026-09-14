# auto-update Delta — fix-release-pipeline-race

## ADDED Requirements

### Requirement: Documented rollback for a bad stable image
The deployment documentation SHALL describe a rollback procedure for a bad `:stable` image: pinning the Pi's compose file to a previous immutable semver tag (`:vX.Y.Z`), pulling and restarting, and reverting the pin to `:stable` once a fixed release exists. The documentation SHALL note that `WATCHTOWER_CLEANUP=true` deletes the previous local image (so rollback re-pulls from GHCR) and that Watchtower keeps checking the pinned tag, which never moves, effectively freezing updates until the pin is reverted.

#### Scenario: Operator rolls back a bad stable release
- **WHEN** a released `:stable` image malfunctions on production Pis
- **THEN** the documented procedure SHALL restore the previous version by pinning its semver tag in `/opt/radio/docker-compose.yml` and running `docker compose pull && docker compose up -d`
- **AND** the procedure SHALL work without requiring GHCR write access

#### Scenario: Rollback prerequisite is documented
- **WHEN** an operator consults the rollback documentation before any tagged release exists
- **THEN** the documentation SHALL state that rollback requires at least one prior `vX.Y.Z` release
- **AND** SHALL point to the GHCR package versions list as the source of available tags
