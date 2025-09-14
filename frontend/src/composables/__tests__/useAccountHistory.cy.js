import { defineComponent, ref, toRef } from 'vue'
import { useAccountHistory } from '../useAccountHistory'
import { rangeToDates } from '@/api/accounts'

const TestComponent = defineComponent({
  props: { id: String, range: String },
  template: '<ul><li v-for="pt in history" :key="pt.date">{{ pt.balance }}</li></ul>',
  setup(props) {
    const { history } = useAccountHistory(toRef(props, 'id'), toRef(props, 'range'))
    return { history }
  },
})

describe('useAccountHistory', () => {
  it('loads account history from API', () => {
    // Intercept account history API call (prefix includes /api)
    cy.intercept('GET', '/api/accounts/123/history*', {
      statusCode: 200,
      body: {
        status: 'success',
        history: [
          { date: '2024-01-01', balance: 100 },
          { date: '2024-01-02', balance: 110 },
        ],
      },
    }).as('getHistory')

    cy.mount(TestComponent, { props: { id: '123', range: '30d' } })
    cy.wait('@getHistory')
    cy.get('li').should('have.length', 2).last().should('contain', '110')
  })

  it('memoizes history per account and range', () => {
    cy.intercept('GET', '/api/accounts/123/history*', {
      statusCode: 200,
      body: { history: [] },
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
      template: `<div><button id="change" @click="range='60d'"></button><ul><li v-for="pt in history" :key="pt.date">{{ pt.balance }}</li></ul></div>`,
      setup(props) {
        const range = ref('30d')
        const { history } = useAccountHistory(toRef(props, 'id'), range)
        return { history, range }
      },
    })

    cy.intercept('GET', '/api/accounts/123/history*', {
      statusCode: 200,
      body: { history: [] },
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
  })
})
