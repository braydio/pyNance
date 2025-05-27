<template>
  <div class="p-4 rounded-xl border bg-white shadow-md w-full max-w-2xl">
    <button class="btn btn-pill btn-outline" @click="showLinkOptions = !showLinkOptions">
      {{ showLinkOptions ? 'Hide' : 'Link Account' }}
    </button>

    <transition name="slide-vertical">
      <div v-if="showLinkOptions" class="mt-4 mt-2 space-y-4">
        <PlaidProductScopeSelector v-model="selectedProducts" />
        <LinkProviderLauncher :selected-products="selectedProducts" :user-id="userID"
          @refresh="$emit('refreshAccount')" />
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import PlaidProductScopeSelector from '@/components/forms//PlaidProductScopeSelector.vue'
import LinkProviderLauncher from '@/components/forms/LinkProviderLauncher.vue'

const selectedProducts = ref([])
const showLinkOptions = ref(false)
const userID = import.meta.env.VITE_USER_ID_PLAID || ''
</script>
