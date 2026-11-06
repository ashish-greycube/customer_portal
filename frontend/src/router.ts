import { createRouter, createWebHistory } from 'vue-router'
import { BASE, session } from './data'
import Login from './pages/Login.vue'
import NoAccess from './pages/NoAccess.vue'
import Dashboard from './pages/Dashboard.vue'
import DocListPage from './pages/DocListPage.vue'
import POSubmission from './pages/POSubmission.vue'
import Queries from './pages/Queries.vue'
import QueryDetail from './pages/QueryDetail.vue'
import Notifications from './pages/Notifications.vue'
import Account from './pages/Account.vue'
import PrintView from './pages/PrintView.vue'

const routes = [
  { path: '/login', component: Login, meta: { bare: true, guest: true } },
  { path: '/no-access', component: NoAccess, meta: { bare: true } },
  { path: '/', component: Dashboard },
  { path: '/opportunities', component: DocListPage, props: { doctype: 'opportunity' } },
  { path: '/quotations', component: DocListPage, props: { doctype: 'quotation' } },
  { path: '/po-submission', component: POSubmission },
  { path: '/sales-orders', component: DocListPage, props: { doctype: 'sales-order' } },
  { path: '/sales-invoices', component: DocListPage, props: { doctype: 'sales-invoice' } },
  { path: '/queries', component: Queries },
  { path: '/queries/:name', component: QueryDetail, props: true },
  { path: '/notifications', component: Notifications },
  { path: '/account', component: Account },
  { path: '/print/:doctype/:name', component: PrintView, props: true },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({ history: createWebHistory(BASE), routes })

router.beforeEach((to) => {
  if (!session.user) return to.meta.guest ? true : { path: '/login', query: to.fullPath !== '/' ? { redirect: to.fullPath } : {} }
  if (to.meta.guest) return '/'
  if (!session.customer && to.path !== '/no-access') return '/no-access'
  if (session.customer && to.path === '/no-access') return '/'
})

export default router
