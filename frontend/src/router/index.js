import { createRouter, createWebHistory } from 'vue-router'
import { useSystemStore } from '../stores/system'
import PinEntry from '../views/PinEntry.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'PinEntry',
      component: PinEntry
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('../views/Dashboard.vue'),
      meta: { requiresPin: true }
    }
  ]
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const store = useSystemStore()
  if (to.meta.requiresPin && !store.pin) {
    next('/')
  } else {
    next()
  }
})

export default router
