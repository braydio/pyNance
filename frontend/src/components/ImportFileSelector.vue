<template>
  <div class="p-4">
    <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-md">
      <h2 class="text-xl font-bold mb-4">📂 Import Transactions from File</h2>

      <div v-if="loading" class="text-gray-500">Loading available files...</div>

      <div v-else>
        <div class="mb-4">
          <label class="block text-sm font-medium mb-1">Select a file to import:</label>
          <select v-model="selectedFile" class="w-full p-2 border rounded">
            <option disabled value="">-- Choose file --</option>
            <option v-for="file in files" :key="file.name" :value="file.name">
              {{ file.label }}
            </option>
          </select>
        </div>

        <button :disabled="!selectedFile" @click="startImport"
          class="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded disabled:opacity-50">
          Import Selected File
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const files = ref([]);
const selectedFile = ref('');
const loading = ref(true);

const loadFiles = async () => {
  try {
    const res = await axios.get('/api/import/files');
    files.value = res.data.map(name => {
      const [provider, type, datePart] = name.split('_');
      const label = `${provider} – ${type} (${datePart.replace(/\..*$/, '').replace('-', '/')})`;
      return { name, label };
    });
  } catch (err) {
    console.error('Failed to load files', err);
  } finally {
    loading.value = false;
  }
};

const startImport = async () => {
  if (!selectedFile.value) return;
  try {
    await axios.post('/api/import/import', { file: selectedFile.value });
    alert(`Import started for: ${selectedFile.value}`);
  } catch (err) {
    console.error('Import failed:', err);
    alert('Failed to import file.');
  }
};

onMounted(() => {
  loadFiles();
});
</script>

<style scoped>
select {
  min-width: 240px;
}
</style>
