/**
 * Spending category composable.
 *
 * Manages selection state, grouping preferences, and dropdown options for
 * category and merchant breakdown views on the dashboard. Fetches supporting
 * data from category and merchant chart endpoints and handles automatic
 * selection of top results when none are chosen.
 */
import { computed, ref } from 'vue'
import { fetchCategoryTree } from '@/api/categories'
import { fetchMerchantBreakdown } from '@/api/charts'

type BreakdownType = 'category' | 'merchant'

export type CategoryOption = {
  id: string
  label: string
}

export type CategoryOptionGroup = {
  id: string
  label: string
  children: CategoryOption[]
}

type MerchantQuery = {
  start_date?: string
  end_date?: string
}

const AUTO_SELECT_LIMIT = 5

/**
 * Map a category tree payload into grouped dropdown options.
 *
 * @param raw - API response nodes representing category parents and children.
 * @returns Option groups with flattened children.
 */
function mapCategoryGroups(raw: any[] = []): CategoryOptionGroup[] {
  return raw
    .map((root) => ({
      id: String(root.id),
      label: root.label ?? root.name ?? 'Category',
      children: (root.children || []).map((child: any) => ({
        id: String(child.id),
        label: child.label ?? child.name ?? 'Category',
      })),
    }))
    .sort((a, b) => a.label.localeCompare(b.label))
}

/**
 * Normalize merchant breakdown data into a single option group.
 *
 * @param raw - Merchant breakdown rows.
 * @returns Grouped merchant options suitable for dropdown selection.
 */
function mapMerchantGroups(raw: any[] = []): CategoryOptionGroup[] {
  const children = (raw || [])
    .map((merchant) => ({
      id: String(merchant.label ?? merchant.id ?? merchant.name ?? ''),
      label: merchant.label ?? merchant.name ?? 'Merchant',
    }))
    .filter((child) => child.id)

  return children.length ? [{ id: 'merchants', label: 'Merchants', children }] : []
}

/**
 * Manage category and merchant selection state for spending breakdowns.
 *
 * Provides reactive selected IDs, grouping toggles, dropdown option data, and
 * helpers to reset or auto-select results emitted from chart payloads.
 */
export function useCategories() {
  const breakdownType = ref<BreakdownType>('category')
  const groupOthers = ref(true)
  const selectedIds = ref<string[]>([])
  const availableIds = ref<string[]>([])
  const categoryGroups = ref<CategoryOptionGroup[]>([])
  const merchantGroups = ref<CategoryOptionGroup[]>([])
  const autoSelected = ref(false)

  const groupedOptions = computed(() =>
    breakdownType.value === 'merchant' ? merchantGroups.value : categoryGroups.value,
  )

  /**
   * Fetch and cache grouped category dropdown options.
   */
  async function loadCategoryGroups(): Promise<void> {
    try {
      const response = await fetchCategoryTree()
      if (response.status === 'success' && Array.isArray(response.data)) {
        categoryGroups.value = mapCategoryGroups(response.data)
      } else {
        categoryGroups.value = []
      }
    } catch {
      categoryGroups.value = []
    }
  }

  /**
   * Fetch merchant breakdown rows and convert them to grouped options.
   *
   * @param params - Optional date filters to scope merchants.
   */
  async function loadMerchantGroups(params: MerchantQuery = {}): Promise<void> {
    try {
      const response = await fetchMerchantBreakdown({ top_n: 50, ...params })
      if (response.status === 'success') {
        merchantGroups.value = mapMerchantGroups(response.data || [])
      } else {
        merchantGroups.value = []
      }
    } catch {
      merchantGroups.value = []
    }
  }

  /**
   * Toggle aggregation of minor categories into the "Others" bucket.
   *
   * Resets auto-selection so the next dataset refresh can populate defaults.
   */
  function toggleGroupOthers(): void {
    groupOthers.value = !groupOthers.value
    autoSelected.value = false
  }

  /**
   * Track IDs emitted from the breakdown chart and auto-select the leading set
   * when the user has not chosen anything yet.
   *
   * @param ids - Flat list of category or merchant identifiers from the chart.
   */
  function setAvailableIds(ids: Array<string | number>): void {
    availableIds.value = (ids || []).map((id) => String(id))
    if (!selectedIds.value.length && availableIds.value.length && !autoSelected.value) {
      selectedIds.value = availableIds.value.slice(0, AUTO_SELECT_LIMIT)
      autoSelected.value = true
    }
  }

  /**
   * Update the current selection, normalizing IDs to strings.
   *
   * @param next - Selected IDs provided by the dropdown or custom handlers.
   */
  function updateSelection(next: string[] | string): void {
    selectedIds.value = Array.isArray(next) ? next.map((id) => String(id)) : [String(next)]
  }

  /**
   * Clear the current selection and allow the next dataset refresh to repopulate defaults.
   */
  function resetSelection(): void {
    selectedIds.value = []
    autoSelected.value = false
  }

  /**
   * Switch between category and merchant breakdowns, clearing the prior selection.
   *
   * @param mode - Breakdown dimension to activate.
   */
  function setBreakdownType(mode: BreakdownType): void {
    if (mode === breakdownType.value) return
    breakdownType.value = mode
    resetSelection()
  }

  /**
   * Refresh both category and merchant dropdown groups.
   *
   * @param params - Optional date filters applied to merchant queries.
   */
  async function refreshOptions(params: MerchantQuery = {}): Promise<void> {
    await Promise.all([loadCategoryGroups(), loadMerchantGroups(params)])
  }

  return {
    breakdownType,
    groupOthers,
    selectedIds,
    groupedOptions,
    categoryGroups,
    merchantGroups,
    loadCategoryGroups,
    loadMerchantGroups,
    refreshOptions,
    toggleGroupOthers,
    setAvailableIds,
    updateSelection,
    resetSelection,
    setBreakdownType,
  }
}
