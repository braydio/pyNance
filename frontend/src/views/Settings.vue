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
      <h2 class="settings-panel-title">Dashboard AI message</h2>
      <p class="settings-panel-copy">
        Control the LLM-generated dashboard header and optionally use an Ollama-compatible server.
      </p>
      <div class="settings-command-fields">
        <label class="settings-checkbox-label">
          <input
            v-model="llmSettings.custom_message_enabled"
            data-testid="llm-message-toggle"
            type="checkbox"
            :disabled="llmSettingsLoading || llmSettingsSaving"
          />
          Enable custom LLM message header
        </label>

        <label for="llm-base-url" class="settings-label">Custom LLM URL</label>
        <BaseInput
          id="llm-base-url"
          v-model="llmSettings.base_url"
          data-testid="llm-base-url"
          :disabled="llmSettingsLoading || llmSettingsSaving"
          placeholder="http://localhost:11434"
          class="settings-input"
          size="md"
          radius="md"
          @enter="saveLlmSettings"
        />
        <p class="settings-field-help">
          Leave blank for OpenAI, or enter an Ollama host, /v1 base URL, or full chat-completions
          URL.
        </p>
        <BaseButton
          data-testid="llm-settings-save"
          variant="solid"
          tone="accent"
          :disabled="llmSettingsLoading || llmSettingsSaving"
          @click="saveLlmSettings"
        >
          {{ llmSettingsSaving ? 'Saving…' : 'Save AI settings' }}
        </BaseButton>
        <p
          v-if="llmSettingsFeedback"
          data-testid="llm-settings-feedback"
          :class="[
            'settings-command-feedback',
            `settings-command-feedback--${llmSettingsFeedback.type}`,
          ]"
          role="status"
        >
          {{ llmSettingsFeedback.message }}
        </p>
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
          :disabled="commandLoading"
          placeholder="Enter command argument"
          class="settings-input"
          size="md"
          radius="md"
          @enter="executeCommand"
        />
        <BaseButton
          data-testid="command-submit"
          variant="solid"
          tone="accent"
          :disabled="!commandCanSubmit"
          @click="executeCommand"
        >
          {{ commandLoading ? 'Running command…' : 'Run command' }}
        </BaseButton>
        <p
          v-if="commandFeedback"
          data-testid="command-feedback"
          :class="[
            'settings-command-feedback',
            `settings-command-feedback--${commandFeedback.type}`,
          ]"
          role="status"
        >
          {{ commandFeedback.message }}
        </p>
        <pre v-if="commandOutput" data-testid="command-output" class="settings-command-output">{{
          commandOutput
        }}</pre>
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
import api from '@/services/api'
import { onMounted, reactive, ref } from 'vue'
import { Settings as SettingsIcon } from 'lucide-vue-next'

const { activeTheme, setTheme, themes } = useTheme()
const commandTemplates = [
  { label: 'Refresh account balances', value: 'refresh-balances' },
  { label: 'Sync transaction history', value: 'sync-transactions' },
  { label: 'Rebuild reporting cache', value: 'rebuild-cache' },
]
const selectedCommandTemplate = ref('refresh-balances')
const commandArgument = ref('')
const llmSettings = reactive({ custom_message_enabled: true, base_url: '' })
const llmSettingsLoading = ref(true)
const llmSettingsSaving = ref(false)
const llmSettingsFeedback = ref(null)

async function loadLlmSettings() {
  llmSettingsLoading.value = true
  try {
    const response = await api.getLlmSettings()
    Object.assign(llmSettings, response.data)
  } catch (_error) {
    llmSettingsFeedback.value = { type: 'error', message: 'Could not load AI settings.' }
  } finally {
    llmSettingsLoading.value = false
  }
}

async function saveLlmSettings() {
  llmSettingsSaving.value = true
  llmSettingsFeedback.value = null
  try {
    const response = await api.updateLlmSettings({ ...llmSettings })
    Object.assign(llmSettings, response.data)
    llmSettingsFeedback.value = { type: 'success', message: 'AI settings saved.' }
  } catch (error) {
    llmSettingsFeedback.value = {
      type: 'error',
      message: error.response?.data?.message || 'Could not save AI settings.',
    }
  } finally {
    llmSettingsSaving.value = false
  }
}

onMounted(loadLlmSettings)
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

.settings-checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  color: var(--color-text-light);
}

.settings-checkbox-label input {
  width: 1rem;
  height: 1rem;
  accent-color: var(--accent-primary);
}

.settings-field-help {
  max-width: 38rem;
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.settings-select,
.settings-input,
.settings-command-fields > button {
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
