<template>
    <div>
      <h2>Link Your Bank Account</h2>
      <button @click="linkPlaid">Link via Plaid</button>
      <button @click="linkTeller">Link via Teller</button>
    </div>
  </template>
  
  <script>
  import axios from 'axios';
  
  export default {
    name: 'LinkAccount',
    methods: {
      async linkPlaid() {
        try {
          // Call backend to create Plaid link token
          const res = await axios.post('/create_link_token', { products: ['transactions'] });
          const linkToken = res.data.link_token;
          // Initialize Plaid Link (assuming Plaid Link JS library is loaded)
          const handler = window.Plaid.create({
            token: linkToken,
            onSuccess: async (public_token, metadata) => {
              // Send the public token to backend for exchange
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
          // Call backend to generate Teller link token
          const res = await axios.post('/generate_link_token', {});
          const linkToken = res.data.link_token;
          // Initialize Teller Connect (assuming Teller Connect JS library is loaded)
          const tellerConnect = window.TellerConnect.create({
            token: linkToken,
            onSuccess: async (public_token, metadata) => {
              // Send the public token to backend for exchange with provider set to 'teller'
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
  