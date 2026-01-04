/**
 * Manage mutually exclusive dashboard overlays and modals.
 *
 * This composable centralizes modal state so only one overlay can be active at
 * a time, preventing stacked dialogs from blocking interactions. It exposes a
 * simple enum-style `currentModal` ref alongside helpers to open or close
 * modals deterministically.
 */
import { computed, ref } from 'vue'

export type DashboardModal = 'none' | 'daily' | 'category' | 'accounts' | 'transactions'

/**
 * Create modal state for the dashboard view with exclusivity guarantees.
 *
 * @param {DashboardModal} initial - Optional initial modal value, defaults to `'none'`.
 * @returns {{
 *   currentModal: import('vue').Ref<DashboardModal>;
 *   openModal: (modal: DashboardModal) => void;
 *   closeModal: (modal?: DashboardModal) => void;
 *   visibility: import('vue').ComputedRef<{
 *     daily: boolean;
 *     category: boolean;
 *     accounts: boolean;
 *     transactions: boolean;
 *   }>;
 * }}
 *   Reactive modal state and control helpers.
 */
export function useDashboardModals(initial: DashboardModal = 'none') {
  const currentModal = ref<DashboardModal>(initial)

  const visibility = computed(() => ({
    daily: currentModal.value === 'daily',
    category: currentModal.value === 'category',
    accounts: currentModal.value === 'accounts',
    transactions: currentModal.value === 'transactions',
  }))

  function openModal(modal: DashboardModal) {
    currentModal.value = modal
  }

  function closeModal(modal?: DashboardModal) {
    if (!modal || currentModal.value === modal) {
      currentModal.value = 'none'
    }
  }

  return {
    currentModal,
    openModal,
    closeModal,
    visibility,
  }
}
