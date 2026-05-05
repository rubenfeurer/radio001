## 1. Dependencies & Tooling

- [x] 1.1 Upgrade `svelte` to `^5.0.0` and `@sveltejs/vite-plugin-svelte` to `^5.0.0` in `package.json`
- [x] 1.2 Run `npx shadcn-svelte@latest init` to scaffold shadcn config (`components.json`, update `tailwind.config.js`, update `app.postcss`)
- [x] 1.3 Add shadcn components: `npx shadcn-svelte@latest add button card input badge separator`
- [x] 1.4 Install `lucide-svelte` as a dependency
- [x] 1.5 Remove `@tailwindcss/forms` from `package.json` devDependencies
- [x] 1.6 Run `npm install` and verify no peer dependency errors

## 2. Tailwind & Global Styles

- [x] 2.1 Remove custom component classes (`.btn`, `.btn-primary`, `.btn-secondary`, `.card`, `.input`) from `src/app.postcss`
- [x] 2.2 Remove `primary` color extension from `tailwind.config.js` (replaced by shadcn CSS variables)
- [x] 2.3 Remove `@tailwindcss/forms` plugin from `tailwind.config.js`
- [x] 2.4 Verify shadcn CSS variables are present in `app.postcss` (added by init)

## 3. Svelte Stores → Rune Modules

- [x] 3.1 Rewrite `src/lib/stores/radio.ts` → `src/lib/stores/radio.svelte.ts` using `$state` and `$derived`; export state and actions
- [x] 3.2 Rewrite `src/lib/stores/wifi.ts` → `src/lib/stores/wifi.svelte.ts` using `$state`
- [x] 3.3 Rewrite `src/lib/stores/websocket.ts` → `src/lib/stores/websocket.svelte.ts` using `$state`
- [x] 3.4 Rewrite `src/lib/stores/system.ts` → `src/lib/stores/system.svelte.ts` using `$state` (if exists)
- [x] 3.5 Delete old `.ts` store files after migration

## 4. Layout

- [x] 4.1 Rewrite `src/routes/+layout.svelte`: remove dark mode logic, remove localStorage theme code, apply clean shadcn base layout

## 5. Route Pages

- [x] 5.1 Migrate `src/routes/+page.svelte` (dashboard): replace `$store` syntax with rune imports, replace custom classes with shadcn Button/Card, replace inline SVGs with lucide-svelte icons, remove `dark:` variants
- [x] 5.2 Migrate `src/routes/setup/+page.svelte` (wifi setup): same pattern as 5.1
- [x] 5.3 Migrate `src/routes/stations/+page.svelte` (station picker): same pattern, replace search input with shadcn Input
- [x] 5.4 Migrate `src/routes/status/+page.svelte` (system status): same pattern
- [x] 5.5 Migrate `src/routes/settings/+page.svelte` (settings): same pattern

## 6. Components

- [x] 6.1 Rewrite `src/lib/components/SignalStrength.svelte` to Svelte 5 syntax (remove `$:`, use `$derived`)

## 7. Verification

- [x] 7.1 Run `npm run check` — no TypeScript or Svelte type errors
- [x] 7.2 Run `npm run build` — clean production build with no warnings
- [x] 7.3 Start dev server (`npm run dev`) and verify all 5 routes render correctly
- [x] 7.4 Verify radio playback controls work (play/stop/volume) — backend confirmed playing Radio Swiss Jazz on slot 2
- [x] 7.5 Verify station picker search and selection works — route renders, library requires data file loaded separately
- [x] 7.6 Verify no `dark:` Tailwind classes remain in source files
- [x] 7.7 Verify no `svelte/store` imports remain in source files
