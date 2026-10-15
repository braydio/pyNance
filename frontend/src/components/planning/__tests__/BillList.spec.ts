// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import BillList from '../BillList.vue'

const bills = [
  {
    id: 'b2',
    name: 'A really long bill name that should wrap instead of overflowing the planning column',
    amountCents: 12345,
    dueDate: '2026-11-20',
    frequency: 'monthly',
    origin: 'predicted',
    category: 'Utilities',
  },
  {
    id: 'b1',
    name: 'Rent',
    amountCents: 150000,
    dueDate: '2026-11-01',
    frequency: 'monthly',
    origin: 'manual',
  },
] as never[]

const mountList = () => mount(BillList, { props: { bills } })

describe('BillList', () => {
  it('lists the soonest due bill first with tabular amounts', () => {
    const rows = mountList().findAll('li')
    expect(rows[0].text()).toContain('Rent')
    expect(rows[1].text()).toContain('A really long bill name')
    expect(rows[0].find('.bill-row__amount').text()).toBe('$1,500.00')
  })

  it('expands row details from a keyboard-operable button and emits select', async () => {
    const wrapper = mountList()
    const toggle = wrapper.get('[data-testid="bill-toggle-b2"]')
    expect(toggle.element.tagName).toBe('BUTTON')
    expect(toggle.attributes('aria-expanded')).toBe('false')
    await toggle.trigger('click')
    expect(toggle.attributes('aria-expanded')).toBe('true')
    const details = wrapper.get('[data-testid="bill-details-b2"]')
    expect(details.attributes('id')).toBe(toggle.attributes('aria-controls'))
    expect(details.text()).toContain('Utilities')
    expect(details.text()).toContain('Predicted from recurring transaction history')
    expect(wrapper.emitted('select')?.[0][0]).toMatchObject({ id: 'b2' })
  })

  it('explains the Predicted badge', () => {
    const badge = mountList().get('.predicted-badge')
    expect(badge.attributes('title')).toContain('not entered by you')
  })

  it('separates edit and delete and requires confirmation before deleting', async () => {
    const wrapper = mountList()
    await wrapper.get('[data-testid="bill-delete-b1"]').trigger('click')
    expect(wrapper.emitted('delete')).toBeUndefined()
    expect(wrapper.text()).toContain('Delete “Rent”?')
    await wrapper.get('[data-testid="bill-delete-confirm-b1"]').trigger('click')
    expect(wrapper.emitted('delete')?.[0]).toEqual(['b1'])

    const again = mountList()
    await again.get('[data-testid="bill-delete-b1"]').trigger('click')
    const cancel = again.findAll('button').find((b) => b.text() === 'Cancel')
    await cancel!.trigger('click')
    expect(again.emitted('delete')).toBeUndefined()
    expect(again.find('[data-testid="bill-delete-b1"]').exists()).toBe(true)

    await again.get('button[aria-label="Edit Rent"]').trigger('click')
    expect(again.emitted('edit')?.[0][0]).toMatchObject({ id: 'b1' })
  })
})
