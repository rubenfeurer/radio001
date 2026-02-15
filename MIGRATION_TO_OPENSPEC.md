# Migration to OpenSpec - Radio001 Project

## Overview

This document records the migration of Radio001 project documentation from a traditional `docs/` directory structure to OpenSpec's spec-driven development approach.

**Migration Date**: February 15, 2026
**OpenSpec Version**: 1.1.1
**Migrated By**: Automated migration during CI fix onboarding tutorial

## What Changed

### Before Migration
```
radio001/
├── docs/
│   ├── CONFIGURATION.md           # Configuration guide
│   ├── RADIO_INTEGRATION_PLAN.md  # Development roadmap
│   ├── HOTSPOT_HANDOFF.md         # Hotspot implementation details
│   └── NOTES.md                   # Development todos
├── README.md                      # Project overview
└── claude.md                      # Development guide
```

### After Migration
```
radio001/
├── openspec/
│   ├── specs/                     # Living project specifications
│   │   ├── system-configuration/spec.md
│   │   ├── radio-integration/spec.md
│   │   ├── hotspot-configuration/spec.md
│   │   └── wifi-management/spec.md
│   └── changes/                   # Development workflow
│       └── archive/               # Completed changes
├── README.md                      # Enhanced with OpenSpec references
└── claude.md                      # Enhanced with OpenSpec workflow
```

## Migration Benefits

### Single Source of Truth
- All system requirements now in `openspec/specs/`
- Specifications written in testable WHEN/THEN format
- No duplication between docs and implementation plans

### Improved AI Development Workflow
- OpenSpec slash commands available: `/opsx:new`, `/opsx:apply`, `/opsx:archive`
- Structured planning before implementation
- Decision history preserved in `openspec/changes/archive/`

### Better Requirement Tracking
- Clear capability definitions for each system component
- Testable scenarios for all functionality
- Requirements linked directly to implementation tasks

## Migrated Content Mapping

| Old Document | New Location | Content Type |
|--------------|--------------|--------------|
| `docs/CONFIGURATION.md` | `openspec/specs/system-configuration/spec.md` | Configuration requirements |
| `docs/RADIO_INTEGRATION_PLAN.md` | `openspec/specs/radio-integration/spec.md` | Radio system capabilities |
| `docs/HOTSPOT_HANDOFF.md` | `openspec/specs/hotspot-configuration/spec.md` | Hotspot mode requirements |
| `docs/NOTES.md` | *Converted to OpenSpec changes* | Development todos |
| New: | `openspec/specs/wifi-management/spec.md` | WiFi system capabilities |

## How to Use OpenSpec

### For New Features
```bash
# Start planned development
npm run opsx:new "add-bluetooth-support"

# Work through artifacts: proposal → specs → design → tasks
npm run opsx:continue

# Implement the planned work
npm run opsx:apply

# Complete and archive
npm run opsx:archive
```

### For Bug Fixes
```bash
# Quick exploration without creating formal change
/opsx:explore

# Or create a change for complex fixes
npm run opsx:new "fix-wifi-reconnection-issue"
```

### For Understanding the System
- Read `openspec/specs/` for complete system requirements
- Check `openspec/changes/archive/` for development decision history
- Use `/opsx:onboard` for interactive workflow tutorial

## Accessing Historical Information

### Old Documentation References
If you need information that was in the old `docs/` directory:

1. **Configuration info** → `openspec/specs/system-configuration/spec.md`
2. **Radio features** → `openspec/specs/radio-integration/spec.md`
3. **Hotspot behavior** → `openspec/specs/hotspot-configuration/spec.md`
4. **WiFi management** → `openspec/specs/wifi-management/spec.md`

### Git History
The complete `docs/` directory history is preserved in git:
```bash
# View old documentation
git show HEAD~1:docs/CONFIGURATION.md
git log --follow docs/CONFIGURATION.md
```

## Development Workflow Changes

### Before (Traditional)
```bash
1. Read docs/SOME_PLAN.md
2. Edit code directly
3. Test manually
4. Commit changes
```

### After (OpenSpec)
```bash
1. /opsx:new "feature-name"           # Plan change
2. Create: proposal → specs → design → tasks
3. /opsx:apply                        # Implement with AI
4. /opsx:archive                      # Complete & preserve
```

### Backward Compatibility
- All existing development scripts still work
- Docker development environment unchanged
- Traditional workflow still supported alongside OpenSpec

## Files Modified During Migration

### Enhanced Files
- `README.md` - Added OpenSpec workflow section and updated documentation links
- `claude.md` - Added OpenSpec commands and workflow guidance
- `.gitignore` - Already included OpenSpec temporary files (no changes needed)
- `package.json` - Already included OpenSpec npm scripts (no changes needed)

### New Files Created
- `openspec/specs/system-configuration/spec.md` - System configuration requirements
- `openspec/specs/radio-integration/spec.md` - Radio system capabilities
- `openspec/specs/hotspot-configuration/spec.md` - Hotspot mode specifications
- `openspec/specs/wifi-management/spec.md` - WiFi management requirements

### Removed Files
- `docs/` directory (entire contents migrated to OpenSpec)

## Next Steps

1. **Try OpenSpec**: Run `/opsx:onboard` for guided tutorial
2. **New features**: Use `/opsx:new <feature-name>` for planned development
3. **Reference specs**: Check `openspec/specs/` for system requirements
4. **Decision history**: Explore `openspec/changes/archive/` for past decisions

## Support

If you need help with OpenSpec or can't find migrated information:
1. Check the OpenSpec specs first: `openspec/specs/`
2. Use `/opsx:explore` to investigate problems
3. Run `/opsx:onboard` for workflow guidance
4. Reference this migration guide for file mappings

The migration maintains all information while providing better structure for AI-assisted development.