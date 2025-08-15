import { defineComponent, toRef } from 'vue'
import { useAccountHistory } from '../useAccountHistory'

const TestComponent = defineComponent({
  props: { id: String },
  template: '<ul><li v-for="pt in history" :key="pt.date">{{ pt.balance }}</li></ul>',
  setup(props) {
    const { history } = useAccountHistory(toRef(props, 'id'))
    return { history }
  }
})

describe('useAccountHistory', () => {
  it('loads account history from API', () => {
    cy.intercept('GET', '/accounts/123/history*', {
      statusCode: 200,
      body: {
        status: 'success',
        history: [
          { date: '2024-01-01', balance: 100 },
          { date: '2024-01-02', balance: 110 }
        ]
      }
    }).as('getHistory')

    cy.mount(TestComponent, { props: { id: '123' } })
    cy.wait('@getHistory')
    cy.get('li').should('have.length', 2).last().should('contain', '110')
  })
})
