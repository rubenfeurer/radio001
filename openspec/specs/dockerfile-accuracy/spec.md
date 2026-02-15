# dockerfile-accuracy Specification

## Purpose
TBD - created by archiving change fix-docker-build-missing-config-templates. Update Purpose after archive.
## Requirements
### Requirement: Dockerfile Dependency Accuracy

The Dockerfile SHALL accurately reflect the actual system dependencies and SHALL NOT reference unused packages or missing files.

#### Scenario: Package Dependencies Match Reality

- **WHEN** the Dockerfile lists system packages in apt-get install
- **THEN** only packages that are actually used by the system SHALL be included
- **AND** packages that are not used SHALL be removed from the installation list
- **AND** the installed packages SHALL match what the running system actually requires

#### Scenario: Configuration File References

- **WHEN** the Dockerfile contains COPY statements for configuration files
- **THEN** all referenced files SHALL exist in the project
- **AND** no COPY statements SHALL reference missing or obsolete files
- **AND** template files SHALL only be copied if they are actually used by the system

#### Scenario: Legacy Cleanup

- **WHEN** the system has migrated from one approach to another (e.g., hostapd to NetworkManager)
- **THEN** the Dockerfile SHALL be updated to reflect the new approach
- **AND** legacy references SHALL be removed from the build process
- **AND** the build artifacts SHALL match the actual runtime dependencies

