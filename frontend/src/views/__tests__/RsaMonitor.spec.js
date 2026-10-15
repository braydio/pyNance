// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { readFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import RsaMonitor from '../RsaMonitor.vue'

const fetchRsaMonitorStatus = vi.hoisted(() => vi.fn())
vi.mock('@/services/api', () => ({ default: { fetchRsaMonitorStatus } }))

const here = path.dirname(fileURLToPath(import.meta.url))

const payload = {
  generated_at: '2026-10-14T12:00:00Z',
  overall_status: 'warning',
  heartbeat: { status: 'ok', age_seconds: 42 },
  orders: {
    queue: { count: 2 },
    sent: {
      count: 1,
      recent: [
        {
          sent_at: '2026-10-14T11:00:00Z',
          ticker: 'AAPL',
          action: 'buy',
          quantity: 3,
          broker: 'Fidelity',
        },
      ],
    },
  },
  account_history: {
    total_value: 12345,
    account_count: 2,
    brokers: [
      {
        name: 'A broker with an extremely long display name that must wrap rather than clip',
        value: 100,
        accounts: 1,
      },
    ],
  },
  components: [{ name: 'AutoRSA', root: '/opt/autorsa/some/very/long/path', status: 'ok' }],
  logs: [{ name: 'autorsa.log', status: 'error', recent_lines: ['line one', 'line two'] }],
}

const stubs = {
  BasePageLayout: { template: '<div><slot /></div>' },
  PageHeader: {
    template:
      '<header><slot name="title" /><slot name="subtitle" /><slot name="actions" /></header>',
  },
}

const mountPage = () => mount(RsaMonitor, { global: { stubs } })

describe('RsaMonitor.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useRealTimers()
    fetchRsaMonitorStatus.mockResolvedValue({ data: payload })
  })

  it('renders semantic status chips and a labelled last-checked line', async () => {
    const wrapper = mountPage()
    await flushPromises()
    const overall = wrapper.get('.metric-panel .status-pill')
    expect(overall.text()).toBe('warning')
    expect(overall.attributes('aria-label')).toBe('Overall status: warning')
    expect(overall.classes()).toContain('warning')
    expect(wrapper.text()).toContain('Last checked')
    expect(wrapper.findAll('.status-pill.ok')).not.toHaveLength(0)
    expect(wrapper.findAll('.status-pill.error')).not.toHaveLength(0)
  })

  it('contains the orders table in a focusable scroll region with right-aligned quantities', async () => {
    const wrapper = mountPage()
    await flushPromises()
    const region = wrapper.get('.table-wrap')
    expect(region.attributes('role')).toBe('region')
    expect(region.attributes('aria-label')).toBe('Sent orders')
    expect(region.attributes('tabindex')).toBe('0')
    expect(wrapper.findAll('th[scope="col"]')).toHaveLength(5)
    expect(wrapper.get('td.num').text()).toBe('3')
  })

  it('bounds each log in a labelled, focusable region and lets long broker names wrap', async () => {
    const wrapper = mountPage()
    await flushPromises()
    const log = wrapper.get('pre')
    expect(log.attributes('aria-label')).toBe('autorsa.log log, recent lines')
    expect(log.attributes('tabindex')).toBe('0')
    expect(log.text()).toContain('line two')
    const source = readFileSync(path.resolve(here, '../RsaMonitor.vue'), 'utf-8')
    expect(source).toContain('max-height: 22rem')
    expect(source).not.toMatch(/\.broker-row span \{[^}]*text-overflow: ellipsis/)
    expect(source).not.toMatch(/font-size: 0\.7[0-9]*rem/)
    expect(source).not.toMatch(/#86efac|#fde68a|#fecaca/)
  })

  it('shows a loading state, then an alert on failure while keeping the last good data', async () => {
    const wrapper = mountPage()
    await flushPromises()
    let reject
    fetchRsaMonitorStatus.mockReturnValueOnce(new Promise((_, r) => (reject = r)))
    await wrapper.get('[data-testid="rsa-refresh"]').trigger('click')
    expect(wrapper.get('[data-testid="rsa-refresh"]').attributes('aria-busy')).toBe('true')
    expect(wrapper.get('[data-testid="rsa-refresh"]').text()).toBe('Refreshing…')
    reject({ response: { data: { message: 'Monitor offline' } } })
    await flushPromises()
    const alert = wrapper.get('[data-testid="rsa-error"]')
    expect(alert.attributes('role')).toBe('alert')
    expect(alert.text()).toContain('Monitor offline')
    expect(alert.text()).toContain('last successful check')
    expect(wrapper.text()).toContain('AutoRSA')
  })

  it('explains the empty state when nothing has loaded', async () => {
    fetchRsaMonitorStatus.mockRejectedValueOnce(new Error('down'))
    const wrapper = mountPage()
    await flushPromises()
    expect(wrapper.get('[data-testid="rsa-error"]').text()).toContain(
      'Unable to load RSA monitor status',
    )
    expect(wrapper.find('.summary-grid').exists()).toBe(false)
    expect(wrapper.text()).toContain('Waiting for runtime data')
  })
})
