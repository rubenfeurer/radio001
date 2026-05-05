## Context

The frontend is a SvelteKit 2 app using Svelte 4, Tailwind CSS 3, and a hand-rolled component system defined in `app.postcss` (`.btn`, `.card`, `.input` etc). It has 5 routes and 3 Svelte stores managing radio/wifi/websocket state. The migration replaces the custom component layer with shadcn-svelte and upgrades to Svelte 5 runes simultaneously — a "big bang" approach chosen because the codebase is small enough to make incremental migration unnecessary overhead.

## Goals / Non-Goals

**Goals:**
- Upgrade Svelte 4 → Svelte 5 (runes-based reactivity)
- Install shadcn-svelte and adopt its component model (components in `src/lib/components/ui/`)
- Replace all custom CSS component classes with shadcn components
- Replace inline SVG icons with lucide-svelte
- Achieve black/white flat design via shadcn's default neutral theme
- Preserve all existing functionality (radio control, wifi management, station picker, settings)

**Non-Goals:**
- Redesigning page layouts or information architecture
- Adding new features or pages
- Migrating to Svelte 5 SSR or server-side stores
- Dark mode (removed — not needed for a device UI with a fixed display)

## Decisions

### D1: Big bang migration (all at once) over incremental

Svelte 4 and Svelte 5 component syntax is incompatible at the component boundary when using runes. A mixed codebase is technically possible but creates confusion. Given 5 routes and 3 stores, a full migration in one change is manageable and avoids a long transitional period.

**Alternative considered**: Route-by-route migration with Svelte 4/5 compatibility shims — rejected because the shim layer adds complexity without meaningful benefit at this codebase size.

### D2: Svelte 5 runes for store migration

Svelte stores (`writable`, `readable`) will be replaced with module-level `$state` and `$derived` runes exported from `.svelte.ts` files. This is the idiomatic Svelte 5 pattern for shared state.

**Alternative considered**: Keep Svelte stores alongside Svelte 5 — stores still work in Svelte 5, but mixing store subscriptions with runes in the same component is awkward. Clean break preferred.

### D3: shadcn CSS variable theming over Tailwind `primary-*` extension

shadcn uses CSS variables (`--primary`, `--background`, etc.) configured in `app.postcss`. This replaces the current `primary-600/700` color extension in `tailwind.config.js`. The default shadcn neutral palette is black/white, which matches the target aesthetic directly.

**Alternative considered**: Keep `primary-*` tokens and just layer shadcn on top — rejected because it creates two theming systems to maintain.

### D4: Remove dark mode

The radio device has a fixed display context (a physical radio). Dark mode toggling via localStorage is unnecessary complexity. shadcn's CSS variables make re-enabling it trivial if needed later.

### D5: lucide-svelte for icons

Replaces all inline SVGs. Consistent sizing, tree-shakeable, well-maintained. shadcn-svelte uses lucide-svelte by default.

## Risks / Trade-offs

- **Svelte 5 runes are a new mental model** → Mitigation: codebase is small; all state is in 3 stores which can be migrated methodically
- **shadcn components are copied, not imported** → Means component updates require manual re-copy; acceptable tradeoff for full ownership
- **No rollback mid-migration** → This is a breaking upgrade; git branch provides the rollback. Do not merge partial state.
- **`@sveltejs/adapter-static` compatibility** → Svelte 5 + adapter-static is supported; no known issues

## Migration Plan

1. Upgrade `svelte` to v5 and `@sveltejs/vite-plugin-svelte` to v5-compatible version in `package.json`
2. Initialize shadcn-svelte (`npx shadcn-svelte@latest init`) — configures `tailwind.config.js`, `app.postcss`, and `components.json`
3. Add required shadcn components: Button, Card, Input, Badge, Separator
4. Install lucide-svelte
5. Migrate Svelte stores → `.svelte.ts` rune modules (wifi, radio, websocket)
6. Update `+layout.svelte`: remove dark mode logic, apply shadcn base layout
7. Migrate each route page to Svelte 5 syntax + shadcn components
8. Remove `app.postcss` custom component classes (`.btn`, `.card`, `.input`)
9. Remove `@tailwindcss/forms` from deps and tailwind config

**Rollback**: `git checkout main` — no database or API changes, purely frontend.

## Open Questions

- None — scope is fully defined by the 5 existing routes.
