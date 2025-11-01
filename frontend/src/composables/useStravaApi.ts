/**
 * Simplified Strava API composable that uses backend endpoints
 * Replaces the complex TypeScript Strava API with simple fetch calls
 */

import { ref } from 'vue'

export interface StravaActivity {
  id: string
  name: string
  distance: number
  moving_time: number
  elapsed_time: number
  total_elevation_gain: number
  type: string
  sport_type: string
  start_date: string
  start_date_local: string
  timezone: string
  utc_offset: number
  start_latlng: [number, number] | null
  end_latlng: [number, number] | null
  achievement_count: number
  kudos_count: number
  comment_count: number
  athlete_count: number
  photo_count: number
  map: {
    id: string
    summary_polyline: string
    resource_state: number
  }
  trainer: boolean
  commute: boolean
  manual: boolean
  private: boolean
  flagged: boolean
  average_speed: number
  max_speed: number
  has_heartrate: boolean
  average_heartrate: number | null
  max_heartrate: number | null
  heartrate_opt_out: boolean
  display_hide_heartrate_option: boolean
  elev_high: number
  elev_low: number
  pr_count: number
  total_photo_count: number
  has_kudoed: boolean
  workout_type: number | null
}

export interface StravaAuthState {
  isAuthenticated: boolean
  accessToken: string | null
  expiresAt: number | null
  athlete: any | null
}

export function useStravaApi() {
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const authState = ref<StravaAuthState>({
    isAuthenticated: false,
    accessToken: null,
    expiresAt: null,
    athlete: null
  })

  /**
   * Get Strava OAuth authorization URL
   */
  async function getAuthUrl(state: string = 'strava_auth'): Promise<string> {
    try {
      isLoading.value = true
      error.value = null

      const url = new URL('/api/strava/auth-url', window.location.origin)
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

      const response = await fetch('/api/strava/exchange-code', {
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
        athlete: data.athlete
      }

      // Store in localStorage for persistence
      localStorage.setItem('strava_auth', JSON.stringify(authState.value))
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
      const stored = localStorage.getItem('strava_auth')
      if (stored) {
        const parsed = JSON.parse(stored)

        // Check if token is expired
        if (parsed.expiresAt && Date.now() > parsed.expiresAt * 1000) {
          localStorage.removeItem('strava_auth')
          return
        }

        authState.value = parsed
      }
    } catch (err) {
      console.error('Failed to load Strava auth state:', err)
      localStorage.removeItem('strava_auth')
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
      athlete: null
    }
    localStorage.removeItem('strava_auth')
  }

  /**
   * Attempt to refresh token only (no redirect)
   */
  async function attemptTokenRefresh(): Promise<boolean> {
    try {
      const response = await fetch('/api/strava/refresh-token', {
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
        sessionStorage.setItem('strava_redirect_after_auth', currentPath)
        const authUrl = await getAuthUrl()
        window.location.href = authUrl
      } catch (error) {
        console.error('Failed to get auth URL for redirect:', error)
        throw new Error('Authentication failed and unable to redirect to login')
      }
    }
  }

  /**
   * Get list of Strava activities
   */
  async function getActivities(
    page: number = 1,
    perPage: number = 30
  ): Promise<StravaActivity[]> {
    try {
      isLoading.value = true
      error.value = null

      // Get strava_id from athlete info
      const stravaId = authState.value.athlete?.id
      if (!stravaId) {
        throw new Error('No Strava user ID available')
      }

      const url = `/api/strava/activities?strava_id=${stravaId}&page=${page}&per_page=${perPage}`
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
   * Get GPX data for a specific activity
   */
  async function getActivityGpx(activityId: string): Promise<any> {
    try {
      isLoading.value = true
      error.value = null

      // Get strava_id from athlete info
      const stravaId = authState.value.athlete?.id
      if (!stravaId) {
        throw new Error('No Strava user ID available')
      }

      const url = `/api/strava/activities/${activityId}/gpx?strava_id=${stravaId}`
      const response = await fetch(url)

      if (!response.ok) {
        await response.text()
        if (response.status === 401) {
          await handleAuthenticationError()
          throw new Error('Authentication failed - redirecting to login')
        }
        throw new Error(
          `Failed to get GPX for activity ${activityId}: ${response.statusText}`
        )
      }

      const data = await response.json()
      return data
    } catch (err: any) {
      error.value = err.message || 'Failed to get activity GPX'
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
    getActivityGpx,
    handleAuthenticationError,
    attemptTokenRefresh
  }
}
