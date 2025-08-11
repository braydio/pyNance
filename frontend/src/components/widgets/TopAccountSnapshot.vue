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
        <li v-for="account in assetAccounts" :key="account.id" class="bs-row bs-row-asset">
          <div class="bs-stripe bs-stripe-green"></div>
          <div class="bs-logo-container">
            <img v-if="account.institution_icon_url" :src="account.institution_icon_url" alt="Bank logo" class="bs-logo"
              loading="lazy" />
            <span v-else class="bs-logo-fallback">{{ initials(account.name) }}</span>
          </div>
          <div class="bs-details">
            <div class="bs-name">{{ account.name }}</div>
            <div class="bs-mask">
              <span v-if="account.mask">•••• {{ mask(account.mask) }}</span>
              <span v-else class="bs-no-mask-icon" role="img" aria-label="Account number unavailable">✱</span>
            </div>
          </div>
          <div class="bs-sparkline">
            <AccountSparkline :account-id="account.id" />
          </div>
          <div class="bs-amount-section">
            <span class="bs-amount bs-amount-green">
              +{{ format(account.adjusted_balance) }}
            </span>
          </div>
        </li>
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
        <li v-for="account in liabilityAccounts" :key="account.id" class="bs-row bs-row-liability">
          <div class="bs-stripe bs-stripe-yellow"></div>
          <div class="bs-logo-container">
            <img v-if="account.institution_icon_url" :src="account.institution_icon_url" alt="Bank logo" class="bs-logo"
              loading="lazy" />
            <span v-else class="bs-logo-fallback">{{ initials(account.name) }}</span>
          </div>
          <div class="bs-details">
            <div class="bs-name">{{ account.name }}</div>
            <div class="bs-mask">
              <span v-if="account.mask">•••• {{ mask(account.mask) }}</span>
              <span v-else class="bs-no-mask-icon" role="img" aria-label="Account number unavailable">✱</span>
            </div>
          </div>
          <div class="bs-sparkline">
            <AccountSparkline :account-id="account.id" />
          </div>
          <div class="bs-amount-section">
            <span class="bs-amount bs-amount-yellow">
              –{{ format(account.adjusted_balance) }}
            </span>
          </div>
        </li>
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
import { ref, computed, toRef, onMounted } from 'vue'
import { useTopAccounts } from '@/composables/useTopAccounts'
import AccountSparkline from './AccountSparkline.vue'

const props = defineProps({
  accountSubtype: { type: String, default: '' },
})

const { allVisibleAccounts, fetchAccounts } = useTopAccounts(toRef(props, 'accountSubtype'))
onMounted(fetchAccounts)

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

const format = val =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(val)

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
  padding: 0.7rem 1.5rem 0.7rem 1.1rem;
  background: var(--color-bg-dark);
  color: var(--color-accent-ice);
  border: none;
  border-radius: 0.9rem 0.9rem 0 0;
  font-size: 1.03rem;
  font-weight: 600;
  transition: background 0.17s, color 0.17s;
  cursor: pointer;
  box-shadow: 0 1px 6px var(--shadow, #2a448a0d);
  position: relative;
}

.bs-tab-active.bs-tab-assets {
  background: linear-gradient(90deg, var(--color-bg-dark) 70%, var(--color-accent-mint) 100%);
  color: var(--color-accent-mint);
  z-index: 2;
}

.bs-tab-active.bs-tab-liabilities {
  background: linear-gradient(90deg, var(--color-bg-dark) 70%, var(--color-accent-yellow) 100%);
  color: var(--color-accent-yellow);
  z-index: 2;
}

.bs-tab-assets:hover,
.bs-tab-assets:focus-visible {
  background: linear-gradient(90deg, var(--color-bg-dark) 90%, var(--color-accent-mint) 100%);
  color: var(--color-accent-mint);
}

.bs-tab-liabilities:hover,
.bs-tab-liabilities:focus-visible {
  background: linear-gradient(90deg, var(--color-bg-dark) 85%, var(--color-accent-yellow) 100%);
  color: var(--color-accent-yellow);
}

.bs-sort-btn {
  padding: 0.55rem 0.9rem;
  background: var(--color-bg-dark);
  color: var(--color-accent-ice);
  border: none;
  border-radius: 0.9rem;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.17s, color 0.17s;
  box-shadow: 0 1px 6px var(--shadow, #2a448a0d);
}
.bs-sort-btn:hover,
.bs-sort-btn:focus-visible {
  background: var(--color-accent-ice);
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
  border: 2px solid var(--color-accent-ice);
  min-height: 36px;
  gap: 0.45rem;
  will-change: transform, box-shadow;
  overflow: hidden;
}

.bs-row-asset {
  border-left: 6px solid var(--color-accent-mint);
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
  color: var(--color-accent-mint);
}

.bs-row-liability .bs-sparkline {
  color: var(--color-accent-yellow);
}

.bs-no-mask-icon {
  display: inline-block;
  color: var(--color-accent-ice);
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
  background: linear-gradient(180deg, var(--color-accent-mint) 20%, var(--color-accent-ice) 100%);
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
  border: 1.7px solid var(--color-accent-ice);
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
  color: var(--color-accent-ice);
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
  color: var(--color-accent-ice);
  letter-spacing: 0.01em;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
  max-width: 100%;
}

.bs-mask {
  font-size: 0.81rem;
  color: var(--color-accent-mint);
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
  color: var(--color-accent-mint);
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
  border-top: 1.5px solid var(--color-accent-ice);
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
