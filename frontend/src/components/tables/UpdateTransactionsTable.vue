<template>
  <div class="transactions space-y-4 p-6 bg-gray-50 rounded-xl shadow">
    <VueToast v-if="toast.message" :type="toast.type" :message="toast.message" @close="toast.message = ''" />

    <table class="min-w-full divide-y divide-gray-200">
      <thead class="bg-gray-100 text-gray-700 text-sm font-semibold uppercase">
        <tr>
          <th class="px-3 py-2 cursor-pointer" @click="sortBy('date')">Date</th>
          <th class="px-3 py-2 cursor-pointer" @click="sortBy('amount')">Amount</th>
          <th class="px-3 py-2 cursor-pointer" @click="sortBy('description')">Description</th>
          <th class="px-3 py-2 cursor-pointer" @click="sortBy('category')">Category</th>
          <th class="px-3 py-2 cursor-pointer" @click="sortBy('merchant_name')">Merchant</th>
          <th class="px-3 py-2">Account</th>
          <th class="px-3 py-2">Institution</th>
          <th class="px-3 py-2">Subtype</th>
          <th class="px-3 py-2">Actions</th>
        </tr>
      </thead>

      <tbody>
        <tr v-for="(tx, index) in filteredTransactions" :key="tx.transaction_id"
          :class="['text-sm', editingIndex === index ? 'bg-yellow-100' : 'hover:bg-gray-100']">
          <td class="px-3 py-2">
            <input v-if="editingIndex === index" v-model="editBuffer.date" type="date" class="input" />
            <span v-else>{{ formatDate(tx.date) }}</span>
          </td>
          <td class="px-3 py-2">
            <input v-if="editingIndex === index" v-model.number="editBuffer.amount" type="number" step="0.01"
              class="input" />
            <span v-else>{{ formatAmount(tx.amount) }}</span>
          </td>
          <td class="px-3 py-2">
            <input v-if="editingIndex === index" v-model="editBuffer.description" type="text" class="input" />
            <span v-else>{{ tx.description }}</span>
          </td>
          <td class="px-3 py-2">
            <select v-if="editingIndex === index" v-model="editBuffer.category" class="input">
              <option disabled value="">-- Select Category --</option>
              <optgroup v-for="group in categoryTree" :label="group.name" :key="group.name">
                <option v-for="child in group.children" :key="child.id" :value="child.name">
                  {{ child.name }}
                </option>
              </optgroup>
            </select>
            <span v-else>{{ tx.category }}</span>
          </td>
          <td class="px-3 py-2">
            <input v-if="editingIndex === index" v-model="editBuffer.merchant_name" type="text" class="input" />
            <span v-else>{{ tx.merchant_name }}</span>
          </td>
          <!-- Non-editable account_name -->
          <td class="px-3 py-2">
            {{ tx.account_name || 'N/A' }}
          </td>

          <!-- Non-editable institution_name -->
          <td class="px-3 py-2">
            {{ tx.institution_name || 'N/A' }}
          </td>

          <!-- Non-editable subtype -->
          <td class="px-3 py-2">
            {{ tx.subtype || 'N/A' }}
          </td>
          <td class="px-3 py-2 space-x-1">
            <template v-if="editingIndex === index">
              <button class="btn-sm" @click="saveEdit(tx)">Save</button>
              <button class="btn-sm" @click="cancelEdit">Cancel</button>
            </template>
            <template v-else>
              <button class="btn-sm" @click="startEdit(index, tx)">Edit</button>
              <button class="btn-sm" @click="markRecurring(index)">Mark</button>
            </template>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.input {
  @apply w-full px-2 py-1 rounded border border-gray-300 bg-white text-gray-800 text-sm;
}

.input:focus {
  @apply outline-none ring-2 ring-blue-300;
}

.btn-sm {
  @apply inline-flex items-center px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700;
}
</style>
