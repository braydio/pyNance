<template>
    <div>
      <!-- Notifications/Reminders Section -->
      <div class="notifications-container">
        <!-- Render an array of notifications -->
        <p 
          v-for="(notif, idx) in notifications" 
          :key="idx" 
          class="notification-message"
        >
          {{ notif }}
        </p>
      </div>
  
      <!-- Existing APR Section -->
      <div class="apr-section">
        <label>APR:</label>
        <input v-model="newApr" type="number" step="0.01" />
        <button @click="saveApr">Save APR</button>
      </div>
    </div>
  </template>
  
  <script>
  import axios from "axios";
  
  export default {
    props: ["accountId", "currentApr"],
    data() {
      return {
        notifications: [
          // This can come from an API or store instead of being hard-coded
          "Reminder: Credit card payment is due soon.",
          "FYI: You requested a statement from 2 months ago."
        ],
        newApr: this.currentApr || 0
      };
    },
    methods: {
      async saveApr() {
        try {
          const resp = await axios.put(`/api/accounts/${this.accountId}/apr`, {
            apr: this.newApr
          });
          console.log("APR updated:", resp.data);
        } catch (err) {
          console.error("Error updating APR:", err);
        }
      }
    }
  };
  </script>
  
  <style scoped>
  /* Basic styling for notifications */
  .notifications-container {
    background-color: #333; /* or your theme color */
    color: #fff;
    padding: 1rem;
    margin-bottom: 1rem;
    border-radius: 6px;
  }
  
  .notification-message {
    margin: 0.25rem 0;
  }
  </style>
<template>
    <div>
      <!-- Notifications/Reminders Section -->
      <div class="notifications-container">
        <!-- Render an array of notifications -->
        <p 
          v-for="(notif, idx) in notifications" 
          :key="idx" 
          class="notification-message"
        >
          {{ notif }}
        </p>
      </div>
  
      <!-- Existing APR Section -->
      <div class="apr-section">
        <label>APR:</label>
        <input v-model="newApr" type="number" step="0.01" />
        <button @click="saveApr">Save APR</button>
      </div>
    </div>
  </template>
  
  <script>
  import axios from "axios";
  
  export default {
    props: ["accountId", "currentApr"],
    data() {
      return {
        notifications: [
          // This can come from an API or store instead of being hard-coded
          "Reminder: Credit card payment is due soon.",
          "FYI: You requested a statement from 2 months ago."
        ],
        newApr: this.currentApr || 0
      };
    },
    methods: {
      async saveApr() {
        try {
          const resp = await axios.put(`/api/accounts/${this.accountId}/apr`, {
            apr: this.newApr
          });
          console.log("APR updated:", resp.data);
        } catch (err) {
          console.error("Error updating APR:", err);
        }
      }
    }
  };
  </script>
  
  <style scoped>
  /* Basic styling for notifications */
  .notifications-container {
    background-color: #333; /* or your theme color */
    color: #fff;
    padding: 1rem;
    margin-bottom: 1rem;
    border-radius: 6px;
  }
  
  .notification-message {
    margin: 0.25rem 0;
  }
  </style>
    