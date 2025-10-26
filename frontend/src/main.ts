import { createApp, watch } from 'vue'
import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { i18n, initializeLanguage } from './i18n'
import { useStravaApi } from './composables/useStravaApi'
import App from './App.vue'
import Landing from './components/Landing.vue'
import Editor from './components/Editor.vue'
import Explorer from './components/Explorer.vue'
import SegmentDetail from './components/SegmentDetail.vue'
import StravaCallback from './components/StravaCallback.vue'
import WahooCallback from './components/WahooCallback.vue'
import RoutePlanner from './components/RoutePlanner.vue'

const routes: RouteRecordRaw[] = [
  { path: '/', component: Landing },
  { path: '/explorer', component: Explorer },
  {
    path: '/editor',
    component: Editor,
    meta: { requiresAuth: true, requiresEditor: true }
  },
  {
    path: '/route-planner',
    component: RoutePlanner
    // No authentication required - route planner works standalone
  },
  { path: '/segment/:id', component: SegmentDetail, props: true },
  { path: '/strava-callback', component: StravaCallback },
  { path: '/wahoo-callback', component: WahooCallback }
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
      console.info('Route requires authentication, attempting token refresh...')

      // Try to refresh the token first
      const refreshSuccess = await attemptTokenRefresh()

      if (refreshSuccess && isAuthenticated()) {
        console.info('Token refresh successful, continuing to route')
        next() // Continue with navigation
      } else {
        console.info('Token refresh failed, redirecting to Strava login')
        try {
          // Store the current path for redirect after auth
          sessionStorage.setItem('strava_redirect_after_auth', to.fullPath)
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
      // Check if route requires authorization (for protected features)
      if (to.meta.requiresEditor) {
        const { useAuthorization } = await import('./composables/useAuthorization')
        const { isAuthorized, isLoadingAuthorization, checkAuthorizationStatus } =
          useAuthorization()

        // If authorization is still loading, wait for it to complete
        if (isLoadingAuthorization.value) {
          // Wait for authorization to complete
          await new Promise((resolve) => {
            const unwatch = watch(
              [isAuthorized, isLoadingAuthorization],
              ([, loading]) => {
                if (!loading) {
                  unwatch()
                  resolve(void 0)
                }
              }
            )
          })
        } else if (!isAuthorized.value) {
          // If not loading and not authorized, try to check authorization status
          await checkAuthorizationStatus()
        }

        if (!isAuthorized.value) {
          next('/')
          return
        }
      }

      // Already authenticated and authorized, continue with navigation
      next()
    }
  } else {
    // Route doesn't require authentication, continue with navigation
    next()
  }
})

// Initialize language before mounting
initializeLanguage()

// Initialize theme before mounting
import { useThemeSettings } from './composables/useThemeSettings'
const { initializeTheme, watchSystemTheme } = useThemeSettings()
initializeTheme()
watchSystemTheme()

const app = createApp(App)
app.use(router)
app.use(i18n)
app.mount('#app')
