// frontend/src/router/index.js
// Centralized application route definitions.

import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import Accounts from '@/views/Accounts.vue'
import Transactions from '@/views/Transactions.vue'
import Forecast from '@/views/Forecast.vue'
import Planning from '@/views/Planning.vue'
import Institutions from '@/views/Institutions.vue'
import Settings from '@/views/Settings.vue'
import ChartRoutePage from '@/views/ChartRoutePage.vue'
import AccountsTable from '@/components/tables/AccountsTable.vue'
import FinancialSummaryDetailed from '@/views/FinancialSummaryDetailed.vue'

const Investments = () => import('@/views/Investments.vue')
const RsaMonitor = () => import('@/views/RsaMonitor.vue')
const routes = [
  { path: '/', name: 'Dashboard', component: Dashboard },
  { path: '/accounts', name: 'Accounts', component: Accounts },
  { path: '/transactions', name: 'Transactions', component: Transactions },
  { path: '/forecast', name: 'Forecast', component: Forecast },
  { path: '/planning', name: 'Planning', component: Planning },
  { path: '/settings', name: 'Settings', component: Settings },
  // Direct chart URLs keep their paths/names; the page wrapper supplies dates and headings.
  {
    path: '/charts/cashflow',
    name: 'DailyNetChart',
    component: ChartRoutePage,
    props: { variant: 'cashflow' },
  },
  {
    path: '/charts/category',
    name: 'CategoryChart',
    component: ChartRoutePage,
    props: { variant: 'category' },
  },
  {
    path: '/charts/assets/year-comparison',
    name: 'NetYearComparisonChart',
    component: ChartRoutePage,
    props: { variant: 'year' },
  },
  { path: '/investments', name: 'Investments', component: Investments },
  { path: '/rsa-monitor', name: 'RsaMonitor', component: RsaMonitor },
  { path: '/institutions', name: 'Institutions', component: Institutions },
  { path: '/accounts/table', name: 'AccountsTable', component: AccountsTable },
  { path: '/summary', name: 'FinancialSummaryDetailed', component: FinancialSummaryDetailed },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
