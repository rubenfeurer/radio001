## ADDED Requirements

### Requirement: Dockerfile Dependency Accuracy

The Dockerfile must accurately reflect the actual system dependencies and not reference unused packages or missing files.

#### Scenario: Package Dependencies Match Reality

- **WHEN** the Dockerfile lists system packages in apt-get install
- **THEN** only packages that are actually used by the system are included
- **AND** packages that are not used are removed from the installation list
- **AND** the installed packages match what the running system actually requires

#### Scenario: Configuration File References

- **WHEN** the Dockerfile contains COPY statements for configuration files
- **THEN** all referenced files exist in the project
- **AND** no COPY statements reference missing or obsolete files
- **AND** template files are only copied if they are actually used by the system

#### Scenario: Legacy Cleanup

- **WHEN** the system has migrated from one approach to another (e.g., hostapd to NetworkManager)
- **THEN** the Dockerfile is updated to reflect the new approach
- **AND** legacy references are removed from the build process
- **AND** the build artifacts match the actual runtime dependencies