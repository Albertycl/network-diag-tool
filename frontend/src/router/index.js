import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import IndexPage from '../pages/IndexPage.vue'
import AdminPage from '../pages/AdminPage.vue'
import HarListPage from '../pages/HarListPage.vue'
import HarDetailPage from '../pages/HarDetailPage.vue'

const routes = [
  {
    path: '/',
    component: MainLayout,
    children: [
      { path: '', redirect: '/admin' },
      { path: 'admin', component: AdminPage },
      { path: 'admin/hars', component: HarListPage },
      { path: 'admin/hars/:id', component: HarDetailPage },
      { path: ':session_uuid?', component: IndexPage }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
