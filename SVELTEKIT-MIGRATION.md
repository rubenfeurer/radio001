# SvelteKit Migration Guide

This guide explains how to migrate from Nuxt to SvelteKit to resolve ARM64 compatibility issues with oxc-parser.

## The Problem

Nuxt 3.17.1+ introduced `oxc-parser` which doesn't provide ARM64 binaries, causing build failures on Raspberry Pi Zero 2 W and M1/M2 Macs with errors like:

```
ERROR  Failed to load native binding
Cannot find module './parser.linux-arm64-gnu.node'
Cannot find module '@oxc-parser/binding-linux-arm64-gnu'
```

## The Solution

**Hybrid Architecture:**
- **Backend:** Keep FastAPI in Docker (working perfectly)
- **Frontend:** Replace Nuxt with SvelteKit (no ARM64 issues)
- **Development:** Local SvelteKit dev server proxies to Docker backend
- **Production:** Static SvelteKit build served by nginx

## Quick Setup

### 1. Create SvelteKit Frontend

```bash
# Create frontend directory
mkdir frontend
cd frontend

# Initialize SvelteKit project
npm create svelte@latest . -- --template skeleton --types typescript --prettier --eslint
npm install

# Add dependencies for our app
npm install -D @tailwindcss/forms @tailwindcss/typography tailwindcss autoprefixer postcss
npm install @sveltejs/adapter-static
```

### 2. Configure SvelteKit

Create `svelte.config.js`:
```javascript
import adapter from '@sveltejs/adapter-static';

export default {
  kit: {
    adapter: adapter({
      pages: 'build',
      assets: 'build',
      fallback: 'index.html',
      precompress: false,
      strict: true
    }),
    prerender: {
      handleMissingId: 'warn'
    }
  }
};
```

Create `vite.config.js`:
```javascript
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
});
```

### 3. Setup Tailwind CSS

```bash
npx tailwindcss init -p
```

Update `tailwind.config.js`:
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          900: '#1e3a8a'
        }
      }
    }
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography')
  ]
};
```

### 4. Development Workflow

```bash
# Terminal 1: Start backend (Docker)
docker-compose up radio-backend

# Terminal 2: Start frontend (Local)
cd frontend
npm run dev
```

Frontend runs on `http://localhost:3000`, proxies API calls to Docker backend on `http://localhost:8000`.

## Migration Checklist

### ✅ Project Structure

```
radio-wifi/
├── frontend/                    # New SvelteKit frontend
│   ├── src/
│   │   ├── routes/
│   │   │   ├── +layout.svelte   # Main layout
│   │   │   ├── +page.svelte     # Home (index.vue)
│   │   │   ├── setup/
│   │   │   │   └── +page.svelte # Setup wizard
│   │   │   ├── settings/
│   │   │   │   └── +page.svelte # Settings page
│   │   │   └── status/
│   │   │       └── +page.svelte # Status page
│   │   ├── lib/
│   │   │   ├── components/      # Reusable components
│   │   │   ├── stores/          # Svelte stores (replaces composables)
│   │   │   └── types.ts         # TypeScript definitions
│   │   ├── app.html            # HTML template
│   │   └── app.postcss         # Global styles
│   ├── static/                 # Static assets
│   ├── package.json
│   └── vite.config.js
├── backend/                    # Unchanged FastAPI backend
├── app/                        # Legacy Nuxt (keep for reference)
└── docker/                     # Docker configurations
```

### 🔄 Component Migration Map

| **Nuxt Component** | **SvelteKit Equivalent** | **Status** |
|-------------------|-------------------------|------------|
| `pages/index.vue` | `routes/+page.svelte` | ✅ Port main dashboard |
| `pages/setup.vue` | `routes/setup/+page.svelte` | ✅ Port setup wizard |
| `pages/settings.vue` | `routes/settings/+page.svelte` | ✅ Port settings |
| `pages/status.vue` | `routes/status/+page.svelte` | ✅ Port status page |
| `components/SignalStrength.vue` | `lib/components/SignalStrength.svelte` | ✅ Port component |
| `composables/useWiFi.ts` | `lib/stores/wifi.ts` | ✅ Convert to stores |
| `types/index.ts` | `lib/types.ts` | ✅ Copy types |
| `nuxt.config.ts` | `svelte.config.js` | ✅ New config |

### 🧩 Code Conversion Examples

#### State Management: Composables → Stores

**Nuxt (Composable):**
```typescript
// composables/useWiFi.ts
export const useWiFi = () => {
  const networks = ref<WiFiNetwork[]>([])
  const isScanning = ref(false)
  
  const scanNetworks = async () => {
    isScanning.value = true
    // API call...
    isScanning.value = false
  }
  
  return { networks, isScanning, scanNetworks }
}
```

**SvelteKit (Store):**
```typescript
// lib/stores/wifi.ts
import { writable } from 'svelte/store';

export const networks = writable<WiFiNetwork[]>([]);
export const isScanning = writable(false);

export const scanNetworks = async () => {
  isScanning.set(true);
  try {
    const response = await fetch('/api/wifi/scan', { method: 'POST' });
    const data = await response.json();
    networks.set(data.networks);
  } finally {
    isScanning.set(false);
  }
};
```

#### Component Usage: Vue → Svelte

**Nuxt (Vue):**
```vue
<template>
  <div>
    <h1>{{ title }}</h1>
    <button @click="handleClick" :disabled="loading">
      {{ loading ? 'Loading...' : 'Scan' }}
    </button>
  </div>
</template>

<script setup>
const title = 'WiFi Setup'
const loading = ref(false)

const handleClick = async () => {
  loading.value = true
  await scanNetworks()
  loading.value = false
}
</script>
```

**SvelteKit (Svelte):**
```svelte
<script lang="ts">
  import { isScanning, scanNetworks } from '$lib/stores/wifi';
  
  const title = 'WiFi Setup';
  
  const handleClick = () => {
    scanNetworks();
  };
</script>

<div>
  <h1>{title}</h1>
  <button on:click={handleClick} disabled={$isScanning}>
    {$isScanning ? 'Loading...' : 'Scan'}
  </button>
</div>
```

#### Routing: navigateTo → goto

**Nuxt:**
```typescript
import { navigateTo } from '#app'
await navigateTo('/setup')
```

**SvelteKit:**
```typescript
import { goto } from '$app/navigation';
goto('/setup');
```

#### API Calls: $fetch → fetch

**Nuxt:**
```typescript
const data = await $fetch('/api/wifi/status')
```

**SvelteKit:**
```typescript
const response = await fetch('/api/wifi/status');
const data = await response.json();
```

## Key Differences: Nuxt vs SvelteKit

| **Feature** | **Nuxt 3** | **SvelteKit** |
|-------------|-----------|---------------|
| **Reactivity** | Vue Composition API (`ref()`, `reactive()`) | Svelte stores (`writable()`, `readable()`) |
| **Routing** | File-based + `navigateTo()` | File-based + `goto()` |
| **State** | Composables + `useState()` | Stores + context |
| **Lifecycle** | `onMounted()`, `onUnmounted()` | `onMount()`, `onDestroy()` |
| **API Calls** | `$fetch()` | `fetch()` |
| **Styling** | Scoped CSS + `<style scoped>` | Component CSS + `:global()` |
| **Build** | Nitro | Vite |
| **SSR** | Built-in | Built-in with adapters |
| **Bundle Size** | Runtime framework | Compiled (smaller) |

## Implementation Steps

### Phase 1: Setup (Day 1)
- [ ] Create SvelteKit project structure
- [ ] Configure Vite proxy to FastAPI backend
- [ ] Setup Tailwind CSS
- [ ] Create basic layout and routing
- [ ] Test backend connectivity

### Phase 2: Core Pages (Day 2-3)
- [ ] Port main dashboard (`pages/index.vue` → `routes/+page.svelte`)
- [ ] Port setup wizard (`pages/setup.vue` → `routes/setup/+page.svelte`)
- [ ] Port settings page (`pages/settings.vue` → `routes/settings/+page.svelte`)
- [ ] Port status page (`pages/status.vue` → `routes/status/+page.svelte`)

### Phase 3: Components & State (Day 4)
- [ ] Port SignalStrength component
- [ ] Convert useWiFi composable to Svelte stores
- [ ] Implement reactive state management
- [ ] Add error handling and loading states

### Phase 4: Polish & Testing (Day 5)
- [ ] Add dark mode toggle
- [ ] Responsive design testing
- [ ] Cross-browser compatibility
- [ ] Performance optimization

### Phase 5: Production (Day 6)
- [ ] Configure static adapter for production builds
- [ ] Update Docker configurations
- [ ] Test deployment on Raspberry Pi
- [ ] Update documentation

## Benefits of This Approach

### ✅ Technical Benefits
1. **No ARM64 Issues**: SvelteKit doesn't use oxc-parser
2. **Better Performance**: Svelte compiles to vanilla JavaScript
3. **Smaller Bundle**: No runtime framework overhead
4. **Faster Development**: Local dev server with instant HMR
5. **Simpler Dependencies**: Fewer build-time dependencies

### ✅ Development Benefits
1. **Local Development**: No Docker required for frontend
2. **Better DX**: Instant hot reload and error reporting
3. **TypeScript**: Full TypeScript support out of the box
4. **Modern Tooling**: Vite for fast builds and development

### ✅ Deployment Benefits
1. **Static Build**: Generated static files for production
2. **CDN Ready**: Can be served from any CDN
3. **Docker Backend**: Keep proven FastAPI backend
4. **Easy Scaling**: Static frontend + containerized backend

## Production Deployment

### Docker Compose Configuration

```yaml
# docker-compose.prod.yml
services:
  radio-backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    ports: 
      - "8000:8000"
    environment:
      - NODE_ENV=production
    networks:
      - radio-network
    
  radio-frontend:
    image: nginx:alpine
    volumes:
      - ./frontend/build:/usr/share/nginx/html:ro
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    ports: 
      - "80:80"
    depends_on: 
      - radio-backend
    networks:
      - radio-network

networks:
  radio-network:
    driver: bridge
```

### Nginx Configuration

```nginx
# nginx.conf
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://radio-backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        proxy_pass http://radio-backend:8000;
    }
}
```

## Testing on Raspberry Pi

### 1. Setup Development Environment
```bash
# On your Mac/PC
cd radio-wifi/frontend
npm run build

# Copy build to Pi
scp -r build/ pi@raspberrypi.local:~/radio-wifi/frontend/
```

### 2. Deploy on Pi
```bash
# On Raspberry Pi
cd ~/radio-wifi
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Verify
```bash
# Check services
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs

# Test frontend
curl http://localhost
# Test backend
curl http://localhost/api/health
```

## Migration Timeline

| **Week** | **Tasks** | **Deliverables** |
|----------|-----------|------------------|
| **Week 1** | Setup SvelteKit, basic routing, component porting | Working frontend with basic functionality |
| **Week 2** | State management, API integration, styling | Feature-complete frontend |
| **Week 3** | Testing, optimization, production deployment | Production-ready application |

## Rollback Plan

If issues arise during migration:

1. **Keep original Nuxt code** in `app/` directory
2. **Use feature flags** to switch between frontends
3. **Docker override** to use original Nuxt container
4. **DNS routing** to serve from different containers

## Success Metrics

- [ ] ✅ No oxc-parser errors during development
- [ ] ✅ Frontend builds successfully on ARM64
- [ ] ✅ Hot reload works locally without Docker
- [ ] ✅ Production build works on Raspberry Pi
- [ ] ✅ Bundle size smaller than Nuxt version
- [ ] ✅ Page load times improved
- [ ] ✅ All original functionality preserved

## Next Steps

1. **Create SvelteKit project structure**
2. **Port existing components systematically**
3. **Test on Raspberry Pi early and often**
4. **Update all documentation**
5. **Consider this architecture for future projects**

---

This migration eliminates the ARM64 compatibility issues while maintaining all existing functionality and improving performance. The hybrid approach provides the best of both worlds: a modern, fast frontend with a proven, stable backend.