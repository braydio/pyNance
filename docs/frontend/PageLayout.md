# Page Layout Components

Use `BasePageLayout` and `PageHeader` to keep view structure and spacing consistent across the application. Combine them at the top of every view to provide a standard header and predictable padding.

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
- Keep tab labels short (one or two words) so they remain legible inside the pill-shaped buttons.
- Avoid wrapping tall content inside the sidebar slot; the layout expects action panels or compact forms.

### Navigation styling

The tab bar renders a frosted glass gradient container that mirrors the dashboard theme. Active tabs use a cyan-to-magenta gradient, while inactive tabs lean on a subtle midnight glaze.

- Do not override the `.tabbed-nav__button` class; instead, adjust accent colors via CSS variables when theming a specific view.
- Tabs automatically wrap on narrow breakpoints. To keep the flow balanced on mobile, limit the tab count to four.

## Contributor guidance

For conventions around layout and slot usage, see [CODEX.md](../../CODEX.md) and [CONTRIBUTING.md](../../CONTRIBUTING.md). Following these guides ensures consistent adoption of layout components throughout the project.
