/**
 * Strava Activities Composable
 * Simplified version that uses the new backend API
 */

import { ref, computed } from 'vue'
import { useStravaApi, type StravaActivity } from './useStravaApi'
import type { GPXData } from '../types'

export function useStravaActivities() {
  const stravaApi = useStravaApi()
  const activities = ref<StravaActivity[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const hasMore = ref(false)

  // Computed properties
  const filteredActivities = computed(() => {
    return activities.value.filter((activity) =>
      ['Ride', 'VirtualRide', 'EBikeRide'].includes(activity.sport_type)
    )
  })

  // Load activities from backend
  const loadActivities = async (
    page: number = 1,
    perPage: number = 30
  ): Promise<void> => {
    try {
      isLoading.value = true
      error.value = null

      const fetchedActivities = await stravaApi.getActivities(page, perPage)
      activities.value = fetchedActivities

      console.info(`Loaded ${fetchedActivities.length} activities from Strava`)
    } catch (err: any) {
      console.error(`Failed to load activities:`, err)
      error.value = err.message || 'Failed to load activities'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Load more activities (pagination)
  const loadMoreActivities = async (page: number = 1): Promise<void> => {
    try {
      const fetchedActivities = await stravaApi.getActivities(page, 30)
      activities.value.push(...fetchedActivities)
      console.info(`Loaded ${fetchedActivities.length} more activities`)
    } catch (err: any) {
      console.error(`Failed to load more activities:`, err)
      error.value = err.message || 'Failed to load more activities'
      throw err
    }
  }

  // Refresh activities
  const refreshActivities = async (): Promise<void> => {
    activities.value = []
    await loadActivities()
  }

  // Clear activities
  const clearActivities = (): void => {
    activities.value = []
    error.value = null
  }

  // Get GPX data for an activity
  const getActivityGpx = async (activityId: string): Promise<GPXData | null> => {
    try {
      isLoading.value = true
      error.value = null

      const gpxData = await stravaApi.getActivityGpx(activityId)
      console.info(`GPX data retrieved for activity ${activityId}`)

      return gpxData
    } catch (err: any) {
      console.error(`Failed to get GPX for activity ${activityId}:`, err)
      error.value = err.message || 'Failed to get activity GPX'
      return null
    } finally {
      isLoading.value = false
    }
  }

  return {
    // State
    activities,
    isLoading,
    error,
    hasMore,

    // Computed
    filteredActivities,

    // Methods
    loadActivities,
    loadMoreActivities,
    refreshActivities,
    clearActivities,
    getActivityGpx
  }
}
