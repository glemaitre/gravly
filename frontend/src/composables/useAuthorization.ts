/**
 * Composable for checking authorization to access editor feature
 * Handles the authorization check against the backend
 */

import { ref, watch } from 'vue'
import { useStravaApi } from './useStravaApi'

export interface AuthorizationState {
  isAuthorizedForEditor: boolean
  isLoadingAuthorization: boolean
  authorizationError: string | null
}

export function useAuthorization() {
  const { authState } = useStravaApi()
  const isLoadingAuthorization = ref(false)
  const authorizationError = ref<string | null>(null)
  const isAuthorizedForEditor = ref(false)

  /**
   * Check if the current authenticated user is authorized to access editor
   */
  async function checkAuthorizationStatus(): Promise<void> {
    // If not authenticated, user cannot be authorized
    if (!authState.value.isAuthenticated || !authState.value.athlete) {
      authorizationError.value = null
      isAuthorizedForEditor.value = false
      return
    }

    // Get Strava ID from athlete object
    const stravaId = authState.value.athlete.id
    if (!stravaId) {
      authorizationError.value = 'No Strava ID found in athlete data'
      isAuthorizedForEditor.value = false
      return
    }

    try {
      isLoadingAuthorization.value = true
      authorizationError.value = null

      const response = await fetch(
        `/api/auth/check-authorization?strava_id=${stravaId}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        }
      )

      if (!response.ok) {
        throw new Error(`Authorization check failed: ${response.statusText}`)
      }

      const data = await response.json()
      isAuthorizedForEditor.value = data.authorized
    } catch (err: any) {
      authorizationError.value = err.message || 'Failed to check authorization'
      isAuthorizedForEditor.value = false
    } finally {
      isLoadingAuthorization.value = false
    }
  }

  /**
   * Clear authorization status (useful for logout)
   */
  function clearAuthorizationCache() {
    isAuthorizedForEditor.value = false
    authorizationError.value = null
  }

  // Watch for authentication state changes to check authorization
  watch(
    [() => authState.value.isAuthenticated, () => authState.value.athlete],
    ([isAuthenticated, athlete], [prevIsAuth, prevAthlete]) => {
      // Check authorization when authentication state changes
      if (
        isAuthenticated &&
        athlete &&
        (!prevIsAuth || prevAthlete?.id !== athlete?.id)
      ) {
        checkAuthorizationStatus()
      } else if (!isAuthenticated) {
        clearAuthorizationCache()
      }
    },
    { immediate: true }
  )

  return {
    checkAuthorizationStatus,
    isAuthorizedForEditor,
    isLoadingAuthorization,
    authorizationError,
    clearAuthorizationCache
  }
}
