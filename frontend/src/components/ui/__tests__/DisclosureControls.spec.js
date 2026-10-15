// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { readFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import GroupedCategoryDropdown from '../GroupedCategoryDropdown.vue'
import FuzzyDropdown from '../FuzzyDropdown.vue'
import TogglePanel from '../TogglePanel.vue'

const here = path.dirname(fileURLToPath(import.meta.url))
const clickOutside = { beforeMount() {}, unmounted() {} }
const global = { directives: { 'click-outside': clickOutside } }

const groups = [
  {
    id: 'food',
    label: 'Food',
    children: [
      { id: 1, label: 'Groceries' },
      { id: 2, label: 'Dining' },
    ],
  },
  { id: 'home', label: 'Home', children: [{ id: 3, label: 'Rent' }] },
]

function mountGrouped(props = {}) {
  return mount(GroupedCategoryDropdown, {
    props: { groups, modelValue: [], ...props },
    global,
    attachTo: document.body,
  })
}

describe('GroupedCategoryDropdown', () => {
  it('uses a real button trigger with truthful aria state and a selected count', async () => {
    const wrapper = mountGrouped({ modelValue: [1, 3] })
    const trigger = wrapper.get('button.dropdown-trigger')
    expect(trigger.element.tagName).toBe('BUTTON')
    expect(trigger.attributes('type')).toBe('button')
    expect(trigger.attributes('aria-expanded')).toBe('false')
    expect(trigger.attributes('aria-haspopup')).toBe('true')
    expect(trigger.text()).toContain('2 selected')

    await trigger.trigger('click')
    expect(trigger.attributes('aria-expanded')).toBe('true')
    expect(trigger.attributes('aria-controls')).toBe(wrapper.get('.dropdown-menu').attributes('id'))
    wrapper.unmount()
  })

  it('closes on Escape and returns focus to the trigger', async () => {
    const wrapper = mountGrouped()
    const trigger = wrapper.get('button.dropdown-trigger')
    await trigger.trigger('click')
    wrapper.get('input[type="checkbox"]').element.focus()
    await wrapper.get('.dropdown-menu input[type="checkbox"]').trigger('keydown', { key: 'Escape' })
    expect(trigger.attributes('aria-expanded')).toBe('false')
    expect(document.activeElement).toBe(trigger.element)
    wrapper.unmount()
  })

  it('bounds the menu height and does not rely on an ancestor clipping it', () => {
    const source = readFileSync(path.resolve(here, '../GroupedCategoryDropdown.vue'), 'utf-8')
    expect(source).toContain('max-height: min(20rem, 50dvh)')
    expect(source).toContain('overflow-y: auto')
    const section = readFileSync(
      path.resolve(here, '../../dashboard/CategoryBreakdownSection.vue'),
      'utf-8',
    )
    expect(section).not.toMatch(/<BasePanel[^>]*overflow-hidden/)
    expect(section).toContain('breakdown-chart-clip')
  })

  it('expands groups independently of selection and exposes aria-expanded', async () => {
    const wrapper = mountGrouped()
    await wrapper.get('button.dropdown-trigger').trigger('click')
    const expand = wrapper.findAll('button.group-expand-btn')[0]
    expect(expand.attributes('aria-expanded')).toBe('false')
    expect(wrapper.text()).not.toContain('Groceries')

    await expand.trigger('click')
    expect(expand.attributes('aria-expanded')).toBe('true')
    expect(expand.attributes('aria-controls')).toBeTruthy()
    expect(wrapper.text()).toContain('Groceries')

    // Selecting the whole group neither collapses nor expands it.
    const groupBox = wrapper.findAll('.group-block')[1].get('input[type="checkbox"]')
    await groupBox.setValue(true)
    expect(wrapper.findAll('button.group-expand-btn')[1].attributes('aria-expanded')).toBe('false')
    expect(wrapper.emitted('update:modelValue').at(-1)[0]).toEqual(['3'])
    wrapper.unmount()
  })

  it('starts groups that already have selections expanded and keeps selection semantics', async () => {
    const wrapper = mountGrouped({ modelValue: [2] })
    await nextTick()
    await wrapper.get('button.dropdown-trigger').trigger('click')
    expect(wrapper.findAll('button.group-expand-btn')[0].attributes('aria-expanded')).toBe('true')
    const child = wrapper.findAll('.group-block')[0].findAll('input[type="checkbox"]')[1]
    expect(child.element.checked).toBe(false)
    await child.setValue(true)
    expect(wrapper.emitted('update:modelValue').at(-1)[0].sort()).toEqual(['1', '2'].sort())
    wrapper.unmount()
  })
})

describe('FuzzyDropdown', () => {
  const options = [
    { id: 'a', name: 'Alpha' },
    { id: 'b', name: 'Bravo' },
    { id: 'c', name: 'Charlie' },
  ]

  it('labels the search field and opens on focus without any blur timer', async () => {
    const wrapper = mount(FuzzyDropdown, {
      props: { options, label: 'Merchants', modelValue: [] },
      global,
      attachTo: document.body,
    })
    const input = wrapper.get('input[type="text"]')
    expect(input.attributes('aria-label')).toBe('Merchants')
    expect(input.attributes('aria-expanded')).toBe('false')
    await input.trigger('focus')
    expect(input.attributes('aria-expanded')).toBe('true')
    // Focus moving to a control inside the menu keeps it open.
    await input.trigger('focusout', { relatedTarget: wrapper.get('.dropdown-menu input').element })
    expect(input.attributes('aria-expanded')).toBe('true')
    // Focus leaving the component closes it immediately.
    await input.trigger('focusout', { relatedTarget: document.body })
    expect(input.attributes('aria-expanded')).toBe('false')
    wrapper.unmount()
  })

  it('closes on Escape and explains the maximum selection', async () => {
    const wrapper = mount(FuzzyDropdown, {
      props: { options, max: 1, modelValue: ['a'] },
      global,
      attachTo: document.body,
    })
    const input = wrapper.get('input[type="text"]')
    await input.trigger('focus')
    expect(wrapper.get('[data-testid="fuzzy-max-note"]').text()).toContain('Maximum of 1 selected')
    const boxes = wrapper.findAll('.dropdown-menu input[type="checkbox"]')
    expect(boxes[0].element.disabled).toBe(false)
    expect(boxes[1].element.disabled).toBe(true)
    await input.trigger('keydown', { key: 'Escape' })
    expect(input.attributes('aria-expanded')).toBe('false')
    wrapper.unmount()
  })

  it('uses themed muted text for the empty state and emits selections', async () => {
    const wrapper = mount(FuzzyDropdown, { props: { options, modelValue: [] }, global })
    await wrapper.get('input[type="text"]').setValue('zzzz')
    const empty = wrapper.get('p')
    expect(empty.text()).toBe('No matches')
    expect(empty.classes()).toContain('text-muted')
    expect(empty.classes()).not.toContain('text-gray-500')
    await wrapper.get('input[type="text"]').setValue('')
    await wrapper.get('.dropdown-menu input[type="checkbox"]').setValue(true)
    expect(wrapper.emitted('update:modelValue').at(-1)[0]).toEqual(['a'])
  })
})

describe('TogglePanel', () => {
  it('keeps v-model and exposes aria-expanded/controls on a non-submitting button', async () => {
    const wrapper = mount(TogglePanel, {
      props: { title: 'Advanced', modelValue: false },
      slots: { default: '<p>Body</p>' },
    })
    const button = wrapper.get('button')
    expect(button.attributes('type')).toBe('button')
    expect(button.attributes('aria-expanded')).toBe('false')
    expect(wrapper.find('.panel-content').exists()).toBe(false)

    await button.trigger('click')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([true])

    await wrapper.setProps({ modelValue: true })
    expect(button.attributes('aria-expanded')).toBe('true')
    expect(wrapper.get('.panel-content').attributes('id')).toBe(button.attributes('aria-controls'))
    expect(wrapper.text()).toContain('Body')
  })

  it('does not hardcode light-only grays or a .dark class', () => {
    const wrapper = mount(TogglePanel, { props: { title: 'x', modelValue: true } })
    expect(wrapper.html()).not.toMatch(/bg-gray|dark:/)
  })
})
