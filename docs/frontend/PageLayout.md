# Page Layout Components

Use `BasePageLayout` and `PageHeader` to keep view structure and spacing consistent across the application. Combine them at the top of every view to provide a standard header and predictable padding.

## App shell

`AppLayout` now wraps the entire client from `App.vue`, providing the global navbar and footer slots in one place. Its `<main>` region applies a centered `max-w-7xl` wrapper with shared horizontal gutters (`px-4 sm:px-6 lg:px-8`) so every routed page keeps symmetrical side spacing by default. Views should not nest `AppLayout`; instead, rely on the page-level layouts below so spacing and framing stay consistent without double wrapping.

## BasePageLayout

Wrap each top-level view with `BasePageLayout` to apply flex column layout and spacing utilities.

### Props

- `padding` – Tailwind padding class or `false` to remove padding. Defaults to `p-6`.
- `gap` – Tailwind gap utility class. Defaults to `gap-6`.

### Example: custom padding

```vue
<BasePageLayout padding="p-2" gap="gap-4">
  <!-- view content -->
</BasePageLayout>
```

## PageHeader

Standard header used within `BasePageLayout`. Centers the title/subtitle stack and supports an optional icon prop with right-aligned `actions` slot.

### Example: icon and subtitle

```vue
<BasePageLayout>
  <PageHeader :icon="SettingsIcon">
    <template #title>Settings</template>
    <template #subtitle>Update your preferences</template>
    <template #actions>
      <UiButton variant="outline">Save</UiButton>
    </template>
  </PageHeader>

  <!-- rest of view -->
</BasePageLayout>
```

Refer to [PageHeader docs](PageHeader.md) for prop and slot details.

## TabbedPageLayout

`TabbedPageLayout` extends `BasePageLayout` with a responsive navigation rail and optional sidebar slot. Use it for views that require grouped content such as "Summary/Transactions/Charts" on the Accounts page.

### Usage tips

- Provide an ordered array of tab labels through the `tabs` prop and pair it with `v-model` to react to tab changes.
- Keep tab labels short (one or two words) so they remain legible inside the compact angular buttons.
- Avoid wrapping tall content inside the sidebar slot; the layout expects action panels or compact forms.

### Navigation styling

The tab bar uses shared surface tokens (`bg-surface-2`, `border-subtle`) and approved radius utilities (`ui-radius-3` container, `ui-radius-2` tabs) so route views inherit the same dark-surface framing and corner scale.

- Do not override `.tabbed-nav__button` button-state colors. Active/inactive/hover/focus states come from `UiButton` variants to preserve accessibility and consistent contrast on dark surfaces.
- Tabs automatically wrap on narrow breakpoints. To keep the flow balanced on mobile, limit the tab count to four.

## Contributor guidance

For conventions around layout and slot usage, see [CODEX.md](../../CODEX.md) and [CONTRIBUTING.md](../../CONTRIBUTING.md). Following these guides ensures consistent adoption of layout components throughout the project.
