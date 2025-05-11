
<template>
  <nav class="menu flex-center p-2 z-50">
    <router-link to="/" class="nav-link">Dashboard</router-link>
    <router-link to="/accounts" class="nav-link">Accounts</router-link>
    <router-link to="/transactions" class="nav-link">Transactions</router-link>
    <router-link to="/gallery" class="nav-link">Gallery</router-link>
    <router-link to="/forecast" class="nav-link">Forecasting</router-link>
    <router-link to="/recurring-transactions" class="nav-link">Recurring Tx</router-link>

    <!-- Dropdown Toggle -->
    <div class="relative">
      <button class="nav-link" :class="{ 'active-dropdown': showDropdown }" @click="toggleDropdown">
        Link / Refresh ▾
      </button>

      <transition name="fade-slide">
        <div v-if="showDropdown" class="dropdown-panel">
          <div class="dropdown-item"><LinkAccount @manual-token-click="$emit('manual-token-click')" /></div>
          <div class="dropdown-divider"></div>
          <div class="dropdown-item"><RefreshPlaidControls /></div>
          <div class="dropdown-divider"></div>
          <div class="dropdown-item"><RefreshTellerControls /></div>
        </div>
      </transition>
    </div>
  </nav>
</template>

<script>
import LinkAccount from '@/components/LinkAccount.vue';
import RefreshPlaidControls from '@/components/RefreshPlaidControls.vue';
import RefreshTellerControls from '@/components/RefreshTellerControls.vue';

export default {
  name: "Navbar",
  components: { LinkAccount, RefreshPlaidControls, RefreshTellerControls },
  data() {
    return {
      showDropdown: false,
    };
  },
  methods: {
    toggleDropdown() {
      this.showDropdown = !this.showDropdown;
    },
  },
};
</script>

<style scoped>
.nav-link.router-link-exact-active {
  background-color: var(--hover);
  color: var(--color-accent-yellow);
  font-weight: bold;
  box-shadow: 0 0 6px var(--hover-glow);
}

.menu {
  background-color: var(--background);
  border-bottom: 1px solid var(--divider);
  box-shadow: 0 2px 4px var(--shadow);
  gap: 1rem;
  position: sticky;
  top: 0;
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.nav-link {
  color: var(--color-text-light);
  font-size: 0.95rem;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  transition: color 0.3s ease, background-color 0.25s ease, box-shadow 0.25s ease;
  text-decoration: none;
  cursor: pointer;
}

.nav-link:hover {
  color: var(--link-hover-color);
  background-color: var(--hover);
  box-shadow: 0 0 6px var(--hover-glow);
}

.active-dropdown {
  background-color: var(--hover);
  color: var(--color-accent-yellow);
  box-shadow: 0 0 6px var(--hover-glow);
}

.relative {
  position: relative;
}

.dropdown-panel {
  position: absolute;
  top: 100%;
  left: 0;
  z-index: 100;
  background-color: var(--color-bg-secondary);
  border: 1px solid var(--color-border-secondary);
  border-radius: 10px;
  padding: 1rem;
  box-shadow: 0 2px 12px var(--shadow);
  min-width: 320px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.dropdown-item {
  width: 100%;
}

.dropdown-divider {
  height: 1px;
  width: 100%;
  background-color: var(--color-border-secondary);
  opacity: 0.5;
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.fade-slide-enter-to,
.fade-slide-leave-from {
  opacity: 1;
  transform: translateY(0);
}
</style>
