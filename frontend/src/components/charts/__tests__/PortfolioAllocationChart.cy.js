import { defineComponent, ref } from 'vue'
import { Chart } from 'chart.js/auto'
import PortfolioAllocationChart from '../PortfolioAllocationChart.vue'

const TestWrapper = defineComponent({
  components: { PortfolioAllocationChart },
  setup() {
    const allocations = ref([
      { label: 'Stocks', value: 60 },
      { label: 'Bonds', value: 40 },
    ])
    return { allocations }
  },
  template: '<PortfolioAllocationChart :allocations="allocations" />',
})

describe('PortfolioAllocationChart', () => {
  it('enables legend and tooltip', () => {
    cy.mount(TestWrapper)
    cy.get('canvas').then(($c) => {
      const chart = Chart.getChart($c[0])
      expect(chart.options.plugins.legend.display).to.be.true
      expect(chart.options.plugins.tooltip.enabled).to.be.true
    })
  })
})
