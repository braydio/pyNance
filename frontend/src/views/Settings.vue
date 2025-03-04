<template>
    <div>
      <h1>Settings</h1>
      <label for="themes">Select Theme:</label>
      <select v-model="selectedTheme" @change="setTheme">
        <option v-for="theme in themes" :key="theme" :value="theme">
          {{ theme }}
        </option>
      </select>
    </div>
  </template>
  
  <script>
  import axios from "axios";
  
  export default {
    name: "Settings",
    data() {
      return {
        themes: [],
        selectedTheme: "",
      };
    },
    async created() {
      await this.fetchThemes();
    },
    methods: {
      async fetchThemes() {
        try {
          const response = await axios.get("/themes");
          this.themes = response.data.themes;
          this.selectedTheme = response.data.current_theme;
        } catch (error) {
          console.error("Failed to fetch themes:", error);
        }
      },
      async setTheme() {
        try {
          await axios.post("/set_theme", { theme: this.selectedTheme });
          alert(`Theme set to ${this.selectedTheme}`);
        } catch (error) {
          console.error("Failed to set theme:", error);
        }
      },
    },
  };
  </script>
  