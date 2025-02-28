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
        // Request a link token for Plaid from the backend
        const res = await axios.post('/create_link_token', { products: ['transactions'] });
        const linkToken = res.data.link_token;

        // Ensure that the Plaid library is loaded
        if (!window.Plaid) {
          console.error("Plaid library is not loaded. Please include the Plaid Link script.");
          return;
        }

        // Initialize Plaid Link using the received link token
        const handler = window.Plaid.create({
          token: linkToken,
          onSuccess: async (public_token, metadata) => {
            // Exchange the public token for an access token on your backend
            const exchangeRes = await axios.post('/exchange_public_token', { public_token, provider: 'plaid' });
            console.log('Plaid account linked', exchangeRes.data);
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
        // Request a link token for Teller from the backend
        const res = await axios.post('/generate_link_token', {});
        const linkToken = res.data.link_token;

        // Ensure that the Teller Connect library is loaded
        if (!window.TellerConnect) {
          console.error("TellerConnect library is not loaded. Please include the Teller Connect script.");
          return;
        }

        // Initialize Teller Connect using the received link token
        const tellerConnect = window.TellerConnect.setup({
          token: linkToken,
          onSuccess: async (public_token, metadata) => {
            // Exchange the public token for an access token on your backend
            const exchangeRes = await axios.post('/exchange_public_token', { public_token, provider: 'teller' });
            console.log('Teller account linked', exchangeRes.data);
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
/* =============================================================================
   Gruvbox Hyprland Inspired Styling for LinkAccount Component
   ============================================================================= */

/* Container styling */
.link-account {
  background-color: var(--gruvbox-bg);
  color: var(--gruvbox-fg);
  padding: 1.5rem;
  border-radius: 6px;
  margin: 1rem 0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.5);
  text-align: center;
}

/* Header styling */
.link-account h2 {
  margin: 0 0 1rem;
  color: var(--gruvbox-yl);
}

/* Button group set to horizontal layout */
.button-group {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

/* Button styling */
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

/* Hover state for buttons */
.button-group button:hover {
  background-color: var(--gruvbox-hover);
  transform: translateY(-2px);
}
</style>
