import { useToast } from 'vue-toastification'

const REFRESH_TOAST_ID = 'global-refresh-status'

/**
 * Create shared refresh toast helpers so all refresh actions use consistent,
 * low-obtrusion notification copy and timing.
 *
 * @returns {{
 *   notifyRefreshStarted: (message?: string) => void,
 *   notifyRefreshSuccess: (message?: string) => void,
 *   notifyRefreshError: (message?: string) => void
 * }} Shared refresh notification functions.
 */
export function useRefreshNotification() {
  const toast = useToast()

  /**
   * Announce the start of a refresh operation.
   *
   * @param {string} [message='Refreshing data…'] - Optional override copy.
   */
  function notifyRefreshStarted(message = 'Refreshing data…') {
    toast.info(message, {
      timeout: 1800,
      toastId: REFRESH_TOAST_ID,
    })
  }

  /**
   * Announce successful completion of a refresh.
   *
   * @param {string} [message='Refresh complete.'] - Optional override copy.
   */
  function notifyRefreshSuccess(message = 'Refresh complete.') {
    toast.success(message, {
      timeout: 2200,
      toastId: REFRESH_TOAST_ID,
    })
  }

  /**
   * Announce a refresh failure.
   *
   * @param {string} [message='Refresh failed. Please try again.'] - Optional override copy.
   */
  function notifyRefreshError(message = 'Refresh failed. Please try again.') {
    toast.error(message, {
      timeout: 2600,
      toastId: REFRESH_TOAST_ID,
    })
  }

  return {
    notifyRefreshStarted,
    notifyRefreshSuccess,
    notifyRefreshError,
  }
}
