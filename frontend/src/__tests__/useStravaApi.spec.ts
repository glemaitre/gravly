import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useStravaApi, type StravaActivity } from '../composables/useStravaApi'

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
  writable: true
})

// Mock window.location
const mockLocation = {
  href: '',
  origin: 'http://localhost:3000'
}
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true
})

// Mock console methods to avoid noise in tests
const mockConsole = {
  info: vi.fn(),
  error: vi.fn(),
  log: vi.fn(),
  warn: vi.fn()
}
Object.defineProperty(console, 'info', { value: mockConsole.info })
Object.defineProperty(console, 'error', { value: mockConsole.error })
Object.defineProperty(console, 'log', { value: mockConsole.log })
Object.defineProperty(console, 'warn', { value: mockConsole.warn })

describe('useStravaApi', () => {
  let composable: ReturnType<typeof useStravaApi>

  beforeEach(() => {
    vi.clearAllMocks()
    mockLocation.href = ''

    // Reset localStorage mock
    mockLocalStorage.getItem.mockReturnValue(null)
    mockLocalStorage.setItem.mockClear()
    mockLocalStorage.removeItem.mockClear()

    // Reset fetch mock
    mockFetch.mockClear()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Initialization', () => {
    it('should initialize with default auth state', () => {
      composable = useStravaApi()

      expect(composable.isLoading.value).toBe(false)
      expect(composable.error.value).toBe(null)
      expect(composable.authState.value).toEqual({
        isAuthenticated: false,
        accessToken: null,
        expiresAt: null,
        athlete: null
      })
      expect(composable.isAuthenticated()).toBe(false)
    })

    it('should load auth state from localStorage on initialization', () => {
      const storedAuth = {
        isAuthenticated: true,
        accessToken: 'mock-token',
        expiresAt: Math.floor(Date.now() / 1000) + 3600, // 1 hour from now
        athlete: { id: 123, name: 'Test Athlete' }
      }

      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(storedAuth))

      composable = useStravaApi()

      expect(mockLocalStorage.getItem).toHaveBeenCalledWith('strava_auth')
      expect(composable.authState.value).toEqual(storedAuth)
      expect(composable.isAuthenticated()).toBe(true)
    })

    it('should clear expired token from localStorage', () => {
      const expiredAuth = {
        isAuthenticated: true,
        accessToken: 'mock-token',
        expiresAt: Math.floor(Date.now() / 1000) - 3600, // 1 hour ago
        athlete: { id: 123, name: 'Test Athlete' }
      }

      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(expiredAuth))

      composable = useStravaApi()

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('strava_auth')
      expect(composable.authState.value).toEqual({
        isAuthenticated: false,
        accessToken: null,
        expiresAt: null,
        athlete: null
      })
      expect(mockConsole.log).toHaveBeenCalledWith(
        'Strava token expired, clearing auth state'
      )
    })

    it('should handle malformed localStorage data gracefully', () => {
      mockLocalStorage.getItem.mockReturnValue('invalid-json')

      composable = useStravaApi()

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('strava_auth')
      expect(mockConsole.error).toHaveBeenCalledWith(
        'Failed to load Strava auth state:',
        expect.any(Error)
      )
    })
  })

  describe('getAuthUrl', () => {
    beforeEach(() => {
      composable = useStravaApi()
    })

    it('should successfully get auth URL', async () => {
      const mockAuthUrl = 'https://strava.com/oauth/authorize?client_id=123'
      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue({ auth_url: mockAuthUrl })
      }
      mockFetch.mockResolvedValue(mockResponse)

      const result = await composable.getAuthUrl('test-state')

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:3000/api/strava/auth-url?state=test-state'
      )
      expect(result).toBe(mockAuthUrl)
      expect(composable.isLoading.value).toBe(false)
      expect(composable.error.value).toBe(null)
    })

    it('should use default state parameter', async () => {
      const mockAuthUrl = 'https://strava.com/oauth/authorize?client_id=123'
      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue({ auth_url: mockAuthUrl })
      }
      mockFetch.mockResolvedValue(mockResponse)

      await composable.getAuthUrl()

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:3000/api/strava/auth-url?state=strava_auth'
      )
    })

    it('should handle fetch errors', async () => {
      const mockResponse = {
        ok: false,
        statusText: 'Internal Server Error',
        text: vi.fn().mockResolvedValue('Server Error')
      }
      mockFetch.mockResolvedValue(mockResponse)

      await expect(composable.getAuthUrl()).rejects.toThrow(
        'Failed to get auth URL: Internal Server Error'
      )
      expect(composable.error.value).toBe(
        'Failed to get auth URL: Internal Server Error'
      )
      expect(composable.isLoading.value).toBe(false)
    })

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'))

      await expect(composable.getAuthUrl()).rejects.toThrow('Network error')
      expect(composable.error.value).toBe('Network error')
      expect(composable.isLoading.value).toBe(false)
    })

    it('should set loading state correctly', async () => {
      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue({ auth_url: 'test-url' })
      }
      mockFetch.mockResolvedValue(mockResponse)

      const promise = composable.getAuthUrl()
      expect(composable.isLoading.value).toBe(true)

      await promise
      expect(composable.isLoading.value).toBe(false)
    })
  })

  describe('exchangeCode', () => {
    beforeEach(() => {
      composable = useStravaApi()
    })

    it('should successfully exchange code for token', async () => {
      const mockTokenData = {
        access_token: 'mock-access-token',
        expires_at: Math.floor(Date.now() / 1000) + 3600,
        athlete: { id: 123, name: 'Test Athlete' }
      }
      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue(mockTokenData)
      }
      mockFetch.mockResolvedValue(mockResponse)

      await composable.exchangeCode('mock-auth-code')

      expect(mockFetch).toHaveBeenCalledWith('/api/strava/exchange-code', {
        method: 'POST',
        body: expect.any(FormData)
      })

      // Check FormData content
      const formDataCall = mockFetch.mock.calls[0][1]
      expect(formDataCall.body).toBeInstanceOf(FormData)

      expect(composable.authState.value).toEqual({
        isAuthenticated: true,
        accessToken: mockTokenData.access_token,
        expiresAt: mockTokenData.expires_at,
        athlete: mockTokenData.athlete
      })
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'strava_auth',
        JSON.stringify(composable.authState.value)
      )
      expect(composable.isLoading.value).toBe(false)
      expect(composable.error.value).toBe(null)
    })

    it('should handle exchange errors', async () => {
      const mockResponse = {
        ok: false,
        statusText: 'Bad Request',
        text: vi.fn().mockResolvedValue('Invalid code')
      }
      mockFetch.mockResolvedValue(mockResponse)

      await expect(composable.exchangeCode('invalid-code')).rejects.toThrow(
        'Failed to exchange code: Bad Request'
      )
      expect(composable.error.value).toBe('Failed to exchange code: Bad Request')
      expect(composable.isLoading.value).toBe(false)
    })

    it('should handle network errors during exchange', async () => {
      mockFetch.mockRejectedValue(new Error('Network timeout'))

      await expect(composable.exchangeCode('mock-code')).rejects.toThrow(
        'Network timeout'
      )
      expect(composable.error.value).toBe('Network timeout')
      expect(composable.isLoading.value).toBe(false)
    })
  })

  describe('clearAuth', () => {
    beforeEach(() => {
      composable = useStravaApi()
      // Set some auth state first
      composable.authState.value = {
        isAuthenticated: true,
        accessToken: 'mock-token',
        expiresAt: Math.floor(Date.now() / 1000) + 3600,
        athlete: { id: 123, name: 'Test Athlete' }
      }
    })

    it('should clear authentication state', () => {
      composable.clearAuth()

      expect(composable.authState.value).toEqual({
        isAuthenticated: false,
        accessToken: null,
        expiresAt: null,
        athlete: null
      })
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('strava_auth')
      expect(composable.isAuthenticated()).toBe(false)
    })
  })

  describe('loadAuthState', () => {
    beforeEach(() => {
      composable = useStravaApi()
    })

    it('should load valid auth state from localStorage', () => {
      const storedAuth = {
        isAuthenticated: true,
        accessToken: 'mock-token',
        expiresAt: Math.floor(Date.now() / 1000) + 3600,
        athlete: { id: 123, name: 'Test Athlete' }
      }

      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(storedAuth))

      composable.loadAuthState()

      expect(composable.authState.value).toEqual(storedAuth)
      expect(mockConsole.log).toHaveBeenCalledWith(
        'Loaded Strava auth state from localStorage'
      )
    })

    it('should handle missing localStorage data', () => {
      mockLocalStorage.getItem.mockReturnValue(null)

      composable.loadAuthState()

      expect(composable.authState.value).toEqual({
        isAuthenticated: false,
        accessToken: null,
        expiresAt: null,
        athlete: null
      })
    })

    it('should clear expired tokens', () => {
      const expiredAuth = {
        isAuthenticated: true,
        accessToken: 'mock-token',
        expiresAt: Math.floor(Date.now() / 1000) - 3600,
        athlete: { id: 123, name: 'Test Athlete' }
      }

      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(expiredAuth))

      composable.loadAuthState()

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('strava_auth')
      expect(composable.authState.value).toEqual({
        isAuthenticated: false,
        accessToken: null,
        expiresAt: null,
        athlete: null
      })
    })
  })

  describe('attemptTokenRefresh', () => {
    beforeEach(() => {
      composable = useStravaApi()
    })

    it('should successfully refresh token', async () => {
      const mockResponse = { ok: true }
      mockFetch.mockResolvedValue(mockResponse)

      const result = await composable.attemptTokenRefresh()

      expect(result).toBe(true)
      expect(mockFetch).toHaveBeenCalledWith('/api/strava/refresh-token', {
        method: 'POST'
      })
      expect(mockConsole.info).toHaveBeenCalledWith('Token refreshed successfully')
    })

    it('should return false on failed refresh', async () => {
      const mockResponse = { ok: false }
      mockFetch.mockResolvedValue(mockResponse)

      const result = await composable.attemptTokenRefresh()

      expect(result).toBe(false)
      // The actual implementation doesn't log on failed refresh, only on network errors
    })

    it('should return false on network error', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'))

      const result = await composable.attemptTokenRefresh()

      expect(result).toBe(false)
      expect(mockConsole.warn).toHaveBeenCalledWith(
        'Token refresh failed:',
        expect.any(Error)
      )
    })
  })

  describe('handleAuthenticationError', () => {
    beforeEach(() => {
      // Clear all mocks before each test
      vi.clearAllMocks()
      mockLocation.href = ''

      // Set up default mocks to prevent initialization errors
      mockLocalStorage.getItem.mockReturnValue(null)
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ auth_url: 'test' })
      })

      composable = useStravaApi()
    })

    it('should refresh token successfully and not redirect', async () => {
      // Mock attemptTokenRefresh to return true
      mockFetch.mockResolvedValueOnce({ ok: true })

      await composable.handleAuthenticationError()

      expect(mockLocation.href).toBe('')
    })

    it('should redirect to login when refresh fails', async () => {
      // Mock refresh to fail and auth URL to succeed
      mockFetch
        .mockResolvedValueOnce({ ok: false }) // refresh fails
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ auth_url: 'https://strava.com/auth' })
        }) // auth URL succeeds

      await composable.handleAuthenticationError()

      expect(mockLocation.href).toBe('https://strava.com/auth')
    })

    it('should handle auth URL generation failure', async () => {
      // Mock refresh to fail and auth URL to fail
      mockFetch
        .mockResolvedValueOnce({ ok: false }) // refresh fails
        .mockRejectedValueOnce(new Error('Auth service down')) // auth URL fails

      await expect(composable.handleAuthenticationError()).rejects.toThrow(
        'Authentication failed and unable to redirect to login'
      )

      expect(mockConsole.error).toHaveBeenCalledWith(
        'Failed to get auth URL for redirect:',
        expect.any(Error)
      )
    })
  })

  describe('getActivities', () => {
    beforeEach(() => {
      composable = useStravaApi()
      // Set up auth state with athlete ID
      composable.authState.value = {
        isAuthenticated: true,
        accessToken: 'mock-token',
        expiresAt: Math.floor(Date.now() / 1000) + 3600,
        athlete: { id: 12345 }
      }
    })

    it('should successfully fetch activities', async () => {
      const mockActivities: StravaActivity[] = [
        {
          id: '1',
          name: 'Morning Ride',
          distance: 10000,
          moving_time: 1800,
          elapsed_time: 1900,
          total_elevation_gain: 100,
          type: 'Ride',
          sport_type: 'cycling',
          start_date: '2024-01-01T10:00:00Z',
          start_date_local: '2024-01-01T11:00:00Z',
          timezone: 'Europe/Paris',
          utc_offset: 3600,
          start_latlng: [48.8566, 2.3522],
          end_latlng: [48.8566, 2.3522],
          achievement_count: 0,
          kudos_count: 5,
          comment_count: 2,
          athlete_count: 1,
          photo_count: 0,
          map: {
            id: 'map1',
            summary_polyline: 'encoded_polyline',
            resource_state: 2
          },
          trainer: false,
          commute: false,
          manual: false,
          private: false,
          flagged: false,
          average_speed: 5.56,
          max_speed: 12.0,
          has_heartrate: false,
          average_heartrate: null,
          max_heartrate: null,
          heartrate_opt_out: false,
          display_hide_heartrate_option: false,
          elev_high: 100,
          elev_low: 50,
          pr_count: 0,
          total_photo_count: 0,
          has_kudoed: false,
          workout_type: null
        }
      ]

      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue({ activities: mockActivities })
      }
      mockFetch.mockResolvedValue(mockResponse)

      const result = await composable.getActivities(1, 30)

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/strava/activities?strava_id=12345&page=1&per_page=30'
      )
      expect(result).toEqual(mockActivities)
      expect(composable.isLoading.value).toBe(false)
      expect(composable.error.value).toBe(null)
      expect(mockConsole.info).toHaveBeenCalledWith('Retrieved 1 Strava activities')
    })

    it('should use default pagination parameters', async () => {
      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue({ activities: [] })
      }
      mockFetch.mockResolvedValue(mockResponse)

      await composable.getActivities()

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/strava/activities?strava_id=12345&page=1&per_page=30'
      )
    })

    it('should handle authentication error', async () => {
      const mockResponse = {
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        text: vi.fn().mockResolvedValue('Unauthorized')
      }
      mockFetch.mockResolvedValue(mockResponse)

      vi.spyOn(composable, 'handleAuthenticationError')

      await expect(composable.getActivities()).rejects.toThrow(
        'Authentication failed and unable to redirect to login'
      )

      expect(composable.isLoading.value).toBe(false)
    })

    it('should handle other API errors', async () => {
      const mockResponse = {
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        text: vi.fn().mockResolvedValue('Server Error')
      }
      mockFetch.mockResolvedValue(mockResponse)

      await expect(composable.getActivities()).rejects.toThrow(
        'Failed to get activities: Internal Server Error'
      )
      expect(composable.error.value).toBe(
        'Failed to get activities: Internal Server Error'
      )
    })

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'))

      await expect(composable.getActivities()).rejects.toThrow('Network error')
      expect(composable.error.value).toBe('Network error')
    })
  })

  describe('getActivityGpx', () => {
    beforeEach(() => {
      composable = useStravaApi()
      // Set up auth state with athlete ID
      composable.authState.value = {
        isAuthenticated: true,
        accessToken: 'mock-token',
        expiresAt: Math.floor(Date.now() / 1000) + 3600,
        athlete: { id: 12345 }
      }
    })

    it('should successfully fetch GPX data', async () => {
      const mockGpxData = {
        points: [
          { lat: 48.8566, lng: 2.3522, elevation: 100 },
          { lat: 48.8567, lng: 2.3523, elevation: 105 }
        ],
        summary: 'GPX data for activity'
      }

      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue(mockGpxData)
      }
      mockFetch.mockResolvedValue(mockResponse)

      const result = await composable.getActivityGpx('activity-123')

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/strava/activities/activity-123/gpx?strava_id=12345'
      )
      expect(result).toEqual(mockGpxData)
      expect(composable.isLoading.value).toBe(false)
      expect(composable.error.value).toBe(null)
      expect(mockConsole.info).toHaveBeenCalledWith(
        'Retrieved GPX data for activity activity-123: 2 points'
      )
    })

    it('should handle authentication error', async () => {
      const mockResponse = {
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        text: vi.fn().mockResolvedValue('Unauthorized')
      }
      mockFetch.mockResolvedValue(mockResponse)

      vi.spyOn(composable, 'handleAuthenticationError')

      await expect(composable.getActivityGpx('activity-123')).rejects.toThrow(
        'Authentication failed and unable to redirect to login'
      )

      expect(composable.isLoading.value).toBe(false)
    })

    it('should handle other API errors', async () => {
      const mockResponse = {
        ok: false,
        status: 404,
        statusText: 'Not Found',
        text: vi.fn().mockResolvedValue('Activity not found')
      }
      mockFetch.mockResolvedValue(mockResponse)

      await expect(composable.getActivityGpx('invalid-id')).rejects.toThrow(
        'Failed to get GPX for activity invalid-id: Not Found'
      )
      expect(composable.error.value).toBe(
        'Failed to get GPX for activity invalid-id: Not Found'
      )
    })

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValue(new Error('Network timeout'))

      await expect(composable.getActivityGpx('activity-123')).rejects.toThrow(
        'Network timeout'
      )
      expect(composable.error.value).toBe('Network timeout')
    })
  })

  describe('isAuthenticated computed', () => {
    beforeEach(() => {
      composable = useStravaApi()
    })

    it('should return false when not authenticated', () => {
      composable.authState.value = {
        isAuthenticated: false,
        accessToken: null,
        expiresAt: null,
        athlete: null
      }

      expect(composable.isAuthenticated()).toBe(false)
    })

    it('should return false when no expiresAt', () => {
      composable.authState.value = {
        isAuthenticated: true,
        accessToken: 'mock-token',
        expiresAt: null,
        athlete: { id: 123, name: 'Test Athlete' }
      }

      expect(composable.isAuthenticated()).toBe(false)
    })

    it('should return false when token is expired', () => {
      composable.authState.value = {
        isAuthenticated: true,
        accessToken: 'mock-token',
        expiresAt: Math.floor(Date.now() / 1000) - 3600, // 1 hour ago
        athlete: { id: 123, name: 'Test Athlete' }
      }

      expect(composable.isAuthenticated()).toBe(false)
    })

    it('should return true when token is valid and not expired', () => {
      composable.authState.value = {
        isAuthenticated: true,
        accessToken: 'mock-token',
        expiresAt: Math.floor(Date.now() / 1000) + 3600, // 1 hour from now
        athlete: { id: 123, name: 'Test Athlete' }
      }

      expect(composable.isAuthenticated()).toBe(true)
    })
  })

  describe('Error handling and edge cases', () => {
    beforeEach(() => {
      composable = useStravaApi()
    })

    it('should handle concurrent API calls', async () => {
      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue({ auth_url: 'test-url' })
      }
      mockFetch.mockResolvedValue(mockResponse)

      // Make concurrent calls
      const promises = [
        composable.getAuthUrl('state1'),
        composable.getAuthUrl('state2'),
        composable.getAuthUrl('state3')
      ]

      await Promise.all(promises)

      expect(mockFetch).toHaveBeenCalledTimes(3)
      expect(composable.isLoading.value).toBe(false)
    })

    it('should handle malformed JSON responses', async () => {
      const mockResponse = {
        ok: true,
        json: vi.fn().mockRejectedValue(new Error('Invalid JSON'))
      }
      mockFetch.mockResolvedValue(mockResponse)

      await expect(composable.getAuthUrl()).rejects.toThrow('Invalid JSON')
      expect(composable.error.value).toBe('Invalid JSON')
    })

    it('should preserve error state between calls', async () => {
      // First call fails
      mockFetch.mockRejectedValueOnce(new Error('First error'))
      await expect(composable.getAuthUrl()).rejects.toThrow('First error')
      expect(composable.error.value).toBe('First error')

      // Second call succeeds
      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue({ auth_url: 'test-url' })
      }
      mockFetch.mockResolvedValue(mockResponse)

      await composable.getAuthUrl()
      expect(composable.error.value).toBe(null)
    })
  })
})
