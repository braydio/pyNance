// @vitest-environment jsdom
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref, computed } from 'vue'
import AccountSnapshot from '../AccountSnapshot.vue'

const pushMock = vi.hoisted(() => vi.fn())
const fetchRecentTransactionsMock = vi.hoisted(() => vi.fn())

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}))

vi.mock('@/api/transactions', () => ({
  fetchRecentTransactions: fetchRecentTransactionsMock,
}))

vi.mock('@/composables/useSnapshotAccounts.js', () => ({
  useSnapshotAccounts: () => {
    const selectedAccounts = ref([
      {
        account_id: 'acct-1',
        name: 'Everyday Checking',
        institution_name: 'PyNance Bank',
        balance: 1234.56,
      },
    ])
    const selectedIds = ref(['acct-1'])
    const reminders = ref([])
    const metadata = ref({ discarded_ids: [] })
    const maxSelection = computed(() => 5)
    const availableAccounts = ref([])
    const isLoading = ref(false)
    const isSaving = ref(false)
    const remindersLoading = ref(false)
    const error = ref(null)

    return {
      selectedAccounts,
      selectedIds,
      reminders,
      metadata,
      maxSelection,
      availableAccounts,
      isLoading,
      isSaving,
      remindersLoading,
      error,
      addAccount: vi.fn(),
      removeAccount: vi.fn(),
      refreshSnapshot: vi.fn().mockResolvedValue(),
      refreshReminders: vi.fn(),
    }
  },
}))

describe('AccountSnapshot navigation', () => {
  beforeEach(() => {
    pushMock.mockReset()
    fetchRecentTransactionsMock.mockReset()
  })

  it('opens transactions view with promote and account filters', async () => {
    fetchRecentTransactionsMock.mockResolvedValue({
      data: {
        transactions: [
          {
            transaction_id: 'tx-123',
            account_id: 'acct-1',
            amount: -45.67,
            name: 'Coffee Shop',
            date: '2024-02-01',
          },
        ],
      },
    })

    const wrapper = mount(AccountSnapshot)

    await wrapper.get('article button').trigger('click')
    await flushPromises()

    const txRow = wrapper.get('[data-testid="account-snapshot-transaction"]')
    await txRow.trigger('click')

    expect(pushMock).toHaveBeenCalledWith({
      name: 'Transactions',
      query: {
        promote: 'tx-123',
        account_id: 'acct-1',
      },
    })
  })

  it('falls back to the expanded account id when missing on the transaction payload', async () => {
    fetchRecentTransactionsMock.mockResolvedValue({
      data: {
        transactions: [
          {
            id: 'legacy-42',
            amount: 150,
            name: 'Refund',
            transaction_date: '2024-01-20',
          },
        ],
      },
    })

    const wrapper = mount(AccountSnapshot)

    await wrapper.get('article button').trigger('click')
    await flushPromises()

    const txRow = wrapper.get('[data-testid="account-snapshot-transaction"]')
    await txRow.trigger('keydown.enter')

    expect(pushMock).toHaveBeenCalledWith({
      name: 'Transactions',
      query: {
        promote: 'legacy-42',
        account_id: 'acct-1',
      },
    })
  })
})
