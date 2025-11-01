/**
 * Simplified Wahoo API composable that uses backend endpoints
 * Replaces the complex TypeScript Wahoo API with simple fetch calls
 */

import { ref } from 'vue'

export interface WahooRoute {
  id: string
  name: string
  distance: number
  elevation_gain: number
  type: string
  created_at: string
  updated_at: string
  points: Array<{
    lat: number
    lng: number
    elevation?: number
  }>
}

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
          localStorage.removeItem('wahoo_auth')
          return
        }

        authState.value = parsed
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
    try {
      const response = await fetch('/api/wahoo/refresh-token', {
        method: 'POST'
      })

      if (response.ok) {
        // Reload auth state from localStorage (backend updated it)
        loadAuthState()
        return true
      }
    } catch {
      // Token refresh failed silently
    }

    return false
  }

  /**
   * Attempt to refresh token and redirect to login if failed
   */
  async function handleAuthenticationError(): Promise<void> {
    const refreshSuccess = await attemptTokenRefresh()

    if (!refreshSuccess) {
      // If refresh failed, clear auth and redirect to login
      clearAuth()

      try {
        // Store current path for redirect after auth
        const currentPath = window.location.pathname + window.location.search
        sessionStorage.setItem('wahoo_redirect_after_auth', currentPath)
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
        try {
          await handleAuthenticationError()
        } catch {
          // Proactive token refresh failed silently
        }
      }
    }
  }

  // Initialize auth state on composable creation
  initializeAuth()

  /**
   * Get available routes
   */
  async function getRoutes(): Promise<WahooRoute[]> {
    try {
      isLoading.value = true
      error.value = null

      const response = await fetch('/api/wahoo/routes')

      if (!response.ok) {
        await response.text()
        if (response.status === 401) {
          await handleAuthenticationError()
          throw new Error('Authentication failed - redirecting to login')
        }
        throw new Error(`Failed to get routes: ${response.statusText}`)
      }

      const data = await response.json()
      return data.routes || []
    } catch (err: any) {
      error.value = err.message || 'Failed to get routes'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Upload a route to Wahoo
   */
  async function uploadRoute(routeId: string): Promise<void> {
    try {
      isLoading.value = true
      error.value = null

      // Get the wahoo_id from the auth state
      const wahooId = authState.value.user?.id
      if (!wahooId) {
        throw new Error('No Wahoo user ID found')
      }

      const url = new URL(`/api/wahoo/routes/${routeId}/upload`, window.location.origin)
      url.searchParams.set('wahoo_id', String(wahooId))

      const response = await fetch(url.toString(), {
        method: 'POST'
      })

      if (!response.ok) {
        await response.text()
        if (response.status === 401) {
          await handleAuthenticationError()
          throw new Error('Authentication failed - redirecting to login')
        }
        throw new Error(`Failed to upload route: ${response.statusText}`)
      }

      await response.json()
    } catch (err: any) {
      error.value = err.message || 'Failed to upload route'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Delete a route from Wahoo Cloud
   */
  async function deleteRoute(routeId: string): Promise<void> {
    try {
      isLoading.value = true
      error.value = null

      // Get the wahoo_id from the auth state
      const wahooId = authState.value.user?.id
      if (!wahooId) {
        throw new Error('No Wahoo user ID found')
      }

      const url = new URL(`/api/wahoo/routes/${routeId}`, window.location.origin)
      url.searchParams.set('wahoo_id', wahooId.toString())

      const response = await fetch(url.toString(), {
        method: 'DELETE'
      })

      if (!response.ok) {
        await response.text()
        if (response.status === 401) {
          await handleAuthenticationError()
          throw new Error('Authentication failed - redirecting to login')
        }
        throw new Error(`Failed to delete route: ${response.statusText}`)
      }

      await response.json()
    } catch (err: any) {
      error.value = err.message || 'Failed to delete route'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Deauthorize the application and clear tokens
   */
  async function deauthorize(): Promise<void> {
    try {
      isLoading.value = true
      error.value = null

      // Get the wahoo_id from the auth state
      const wahooId = authState.value.user?.id
      if (!wahooId) {
        throw new Error('No Wahoo user ID found')
      }

      const formData = new FormData()
      formData.append('wahoo_id', wahooId.toString())

      const response = await fetch('/api/wahoo/deauthorize', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error('Failed to deauthorize')
      }

      // Clear local auth state
      clearAuth()
    } catch (err: any) {
      error.value = err.message || 'Failed to deauthorize'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Get user information from Wahoo
   */
  async function getUser(): Promise<any> {
    try {
      isLoading.value = true
      error.value = null

      const response = await fetch('/api/wahoo/user')

      if (!response.ok) {
        if (response.status === 401) {
          await handleAuthenticationError()
          throw new Error('Authentication failed')
        }
        throw new Error('Failed to get user info')
      }

      const data = await response.json()

      // Update auth state with user info
      authState.value.user = data

      // Save to localStorage
      localStorage.setItem('wahoo_auth', JSON.stringify(authState.value))

      return data
    } catch (err: any) {
      error.value = err.message || 'Failed to get user info'
      throw err
    } finally {
      isLoading.value = false
    }
  }

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
    attemptTokenRefresh,
    getRoutes,
    uploadRoute,
    deleteRoute,
    deauthorize,
    getUser
  }
}
