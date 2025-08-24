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

Standard header used within `BasePageLayout`. Provides slots for an optional icon, title, subtitle, and right-aligned actions.

### Example: icon and subtitle
```vue
<BasePageLayout>
  <PageHeader>
    <template #icon>
      <SettingsIcon class="w-6 h-6" />
    </template>
    <template #title>Settings</template>
    <template #subtitle>Update your preferences</template>
    <template #actions>
      <UiButton variant="outline">Save</UiButton>
    </template>
  </PageHeader>

  <!-- rest of view -->
</BasePageLayout>
```

Refer to [PageHeader docs](PageHeader.md) for additional slot details.

## Contributor guidance

For conventions around layout and slot usage, see [CODEX.md](../../CODEX.md) and [CONTRIBUTING.md](../../CONTRIBUTING.md). Following these guides ensures consistent adoption of layout components throughout the project.
