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

const MODAL_KEYS: DashboardModal[] = ['none', 'daily', 'category', 'accounts', 'transactions']

/**
 * Create modal state for the dashboard view with exclusivity guarantees.
 *
 * @param {DashboardModal} initial - Optional initial modal value, defaults to `'none'`.
 * @returns {{
 *   currentModal: import('vue').Ref<DashboardModal>;
 *   openModal: (modal: DashboardModal) => void;
 *   closeModal: (modal?: DashboardModal) => void;
 *   isVisible: (modal: DashboardModal) => import('vue').ComputedRef<boolean>;
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
  const currentModal = ref<DashboardModal>(MODAL_KEYS.includes(initial) ? initial : 'none')

  const visibility = computed(() => ({
    daily: currentModal.value === 'daily',
    category: currentModal.value === 'category',
    accounts: currentModal.value === 'accounts',
    transactions: currentModal.value === 'transactions',
  }))

  function openModal(modal: DashboardModal) {
    currentModal.value = MODAL_KEYS.includes(modal) ? modal : 'none'
  }

  function closeModal(modal?: DashboardModal) {
    if (!modal || currentModal.value === modal) {
      currentModal.value = 'none'
    }
  }

  /**
   * Create a computed visibility flag for the provided modal name.
   *
   * @param {DashboardModal} modal - Target modal key to observe.
   * @returns {import('vue').ComputedRef<boolean>} Visibility flag that updates
   *   when the active modal changes.
   */
  function isVisible(modal: DashboardModal) {
    return computed(() => currentModal.value === modal)
  }

  return {
    currentModal,
    openModal,
    closeModal,
    isVisible,
    visibility,
  }
}
