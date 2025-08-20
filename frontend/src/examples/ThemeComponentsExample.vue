<template>
  <div class="space-y-8 p-8">
    <!-- Card Examples -->
    <section>
      <h2 class="text-2xl font-bold mb-4 text-white">Card Components</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <h3 class="text-lg font-semibold mb-2">Glassmorphic Card</h3>
          <p class="text-gray-300">This card now features glassmorphic styling with violet gradients and hover effects.</p>
        </Card>
        
        <Card>
          <h3 class="text-lg font-semibold mb-2">Another Card</h3>
          <p class="text-gray-300">Hover over the cards to see the subtle glow effect.</p>
        </Card>
      </div>
    </section>

    <!-- Button Examples -->
    <section>
      <h2 class="text-2xl font-bold mb-4 text-white">Button Variants</h2>
      <div class="flex flex-wrap gap-4">
        <Button>Default Button</Button>
        <Button variant="outline">Outline Button</Button>
        <Button variant="violet-primary">Violet Primary</Button>
        <Button variant="blue-secondary">Blue Secondary</Button>
        <Button variant="violet-primary" pill>Pill Violet</Button>
        <Button variant="blue-secondary" pill>Pill Blue</Button>
        <Button variant="violet-primary" disabled>Disabled</Button>
      </div>
    </section>

    <!-- Modal Example -->
    <section>
      <h2 class="text-2xl font-bold mb-4 text-white">Modal Component</h2>
      <Button variant="violet-primary" @click="showModal = true">Open Modal</Button>
      
      <Modal v-if="showModal" @close="showModal = false">
        <template #title>
          Updated Modal
        </template>
        <template #body>
          <div class="space-y-4">
            <p class="text-gray-300">
              This modal now uses the same styling approach as TransactionModal with:
            </p>
            <ul class="list-disc list-inside space-y-2 text-gray-300">
              <li>Gradient backgrounds with violet/blue color scheme</li>
              <li>Consistent close button styling and animations</li>
              <li>Backdrop blur and modern glassmorphic effects</li>
              <li>Smooth fade-slide animations</li>
            </ul>
            <div class="flex gap-4 pt-4">
              <Button variant="violet-primary" @click="showModal = false">
                Close Modal
              </Button>
              <Button variant="blue-secondary">
                Secondary Action
              </Button>
            </div>
          </div>
        </template>
      </Modal>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Card from '../components/ui/Card.vue'
import Button from '../components/ui/Button.vue'
import Modal from '../components/ui/Modal.vue'

const showModal = ref(false)
</script>
