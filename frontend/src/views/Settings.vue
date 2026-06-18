<template>
  <BasePageLayout gap="gap-6">
    <PageHeader :icon="SettingsIcon">
      <template #title>Settings</template>
      <template #subtitle>Preferences and account maintenance</template>
    </PageHeader>

    <section class="settings-panel">
      <h2 class="settings-panel-title">Appearance</h2>
      <label for="themes" class="settings-label">Theme</label>
      <BaseSelect
        id="themes"
        v-model="selectedTheme"
        class="settings-select"
        size="md"
        radius="md"
        @change="setTheme"
      >
        <option v-for="theme in themes" :key="theme" :value="theme">
          {{ theme }}
        </option>
      </BaseSelect>
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

<script>
import axios from 'axios'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseInput from '@/components/base/BaseInput.vue'
import BaseSelect from '@/components/base/BaseSelect.vue'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import RefreshPlaidControls from '@/components/widgets/RefreshPlaidControls.vue'
import { Settings as SettingsIcon } from 'lucide-vue-next'

export default {
  name: 'Settings',
  components: {
    BaseButton,
    BaseInput,
    BaseSelect,
    BasePageLayout,
    PageHeader,
    RefreshPlaidControls,
  },
  data() {
    return {
      themes: [],
      selectedTheme: '',
      commandTemplates: [
        { label: 'Refresh account balances', value: 'refresh-balances' },
        { label: 'Sync transaction history', value: 'sync-transactions' },
        { label: 'Rebuild reporting cache', value: 'rebuild-cache' },
      ],
      selectedCommandTemplate: 'refresh-balances',
      commandArgument: '',
      commandLoading: false,
      commandFeedback: null,
      commandOutput: '',
      SettingsIcon,
    }
  },
  computed: {
    /** Return whether the current command form can start a request. */
    commandCanSubmit() {
      return (
        Boolean(this.selectedCommandTemplate && this.commandArgument.trim()) && !this.commandLoading
      )
    },
  },
  async created() {
    await this.fetchThemes()
  },
  methods: {
    async fetchThemes() {
      try {
        const response = await axios.get('/themes')
        this.themes = response.data.themes
        this.selectedTheme = response.data.current_theme
      } catch (error) {
        console.error('Failed to fetch themes:', error)
      }
    },
    /** Submit the validated command form and expose the request result inline. */
    async executeCommand() {
      if (!this.commandCanSubmit) return

      this.commandLoading = true
      this.commandFeedback = null
      this.commandOutput = ''

      try {
        const response = await axios.post('/api/codex/exec', {
          preset: this.selectedCommandTemplate,
          task: this.commandArgument.trim(),
        })
        this.commandFeedback = { type: 'success', message: 'Command completed successfully.' }
        this.commandOutput = response.data.stdout || ''
      } catch (error) {
        this.commandFeedback = {
          type: 'error',
          message: error.response?.data?.error || 'Unable to run command. Please try again.',
        }
      } finally {
        this.commandLoading = false
      }
    },
    async setTheme() {
      try {
        await axios.post('/set_theme', { theme: this.selectedTheme })
        alert(`Theme set to ${this.selectedTheme}`)
      } catch (error) {
        console.error('Failed to set theme:', error)
      }
    },
  },
}
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
.settings-input,
.settings-command-fields > button {
  max-width: 18rem;
}

.settings-command-feedback {
  margin: 0;
  color: var(--color-text-muted);
}

.settings-command-feedback--success {
  color: var(--color-accent-green);
}

.settings-command-feedback--error {
  color: var(--color-accent-red);
}

.settings-command-output {
  max-width: 100%;
  overflow-x: auto;
  color: var(--color-text-light);
  white-space: pre-wrap;
}
</style>
