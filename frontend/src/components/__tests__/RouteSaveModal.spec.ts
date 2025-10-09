import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import RouteSaveModal from '../RouteSaveModal.vue'
import RouteInfoCard from '../RouteInfoCard.vue'
import type { TrackResponse } from '../../types'
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
  let mockSegments: TrackResponse[]
  let mockRouteTrackPoints: Array<{
    lat: number
    lng: number
    elevation: number
    distance: number
  }>

  beforeEach(() => {
    mockSegments = [
      {
        id: 1,
        name: 'Segment 1',
        track_type: 'segment',
        difficulty_level: 3,
        surface_type: ['broken-paved-road'],
        tire_dry: 'semi-slick',
        tire_wet: 'knobs',
        barycenter_latitude: 45.5,
        barycenter_longitude: -73.5,
        bound_north: 45.6,
        bound_south: 45.4,
        bound_east: -73.4,
        bound_west: -73.6,
        file_path: 'test1.gpx',
        comments: ''
      },
      {
        id: 2,
        name: 'Segment 2',
        track_type: 'segment',
        difficulty_level: 4,
        surface_type: ['forest-trail'],
        tire_dry: 'knobs',
        tire_wet: 'knobs',
        barycenter_latitude: 45.5,
        barycenter_longitude: -73.5,
        bound_north: 45.6,
        bound_south: 45.4,
        bound_east: -73.4,
        bound_west: -73.6,
        file_path: 'test2.gpx',
        comments: ''
      }
    ]

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
        selectedSegments: mockSegments,
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
        selectedSegments: mockSegments,
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
        selectedSegments: [],
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
        selectedSegments: mockSegments,
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
        selectedSegments: [],
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
        selectedSegments: mockSegments,
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
        selectedSegments: mockSegments,
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
        selectedSegments: mockSegments,
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
        selectedSegments: mockSegments,
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
    it('should calculate median difficulty from segments (even number)', async () => {
      const wrapper = createWrapper({
        selectedSegments: mockSegments,
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints
      })

      // Check computed stats
      const stats = (wrapper.vm as any).computedStats
      // Median of [3, 4] is (3 + 4) / 2 = 3.5
      expect(stats.difficulty).toBe(3.5)
    })

    it('should calculate median difficulty from segments (odd number)', async () => {
      const threeSegments = [
        ...mockSegments,
        {
          ...mockSegments[0],
          id: 3,
          difficulty_level: 5
        }
      ]

      const wrapper = createWrapper({
        selectedSegments: threeSegments,
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints
      })

      // Check computed stats
      const stats = (wrapper.vm as any).computedStats
      // Median of [3, 4, 5] is 4
      expect(stats.difficulty).toBe(4)
    })

    it('should calculate median difficulty with unsorted input', async () => {
      const unsortedSegments = [
        {
          ...mockSegments[0],
          id: 1,
          difficulty_level: 5
        },
        {
          ...mockSegments[1],
          id: 2,
          difficulty_level: 2
        },
        {
          ...mockSegments[0],
          id: 3,
          difficulty_level: 3
        }
      ]

      const wrapper = createWrapper({
        selectedSegments: unsortedSegments,
        routeDistance: 25.5,
        elevationStats: {
          totalGain: 450,
          totalLoss: 380,
          maxElevation: 500,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints
      })

      // Check computed stats
      const stats = (wrapper.vm as any).computedStats
      // Median of [5, 2, 3] sorted is [2, 3, 5], median is 3
      expect(stats.difficulty).toBe(3)
    })

    it('should collect all surface types from segments', async () => {
      const wrapper = createWrapper({
        selectedSegments: mockSegments,
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
      expect(stats.surfaceTypes).toContain('broken-paved-road')
      expect(stats.surfaceTypes).toContain('forest-trail')
    })

    it('should recommend worst-case tire for dry conditions', async () => {
      const wrapper = createWrapper({
        selectedSegments: mockSegments,
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
      // Segments have semi-slick and knobs, should recommend knobs
      expect(stats.tireDry).toBe('knobs')
    })

    it('should recommend worst-case tire for wet conditions', async () => {
      const wrapper = createWrapper({
        selectedSegments: mockSegments,
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
      // Both segments have knobs for wet, should recommend knobs
      expect(stats.tireWet).toBe('knobs')
    })

    it('should use default stats for waypoint routes (no segments)', () => {
      const wrapper = createWrapper({
        selectedSegments: [],
        routeDistance: 15.5,
        elevationStats: {
          totalGain: 200,
          totalLoss: 150,
          maxElevation: 300,
          minElevation: 100
        },
        routeTrackPoints: mockRouteTrackPoints
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
        selectedSegments: mockSegments,
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
        selectedSegments: mockSegments,
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
        selectedSegments: mockSegments,
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
        selectedSegments: mockSegments,
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
        selectedSegments: mockSegments,
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
        selectedSegments: mockSegments,
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

    it('should include segment IDs and isReversed flags in API call', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ id: 123 })
      })
      global.fetch = mockFetch

      const segmentsWithReversed = [
        { ...mockSegments[0], isReversed: true },
        { ...mockSegments[1], isReversed: false }
      ]

      const wrapper = createWrapper({
        selectedSegments: segmentsWithReversed,
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
      expect(bodyData.segments[0].id).toBe(1)
      expect(bodyData.segments[0].isReversed).toBe(true)
      expect(bodyData.segments[1].id).toBe(2)
      expect(bodyData.segments[1].isReversed).toBe(false)
    })

    it('should include computed stats in API call', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ id: 123 })
      })
      global.fetch = mockFetch

      const wrapper = createWrapper({
        selectedSegments: mockSegments,
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
      expect(bodyData.computed_stats).toBeDefined()
      expect(bodyData.computed_stats.distance).toBe(25.5)
      expect(bodyData.computed_stats.difficulty).toBe(3.5)
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
        selectedSegments: mockSegments,
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
      const slickSegments = [
        { ...mockSegments[0], tire_dry: 'slick', tire_wet: 'slick' }
      ]

      const wrapper = createWrapper({
        selectedSegments: slickSegments,
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

    it('should recommend semi-slick when one segment needs it', () => {
      const mixedSegments = [
        { ...mockSegments[0], tire_dry: 'slick', tire_wet: 'slick' },
        { ...mockSegments[1], tire_dry: 'semi-slick', tire_wet: 'semi-slick' }
      ]

      const wrapper = createWrapper({
        selectedSegments: mixedSegments,
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
      expect(stats.tireDry).toBe('semi-slick')
      expect(stats.tireWet).toBe('semi-slick')
    })

    it('should recommend knobs when any segment needs knobs', () => {
      const wrapper = createWrapper({
        selectedSegments: mockSegments,
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
      // At least one segment has knobs
      expect(stats.tireDry).toBe('knobs')
      expect(stats.tireWet).toBe('knobs')
    })
  })
})
