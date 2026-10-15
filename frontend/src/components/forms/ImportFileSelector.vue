<template>
  <div class="import-selector">
    <div class="import-box">
      <h2>Import transactions from a file</h2>
    </div>
    <div v-if="loading" class="status" role="status">Loading available files...</div>

    <div v-else>
      <label class="text-label" for="import-file-select">Import file</label>

      <div class="import-controls">
        <select id="import-file-select" v-model="selectedFile" class="input select">
          <option disabled value="">Select a file to import</option>
          <option v-for="file in files" :key="file.name" :value="file.name">
            {{ file.label }}
          </option>
        </select>

        <button
          type="button"
          :disabled="!selectedFile || importing"
          class="btn btn-primary"
          @click="startImport"
        >
          {{ importing ? 'Importing…' : 'Import selected file' }}
        </button>
      </div>
      <p
        v-if="message"
        :class="messageIsError ? 'text-negative' : 'text-muted'"
        :role="messageIsError ? 'alert' : 'status'"
      >
        {{ message }}
      </p>
      <p v-else-if="!files.length" class="status">No import files are available.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const files = ref([])
const selectedFile = ref('')
const loading = ref(true)
const importing = ref(false)
const message = ref('')
const messageIsError = ref(false)

async function loadFiles() {
  try {
    const res = await axios.get('/api/import/files')
    files.value = res.data.map((name) => {
      const [provider, type, datePart] = name.split('_')
      const label = `${provider} → ${type} (${datePart.replace(/\..*$/, '').replace('-', '/')})`
      return { name, label }
    })
  } catch (err) {
    console.error('Failed to load import files:', err)
  } finally {
    loading.value = false
  }
}

async function startImport() {
  if (!selectedFile.value || importing.value) return
  importing.value = true
  message.value = ''
  try {
    await axios.post('/api/import/import', { file: selectedFile.value })
    messageIsError.value = false
    message.value = `Import started for ${selectedFile.value}.`
  } catch (err) {
    console.error('Import failed:', err)
    messageIsError.value = true
    message.value = 'Failed to import the file. Check the file and try again.'
  } finally {
    importing.value = false
  }
}

onMounted(loadFiles)
</script>

<style scoped>
@reference "../../assets/css/main.css";
.import-selector {
  padding: 1rem;
  background-color: var(--color-bg-secondary);
  border-radius: 10px;
  box-shadow: 0 2px 10px var(--shadow);
}

.import-box {
  display: flex;
  flex-direction: column;
  align-items: center; /* ✅ centers all children horizontally */
  gap: 0.75rem;
  text-align: center;
  margin-bottom: 1rem;
}

.import-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin-top: 0.25rem;
  flex-wrap: wrap;
}

.text-label {
  font-weight: 500;
  color: var(--color-text-muted);
  margin-bottom: 0.25rem;
  display: inline-block;
}
.status {
  color: var(--color-text-muted);
  font-style: italic;
}

select {
  width: min(22rem, 100%);
}

.import-controls {
  align-items: stretch;
}
</style>
