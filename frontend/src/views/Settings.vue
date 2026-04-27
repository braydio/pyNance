<template>
  <BasePageLayout gap="gap-6">
    <PageHeader :icon="SettingsIcon">
      <template #title>Settings</template>
      <template #subtitle>Preferences and account maintenance</template>
    </PageHeader>

    <section class="settings-panel">
      <h2 class="settings-panel-title">Appearance</h2>
      <label for="themes" class="settings-label">Theme</label>
      <select id="themes" v-model="selectedTheme" class="input settings-select" @change="setTheme">
        <option v-for="theme in themes" :key="theme" :value="theme">
          {{ theme }}
        </option>
      </select>
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
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import RefreshPlaidControls from '@/components/widgets/RefreshPlaidControls.vue'
import { Settings as SettingsIcon } from 'lucide-vue-next'

export default {
  name: 'Settings',
  components: {
    BasePageLayout,
    PageHeader,
    RefreshPlaidControls,
  },
  data() {
    return {
      themes: [],
      selectedTheme: '',
      SettingsIcon,
    }
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

.settings-select {
  max-width: 18rem;
}
</style>
