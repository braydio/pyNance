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

## Contributor guidance

For conventions around layout and slot usage, see [CODEX.md](../../CODEX.md) and [CONTRIBUTING.md](../../CONTRIBUTING.md). Following these guides ensures consistent adoption of layout components throughout the project.
