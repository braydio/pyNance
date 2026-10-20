<!-- InternalTransferScanner.vue - Transfer Review: confirm money moved between your own accounts -->
<template>
  <div class="space-y-4">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h2 class="text-xl font-bold">Transfer Review</h2>
        <p class="text-sm text-muted">
          Finds a withdrawal and a matching deposit between your own accounts so they stop counting
          as spending and income. Nothing changes until you confirm a pair.
        </p>
      </div>
      <UiButton type="button" size="sm" :disabled="loading" @click="scan">
        {{ loading ? 'Scanning...' : scanned ? 'Scan again' : 'Scan last 90 days' }}
      </UiButton>
    </div>

    <p v-if="scanned && !scanError" class="text-sm text-muted" data-testid="scan-summary">
      Scanned {{ range.start }} to {{ range.end }} · {{ visiblePairs.length }}
      {{ visiblePairs.length === 1 ? 'pair' : 'pairs' }} to review
      <span v-if="dismissedCount"> · {{ dismissedCount }} dismissed</span>
      <span v-if="truncated" data-testid="scan-loaded-only">
        · loaded pairs only, not every transfer</span
      >
    </p>
    <p v-if="truncated" class="text-sm text-muted" role="status" data-testid="scan-truncated">
      Results were limited to keep the review fast. Confirm or dismiss these, then scan again to see
      more.
    </p>

    <ul v-if="visiblePairs.length" class="space-y-4">
      <li
        v-for="pair in visiblePairs"
        :key="pair.pair_id"
        class="border p-4 rounded-md space-y-3"
        :data-testid="`pair-${pair.pair_id}`"
      >
        <div class="grid gap-3 sm:grid-cols-2">
          <div v-for="side in sidesOf(pair)" :key="side.role" class="text-sm">
            <p class="font-medium">{{ side.role }}</p>
            <p>{{ side.data.account_label }}</p>
            <p class="text-muted">{{ side.data.merchant }} · {{ side.data.date }}</p>
            <p class="font-medium">{{ formatSignedAmount(side.data.amount) }}</p>
          </div>
        </div>

        <div class="text-sm">
          <p class="font-medium">
            {{ pair.confidence_label === 'strong' ? 'Strong match' : 'Needs your review' }}
          </p>
          <ul class="list-disc pl-5 text-muted">
            <li v-for="line in evidenceLines(pair)" :key="line">{{ line }}</li>
          </ul>
        </div>

        <p v-if="errors[pair.pair_id]" class="text-sm text-negative" role="alert">
          {{ errors[pair.pair_id] }}
        </p>
        <div class="flex flex-wrap gap-2">
          <UiButton
            type="button"
            variant="primary"
            :disabled="busy[pair.pair_id]"
            @click="confirm(pair)"
          >
            {{ busy[pair.pair_id] ? 'Confirming...' : 'Confirm Pair' }}
          </UiButton>
          <UiButton
            type="button"
            variant="outline"
            :disabled="busy[pair.pair_id]"
            @click="dismiss(pair)"
          >
            Not a Transfer
          </UiButton>
        </div>
      </li>
    </ul>

    <p v-else-if="scanError" class="text-sm text-negative" role="alert">
      {{ scanError }}
    </p>
    <p v-else-if="scanned" class="text-sm text-muted" role="status">
      {{ confirmedCount ? 'All done. ' : '' }}No transfer pairs left to review.
    </p>
    <p v-if="confirmedCount" class="text-sm text-muted" role="status" data-testid="confirmed-count">
      {{ confirmedCount }} {{ confirmedCount === 1 ? 'pair' : 'pairs' }} confirmed as transfers.
    </p>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import api from '@/services/api.js'
import UiButton from '@/components/ui/Button.vue'

const pairs = ref([])
const loading = ref(false)
const scanned = ref(false)
const scanError = ref('')
const truncated = ref(false)
const range = ref({ start: '', end: '' })
const dismissed = reactive({})
const confirmed = reactive({})
const busy = reactive({})
const errors = reactive({})

const visiblePairs = computed(() =>
  pairs.value.filter((p) => !dismissed[p.pair_id] && !confirmed[p.pair_id]),
)
const dismissedCount = computed(() => Object.keys(dismissed).length)
const confirmedCount = computed(() => Object.keys(confirmed).length)

/** Turn an API failure into a short, actionable message. */
function describeError(err, fallback) {
  const data = err?.response?.data
  if (data?.code === 'owner_not_configured') {
    return 'Transfer review is not set up on this server yet (PYNANCE_OWNER_USER_ID is missing).'
  }
  return data?.message || fallback
}

async function scan() {
  loading.value = true
  scanError.value = ''
  try {
    const res = await api.scanInternalTransfers()
    pairs.value = res.pairs || []
    truncated.value = Boolean(res.truncated)
    range.value = res.range || { start: '', end: '' }
    Object.keys(dismissed).forEach((key) => delete dismissed[key])
  } catch (err) {
    console.error('Failed to scan internal transfers:', err)
    pairs.value = []
    scanError.value = describeError(err, 'Unable to scan for internal transfers. Try again.')
  } finally {
    scanned.value = true
    loading.value = false
  }
}

async function confirm(pair) {
  busy[pair.pair_id] = true
  delete errors[pair.pair_id]
  try {
    await api.updateTransaction({
      transaction_id: pair.left.transaction_id,
      is_internal: true,
      counterpart_transaction_id: pair.right.transaction_id,
      flag_counterpart: true,
    })
    confirmed[pair.pair_id] = true
  } catch (err) {
    console.error('Failed to confirm transfer pair:', err)
    errors[pair.pair_id] = describeError(err, 'Could not confirm this pair. Nothing was changed.')
  } finally {
    busy[pair.pair_id] = false
  }
}

/** Hide a pair for this session only; it is not remembered after the next scan. */
function dismiss(pair) {
  dismissed[pair.pair_id] = true
}

function sidesOf(pair) {
  return [
    { role: 'Money out', data: pair.left },
    { role: 'Money in', data: pair.right },
  ]
}

function evidenceLines(pair) {
  const e = pair.evidence || {}
  const lines = []
  lines.push(
    e.amount_gap_cents
      ? `Amounts differ by $${(e.amount_gap_cents / 100).toFixed(2)}`
      : 'Exact same amount',
  )
  lines.push(
    e.day_gap
      ? `Posted ${e.day_gap} ${e.day_gap === 1 ? 'day' : 'days'} apart`
      : 'Posted the same day',
  )
  if (e.transfer_keyword) lines.push('Both descriptions mention a transfer or payment')
  if (e.shared_tokens?.length) lines.push(`Shared words: ${e.shared_tokens.join(', ')}`)
  return lines
}

function formatSignedAmount(amount) {
  const numeric = Number(amount) || 0
  return `${numeric >= 0 ? '+' : '-'}$${Math.abs(numeric).toFixed(2)}`
}
</script>
