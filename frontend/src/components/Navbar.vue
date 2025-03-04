<template>
  <nav class="menu">
    <router-link to="/">Dashboard</router-link>
    <router-link to="/accounts">Accounts</router-link>
    <router-link to="/transactions">Transactions</router-link>
    <router-link to="/gallery">Gallery</router-link>
  </nav>
</template>

<script>
export default {
  name: "Navbar",
};
</script>

<style scoped>
.menu {
  background: var(--header-bg);
  padding: 15px;
  display: flex;
  justify-content: center;
  gap: 20px;
}
.menu a {
  color: var(--text-color);
  text-decoration: none;
  font-size: 1rem;
  transition: color 0.3s;
}
.menu a:hover {
  color: var(--accent-color);
}
</style>
