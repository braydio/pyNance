<template>
  <div class="import-selector">
    <div class="import-box">
      <h2>󰋺 Import Transactions from File</h2>
    </div>
      <div v-if="loading" class="status">Loading available files...</div>

      <div v-else>
        <label class="text-label"> Click the dropdown. </label>

        <div class="import-controls">
          <select v-model="selectedFile">
            <option disabled value=""> -- Go ahead, do it. -- </option>
            <option v-for="file in files" :key="file.name" :value="file.name">
              {{ file.label }}
            </option>
          </select>

          <button :disabled="!selectedFile" @click="startImport" class="btn btn-primary">
            Click Me
          </button>
        </div>
      </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const files = ref([])
const selectedFile = ref('')
const loading = ref(true)

async function loadFiles() {
  try {
    const res = await axios.get('/api/import/files')
    files.value = res.data.map(name => {
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
  if (!selectedFile.value) return
  try {
    await axios.post('/api/import/import', { file: selectedFile.value })
    alert(`Import started for: ${selectedFile.value}`)
  } catch (err) {
    console.error('Import failed:', err)
    alert('Failed to import file.')
  }
}

onMounted(loadFiles)
</script>



<style scoped>
.import-selector {
  padding: 1rem;
  background-color: var(--color-bg-secondary);
  border-radius: 10px;
  box-shadow: 0 2px 10px var(--shadow);
}


.import-box {
  display: flex;
  flex-direction: column;
  align-items: center;      /* ✅ centers all children horizontally */
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
  padding: 0.5rem;
  border-radius: 6px;
  border: 1px solid var(--divider);
  background-color: var(--color-bg-dark);
  color: var(--color-text-muted);
  min-width: 220px;
}

.btn-primary {
  background-color: var(--button-bg);
  color: var(--color-text-light);
  padding: 0.5rem 1rem;
  border: groove 2px var(--neon-purple);
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary:hover {
  background-color: var(--neon-purple);
  color: var(--page-bg);
  border: groove 2px transparent;
}
</style>
