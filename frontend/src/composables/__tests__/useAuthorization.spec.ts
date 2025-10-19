import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { useAuthorization } from '../useAuthorization'
import { useStravaApi } from '../useStravaApi'

// Mock useStravaApi
vi.mock('../useStravaApi', () => ({
  useStravaApi: vi.fn()
}))

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

describe('useAuthorization', () => {
  let mockStravaAuthState: any

  beforeEach(() => {
    vi.clearAllMocks()

    // Mock Strava API state
    mockStravaAuthState = {
      isAuthenticated: false,
      athlete: null
    }

    // Reset mock fetch
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ authorized: false, user: null })
    })

    // Mock useStravaApi returning reactive refs with all methods
    const mockStravaApi = vi.mocked(useStravaApi)
    mockStravaApi.mockReturnValue({
      // State
      isLoading: ref(false),
      error: ref(null),
      authState: ref(mockStravaAuthState),

      // Methods
      isAuthenticated: vi.fn(),
      getAuthUrl: vi.fn(),
      exchangeCode: vi.fn(),
      clearAuth: vi.fn(),
      loadAuthState: vi.fn(),
      getActivities: vi.fn(),
      getActivityGpx: vi.fn(),
      handleAuthenticationError: vi.fn(),
      attemptTokenRefresh: vi.fn()
    })
  })

  it('should initialize with unauthorized state', () => {
    const { isAuthorized, isLoadingAuthorization, authorizationError } =
      useAuthorization()

    expect(isAuthorized.value).toBe(false)
    expect(isLoadingAuthorization.value).toBe(false)
    expect(authorizationError.value).toBe(null)
  })

  it('should handle unauthenticated user', async () => {
    const { isAuthorized, authorizationError, checkAuthorizationStatus } =
      useAuthorization()

    // When not authenticated
    expect(isAuthorized.value).toBe(false)

    // Calling checkAuthorizationStatus when not authenticated should return early
    await checkAuthorizationStatus()
    expect(isAuthorized.value).toBe(false)
    expect(authorizationError.value).toBe(null)
  })

  it('should handle when athlete is null', async () => {
    // Setup authenticated but athlete is null
    mockStravaAuthState.isAuthenticated = true
    mockStravaAuthState.athlete = null

    const { isAuthorized, authorizationError, checkAuthorizationStatus } =
      useAuthorization()

    await checkAuthorizationStatus()

    expect(isAuthorized.value).toBe(false)
    expect(authorizationError.value).toBe(null)

    // Should not have called fetch since it returns early
    expect(mockFetch).not.toHaveBeenCalled()
  })

  it('should check authorization for authenticated user', async () => {
    // Setup authenticated user
    mockStravaAuthState.isAuthenticated = true
    mockStravaAuthState.athlete = { id: 820773, firstname: 'Test', lastname: 'User' }

    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        authorized: true,
        user: { strava_id: 820773, firstname: 'Test', lastname: 'User' }
      })
    })

    const { isAuthorized, checkAuthorizationStatus } = useAuthorization()

    await checkAuthorizationStatus()
    expect(mockFetch).toHaveBeenCalledWith(
      '/api/auth/check-authorization?strava_id=820773',
      expect.objectContaining({
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      })
    )
    expect(isAuthorized.value).toBe(true)
  })

  it('should handle API error when checking authorization', async () => {
    // Setup authenticated user
    mockStravaAuthState.isAuthenticated = true
    mockStravaAuthState.athlete = { id: 820773, firstname: 'Test', lastname: 'User' }

    mockFetch.mockRejectedValue(new Error('Network error'))

    const { isAuthorized, authorizationError, checkAuthorizationStatus } =
      useAuthorization()

    await checkAuthorizationStatus()

    expect(isAuthorized.value).toBe(false)
    expect(authorizationError.value).toBe('Network error')
  })

  it('should handle HTTP response error when response is not ok', async () => {
    // Setup authenticated user
    mockStravaAuthState.isAuthenticated = true
    mockStravaAuthState.athlete = { id: 820773, firstname: 'Test', lastname: 'User' }

    // Mock a response where response.ok is false
    mockFetch.mockResolvedValue({
      ok: false,
      statusText: 'Internal Server Error',
      json: async () => ({})
    })

    const { isAuthorized, authorizationError, checkAuthorizationStatus } =
      useAuthorization()

    await checkAuthorizationStatus()

    expect(isAuthorized.value).toBe(false)
    expect(authorizationError.value).toBe(
      'Authorization check failed: Internal Server Error'
    )
  })

  it('should clear authorization cache', () => {
    const { isAuthorized, clearAuthorizationCache } = useAuthorization()

    // Mock some cached result
    useStravaApi().authState.value.isAuthenticated = true

    clearAuthorizationCache()

    // This should clear cache and reset state
    expect(isAuthorized.value).toBe(false)
  })

  it('should handle missing athlete ID', async () => {
    mockStravaAuthState.isAuthenticated = true
    mockStravaAuthState.athlete = {} // No ID

    const { isAuthorized, authorizationError, checkAuthorizationStatus } =
      useAuthorization()

    await checkAuthorizationStatus()

    expect(isAuthorized.value).toBe(false)
    expect(authorizationError.value).toBe('No Strava ID found in athlete data')
  })

  it('should handle unauthorized user response', async () => {
    mockStravaAuthState.isAuthenticated = true
    mockStravaAuthState.athlete = { id: 123456, firstname: 'Test', lastname: 'User' }

    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ authorized: false, user: null })
    })

    const { isAuthorized, checkAuthorizationStatus } = useAuthorization()

    await checkAuthorizationStatus()

    expect(isAuthorized.value).toBe(false)
  })
})
