<template>
  <div class="account-selector">
    <!-- Header with selection info -->
    <div class="selector-header">
      <div class="selection-info">
        <h3 class="selector-title">Account Filter</h3>
        <p class="selection-count" v-if="availableAccounts.length > 0">
          {{ hasSelection ? `${selectedAccountIds.length} of ${availableAccounts.length} selected` : 'All accounts' }}
        </p>
      </div>
      
      <!-- Quick actions -->
      <div class="quick-actions" v-if="availableAccounts.length > 0">
        <button 
          @click="selectAll" 
          class="action-btn"
          :disabled="selectedAccountIds.length === availableAccounts.length"
        >
          Select All
        </button>
        <button 
          @click="deselectAll" 
          class="action-btn"
          :disabled="selectedAccountIds.length === 0"
        >
          Clear
        </button>
        <button @click="selectAccountsByType('depository')" class="action-btn type-btn">
          Assets Only
        </button>
        <button @click="selectAccountsByType('credit')" class="action-btn type-btn">
          Liabilities Only
        </button>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <span>Loading accounts...</span>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="error-state">
      <p class="error-text">{{ error }}</p>
      <button @click="fetchAccounts" class="retry-btn">Retry</button>
    </div>

    <!-- Account grid -->
    <div v-else-if="availableAccounts.length > 0" class="accounts-grid">
      <div 
        v-for="account in availableAccounts" 
        :key="account.id"
        class="account-card"
        :class="{ 
          'selected': selectedAccountIds.includes(account.id),
          'asset': account.balance >= 0,
          'liability': account.balance < 0
        }"
        @click="toggleAccount(account.id)"
      >
        <div class="account-header">
          <div class="account-icon">
            <img 
              v-if="account.institution_icon_url" 
              :src="account.institution_icon_url" 
              :alt="account.institution_name || 'Bank'"
              class="icon-img"
            />
            <span v-else class="icon-fallback">
              {{ initials(account.name) }}
            </span>
          </div>
          <div class="account-info">
            <div class="account-name">{{ account.name }}</div>
            <div class="account-details">
              <span class="account-type">{{ account.type }}</span>
              <span class="account-mask" v-if="account.mask">•••• {{ account.mask }}</span>
            </div>
          </div>
          <div class="selection-indicator">
            <div class="checkbox" :class="{ checked: selectedAccountIds.includes(account.id) }">
              <svg v-if="selectedAccountIds.includes(account.id)" class="check-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
            </div>
          </div>
        </div>
        
        <div class="account-balance">
          <span class="balance-amount" :class="{ positive: account.balance >= 0, negative: account.balance < 0 }">
            {{ formatBalance(account.balance) }}
          </span>
          <span class="balance-label">{{ account.balance >= 0 ? 'Asset' : 'Liability' }}</span>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="empty-state">
      <p class="empty-text">No accounts found</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  selectedAccountIds: { type: Array, required: true },
  availableAccounts: { type: Array, required: true },
  loading: { type: Boolean, default: false },
  error: { type: String, default: null }
})

const emit = defineEmits([
  'toggle-account',
  'select-all',
  'deselect-all', 
  'select-accounts-by-type',
  'fetch-accounts'
])

// Computed
const hasSelection = computed(() => props.selectedAccountIds.length > 0)

// Methods
function toggleAccount(accountId) {
  emit('toggle-account', accountId)
}

function selectAll() {
  emit('select-all')
}

function deselectAll() {
  emit('deselect-all')
}

function selectAccountsByType(type) {
  emit('select-accounts-by-type', type)
}

function fetchAccounts() {
  emit('fetch-accounts')
}

function formatBalance(amount) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0
  }).format(Math.abs(amount))
}

function initials(name) {
  if (!name) return '??'
  return name.split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}
</script>

<style scoped>
.account-selector {
  background: var(--color-bg-dark);
  border-radius: 1rem;
  padding: 1.5rem;
  border: 1px solid var(--divider);
  box-shadow: 0 4px 24px var(--shadow, rgba(0, 0, 0, 0.15));
}

/* Header */
.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--divider);
}

.selection-info {
  flex: 1;
}

.selector-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 0.25rem;
}

.selection-count {
  font-size: 0.9rem;
  color: var(--color-text-light);
  margin: 0;
}

/* Quick Actions */
.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.action-btn {
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  border: 1px solid var(--divider);
  background: var(--color-bg-sec);
  color: var(--color-text);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover:not(:disabled) {
  background: var(--color-bg-dark);
  border-color: var(--color-accent-cyan);
  color: var(--color-accent-cyan);
  transform: translateY(-1px);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.type-btn {
  background: linear-gradient(135deg, var(--color-bg-sec) 0%, var(--color-bg-dark) 100%);
}

/* States */
.loading-state, .error-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  gap: 0.75rem;
}

.loading-spinner {
  width: 1.5rem;
  height: 1.5rem;
  border: 2px solid var(--divider);
  border-top: 2px solid var(--color-accent-cyan);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-state {
  flex-direction: column;
}

.error-text {
  color: var(--color-accent-red, #ef4444);
  margin-bottom: 1rem;
}

.retry-btn {
  padding: 0.5rem 1rem;
  background: var(--color-accent-cyan);
  color: white;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-weight: 500;
}

.retry-btn:hover {
  opacity: 0.9;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--color-text-muted);
}

/* Account Grid */
.accounts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
  max-height: 400px;
  overflow-y: auto;
  padding-right: 0.5rem;
}

.account-card {
  background: var(--color-bg-sec);
  border: 2px solid var(--divider);
  border-radius: 0.75rem;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.account-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px var(--shadow, rgba(0, 0, 0, 0.1));
}

.account-card.selected {
  border-color: var(--color-accent-cyan);
  background: linear-gradient(135deg, var(--color-bg-sec) 0%, rgba(6, 182, 212, 0.1) 100%);
}

.account-card.asset {
  border-left: 4px solid var(--color-accent-cyan);
}

.account-card.liability {
  border-left: 4px solid var(--color-accent-yellow);
}

/* Account Header */
.account-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.account-icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-dark);
  border: 2px solid var(--divider);
  flex-shrink: 0;
}

.icon-img {
  width: 70%;
  height: 70%;
  object-fit: contain;
  border-radius: 50%;
}

.icon-fallback {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--color-accent-cyan);
}

.account-info {
  flex: 1;
  min-width: 0;
}

.account-name {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 0.25rem;
}

.account-details {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--color-text-light);
}

.account-type {
  text-transform: capitalize;
  background: var(--color-bg-dark);
  padding: 0.1rem 0.5rem;
  border-radius: 0.25rem;
  border: 1px solid var(--divider);
}

.account-mask {
  font-family: monospace;
}

/* Selection Indicator */
.selection-indicator {
  flex-shrink: 0;
}

.checkbox {
  width: 1.25rem;
  height: 1.25rem;
  border: 2px solid var(--divider);
  border-radius: 0.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-dark);
  transition: all 0.2s ease;
}

.checkbox.checked {
  background: var(--color-accent-cyan);
  border-color: var(--color-accent-cyan);
  color: white;
}

.check-icon {
  width: 0.875rem;
  height: 0.875rem;
}

/* Account Balance */
.account-balance {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 0.75rem;
  border-top: 1px solid var(--divider);
}

.balance-amount {
  font-size: 1rem;
  font-weight: 700;
}

.balance-amount.positive {
  color: var(--color-accent-cyan);
}

.balance-amount.negative {
  color: var(--color-accent-yellow);
}

.balance-label {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Responsive */
@media (max-width: 768px) {
  .account-selector {
    padding: 1rem;
  }
  
  .selector-header {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }
  
  .quick-actions {
    justify-content: center;
  }
  
  .accounts-grid {
    grid-template-columns: 1fr;
    max-height: 300px;
  }
}
</style>
