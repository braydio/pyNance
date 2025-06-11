<template>
  <div>
    <button class="btn" @click="open = true">View Scan Results</button>
    <Modal v-if="open" @close="open = false">
      <template #title>Scan Results</template>
      <template #body>
        <ScanResultsTable :results="results" />
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import Modal from '../ui/Modal.vue';
import ScanResultsTable from './ScanResultsTable.vue';

const props = defineProps({
  results: { type: Array, default: () => [] }
});
const open = ref(false);
</script>
