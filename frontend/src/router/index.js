import { createRouter, createWebHistory } from 'vue-router';
import Dashboard from '../views/Dashboard.vue';
import Accounts from '../views/Accounts.vue';
import Transactions from '../views/Transactions.vue';
import Settings from '../views/Settings.vue';
import TellerDot from '../views/TellerDot.vue';
import Investments from '../views/Investments.vue';
import DailyNetChart from '@/components/DailyNetChart.vue';
import CategoryBreakdownChart from '@/components/CategoryBreakdownChart.vue';

const routes = [
  { path: '/', name: 'Dashboard', component: Dashboard },
  { path: '/accounts', name: 'Accounts', component: Accounts },
  { path: '/transactions', name: 'Transactions', component: Transactions },
  { path: '/charts/cashflow', name: 'DailyNetChart', component: DailyNetChart },
  { path: '/charts/category', name: 'CategoryChart', component: CategoryBreakdownChart },
  { path: '/settings', name: 'Settings', component: Settings },
  { path: '/teller-dot', name: 'TellerDot', component: TellerDot },
  { path: '/investments', name: 'Investments', component: Investments },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
