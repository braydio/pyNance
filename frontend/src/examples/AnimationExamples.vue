<template>
  <div class="container py-8 space-y-8">
    <h1 class="heading-md">Animation Examples</h1>
    
    <!-- Button Animations -->
    <section class="card">
      <h2 class="text-xl font-bold mb-4 text-[var(--color-accent-cyan)]">Button Animations</h2>
      <div class="flex flex-wrap gap-4">
        <button class="btn hover-lift">Standard Button</button>
        <button class="btn-outline hover-glow">Outlined Button</button>
        <button class="btn-ghost">Ghost Button</button>
        <button class="btn-sm">Small Button</button>
        <button class="btn-lg hover-lift-lg">Large Button</button>
      </div>
    </section>

    <!-- Card Animations -->
    <section>
      <h2 class="text-xl font-bold mb-4 text-[var(--color-accent-cyan)]">Card Animations</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="card hover-scale-sm">
          <h3 class="font-semibold mb-2">Hover Scale Card</h3>
          <p>This card scales slightly on hover.</p>
        </div>
        <div class="card-interactive">
          <h3 class="font-semibold mb-2">Interactive Card</h3>
          <p>This card has enhanced hover effects.</p>
        </div>
      </div>
    </section>

    <!-- Input Animations -->
    <section class="card">
      <h2 class="text-xl font-bold mb-4 text-[var(--color-accent-cyan)]">Input Animations</h2>
      <div class="space-y-4">
        <input class="input" placeholder="Standard input with transitions" />
        <input class="input-lg" placeholder="Large input with enhanced focus ring" />
      </div>
    </section>

    <!-- Link Animations -->
    <section class="card">
      <h2 class="text-xl font-bold mb-4 text-[var(--color-accent-cyan)]">Link Animations</h2>
      <div class="space-y-2">
        <div><a href="#" class="link">Simple Link</a></div>
        <div><a href="#" class="link-underline">Link with Animated Underline</a></div>
        <div><a href="#" class="link-glow">Link with Glow Effect</a></div>
      </div>
    </section>

    <!-- Loading States -->
    <section class="card">
      <h2 class="text-xl font-bold mb-4 text-[var(--color-accent-cyan)]">Loading States</h2>
      <div class="space-y-4">
        <div class="pulse-subtle">
          <p>Content with subtle pulse animation</p>
        </div>
        <div class="space-y-2">
          <div class="skeleton-dark skeleton-text-lg w-3/4"></div>
          <div class="skeleton-dark skeleton-text w-1/2"></div>
          <div class="skeleton-dark skeleton-text w-2/3"></div>
        </div>
        <button class="btn pulse-glow">Button with Pulse Glow</button>
      </div>
    </section>

    <!-- Collapsible Section -->
    <section class="card">
      <h2 class="text-xl font-bold mb-4 text-[var(--color-accent-cyan)]">Collapsible Content</h2>
      <button @click="toggleAccordion" class="btn mb-4">
        Toggle Accordion
      </button>
      <transition name="accordion">
        <div v-if="showAccordion" class="bg-gray-800 p-4 rounded">
          <p>This content slides in and out with smooth accordion animation.</p>
          <p class="mt-2">Perfect for expandable sections, FAQs, or detail panels.</p>
        </div>
      </transition>
    </section>

    <!-- List Animations -->
    <section class="card">
      <h2 class="text-xl font-bold mb-4 text-[var(--color-accent-cyan)]">Staggered List Animation</h2>
      <button @click="toggleList" class="btn mb-4">
        {{ showList ? 'Hide List' : 'Show List' }}
      </button>
      <transition name="accordion">
        <ul v-if="showList" class="space-y-2">
          <li v-for="item in listItems" :key="item.id" class="stagger-item card-interactive p-3">
            {{ item.name }}
          </li>
        </ul>
      </transition>
    </section>

    <!-- Modal Example -->
    <section class="card">
      <h2 class="text-xl font-bold mb-4 text-[var(--color-accent-cyan)]">Modal Animation</h2>
      <button @click="showModal = true" class="btn hover-lift">
        Show Modal
      </button>
    </section>

    <!-- Modal Component -->
    <transition name="modal-fade-slide">
      <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur px-4"
           @click.self="showModal = false">
        <div class="relative w-full max-w-md mx-auto rounded-2xl shadow-2xl bg-gradient-to-br from-violet-950/70 via-slate-900/90 to-blue-950/90 border-2 border-violet-400/40 p-6">
          <button @click="showModal = false" 
                  class="absolute top-4 right-4 rounded-full hover:bg-violet-600/80 active:bg-violet-700/80 focus:outline-none focus:ring-2 focus:ring-violet-400 transition group">
            <svg class="w-6 h-6 text-violet-200 group-hover:text-white transition" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 6l12 12M6 18L18 6" />
            </svg>
          </button>
          <h3 class="text-xl font-bold text-white mb-4">Animated Modal</h3>
          <p class="text-gray-300">This modal uses the same fadeInUp animation as the TransactionModal.</p>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const showAccordion = ref(false)
const showList = ref(false)
const showModal = ref(false)

const listItems = ref([
  { id: 1, name: 'First item with stagger animation' },
  { id: 2, name: 'Second item appears slightly later' },
  { id: 3, name: 'Third item continues the sequence' },
  { id: 4, name: 'Fourth item completes the stagger' },
  { id: 5, name: 'Fifth item finishes the animation' },
])

function toggleAccordion() {
  showAccordion.value = !showAccordion.value
}

function toggleList() {
  showList.value = !showList.value
}
</script>

<style scoped>
@import '../assets/css/main.css';
</style>
