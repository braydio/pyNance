<template>
  <div class="p-4">
    <Card>
      <CardContent>
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

          <Button :disabled="!selectedFile" @click="startImport">
            Import Selected File
          </Button>
        </div>
      </CardContent>
    </Card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import axios from 'axios';

const files = ref([]);
const selectedFile = ref('');
const loading = ref(true);

const loadFiles = async () => {
  try {
    const res = await axios.get('/api/imports/files');
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
    await axios.post('/api/imports/import', { file: selectedFile.value });
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
