import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Accounts from '../views/Accounts.vue'
import Transactions from '../views/Transactions.vue'
import RecurringTX from '../views/RecurringTX.vue'
import Forecast from '@/views/Forecast.vue';
import Investments from '../views/Investments.vue';
import Institutions from '../views/Institutions.vue';
import DailyNetChart from '@/components/charts/DailyNetChart.vue';
import CategoryBreakdownChart from '@/components/charts/CategoryBreakdownChart.vue';
import NetYearComparisonChart from '@/components/charts/NetYearComparisonChart.vue';
import AccountsTable from '@/components/tables/AccountsTable.vue';
import ForecastMock from '@/views/ForecastMock.vue';
import RecurringScanDemo from '@/views/RecurringScanDemo.vue';


const routes = [
  { path: '/', name: 'Dashboard', component: Dashboard },
  { path: '/accounts', name: 'Accounts', component: Accounts },
  { path: '/transactions', name: 'Transactions', component: Transactions },
  { path: '/forecast', name: 'Forecast', component: Forecast },
  { path: '/charts/cashflow', name: 'DailyNetChart', component: DailyNetChart },
  { path: '/charts/category', name: 'CategoryChart', component: CategoryBreakdownChart },
  {
    path: '/charts/assets/year-comporison',
    name: 'NetYearComparisonChart',
    component: NetYearComparisonChart,
  },
  { path: '/investments', name: 'Investments', component: Investments },
  { path: '/institutions', name: 'Institutions', component: Institutions },
  { path: '/accounts/table', name: 'AccountsTable', component: AccountsTable },
  { path: '/recurring-transactions', name: 'RecurringTx', component: RecurringTX },
  {
    path: '/recurring-scan-demo/:accountId?',
    name: 'RecurringScanDemo',
    component: RecurringScanDemo,
  },
  { path: '/forecast-mock', name: 'ForecastMock', component: ForecastMock },

]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
