import { defineComponent, ref, toRef } from 'vue'
import { useAccountHistory } from '../useAccountHistory'
import { rangeToDates } from '@/api/accounts'

const TestComponent = defineComponent({
  props: { id: String, range: String },
  template:
    '<ul><li v-for="pt in balances" :key="pt.date">{{ pt.date }}={{ pt.balance }}</li></ul>',
  setup(props) {
    const { history, balances } = useAccountHistory(toRef(props, 'id'), toRef(props, 'range'))
    return { history, balances }
  },
})

describe('useAccountHistory', () => {
  it('loads and normalizes account history from API', () => {
    cy.intercept('GET', '/api/accounts/123/history*', {
      statusCode: 200,
      body: {
        status: 'success',
        data: {
          balances: [
            { date: '2024-01-03', balance: '110.25' },
            { date: '2024-01-01', amount: '100.00' },
          ],
        },
      },
    }).as('getHistory')

    cy.mount(TestComponent, { props: { id: '123', range: '30d' } })
    cy.wait('@getHistory')
    cy.get('li').should('have.length', 2)
    cy.get('li').first().should('contain', '2024-01-01=100')
    cy.get('li').last().should('contain', '2024-01-03=110.25')
  })

  it('memoizes history per account and range window', () => {
    cy.intercept('GET', '/api/accounts/123/history*', {
      statusCode: 200,
      body: { balances: [] },
    }).as('getHistory')

    cy.mount(TestComponent, { props: { id: '123', range: '30d' } })
    cy.wait('@getHistory')

    cy.mount(TestComponent, { props: { id: '123', range: '30d' } })
    cy.wait(100)
    cy.get('@getHistory.all').should('have.length', 1)
  })

  it('fetches new data when range changes', () => {
    const RangeComponent = defineComponent({
      props: { id: String },
      template:
        '<div><button id="change" @click="range=\'60d\'"></button><ul><li v-for="pt in history" :key="pt.date">{{ pt.balance }}</li></ul></div>',
      setup(props) {
        const range = ref('30d')
        const { history } = useAccountHistory(toRef(props, 'id'), range)
        return { history, range }
      },
    })

    cy.intercept('GET', '/api/accounts/123/history*', {
      statusCode: 200,
      body: { balances: [] },
    }).as('getHistory')

    cy.mount(RangeComponent, { props: { id: '123' } })
    cy.wait('@getHistory')
      .its('request.url')
      .then((url) => {
        const params = new URL(url).searchParams
        const { start, end } = rangeToDates('30d')
        expect(params.get('start_date')).to.eq(start)
        expect(params.get('end_date')).to.eq(end)
      })
    cy.get('#change').click()
    cy.wait('@getHistory')
      .its('request.url')
      .then((url) => {
        const params = new URL(url).searchParams
        const { start, end } = rangeToDates('60d')
        expect(params.get('start_date')).to.eq(start)
        expect(params.get('end_date')).to.eq(end)
      })
    cy.get('@getHistory.all').should('have.length', 2)
  })
})
