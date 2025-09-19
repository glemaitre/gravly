import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import SegmentDetail from '../SegmentDetail.vue'
import type { TrackResponse } from '../../types'

// Mock Vue Router
const mockRouter = {
  push: vi.fn(),
  replace: vi.fn(),
  go: vi.fn(),
  back: vi.fn(),
  forward: vi.fn()
}

const mockRoute = {
  params: { id: '123' },
  query: {},
  path: '/segment/123',
  name: 'segment-detail',
  id: '123'
}

// Mock useRouter and useRoute composables
vi.mock('vue-router', () => ({
  useRouter: () => mockRouter,
  useRoute: () => mockRoute
}))

// Mock i18n
const mockT = vi.fn((key: string) => key)
vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: mockT
  })
}))

// Mock Chart.js
const mockChart = {
  destroy: vi.fn(),
  update: vi.fn(),
  render: vi.fn()
}

vi.mock('chart.js/auto', () => ({
  Chart: vi.fn(() => mockChart)
}))

// Mock Leaflet
const mockMapInstance = {
  setView: vi.fn(),
  addLayer: vi.fn(),
  removeLayer: vi.fn(),
  invalidateSize: vi.fn(),
  fitBounds: vi.fn(),
  on: vi.fn(),
  off: vi.fn(),
  remove: vi.fn(),
  eachLayer: vi.fn(),
  getBounds: vi.fn(() => ({
    getNorth: vi.fn(() => 50.0),
    getSouth: vi.fn(() => 40.0),
    getEast: vi.fn(() => 10.0),
    getWest: vi.fn(() => 0.0)
  })),
  getCenter: vi.fn(() => ({ lat: 45.0, lng: 5.0 })),
  getZoom: vi.fn(() => 10),
  _layers: {},
  _leaflet_id: 1
}

const mockPolyline = {
  addTo: vi.fn(),
  remove: vi.fn(),
  on: vi.fn(),
  off: vi.fn(),
  getBounds: vi.fn(() => ({
    getNorth: vi.fn(() => 50.0),
    getSouth: vi.fn(() => 40.0),
    getEast: vi.fn(() => 10.0),
    getWest: vi.fn(() => 0.0)
  })),
  _leaflet_id: 'polyline-1'
}

const mockMarker = {
  addTo: vi.fn(),
  remove: vi.fn(),
  setLatLng: vi.fn(),
  _leaflet_id: 'marker-1'
}

// Mock Leaflet module
vi.mock('leaflet', () => ({
  default: {
    map: vi.fn(() => mockMapInstance),
    tileLayer: vi.fn(() => ({
      addTo: vi.fn()
    })),
    polyline: vi.fn(() => mockPolyline),
    marker: vi.fn(() => mockMarker),
    latLng: vi.fn((lat, lng) => ({ lat, lng })),
    latLngBounds: vi.fn(() => ({
      extend: vi.fn(),
      getNorth: vi.fn(() => 50.0),
      getSouth: vi.fn(() => 40.0),
      getEast: vi.fn(() => 10.0),
      getWest: vi.fn(() => 0.0)
    }))
  }
}))

// Mock fetch
global.fetch = vi.fn()

// Mock DOM methods
Object.defineProperty(document, 'getElementById', {
  value: vi.fn(() => ({
    offsetWidth: 800,
    offsetHeight: 600
  }))
})

describe('SegmentDetail', () => {
  let wrapper: any

  const mockSegment: TrackResponse = {
    id: 123,
    name: 'Test Segment',
    track_type: 'segment',
    file_path: 'test.gpx',
    bound_north: 45.8,
    bound_south: 45.7,
    bound_east: 4.9,
    bound_west: 4.8,
    barycenter_latitude: 45.75,
    barycenter_longitude: 4.85,
    difficulty_level: 3,
    surface_type: 'forest-trail',
    tire_dry: 'semi-slick',
    tire_wet: 'knobs',
    comments: 'Test segment for testing'
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockT.mockImplementation((key: string) => key)
    // Reset fetch mock
    ;(global.fetch as any).mockClear()
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('Component Rendering', () => {
    it('renders correctly', () => {
      wrapper = mount(SegmentDetail)
      expect(wrapper.find('.segment-detail').exists()).toBe(true)
    })

    it('shows loading state initially', () => {
      wrapper = mount(SegmentDetail)
      expect(wrapper.find('.loading-container').exists()).toBe(true)
      expect(wrapper.find('.loading-spinner').exists()).toBe(true)
    })

    it('shows error state when error occurs', async () => {
      // Mock fetch to return error
      ;(global.fetch as any).mockRejectedValueOnce(new Error('Network error'))

      wrapper = mount(SegmentDetail)

      // Wait for async operations
      await wrapper.vm.$nextTick()
      await new Promise((resolve) => setTimeout(resolve, 100))

      expect(wrapper.find('.error-container').exists()).toBe(true)
      expect(wrapper.find('.error-message').exists()).toBe(true)
    })
  })

  describe('Header Section', () => {
    it('shows loading text when segment is not loaded', () => {
      wrapper = mount(SegmentDetail)
      expect(wrapper.find('.segment-title').text()).toBe('Loading...')
    })

    it('has back button with correct text', () => {
      wrapper = mount(SegmentDetail)
      const backButton = wrapper.find('.back-button')
      expect(backButton.exists()).toBe(true)
      expect(backButton.text()).toContain('segmentDetail.backToTrackFinder')
    })

    it('calls goBack when back button is clicked', async () => {
      wrapper = mount(SegmentDetail)

      const backButton = wrapper.find('.back-button')
      await backButton.trigger('click')

      expect(mockRouter.push).toHaveBeenCalledWith('/')
    })
  })

  describe('Data Loading', () => {
    it('handles API errors gracefully', async () => {
      // Mock API error
      ;(global.fetch as any).mockRejectedValueOnce(new Error('API Error'))

      wrapper = mount(SegmentDetail)

      await wrapper.vm.$nextTick()
      await new Promise((resolve) => setTimeout(resolve, 100))

      expect(wrapper.find('.error-container').exists()).toBe(true)
    })
  })

  describe('Utility Functions', () => {
    it('formats distance correctly', () => {
      wrapper = mount(SegmentDetail)
      expect(wrapper.vm.formatDistance(1.5)).toBe('1.50 km')
    })

    it('formats elevation correctly', () => {
      wrapper = mount(SegmentDetail)
      expect(wrapper.vm.formatElevation(120.7)).toBe('121m')
    })

    it('gets track type icon correctly', () => {
      wrapper = mount(SegmentDetail)
      expect(wrapper.vm.getTrackTypeIcon('segment')).toBe('fa-route')
      expect(wrapper.vm.getTrackTypeIcon('route')).toBe('fa-map')
    })

    it('gets difficulty word correctly', () => {
      wrapper = mount(SegmentDetail)
      // Mock the t function to return expected values
      mockT.mockImplementation((key: string) => {
        const translations: Record<string, string> = {
          'difficulty.level1': 'Easy',
          'difficulty.level2': 'Moderate',
          'difficulty.level3': 'Hard',
          'difficulty.level4': 'Very Hard',
          'difficulty.level5': 'Extreme'
        }
        return translations[key] || key
      })

      expect(wrapper.vm.getDifficultyWord(1)).toBe('Easy')
      expect(wrapper.vm.getDifficultyWord(3)).toBe('Hard')
      expect(wrapper.vm.getDifficultyWord(5)).toBe('Extreme')
    })
  })

  describe('Component Lifecycle', () => {
    it('cleans up resources on unmount', () => {
      wrapper = mount(SegmentDetail)

      // Set some refs to test cleanup
      wrapper.vm.map = mockMapInstance
      wrapper.vm.elevationChart = mockChart
      wrapper.vm.mapMarker = mockMarker

      wrapper.unmount()

      expect(mockMapInstance.remove).toHaveBeenCalled()
      expect(mockChart.destroy).toHaveBeenCalled()
      expect(mockMarker.remove).toHaveBeenCalled()
    })
  })

  describe('Component Structure', () => {
    it('has proper CSS classes for layout', () => {
      wrapper = mount(SegmentDetail)

      expect(wrapper.find('.segment-detail').exists()).toBe(true)
      expect(wrapper.find('.detail-header').exists()).toBe(true)
    })

    it('has proper header structure', () => {
      wrapper = mount(SegmentDetail)

      expect(wrapper.find('.header-wrapper').exists()).toBe(true)
      expect(wrapper.find('.header-left').exists()).toBe(true)
      expect(wrapper.find('.segment-title').exists()).toBe(true)
      expect(wrapper.find('.back-button').exists()).toBe(true)
    })
  })

  describe('Error Handling', () => {
    it('shows error message when segment fetch fails', async () => {
      // Mock segment fetch failure - but first ensure we have a segment ID
      ;(global.fetch as any).mockRejectedValueOnce(new Error('Segment not found'))

      wrapper = mount(SegmentDetail)

      await wrapper.vm.$nextTick()
      await new Promise((resolve) => setTimeout(resolve, 100))

      expect(wrapper.find('.error-container').exists()).toBe(true)
      // The component successfully gets the segment ID from route, but fetch fails
      // so it shows the actual fetch error message
      expect(wrapper.find('.error-message').text()).toContain('Segment not found')
    })

    it('shows error message when GPX data fetch fails', async () => {
      // Mock successful segment fetch but failed GPX fetch
      ;(global.fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockSegment)
        })
        .mockRejectedValueOnce(new Error('GPX data not found'))

      wrapper = mount(SegmentDetail)

      await wrapper.vm.$nextTick()
      await new Promise((resolve) => setTimeout(resolve, 100))

      expect(wrapper.find('.error-container').exists()).toBe(true)
    })
  })
})
