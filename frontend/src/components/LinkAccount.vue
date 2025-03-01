<template>
  <div class="link-account">
    <h2>Link Your Bank Account</h2>
    <div class="button-group">
      <button @click="linkPlaid">Plaid Link</button>
      <button @click="linkTeller">Teller.io</button>
    </div>
  </div>
</template>


<script>
import axios from 'axios';

export default {
  name: 'LinkAccount',
  methods: {
    async linkPlaid() {
      try {
        // Request a link token for Plaid from the backend.
        // Adjust the endpoint URL as needed.
        const res = await axios.post('/api/plaid/transactions/generate_link_token', { 
          user_id: 'BraydensFinanceDashroad',
          products: ['transactions']
        });
        const linkToken = res.data.link_token;
        if (!linkToken) {
          console.error("No Plaid link token received");
          return;
        }
        // Ensure the Plaid library is loaded.
        if (!window.Plaid) {
          console.error("Plaid library is not loaded. Please include the Plaid Link script.");
          return;
        }
        // Initialize Plaid Link using the received token.
        const handler = window.Plaid.create({
          token: linkToken,
          onSuccess: async (public_token, metadata) => {
            // Exchange the public token for an access token via your backend.
            const exchangeRes = await axios.post('/api/plaid/transactions/exchange_public_token', {
              public_token,
              provider: 'plaid'
            });
            console.log('Plaid account linked', exchangeRes.data);
            // Optionally, emit an event or update a parent component to refresh the accounts.
          },
          onExit: (err, metadata) => {
            console.log('Plaid Link exited', err, metadata);
          }
        });
        handler.open();
      } catch (err) {
        console.error('Error linking via Plaid', err);
      }
    },
    async linkTeller() {
      try {
        // Request a link token for Teller from the backend.
        // Adjust the endpoint URL as needed.
        const res = await axios.post('/api/teller/transactions/generate_link_token', { 
          user_id: 'user_12345',
          products: ['transactions', 'balance']
        });
        const linkToken = res.data.link_token;
        if (!linkToken) {
          console.error("No Teller link token received");
          return;
        }
        // Ensure the TellerConnect library is loaded.
        if (!window.TellerConnect) {
          console.error("TellerConnect library is not loaded. Please include the Teller Connect script.");
          return;
        }
        // Initialize Teller Connect using the received token.
        const tellerConnect = window.TellerConnect.setup({
          token: linkToken,
          onSuccess: async (public_token, metadata) => {
            // Exchange the public token for an access token on your backend.
            const exchangeRes = await axios.post('/api/teller/transactions/exchange_public_token', {
              public_token,
              provider: 'teller'
            });
            console.log('Teller account linked', exchangeRes.data);
            // Optionally, trigger a refresh of the linked accounts.
          },
          onExit: (err, metadata) => {
            console.log('Teller Link exited', err, metadata);
          }
        });
        tellerConnect.open();
      } catch (err) {
        console.error('Error linking via Teller', err);
      }
    }
  }
};
</script>

<style scoped>
/* Gruvbox Hyprland Inspired Styling for LinkAccount Component */
.link-account {
  background-color: var(--gruvbox-bg);
  color: var(--gruvbox-fg);
  padding: 1.5rem;
  border-radius: 6px;
  margin: 1rem 0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.5);
  text-align: center;
}
.link-account h2 {
  margin: 0 0 1rem;
  color: var(--gruvbox-yl);
}
.button-group {
  display: flex;
  gap: 1rem;
  justify-content: center;
}
.button-group button {
  background-color: var(--gruvbox-accent);
  color: var(--gruvbox-fg);
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 3px;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.2s ease;
}
.button-group button:hover {
  background-color: var(--gruvbox-hover);
  transform: translateY(-2px);
}
</style>
