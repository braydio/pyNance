import { createRouter, createWebHistory } from 'vue-router';
import Dashboard from '../views/Dashboard.vue';
import Accounts from '../views/Accounts.vue';
import Transactions from '../views/Transactions.vue';
import Gallery from '@/views/Gallery.vue';
import Investments from '../views/Investments.vue';
import DailyNetChart from '../components/DailyNetChart.vue';
import CategoryBreakdownChart from '@/components/CategoryBreakdownChart.vue';
import NetYearComparisonChart from '../components/NetYearComparisonChart.vue';
import AccountsTable from '@/components/AccountsTable.vue';


const routes = [
  { path: '/', name: 'Dashboard', component: Dashboard },
  { path: '/accounts', name: 'Accounts', component: Accounts },
  { path: '/transactions', name: 'Transactions', component: Transactions },
  { path: '/charts/cashflow', name: 'DailyNetChart', component: DailyNetChart },
  { path: '/charts/category', name: 'CategoryChart', component: CategoryBreakdownChart },
  { path: '/charts/assets/year-comporison', name: 'NetYearComparisonChart', component: NetYearComparisonChart },
  { path: '/gallery', name: 'Gallery', component: Gallery },
  { path: '/investments', name: 'Investments', component: Investments },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
