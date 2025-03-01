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
import api from "@/services/api";

export default {
  name: "LinkAccount",
  data() {
    return {
      scriptsLoaded: false,
      plaidLinkToken: null,
      tellerConnectInstance: null,
      // The user ID should be dynamically determined; here it's hard-coded for demonstration.
      userId: "user_12345",
      // Teller Application ID from your Teller dashboard; set in your .env as VITE_TELLER_APP_ID.
      tellerAppId: import.meta.env.VITE_TELLER_APP_ID || "app_xxxxxx",
    };
  },
  methods: {
    // Dynamically load an external script.
    loadScript(src) {
      return new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = src;
        // Teller recommends not using async or defer so that the script executes immediately.
        script.async = false;
        script.onload = () => resolve();
        script.onerror = () =>
          reject(new Error(`Failed to load script: ${src}`));
        document.body.appendChild(script);
      });
    },
    // Load external libraries for Plaid and Teller Connect.
    async loadExternalScripts() {
      try {
        await this.loadScript("https://cdn.plaid.com/link/v2/stable/link-initialize.js");
        await this.loadScript("https://cdn.teller.io/connect/connect.js");
        this.scriptsLoaded = true;
        console.log("External scripts loaded");
        // Preload Plaid link token once scripts are loaded.
        await this.preloadPlaidLinkToken();
      } catch (error) {
        console.error("Error loading external scripts:", error);
      }
    },
    // Preload the Plaid link token from your backend.
    async preloadPlaidLinkToken() {
      try {
        const plaidRes = await api.generateLinkToken("plaid", {
          user_id: this.userId,
          products: ["transactions"],
        });
        this.plaidLinkToken = plaidRes.link_token;
      } catch (err) {
        console.error("Error generating Plaid link token:", err);
      }
    },
    async linkPlaid() {
      if (!this.scriptsLoaded) {
        console.error("External scripts not loaded yet.");
        return;
      }
      if (!this.plaidLinkToken) {
        console.error("Plaid link token not available.");
        return;
      }
      if (!window.Plaid) {
        console.error("Plaid library not available. Please check the script inclusion.");
        return;
      }
      // Initialize Plaid Link using the preloaded token.
      const handler = window.Plaid.create({
        token: this.plaidLinkToken,
        onSuccess: async (public_token, metadata) => {
          console.log("Plaid onSuccess, public_token:", public_token);
          // Exchange the public token for an access token via your backend.
          const exchangeRes = await api.exchangePublicToken("plaid", public_token);
          console.log("Plaid exchange response:", exchangeRes);
          // Optionally, trigger a refresh of your account list.
        },
        onExit: (err, metadata) => {
          console.log("Plaid Link exited", err, metadata);
        },
      });
      handler.open();
    },
    async linkTeller() {
      if (!this.scriptsLoaded) {
        console.error("External scripts not loaded yet.");
        return;
      }
      if (!window.TellerConnect) {
        console.error("TellerConnect library not available. Please check the script inclusion.");
        return;
      }
      // Initialize Teller Connect according to Teller's recommended integration.
      if (!this.tellerConnectInstance) {
        this.tellerConnectInstance = window.TellerConnect.setup({
          applicationId: this.tellerAppId,
          products: ["transactions", "balance"],
          onInit: function() {
            console.log("Teller Connect has initialized");
          },
          onSuccess: async function(enrollment) {
            console.log("User enrolled successfully", enrollment.accessToken);
            // The enrollment object contains the accessToken.
            // Optionally, you can send this accessToken to your backend for processing.
            const exchangeRes = await api.exchangePublicToken("teller", enrollment.accessToken);
            console.log("Teller exchange response:", exchangeRes);
          },
          onExit: function() {
            console.log("User closed Teller Connect");
          }
        });
      }
      this.tellerConnectInstance.open();
    },
  },
  mounted() {
    this.loadExternalScripts();
  }
};
</script>

<style scoped>
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
