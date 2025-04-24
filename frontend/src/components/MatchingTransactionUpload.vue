
<template>
  <div class="p-4">
    <Card>
      <CardContent>
        <h2 class="text-xl font-bold mb-4">📁 Upload Transactions</h2>

        <input type="file" @change="handleFileChange" accept=".csv" class="mb-4" />

        <div v-if="csvHeaders.length">
          <p class="mb-2 text-sm">Account Matching:</p>
          <div v-if="matchingAccounts.length">
            <label>Select matching account:</label>
            <select v-model="selectedAccount" class="border rounded w-full p-2 mb-4">
              <option v-for="acc in matchingAccounts" :key="acc.account_id" :value="acc.account_id">
                {{ acc.name }} - {{ acc.institution_name }} ({{ acc.type }})
              </option>
            </select>
          </div>
          <div v-else>
            <p class="text-sm text-red-500">No matching account found. A new one will be created.</p>
          </div>
        </div>

        <Button :disabled="!file || uploading" @click="uploadFile">
          {{ uploading ? 'Uploading...' : 'Upload Transactions' }}
        </Button>
      </CardContent>
    </Card>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Papa from 'papaparse';

const file = ref(null);
const csvHeaders = ref([]);
const matchingAccounts = ref([]);
const selectedAccount = ref(null);
const uploading = ref(false);

const handleFileChange = (e) => {
  file.value = e.target.files[0];
  if (!file.value) return;

  Papa.parse(file.value, {
    header: true,
    preview: 1,
    complete: async (results) => {
      const sampleRow = results.data[0];
      csvHeaders.value = Object.keys(sampleRow);

      const matchPayload = {
        name: sampleRow.name,
        institution_name: sampleRow.institution_name,
        type: sampleRow.type,
        subtype: sampleRow.subtype,
        account_id: sampleRow.account_id,
      };

      try {
        const res = await fetch('/api/accounts/match', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(matchPayload),
        });
        const data = await res.json();
        matchingAccounts.value = data;
        if (data.length === 1) {
          selectedAccount.value = data[0].account_id;
        }
      } catch (err) {
        console.error('Matching failed:', err);
      }
    },
  });
};

const uploadFile = async () => {
  if (!file.value) return;
  uploading.value = true;
  const formData = new FormData();
  formData.append('file', file.value);
  if (selectedAccount.value) {
    formData.append('account_id', selectedAccount.value);
  }

  try {
    await fetch('/api/import/import', {
      method: 'POST',
      body: formData,
    });
    alert('File uploaded successfully.');
  } catch (e) {
    alert('Upload failed.');
  } finally {
    uploading.value = false;
  }
};
</script>

<style scoped>
select {
  min-width: 240px;
}
</style>
