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
  const currentPage = ref(1)
  const perPage = ref(30)

  // Computed properties
  const filteredActivities = computed(() => {
    return activities.value.filter((activity) =>
      ['Ride', 'VirtualRide', 'EBikeRide'].includes(activity.sport_type)
    )
  })

  // Load activities from backend
  const loadActivities = async (
    page: number = 1,
    pageSize: number = 30
  ): Promise<void> => {
    try {
      isLoading.value = true
      error.value = null

      const fetchedActivities = await stravaApi.getActivities(page, pageSize)
      activities.value = fetchedActivities
      currentPage.value = page
      perPage.value = pageSize

      // Set hasMore based on whether we got a full page of results
      hasMore.value = fetchedActivities.length === pageSize

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
  const loadMoreActivities = async (): Promise<void> => {
    try {
      isLoading.value = true
      error.value = null

      const nextPage = currentPage.value + 1
      const fetchedActivities = await stravaApi.getActivities(nextPage, perPage.value)

      // Append new activities to existing ones
      activities.value = [...activities.value, ...fetchedActivities]
      currentPage.value = nextPage

      // Set hasMore based on whether we got a full page of results
      hasMore.value = fetchedActivities.length === perPage.value

      console.info(
        `Loaded ${fetchedActivities.length} more activities (page ${nextPage})`
      )
    } catch (err: any) {
      console.error(`Failed to load more activities:`, err)
      error.value = err.message || 'Failed to load more activities'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Refresh activities
  const refreshActivities = async (): Promise<void> => {
    activities.value = []
    currentPage.value = 1
    hasMore.value = false
    await loadActivities()
  }

  // Clear activities
  const clearActivities = (): void => {
    activities.value = []
    currentPage.value = 1
    hasMore.value = false
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
    currentPage,
    perPage,

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
