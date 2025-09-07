import { describe, it, expect } from 'vitest'
import { nextTick } from 'vue'
import { useAccountGroups } from '../useAccountGroups.js'

describe('useAccountGroups', () => {
  it('initializes with at least one group and active id', () => {
    const { groups, activeGroupId } = useAccountGroups()
    expect(groups.value.length).toBeGreaterThan(0)
    expect(activeGroupId.value).toBe(groups.value[0].id)
  })

  it('maintains an active group when groups are cleared', async () => {
    const { groups, activeGroupId } = useAccountGroups()
    groups.value.splice(0, groups.value.length)
    await nextTick()
    expect(groups.value.length).toBe(1)
    expect(activeGroupId.value).toBe(groups.value[0].id)
  })
})
