// transactions-scroll-nav.cy.js - TP-20261020-002 real-browser scroll and navbar QA.
//
// Wheel input is dispatched through the Chrome DevTools protocol (Input.dispatchMouseEvent), so the
// browser's own scroll chaining decides the outcome rather than a synthetic DOM event.
// Run: npm run build && npx vite preview --port 4173 & npx cypress run --e2e --spec cypress/e2e/transactions-scroll-nav.cy.js

const makeRows = (count) =>
  Array.from({ length: count }, (_, i) => ({
    transaction_id: `tx-${i}`,
    date: '2026-10-01',
    amount: -12.34 - i,
    description: `Transaction ${i}`,
    category: 'General',
    merchant_name: 'Merchant',
    account_name: 'Checking',
    institution_name: 'Bank',
    subtype: 'checking',
  }))

const stubTransactions = (count) => {
  cy.intercept('GET', '/api/transactions/get_transactions*', {
    status: 'success',
    data: { transactions: makeRows(count), total: count },
  }).as('getTx')
}

const wheel = (x, y, deltaY, deltaX = 0) =>
  Cypress.automation('remote:debugger:protocol', {
    command: 'Input.dispatchMouseEvent',
    params: { type: 'mouseWheel', x, y, deltaX, deltaY },
  })

// The app runs in Cypress's scaled iframe; wheel input is dispatched in top-level page coordinates.
const centerOf = (selector) =>
  cy.get(selector).then(($el) => {
    const r = $el[0].getBoundingClientRect()
    const appWin = $el[0].ownerDocument.defaultView
    const frame = window.top.document.querySelector('iframe.aut-iframe')
    const f = frame.getBoundingClientRect()
    const scale = f.width / appWin.innerWidth
    const px = r.left + r.width / 2
    const py = Math.min(r.top + 80, appWin.innerHeight - 20)
    return { x: Math.round(f.left + px * scale), y: Math.round(f.top + py * scale) }
  })

describe('Transactions scrolling and navigation', () => {
  beforeEach(() => {
    cy.viewport(1280, 700)
  })

  it('short paginated table: wheel over the grid scrolls the document', () => {
    stubTransactions(10)
    cy.visit('/transactions')
    cy.wait('@getTx')
    cy.get('[aria-label="Transactions table"]').should('be.visible')
    cy.window().its('scrollY').should('eq', 0)
    cy.document().then((doc) => {
      expect(doc.documentElement.scrollHeight, 'page taller than viewport').to.be.greaterThan(700)
    })
    centerOf('[aria-label="Transactions table"]').then(({ x, y }) => {
      cy.wrap(wheel(x, y, 300))
    })
    cy.window().its('scrollY').should('be.greaterThan', 0)
  })

  it('virtualized table: scrolls internally, then chains to the page at the end', () => {
    stubTransactions(120)
    cy.visit('/transactions')
    cy.wait('@getTx')
    cy.get('.table-scroll--virtual')
      .should('exist')
      .scrollIntoView({ offset: { top: -80, left: 0 } })
    cy.window().then((win) => {
      cy.wrap(win.scrollY).as('pageY')
    })
    centerOf('.table-scroll--virtual').then(({ x, y }) => {
      cy.wrap(wheel(x, y, 200))
    })
    cy.get('.table-scroll--virtual').its('0.scrollTop').should('be.greaterThan', 0)
    cy.get('@pageY').then((pageY) => {
      cy.window().its('scrollY').should('eq', pageY)
    })
    // Exhaust the inner scroller, then keep wheeling: the page must take over.
    cy.get('.table-scroll--virtual').then(($el) => {
      $el[0].scrollTop = $el[0].scrollHeight
    })
    centerOf('.table-scroll--virtual').then(({ x, y }) => {
      cy.wrap(wheel(x, y, 400))
    })
    cy.get('@pageY').then((pageY) => {
      cy.window().its('scrollY').should('be.greaterThan', pageY)
    })
  })
  ;[320, 390, 640, 768, 950, 1100, 1280].forEach((width) => {
    it(`navbar stays on one row at ${width}px with the active route reachable`, () => {
      stubTransactions(10)
      cy.viewport(width, 700)
      cy.visit('/transactions')
      cy.get('[data-testid="nav-links"]').then(($links) => {
        const top = $links.find('a')[0].getBoundingClientRect().top
        $links.find('a').each((_, a) => {
          expect(Math.abs(a.getBoundingClientRect().top - top)).to.be.lessThan(4)
        })
        const active = $links.find('.router-link-exact-active')[0]
        const box = active.getBoundingClientRect()
        const host = $links[0].getBoundingClientRect()
        expect(box.left).to.be.at.least(host.left - 1)
        expect(box.right).to.be.at.most(host.right + 1)
      })
      cy.document().then((doc) => {
        expect(doc.documentElement.scrollWidth).to.be.at.most(width)
      })
      cy.screenshot(`transactions-nav-${width}`, { capture: 'viewport' })
    })
  })
})
