/**
 * Basic Cypress test template.
 * This can be customized to create specific test cases.
 */

describe('{{TEST_NAME}}', () => {
  beforeEach(() => {
    // Visit the URL before each test
    cy.visit('{{TEST_URL}}')
    
    // Wait for the page to load
    cy.wait(2000)
  })

  it('should perform the test steps', () => {
    // Test code will be added here
    // {{TEST_STEPS}}
    
    // Example: Check if a specific element exists
    // cy.get('h1').should('be.visible')
    
    // Example: Fill a form
    // cy.get('#username').type('testuser')
    // cy.get('#password').type('password123')
    // cy.get('#submit-button').click()
    
    // Example: Verify redirection or content
    // cy.url().should('include', '/dashboard')
    // cy.get('.welcome-message').should('contain', 'Welcome')
  })
}) 