<template>
  <BasePageLayout>
    <PageHeader :icon="SettingsIcon">
      <template #title>Settings</template>
      <template #subtitle>Manage application preferences</template>
    </PageHeader>

    <label for="themes">Select Theme:</label>
    <select v-model="selectedTheme" @change="setTheme">
      <option v-for="theme in themes" :key="theme" :value="theme">
        {{ theme }}
      </option>
    </select>
  </BasePageLayout>
</template>

<script>
import axios from 'axios'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import { Settings as SettingsIcon } from 'lucide-vue-next'

export default {
  name: 'Settings',
  components: {
    BasePageLayout,
    PageHeader,
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

