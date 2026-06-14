<template>
  <BasePageLayout gap="gap-6">
    <PageHeader :icon="SettingsIcon">
      <template #title> Settings </template>
      <template #subtitle> Preferences and account maintenance </template>
    </PageHeader>

    <section class="settings-panel">
      <h2 class="settings-panel-title">Appearance</h2>
      <p class="settings-panel-copy">Choose a palette. Your preference is saved in this browser.</p>
      <div class="theme-options" role="radiogroup" aria-label="Application theme">
        <button
          v-for="theme in themes"
          :key="theme.id"
          type="button"
          class="theme-option"
          :class="{ 'theme-option--active': activeTheme === theme.id }"
          role="radio"
          :aria-checked="activeTheme === theme.id"
          @click="setTheme(theme.id)"
        >
          <span class="theme-option-swatch" :data-preview-theme="theme.id" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
          <span>
            <strong>{{ theme.label }}</strong>
            <small>{{ theme.description }}</small>
          </span>
        </button>
      </div>
    </section>

    <section class="settings-panel">
      <h2 class="settings-panel-title">Command</h2>
      <p class="settings-panel-copy">Choose a command template and provide task-specific input.</p>
      <div class="settings-command-fields">
        <label for="command-template" class="settings-label">Template</label>
        <BaseSelect
          id="command-template"
          v-model="selectedCommandTemplate"
          class="settings-select"
          size="md"
          radius="md"
        >
          <option
            v-for="template in commandTemplates"
            :key="template.value"
            :value="template.value"
          >
            {{ template.label }}
          </option>
        </BaseSelect>

        <label for="command-argument" class="settings-label">Task argument</label>
        <BaseInput
          id="command-argument"
          v-model="commandArgument"
          placeholder="Enter command argument"
          class="settings-input"
          size="md"
          radius="md"
        />
      </div>
    </section>

    <section class="settings-panel">
      <div class="settings-panel-header">
        <h2 class="settings-panel-title">Connected Accounts</h2>
        <p class="settings-panel-copy">Refresh Plaid activity without leaving settings.</p>
      </div>
      <RefreshPlaidControls />
    </section>
  </BasePageLayout>
</template>

<script setup>
/**
 * Application settings view for local appearance preferences and account maintenance.
 */
import BaseInput from '@/components/base/BaseInput.vue'
import BaseSelect from '@/components/base/BaseSelect.vue'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import RefreshPlaidControls from '@/components/widgets/RefreshPlaidControls.vue'
import { useTheme } from '@/composables/useTheme'
import { ref } from 'vue'
import { Settings as SettingsIcon } from 'lucide-vue-next'

const { activeTheme, setTheme, themes } = useTheme()
const commandTemplates = [
  { label: 'Refresh account balances', value: 'refresh-balances' },
  { label: 'Sync transaction history', value: 'sync-transactions' },
  { label: 'Rebuild reporting cache', value: 'rebuild-cache' },
]
const selectedCommandTemplate = ref('refresh-balances')
const commandArgument = ref('')
</script>

<style scoped>
.settings-panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.25rem;
  border: 1px solid var(--divider);
  border-radius: 1rem;
  background: var(--themed-bg, var(--color-bg-sec));
}

.settings-panel-header {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.settings-panel-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text-light);
}

.settings-panel-copy,
.settings-label {
  font-size: 0.95rem;
  color: var(--color-text-muted);
}

.settings-command-fields {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.settings-select,
.settings-input {
  max-width: 18rem;
}

.theme-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr));
  gap: 0.75rem;
}

.theme-option {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding: 0.9rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-3);
  background: var(--surface-1);
  color: var(--text-primary);
  text-align: left;
  cursor: pointer;
  transition: 0.2s ease;
}

.theme-option:hover,
.theme-option:focus-visible,
.theme-option--active {
  border-color: var(--accent-primary);
  background: var(--accent-surface);
  outline: none;
}

.theme-option--active {
  box-shadow: inset 3px 0 0 var(--accent-primary);
}

.theme-option strong,
.theme-option small {
  display: block;
}

.theme-option small {
  margin-top: 0.2rem;
  color: var(--text-muted);
}

.theme-option-swatch {
  display: flex;
  width: 3.4rem;
  height: 2.6rem;
  overflow: hidden;
  flex: 0 0 auto;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-2);
  background: #192330;
}

.theme-option-swatch[data-preview-theme='everforest-light'] {
  background: #fdf6e3;
}

.theme-option-swatch span {
  width: 0.3rem;
  height: 100%;
  background: #dbc074;
}

.theme-option-swatch span:nth-child(2) {
  background: #81b29a;
}

.theme-option-swatch span:nth-child(3) {
  background: #63cdcf;
}

.theme-option-swatch[data-preview-theme='everforest-light'] span:nth-child(1) {
  background: #8da101;
}

.theme-option-swatch[data-preview-theme='everforest-light'] span:nth-child(2) {
  background: #35a77c;
}

.theme-option-swatch[data-preview-theme='everforest-light'] span:nth-child(3) {
  background: #dfa000;
}
</style>
