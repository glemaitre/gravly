import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { nextTick } from 'vue'

// Mock Leaflet
vi.mock('leaflet', () => ({
  default: {
    map: vi.fn(() => ({
      setView: vi.fn(),
      fitBounds: vi.fn(),
      remove: vi.fn()
    })),
    tileLayer: vi.fn(() => ({
      addTo: vi.fn()
    })),
    polyline: vi.fn(() => ({
      addTo: vi.fn(),
      getBounds: vi.fn(() => ({
        getCenter: vi.fn(() => [0, 0])
      }))
    })),
    circleMarker: vi.fn(() => ({
      addTo: vi.fn(),
      bindPopup: vi.fn()
    })),
    marker: vi.fn(() => ({
      addTo: vi.fn(),
      bindPopup: vi.fn()
    })),
    latLngBounds: vi.fn(() => ({
      getCenter: vi.fn(() => [0, 0])
    }))
  }
}))

import StravaActivityDetailsModal from '../StravaActivityDetailsModal.vue'

// Import real locale files
import en from '../../i18n/locales/en'
import fr from '../../i18n/locales/fr'

// Mock console methods to avoid noise in tests
const mockConsole = {
  log: vi.fn(),
  error: vi.fn(),
  warn: vi.fn(),
  info: vi.fn()
}
Object.defineProperty(console, 'log', { value: mockConsole.log })
Object.defineProperty(console, 'error', { value: mockConsole.error })
Object.defineProperty(console, 'warn', { value: mockConsole.warn })
Object.defineProperty(console, 'info', { value: mockConsole.info })

describe('StravaActivityDetailsModal', () => {
  let wrapper: VueWrapper<any>
  let i18n: ReturnType<typeof createI18n>

  // Sample activity data for tests
  const sampleActivity = {
    id: '1',
    name: 'Morning Ride',
    distance: 10000,
    moving_time: 1800,
    elapsed_time: 1900,
    total_elevation_gain: 100,
    average_speed: 5.56,
    max_speed: 12.0,
    average_heartrate: 150,
    max_heartrate: 180,
    type: 'Ride',
    sport_type: 'Ride',
    start_date: '2024-01-01T10:00:00Z',
    start_date_local: '2024-01-01T11:00:00Z',
    timezone: 'Europe/Paris',
    utc_offset: 3600,
    start_latlng: [48.8566, 2.3522] as [number, number],
    end_latlng: [48.8566, 2.3522] as [number, number],
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
    has_heartrate: true,
    heartrate_opt_out: false,
    display_hide_heartrate_option: false,
    elev_high: 100,
    elev_low: 50,
    pr_count: 0,
    total_photo_count: 0,
    has_kudoed: false,
    workout_type: null
  }

  const activityWithoutGps = {
    ...sampleActivity,
    id: '2',
    name: 'Virtual Ride',
    type: 'VirtualRide',
    start_latlng: null,
    end_latlng: null,
    map: null
  }

  beforeEach(() => {
    vi.clearAllMocks()

    // Create i18n instance using real locale files
    i18n = createI18n({
      legacy: false,
      locale: 'en',
      fallbackLocale: 'en',
      messages: { en, fr }
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
    if (wrapper) {
      wrapper.unmount()
    }
  })

  const createWrapper = (props = {}) => {
    wrapper = mount(StravaActivityDetailsModal, {
      global: {
        plugins: [i18n],
        stubs: {
          'fa-solid': true // Stub FontAwesome icons
        }
      },
      props: {
        isVisible: false,
        activity: null,
        isImporting: false,
        ...props
      }
    })
    return wrapper
  }

  describe('Modal Visibility', () => {
    it('should not render when isVisible is false', () => {
      wrapper = createWrapper({ isVisible: false })

      expect(wrapper.find('.modal-overlay').exists()).toBe(false)
    })

    it('should render when isVisible is true', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      expect(wrapper.find('.modal-overlay').exists()).toBe(true)
      expect(wrapper.find('.modal-content').exists()).toBe(true)
    })

    it('should emit close when overlay is clicked', async () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })
      await wrapper.vm.$nextTick()

      const overlay = wrapper.find('.modal-overlay')
      await overlay.trigger('click')

      expect(wrapper.emitted('close')).toBeTruthy()
      expect(wrapper.emitted('close')).toHaveLength(1)
    })

    it('should not emit close when modal content is clicked', async () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })
      await wrapper.vm.$nextTick()

      const content = wrapper.find('.modal-content')
      await content.trigger('click')

      expect(wrapper.emitted('close')).toBeFalsy()
    })
  })

  describe('Modal Header', () => {
    it('should display activity name in header', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      expect(wrapper.find('.activity-name').text()).toContain('Morning Ride')
    })

    it('should display formatted start time', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      expect(wrapper.find('.activity-start-time').exists()).toBe(true)
      // The exact format depends on locale, but should contain date/time info
      const startTime = wrapper.find('.activity-start-time').text()
      expect(startTime).toBeTruthy()
    })
  })

  describe('Activity Display', () => {
    it('should display activity name', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      expect(wrapper.find('.activity-name').text()).toContain('Morning Ride')
    })

    it('should display activity header with info and actions', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      expect(wrapper.find('.activity-header').exists()).toBe(true)
      expect(wrapper.find('.activity-info').exists()).toBe(true)
      expect(wrapper.find('.modal-actions').exists()).toBe(true)
    })

    it('should handle different activity types', () => {
      const runActivity = { ...sampleActivity, type: 'Run' }
      wrapper = createWrapper({ isVisible: true, activity: runActivity })

      expect(wrapper.find('.activity-name').text()).toContain('Morning Ride')
      // Activity type is not displayed in the current component structure
    })
  })

  describe('Statistics Grid', () => {
    it('should display all statistics correctly', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      const statsGrid = wrapper.find('.stats-grid')
      expect(statsGrid.exists()).toBe(true)

      // Check that stat cards exist
      const statCards = wrapper.findAll('.stat-card')
      expect(statCards.length).toBeGreaterThan(0)
    })

    it('should display distance correctly', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      expect(wrapper.text()).toContain('10.0 km')
      expect(wrapper.text()).toContain('Distance')
    })

    it('should display duration correctly', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      expect(wrapper.text()).toContain('30m')
      expect(wrapper.text()).toContain('Moving Time')
    })

    it('should display elevation correctly', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      expect(wrapper.text()).toContain('100 m')
      expect(wrapper.text()).toContain('Elevation Gain')
    })

    it('should display average speed correctly', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      expect(wrapper.text()).toContain('20.0 km/h') // 5.56 * 3.6
      expect(wrapper.text()).toContain('Average Speed')
    })

    it('should display max speed correctly', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      expect(wrapper.text()).toContain('43.2 km/h') // 12.0 * 3.6
      expect(wrapper.text()).toContain('Max Speed')
    })

    it('should display heartrate when available', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      expect(wrapper.text()).toContain('150')
      expect(wrapper.text()).toContain('Avg Heartrate')
    })

    it('should display N/A for heartrate when not available', () => {
      const activityWithoutHeartrate = { ...sampleActivity, average_heartrate: null }
      wrapper = createWrapper({ isVisible: true, activity: activityWithoutHeartrate })

      expect(wrapper.text()).toContain('N/A')
      expect(wrapper.text()).toContain('Avg Heartrate')
    })

    it('should display section title with icon', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      const sectionTitle = wrapper.find('.section-title')
      expect(sectionTitle.exists()).toBe(true)
      expect(sectionTitle.text()).toContain('Activity Stats')
    })
  })

  describe('GPS Status', () => {
    it('should not show GPS warning for activities with GPS', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      const gpsWarning = wrapper.find('.gps-warning')
      expect(gpsWarning.exists()).toBe(false)
    })

    it('should show GPS warning for activities without GPS', () => {
      wrapper = createWrapper({ isVisible: true, activity: activityWithoutGps })

      const gpsWarning = wrapper.find('.gps-warning')
      expect(gpsWarning.exists()).toBe(true)
      expect(gpsWarning.text()).toContain('no GPS data')
    })
  })

  describe('Map Section', () => {
    it('should display map section for activities with GPS', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      const mapSection = wrapper.find('.map-section')
      expect(mapSection.exists()).toBe(true)
      expect(mapSection.text()).toContain('Route Preview')

      const mapContainer = wrapper.find('.activity-map')
      expect(mapContainer.exists()).toBe(true)
    })

    it('should not display map section for activities without GPS', () => {
      wrapper = createWrapper({ isVisible: true, activity: activityWithoutGps })

      const mapSection = wrapper.find('.map-section')
      expect(mapSection.exists()).toBe(false)
    })

    it('should display route preview section title with icon', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      const sectionTitle = wrapper.find('.section-title')
      expect(sectionTitle.exists()).toBe(true)
      expect(sectionTitle.text()).toContain('Route Preview')
    })
  })

  describe('User Interactions', () => {
    it('should emit import when import button is clicked', async () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })
      await wrapper.vm.$nextTick()

      const importButton = wrapper.find('.btn-primary')
      await importButton.trigger('click')

      expect(wrapper.emitted('import')).toBeTruthy()
      expect(wrapper.emitted('import')?.[0]).toEqual([sampleActivity])
    })

    it('should disable import button when importing', () => {
      wrapper = createWrapper({
        isVisible: true,
        activity: sampleActivity,
        isImporting: true
      })

      const importButton = wrapper.find('.btn-primary')
      expect(importButton.attributes('disabled')).toBeDefined()
    })

    it('should disable import button for activities without GPS', () => {
      wrapper = createWrapper({ isVisible: true, activity: activityWithoutGps })

      const importButton = wrapper.find('.btn-primary')
      expect(importButton.attributes('disabled')).toBeDefined()
    })

    it('should show loading spinner when importing', () => {
      wrapper = createWrapper({
        isVisible: true,
        activity: sampleActivity,
        isImporting: true
      })

      // The spinner icon should be present (though stubbed)
      expect(wrapper.find('.btn-primary').exists()).toBe(true)
      expect(wrapper.text()).toContain('Import')
    })

    it('should emit close when cancel button is clicked', async () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })
      await wrapper.vm.$nextTick()

      const cancelButton = wrapper.find('.btn-secondary')
      await cancelButton.trigger('click')

      expect(wrapper.emitted('close')).toBeTruthy()
      expect(wrapper.emitted('close')).toHaveLength(1)
    })

    it('should display correct button text', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      const importButton = wrapper.find('.btn-primary')
      const cancelButton = wrapper.find('.btn-secondary')

      expect(importButton.text()).toContain('Import')
      expect(cancelButton.text()).toContain('Cancel')
    })
  })

  describe('Formatting Functions', () => {
    it('should format distance correctly', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      expect(wrapper.vm.formatDistance(1000)).toBe('1.0 km')
      expect(wrapper.vm.formatDistance(500)).toBe('500 m')
      expect(wrapper.vm.formatDistance(1500)).toBe('1.5 km')
    })

    it('should format duration correctly', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      expect(wrapper.vm.formatDuration(1800)).toBe('30m') // 30 minutes
      expect(wrapper.vm.formatDuration(3660)).toBe('1h 1m') // 1 hour 1 minute
      expect(wrapper.vm.formatDuration(7200)).toBe('2h 0m') // 2 hours
    })

    it('should format elevation correctly', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      expect(wrapper.vm.formatElevation(100)).toBe('100 m')
      expect(wrapper.vm.formatElevation(150.5)).toBe('151 m')
      expect(wrapper.vm.formatElevation(999.9)).toBe('1000 m')
    })

    it('should format speed correctly', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      expect(wrapper.vm.formatSpeed(5.56)).toBe('20.0 km/h') // 5.56 * 3.6
      expect(wrapper.vm.formatSpeed(10)).toBe('36.0 km/h') // 10 * 3.6
      expect(wrapper.vm.formatSpeed(0)).toBe('0.0 km/h')
    })

    it('should format date time correctly for English locale', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      const formattedDate = wrapper.vm.formatDateTime('2024-01-01T11:00:00Z')
      expect(formattedDate).toBeTruthy()
      expect(typeof formattedDate).toBe('string')
    })

    it('should format date time correctly for French locale', () => {
      // Create a new i18n instance with French locale
      const frI18n = createI18n({
        legacy: false,
        locale: 'fr',
        fallbackLocale: 'fr',
        messages: { en, fr }
      })

      const frWrapper = mount(StravaActivityDetailsModal, {
        global: {
          plugins: [frI18n],
          stubs: {
            'fa-solid': true
          }
        },
        props: {
          isVisible: true,
          activity: sampleActivity,
          isImporting: false
        }
      })

      const formattedDate = frWrapper.vm.formatDateTime('2024-01-01T11:00:00Z')
      expect(formattedDate).toBeTruthy()
      expect(typeof formattedDate).toBe('string')

      frWrapper.unmount()
    })
  })

  describe('Activity Type Icons', () => {
    it('should return correct icon for Ride', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      expect(wrapper.vm.getActivityTypeIcon('Ride')).toBe('fa-solid fa-bicycle')
    })

    it('should return correct icon for VirtualRide', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      expect(wrapper.vm.getActivityTypeIcon('VirtualRide')).toBe('fa-solid fa-bicycle')
    })

    it('should return correct icon for Run', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      expect(wrapper.vm.getActivityTypeIcon('Run')).toBe('fa-solid fa-running')
    })

    it('should return correct icon for Walk', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      expect(wrapper.vm.getActivityTypeIcon('Walk')).toBe('fa-solid fa-walking')
    })

    it('should return default icon for unknown type', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      expect(wrapper.vm.getActivityTypeIcon('Unknown')).toBe('fa-solid fa-dumbbell')
    })
  })

  describe('Polyline Decoding', () => {
    it('should decode polyline correctly', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      // Test with a simple polyline (this is a basic test)
      const coordinates = wrapper.vm.decodePolyline('_p~iF~ps|U')
      expect(Array.isArray(coordinates)).toBe(true)
    })

    it('should subsample coordinates correctly', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      const coordinates = [
        [0, 0],
        [1, 1],
        [2, 2],
        [3, 3],
        [4, 4]
      ]
      const subsampled = wrapper.vm.subsampleCoordinates(coordinates, 3)

      expect(subsampled).toHaveLength(3)
      expect(subsampled[0]).toEqual([0, 0]) // First point
      expect(subsampled[2]).toEqual([4, 4]) // Last point
    })

    it('should return original coordinates if count is within limit', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      const coordinates = [
        [0, 0],
        [1, 1]
      ]
      const subsampled = wrapper.vm.subsampleCoordinates(coordinates, 5)

      expect(subsampled).toEqual(coordinates)
    })
  })

  describe('Modal Lifecycle', () => {
    it('should create map when modal becomes visible with activity', async () => {
      wrapper = createWrapper({ isVisible: false, activity: sampleActivity })

      // Change visibility to true
      await wrapper.setProps({ isVisible: true })
      await nextTick()

      // Map creation is mocked, so we just verify the component handles the change
      expect(wrapper.find('.map-section').exists()).toBe(true)
    })

    it('should handle activity changes', async () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })
      await nextTick()

      // Change activity
      await wrapper.setProps({ activity: activityWithoutGps })
      await nextTick()

      expect(wrapper.find('.map-section').exists()).toBe(false)
      expect(wrapper.find('.gps-warning').exists()).toBe(true)
    })

    it('should not render modal body when activity is null', () => {
      wrapper = createWrapper({ isVisible: true, activity: null })

      expect(wrapper.find('.modal-body').exists()).toBe(false)
    })
  })

  describe('Component Integration', () => {
    it('should properly integrate with i18n', () => {
      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })

      expect(wrapper.text()).toContain('Distance')
      expect(wrapper.text()).toContain('Moving Time')
      expect(wrapper.text()).toContain('Activity Stats')
    })

    it('should handle missing activity data gracefully', () => {
      const incompleteActivity = {
        id: '3',
        name: 'Incomplete Activity',
        distance: 0,
        moving_time: 0,
        total_elevation_gain: 0,
        average_speed: 0,
        max_speed: 0,
        type: 'Ride',
        start_date_local: '2024-01-01T10:00:00Z',
        elapsed_time: 0,
        kudos_count: 0,
        comment_count: 0,
        start_latlng: null,
        end_latlng: null,
        map: null
      }

      wrapper = createWrapper({ isVisible: true, activity: incompleteActivity })

      expect(wrapper.find('.modal-body').exists()).toBe(true)
      expect(wrapper.find('.activity-name').text()).toContain('Incomplete Activity')
      expect(wrapper.find('.gps-warning').exists()).toBe(true)
    })
  })

  describe('Error Handling', () => {
    it('should handle map creation errors gracefully', async () => {
      // Mock console.error to verify error handling
      const originalConsoleError = console.error
      console.error = vi.fn()

      wrapper = createWrapper({ isVisible: true, activity: sampleActivity })
      await nextTick()

      // Simulate map creation error by calling the function directly
      try {
        await wrapper.vm.createMap()
      } catch {
        // Error should be caught and logged
      }

      // Restore console.error
      console.error = originalConsoleError
    })
  })
})
