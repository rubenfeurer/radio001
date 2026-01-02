# Claude Development Guide for Radio001

## Dev environment tips
- Use `./scripts/dev-environment.sh start` to start the FastAPI backend in Docker (recommended).
- Alternatively, use `docker-compose -f compose/docker-compose.yml up radio-backend -d` for manual Docker control.
- Run `./scripts/setup-dev.sh` for initial setup - it will install dependencies and configure pre-commit hooks.
- Use `npm run dev` in `frontend/` to start the local development server with hot reload on port 5173.
- Backend API runs on port 8000 - access the interactive docs at http://localhost:8000/docs.
- Frontend proxies API requests to the backend, so always ensure the backend container is running during development.
- For production builds, use `npm run build` in `frontend/` to generate static files.
- Check the `frontend/package.json` and `backend/pyproject.toml` for available scripts and dependencies.
- Use `./scripts/dev-environment.sh status` to check if services are running.
- Use `./scripts/dev-environment.sh logs` to view all logs, or `./scripts/dev-environment.sh logs radio-backend` for specific service logs.

## Project structure notes
- Frontend code lives in `frontend/src/` with routes in `frontend/src/routes/`.
- Backend code lives in `backend/` with API routes in `backend/api/routes/`.
- Radio business logic is in `backend/core/` and hardware controls in `backend/hardware/`.
- Station data is stored in `data/` directory.
- Notification sounds are in `assets/sounds/`.
- All Docker configurations are in `compose/` directory.

## Testing instructions
- Backend tests: Run `pytest` from the `backend/` directory (142 tests in the suite).
- Frontend tests: Run `npm test` from the `frontend/` directory.
- To test specific backend modules, use `pytest tests/test_<module>.py`.
- To test API endpoints, use `pytest tests/api/` or access the interactive docs at http://localhost:8000/docs.
- Before committing, ensure all tests pass for both frontend and backend.
- For hardware-related tests, the system supports mock mode - check `backend/hardware/` for GPIO mocking.
- After changing API routes or data models, verify the OpenAPI schema at http://localhost:8000/openapi.json.

## Backend development
- FastAPI backend uses Python 3.11+ with async/await patterns.
- Main entry point is `backend/main.py` which combines WiFi and Radio APIs.
- WiFi endpoints are under `/api/wifi/` and Radio endpoints under `/radio/`.
- WebSocket support for real-time radio updates at `/ws/radio`.
- Use `docker-compose logs radio-backend` to view backend logs.
- For dependency changes, update `backend/requirements.txt` and rebuild the container.
- Hardware integration supports both real GPIO (production) and mock mode (development).

## Frontend development
- SvelteKit frontend with TypeScript.
- State management uses Svelte stores in `frontend/src/lib/stores/`.
- UI components are in `frontend/src/lib/components/`.
- Responsive design optimized for mobile devices.
- Dark mode support with automatic theme switching.
- WebSocket integration for real-time radio status updates.
- API client code should handle both development (local proxy) and production (direct) endpoints.

## Docker workflow
- Development: `./scripts/dev-environment.sh start` (recommended)
- Alternative: `docker-compose -f compose/docker-compose.yml up radio-backend -d`
- Production: `docker-compose -f compose/docker-compose.prod.yml up -d`
- View logs: `./scripts/dev-environment.sh logs [service]` or `docker-compose -f compose/docker-compose.yml logs -f radio-backend`
- Rebuild after changes: `./scripts/dev-environment.sh rebuild [service]` or `docker-compose -f compose/docker-compose.yml up radio-backend --build -d`
- Stop services: `./scripts/dev-environment.sh stop` or `docker-compose -f compose/docker-compose.yml down`
- Check status: `./scripts/dev-environment.sh status`
- Open shell: `./scripts/dev-environment.sh shell radio-backend`
- Cleanup: `./scripts/dev-environment.sh cleanup`

## Deployment notes
- Target platform is Raspberry Pi Zero 2 W (ARM64 architecture).
- Use `./scripts/deploy-pi.sh` for automated deployment to Raspberry Pi.
- Production deployment uses static frontend build served by backend or separate nginx.
- Ensure Docker is installed on the Pi before deploying.
- Access deployed app at http://radio.local or http://[pi-ip-address].
- Hardware controls require actual GPIO pins - use mock mode for non-Pi development.

## PR instructions
- Title format: `[frontend]` or `[backend]` prefix followed by descriptive title.
- Always run both `npm test` (frontend) and `pytest` (backend) before committing.
- For backend changes, ensure Docker build succeeds: `docker-compose -f compose/docker-compose.yml build radio-backend`
- For frontend changes, ensure production build works: `cd frontend && npm run build`
- Update relevant documentation in `docs/` if adding new features or API endpoints.
- Follow the phase implementation plan in `docs/PHASE4_IMPLEMENTATION_PLAN.md` for frontend work.
- Ensure ARM64 compatibility - avoid x86-specific dependencies.

## Current development focus
- Phase 4: Frontend integration of radio features.
- Radio UI components in `frontend/src/lib/components/`.
- Radio state management in `frontend/src/lib/stores/radio.ts`.
- Navigation updates to unify WiFi and Radio interfaces.
- Refer to `docs/PHASE4_IMPLEMENTATION_PLAN.md` for step-by-step implementation guide.

## Common commands
```bash
# Initial setup (first time only)
./scripts/setup-dev.sh

# Start development environment
./scripts/dev-environment.sh start
cd frontend && npm run dev

# Check service status
./scripts/dev-environment.sh status

# View logs
./scripts/dev-environment.sh logs              # All services
./scripts/dev-environment.sh logs radio-backend # Specific service

# Run all backend tests
cd backend && pytest

# Run all frontend tests
cd frontend && npm test

# Rebuild after code changes
./scripts/dev-environment.sh rebuild radio-backend

# Open shell in container
./scripts/dev-environment.sh shell radio-backend

# Stop services
./scripts/dev-environment.sh stop

# Build for production
cd frontend && npm run build
docker-compose -f compose/docker-compose.prod.yml build

# Deploy to Raspberry Pi
./scripts/deploy-pi.sh

# Cleanup Docker resources
./scripts/dev-environment.sh cleanup
```

## API development tips
- WiFi API: Located in `backend/api/routes/wifi.py`
- Radio API: Located in `backend/api/routes/radio.py`
- All endpoints are documented with OpenAPI/Swagger at http://localhost:8000/docs
- Use Pydantic models for request/response validation
- WebSocket endpoint for real-time updates: `ws://localhost:8000/ws/radio`
- Test API endpoints interactively at http://localhost:8000/docs before writing frontend code

## Debugging tips
- Backend: Add `import pdb; pdb.set_trace()` for debugging (won't work in Docker without tty)
- Frontend: Use browser DevTools and SvelteKit's built-in error overlay
- Check Docker logs for backend errors: `docker-compose logs -f radio-backend`
- For WebSocket issues, use browser DevTools Network tab to inspect WS connections
- Hardware issues: Ensure mock mode is enabled in development (check `backend/hardware/`)
