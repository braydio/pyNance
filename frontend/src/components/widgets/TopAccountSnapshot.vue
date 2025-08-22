<!--
  TopAccountSnapshot.vue
  Displays the top asset and liability accounts with totals.
  Users can toggle which list is visible and sort amounts ascending or descending.
-->
<template>
  <div class="bank-statement-list bs-collapsible w-full h-full">
    <div class="bs-toggle-row">
      <button :class="['bs-tab', expanded === 'assets' && 'bs-tab-active', 'bs-tab-assets']" @click="toggle('assets')"
        aria-label="Show Assets">
        Assets
      </button>
      <button :class="['bs-tab', expanded === 'liabilities' && 'bs-tab-active', 'bs-tab-liabilities']"
        @click="toggle('liabilities')" aria-label="Show Liabilities">
        Liabilities
      </button>
      <button class="bs-sort-btn" @click="toggleSort" aria-label="Toggle sort order">
        {{ sortAsc ? 'Sort: ▲' : 'Sort ▼' }}
      </button>
    </div>

    <Transition name="bs-slide">
      <ul v-if="expanded === 'assets'" class="bs-list">
        <template v-for="account in assetAccounts" :key="account.id">
          <li class="bs-account-container">
            <div class="bs-row bs-row-asset" @click="toggleDetails(account.id)" role="button" tabindex="0" @keydown.enter="toggleDetails(account.id)" @keydown.space="toggleDetails(account.id)">
              <div class="bs-stripe bs-stripe-green"></div>
              <div class="bs-logo-container">
                <img v-if="account.institution_icon_url" :src="account.institution_icon_url" alt="Bank logo" class="bs-logo"
                  loading="lazy" />
                <span v-else class="bs-logo-fallback">{{ initials(account.name) }}</span>
              </div>
              <div class="bs-details">
                <div class="bs-name">
                  <span class="bs-toggle-icon" :class="{ 'bs-expanded': openAccountId === account.id }">▶</span>
                  {{ account.name }}
                </div>
                <div class="bs-mask">
                  <span v-if="account.mask">•••• {{ mask(account.mask) }}</span>
                  <span v-else class="bs-no-mask-icon" role="img" aria-label="Account number unavailable">∗</span>
                </div>
              </div>
              <div class="bs-sparkline">
                <AccountSparkline :account-id="account.id" />
              </div>
              <div class="bs-amount-section">
                <span class="bs-amount bs-amount-green">{{ format(account.adjusted_balance) }}</span>
              </div>
            </div>
          </li>
          <li v-if="openAccountId === account.id" class="bs-details-row">
            <div class="bs-details-content">
              <ul class="bs-details-list">
                <li v-for="tx in recentTxs[account.id]" :key="tx.id" class="bs-tx-row">
                  <span class="bs-tx-date">{{ tx.date }}</span>
                  <span class="bs-tx-name">{{ tx.name }}</span>
                  <span class="bs-tx-amount">{{ format(tx.amount) }}</span>
                </li>
                <li v-if="recentTxs[account.id]?.length === 0" class="bs-tx-empty">No recent transactions</li>
              </ul>
            </div>
          </li>
        </template>
        <!-- Assets summary footer -->
        <li v-if="assetAccounts.length" class="bs-summary-row">
          <div></div>
          <div class="bs-summary-label">Total Assets</div>
          <div class="bs-summary-amount bs-amount-green">
            {{ format(totalAssets) }}
          </div>
        </li>
      </ul>
    </Transition>

    <Transition name="bs-slide">
      <ul v-if="expanded === 'liabilities'" class="bs-list">
        <template v-for="account in liabilityAccounts" :key="account.id">
          <li class="bs-account-container">
            <div class="bs-row bs-row-liability" @click="toggleDetails(account.id)" role="button" tabindex="0" @keydown.enter="toggleDetails(account.id)" @keydown.space="toggleDetails(account.id)">
              <div class="bs-stripe bs-stripe-yellow"></div>
              <div class="bs-logo-container">
                <img v-if="account.institution_icon_url" :src="account.institution_icon_url" alt="Bank logo" class="bs-logo"
                  loading="lazy" />
                <span v-else class="bs-logo-fallback">{{ initials(account.name) }}</span>
              </div>
              <div class="bs-details">
                <div class="bs-name">
                  <span class="bs-toggle-icon" :class="{ 'bs-expanded': openAccountId === account.id }">▶</span>
                  {{ account.name }}
                </div>
                <div class="bs-mask">
                  <span v-if="account.mask">•••• {{ mask(account.mask) }}</span>
                  <span v-else class="bs-no-mask-icon" role="img" aria-label="Account number unavailable">∗</span>
                </div>
              </div>
              <div class="bs-sparkline">
                <AccountSparkline :account-id="account.id" />
              </div>
              <div class="bs-amount-section">
                <span class="bs-amount bs-amount-yellow">{{ format(account.adjusted_balance) }}</span>
              </div>
            </div>
          </li>
          <li v-if="openAccountId === account.id" class="bs-details-row">
            <div class="bs-details-content">
              <ul class="bs-details-list">
                <li v-for="tx in recentTxs[account.id]" :key="tx.id" class="bs-tx-row">
                  <span class="bs-tx-date">{{ tx.date }}</span>
                  <span class="bs-tx-name">{{ tx.name }}</span>
                  <span class="bs-tx-amount">{{ format(tx.amount) }}</span>
                </li>
                <li v-if="recentTxs[account.id]?.length === 0" class="bs-tx-empty">No recent transactions</li>
              </ul>
            </div>
          </li>
        </template>
        <!-- Liabilities summary footer -->
        <li v-if="liabilityAccounts.length" class="bs-summary-row">
          <div></div>
          <div class="bs-summary-label">Total Liabilities</div>
          <div class="bs-summary-amount bs-amount-yellow">
            {{ format(totalLiabilities) }}
          </div>
        </li>
      </ul>
    </Transition>

    <div
      v-if="((expanded === 'assets' && !assetAccounts.length) || (expanded === 'liabilities' && !liabilityAccounts.length))"
      class="bs-empty">
      No accounts available for this category.
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, toRef, onMounted } from 'vue'
import { useTopAccounts } from '@/composables/useTopAccounts'
import AccountSparkline from './AccountSparkline.vue'
import { fetchRecentTransactions } from '@/api/accounts'

const props = defineProps({
  accountSubtype: { type: String, default: '' },
})

const { allVisibleAccounts, fetchAccounts } = useTopAccounts(toRef(props, 'accountSubtype'))
onMounted(fetchAccounts)

// Details dropdown state
const openAccountId = ref(null)
const recentTxs = reactive({})

/** Toggle details dropdown for an account and load recent transactions */
function toggleDetails(accountId) {
  openAccountId.value = openAccountId.value === accountId ? null : accountId
  if (openAccountId.value === accountId && !recentTxs[accountId]) {
    fetchRecentTransactions(accountId, 3)
      .then((res) => {
        let txs = []
        if (Array.isArray(res?.transactions)) {
          txs = res.transactions
        } else if (Array.isArray(res?.data?.transactions)) {
          txs = res.data.transactions
        } else if (Array.isArray(res?.data)) {
          txs = res.data
        }
        recentTxs[accountId] = txs
      })
      .catch(() => {
        recentTxs[accountId] = []
      })
  }
}

const expanded = ref('assets')
const sortAsc = ref(false)

function toggle(type) {
  expanded.value = expanded.value === type ? null : type
}

function toggleSort() {
  sortAsc.value = !sortAsc.value
}

const assetAccounts = computed(() =>
  allVisibleAccounts.value
    ? [...allVisibleAccounts.value]
      .filter(a => a.adjusted_balance >= 0)
      .sort((a, b) => (sortAsc.value ? 1 : -1) * (Math.abs(a.adjusted_balance) - Math.abs(b.adjusted_balance)))
      .slice(0, 7)
    : []
)
const liabilityAccounts = computed(() =>
  allVisibleAccounts.value
    ? [...allVisibleAccounts.value]
      .filter(a => a.adjusted_balance < 0)
      .sort((a, b) => (sortAsc.value ? 1 : -1) * (Math.abs(a.adjusted_balance) - Math.abs(b.adjusted_balance)))
      .slice(0, 7)
    : []
)

const totalAssets = computed(() =>
  assetAccounts.value.reduce((sum, a) => sum + a.adjusted_balance, 0)
)
const totalLiabilities = computed(() =>
  liabilityAccounts.value.reduce((sum, a) => sum + a.adjusted_balance, 0)
)

const format = (val) => {
  const formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
  if (typeof val !== 'number') return ''
  if (val < 0) {
    return `(${formatter.format(Math.abs(val))})`
  }
  return formatter.format(val)
}

  function mask(maskString) {
    if (!maskString) return null
    return maskString.toString().slice(-4)
  }
function initials(name) {
  if (!name) return '??'
  return name.split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2)
}
</script>

<style scoped>
/* Account details dropdown styles */
.bs-details-btn-section {
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
}
.bs-details-btn {
  background: none;
  border: none;
  color: var(--color-text-muted);
  font-size: 0.85rem;
  cursor: pointer;
  padding: 0.2rem 0.5rem;
  border-radius: 0.25rem;
  transition: background 0.2s;
}
.bs-details-btn:hover {
  background: var(--color-bg-dark);
}
.bs-details-row {
  grid-column: 1 / -1;
  background: var(--color-bg-dark);
  padding: 0.5rem 1rem;
}
.bs-details-content {
  font-size: 0.85rem;
  color: var(--color-text-light);
}
.bs-details-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.bs-tx-row {
  display: flex;
  justify-content: space-between;
  padding: 0.25rem 0;
  border-bottom: 1px solid var(--divider);
}
.bs-tx-date {
  flex: 0 0 auto;
  width: 5ch;
  color: var(--color-text-muted);
}
.bs-tx-name {
  flex: 1 1 auto;
  padding: 0 0.5rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.bs-tx-amount {
  flex: 0 0 auto;
  width: 7ch;
  text-align: right;
}
.bs-tx-empty {
  text-align: center;
  color: var(--color-text-muted);
  font-style: italic;
  padding: 0.5rem 0;
}
.bank-statement-list {
  max-width: unset;
  margin: 0;
  padding: 0;
  border-radius: 1.3rem;
  user-select: none;
  width: 100%;
  height: 100%;
  background: transparent;
  box-shadow: none;
  border: none;
}

.bs-toggle-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 0.7rem;
  margin-bottom: 1.1rem;
  background: transparent;
  border-radius: 1rem 1rem 0 0;
}

 .bs-tab {
  padding: 0.5rem 1rem;
  background: var(--color-bg-sec);
  color: var(--color-accent-cyan);
  border: 1px solid var(--divider);
  border-radius: 0.8rem 0.8rem 0 0;
  font-size: 1rem;
  font-weight: 600;
  transition: background 0.2s, color 0.2s;
  cursor: pointer;
  position: relative;
}

.bs-tab-active.bs-tab-assets {
  background: linear-gradient(90deg, var(--color-bg-dark) 70%, var(--color-accent-cyan) 100%);
  color: var(--color-accent-cyan);
  z-index: 2;
}

.bs-tab-active.bs-tab-liabilities {
  background: linear-gradient(90deg, var(--color-bg-dark) 70%, var(--color-accent-yellow) 100%);
  color: var(--color-accent-yellow);
  z-index: 2;
}

/* Hover state retains original gradient styling */

.bs-tab-liabilities:hover,
.bs-tab-liabilities:focus-visible {
  background: linear-gradient(90deg, var(--color-bg-dark) 85%, var(--color-accent-yellow) 100%);
  color: var(--color-accent-yellow);
}

.bs-sort-btn {
  padding: 0.4rem 0.8rem;
  background: var(--color-bg-sec);
  color: var(--color-accent-cyan);
  border: 1px solid var(--divider);
  border-radius: 0.8rem;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}
.bs-sort-btn:hover,
.bs-sort-btn:focus-visible {
  background: var(--color-accent-cyan);
  color: var(--color-bg-dark);
}

.bs-list {
  display: flex;
  flex-direction: column;
  gap: 1.46rem;
  /* Increased gap for more separation */
  margin: 0;
  padding: 0.22rem 0.22rem 0.22rem 0.16rem;
  list-style: none;
}

.bs-row {
  display: grid;
  grid-template-columns: auto 1fr auto auto;
  align-items: center;
  background: linear-gradient(90deg, var(--color-bg-dark) 80%, var(--color-bg-sec) 100%);
  border-radius: 11px;
  padding: 0.39rem 0.45rem 0.39rem 0.1rem;
  box-shadow: 0 2px 14px var(--shadow, #1c274055);
  position: relative;
  border: 2px solid var(--color-accent-cyan);
  min-height: 36px;
  gap: 0.45rem;
  will-change: transform, box-shadow;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s ease;
}

.bs-row:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 20px var(--shadow, #1c274077);
  border-color: var(--color-accent-cyan);
}

.bs-row:focus {
  outline: 2px solid var(--color-accent-cyan);
  outline-offset: 2px;
}

.bs-row:active {
  transform: translateY(0);
}

.bs-row-asset {
  border-left: 6px solid var(--color-accent-cyan);
}

.bs-row-liability {
  border-left: 6px solid var(--color-accent-yellow);
}

.bs-sparkline {
  width: 60px;
  height: 20px;
  align-self: center;
}

.bs-row-asset .bs-sparkline {
  color: var(--color-accent-cyan);
}

.bs-row-liability .bs-sparkline {
  color: var(--color-accent-yellow);
}

.bs-no-mask-icon {
  display: inline-block;
  color: var(--color-accent-cyan);
  font-size: 0.8rem;
}

.bs-stripe {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 6px;
  border-radius: 8px 0 0 8px;
  z-index: 1;
  opacity: 0.75;
  pointer-events: none;
}

.bs-stripe-green {
  background: linear-gradient(180deg, var(--color-accent-cyan) 20%, var(--color-accent-blue) 100%);
}

.bs-stripe-yellow {
  background: linear-gradient(180deg, var(--color-accent-yellow) 20%, #ffe89b 100%);
}

.bs-logo-container {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-bg-dark);
  box-shadow: 0 2px 10px var(--shadow, #364b7a16);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
  border: 1.7px solid var(--color-accent-cyan);
  overflow: hidden;
}

.bs-logo {
  width: 20px;
  height: 20px;
  object-fit: contain;
  display: block;
  border-radius: 50%;
  background: #fff;
}

.bs-logo-fallback {
  font-size: 0.89rem;
  font-weight: 700;
  color: var(--color-accent-cyan);
  text-align: center;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--color-bg-sec);
}

.bs-details {
  min-width: 0;
  flex: 1 1 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  z-index: 2;
  overflow: hidden;
}

.bs-name {
  font-size: 0.97rem;
  font-weight: 600;
  color: var(--color-accent-cyan);
  letter-spacing: 0.01em;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
  max-width: 100%;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.bs-toggle-icon {
  font-size: 0.7rem;
  color: var(--color-accent-cyan);
  transition: transform 0.3s ease;
  display: inline-block;
  opacity: 0.8;
  flex-shrink: 0;
}

.bs-toggle-icon.bs-expanded {
  transform: rotate(90deg);
  opacity: 1;
}

.bs-row:hover .bs-toggle-icon {
  opacity: 1;
  color: var(--color-accent-cyan);
}

.bs-mask {
  font-size: 0.81rem;
  color: var(--color-accent-cyan);
  opacity: 0.87;
  margin-top: 1px;
  letter-spacing: 0.03em;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
  max-width: 100%;
}

.bs-amount-section {
  display: flex;
  align-items: flex-end;
  justify-content: flex-end;
  height: 100%;
  z-index: 2;
}

.bs-amount {
  font-size: 1.01rem;
  font-weight: 700;
  letter-spacing: 0.01em;
  min-width: 4.6ch;
  text-align: right;
  padding-right: 0.13em;
  margin-left: 0.2em;
  word-break: keep-all;
}

.bs-amount-green {
  color: var(--color-accent-cyan);
}

.bs-amount-yellow {
  color: var(--color-accent-yellow);
}

.bs-empty {
  color: var(--color-text-muted);
  font-style: italic;
  padding: 1.2rem 0 0.7rem 0;
  text-align: center;
  font-size: 1.01rem;
}

.bs-summary-row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  border-top: 1.5px solid var(--color-accent-cyan);
  margin-top: 0.12rem;
  padding: 0.18rem 0.12rem 0.12rem 0.06rem;
  background: transparent;
  min-height: 24px;
}

.bs-summary-label {
  font-size: 0.91rem;
  color: var(--color-text-muted);
  font-weight: 600;
  text-align: right;
}

.bs-summary-amount {
  font-size: 1.02rem;
  font-weight: 700;
  text-align: right;
}

/* New account container and themed button styles */
.bs-account-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.bs-details-btn-row {
  display: flex;
  justify-content: center;
  padding: 0.2rem 0.8rem;
}

.bs-details-btn-themed {
  background: linear-gradient(135deg, var(--color-bg-sec) 0%, var(--color-bg-dark) 100%);
  border: 1px solid var(--color-accent-cyan);
  color: var(--color-accent-cyan);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  padding: 0.4rem 0.8rem;
  border-radius: 0.6rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 0.3rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(4px);
  letter-spacing: 0.02em;
}

.bs-details-btn-themed:hover {
  background: linear-gradient(135deg, var(--color-accent-cyan) 0%, var(--color-accent-blue) 100%);
  color: var(--color-bg-dark);
  border-color: var(--color-accent-cyan);
  box-shadow: 0 4px 16px rgba(99, 205, 207, 0.3);
  transform: translateY(-1px);
}

.bs-details-btn-themed:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.bs-btn-icon {
  font-size: 0.7rem;
  opacity: 0.8;
  transition: opacity 0.2s;
}

.bs-details-btn-themed:hover .bs-btn-icon {
  opacity: 1;
}

/* Animations */
.bs-slide-enter-active,
.bs-slide-leave-active {
  transition: all 0.45s cubic-bezier(.44, .11, .42, 1.07);
}

.bs-slide-enter-from {
  opacity: 0;
  transform: translateY(-12px) scale(0.98);
}

.bs-slide-leave-to {
  opacity: 0;
  transform: translateY(-15px) scale(0.97);
}

/* Responsive */
@media (max-width: 630px) {
  .bank-statement-list {
    padding: 0.18rem 0.08rem 0.45rem 0.08rem;
    max-width: 99vw;
  }

  .bs-tab {
    padding: 0.54rem 0.9rem 0.54rem 0.8rem;
    font-size: 0.89rem;
  }

  .bs-sort-btn {
    padding: 0.45rem 0.75rem;
    font-size: 0.8rem;
  }

  .bs-list {
    padding: 0.1rem 0.05rem 0.1rem 0.05rem;
  }

  .bs-row {
    padding: 0.32rem 0.22rem 0.32rem 0.05rem;
    min-height: 27px;
  }

  .bs-summary-row {
    padding: 0.12rem 0.08rem 0.09rem 0.04rem;
  }
}
</style>
/* Account details dropdown styles */
.bs-details-btn-section {
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
}
.bs-details-btn {
  background: none;
  border: none;
  color: var(--color-text-muted);
  font-size: 0.85rem;
  cursor: pointer;
  padding: 0.2rem 0.5rem;
  border-radius: 0.25rem;
  transition: background 0.2s;
}
.bs-details-btn:hover {
  background: var(--color-bg-dark);
}
.bs-details-row {
  grid-column: 1 / -1;
  background: var(--color-bg-dark);
  padding: 0.5rem 1rem;
}
.bs-details-content {
  font-size: 0.85rem;
  color: var(--color-text-light);
}
.bs-details-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.bs-tx-row {
  display: flex;
  justify-content: space-between;
  padding: 0.25rem 0;
  border-bottom: 1px solid var(--divider);
}
.bs-tx-date {
  flex: 0 0 auto;
  width: 5ch;
  color: var(--color-text-muted);
}
.bs-tx-name {
  flex: 1 1 auto;
  padding: 0 0.5rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.bs-tx-amount {
  flex: 0 0 auto;
  width: 7ch;
  text-align: right;
}
.bs-tx-empty {
  text-align: center;
  color: var(--color-text-muted);
  font-style: italic;
  padding: 0.5rem 0;
}
