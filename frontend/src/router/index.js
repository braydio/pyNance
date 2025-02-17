// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';
import Dashboard from '../views/Dashboard.vue';
import Accounts from '../views/Accounts.vue';
import AccountsTable from '../components/AccountsTable.vue';
import Transactions from '../views/Transactions.vue';
import Settings from '../views/Settings.vue';
import TellerDot from '../views/TellerDot.vue';
import Investments from '../views/Investments.vue';

const routes = [
  { path: '/', name: 'Dashboard', component: Dashboard },
  { path: '/accounts', name: 'Accounts', component: Accounts },
  { path: "/accounts", name: "Accounts", component: AccountsTable },
  { path: '/transactions', name: 'Transactions', component: Transactions },
  { path: '/settings', name: 'Settings', component: Settings },
  { path: '/teller-dot', name: 'TellerDot', component: TellerDot },
  { path: '/investments', name: 'Investments', component: Investments },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
