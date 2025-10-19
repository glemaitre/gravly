/**
 * Simplified Wahoo API composable that uses backend endpoints
 * Replaces the complex TypeScript Wahoo API with simple fetch calls
 */

import { ref } from 'vue'

export interface WahooActivity {
  id: string
  name: string
  distance: number
  duration: number
  elevation_gain: number
  type: string
  start_time: string
  end_time: string
  average_speed: number
  max_speed: number
  average_heart_rate: number | null
  max_heart_rate: number | null
  calories: number | null
  route_id: string | null
}

export interface WahooAuthState {
  isAuthenticated: boolean
  accessToken: string | null
  expiresAt: number | null
  user: any | null
}

export function useWahooApi() {
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const authState = ref<WahooAuthState>({
    isAuthenticated: false,
    accessToken: null,
    expiresAt: null,
    user: null
  })

  /**
   * Get Wahoo OAuth authorization URL
   */
  async function getAuthUrl(state: string = 'wahoo_auth'): Promise<string> {
    try {
      isLoading.value = true
      error.value = null

      const url = new URL('/api/wahoo/auth-url', window.location.origin)
      url.searchParams.set('state', state)

      const response = await fetch(url.toString())

      if (!response.ok) {
        await response.text()
        throw new Error(`Failed to get auth URL: ${response.statusText}`)
      }

      const data = await response.json()
      return data.auth_url
    } catch (err: any) {
      error.value = err.message || 'Failed to get authorization URL'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Exchange authorization code for access token
   */
  async function exchangeCode(code: string): Promise<void> {
    try {
      isLoading.value = true
      error.value = null

      const formData = new FormData()
      formData.append('code', code)

      const response = await fetch('/api/wahoo/exchange-code', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        await response.text()
        throw new Error(`Failed to exchange code: ${response.statusText}`)
      }

      const data = await response.json()

      // Store auth state
      authState.value = {
        isAuthenticated: true,
        accessToken: data.access_token,
        expiresAt: data.expires_at,
        user: data.user || null
      }

      // Store in localStorage for persistence
      localStorage.setItem('wahoo_auth', JSON.stringify(authState.value))
    } catch (err: any) {
      error.value = err.message || 'Failed to exchange authorization code'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Load auth state from localStorage
   */
  function loadAuthState(): void {
    try {
      const stored = localStorage.getItem('wahoo_auth')
      if (stored) {
        const parsed = JSON.parse(stored)

        // Check if token is expired
        if (parsed.expiresAt && Date.now() > parsed.expiresAt * 1000) {
          console.log('Wahoo token expired, clearing auth state')
          localStorage.removeItem('wahoo_auth')
          return
        }

        authState.value = parsed
        console.log('Loaded Wahoo auth state from localStorage')
      }
    } catch (err) {
      console.error('Failed to load Wahoo auth state:', err)
      localStorage.removeItem('wahoo_auth')
    }
  }

  /**
   * Clear authentication state
   */
  function clearAuth(): void {
    authState.value = {
      isAuthenticated: false,
      accessToken: null,
      expiresAt: null,
      user: null
    }
    localStorage.removeItem('wahoo_auth')
  }

  /**
   * Attempt to refresh token only (no redirect)
   */
  async function attemptTokenRefresh(): Promise<boolean> {
    console.info('Attempting Wahoo token refresh...')

    try {
      const response = await fetch('/api/wahoo/refresh-token', {
        method: 'POST'
      })

      if (response.ok) {
        console.info('Wahoo token refreshed successfully')
        // Reload auth state from localStorage (backend updated it)
        loadAuthState()
        return true
      }
    } catch (error) {
      console.warn('Wahoo token refresh failed:', error)
    }

    return false
  }

  /**
   * Attempt to refresh token and redirect to login if failed
   */
  async function handleAuthenticationError(): Promise<void> {
    console.info('Wahoo authentication error detected, attempting token refresh...')

    const refreshSuccess = await attemptTokenRefresh()

    if (!refreshSuccess) {
      // If refresh failed, clear auth and redirect to login
      console.info('Wahoo token refresh failed, redirecting to Wahoo login...')
      clearAuth()

      try {
        const authUrl = await getAuthUrl()
        window.location.href = authUrl
      } catch (error) {
        console.error('Failed to get auth URL for redirect:', error)
        throw new Error('Authentication failed and unable to redirect to login')
      }
    }
  }

  /**
   * Get list of Wahoo activities
   */
  async function getActivities(
    page: number = 1,
    perPage: number = 30
  ): Promise<WahooActivity[]> {
    try {
      isLoading.value = true
      error.value = null

      const url = `/api/wahoo/activities?page=${page}&per_page=${perPage}`
      const response = await fetch(url)

      if (!response.ok) {
        await response.text()
        if (response.status === 401) {
          await handleAuthenticationError()
          throw new Error('Authentication failed - redirecting to login')
        }
        throw new Error(`Failed to get activities: ${response.statusText}`)
      }

      const data = await response.json()
      console.info(`Retrieved ${data.activities?.length || 0} Wahoo activities`)
      return data.activities
    } catch (err: any) {
      error.value = err.message || 'Failed to get activities'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Get route data for a specific activity
   */
  async function getActivityRoute(activityId: string): Promise<any> {
    try {
      isLoading.value = true
      error.value = null

      const url = `/api/wahoo/activities/${activityId}/route`
      const response = await fetch(url)

      if (!response.ok) {
        await response.text()
        if (response.status === 401) {
          await handleAuthenticationError()
          throw new Error('Authentication failed - redirecting to login')
        }
        throw new Error(
          `Failed to get route for activity ${activityId}: ${response.statusText}`
        )
      }

      const data = await response.json()
      console.info(
        `Retrieved route data for activity ${activityId}: ${data.points?.length || 0} points`
      )
      return data
    } catch (err: any) {
      error.value = err.message || 'Failed to get activity route'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Initialize authentication state and check for token refresh
   */
  async function initializeAuth(): Promise<void> {
    loadAuthState()

    // If we have a token but it's close to expiring, try to refresh it proactively
    if (authState.value.isAuthenticated && authState.value.expiresAt) {
      const timeUntilExpiry = authState.value.expiresAt * 1000 - Date.now()
      const fiveMinutes = 5 * 60 * 1000 // 5 minutes in milliseconds

      if (timeUntilExpiry < fiveMinutes && timeUntilExpiry > 0) {
        console.info('Wahoo token expires soon, attempting proactive refresh...')
        try {
          await handleAuthenticationError()
        } catch (error) {
          console.warn('Proactive Wahoo token refresh failed:', error)
        }
      }
    }
  }

  // Initialize auth state on composable creation
  initializeAuth()

  return {
    // State
    isLoading,
    error,
    authState,

    // Computed
    isAuthenticated: () => {
      if (!authState.value.isAuthenticated) return false
      if (!authState.value.expiresAt) return false
      return Date.now() < authState.value.expiresAt * 1000
    },

    // Methods
    getAuthUrl,
    exchangeCode,
    clearAuth,
    loadAuthState,
    getActivities,
    getActivityRoute,
    handleAuthenticationError,
    attemptTokenRefresh
  }
}
