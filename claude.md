# Claude Development Guide for Radio001

## OpenSpec Workflow

This project uses OpenSpec for spec-driven development. Use slash commands in chat:
- `/opsx:new <name>` - Start new change
- `/opsx:ff <name>` - Fast-forward: all artifacts at once
- `/opsx:apply` - Implement tasks
- `/opsx:continue` - Continue existing change
- `/opsx:explore` - Think through problems
- `/opsx:verify` - Verify implementation
- `/opsx:archive` - Complete & preserve
- `/opsx:onboard` - Guided tutorial

Structure: `openspec/specs/` (specifications), `openspec/changes/` (active work), `openspec/changes/archive/` (completed)

## Project Structure

- **Frontend**: SvelteKit + TypeScript in `frontend/src/`, routes in `frontend/src/routes/`
- **Backend**: FastAPI (Python 3.11+) in `backend/`, routes in `backend/api/routes/`
- **Radio logic**: `backend/core/`, hardware in `backend/hardware/` (supports mock mode)
- **Docker configs**: `compose/`, station data in `data/`, sounds in `assets/sounds/`
- **Specs**: `openspec/specs/` - system requirements and capabilities

## Dev Environment

```bash
./scripts/setup-dev.sh                        # First-time setup
./scripts/dev-environment.sh start             # Start backend (Docker)
cd frontend && npm run dev                     # Frontend dev server (port 5173)
./scripts/dev-environment.sh status|logs|stop  # Manage services
```

Backend API: http://localhost:8000/docs | WebSocket: ws://localhost:8000/ws/radio
Frontend proxies to backend - ensure backend is running during development.

## Testing

```bash
cd backend && ./run_tests.sh          # All backend tests (see backend/TESTING.md)
cd backend && ./run_tests.sh -t unit  # Unit tests only
cd frontend && npm test               # Frontend tests
```

CRITICAL: When writing RadioManager tests, follow the pattern in `backend/TESTING.md`.
Run both frontend and backend tests before committing.

## Key Details

- Target: Raspberry Pi Zero 2 W (ARM64) - avoid x86-specific dependencies
- WiFi API: `/api/wifi/`, Radio API: `/radio/`
- Deploy: `./scripts/deploy-pi.sh` | Access: http://radio.local
- PR titles: `[frontend]` or `[backend]` prefix
- Rebuild container after dependency changes to `backend/requirements.txt`
- Current focus: Phase 4 frontend integration (see `openspec/specs/radio-integration/spec.md`)
