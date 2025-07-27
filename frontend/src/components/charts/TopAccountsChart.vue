<template>
  <div class="bank-statement-list card bs-collapsible">
    <div class="bs-toggle-row">
      <button :class="['bs-tab', expanded === 'assets' && 'bs-tab-active', 'bs-tab-assets']" @click="toggle('assets')"
        aria-label="Show Assets">
        Assets
      </button>
      <button :class="['bs-tab', expanded === 'liabilities' && 'bs-tab-active', 'bs-tab-liabilities']"
        @click="toggle('liabilities')" aria-label="Show Liabilities">
        Liabilities
      </button>
      <span class="bs-net-amount" :class="netTotal >= 0 ? 'bs-net-green' : 'bs-net-red'">
        Net: {{ format(netTotal) }}
      </span>
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
            <div class="bs-mask">•••• {{ mask(account.mask) }}</div>
          </div>
          <div class="bs-amount-section">
            <span class="bs-amount bs-amount-green">
              +{{ format(account.adjusted_balance) }}
            </span>
          </div>
        </li>
      </ul>
    </Transition>

    <Transition name="bs-slide">
      <ul v-if="expanded === 'liabilities'" class="bs-list">
        <li v-for="account in liabilityAccounts" :key="account.id" class="bs-row bs-row-liability">
          <div class="bs-stripe bs-stripe-red"></div>
          <div class="bs-logo-container">
            <img v-if="account.institution_icon_url" :src="account.institution_icon_url" alt="Bank logo" class="bs-logo"
              loading="lazy" />
            <span v-else class="bs-logo-fallback">{{ initials(account.name) }}</span>
          </div>
          <div class="bs-details">
            <div class="bs-name">{{ account.name }}</div>
            <div class="bs-mask">•••• {{ mask(account.mask) }}</div>
          </div>
          <div class="bs-amount-section">
            <span class="bs-amount bs-amount-red">
              –{{ format(account.adjusted_balance) }}
            </span>
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

const props = defineProps({
  accountSubtype: { type: String, default: '' },
})

const { allVisibleAccounts, fetchAccounts } = useTopAccounts(toRef(props, 'accountSubtype'))
onMounted(fetchAccounts)

const expanded = ref('assets')

function toggle(type) {
  expanded.value = expanded.value === type ? null : type
}

const assetAccounts = computed(() =>
  allVisibleAccounts.value
    ? [...allVisibleAccounts.value]
      .filter(a => a.adjusted_balance >= 0)
      .sort((a, b) => Math.abs(b.adjusted_balance) - Math.abs(a.adjusted_balance))
      .slice(0, 5)
    : []
)
const liabilityAccounts = computed(() =>
  allVisibleAccounts.value
    ? [...allVisibleAccounts.value]
      .filter(a => a.adjusted_balance < 0)
      .sort((a, b) => Math.abs(b.adjusted_balance) - Math.abs(a.adjusted_balance))
      .slice(0, 5)
    : []
)
const netTotal = computed(() => assetAccounts.value.reduce((sum, a) => sum + a.adjusted_balance, 0) +
  liabilityAccounts.value.reduce((sum, a) => sum + a.adjusted_balance, 0))

const format = val =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(val)

function mask(maskString) {
  if (!maskString) return '----'
  return maskString.toString().slice(-4)
}
function initials(name) {
  if (!name) return '??'
  return name.split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2)
}
</script>

<style scoped>
@reference "../../assets/css/main.css";

.bank-statement-list {
  max-width: 550px;
  margin: 1.5rem auto;
  padding: 0.1rem 0.1rem 1rem 0.1rem;
  border-radius: 1.3rem;
  background: #1a2340;
  box-shadow: 0 4px 36px #193e854d;
  border: 1.5px solid #22356a;
  user-select: none;
}

.bs-toggle-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 0.7rem;
  margin-bottom: 1.25rem;
  background: transparent;
  border-radius: 1rem 1rem 0 0;
}

.bs-tab {
  padding: 1.05rem 2.2rem 1.05rem 1.5rem;
  background: #232f53;
  color: #b5cdf6;
  border: none;
  border-radius: 0.9rem 0.9rem 0 0;
  font-size: 1.11rem;
  font-weight: 600;
  transition: background 0.17s, color 0.17s;
  cursor: pointer;
  box-shadow: 0 1px 6px #2a448a0d;
  position: relative;
}

.bs-tab-active.bs-tab-assets {
  background: linear-gradient(90deg, #182e5d 60%, #19e68a23 100%);
  color: #7cf2bf;
  z-index: 2;
}

.bs-tab-active.bs-tab-liabilities {
  background: linear-gradient(90deg, #213b6a 60%, #fa606023 100%);
  color: #ffa9a9;
  z-index: 2;
}

.bs-tab-assets:hover,
.bs-tab-assets:focus-visible {
  background: linear-gradient(90deg, #233d7a 90%, #19e68a23 100%);
  color: #8df6c5;
}

.bs-tab-liabilities:hover,
.bs-tab-liabilities:focus-visible {
  background: linear-gradient(90deg, #25417e 80%, #fa606023 100%);
  color: #ffb1b1;
}

.bs-net-amount {
  margin-left: auto;
  padding: 0.7rem 1.1rem 0.7rem 1.2rem;
  font-size: 1.11rem;
  font-weight: 700;
  border-radius: 0.7rem;
  background: #203059;
  color: #a7f1e8;
  border: 1.1px solid #344e86;
  letter-spacing: 0.01em;
}

.bs-net-green {
  color: #78ffc9;
  background: #243f3c;
}

.bs-net-red {
  color: #ffb2b2;
  background: #3d2525;
}

.bs-list {
  display: flex;
  flex-direction: column;
  gap: 1.11rem;
  margin: 0;
  padding: 0.5rem 0.6rem 0.3rem 0.2rem;
  list-style: none;
}

/* Bank row styling */
.bs-row {
  display: flex;
  align-items: center;
  background: linear-gradient(90deg, #242f4d 80%, #253e70 100%);
  border-radius: 11px;
  padding: 0.89rem 1.1rem 0.89rem 0.1rem;
  box-shadow: 0 2px 14px #1c274055;
  position: relative;
  border: 1.5px solid #263c66;
  transition: box-shadow 0.17s, background 0.16s, transform 0.12s;
  min-height: 54px;
  gap: 1.08rem;
  will-change: transform, box-shadow;
  overflow: hidden;
}

.bs-row-asset {
  border-left: 6px solid #3cf8b2;
}

.bs-row-liability {
  border-left: 6px solid #ff8e8e;
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
  background: linear-gradient(180deg, #39ffab 20%, #19e68a 100%);
}

.bs-stripe-red {
  background: linear-gradient(180deg, #ff6262 20%, #fa6060 100%);
}

.bs-logo-container {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: #222c4b;
  box-shadow: 0 2px 10px #364b7a16;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 0.59rem;
  z-index: 2;
  border: 1.3px solid #243266;
  overflow: hidden;
}

.bs-logo {
  width: 34px;
  height: 34px;
  object-fit: contain;
  display: block;
  border-radius: 50%;
  background: #fff;
}

.bs-logo-fallback {
  font-size: 1.08rem;
  font-weight: 700;
  color: #bac3de;
  letter-spacing: 0.04em;
  text-align: center;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #37446d;
}

.bs-details {
  flex: 1 1 0;
  display: flex;
  flex-direction: column;
  min-width: 0;
  z-index: 2;
}

.bs-name {
  font-size: 1.10rem;
  font-weight: 600;
  color: #e4f1ff;
  letter-spacing: 0.01em;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
}

.bs-mask {
  font-size: 0.98rem;
  color: #8ca1d6;
  opacity: 0.83;
  margin-top: 2.5px;
  letter-spacing: 0.03em;
}

.bs-amount-section {
  display: flex;
  align-items: center;
  gap: 0.22rem;
  margin-left: 1.1rem;
  z-index: 2;
}

.bs-amount {
  font-size: 1.22rem;
  font-weight: 700;
  letter-spacing: 0.01em;
  min-width: 5.3ch;
  display: inline-block;
  text-align: right;
  padding-right: 0.15em;
  margin-left: 0.1em;
}

.bs-amount-green {
  color: #39ffab;
}

.bs-amount-red {
  color: #ff8e8e;
}

.bs-empty {
  color: #acb7d1;
  font-style: italic;
  padding: 1.2rem 0 0.7rem 0;
  text-align: center;
  font-size: 1.07rem;
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
    padding: 0.25rem 0.08rem 0.6rem 0.08rem;
    max-width: 99vw;
  }

  .bs-tab,
  .bs-net-amount {
    padding: 0.66rem 0.9rem 0.66rem 0.9rem;
    font-size: 0.96rem;
  }

  .bs-list {
    padding: 0.1rem 0.05rem 0.2rem 0.08rem;
  }

  .bs-row {
    padding: 0.62rem 0.35rem 0.62rem 0.05rem;
    min-height: 42px;
  }
}
</style>
