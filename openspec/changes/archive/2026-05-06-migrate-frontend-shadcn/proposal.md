## Why

The current frontend uses a hand-rolled Tailwind component system (`.btn`, `.card`, `.input` classes) with Svelte 4. Migrating to shadcn-svelte with Svelte 5 replaces the ad-hoc design system with a well-maintained, copy-owned component library and aligns the codebase with the current Svelte ecosystem.

## What Changes

- **BREAKING**: Upgrade Svelte 4 → Svelte 5 (runes-based reactivity replaces stores and `$:` syntax)
- **BREAKING**: Replace custom CSS component classes (`.btn-primary`, `.btn-secondary`, `.card`, `.input`) with shadcn-svelte components
- Install shadcn-svelte and its dependencies (bits-ui, lucide-svelte, clsx, tailwind-merge)
- Replace inline SVG icons with lucide-svelte icon components
- Replace Tailwind `primary-*` color tokens with shadcn CSS variable theming
- Migrate all 5 routes to use shadcn components: `/`, `/setup`, `/stations`, `/status`, `/settings`
- Migrate Svelte stores to Svelte 5 runes (`$state`, `$derived`, `$effect`)
- Remove dark mode manual toggle — replaced by shadcn's CSS variable dark mode strategy
- Remove `@tailwindcss/forms` plugin (shadcn handles form styling)

## Capabilities

### New Capabilities
- `frontend-design-system`: shadcn-svelte component library with black/white flat design, CSS variable theming, and lucide icons

### Modified Capabilities
- `homepage-radio-controls`: UI implementation changes (shadcn components replace custom classes); no requirement changes
- `wifi-management`: UI implementation changes only
- `system-configuration`: UI implementation changes only

## Impact

- `frontend/package.json`: add shadcn-svelte, bits-ui, lucide-svelte, clsx, tailwind-merge; upgrade svelte to v5
- `frontend/src/app.postcss`: replace custom component classes with shadcn CSS variable base styles
- `frontend/tailwind.config.js`: replace `primary-*` color extension with shadcn CSS variable config
- `frontend/src/lib/stores/`: all stores rewritten as Svelte 5 rune-based state modules
- `frontend/src/routes/`: all 5 route pages updated to use shadcn components and Svelte 5 syntax
- `frontend/src/lib/components/`: new `ui/` subdirectory with shadcn component copies
- No backend changes required
