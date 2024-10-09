import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

import UploadReturnReceipt from '../views/UploadReturnReceipt.vue'
import UploadInvoice from '../views/UploadInvoice.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/step1',
      name: 'upload-return-receipt',
      component: UploadReturnReceipt
    },
    {
      path: '/step2',
      name: 'upload-invoice',
      component: UploadInvoice
    },
    {
      path: '/step3',
      name: 'compare-contents',
      component: HomeView
    },
    {
      path: '/about',
      name: 'about',
      // route level code-splitting
      // this generates a separate chunk (About.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import('../views/AboutView.vue')
    }
  ]
})

export default router
