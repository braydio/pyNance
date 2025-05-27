<template>
  <div class="link-account-wrapper">
    <button class="btn btn-pill btn-outline" @click="showLinkOptions = !showLinkOptions">
      {{ showLinkOptions ? 'Hide' : 'Link Account' }}
    </button>

    <transition name="slide-vertical">
      <div v-if="showLinkOptions" class="link-account mt-4">
        <PlaidProductScopeSelector v-model="selectedProducts" />
        <LinkProviderLauncher :selected-products="selectedProducts" :user-id="userID"
          @refresh="$emit('refreshAccount')" />
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import PlaidProductScopeSelector from '@/components/PlaidProductScopeSelector.vue'
import LinkProviderLauncher from '@/components/LinkProviderLauncher.vue'

const selectedProducts = ref([])
const showLinkOptions = ref(false)
const userID = import.meta.env.VITE_USER_ID_PLAID || ''
</script>

<style scoped>
.link-account-wrapper {
  @apply p-4 rounded-xl border bg-white shadow-md w-full max-w-2xl;
}

.link-account {
  @apply mt-2 space-y-4;
}
</style>


<style scoped>
.link-account-wrapper {
  background-color: var(--themed-bg);
  color: var(--color-text-light);
  border: 1px solid var(--color-text-light);
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 8px var(--shadow);
  width: 100%;
  max-width: 600px;
}

.link-account-wrapper h2 {
  margin-bottom: 0.5rem;
  color: var(--neon-purple);
  text-align: center;
}

.button-group {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.button-group button {
  background-color: var(--themed-bg);
  color: var(--color-text-light);
  border: 1px groove transparent;
  border-radius: 3px;
  font-weight: bold;
  padding: 0.5rem 1rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.button-group button:hover {
  background-color: var(--neon-mint);
  color: var(--themed-bg);
}
</style>
<style scoped>
.control-block {
  background-color: var(--themed-bg);
  color: var(--color-text-light);
  border: 1px solid var(--color-text-light);
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 8px var(--shadow);
  width: 100%;
  max-width: 600px;
}

.control-block h2 {
  margin-bottom: 0.5rem;
  color: var(--neon-purple);
  text-align: center;
}

.button-group {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.button-group button {
  background-color: var(--themed-bg);
  color: var(--color-text-light);
  border: 1px groove transparent;
  border-radius: 3px;
  font-weight: bold;
  padding: 0.5rem 1rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.button-group button:hover {
  background-color: var(--neon-mint);
  color: var(--themed-bg);
}
</style>
