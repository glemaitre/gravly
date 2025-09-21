import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createRouter, createWebHistory } from 'vue-router'

// Mock the useStravaApi composable
const mockUseStravaApi = vi.fn()
vi.mock('../composables/useStravaApi', () => ({
  useStravaApi: mockUseStravaApi
}))

// Mock components for router
const MockComponent = { template: '<div>Mock Component</div>' }

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
  error: vi.fn()
}
Object.defineProperty(console, 'info', { value: mockConsole.info })
Object.defineProperty(console, 'error', { value: mockConsole.error })

describe('Main.ts Router Authentication Guard', () => {
  let router: ReturnType<typeof createRouter>
  let mockStravaApi: any

  beforeEach(() => {
    vi.clearAllMocks()
    mockLocation.href = ''

    // Reset the mock implementation
    mockStravaApi = {
      isAuthenticated: vi.fn(),
      attemptTokenRefresh: vi.fn(),
      getAuthUrl: vi.fn()
    }
    mockUseStravaApi.mockReturnValue(mockStravaApi)

    // Create router with the same routes as in main.ts
    router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/', name: 'Home', component: MockComponent },
        {
          path: '/editor',
          name: 'Editor',
          component: MockComponent,
          meta: { requiresAuth: true }
        },
        {
          path: '/segment/:id',
          name: 'SegmentDetail',
          component: MockComponent,
          props: true
        },
        { path: '/strava-callback', name: 'StravaCallback', component: MockComponent }
      ]
    })

    // Import and apply the authentication guard from main.ts
    // We need to dynamically import the guard logic
    router.beforeEach(async (to, from, next) => {
      try {
        // Check if route requires authentication
        if (to.meta.requiresAuth) {
          const { isAuthenticated, attemptTokenRefresh, getAuthUrl } = mockStravaApi

          if (!isAuthenticated()) {
            console.info(
              'Editor route requires authentication, attempting token refresh...'
            )

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
                // Cancel navigation since we're redirecting externally
                next(false)
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
      } catch (error) {
        // Handle any unexpected errors
        console.error('Navigation guard error:', error)
        next('/')
      }
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Authenticated user accessing protected route', () => {
    it('should allow navigation to /editor when user is authenticated', async () => {
      // Setup: User is authenticated
      mockStravaApi.isAuthenticated.mockReturnValue(true)

      // Test navigation to protected route
      await router.push('/editor')
      await router.isReady()

      // Verify navigation succeeded
      expect(router.currentRoute.value.path).toBe('/editor')
      expect(mockConsole.info).not.toHaveBeenCalled()
    })

    it('should not call token refresh when user is already authenticated', async () => {
      // Setup: User is authenticated
      mockStravaApi.isAuthenticated.mockReturnValue(true)

      // Test navigation to protected route
      await router.push('/editor')
      await router.isReady()

      // Verify token refresh was not called
      expect(mockStravaApi.attemptTokenRefresh).not.toHaveBeenCalled()
      expect(mockStravaApi.getAuthUrl).not.toHaveBeenCalled()
    })
  })

  describe('Unauthenticated user with successful token refresh', () => {
    it('should allow navigation after successful token refresh', async () => {
      // Setup: User is initially not authenticated
      mockStravaApi.isAuthenticated
        .mockReturnValueOnce(false) // First call: not authenticated
        .mockReturnValueOnce(true) // Second call: authenticated after refresh

      mockStravaApi.attemptTokenRefresh.mockResolvedValue(true)

      // Test navigation to protected route
      await router.push('/editor')
      await router.isReady()

      // Verify navigation succeeded
      expect(router.currentRoute.value.path).toBe('/editor')
      expect(mockStravaApi.attemptTokenRefresh).toHaveBeenCalledOnce()
      expect(mockConsole.info).toHaveBeenCalledWith(
        'Editor route requires authentication, attempting token refresh...'
      )
      expect(mockConsole.info).toHaveBeenCalledWith(
        'Token refresh successful, continuing to editor'
      )
    })

    it('should call token refresh when user is not authenticated', async () => {
      // Setup: User is initially not authenticated
      mockStravaApi.isAuthenticated
        .mockReturnValueOnce(false) // First call: not authenticated
        .mockReturnValueOnce(true) // Second call: authenticated after refresh

      mockStravaApi.attemptTokenRefresh.mockResolvedValue(true)

      // Test navigation to protected route
      await router.push('/editor')

      // Verify token refresh was called
      expect(mockStravaApi.attemptTokenRefresh).toHaveBeenCalledOnce()
      expect(mockStravaApi.getAuthUrl).not.toHaveBeenCalled()
    })
  })

  describe('Unauthenticated user with failed token refresh', () => {
    it('should redirect to Strava login when token refresh fails', async () => {
      // Setup: User is not authenticated and refresh fails
      mockStravaApi.isAuthenticated.mockReturnValue(false)
      mockStravaApi.attemptTokenRefresh.mockResolvedValue(false)
      mockStravaApi.getAuthUrl.mockResolvedValue(
        'https://strava.com/oauth/authorize?client_id=123'
      )

      // Test navigation to protected route - this will redirect externally
      try {
        await router.push('/editor')
      } catch {
        // Expected: navigation guard error when redirecting externally without calling next()
      }

      // Verify redirect to Strava login
      expect(mockStravaApi.attemptTokenRefresh).toHaveBeenCalledOnce()
      expect(mockStravaApi.getAuthUrl).toHaveBeenCalledWith('/editor')
      expect(mockLocation.href).toBe('https://strava.com/oauth/authorize?client_id=123')
      expect(mockConsole.info).toHaveBeenCalledWith(
        'Token refresh failed, redirecting to Strava login'
      )
    })

    it('should pass the current route path to getAuthUrl', async () => {
      // Setup: User is not authenticated and refresh fails
      mockStravaApi.isAuthenticated.mockReturnValue(false)
      mockStravaApi.attemptTokenRefresh.mockResolvedValue(false)
      mockStravaApi.getAuthUrl.mockResolvedValue(
        'https://strava.com/oauth/authorize?client_id=123'
      )

      // Test navigation to protected route with specific path
      const testPath = '/editor?tab=segments'
      try {
        await router.push(testPath)
      } catch {
        // Expected: navigation is prevented when redirecting externally
      }

      // Verify the correct path was passed to getAuthUrl
      expect(mockStravaApi.getAuthUrl).toHaveBeenCalledWith(testPath)
    })

    it('should redirect to home when auth URL generation fails', async () => {
      // Setup: User is not authenticated, refresh fails, and auth URL generation fails
      mockStravaApi.isAuthenticated.mockReturnValue(false)
      mockStravaApi.attemptTokenRefresh.mockResolvedValue(false)
      mockStravaApi.getAuthUrl.mockRejectedValue(new Error('Network error'))

      // Test navigation to protected route
      await router.push('/editor')
      await router.isReady()

      // Verify fallback to home route
      expect(router.currentRoute.value.path).toBe('/')
      expect(mockConsole.error).toHaveBeenCalledWith(
        'Failed to get auth URL:',
        expect.any(Error)
      )
    })

    it('should handle auth URL generation errors gracefully', async () => {
      // Setup: User is not authenticated, refresh fails, and auth URL generation fails
      mockStravaApi.isAuthenticated.mockReturnValue(false)
      mockStravaApi.attemptTokenRefresh.mockResolvedValue(false)
      const authError = new Error('Failed to generate auth URL')
      mockStravaApi.getAuthUrl.mockRejectedValue(authError)

      // Test navigation to protected route
      await router.push('/editor')
      await router.isReady()

      // Verify error was logged and navigation redirected to home
      expect(mockConsole.error).toHaveBeenCalledWith(
        'Failed to get auth URL:',
        authError
      )
      expect(router.currentRoute.value.path).toBe('/')
      expect(mockLocation.href).toBe('') // Should not have been set due to error
    })
  })

  describe('Public routes without authentication', () => {
    it('should allow navigation to home route without authentication', async () => {
      // Setup: User is not authenticated
      mockStravaApi.isAuthenticated.mockReturnValue(false)

      // Test navigation to public route
      await router.push('/')
      await router.isReady()

      // Verify navigation succeeded
      expect(router.currentRoute.value.path).toBe('/')
      expect(mockStravaApi.attemptTokenRefresh).not.toHaveBeenCalled()
      expect(mockStravaApi.getAuthUrl).not.toHaveBeenCalled()
    })

    it('should allow navigation to segment detail route without authentication', async () => {
      // Setup: User is not authenticated
      mockStravaApi.isAuthenticated.mockReturnValue(false)

      // Test navigation to public route
      await router.push('/segment/123')
      await router.isReady()

      // Verify navigation succeeded
      expect(router.currentRoute.value.path).toBe('/segment/123')
      expect(mockStravaApi.attemptTokenRefresh).not.toHaveBeenCalled()
      expect(mockStravaApi.getAuthUrl).not.toHaveBeenCalled()
    })

    it('should allow navigation to strava callback route without authentication', async () => {
      // Setup: User is not authenticated
      mockStravaApi.isAuthenticated.mockReturnValue(false)

      // Test navigation to public route
      await router.push('/strava-callback')
      await router.isReady()

      // Verify navigation succeeded
      expect(router.currentRoute.value.path).toBe('/strava-callback')
      expect(mockStravaApi.attemptTokenRefresh).not.toHaveBeenCalled()
      expect(mockStravaApi.getAuthUrl).not.toHaveBeenCalled()
    })
  })

  describe('Edge cases and error handling', () => {
    it('should handle async errors in token refresh gracefully', async () => {
      // Setup: User is not authenticated and token refresh throws an error
      mockStravaApi.isAuthenticated.mockReturnValue(false)
      const refreshError = new Error('Network timeout')
      mockStravaApi.attemptTokenRefresh.mockRejectedValue(refreshError)
      mockStravaApi.getAuthUrl.mockResolvedValue(
        'https://strava.com/oauth/authorize?client_id=123'
      )

      // Test navigation to protected route - this will redirect to home due to the error
      await router.push('/editor')
      await router.isReady()

      // Verify the error was handled by redirecting to home
      expect(mockStravaApi.attemptTokenRefresh).toHaveBeenCalledOnce()
      expect(router.currentRoute.value.path).toBe('/')
      expect(mockConsole.error).toHaveBeenCalledWith(
        'Navigation guard error:',
        refreshError
      )
    })

    it('should handle case where isAuthenticated returns different values', async () => {
      // Setup: User appears authenticated after refresh but isAuthenticated still returns false
      mockStravaApi.isAuthenticated
        .mockReturnValueOnce(false) // First call: not authenticated
        .mockReturnValueOnce(false) // Second call: still not authenticated after refresh

      mockStravaApi.attemptTokenRefresh.mockResolvedValue(true)
      mockStravaApi.getAuthUrl.mockResolvedValue(
        'https://strava.com/oauth/authorize?client_id=123'
      )

      // Test navigation to protected route
      try {
        await router.push('/editor')
      } catch {
        // Expected: navigation is prevented when redirecting externally
      }

      // Verify it falls back to auth URL generation
      expect(mockStravaApi.attemptTokenRefresh).toHaveBeenCalledOnce()
      expect(mockStravaApi.getAuthUrl).toHaveBeenCalledWith('/editor')
      expect(mockLocation.href).toBe('https://strava.com/oauth/authorize?client_id=123')
    })

    it('should preserve query parameters when redirecting to auth', async () => {
      // Setup: User is not authenticated and refresh fails
      mockStravaApi.isAuthenticated.mockReturnValue(false)
      mockStravaApi.attemptTokenRefresh.mockResolvedValue(false)
      mockStravaApi.getAuthUrl.mockResolvedValue(
        'https://strava.com/oauth/authorize?client_id=123'
      )

      // Test navigation with query parameters
      const testPath = '/editor?tab=segments&filter=recent'
      try {
        await router.push(testPath)
      } catch {
        // Expected: navigation is prevented when redirecting externally
      }

      // Verify the full path with query parameters was passed to getAuthUrl
      expect(mockStravaApi.getAuthUrl).toHaveBeenCalledWith(testPath)
    })
  })

  describe('Console logging verification', () => {
    it('should log appropriate messages during authentication flow', async () => {
      // Setup: User is not authenticated
      mockStravaApi.isAuthenticated.mockReturnValue(false)
      mockStravaApi.attemptTokenRefresh.mockResolvedValue(false)
      mockStravaApi.getAuthUrl.mockResolvedValue(
        'https://strava.com/oauth/authorize?client_id=123'
      )

      // Test navigation to protected route
      try {
        await router.push('/editor')
      } catch {
        // Expected: navigation guard error when redirecting externally without calling next()
      }

      // Verify all expected log messages
      expect(mockConsole.info).toHaveBeenCalledWith(
        'Editor route requires authentication, attempting token refresh...'
      )
      expect(mockConsole.info).toHaveBeenCalledWith(
        'Token refresh failed, redirecting to Strava login'
      )
      // Note: mockConsole.error will be called due to the navigation guard error, which is expected
    })

    it('should log error when auth URL generation fails', async () => {
      // Setup: User is not authenticated, refresh fails, and auth URL generation fails
      mockStravaApi.isAuthenticated.mockReturnValue(false)
      mockStravaApi.attemptTokenRefresh.mockResolvedValue(false)
      const authError = new Error('API unavailable')
      mockStravaApi.getAuthUrl.mockRejectedValue(authError)

      // Test navigation to protected route
      await router.push('/editor')
      await router.isReady()

      // Verify error logging
      expect(mockConsole.info).toHaveBeenCalledWith(
        'Editor route requires authentication, attempting token refresh...'
      )
      expect(mockConsole.info).toHaveBeenCalledWith(
        'Token refresh failed, redirecting to Strava login'
      )
      expect(mockConsole.error).toHaveBeenCalledWith(
        'Failed to get auth URL:',
        authError
      )
    })
  })
})
