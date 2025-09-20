import { createApp } from 'vue'
import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { i18n, initializeLanguage } from './i18n'
import { useStravaApi } from './composables/useStravaApi'
import App from './App.vue'
import Editor from './components/Editor.vue'
import LandingPage from './components/LandingPage.vue'
import SegmentDetail from './components/SegmentDetail.vue'
import StravaCallback from './components/StravaCallback.vue'

const routes: RouteRecordRaw[] = [
  { path: '/', component: LandingPage },
  { 
    path: '/editor', 
    component: Editor,
    meta: { requiresAuth: true }
  },
  { path: '/segment/:id', component: SegmentDetail, props: true },
  { path: '/strava-callback', component: StravaCallback }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Authentication guard
router.beforeEach(async (to, from, next) => {
  // Check if route requires authentication
  if (to.meta.requiresAuth) {
    const { isAuthenticated, attemptTokenRefresh, getAuthUrl } = useStravaApi()
    
    if (!isAuthenticated()) {
      console.info('Editor route requires authentication, attempting token refresh...')
      
      // Try to refresh the token first
      const refreshSuccess = await attemptTokenRefresh()
      
      if (refreshSuccess && isAuthenticated()) {
        console.info('Token refresh successful, continuing to editor')
        next() // Continue with navigation
      } else {
        console.info('Token refresh failed, redirecting to Strava login')
        try {
          const authUrl = await getAuthUrl(to.fullPath)
          window.location.href = authUrl
          // Don't call next() as we're redirecting away from the app
        } catch (error) {
          console.error('Failed to get auth URL:', error)
          // If we can't get auth URL, redirect to home
          next('/')
        }
      }
    } else {
      // Already authenticated, continue with navigation
      next()
    }
  } else {
    // Route doesn't require authentication, continue with navigation
    next()
  }
})

// Initialize language before mounting
initializeLanguage()

const app = createApp(App)
app.use(router)
app.use(i18n)
app.mount('#app')
