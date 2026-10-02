import { createRouter, createWebHashHistory } from 'vue-router'
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
      { path: 'admin', component: AdminPage },
      { path: 'admin/hars', component: HarListPage },
      { path: 'admin/hars/:id', component: HarDetailPage },
      { path: 'diagnosis/:session_uuid', component: IndexPage },
      { path: ':session_uuid?', component: IndexPage }
    ]
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
