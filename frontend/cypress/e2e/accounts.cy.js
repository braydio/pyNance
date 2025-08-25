// accounts.cy.js
// Cypress E2E test to verify accounts control bar alignment with table header

describe('Accounts control bar', () => {
  it('aligns with the table header', () => {
    cy.visit('/accounts/table');
    cy.get('[data-testid="accounts-control-bar"]').then($bar => {
      const barRight = $bar[0].getBoundingClientRect().right;
      cy.get('table thead').then($head => {
        const headRight = $head[0].getBoundingClientRect().right;
        expect(Math.abs(barRight - headRight)).to.be.lessThan(2);
      });
    });
  });
});
