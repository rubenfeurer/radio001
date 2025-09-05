# Development Guide

Complete development setup and workflow guide for the Radio WiFi Configuration project using the **hybrid SvelteKit + FastAPI approach**.

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone <repository-url> radio-wifi
cd radio-wifi

# 2. Start backend (Docker)
docker-compose up radio-backend -d

# 3. Setup and start frontend (Local)
cd frontend
npm install
npm run dev

# Access: http://localhost:3000
```

## 🏗️ New Hybrid Architecture

**Why This Approach?**
- ✅ **Solves ARM64 Issues**: No more oxc-parser problems
- ✅ **Local Development**: Fast hot reload without Docker
- ✅ **Proven Backend**: Keep stable FastAPI backend
- ✅ **Better Performance**: SvelteKit compiles to vanilla JS

**Architecture:**
```
┌─────────────────┐    ┌──────────────────┐
│   SvelteKit     │────│   FastAPI        │
│   Frontend      │ API│   Backend        │
│   (Local)       │────│   (Docker)       │
└─────────────────┘    └──────────────────┘
      :3000                    :8000
```

## 📁 Project Structure

```
radio-wifi/
├── frontend/              # 🆕 SvelteKit frontend
│   ├── src/
│   │   ├── routes/        # Pages (file-based routing)
│   │   ├── lib/
│   │   │   ├── components/# Reusable components  
│   │   │   ├── stores/    # Svelte stores (state)
│   │   │   └── types.ts   # TypeScript types
│   │   ├── app.html       # HTML template
│   │   └── app.postcss    # Global styles
│   ├── static/            # Static assets
│   ├── package.json       # Frontend dependencies
│   └── vite.config.js     # Vite + proxy config
├── backend/               # ✅ Unchanged FastAPI backend
│   ├── main.py            # FastAPI application
│   └── requirements.txt   # Python dependencies
├── app/                   # 📦 Legacy Nuxt (deprecated)
├── docker/                # Docker configurations
└── scripts/               # Helper scripts
```

## 🛠️ Development Environment

### Prerequisites

- **Node.js 18+** (for local frontend development)
- **Docker & Docker Compose** (for backend)
- **Git** (for version control)

### Environment Setup

1. **Backend Development (Docker):**
   ```bash
   docker-compose up radio-backend -d    # Start backend
   docker-compose logs radio-backend     # View logs
   docker-compose exec radio-backend bash # Shell access
   ```

2. **Frontend Development (Local):**
   ```bash
   cd frontend
   npm install                           # Install dependencies
   npm run dev                           # Start dev server
   npm run build                         # Build for production
   npm run preview                       # Preview production build
   ```

### Development Workflow

```bash
# Terminal 1: Backend
docker-compose up radio-backend

# Terminal 2: Frontend  
cd frontend && npm run dev

# Terminal 3: Development
git checkout -b feature/new-feature
# ... make changes ...
git add . && git commit -m "feat: add new feature"
git push origin feature/new-feature
```

## 🔧 Configuration

### Frontend Configuration

**vite.config.js** - Proxy configuration for API calls:
```javascript
export default defineConfig({
  plugins: [sveltekit()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000'  // Proxy to Docker backend
    }
  }
});
```

**package.json** - Development scripts:
```json
{
  "scripts": {
    "dev": "vite dev --host 0.0.0.0 --port 3000",
    "build": "vite build",
    "preview": "vite preview",
    "check": "svelte-kit sync && svelte-check",
    "lint": "eslint ."
  }
}
```

### Backend Configuration

Backend runs in Docker with these environment variables:
```env
NODE_ENV=development
API_PORT=8000
WIFI_INTERFACE=wlan0
HOSTNAME=radio
HOTSPOT_SSID=Radio-Setup
HOTSPOT_PASSWORD=radio123
```

## 📊 State Management

### Svelte Stores (replaces Nuxt composables)

**Before (Nuxt composables):**
```typescript
const { networks, scanNetworks, isScanning } = useWiFi()
```

**After (Svelte stores):**
```typescript
import { networks, scanNetworks, isScanning } from '$lib/stores/wifi'

// Reactive values with $ prefix
$networks        // Array of networks
$isScanning      // Boolean state
scanNetworks()   // Function call
```

### Store Structure

```typescript
// lib/stores/wifi.ts
export const networks = writable<WiFiNetwork[]>([]);
export const isScanning = writable(false);
export const status = writable<SystemStatus | null>(null);

// Derived stores (computed values)
export const currentNetwork = derived(
  [status, networks], 
  ([$status, $networks]) => { /* ... */ }
);

// Actions
export const scanNetworks = async () => { /* ... */ };
export const connectToNetwork = async (credentials) => { /* ... */ };
```

## 🎨 Component Development

### Vue to Svelte Migration

**Vue Component (Nuxt):**
```vue
<template>
  <div>
    <h1>{{ title }}</h1>
    <button @click="handleClick" :disabled="loading">
      {{ loading ? 'Loading...' : 'Click me' }}
    </button>
  </div>
</template>

<script setup>
const title = 'Hello'
const loading = ref(false)

const handleClick = () => {
  loading.value = true
}
</script>
```

**Svelte Component:**
```svelte
<script lang="ts">
  const title = 'Hello';
  let loading = false;

  const handleClick = () => {
    loading = true;
  };
</script>

<div>
  <h1>{title}</h1>
  <button on:click={handleClick} disabled={loading}>
    {loading ? 'Loading...' : 'Click me'}
  </button>
</div>
```

### Key Differences

| Feature | Nuxt/Vue | SvelteKit |
|---------|----------|-----------|
| Reactivity | `ref()`, `reactive()` | Direct assignment |
| Events | `@click` | `on:click` |
| Conditionals | `v-if` | `{#if}` |
| Loops | `v-for` | `{#each}` |
| Store access | `composable()` | `$store` |
| Routing | `navigateTo()` | `goto()` |

## 🔗 API Integration

### API Calls

**Nuxt approach:**
```typescript
const data = await $fetch('/api/wifi/status')
```

**SvelteKit approach:**
```typescript
const response = await fetch('/api/wifi/status');
const data = await response.json();
```

### Error Handling

```typescript
// stores/wifi.ts
export const scanNetworks = async () => {
  isScanning.set(true);
  error.set(null);
  
  try {
    const response = await fetch('/api/wifi/scan', { method: 'POST' });
    const result = await response.json();
    
    if (result.success) {
      networks.set(result.data);
    } else {
      throw new Error(result.message);
    }
  } catch (err) {
    error.set(err.message);
  } finally {
    isScanning.set(false);
  }
};
```

## 🚀 Production Deployment

### Build Process

```bash
# 1. Build frontend
cd frontend
npm run build

# 2. Deploy with Docker
docker-compose -f docker-compose.prod.yml up -d
```

### Production Structure

```yaml
# docker-compose.prod.yml
services:
  radio-backend:
    build: ./backend
    ports: ["8000:8000"]
    
  radio-frontend:
    image: nginx:alpine
    volumes:
      - ./frontend/build:/usr/share/nginx/html:ro
    ports: ["80:80"]
    depends_on: [radio-backend]
```

## 📱 Pages & Routing

### File-based Routing

```
frontend/src/routes/
├── +layout.svelte          # Main layout
├── +page.svelte           # Home page (/)
├── setup/
│   └── +page.svelte       # Setup page (/setup)
├── settings/
│   └── +page.svelte       # Settings page (/settings)
└── status/
    └── +page.svelte       # Status page (/status)
```

### Navigation

```svelte
<script>
  import { goto } from '$app/navigation';
</script>

<button on:click={() => goto('/setup')}>
  Go to Setup
</button>

<!-- Or with links -->
<a href="/setup">Setup</a>
```

## 🧪 Testing & Quality

### Development Commands

```bash
# Frontend checks
cd frontend
npm run check        # TypeScript checking
npm run lint         # ESLint
npm run lint:fix     # Auto-fix linting issues

# Backend checks
docker-compose exec radio-backend python -m pytest
```

### Code Quality

- **TypeScript**: Full type checking for both frontend and API calls
- **ESLint**: Code linting with Svelte-specific rules
- **Prettier**: Code formatting with Svelte support
- **Svelte Check**: Component validation

## 🔄 Migration Status

### ✅ Completed
- [x] SvelteKit project setup
- [x] Basic routing structure
- [x] Tailwind CSS integration
- [x] WiFi store (replaces useWiFi composable)
- [x] API proxy configuration
- [x] TypeScript types
- [x] Development workflow

### 🚧 In Progress
- [ ] Home page component (from pages/index.vue)
- [ ] Setup wizard (from pages/setup.vue)
- [ ] Status page (from pages/status.vue)
- [ ] Settings page (from pages/settings.vue)
- [ ] SignalStrength component

### 📋 Todo
- [ ] Production deployment testing
- [ ] Raspberry Pi deployment scripts
- [ ] Performance optimization
- [ ] PWA features
- [ ] End-to-end testing

## 🔍 Troubleshooting

### Common Issues

**1. Frontend not connecting to backend:**
```bash
# Check if backend is running
docker-compose ps
docker-compose logs radio-backend

# Check proxy configuration in vite.config.js
```

**2. TypeScript errors:**
```bash
cd frontend
npm run check        # Check for type errors
npm install          # Reinstall if needed
```

**3. Port conflicts:**
```bash
# Change ports in package.json or docker-compose.yml
# Frontend: 3000 (configurable)
# Backend: 8000 (configurable)
```

**4. API calls failing:**
```bash
# Verify API endpoints
curl http://localhost:8000/health
curl http://localhost:3000/api/health  # Should proxy
```

### Debug Tools

- **Svelte DevTools**: Browser extension for Svelte debugging
- **Network Tab**: Monitor API calls and proxy behavior
- **Docker Logs**: `docker-compose logs radio-backend`
- **Console**: Frontend errors appear in browser console

## 📚 Resources

### Documentation
- [SvelteKit Docs](https://kit.svelte.dev/docs)
- [Svelte Tutorial](https://svelte.dev/tutorial)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Vite Configuration](https://vitejs.dev/config/)

### Migration Guides
- [SVELTEKIT-MIGRATION.md](./SVELTEKIT-MIGRATION.md) - Detailed migration guide
- [Vue to Svelte comparison](https://svelte.dev/docs#vue-js)

## 🎯 Best Practices

### Development
1. **Keep backend in Docker** - Ensures consistency
2. **Use local frontend** - Faster development cycle
3. **Leverage hot reload** - Instant feedback on changes
4. **Test early on Pi** - Catch platform-specific issues

### Code Organization
1. **Stores for global state** - WiFi status, networks, etc.
2. **Components for reusability** - SignalStrength, NetworkList
3. **Types for safety** - Shared TypeScript definitions
4. **API layer separation** - Centralized API calls

### Performance
1. **Static generation** - Pre-build pages where possible
2. **Lazy loading** - Load components as needed
3. **Minimal bundles** - Tree-shake unused code
4. **Caching** - Leverage browser and CDN caching

---

This hybrid approach solves the ARM64 compatibility issues while providing a modern, fast development experience. The combination of local SvelteKit development with containerized FastAPI backend gives us the best of both worlds.