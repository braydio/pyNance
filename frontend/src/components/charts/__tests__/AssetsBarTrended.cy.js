import { defineComponent } from 'vue'
import { Chart } from 'chart.js/auto'
import AssetsBarTrended from '../AssetsBarTrended.vue'

const TestWrapper = defineComponent({
  components: { AssetsBarTrended },
  template: '<AssetsBarTrended />',
})

describe('AssetsBarTrended', () => {
  it('enables legend and tooltip', () => {
    cy.intercept('GET', '/api/charts/net_assets', {
      statusCode: 200,
      body: {
        status: 'success',
        data: [{ date: '2024-01-01', assets: 100, liabilities: 50 }],
      },
    }).as('netAssets')

    cy.mount(TestWrapper)
    cy.wait('@netAssets')
    cy.get('canvas').then(($c) => {
      const chart = Chart.getChart($c[0])
      expect(chart.options.plugins.legend.display).to.be.true
      expect(chart.options.plugins.tooltip.enabled).to.be.true
    })
  })
})
