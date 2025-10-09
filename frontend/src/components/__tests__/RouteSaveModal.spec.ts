import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import RouteSaveModal from '../RouteSaveModal.vue'
import RouteInfoCard from '../RouteInfoCard.vue'
import en from '../../i18n/locales/en'
import fr from '../../i18n/locales/fr'

// Create i18n instance for tests
const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en,
    fr
  }
})

// Mock fetch globally
global.fetch = vi.fn()

// Helper function to create wrapper with default config
function createWrapper(props: any, options: any = {}) {
  return mount(RouteSaveModal, {
    props,
    global: {
      plugins: [i18n],
      components: {
        RouteInfoCard
      },
      ...options.global
    },
    ...options
  })
}

describe('RouteSaveModal', () => {
  let mockRouteTrackPoints: Array<{
    lat: number
    lng: number
    elevation: number
    distance: number
  }>

  let mockRouteFeatures: {
    difficulty_level: number
    surface_types: string[]
    tire_dry: string
    tire_wet: string
  }

  beforeEach(() => {
    mockRouteFeatures = {
      difficulty_level: 3,
      surface_types: ['broken-paved-road', 'forest-trail'],
      tire_dry: 'semi-slick',
      tire_wet: 'knobs'
    }

    mockRouteTrackPoints = [
      { lat: 45.5, lng: -73.5, elevation: 100, distance: 0 },
      { lat: 45.51, lng: -73.51, elevation: 120, distance: 1000 },
      { lat: 45.52, lng: -73.52, elevation: 150, distance: 2000 }
    ]

    // Reset fetch mock
    vi.resetAllMocks()
  })

  describe('Component Rendering', () => {
    it('should render save button', () => {
      const wrapper = createWrapper({
        routeFeatures: mockRouteFeatures,
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints
      })

      expect(wrapper.find('.save-route-btn').exists()).toBe(true)
    })

    it('should render RouteInfoCard component', () => {
      const wrapper = createWrapper({
        routeFeatures: mockRouteFeatures,
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints,
        show: true
      })

      expect(wrapper.findComponent(RouteInfoCard).exists()).toBe(true)
    })
  })

  describe('Button State', () => {
    it('should disable save button when no segments selected', () => {
      const wrapper = createWrapper({
        routeFeatures: null,
        routeDistance: 0,
        elevationStats: {
          totalGain: 0,
          totalLoss: 0,
          maxElevation: 0,
          minElevation: 0
        },
        routeTrackPoints: []
      })

      const button = wrapper.find('.save-route-btn')
      expect(button.classes()).toContain('disabled')
      expect(button.attributes('disabled')).toBeDefined()
    })

    it('should enable save button when segments are selected', () => {
      const wrapper = createWrapper({
        routeFeatures: mockRouteFeatures,
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints
      })

      const button = wrapper.find('.save-route-btn')
      expect(button.classes()).not.toContain('disabled')
      expect(button.attributes('disabled')).toBeUndefined()
    })

    it('should show disabled title when no segments selected', () => {
      const wrapper = createWrapper({
        routeFeatures: null,
        routeDistance: 0,
        elevationStats: {
          totalGain: 0,
          totalLoss: 0,
          maxElevation: 0,
          minElevation: 0
        },
        routeTrackPoints: []
      })

      const button = wrapper.find('.save-route-btn')
      expect(button.attributes('title')).toBeTruthy()
    })
  })

  describe('Modal Visibility with show prop', () => {
    it('should show modal when show prop is true', async () => {
      const wrapper = createWrapper({
        routeFeatures: mockRouteFeatures,
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints,
        show: true
      })

      await wrapper.vm.$nextTick()
      expect(wrapper.find('.modal-overlay').exists()).toBe(true)
      expect(wrapper.find('.modal-content').exists()).toBe(true)
      expect(wrapper.find('#route-name').exists()).toBe(true)
      expect(wrapper.find('#route-comments').exists()).toBe(true)
    })

    it('should hide modal when show prop is false', async () => {
      const wrapper = createWrapper({
        routeFeatures: mockRouteFeatures,
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints,
        show: false
      })

      await wrapper.vm.$nextTick()
      expect(wrapper.find('.modal-overlay').exists()).toBe(false)
    })
  })

  describe('Modal Form Elements', () => {
    it('should have route name input with maxlength when modal is shown', async () => {
      const wrapper = createWrapper({
        routeFeatures: mockRouteFeatures,
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints,
        show: true
      })

      await wrapper.vm.$nextTick()

      const nameInput = wrapper.find('#route-name')
      expect(nameInput.exists()).toBe(true)
      expect(nameInput.attributes('maxlength')).toBe('100')
    })

    it('should have comments textarea with maxlength when modal is shown', async () => {
      const wrapper = createWrapper({
        routeFeatures: mockRouteFeatures,
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints,
        show: true
      })

      await wrapper.vm.$nextTick()

      const commentsTextarea = wrapper.find('#route-comments')
      expect(commentsTextarea.exists()).toBe(true)
      expect(commentsTextarea.attributes('maxlength')).toBe('500')
    })
  })

  describe('Route Statistics Calculation', () => {
    it('should use route features from props (difficulty from backend)', async () => {
      const wrapper = createWrapper({
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints,
        routeFeatures: {
          difficulty_level: 3,
          surface_types: ['broken-paved-road'],
          tire_dry: 'semi-slick',
          tire_wet: 'knobs'
        }
      })

      // Check computed stats use the provided route features
      const stats = (wrapper.vm as any).computedStats
      expect(stats.difficulty).toBe(3)
    })

    it('should use difficulty from route features', async () => {
      const wrapper = createWrapper({
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints,
        routeFeatures: {
          difficulty_level: 4,
          surface_types: ['broken-paved-road', 'forest-trail'],
          tire_dry: 'knobs',
          tire_wet: 'knobs'
        }
      })

      // Check computed stats
      const stats = (wrapper.vm as any).computedStats
      expect(stats.difficulty).toBe(4)
    })

    it('should handle different difficulty levels from backend', async () => {
      const wrapper = createWrapper({
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints,
        routeFeatures: {
          difficulty_level: 3,
          surface_types: ['broken-paved-road'],
          tire_dry: 'slick',
          tire_wet: 'semi-slick'
        }
      })

      // Check computed stats
      const stats = (wrapper.vm as any).computedStats
      expect(stats.difficulty).toBe(3)
    })

    it('should use surface types from route features', async () => {
      const wrapper = createWrapper({
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints,
        routeFeatures: {
          difficulty_level: 3,
          surface_types: ['broken-paved-road', 'forest-trail'],
          tire_dry: 'semi-slick',
          tire_wet: 'knobs'
        }
      })

      const stats = (wrapper.vm as any).computedStats
      expect(stats.surfaceTypes).toContain('broken-paved-road')
      expect(stats.surfaceTypes).toContain('forest-trail')
    })

    it('should use tire recommendations from route features (dry)', async () => {
      const wrapper = createWrapper({
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints,
        routeFeatures: {
          difficulty_level: 3,
          surface_types: ['broken-paved-road'],
          tire_dry: 'knobs',
          tire_wet: 'semi-slick'
        }
      })

      const stats = (wrapper.vm as any).computedStats
      // Should use the tire recommendation from backend
      expect(stats.tireDry).toBe('knobs')
    })

    it('should use tire recommendations from route features (wet)', async () => {
      const wrapper = createWrapper({
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints,
        routeFeatures: {
          difficulty_level: 3,
          surface_types: ['broken-paved-road'],
          tire_dry: 'slick',
          tire_wet: 'knobs'
        }
      })

      const stats = (wrapper.vm as any).computedStats
      // Should use the tire recommendation from backend
      expect(stats.tireWet).toBe('knobs')
    })

    it('should use default stats for waypoint routes (no route features)', () => {
      const wrapper = createWrapper({
        routeDistance: 15.5,
        elevationStats: {
          totalGain: 200,
          totalLoss: 150,
          maxElevation: 300,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints,
        routeFeatures: null // No features for waypoint route
      })

      const stats = (wrapper.vm as any).computedStats
      expect(stats.difficulty).toBe(0)
      expect(stats.surfaceTypes).toEqual([])
      expect(stats.tireDry).toBe('slick')
      expect(stats.tireWet).toBe('slick')
    })
  })

  describe('Form Validation', () => {
    it('should disable save button in modal when route name is empty', async () => {
      const wrapper = createWrapper({
        routeFeatures: mockRouteFeatures,
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints,
        show: true
      })

      await wrapper.vm.$nextTick()

      const saveButton = wrapper.find('.btn-primary')
      expect(saveButton.exists()).toBe(true)
      expect(saveButton.attributes('disabled')).toBeDefined()
    })

    it('should enable save button when route name is filled', async () => {
      const wrapper = createWrapper({
        routeFeatures: mockRouteFeatures,
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints,
        show: true
      })

      await wrapper.vm.$nextTick()

      const nameInput = wrapper.find('#route-name')
      await nameInput.setValue('Test Route')

      const saveButton = wrapper.find('.btn-primary')
      expect(saveButton.attributes('disabled')).toBeUndefined()
    })
  })

  describe('Save Route API Call', () => {
    it('should call API with correct data when saving route', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ id: 123 })
      })
      global.fetch = mockFetch

      const wrapper = createWrapper({
        routeFeatures: mockRouteFeatures,
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints,
        show: true
      })

      await wrapper.vm.$nextTick()

      await wrapper.find('#route-name').setValue('Test Route')
      await wrapper.find('#route-comments').setValue('Test comments')

      await wrapper.find('.btn-primary').trigger('click')
      await flushPromises()

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/routes/',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        })
      )

      const callArgs = mockFetch.mock.calls[0][1]
      const bodyData = JSON.parse(callArgs.body)
      expect(bodyData.name).toBe('Test Route')
      expect(bodyData.comments).toBe('Test comments')
      expect(bodyData.track_type).toBe('route')
    })

    it('should emit route-saved event on successful save', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ id: 123 })
      })
      global.fetch = mockFetch

      const wrapper = createWrapper({
        routeFeatures: mockRouteFeatures,
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints,
        show: true
      })

      await wrapper.vm.$nextTick()
      await wrapper.find('#route-name').setValue('Test Route')
      await wrapper.find('.btn-primary').trigger('click')
      await flushPromises()

      expect(wrapper.emitted('route-saved')).toBeTruthy()
      expect(wrapper.emitted('route-saved')![0]).toEqual([123])
    })

    it('should show success message after successful save', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ id: 123 })
      })
      global.fetch = mockFetch

      const wrapper = createWrapper({
        routeFeatures: mockRouteFeatures,
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints,
        show: true
      })

      await wrapper.vm.$nextTick()
      await wrapper.find('#route-name').setValue('Test Route')
      await wrapper.find('.btn-primary').trigger('click')
      await flushPromises()

      expect(wrapper.find('.save-success-message').exists()).toBe(true)
    })

    it('should show error message on failed save', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: false,
        text: async () => 'Error saving route'
      })
      global.fetch = mockFetch

      const wrapper = createWrapper({
        routeFeatures: mockRouteFeatures,
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints,
        show: true
      })

      await wrapper.vm.$nextTick()
      await wrapper.find('#route-name').setValue('Test Route')
      await wrapper.find('.btn-primary').trigger('click')
      await flushPromises()

      expect(wrapper.find('.save-error-message').exists()).toBe(true)
    })

    it('should include route features in API call', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ id: 123 })
      })
      global.fetch = mockFetch

      const routeFeatures = {
        difficulty_level: 3,
        surface_types: ['broken-paved-road', 'forest-trail'],
        tire_dry: 'semi-slick',
        tire_wet: 'knobs'
      }

      const wrapper = createWrapper({
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints,
        routeFeatures,
        show: true
      })

      await wrapper.vm.$nextTick()
      await wrapper.find('#route-name').setValue('Test Route')
      await wrapper.find('.btn-primary').trigger('click')
      await flushPromises()

      const callArgs = mockFetch.mock.calls[0][1]
      const bodyData = JSON.parse(callArgs.body)
      expect(bodyData.route_features).toBeDefined()
      expect(bodyData.route_features.difficulty_level).toBe(3)
      expect(bodyData.route_features.tire_dry).toBe('semi-slick')
      expect(bodyData.route_features.tire_wet).toBe('knobs')
    })

    it('should include computed stats in API call', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ id: 123 })
      })
      global.fetch = mockFetch

      const routeFeatures = {
        difficulty_level: 3,
        surface_types: ['broken-paved-road'],
        tire_dry: 'semi-slick',
        tire_wet: 'knobs'
      }

      const wrapper = createWrapper({
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints,
        routeFeatures,
        show: true
      })

      await wrapper.vm.$nextTick()
      await wrapper.find('#route-name').setValue('Test Route')
      await wrapper.find('.btn-primary').trigger('click')
      await flushPromises()

      const callArgs = mockFetch.mock.calls[0][1]
      const bodyData = JSON.parse(callArgs.body)
      expect(bodyData.computed_stats).toBeDefined()
      expect(bodyData.computed_stats.distance).toBe(25.5)
      expect(bodyData.computed_stats.difficulty).toBe(3) // From route features
      expect(bodyData.computed_stats.elevationGain).toBe(450)
      expect(bodyData.computed_stats.elevationLoss).toBe(380)
    })

    it('should include route track points in API call', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ id: 123 })
      })
      global.fetch = mockFetch

      const wrapper = createWrapper({
        routeFeatures: mockRouteFeatures,
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints,
        show: true
      })

      await wrapper.vm.$nextTick()
      await wrapper.find('#route-name').setValue('Test Route')
      await wrapper.find('.btn-primary').trigger('click')
      await flushPromises()

      const callArgs = mockFetch.mock.calls[0][1]
      const bodyData = JSON.parse(callArgs.body)
      expect(bodyData.route_track_points).toEqual(mockRouteTrackPoints)
    })
  })

  describe('Tire Recommendation Logic', () => {
    it('should recommend slick when all segments have slick tires', () => {
      const wrapper = createWrapper({
        routeFeatures: {
          difficulty_level: 2,
          surface_types: ['broken-paved-road'],
          tire_dry: 'slick',
          tire_wet: 'slick'
        },
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints
      })

      const stats = (wrapper.vm as any).computedStats
      expect(stats.tireDry).toBe('slick')
      expect(stats.tireWet).toBe('slick')
    })

    it('should use semi-slick from route features when provided', () => {
      const routeFeatures = {
        difficulty_level: 3,
        surface_types: ['broken-paved-road'],
        tire_dry: 'semi-slick',
        tire_wet: 'semi-slick'
      }

      const wrapper = createWrapper({
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints,
        routeFeatures
      })

      const stats = (wrapper.vm as any).computedStats
      expect(stats.tireDry).toBe('semi-slick')
      expect(stats.tireWet).toBe('semi-slick')
    })

    it('should use knobs from route features when provided', () => {
      const routeFeatures = {
        difficulty_level: 4,
        surface_types: ['forest-trail'],
        tire_dry: 'knobs',
        tire_wet: 'knobs'
      }

      const wrapper = createWrapper({
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints,
        routeFeatures
      })

      const stats = (wrapper.vm as any).computedStats
      // Route features provide the tire recommendation
      expect(stats.tireDry).toBe('knobs')
      expect(stats.tireWet).toBe('knobs')
    })
  })
})
