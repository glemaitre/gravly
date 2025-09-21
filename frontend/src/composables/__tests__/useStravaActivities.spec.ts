import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import type { GPXData } from '../../types'
import type { StravaActivity } from '../useStravaApi'

// Mock the useStravaApi composable
vi.mock('../useStravaApi', () => ({
  useStravaApi: vi.fn()
}))

import { useStravaActivities } from '../useStravaActivities'
import { useStravaApi } from '../useStravaApi'

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

describe('useStravaActivities', () => {
  let composable: ReturnType<typeof useStravaActivities>
  let mockStravaApi: any
  const mockUseStravaApi = vi.mocked(useStravaApi)

  // Sample data for tests
  const sampleActivities: StravaActivity[] = [
    {
      id: '1',
      name: 'Morning Ride',
      distance: 10000,
      moving_time: 1800,
      elapsed_time: 1900,
      total_elevation_gain: 100,
      type: 'Ride',
      sport_type: 'Ride',
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
    },
    {
      id: '2',
      name: 'Virtual Ride',
      distance: 15000,
      moving_time: 2700,
      elapsed_time: 2700,
      total_elevation_gain: 200,
      type: 'VirtualRide',
      sport_type: 'VirtualRide',
      start_date: '2024-01-02T10:00:00Z',
      start_date_local: '2024-01-02T11:00:00Z',
      timezone: 'Europe/Paris',
      utc_offset: 3600,
      start_latlng: null,
      end_latlng: null,
      achievement_count: 1,
      kudos_count: 3,
      comment_count: 0,
      athlete_count: 1,
      photo_count: 0,
      map: {
        id: 'map2',
        summary_polyline: 'encoded_polyline_2',
        resource_state: 2
      },
      trainer: true,
      commute: false,
      manual: false,
      private: false,
      flagged: false,
      average_speed: 5.56,
      max_speed: 15.0,
      has_heartrate: true,
      average_heartrate: 150,
      max_heartrate: 180,
      heartrate_opt_out: false,
      display_hide_heartrate_option: true,
      elev_high: 200,
      elev_low: 100,
      pr_count: 1,
      total_photo_count: 0,
      has_kudoed: false,
      workout_type: 1
    },
    {
      id: '3',
      name: 'Running',
      distance: 5000,
      moving_time: 1800,
      elapsed_time: 1900,
      total_elevation_gain: 50,
      type: 'Run',
      sport_type: 'Run',
      start_date: '2024-01-03T10:00:00Z',
      start_date_local: '2024-01-03T11:00:00Z',
      timezone: 'Europe/Paris',
      utc_offset: 3600,
      start_latlng: [48.8566, 2.3522],
      end_latlng: [48.8566, 2.3522],
      achievement_count: 0,
      kudos_count: 2,
      comment_count: 1,
      athlete_count: 1,
      photo_count: 0,
      map: {
        id: 'map3',
        summary_polyline: 'encoded_polyline_3',
        resource_state: 2
      },
      trainer: false,
      commute: false,
      manual: false,
      private: false,
      flagged: false,
      average_speed: 2.78,
      max_speed: 5.0,
      has_heartrate: false,
      average_heartrate: null,
      max_heartrate: null,
      heartrate_opt_out: false,
      display_hide_heartrate_option: false,
      elev_high: 50,
      elev_low: 25,
      pr_count: 0,
      total_photo_count: 0,
      has_kudoed: false,
      workout_type: null
    }
  ]

  const sampleGpxData: GPXData = {
    file_id: 'gpx-123',
    track_name: 'Test Track',
    points: [
      {
        latitude: 48.8566,
        longitude: 2.3522,
        elevation: 100,
        time: '2024-01-01T10:00:00Z'
      },
      {
        latitude: 48.8567,
        longitude: 2.3523,
        elevation: 105,
        time: '2024-01-01T10:01:00Z'
      }
    ],
    total_stats: {
      total_points: 2,
      total_distance: 1000,
      total_elevation_gain: 5,
      total_elevation_loss: 0
    },
    bounds: {
      north: 48.8567,
      south: 48.8566,
      east: 2.3523,
      west: 2.3522,
      min_elevation: 100,
      max_elevation: 105
    }
  }

  beforeEach(() => {
    vi.clearAllMocks()

    // Setup mock Strava API
    mockStravaApi = {
      getActivities: vi.fn(),
      getActivityGpx: vi.fn()
    }
    mockUseStravaApi.mockReturnValue(mockStravaApi)

    composable = useStravaActivities()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Initialization', () => {
    it('should initialize with default state', () => {
      expect(composable.activities.value).toEqual([])
      expect(composable.isLoading.value).toBe(false)
      expect(composable.error.value).toBe(null)
      expect(composable.filteredActivities.value).toEqual([])
    })

    it('should use Strava API composable', () => {
      expect(mockUseStravaApi).toHaveBeenCalled()
    })
  })

  describe('filteredActivities computed property', () => {
    it('should filter activities to only include cycling sports', () => {
      // Set up activities with different sport types
      composable.activities.value = sampleActivities

      const filtered = composable.filteredActivities.value

      expect(filtered).toHaveLength(2)
      expect(filtered.map((a) => a.sport_type)).toEqual(['Ride', 'VirtualRide'])
      expect(filtered).not.toContain(expect.objectContaining({ sport_type: 'Run' }))
    })

    it('should include Ride activities', () => {
      composable.activities.value = [sampleActivities[0]] // Ride activity

      expect(composable.filteredActivities.value).toHaveLength(1)
      expect(composable.filteredActivities.value[0].sport_type).toBe('Ride')
    })

    it('should include VirtualRide activities', () => {
      composable.activities.value = [sampleActivities[1]] // VirtualRide activity

      expect(composable.filteredActivities.value).toHaveLength(1)
      expect(composable.filteredActivities.value[0].sport_type).toBe('VirtualRide')
    })

    it('should include EBikeRide activities', () => {
      const ebikeActivity = { ...sampleActivities[0], sport_type: 'EBikeRide' }
      composable.activities.value = [ebikeActivity]

      expect(composable.filteredActivities.value).toHaveLength(1)
      expect(composable.filteredActivities.value[0].sport_type).toBe('EBikeRide')
    })

    it('should exclude non-cycling activities', () => {
      composable.activities.value = [sampleActivities[2]] // Run activity

      expect(composable.filteredActivities.value).toHaveLength(0)
    })

    it('should return empty array when no activities', () => {
      composable.activities.value = []

      expect(composable.filteredActivities.value).toEqual([])
    })
  })

  describe('loadActivities', () => {
    it('should successfully load activities', async () => {
      mockStravaApi.getActivities.mockResolvedValue(sampleActivities.slice(0, 2))

      await composable.loadActivities(1, 30)

      expect(mockStravaApi.getActivities).toHaveBeenCalledWith(1, 30)
      expect(composable.activities.value).toEqual(sampleActivities.slice(0, 2))
      expect(composable.isLoading.value).toBe(false)
      expect(composable.error.value).toBe(null)
      expect(mockConsole.info).toHaveBeenCalledWith('Loaded 2 activities from Strava')
    })

    it('should use default pagination parameters', async () => {
      mockStravaApi.getActivities.mockResolvedValue(sampleActivities)

      await composable.loadActivities()

      expect(mockStravaApi.getActivities).toHaveBeenCalledWith(1, 30)
    })

    it('should set loading state correctly', async () => {
      mockStravaApi.getActivities.mockResolvedValue(sampleActivities)

      const promise = composable.loadActivities()
      expect(composable.isLoading.value).toBe(true)

      await promise
      expect(composable.isLoading.value).toBe(false)
    })

    it('should handle API errors', async () => {
      const error = new Error('API Error')
      mockStravaApi.getActivities.mockRejectedValue(error)

      await expect(composable.loadActivities()).rejects.toThrow('API Error')

      expect(composable.error.value).toBe('API Error')
      expect(composable.isLoading.value).toBe(false)
      expect(mockConsole.error).toHaveBeenCalledWith(
        'Failed to load activities:',
        error
      )
    })

    it('should handle errors without message', async () => {
      const error = new Error()
      mockStravaApi.getActivities.mockRejectedValue(error)

      await expect(composable.loadActivities()).rejects.toThrow()

      expect(composable.error.value).toBe('Failed to load activities')
    })

    it('should clear error before loading', async () => {
      // Set an error first
      composable.error.value = 'Previous error'
      mockStravaApi.getActivities.mockResolvedValue(sampleActivities)

      await composable.loadActivities()

      expect(composable.error.value).toBe(null)
    })
  })

  describe('loadMoreActivities', () => {
    beforeEach(() => {
      // Set up some existing activities and pagination state
      composable.activities.value = sampleActivities.slice(0, 1)
      composable.currentPage.value = 1
      composable.perPage.value = 30
    })

    it('should append new activities to existing ones and update pagination', async () => {
      const moreActivities = sampleActivities.slice(1, 3)
      mockStravaApi.getActivities.mockResolvedValue(moreActivities)

      await composable.loadMoreActivities()

      expect(mockStravaApi.getActivities).toHaveBeenCalledWith(2, 30)
      expect(composable.activities.value).toHaveLength(3)
      expect(composable.activities.value).toEqual([
        ...sampleActivities.slice(0, 1),
        ...moreActivities
      ])
      expect(composable.currentPage.value).toBe(2)
      expect(mockConsole.info).toHaveBeenCalledWith('Loaded 2 more activities (page 2)')
    })

    it('should set hasMore to false when fewer activities than perPage are returned', async () => {
      const moreActivities = sampleActivities.slice(1, 2) // Only 1 activity, less than perPage (30)
      mockStravaApi.getActivities.mockResolvedValue(moreActivities)

      await composable.loadMoreActivities()

      expect(composable.hasMore.value).toBe(false)
    })

    it('should set hasMore to true when full page of activities is returned', async () => {
      // Create a full page of activities (30 items)
      const fullPageActivities = Array.from({ length: 30 }, (_, i) => ({
        ...sampleActivities[0],
        id: `activity-${i + 2}`,
        name: `Activity ${i + 2}`
      }))
      mockStravaApi.getActivities.mockResolvedValue(fullPageActivities)

      await composable.loadMoreActivities()

      expect(composable.hasMore.value).toBe(true)
    })

    it('should handle API errors', async () => {
      const error = new Error('Network error')
      mockStravaApi.getActivities.mockRejectedValue(error)

      await expect(composable.loadMoreActivities()).rejects.toThrow('Network error')

      expect(composable.error.value).toBe('Network error')
      expect(mockConsole.error).toHaveBeenCalledWith(
        'Failed to load more activities:',
        error
      )
    })

    it('should not affect existing activities on error', async () => {
      const initialActivities = composable.activities.value
      const initialPage = composable.currentPage.value
      mockStravaApi.getActivities.mockRejectedValue(new Error('API Error'))

      await expect(composable.loadMoreActivities()).rejects.toThrow()

      expect(composable.activities.value).toEqual(initialActivities)
      expect(composable.currentPage.value).toBe(initialPage)
    })
  })

  describe('refreshActivities', () => {
    beforeEach(() => {
      // Set up some existing activities, error, and pagination state
      composable.activities.value = sampleActivities
      composable.error.value = 'Some error'
      composable.currentPage.value = 3
      composable.hasMore.value = true
    })

    it('should clear activities, reset pagination, and reload', async () => {
      mockStravaApi.getActivities.mockResolvedValue(sampleActivities.slice(0, 2))

      await composable.refreshActivities()

      expect(composable.activities.value).toEqual(sampleActivities.slice(0, 2))
      expect(mockStravaApi.getActivities).toHaveBeenCalledWith(1, 30)
      expect(composable.currentPage.value).toBe(1)
      expect(composable.hasMore.value).toBe(false)
    })

    it('should handle errors during refresh', async () => {
      const error = new Error('Refresh failed')
      mockStravaApi.getActivities.mockRejectedValue(error)

      await expect(composable.refreshActivities()).rejects.toThrow('Refresh failed')

      expect(composable.activities.value).toEqual([]) // Should still be cleared
      expect(composable.currentPage.value).toBe(1)
      expect(composable.hasMore.value).toBe(false)
      expect(composable.error.value).toBe('Refresh failed')
    })
  })

  describe('clearActivities', () => {
    beforeEach(() => {
      composable.activities.value = sampleActivities
      composable.error.value = 'Some error'
      composable.currentPage.value = 3
      composable.hasMore.value = true
    })

    it('should clear activities, error, and reset pagination', () => {
      composable.clearActivities()

      expect(composable.activities.value).toEqual([])
      expect(composable.error.value).toBe(null)
      expect(composable.currentPage.value).toBe(1)
      expect(composable.hasMore.value).toBe(false)
    })
  })

  describe('getActivityGpx', () => {
    it('should successfully get GPX data', async () => {
      mockStravaApi.getActivityGpx.mockResolvedValue(sampleGpxData)

      const result = await composable.getActivityGpx('activity-123')

      expect(mockStravaApi.getActivityGpx).toHaveBeenCalledWith('activity-123')
      expect(result).toEqual(sampleGpxData)
      expect(composable.isLoading.value).toBe(false)
      expect(composable.error.value).toBe(null)
      expect(mockConsole.info).toHaveBeenCalledWith(
        'GPX data retrieved for activity activity-123'
      )
    })

    it('should set loading state correctly', async () => {
      mockStravaApi.getActivityGpx.mockResolvedValue(sampleGpxData)

      const promise = composable.getActivityGpx('activity-123')
      expect(composable.isLoading.value).toBe(true)

      await promise
      expect(composable.isLoading.value).toBe(false)
    })

    it('should handle API errors and return null', async () => {
      const error = new Error('GPX not found')
      mockStravaApi.getActivityGpx.mockRejectedValue(error)

      const result = await composable.getActivityGpx('activity-123')

      expect(result).toBe(null)
      expect(composable.error.value).toBe('GPX not found')
      expect(composable.isLoading.value).toBe(false)
      expect(mockConsole.error).toHaveBeenCalledWith(
        'Failed to get GPX for activity activity-123:',
        error
      )
    })

    it('should handle errors without message', async () => {
      const error = new Error()
      mockStravaApi.getActivityGpx.mockRejectedValue(error)

      const result = await composable.getActivityGpx('activity-123')

      expect(result).toBe(null)
      expect(composable.error.value).toBe('Failed to get activity GPX')
    })

    it('should clear error before loading', async () => {
      // Set an error first
      composable.error.value = 'Previous error'
      mockStravaApi.getActivityGpx.mockResolvedValue(sampleGpxData)

      await composable.getActivityGpx('activity-123')

      expect(composable.error.value).toBe(null)
    })
  })

  describe('Error handling and state management', () => {
    it('should handle concurrent loadActivities calls', async () => {
      mockStravaApi.getActivities
        .mockResolvedValueOnce(sampleActivities.slice(0, 1))
        .mockResolvedValueOnce(sampleActivities.slice(1, 2))

      const promises = [composable.loadActivities(1), composable.loadActivities(2)]

      await Promise.all(promises)

      expect(mockStravaApi.getActivities).toHaveBeenCalledTimes(2)
      expect(composable.isLoading.value).toBe(false)
    })

    it('should handle concurrent getActivityGpx calls', async () => {
      mockStravaApi.getActivityGpx
        .mockResolvedValueOnce(sampleGpxData)
        .mockResolvedValueOnce({ ...sampleGpxData, file_id: 'gpx-456' })

      const promises = [
        composable.getActivityGpx('activity-1'),
        composable.getActivityGpx('activity-2')
      ]

      const results = await Promise.all(promises)

      expect(results).toHaveLength(2)
      expect(results[0]).toEqual(sampleGpxData)
      expect(results[1]).toEqual({ ...sampleGpxData, file_id: 'gpx-456' })
    })

    it('should preserve state between different operations', async () => {
      // Load activities first
      mockStravaApi.getActivities.mockResolvedValue(sampleActivities.slice(0, 2))
      await composable.loadActivities()

      expect(composable.activities.value).toHaveLength(2)

      // Then load more activities
      mockStravaApi.getActivities.mockResolvedValue(sampleActivities.slice(2, 3))
      await composable.loadMoreActivities()

      expect(composable.activities.value).toHaveLength(3)
      expect(composable.filteredActivities.value).toHaveLength(2) // Only cycling activities
    })

    it('should handle mixed success and error scenarios', async () => {
      // First call succeeds
      mockStravaApi.getActivities.mockResolvedValueOnce(sampleActivities.slice(0, 1))
      await composable.loadActivities()

      expect(composable.activities.value).toHaveLength(1)
      expect(composable.error.value).toBe(null)

      // Second call fails
      mockStravaApi.getActivities.mockRejectedValueOnce(new Error('Network error'))
      await expect(composable.loadMoreActivities()).rejects.toThrow()

      expect(composable.activities.value).toHaveLength(1) // Should still have the first activity
      expect(composable.error.value).toBe('Network error')
    })
  })

  describe('Integration with Strava API', () => {
    it('should properly integrate with useStravaApi', () => {
      expect(mockUseStravaApi).toHaveBeenCalledOnce()
      expect(composable).toHaveProperty('activities')
      expect(composable).toHaveProperty('isLoading')
      expect(composable).toHaveProperty('error')
      expect(composable).toHaveProperty('hasMore')
      expect(composable).toHaveProperty('currentPage')
      expect(composable).toHaveProperty('perPage')
      expect(composable).toHaveProperty('filteredActivities')
      expect(composable).toHaveProperty('loadActivities')
      expect(composable).toHaveProperty('loadMoreActivities')
      expect(composable).toHaveProperty('refreshActivities')
      expect(composable).toHaveProperty('clearActivities')
      expect(composable).toHaveProperty('getActivityGpx')
    })

    it('should pass through API parameters correctly', async () => {
      mockStravaApi.getActivities.mockResolvedValue([])

      await composable.loadActivities(3, 50)

      expect(mockStravaApi.getActivities).toHaveBeenCalledWith(3, 50)
    })

    it('should handle API authentication errors', async () => {
      const authError = new Error('Authentication failed')
      mockStravaApi.getActivities.mockRejectedValue(authError)

      await expect(composable.loadActivities()).rejects.toThrow('Authentication failed')

      expect(composable.error.value).toBe('Authentication failed')
    })
  })
})
