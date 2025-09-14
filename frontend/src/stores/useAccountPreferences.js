import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

// useAccountPreferences
// Manages per-account preferences like selected chart range and persists to localStorage.
export const useAccountPreferences = defineStore('accountPreferences', () => {
  // Mapping of accountId -> selectedRange
  const selectedRanges = ref({})

  // Initialize from localStorage if available
  try {
    const stored = JSON.parse(localStorage.getItem('accountPreferences'))
    if (stored?.selectedRanges) {
      selectedRanges.value = stored.selectedRanges
    }
  } catch (_) {
    // ignore malformed JSON
  }

  // Persist ranges whenever they change
  watch(
    selectedRanges,
    (val) => {
      localStorage.setItem('accountPreferences', JSON.stringify({ selectedRanges: val }))
    },
    { deep: true },
  )

  /**
   * Get stored range for an account, defaulting to '30d'.
   * @param {string} accountId
   * @returns {string}
   */
  function getSelectedRange(accountId) {
    return selectedRanges.value[accountId] || '30d'
  }

  /**
   * Update selected range for an account.
   * @param {string} accountId
   * @param {string} range
   */
  function setSelectedRange(accountId, range) {
    selectedRanges.value[accountId] = range
  }

  return { selectedRanges, getSelectedRange, setSelectedRange }
})
