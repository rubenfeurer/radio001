## ADDED Requirements

### Requirement: shadcn-svelte component library is installed and configured
The system SHALL use shadcn-svelte as the UI component library with components copied into `src/lib/components/ui/`. Tailwind CSS SHALL be configured to use shadcn CSS variables for theming. The default neutral (black/white) palette SHALL be used.

#### Scenario: shadcn components are available for use
- **WHEN** a developer adds a new route or component
- **THEN** they SHALL import UI primitives from `$lib/components/ui/` (e.g., Button, Card, Input)

#### Scenario: CSS variables define the theme
- **WHEN** the application renders
- **THEN** all colors SHALL be resolved from CSS variables defined in `app.postcss` (e.g., `--background`, `--foreground`, `--primary`)

### Requirement: Svelte 5 runes replace Svelte 4 stores
The system SHALL use Svelte 5 rune-based state modules (`.svelte.ts` files with `$state` and `$derived`) instead of Svelte writable/readable stores. All shared state (radio, wifi, websocket) SHALL be exported from rune modules.

#### Scenario: Radio state is reactive across components
- **WHEN** the radio playback state changes (e.g., station starts playing)
- **THEN** all components reading that state SHALL reactively update without explicit store subscriptions

#### Scenario: No Svelte 4 store imports remain
- **WHEN** the migration is complete
- **THEN** there SHALL be no imports of `svelte/store` (`writable`, `readable`, `derived`) in the codebase

### Requirement: All UI components use shadcn primitives
The system SHALL use shadcn Button, Card, Input components in place of custom CSS classes. No custom `.btn`, `.btn-primary`, `.btn-secondary`, `.card`, or `.input` classes SHALL remain in active use.

#### Scenario: Primary action buttons use shadcn Button
- **WHEN** a primary action is rendered (e.g., WiFi Manager link, save button)
- **THEN** it SHALL use `<Button>` from shadcn with appropriate variant

#### Scenario: Content containers use shadcn Card
- **WHEN** a content section is rendered (e.g., WiFi status section, radio section)
- **THEN** it SHALL use `<Card>` and `<CardContent>` from shadcn

### Requirement: Icons use lucide-svelte
The system SHALL use lucide-svelte icon components in place of inline SVG markup. No inline `<svg>` elements SHALL be used for iconography.

#### Scenario: Navigation and action icons render correctly
- **WHEN** an icon is needed (e.g., refresh, settings gear, play/stop, signal strength)
- **THEN** it SHALL be imported from `lucide-svelte` and rendered as a component

### Requirement: Dark mode is removed
The system SHALL NOT include a dark mode toggle or dark mode CSS classes. No `dark:` Tailwind variants SHALL be used. The `localStorage` theme persistence SHALL be removed.

#### Scenario: Application renders in light mode only
- **WHEN** the application loads on any device
- **THEN** it SHALL render using the light theme CSS variables without checking system preferences or localStorage
