<template>
  <Card class="w-full max-w-2xl">
    <UiButton variant="primary" pill @click="showLinkOptions = !showLinkOptions">
      {{ showLinkOptions ? 'Hide' : 'Link Account' }}
    </UiButton>

    <transition name="slide-vertical">
      <div v-if="showLinkOptions" class="mt-4 space-y-4">
        <PlaidProductScopeSelector v-model="selectedProducts" />
        <LinkProviderLauncher
          :selected-products="selectedProducts"
          :user-id="userID"
          @refresh="$emit('refreshAccount')"
        />
      </div>
    </transition>
  </Card>
</template>

<script setup>
import { ref } from 'vue'
import Card from '@/components/ui/Card.vue'
import UiButton from '@/components/ui/Button.vue'
import PlaidProductScopeSelector from '@/components/forms//PlaidProductScopeSelector.vue'
import LinkProviderLauncher from '@/components/forms/LinkProviderLauncher.vue'

const selectedProducts = ref([])
const showLinkOptions = ref(false)
const userID = import.meta.env.VITE_USER_ID_PLAID || ''
</script>
