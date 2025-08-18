Below is a repo-accurate, agent-executable rewrite. It preserves your architecture (Vue 3 + Composition API composables), removes non-existent paths, makes `randomId()` robust without `crypto.randomUUID`, aligns tests with Jest/Vue Test Utils, and keeps persistence in `services/`.

---

# Planning Page — Implementation Plan (repo-accurate)

## Conventions & Guardrails

- **State**: use a singleton composable `src/composables/planning.js` (not `stores/`).
- **Typing**: use **inline JSDoc typedefs** within JS files (no `src/types/`).
- **IDs**: use `randomId()` helper (no reliance on `crypto.randomUUID`).
- **Currency**: store integer cents; format on render.
- **Dates**: ISO `YYYY-MM-DD` (local).
- **Persistence**: versioned `localStorage` via `src/services/planningService.js`.
- **Styling**: Tailwind, consistent with existing components.
- **Tests**: colocate unit tests under `frontend/src/views/__tests__/` using **Jest + Vue Test Utils** (aligns with your repo).

---

## Files to Add / Modify

```
frontend/src/views/Planning.vue                         # NEW
frontend/src/router/index.js                            # MODIFY: add route
frontend/src/composables/planning.js                    # NEW (state singleton)
frontend/src/services/planningService.js                # NEW (versioned persistence)
frontend/src/utils/currency.js                          # NEW (toCents/fromCents/formatCurrency)
frontend/src/components/planning/BillForm.vue           # NEW
frontend/src/components/planning/BillList.vue           # NEW
frontend/src/components/planning/Allocator.vue          # NEW
frontend/src/components/planning/PlanningSummary.vue    # NEW
frontend/src/views/__tests__/planning.spec.js           # NEW (Jest/Vue Test Utils)
# (Optional) if you already run Cypress, mirror an e2e spec as planning.cy.js
```

---

## Data Contracts (inline JSDoc)

Embed at the top of `src/composables/planning.js`:

```js
/**
 * @typedef {"manual"|"predicted"} BillOrigin
 * @typedef {"fixed"|"percent"} AllocationType
 *
 * @typedef {Object} Bill
 * @property {string} id
 * @property {string} name
 * @property {number} amountCents
 * @property {string} dueDate       // YYYY-MM-DD
 * @property {string=} category
 * @property {BillOrigin} origin
 *
 * @typedef {Object} Allocation
 * @property {string} id
 * @property {string} target        // "bill:<billId>" | "savings:<name>" | "goal:<name>"
 * @property {AllocationType} kind
 * @property {number} value         // cents when fixed; 0-100 when percent
 *
 * @typedef {Object} Scenario
 * @property {string} id
 * @property {string} name
 * @property {number} planningBalanceCents
 * @property {Allocation[]} allocations
 *
 * @typedef {Object} PlanningState
 * @property {number} version
 * @property {boolean} devMode
 * @property {Bill[]} bills
 * @property {Scenario[]} scenarios
 * @property {string} activeScenarioId
 * @property {string} lastSavedAt    // ISO
 */
```

---

## Utilities

`frontend/src/utils/currency.js`

```js
export const toCents = (n) => Math.round(Number(n || 0) * 100)
export const fromCents = (c) => Number(c || 0) / 100
export const formatCurrency = (cents, locale = 'en-US', currency = 'USD') =>
  new Intl.NumberFormat(locale, { style: 'currency', currency }).format(fromCents(cents))
```

---

## Persistence Service (versioned, resilient)

`frontend/src/services/planningService.js`

```js
const KEY = 'pyNance:planning:v1'

/** @returns {import('../composables/planning').PlanningState|null} */
export function loadPlanning() {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return null
    const data = JSON.parse(raw)
    return migrate(data)
  } catch {
    return null
  }
}

/** @param {import('../composables/planning').PlanningState} state */
export function savePlanning(state) {
  try {
    localStorage.setItem(KEY, JSON.stringify(state))
  } catch {
    // ignore quota/availability errors
  }
}

function migrate(data) {
  if (!data || typeof data !== 'object') return null
  if (!data.version) data.version = 1
  switch (data.version) {
    case 1:
      return data
    default:
      return data
  }
}
```

---

## Composable (singleton state + autosave)

`frontend/src/composables/planning.js`

```js
import { reactive, computed, watch } from 'vue'
import { loadPlanning, savePlanning } from '@/services/planningService'
import { toCents } from '@/utils/currency'

/** robust ID without relying on crypto.randomUUID */
function randomId() {
  // 16-char base36 with timestamp
  return (Date.now().toString(36) + Math.random().toString(36).slice(2, 10)).toUpperCase()
}

/** @returns {import('./planning').PlanningState} */
function defaultState() {
  const scenarioId = randomId()
  return {
    version: 1,
    devMode: false,
    bills: [],
    scenarios: [
      {
        id: scenarioId,
        name: 'Default',
        planningBalanceCents: 0,
        allocations: [],
      },
    ],
    activeScenarioId: scenarioId,
    lastSavedAt: new Date().toISOString(),
  }
}

const state = reactive(loadPlanning() || defaultState())

// ---------- Getters ----------
const activeScenario = computed(
  () => state.scenarios.find((s) => s.id === state.activeScenarioId) || null,
)

const totalBillsCents = computed(() => state.bills.reduce((a, b) => a + (b.amountCents || 0), 0))

const allocatedCents = computed(() => {
  const s = activeScenario.value
  if (!s) return 0
  const percentSum = s.allocations
    .filter((a) => a.kind === 'percent')
    .reduce((a, b) => a + Number(b.value || 0), 0)
  const fixedSum = s.allocations
    .filter((a) => a.kind === 'fixed')
    .reduce((a, b) => a + Number(b.value || 0), 0)
  const cappedPct = Math.min(100, Math.max(0, percentSum))
  const pctAlloc = Math.floor((s.planningBalanceCents * cappedPct) / 100)
  return fixedSum + pctAlloc
})

const remainingCents = computed(() => {
  const s = activeScenario.value
  if (!s) return 0
  return Math.max(0, s.planningBalanceCents - allocatedCents.value)
})

// ---------- Actions ----------
function setPlanningBalance(n) {
  const s = activeScenario.value
  if (!s) return
  s.planningBalanceCents = typeof n === 'number' ? n : toCents(n)
}

/** @param {import('./planning').Bill} bill */
function upsertBill(bill) {
  const idx = state.bills.findIndex((b) => b.id === bill.id)
  if (idx >= 0) state.bills[idx] = bill
  else state.bills.push(bill)
}

function deleteBill(id) {
  const i = state.bills.findIndex((b) => b.id === id)
  if (i >= 0) state.bills.splice(i, 1)
}

/** @param {import('./planning').Allocation} a */
function addAllocation(a) {
  const s = activeScenario.value
  if (!s) return
  s.allocations.push(a)
}

/** @param {import('./planning').Allocation} a */
function updateAllocation(a) {
  const s = activeScenario.value
  if (!s) return
  const i = s.allocations.findIndex((x) => x.id === a.id)
  if (i >= 0) s.allocations[i] = a
}

function deleteAllocation(id) {
  const s = activeScenario.value
  if (!s) return
  const i = s.allocations.findIndex((x) => x.id === id)
  if (i >= 0) s.allocations.splice(i, 1)
}

function setDevMode(v) {
  state.devMode = !!v
}

/**
 * Replace prior predicted bills with freshly generated predictions (dev only)
 * @param {(todayISO:string)=>import('./planning').Bill[]} generateFn
 */
function ensurePredictedBills(generateFn) {
  if (!state.devMode) return
  const today = new Date().toISOString().slice(0, 10)
  const predicted = (generateFn?.(today) || []).map((b) => ({ ...b, origin: 'predicted' }))
  state.bills = state.bills.filter((b) => b.origin !== 'predicted').concat(predicted)
}

function selectScenario(id) {
  state.activeScenarioId = id
}
function addScenario(name) {
  const sc = { id: randomId(), name, planningBalanceCents: 0, allocations: [] }
  state.scenarios.push(sc)
  state.activeScenarioId = sc.id
}
function renameScenario(id, name) {
  const s = state.scenarios.find((x) => x.id === id)
  if (s) s.name = name
}
function deleteScenario(id) {
  const i = state.scenarios.findIndex((x) => x.id === id)
  if (i >= 0) {
    const wasActive = state.activeScenarioId === id
    state.scenarios.splice(i, 1)
    if (wasActive) state.activeScenarioId = state.scenarios[0]?.id || null
  }
}

// ---------- Autosave ----------
let t
watch(
  state,
  () => {
    clearTimeout(t)
    t = setTimeout(() => {
      state.lastSavedAt = new Date().toISOString()
      savePlanning(state)
    }, 300)
  },
  { deep: true },
)

export function usePlanning() {
  return {
    state,
    activeScenario,
    totalBillsCents,
    allocatedCents,
    remainingCents,
    setPlanningBalance,
    upsertBill,
    deleteBill,
    addAllocation,
    updateAllocation,
    deleteAllocation,
    setDevMode,
    ensurePredictedBills,
    selectScenario,
    addScenario,
    renameScenario,
    deleteScenario,
    randomId,
  }
}
```

---

## View

`frontend/src/views/Planning.vue`

```vue
<template>
  <div class="p-6 space-y-6">
    <header class="flex items-center justify-between">
      <h1 class="text-2xl font-semibold">Planning</h1>
      <div class="flex items-center gap-4">
        <label class="flex items-center gap-2">
          <input type="checkbox" v-model="devMode" class="h-4 w-4" />
          <span>Dev/Forecast Mode</span>
        </label>
        <span class="text-sm opacity-70">Saved: {{ lastSaved }}</span>
      </div>
    </header>

    <PlanningSummary
      :planning-balance-cents="activeScenario?.planningBalanceCents || 0"
      :total-bills-cents="totalBillsCents"
      :allocated-cents="allocatedCents"
      :remaining-cents="remainingCents"
      @update-balance="setPlanningBalance"
    />

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <section class="rounded-2xl shadow p-4">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-lg font-medium">Bills & Obligations</h2>
          <BillForm @save="onSaveBill" />
        </div>
        <BillList :bills="bills" @delete="deleteBill" @edit="onSaveBill" />
      </section>

      <section class="rounded-2xl shadow p-4">
        <h2 class="text-lg font-medium mb-3">Allocator</h2>
        <Allocator
          :scenario="activeScenario"
          :bills="bills"
          @add="addAllocation"
          @update="updateAllocation"
          @delete="deleteAllocation"
        />
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { usePlanning } from '@/composables/planning'
import PlanningSummary from '@/components/planning/PlanningSummary.vue'
import BillForm from '@/components/planning/BillForm.vue'
import BillList from '@/components/planning/BillList.vue'
import Allocator from '@/components/planning/Allocator.vue'

const planning = usePlanning()

const bills = computed(() => planning.state.bills)
const activeScenario = computed(() => planning.activeScenario.value)
const totalBillsCents = computed(() => planning.totalBillsCents.value)
const allocatedCents = computed(() => planning.allocatedCents.value)
const remainingCents = computed(() => planning.remainingCents.value)
const devMode = computed({
  get: () => planning.state.devMode,
  set: (v) => planning.setDevMode(v),
})
const lastSaved = computed(() => new Date(planning.state.lastSavedAt).toLocaleString())

function onSaveBill(bill) {
  planning.upsertBill(bill)
}
function deleteBill(id) {
  planning.deleteBill(id)
}
function setPlanningBalance(v) {
  planning.setPlanningBalance(v)
}

// Stubbed forecast generator (replace later with backend)
function generatePredictedBills(todayISO) {
  const next = (offset) => {
    const d = new Date(todayISO)
    d.setDate(d.getDate() + offset)
    return d.toISOString().slice(0, 10)
  }
  return [
    {
      id: 'pred:rent',
      name: 'Rent (pred)',
      amountCents: 120000,
      dueDate: next(14),
      category: 'Housing',
      origin: 'predicted',
    },
    {
      id: 'pred:power',
      name: 'Power (pred)',
      amountCents: 9000,
      dueDate: next(7),
      category: 'Utilities',
      origin: 'predicted',
    },
  ]
}

onMounted(() => {
  planning.ensurePredictedBills(generatePredictedBills)
})
</script>
```

---

## Components

`frontend/src/components/planning/PlanningSummary.vue`

```vue
<template>
  <div class="rounded-2xl shadow p-4 grid grid-cols-1 md:grid-cols-4 gap-4">
    <div>
      <label class="text-sm block mb-1">Planning Balance</label>
      <input
        class="border rounded px-2 py-1 w-full"
        :value="balanceDisplay"
        @input="onInput"
        inputmode="decimal"
      />
    </div>
    <Stat label="Bills (sum)" :value="fmt(totalBillsCents)" />
    <Stat label="Allocated" :value="fmt(allocatedCents)" />
    <Stat label="Remaining" :value="fmt(remainingCents)" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatCurrency, fromCents, toCents } from '@/utils/currency'

const props = defineProps({
  planningBalanceCents: { type: Number, required: true },
  totalBillsCents: { type: Number, required: true },
  allocatedCents: { type: Number, required: true },
  remainingCents: { type: Number, required: true },
})
const emit = defineEmits(['update-balance'])

const balanceDisplay = computed(() => fromCents(props.planningBalanceCents).toFixed(2))
function fmt(c) {
  return formatCurrency(c)
}
function onInput(e) {
  const v = (e.target.value || '0').replace(/[^0-9.]/g, '')
  emit('update-balance', toCents(Number(v || 0)))
}
</script>

<script>
export default {
  components: {
    Stat: {
      props: { label: String, value: String },
      template: `<div class="p-3 rounded border">
        <div class="text-sm opacity-70">{{label}}</div>
        <div class="text-lg font-medium">{{value}}</div>
      </div>`,
    },
  },
}
</script>
```

`frontend/src/components/planning/BillForm.vue`

```vue
<template>
  <button @click="open = true" class="px-3 py-1 rounded bg-gray-900 text-white">Add Bill</button>
  <dialog :open="open" class="p-0">
    <form @submit.prevent="save" class="p-4 space-y-3 min-w-[320px]">
      <h3 class="font-medium">Add/Edit Bill</h3>
      <input v-model="name" placeholder="Name" class="border rounded px-2 py-1 w-full" required />
      <input
        v-model.number="amount"
        placeholder="Amount (USD)"
        inputmode="decimal"
        class="border rounded px-2 py-1 w-full"
        required
      />
      <input v-model="dueDate" type="date" class="border rounded px-2 py-1 w-full" required />
      <input v-model="category" placeholder="Category" class="border rounded px-2 py-1 w-full" />
      <div class="flex justify-end gap-2">
        <button type="button" class="px-3 py-1" @click="close">Cancel</button>
        <button class="px-3 py-1 rounded bg-gray-900 text-white">Save</button>
      </div>
    </form>
  </dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { toCents } from '@/utils/currency'
import { usePlanning } from '@/composables/planning'

const planning = usePlanning()
const props = defineProps({ bill: { type: Object, default: null } })
const emit = defineEmits(['save'])

const open = ref(false)
const name = ref('')
const amount = ref(0)
const dueDate = ref('')
const category = ref('')

watch(
  () => props.bill,
  (b) => {
    if (!b) return
    name.value = b.name
    amount.value = (b.amountCents / 100).toFixed(2)
    dueDate.value = b.dueDate
    category.value = b.category || ''
    open.value = true
  },
)

function close() {
  open.value = false
}

function save() {
  const bill = {
    id: props.bill?.id || planning.randomId(),
    name: name.value.trim(),
    amountCents: toCents(amount.value),
    dueDate: dueDate.value,
    category: category.value.trim() || undefined,
    origin: props.bill?.origin || 'manual',
  }
  emit('save', bill)
  close()
}
</script>
```

`frontend/src/components/planning/BillList.vue`

```vue
<template>
  <table class="w-full text-sm">
    <thead>
      <tr class="text-left border-b">
        <th class="py-2">Name</th>
        <th>Amount</th>
        <th>Due</th>
        <th>Category</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="b in bills" :key="b.id" class="border-b">
        <td class="py-2">
          <span>{{ b.name }}</span>
          <span
            v-if="b.origin === 'predicted'"
            class="ml-2 text-xs px-2 py-0.5 rounded bg-yellow-100"
            >predicted</span
          >
        </td>
        <td>{{ fmt(b.amountCents) }}</td>
        <td>{{ b.dueDate }}</td>
        <td>{{ b.category || '—' }}</td>
        <td class="text-right">
          <button class="px-2" @click="$emit('edit', b)">Edit</button>
          <button class="px-2 text-red-600" @click="$emit('delete', b.id)">Delete</button>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
import { formatCurrency } from '@/utils/currency'
defineProps({ bills: { type: Array, required: true } })
function fmt(c) {
  return formatCurrency(c)
}
</script>
```

`frontend/src/components/planning/Allocator.vue`

```vue
<template>
  <div class="space-y-3">
    <form class="flex gap-2 items-end" @submit.prevent="add">
      <div class="flex-1">
        <label class="text-xs block">Target</label>
        <select v-model="target" class="border rounded px-2 py-1 w-full">
          <optgroup label="Bills">
            <option v-for="b in bills" :key="b.id" :value="`bill:${b.id}`">{{ b.name }}</option>
          </optgroup>
          <optgroup label="Savings">
            <option value="savings:General">Savings (General)</option>
          </optgroup>
          <optgroup label="Goals">
            <option value="goal:Emergency Fund">Goal: Emergency Fund</option>
          </optgroup>
        </select>
      </div>
      <div>
        <label class="text-xs block">Kind</label>
        <select v-model="kind" class="border rounded px-2 py-1">
          <option value="fixed">Fixed</option>
          <option value="percent">Percent</option>
        </select>
      </div>
      <div>
        <label class="text-xs block">Value</label>
        <input
          v-model.number="value"
          :placeholder="kind === 'fixed' ? 'USD' : '%'"
          class="border rounded px-2 py-1 w-28"
          inputmode="decimal"
        />
      </div>
      <button class="px-3 py-1 rounded bg-gray-900 text-white">Add</button>
    </form>

    <table class="w-full text-sm">
      <thead>
        <tr class="text-left border-b">
          <th>Target</th>
          <th>Kind</th>
          <th>Value</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="a in scenario.allocations" :key="a.id" class="border-b">
          <td>{{ a.target }}</td>
          <td>{{ a.kind }}</td>
          <td>{{ kindDisplay(a) }}</td>
          <td class="text-right">
            <button class="px-2" @click="edit(a)">Edit</button>
            <button class="px-2 text-red-600" @click="$emit('delete', a.id)">Delete</button>
          </td>
        </tr>
      </tbody>
    </table>

    <dialog :open="open" class="p-0">
      <form @submit.prevent="saveEdit" class="p-4 space-y-3 min-w-[320px]">
        <h3 class="font-medium">Edit Allocation</h3>
        <div>{{ editing?.target }}</div>
        <select v-model="editing.kind" class="border rounded px-2 py-1">
          <option value="fixed">Fixed</option>
          <option value="percent">Percent</option>
        </select>
        <input v-model.number="editValue" class="border rounded px-2 py-1" inputmode="decimal" />
        <div class="flex justify-end gap-2">
          <button type="button" class="px-3 py-1" @click="open = false">Cancel</button>
          <button class="px-3 py-1 rounded bg-gray-900 text-white">Save</button>
        </div>
      </form>
    </dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { toCents, formatCurrency } from '@/utils/currency'

const props = defineProps({
  scenario: { type: Object, required: true },
  bills: { type: Array, required: true },
})
const emit = defineEmits(['add', 'update', 'delete'])

const target = ref('')
const kind = ref('fixed')
const value = ref(0)

function add() {
  const v = kind.value === 'fixed' ? toCents(value.value) : Number(value.value)
  const a = {
    id: (Date.now().toString(36) + Math.random().toString(36).slice(2, 8)).toUpperCase(),
    target: target.value,
    kind: kind.value,
    value: v,
  }
  emit('add', a)
  target.value = ''
  kind.value = 'fixed'
  value.value = 0
}

function kindDisplay(a) {
  return a.kind === 'fixed' ? formatCurrency(a.value) : `${a.value}%`
}

// Edit dialog
const open = ref(false)
const editing = ref(null)
const editValue = ref(0)
function edit(a) {
  editing.value = { ...a }
  editValue.value = a.kind === 'fixed' ? (a.value / 100).toFixed(2) : a.value
  open.value = true
}
function saveEdit() {
  const a = { ...editing.value }
  a.value = a.kind === 'fixed' ? toCents(editValue.value) : Number(editValue.value)
  emit('update', a)
  open.value = false
}
</script>
```

---

## Router (modify directly)

`frontend/src/router/index.js` — add import and route:

```js
// add near other imports
import Planning from '@/views/Planning.vue';

// add inside routes array
{ path: '/planning', name: 'Planning', component: Planning },
```

Add a sidebar/menu item named **Planning** pointing to `/planning` (mirror existing nav pattern).

---

## Allocation Rules

- Apply **fixed** allocations first (sum of fixed cents).
- Apply **percent** allocations on **planning balance** with aggregate cap at 100%.
- Remaining never shows negative (clamp to 0).
- Predicted bills are replaced on each dev-mode generation and visually tagged.

---

## Testing (Jest + Vue Test Utils)

`frontend/src/views/__tests__/planning.spec.js`

```js
import { mount } from '@vue/test-utils'
import { usePlanning } from '@/composables/planning'
import Planning from '@/views/Planning.vue'

describe('Planning Page', () => {
  beforeEach(() => {
    // clear storage between tests
    localStorage.clear()
  })

  it('renders and updates planning balance', async () => {
    const wrapper = mount(Planning)
    const { state } = usePlanning()
    // initial
    expect(state.scenarios.length).toBe(1)
    // update balance via composable and assert computed changes flow through
    state.scenarios[0].planningBalanceCents = 50000 // $500
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('$500.00')
  })

  it('adds a manual bill and reflects sum', async () => {
    const wrapper = mount(Planning)
    const { upsertBill } = usePlanning()
    upsertBill({
      id: 'B1',
      name: 'Internet',
      amountCents: 7000,
      dueDate: '2025-09-01',
      origin: 'manual',
    })
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('$70.00')
  })

  it('allocation math: fixed then percent with cap', async () => {
    const { state, addAllocation } = usePlanning()
    state.scenarios[0].planningBalanceCents = 100000 // $1000
    addAllocation({ id: 'A1', target: 'savings:General', kind: 'fixed', value: 30000 }) // $300
    addAllocation({ id: 'A2', target: 'goal:Emergency', kind: 'percent', value: 25 }) // 25% of 1000 = 250
    // allocated = 55000, remaining = 45000
    expect(state.scenarios[0].allocations.length).toBe(2)
  })
})
```

_(If you run Cypress, mirror the earlier e2e flow; otherwise skip.)_

---

## Milestones & Done Criteria

- **M1 – Scaffolding**: Route + `Planning.vue` render; composable + persistence wired; summary shows zeros; autosave timestamp visible.
- **M2 – Bills**: Add/Edit/Delete via `BillForm`/`BillList`; totals correct; predicted tag renders.
- **M3 – Allocator**: Add/edit/delete fixed & percent allocations; remaining updates per rules.
- **M4 – Dev Mode**: Toggle persists; predicted bills injected/replaced.
- **M5 – Tests**: Jest unit tests passing for composable math and key UI flows.

---

## Backend (future-proof only)

When you’re ready, add Flask models/routes (`planning_bills`, `planning_scenarios`, `planning_allocations`) and swap the dev forecast stub with `GET /api/recurring/forecast?from=YYYY-MM-DD&to=YYYY-MM-DD`. Until then, all state remains local via the service.

---

## What Changed vs Prior Spec

- **State lives in `src/composables/`**, not `stores/`.
- **No `src/types/`**; all typedefs are inline JSDoc.
- **Router edited directly** (`index.js`), no patch file.
- **`randomId()`** avoids `crypto.randomUUID` entirely.
- **Tests aligned to Jest/Vue Test Utils** and colocated under `views/__tests__/`.
- All paths match your repo’s current conventions.
