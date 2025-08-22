<template>
  <!-- Navbar links are centered within a max-width container -->
  <nav class="menu z-50">
    <div class="container nav-inner">
      <router-link to="/" class="nav-link">Dashboard</router-link>
      <router-link to="/accounts" class="nav-link">Accounts</router-link>
      <router-link to="/transactions" class="nav-link">Transactions</router-link>
      <router-link to="/forecast" class="nav-link">Forecasting</router-link>
      <router-link to="/recurring-transactions" class="nav-link">Recurring Tx</router-link>
    </div>
  </nav>
</template>

<script>
export default {
  name: 'Navbar',
}
</script>

<style scoped>
@reference "../../assets/css/main.css";

.nav-link.router-link-exact-active {
  background-color: var(--hover-bg);
  color: var(--color-accent-yellow);
  font-weight: bold;
  box-shadow: 0 0 6px var(--hover-glow);
}

.menu {
  background-color: var(--background);
  border-bottom: 1px solid var(--divider);
  box-shadow: 0 2px 4px var(--shadow);
  position: sticky;
  top: 0;
  backdrop-filter: blur(6px);
}

.nav-inner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 0.5rem 0;
}

.nav-link {
  color: var(--color-text-light);
  font-size: 0.95rem;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  transition:
    color 0.3s ease,
    background-color 0.25s ease,
    box-shadow 0.25s ease;
  text-decoration: none;
  cursor: pointer;
}

.nav-link:hover {
  color: var(--link-hover-color);
  background-color: var(--hover-bg);
  box-shadow: 0 0 6px var(--hover-glow);
}
</style>
