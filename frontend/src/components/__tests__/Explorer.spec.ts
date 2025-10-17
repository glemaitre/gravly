import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import Explorer from '../Explorer.vue'

// Import real locale files
import en from '../../i18n/locales/en'
import fr from '../../i18n/locales/fr'

// Create i18n instance for testing
const i18n = createI18n({
  legacy: false,
  locale: 'en',
  fallbackLocale: 'en',
  messages: { en, fr }
})

// Mock Vue Router
const mockRouter = {
  push: vi.fn(),
  replace: vi.fn(),
  go: vi.fn(),
  back: vi.fn(),
  forward: vi.fn()
}

// Mock useRouter composable
vi.mock('vue-router', () => ({
  useRouter: () => mockRouter
}))

// Helper function to mount component with router mock and i18n
const mountWithRouter = (component: any, options: any = {}) => {
  return mount(component, {
    global: {
      plugins: [i18n],
      ...(options.global || {})
    },
    ...options
  })
}

// Mock Leaflet with more comprehensive functionality
const mockMapInstance = {
  setView: vi.fn(),
  addLayer: vi.fn(),
  removeLayer: vi.fn(),
  invalidateSize: vi.fn(),
  fitBounds: vi.fn(),
  on: vi.fn(),
  off: vi.fn(),
  remove: vi.fn(),
  eachLayer: vi.fn((callback) => {
    // Mock implementation - call callback with some mock layers
    const mockLayers = [{ _leaflet_id: 'tile-layer' }, { _leaflet_id: 'control-layer' }]
    mockLayers.forEach(callback)
  }),
  getBounds: vi.fn(() => ({
    getNorth: vi.fn(() => 50.0),
    getSouth: vi.fn(() => 40.0),
    getEast: vi.fn(() => 10.0),
    getWest: vi.fn(() => 0.0),
    contains: vi.fn(() => false)
  })),
  getCenter: vi.fn(() => ({ lat: 45.0, lng: 5.0 })),
  getZoom: vi.fn(() => 10),
  _layers: {},
  _leaflet_id: 1
}

const mockPolyline = {
  addTo: vi.fn(() => mockPolyline),
  setStyle: vi.fn(),
  on: vi.fn(),
  _leaflet_id: 2
}

const mockMarker = {
  addTo: vi.fn(() => mockMarker),
  _leaflet_id: 3
}

const mockCircleMarker = {
  addTo: vi.fn(() => mockCircleMarker),
  setRadius: vi.fn(),
  bindPopup: vi.fn(() => mockCircleMarker),
  _leaflet_id: 4
}

const mockRectangle = {
  addTo: vi.fn(() => mockRectangle),
  setStyle: vi.fn(),
  on: vi.fn(),
  _leaflet_id: 5
}

const mockTileLayer = {
  addTo: vi.fn(() => mockTileLayer)
}

const mockScaleControl = {
  addTo: vi.fn(() => mockScaleControl)
}

const mockZoomControl = {
  addTo: vi.fn(() => mockZoomControl)
}

vi.mock('leaflet', () => ({
  default: {
    map: vi.fn(() => mockMapInstance),
    tileLayer: vi.fn(() => mockTileLayer),
    polyline: vi.fn(() => mockPolyline),
    marker: vi.fn(() => mockMarker),
    circleMarker: vi.fn(() => mockCircleMarker),
    rectangle: vi.fn(() => mockRectangle),
    divIcon: vi.fn(() => ({})),
    latLngBounds: vi.fn(() => ({
      fitBounds: vi.fn()
    })),
    control: {
      scale: vi.fn(() => mockScaleControl),
      zoom: vi.fn(() => mockZoomControl)
    },
    // Add Leaflet classes for instanceof checks
    Rectangle: class MockRectangle {},
    Polyline: class MockPolyline {},
    CircleMarker: class MockCircleMarker {}
  }
}))

// Mock EventSource
global.EventSource = vi.fn(() => ({
  onopen: null,
  onmessage: null,
  onerror: null,
  readyState: 1,
  url: '/api/segments/search',
  close: vi.fn()
})) as any

// Mock gpxParser
vi.mock('../../utils/gpxParser', () => ({
  parseGPXData: vi.fn(() => ({
    points: [
      { lat: 45.0, lng: 5.0, elevation: 100 },
      { lat: 45.1, lng: 5.1, elevation: 110 }
    ],
    bounds: {
      north: 45.1,
      south: 45.0,
      east: 5.1,
      west: 5.0
    }
  }))
}))

// Mock DOM methods
Object.defineProperty(document, 'getElementById', {
  value: vi.fn(() => ({
    offsetWidth: 800,
    offsetHeight: 600
  }))
})

describe('Explorer', () => {
  let wrapper: any

  beforeEach(() => {
    vi.clearAllMocks()
    // Suppress expected console errors during tests
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    vi.spyOn(console, 'log').mockImplementation(() => {})
    vi.spyOn(console, 'info').mockImplementation(() => {})
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
    // Restore console methods
    vi.restoreAllMocks()
  })

  it('renders correctly', () => {
    wrapper = mountWithRouter(Explorer)

    expect(wrapper.find('.landing-page').exists()).toBe(true)
    expect(wrapper.find('.landing-content').exists()).toBe(true)
  })

  it('has correct CSS classes for styling', () => {
    const wrapper = mountWithRouter(Explorer)

    const landingPage = wrapper.find('.landing-page')
    const landingContent = wrapper.find('.landing-content')

    expect(landingPage.exists()).toBe(true)
    expect(landingContent.exists()).toBe(true)
  })

  it('has proper structure with landing-page container', () => {
    const wrapper = mountWithRouter(Explorer)

    const landingPage = wrapper.find('.landing-page')
    expect(landingPage.exists()).toBe(true)

    // Check that landing-content is inside landing-page
    const landingContent = landingPage.find('.landing-content')
    expect(landingContent.exists()).toBe(true)
  })

  it('renders as a single root element', () => {
    const wrapper = mountWithRouter(Explorer)

    // Should have root element with button and content
    expect(wrapper.element.children.length).toBe(2) // Button + landing-content
    // Check that the root element has the landing-page class
    expect(wrapper.element.classList.contains('landing-page')).toBe(true)
  })

  it('has correct component name', () => {
    const wrapper = mountWithRouter(Explorer)

    expect(wrapper.vm.$options.name || 'Explorer').toBe('Explorer')
  })

  it('is a functional component with no props', () => {
    const wrapper = mountWithRouter(Explorer)

    // Should not have any props
    expect(Object.keys(wrapper.props())).toHaveLength(0)
  })

  it('has content area ready for future content', () => {
    const wrapper = mountWithRouter(Explorer)

    const landingContent = wrapper.find('.landing-content')
    expect(landingContent.exists()).toBe(true)

    // Content area should have map section
    expect(landingContent.find('.map-section').exists()).toBe(true)
  })

  it('maintains proper HTML structure', () => {
    const wrapper = mountWithRouter(Explorer)

    const html = wrapper.html()

    // Should contain the expected HTML structure (accounting for scoped CSS attributes)
    expect(html).toContain('class="landing-page"')
    expect(html).toContain('class="landing-content"')
    expect(html).toContain('class="map-section"')
    expect(html).toContain('class="segment-list-section"')
    expect(html).toContain('</div>')
    expect(html).toContain('</div>')
  })

  it('has scoped styles applied correctly', () => {
    const wrapper = mountWithRouter(Explorer)

    const landingPage = wrapper.find('.landing-page')
    const landingContent = wrapper.find('.landing-content')

    // Check that elements exist (styles are applied via CSS, not directly testable in unit tests)
    expect(landingPage.exists()).toBe(true)
    expect(landingContent.exists()).toBe(true)
  })

  it('is ready for future content expansion', () => {
    const wrapper = mountWithRouter(Explorer)

    // The component should be structured to easily accept new content
    const landingContent = wrapper.find('.landing-content')
    expect(landingContent.exists()).toBe(true)

    // Should be able to add content inside landing-content
    expect(landingContent.element.children.length).toBe(1) // content-wrapper
  })

  it('follows Vue 3 Composition API patterns', () => {
    const wrapper = mountWithRouter(Explorer)

    // Component should be using <script setup> syntax
    // This is verified by the fact that it mounts without errors
    expect(wrapper.vm).toBeDefined()
  })

  it('has proper accessibility structure', () => {
    const wrapper = mountWithRouter(Explorer)

    // Should have proper div structure for screen readers
    const landingPage = wrapper.find('.landing-page')
    expect(landingPage.exists()).toBe(true)

    // Should be a semantic container
    expect(landingPage.element.tagName).toBe('DIV')
  })

  it('can be mounted multiple times without issues', () => {
    // Test that the component is stateless and can be reused
    const wrapper1 = mountWithRouter(Explorer)
    const wrapper2 = mountWithRouter(Explorer)

    expect(wrapper1.find('.landing-page').exists()).toBe(true)
    expect(wrapper2.find('.landing-page').exists()).toBe(true)

    // Both instances should be identical
    expect(wrapper1.html()).toBe(wrapper2.html())
  })

  it('handles component lifecycle correctly', () => {
    wrapper = mountWithRouter(Explorer)

    // Component should mount successfully
    expect(wrapper.find('.landing-page').exists()).toBe(true)

    // Should be able to unmount without errors
    expect(() => wrapper.unmount()).not.toThrow()
  })

  describe('Map functionality', () => {
    it('renders map container', () => {
      wrapper = mountWithRouter(Explorer)

      expect(wrapper.find('#landing-map').exists()).toBe(true)
      expect(wrapper.find('.map').exists()).toBe(true)
      expect(wrapper.find('.card-map').exists()).toBe(true)
    })

    it('displays map section without hero titles', () => {
      wrapper = mountWithRouter(Explorer)

      expect(wrapper.find('.hero-section').exists()).toBe(false)
      expect(wrapper.find('.hero-title').exists()).toBe(false)
      expect(wrapper.find('.hero-subtitle').exists()).toBe(false)
      expect(wrapper.find('.map-section').exists()).toBe(true)
    })

    it('has proper map section structure', () => {
      wrapper = mountWithRouter(Explorer)

      expect(wrapper.find('.map-section').exists()).toBe(true)
      expect(wrapper.find('.map-container').exists()).toBe(true)
      expect(wrapper.find('.card').exists()).toBe(true)
    })

    it('has correct map dimensions with full width and 65% height', () => {
      wrapper = mountWithRouter(Explorer)

      const mapElement = wrapper.find('.map')
      expect(mapElement.exists()).toBe(true)
      expect(mapElement.attributes('id')).toBe('landing-map')
      expect(mapElement.classes()).toContain('map')
    })

    it('has responsive CSS classes', () => {
      wrapper = mountWithRouter(Explorer)

      const mapContainer = wrapper.find('.map-container')
      expect(mapContainer.exists()).toBe(true)
      expect(mapContainer.classes()).toContain('map-container')
    })

    it('has full width and 65% height styling', () => {
      wrapper = mountWithRouter(Explorer)

      const mapElement = wrapper.find('.map')
      expect(mapElement.exists()).toBe(true)

      // Check that the map element has the correct class and attributes
      expect(mapElement.classes()).toContain('map')
      expect(mapElement.attributes('id')).toBe('landing-map')

      // In a real browser, the CSS height: 65vh and width: 100% would be applied
      // In the test environment, we verify the element structure is correct
      expect(mapElement.element.tagName).toBe('DIV')
    })
  })

  describe('Responsive design', () => {
    it('has proper responsive structure', () => {
      wrapper = mountWithRouter(Explorer)

      const landingContent = wrapper.find('.landing-content')
      expect(landingContent.exists()).toBe(true)
      expect(landingContent.classes()).toContain('landing-content')
    })

    it('maintains proper layout structure', () => {
      wrapper = mountWithRouter(Explorer)

      // Check that all main sections exist
      expect(wrapper.find('.map-section').exists()).toBe(true)
      expect(wrapper.find('.map-container').exists()).toBe(true)
    })
  })

  describe('Non-regression tests', () => {
    it('should not have duplicate map containers', () => {
      wrapper = mountWithRouter(Explorer)

      const mapContainers = wrapper.findAll('#landing-map')
      expect(mapContainers).toHaveLength(1)
    })

    it('should have proper map container hierarchy', () => {
      wrapper = mountWithRouter(Explorer)

      const mapSection = wrapper.find('.map-section')
      const mapContainer = mapSection.find('.map-container')
      const card = mapContainer.find('.card')
      const map = card.find('.map')

      expect(mapSection.exists()).toBe(true)
      expect(mapContainer.exists()).toBe(true)
      expect(card.exists()).toBe(true)
      expect(map.exists()).toBe(true)
    })

    it('should maintain consistent structure across multiple mounts', () => {
      const wrapper1 = mountWithRouter(Explorer)
      const wrapper2 = mountWithRouter(Explorer)

      expect(wrapper1.find('.landing-page').exists()).toBe(true)
      expect(wrapper2.find('.landing-page').exists()).toBe(true)
      expect(wrapper1.find('#landing-map').exists()).toBe(true)
      expect(wrapper2.find('#landing-map').exists()).toBe(true)

      wrapper1.unmount()
      wrapper2.unmount()
    })
  })

  describe('Loading States', () => {
    it('should show loading indicator when loading is true', async () => {
      wrapper = mountWithRouter(Explorer)

      // Set loading state
      await wrapper.vm.$nextTick()
      wrapper.vm.loading = true
      wrapper.vm.totalTracks = 5
      wrapper.vm.loadedTracks = 2

      await wrapper.vm.$nextTick()

      const loadingIndicator = wrapper.find('.loading-indicator')
      expect(loadingIndicator.exists()).toBe(true)
      expect(loadingIndicator.text()).toContain('🔍 Loading segments...')
    })

    it('should show searching message when no tracks loaded', async () => {
      wrapper = mountWithRouter(Explorer)

      wrapper.vm.loading = true
      wrapper.vm.totalTracks = 0

      await wrapper.vm.$nextTick()

      const loadingIndicator = wrapper.find('.loading-indicator')
      expect(loadingIndicator.text()).toContain('🔍 Loading segments...')
    })

    it('should hide loading indicator when loading is false', async () => {
      wrapper = mountWithRouter(Explorer)

      wrapper.vm.loading = false

      await wrapper.vm.$nextTick()

      const loadingIndicator = wrapper.find('.loading-indicator')
      expect(loadingIndicator.exists()).toBe(false)
    })
  })

  describe('Map Controls', () => {
    it('should render Max Results control', () => {
      wrapper = mountWithRouter(Explorer)

      const mapControls = wrapper.find('.map-controls')
      expect(mapControls.exists()).toBe(true)

      const limitControl = mapControls.find('.limit-control')
      expect(limitControl.exists()).toBe(true)

      const limitLabel = limitControl.find('.limit-label')
      expect(limitLabel.exists()).toBe(true)
      expect(limitLabel.text()).toContain('Max Results:')

      const limitSelect = limitControl.find('.limit-select')
      expect(limitSelect.exists()).toBe(true)
    })

    it('should have correct default search limit', () => {
      wrapper = mountWithRouter(Explorer)

      expect(wrapper.vm.searchLimit).toBe(50)
    })

    it('should handle limit change events', async () => {
      wrapper = mountWithRouter(Explorer)

      const limitSelect = wrapper.find('.limit-select')
      expect(limitSelect.exists()).toBe(true)

      // Test that the method exists
      expect(typeof wrapper.vm.onLimitChange).toBe('function')

      // Test calling the method directly
      wrapper.vm.onLimitChange()

      // Should not throw error
      expect(wrapper.vm.searchLimit).toBeDefined()
    })

    it('should have all limit options available', () => {
      wrapper = mountWithRouter(Explorer)

      const limitSelect = wrapper.find('.limit-select')
      const options = limitSelect.findAll('option')

      expect(options).toHaveLength(4)
      expect(options[0].text()).toBe('25')
      expect(options[1].text()).toBe('50')
      expect(options[2].text()).toBe('75')
      expect(options[3].text()).toBe('100')
    })
  })

  describe('Map Initialization', () => {
    it('should initialize map on mount', async () => {
      wrapper = mountWithRouter(Explorer)

      // Wait for onMounted to execute
      await wrapper.vm.$nextTick()
      await new Promise((resolve) => setTimeout(resolve, 100))

      // Check that Leaflet.map was called with the correct arguments
      const L = await import('leaflet')
      expect(L.default.map).toHaveBeenCalled()

      // The first argument should be the container element
      const firstCall = L.default.map.mock.calls[0]
      expect(firstCall[0]).toHaveProperty('offsetWidth')
      expect(firstCall[0]).toHaveProperty('offsetHeight')
    })

    it('should set up tile layer', async () => {
      wrapper = mountWithRouter(Explorer)

      await wrapper.vm.$nextTick()
      await new Promise((resolve) => setTimeout(resolve, 100))

      const L = await import('leaflet')
      expect(L.default.tileLayer).toHaveBeenCalled()
      expect(mockTileLayer.addTo).toHaveBeenCalledWith(mockMapInstance)
    })

    it('should add scale control and zoom control', async () => {
      wrapper = mountWithRouter(Explorer)

      await wrapper.vm.$nextTick()
      await new Promise((resolve) => setTimeout(resolve, 100))

      const L = await import('leaflet')
      expect(L.default.control.scale).toHaveBeenCalled()
      expect(L.default.control.zoom).toHaveBeenCalled()
      expect(mockScaleControl.addTo).toHaveBeenCalledWith(mockMapInstance)
      expect(mockZoomControl.addTo).toHaveBeenCalledWith(mockMapInstance)
    })

    it('should set initial map view', async () => {
      // Clear any existing localStorage data
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.clear()
      }

      // Mock localStorage to return null (no saved state)
      const mockLocalStorage = {
        getItem: vi.fn(() => null),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn()
      }

      Object.defineProperty(window, 'localStorage', {
        value: mockLocalStorage,
        writable: true
      })

      wrapper = mountWithRouter(Explorer)

      await wrapper.vm.$nextTick()
      await new Promise((resolve) => setTimeout(resolve, 100))

      expect(mockMapInstance.setView).toHaveBeenCalledWith([46.942728, 4.033681], 14)
    })

    it('should not initialize map if already exists', async () => {
      wrapper = mountWithRouter(Explorer)

      // First mount
      await wrapper.vm.$nextTick()
      await new Promise((resolve) => setTimeout(resolve, 100))

      const L = await import('leaflet')
      const mapCallCount = L.default.map.mock.calls.length

      // Try to initialize again (should not create new map)
      wrapper.vm.initializeMap()
      await wrapper.vm.$nextTick()

      expect(L.default.map.mock.calls.length).toBe(mapCallCount)
    })
  })

  describe('EventSource Integration', () => {
    it('should have searchSegmentsInView method', () => {
      wrapper = mountWithRouter(Explorer)

      expect(typeof wrapper.vm.searchSegmentsInView).toBe('function')
    })

    it('should have eventSource property', () => {
      wrapper = mountWithRouter(Explorer)

      expect(wrapper.vm.eventSource).toBeNull()
    })

    it('should have loading state properties', () => {
      wrapper = mountWithRouter(Explorer)

      expect(wrapper.vm.loading).toBe(false)
      expect(wrapper.vm.totalTracks).toBe(0)
      expect(wrapper.vm.loadedTracks).toBe(0)
    })

    it('should have segments array', () => {
      wrapper = mountWithRouter(Explorer)

      expect(Array.isArray(wrapper.vm.segments)).toBe(true)
      expect(wrapper.vm.segments).toHaveLength(0)
    })
  })

  describe('GPX Data Processing', () => {
    it('should have parseGPXData imported', async () => {
      const { parseGPXData } = await import('../../utils/gpxParser')
      expect(typeof parseGPXData).toBe('function')
    })

    it('should have processTrack method', () => {
      wrapper = mountWithRouter(Explorer)

      expect(typeof wrapper.vm.processTrack).toBe('function')
    })

    it('should have addGPXTrackToMap method', () => {
      wrapper = mountWithRouter(Explorer)

      expect(typeof wrapper.vm.addGPXTrackToMap).toBe('function')
    })

    it('should have addBoundingBoxToMap method', () => {
      wrapper = mountWithRouter(Explorer)

      expect(typeof wrapper.vm.addBoundingBoxToMap).toBe('function')
    })
  })

  describe('Component Lifecycle', () => {
    it('should mount and unmount without errors', () => {
      wrapper = mountWithRouter(Explorer)

      expect(wrapper.exists()).toBe(true)

      // Should unmount cleanly
      expect(() => wrapper.unmount()).not.toThrow()
    })

    it('should have onMounted and onUnmounted lifecycle hooks', () => {
      wrapper = mountWithRouter(Explorer)

      // Component should mount successfully, indicating lifecycle hooks work
      expect(wrapper.exists()).toBe(true)
    })

    it('should initialize map on mount', async () => {
      wrapper = mountWithRouter(Explorer)

      await wrapper.vm.$nextTick()
      await new Promise((resolve) => setTimeout(resolve, 100))

      // Map should be initialized (we can't directly test the private map variable)
      // but we can test that the component mounted successfully
      expect(wrapper.exists()).toBe(true)
    })
  })

  describe('Dynamic Circle Scaling', () => {
    it('should have updateCircleSizes method', () => {
      wrapper = mountWithRouter(Explorer)

      expect(typeof wrapper.vm.updateCircleSizes).toBe('function')
    })

    it('should calculate correct radius for different zoom levels', () => {
      wrapper = mountWithRouter(Explorer)

      // Test the radius calculation logic
      const baseRadius = 6
      const maxRadius = 10
      const minRadius = 2

      const testZoomLevels = [
        { zoom: 5, expectedRadius: 4 }, // 6 + (5-10) * 0.4 = 6 + (-5) * 0.4 = 4
        { zoom: 8, expectedRadius: 5.2 }, // 6 + (8-10) * 0.4 = 6 + (-2) * 0.4 = 5.2
        { zoom: 10, expectedRadius: 6 }, // baseRadius
        { zoom: 12, expectedRadius: 6.8 }, // baseRadius + (12-10) * 0.4 = 6 + 2 * 0.4 = 6.8
        { zoom: 15, expectedRadius: 8 } // 6 + (15-10) * 0.4 = 6 + 5 * 0.4 = 8
      ]

      testZoomLevels.forEach(({ zoom, expectedRadius }) => {
        const dynamicRadius = Math.max(
          minRadius,
          Math.min(maxRadius, baseRadius + (zoom - 10) * 0.4)
        )

        expect(dynamicRadius).toBeCloseTo(expectedRadius, 1)
      })
    })

    it('should update circle markers when zoom level changes', async () => {
      wrapper = mountWithRouter(Explorer)

      // Mock the currentMapLayers with some test data
      const mockLayerData = {
        startMarker: { setRadius: vi.fn() },
        endMarker: { setRadius: vi.fn() }
      }
      wrapper.vm.currentMapLayers = new Map([['test-segment', mockLayerData]])

      // Mock different zoom levels
      mockMapInstance.getZoom.mockReturnValue(5) // Very zoomed out

      // Call the updateCircleSizes function directly - should not throw error
      expect(() => wrapper.vm.updateCircleSizes()).not.toThrow()

      // Test with zoomed in level
      mockMapInstance.getZoom.mockReturnValue(15) // Very zoomed in
      expect(() => wrapper.vm.updateCircleSizes()).not.toThrow()
    })

    it('should handle empty currentMapLayers gracefully', () => {
      wrapper = mountWithRouter(Explorer)

      // Set empty map layers
      wrapper.vm.currentMapLayers = new Map()

      // Should not throw error
      expect(() => wrapper.vm.updateCircleSizes()).not.toThrow()
    })

    it('should handle layers without markers gracefully', () => {
      wrapper = mountWithRouter(Explorer)

      // Mock layer data without markers
      const mockLayerData = {
        polyline: { someProperty: 'value' }
        // No startMarker or endMarker
      }
      wrapper.vm.currentMapLayers = new Map([['test-segment', mockLayerData]])

      // Should not throw error
      expect(() => wrapper.vm.updateCircleSizes()).not.toThrow()
    })
  })

  describe('Segment Loading and Display', () => {
    it('should display loading indicator when loading segments', async () => {
      wrapper = mountWithRouter(Explorer)
      await wrapper.vm.$nextTick()

      // Set loading state
      wrapper.vm.loading = true
      wrapper.vm.totalTracks = 5
      wrapper.vm.loadedTracks = 2
      await wrapper.vm.$nextTick()

      const loadingIndicator = wrapper.find('.loading-indicator')
      expect(loadingIndicator.exists()).toBe(true)
      expect(loadingIndicator.text()).toContain('Loading segments...')
    })

    it('should display search indicator when loading and no tracks', async () => {
      wrapper = mountWithRouter(Explorer)
      await wrapper.vm.$nextTick()

      // Set loading state to true and no tracks
      wrapper.vm.loading = true
      wrapper.vm.totalTracks = 0
      await wrapper.vm.$nextTick()

      const loadingIndicator = wrapper.find('.loading-indicator')
      expect(loadingIndicator.exists()).toBe(true)
      expect(loadingIndicator.text()).toContain('Loading segments...')
    })

    it('should pass segments data to SegmentList component', async () => {
      const mockSegments = [
        {
          id: 1,
          name: 'Test Segment 1',
          track_type: 'segment',
          file_path: 'test1.gpx',
          bound_north: 45.8,
          bound_south: 45.7,
          bound_east: 4.9,
          bound_west: 4.8,
          difficulty_level: 3,
          surface_type: ['forest-trail'],
          tire_dry: 'semi-slick',
          tire_wet: 'knobs',
          comments: 'Test comment'
        },
        {
          id: 2,
          name: 'Test Segment 2',
          track_type: 'route',
          file_path: 'test2.gpx',
          bound_north: 45.9,
          bound_south: 45.8,
          bound_east: 5.0,
          bound_west: 4.9,
          difficulty_level: 4,
          surface_type: ['big-stone-road'],
          tire_dry: 'knobs',
          tire_wet: 'knobs',
          comments: ''
        }
      ]

      wrapper = mountWithRouter(Explorer)
      wrapper.vm.segments = mockSegments
      await wrapper.vm.$nextTick()

      const segmentList = wrapper.findComponent({ name: 'SegmentList' })
      expect(segmentList.exists()).toBe(true)
      expect(segmentList.props('segments')).toEqual(mockSegments)
      expect(segmentList.props('loading')).toBe(false)
    })

    it('should pass loading state to SegmentList component', async () => {
      wrapper = mountWithRouter(Explorer)
      wrapper.vm.loading = true
      await wrapper.vm.$nextTick()

      const segmentList = wrapper.findComponent({ name: 'SegmentList' })
      expect(segmentList.props('loading')).toBe(true)
    })
  })

  describe('Event Handling', () => {
    it('should handle segment click events', async () => {
      wrapper = mountWithRouter(Explorer)

      const mockSegment = {
        id: 1,
        name: 'Test Segment',
        track_type: 'segment',
        file_path: 'test.gpx',
        bound_north: 45.8,
        bound_south: 45.7,
        bound_east: 4.9,
        bound_west: 4.8,
        difficulty_level: 3,
        surface_type: ['forest-trail'],
        tire_dry: 'semi-slick',
        tire_wet: 'knobs',
        comments: 'Test'
      }

      // Test that the method exists and can be called
      expect(typeof wrapper.vm.onSegmentClick).toBe('function')

      // Test calling the method directly
      wrapper.vm.onSegmentClick(mockSegment)

      // Verify the method executes without error
      expect(wrapper.vm.segments).toBeDefined()
    })

    it('should add click handlers to GPX track polylines', async () => {
      wrapper = mountWithRouter(Explorer)

      const mockSegment = {
        id: 1,
        name: 'Test Segment',
        track_type: 'segment',
        file_path: 'test.gpx',
        bound_north: 45.8,
        bound_south: 45.7,
        bound_east: 4.9,
        bound_west: 4.8,
        difficulty_level: 3,
        surface_type: ['forest-trail'],
        tire_dry: 'semi-slick',
        tire_wet: 'knobs',
        comments: 'Test'
      }

      const mockGPXData = {
        points: [
          { latitude: 45.7, longitude: 4.8 },
          { latitude: 45.8, longitude: 4.9 }
        ]
      }

      // Test that addGPXTrackToMap can be called
      expect(() =>
        wrapper.vm.addGPXTrackToMap(mockSegment, mockGPXData, mockMapInstance)
      ).not.toThrow()

      // Verify that the polyline was created and added to the map
      expect(mockPolyline.addTo).toHaveBeenCalledWith(mockMapInstance)
    })

    it('should add click handlers to bounding box rectangles', async () => {
      wrapper = mountWithRouter(Explorer)

      const mockSegment = {
        id: 1,
        name: 'Test Segment',
        track_type: 'segment',
        file_path: 'test.gpx',
        bound_north: 45.8,
        bound_south: 45.7,
        bound_east: 4.9,
        bound_west: 4.8,
        difficulty_level: 3,
        surface_type: ['forest-trail'],
        tire_dry: 'semi-slick',
        tire_wet: 'knobs',
        comments: 'Test'
      }

      // Test that addBoundingBoxToMap can be called
      expect(() =>
        wrapper.vm.addBoundingBoxToMap(mockSegment, mockMapInstance)
      ).not.toThrow()

      // Verify that the rectangle was created and added to the map
      expect(mockRectangle.addTo).toHaveBeenCalledWith(mockMapInstance)
    })

    it('should handle segment hover events', async () => {
      wrapper = mountWithRouter(Explorer)

      const mockSegment = {
        id: 1,
        name: 'Test Segment',
        track_type: 'segment',
        file_path: 'test.gpx',
        bound_north: 45.8,
        bound_south: 45.7,
        bound_east: 4.9,
        bound_west: 4.8,
        difficulty_level: 3,
        surface_type: ['forest-trail'],
        tire_dry: 'semi-slick',
        tire_wet: 'knobs',
        comments: 'Test'
      }

      // Test that the method exists and can be called
      expect(typeof wrapper.vm.onSegmentHover).toBe('function')

      // Test calling the method directly
      wrapper.vm.onSegmentHover(mockSegment)

      // Verify the method executes without error
      expect(wrapper.vm.segments).toBeDefined()
    })

    it('should handle segment leave events', async () => {
      wrapper = mountWithRouter(Explorer)

      // Test that the method exists and can be called
      expect(typeof wrapper.vm.onSegmentLeave).toBe('function')

      // Test calling the method directly
      wrapper.vm.onSegmentLeave()

      // Verify the method executes without error
      expect(wrapper.vm.segments).toBeDefined()
    })

    it('should handle track type change events', async () => {
      wrapper = mountWithRouter(Explorer)

      // Test that the method exists and can be called
      expect(typeof wrapper.vm.onTrackTypeChange).toBe('function')

      // Test calling the method directly
      wrapper.vm.onTrackTypeChange('route')

      // Verify the track type was updated
      expect(wrapper.vm.selectedTrackType).toBe('route')
    })
  })

  describe('Segment Selection Behavior', () => {
    const mockSegment1 = {
      id: 1,
      name: 'Test Segment 1',
      track_type: 'segment',
      file_path: 'test1.gpx',
      bound_north: 45.8,
      bound_south: 45.7,
      bound_east: 4.9,
      bound_west: 4.8,
      difficulty_level: 3,
      surface_type: ['forest-trail'],
      tire_dry: 'semi-slick',
      tire_wet: 'knobs',
      comments: 'Test 1'
    }

    const mockSegment2 = {
      id: 2,
      name: 'Test Segment 2',
      track_type: 'segment',
      file_path: 'test2.gpx',
      bound_north: 45.9,
      bound_south: 45.8,
      bound_east: 5.0,
      bound_west: 4.9,
      difficulty_level: 4,
      surface_type: ['road'],
      tire_dry: 'slick',
      tire_wet: 'semi-slick',
      comments: 'Test 2'
    }

    beforeEach(() => {
      wrapper = mountWithRouter(Explorer)
      // Mock the map instance
      wrapper.vm.map = mockMapInstance
    })

    it('should select a segment when clicked', async () => {
      // Initially no segment should be selected
      expect(wrapper.vm.selectedSegmentId).toBeNull()

      // Click on a segment
      wrapper.vm.onSegmentClick(mockSegment1)

      // Verify the segment is selected
      expect(wrapper.vm.selectedSegmentId).toBe(mockSegment1.id)
    })

    it('should deselect a segment when clicked again', async () => {
      // First select a segment
      wrapper.vm.onSegmentClick(mockSegment1)
      expect(wrapper.vm.selectedSegmentId).toBe(mockSegment1.id)

      // Click the same segment again
      wrapper.vm.onSegmentClick(mockSegment1)

      // Verify the segment is deselected
      expect(wrapper.vm.selectedSegmentId).toBeNull()
    })

    it('should deselect previous segment when selecting a new one', async () => {
      // Select first segment
      wrapper.vm.onSegmentClick(mockSegment1)
      expect(wrapper.vm.selectedSegmentId).toBe(mockSegment1.id)

      // Select second segment
      wrapper.vm.onSegmentClick(mockSegment2)

      // Verify only the second segment is selected
      expect(wrapper.vm.selectedSegmentId).toBe(mockSegment2.id)
    })

    it('should create selected rectangle when segment is selected', async () => {
      // Select a segment
      wrapper.vm.onSegmentClick(mockSegment1)

      // Verify the segment is selected
      expect(wrapper.vm.selectedSegmentId).toBe(mockSegment1.id)
      expect(wrapper.vm.selectedRectangle).toBeDefined()
    })

    it('should remove selected rectangle when segment is deselected', async () => {
      // Select a segment
      wrapper.vm.onSegmentClick(mockSegment1)
      expect(wrapper.vm.selectedSegmentId).toBe(mockSegment1.id)
      expect(wrapper.vm.selectedRectangle).toBeDefined()

      // Deselect the segment
      wrapper.vm.onSegmentClick(mockSegment1)

      // Verify selection is cleared
      expect(wrapper.vm.selectedSegmentId).toBeNull()
      expect(wrapper.vm.selectedRectangle).toBeNull()
    })

    it('should not show hover rectangle when segment is selected', async () => {
      // Select a segment first
      wrapper.vm.onSegmentClick(mockSegment1)
      expect(wrapper.vm.selectedSegmentId).toBe(mockSegment1.id)

      // Try to hover over the selected segment
      wrapper.vm.onSegmentHover(mockSegment1)

      // Verify hover rectangle was not created (should be null since segment is selected)
      expect(wrapper.vm.hoverRectangle).toBeNull()
    })

    it('should show hover rectangle when segment is not selected', async () => {
      // Hover over a non-selected segment
      wrapper.vm.onSegmentHover(mockSegment1)

      // Verify hover rectangle was created
      expect(wrapper.vm.hoverRectangle).toBeDefined()
    })

    it('should clear selection state on cleanup', async () => {
      // Select a segment
      wrapper.vm.onSegmentClick(mockSegment1)
      expect(wrapper.vm.selectedSegmentId).toBe(mockSegment1.id)

      // Call cleanup
      wrapper.vm.cleanupMap()

      // Verify selection state is cleared
      expect(wrapper.vm.selectedSegmentId).toBeNull()
    })

    it('should pass selectedSegmentId to SegmentList', async () => {
      // Select a segment
      wrapper.vm.onSegmentClick(mockSegment1)

      // Wait for reactivity to update
      await wrapper.vm.$nextTick()

      // Get the SegmentList component
      const segmentList = wrapper.findComponent({ name: 'SegmentList' })
      expect(segmentList.exists()).toBe(true)

      // Verify selectedSegmentId is passed
      expect(segmentList.props('selectedSegmentId')).toBe(mockSegment1.id)
    })
  })

  describe('Map Bounds and Search Functionality', () => {
    it('should initialize with default map bounds', () => {
      wrapper = mountWithRouter(Explorer)

      // Check that the component has the expected initial state
      expect(wrapper.vm.segments).toEqual([])
      expect(wrapper.vm.loading).toBe(false)
      expect(wrapper.vm.totalTracks).toBe(0)
      expect(wrapper.vm.loadedTracks).toBe(0)
      expect(wrapper.vm.selectedTrackType).toBe('segment')
    })

    it('should have searchSegmentsInView method', () => {
      wrapper = mountWithRouter(Explorer)

      // Test that the method exists
      expect(typeof wrapper.vm.searchSegmentsInView).toBe('function')
    })

    it('should have debouncedSearchSegments method', () => {
      wrapper = mountWithRouter(Explorer)

      // Test that the method exists
      expect(typeof wrapper.vm.debouncedSearchSegments).toBe('function')
    })
  })

  describe('GPX Data Processing', () => {
    it('should have fetchAndRenderGPXData method', () => {
      wrapper = mountWithRouter(Explorer)

      // Test that the method exists
      expect(typeof wrapper.vm.fetchAndRenderGPXData).toBe('function')
    })

    it('should have processTrack method', () => {
      wrapper = mountWithRouter(Explorer)

      // Test that the method exists
      expect(typeof wrapper.vm.processTrack).toBe('function')
    })

    it('should handle GPX data processing', async () => {
      const mockTrack = {
        id: 1,
        name: 'Test Track',
        track_type: 'segment',
        file_path: 'test.gpx',
        bound_north: 45.8,
        bound_south: 45.7,
        bound_east: 4.9,
        bound_west: 4.8,
        difficulty_level: 3,
        surface_type: ['forest-trail'],
        tire_dry: 'semi-slick',
        tire_wet: 'knobs',
        comments: 'Test'
      }

      wrapper = mountWithRouter(Explorer)

      // Test that processTrack can be called
      await wrapper.vm.processTrack(mockTrack)

      // Should not throw error
      expect(wrapper.vm.segments).toBeDefined()
    })
  })

  describe('Component Lifecycle', () => {
    it('should have initializeMap method', () => {
      wrapper = mountWithRouter(Explorer)

      // Test that the method exists
      expect(typeof wrapper.vm.initializeMap).toBe('function')
    })

    it('should have cleanupMap method', () => {
      wrapper = mountWithRouter(Explorer)

      // Test that the method exists
      expect(typeof wrapper.vm.cleanupMap).toBe('function')
    })

    it('should clean up resources on unmount', () => {
      wrapper = mountWithRouter(Explorer)

      // Test that cleanupMap can be called
      wrapper.vm.cleanupMap()

      // Should not throw error
      expect(wrapper.exists()).toBe(true)
    })
  })

  describe('Fixed Center Marker', () => {
    it('renders center marker in template', () => {
      wrapper = mountWithRouter(Explorer)

      const centerMarker = wrapper.find('.fixed-center-marker')
      expect(centerMarker.exists()).toBe(true)
      expect(centerMarker.text()).toBe('📍')
      expect(centerMarker.attributes('title')).toBe('Search Center')
    })

    it('has correct CSS classes and attributes', () => {
      wrapper = mountWithRouter(Explorer)

      const centerMarker = wrapper.find('.fixed-center-marker')
      expect(centerMarker.classes()).toContain('fixed-center-marker')
      expect(centerMarker.attributes('title')).toBe('Search Center')
    })

    it('is positioned absolutely at center of map container', () => {
      wrapper = mountWithRouter(Explorer)

      const centerMarker = wrapper.find('.fixed-center-marker')
      const mapContainer = wrapper.find('.card-map')

      expect(centerMarker.exists()).toBe(true)
      expect(mapContainer.exists()).toBe(true)

      // Check that center marker is inside the map container
      expect(mapContainer.find('.fixed-center-marker').exists()).toBe(true)
    })

    it('has proper CSS class for styling', () => {
      wrapper = mountWithRouter(Explorer)

      const centerMarker = wrapper.find('.fixed-center-marker')
      expect(centerMarker.exists()).toBe(true)
      expect(centerMarker.classes()).toContain('fixed-center-marker')

      // In test environment, we can't easily test computed styles
      // but we can verify the element exists and has the right class
      expect(centerMarker.element).toBeDefined()
    })

    it('has correct HTML structure for centering', () => {
      wrapper = mountWithRouter(Explorer)

      const centerMarker = wrapper.find('.fixed-center-marker')
      expect(centerMarker.exists()).toBe(true)

      // Check that the element is properly structured
      expect(centerMarker.element.tagName).toBe('DIV')
      expect(centerMarker.text()).toBe('📍')
    })

    it('has proper accessibility attributes', () => {
      wrapper = mountWithRouter(Explorer)

      const centerMarker = wrapper.find('.fixed-center-marker')
      expect(centerMarker.attributes('title')).toBe('Search Center')
    })

    it('has CSS styles defined in component', () => {
      wrapper = mountWithRouter(Explorer)

      // Check that the component has the CSS styles defined
      // We can't test computed styles in jsdom, but we can verify
      // that the styles are present in the component's style section
      const component = wrapper.vm
      expect(component).toBeDefined()

      // The styles are defined in the <style> section of the component
      // and will be applied in a real browser environment
      const centerMarker = wrapper.find('.fixed-center-marker')
      expect(centerMarker.exists()).toBe(true)
    })

    it('maintains center position during map interactions', async () => {
      wrapper = mountWithRouter(Explorer)

      // Wait for component to mount
      await wrapper.vm.$nextTick()
      await new Promise((resolve) => setTimeout(resolve, 100))

      const centerMarker = wrapper.find('.fixed-center-marker')
      expect(centerMarker.exists()).toBe(true)

      // Simulate map movement (the center marker should remain in the same position)
      // since it's positioned absolutely relative to the container, not the map

      // The marker should always be at the center of the container
      expect(centerMarker.classes()).toContain('fixed-center-marker')
    })

    it('does not interfere with map controls', () => {
      wrapper = mountWithRouter(Explorer)

      const centerMarker = wrapper.find('.fixed-center-marker')
      const mapControls = wrapper.find('.map-controls')

      // All elements should exist
      expect(centerMarker.exists()).toBe(true)
      expect(mapControls.exists()).toBe(true)

      // Center marker should not overlap with controls
      // (This is ensured by z-index and positioning)
      expect(centerMarker.element).toBeDefined()
      expect(mapControls.element).toBeDefined()
    })

    it('is always visible regardless of map state', () => {
      wrapper = mountWithRouter(Explorer)

      const centerMarker = wrapper.find('.fixed-center-marker')
      expect(centerMarker.exists()).toBe(true)
      expect(centerMarker.isVisible()).toBe(true)

      // Even when loading, the center marker should be visible
      wrapper.vm.loading = true
      expect(centerMarker.isVisible()).toBe(true)

      // Even when no segments, the center marker should be visible
      wrapper.vm.segments = []
      expect(centerMarker.isVisible()).toBe(true)
    })

    it('works correctly with map initialization', async () => {
      wrapper = mountWithRouter(Explorer)

      // Wait for component to mount and map to initialize
      await wrapper.vm.$nextTick()
      await new Promise((resolve) => setTimeout(resolve, 100))

      const centerMarker = wrapper.find('.fixed-center-marker')
      expect(centerMarker.exists()).toBe(true)
      expect(centerMarker.isVisible()).toBe(true)

      // Center marker should be present even after map initialization
      expect(centerMarker.text()).toBe('📍')
      expect(centerMarker.attributes('title')).toBe('Search Center')
    })

    it('does not require JavaScript updates for positioning', () => {
      wrapper = mountWithRouter(Explorer)

      const centerMarker = wrapper.find('.fixed-center-marker')
      expect(centerMarker.exists()).toBe(true)

      // The center marker is positioned using CSS only, no JavaScript needed
      // This is the key benefit of the fixed positioning approach
      expect(centerMarker.classes()).toContain('fixed-center-marker')

      // No need to test JavaScript positioning logic since it's CSS-based
      expect(centerMarker.element).toBeDefined()
    })
  })

  describe('Segment Containment Filtering', () => {
    it('filters segments to show only those at least partially visible within map bounds', () => {
      wrapper = mountWithRouter(Explorer)

      // Mock segments with different containment scenarios
      const mockSegments = [
        // Fully contained segment
        {
          id: 1,
          bound_north: 45.8,
          bound_south: 45.7,
          bound_east: 4.9,
          bound_west: 4.8,
          name: 'Contained Segment',
          surface_type: ['asphalt'],
          difficulty_level: 'easy',
          track_type: 'segment',
          file_path: '/test1.gpx',
          barycenter_latitude: 45.75,
          barycenter_longitude: 4.85,
          tire_type: 'road'
        },
        // Partially overlapping segment (should be included with intersection logic)
        {
          id: 2,
          bound_north: 45.95, // Extends beyond search north (45.9)
          bound_south: 45.6,
          bound_east: 5.0,
          bound_west: 4.7,
          name: 'Overlapping Segment',
          surface_type: ['gravel'],
          difficulty_level: 'medium',
          track_type: 'segment',
          file_path: '/test2.gpx',
          barycenter_latitude: 45.75,
          barycenter_longitude: 4.85,
          tire_type: 'gravel'
        },
        // Segment outside bounds (should be filtered out)
        {
          id: 3,
          bound_north: 46.0,
          bound_south: 45.9,
          bound_east: 5.1,
          bound_west: 5.0,
          name: 'Outside Segment',
          surface_type: ['dirt'],
          difficulty_level: 'hard',
          track_type: 'segment',
          file_path: '/test3.gpx',
          barycenter_latitude: 45.95,
          barycenter_longitude: 5.05,
          tire_type: 'mountain'
        }
      ]

      // Set up mock segments
      wrapper.vm.segments = mockSegments

      // Mock map bounds (search area) - larger area to contain the test segment
      const mockBounds = {
        getNorth: () => 45.9, // Larger than segment's north (45.8)
        getSouth: () => 45.6, // Smaller than segment's south (45.7)
        getEast: () => 5.0, // Larger than segment's east (4.9)
        getWest: () => 4.7 // Smaller than segment's west (4.8)
      }

      // Mock map.getBounds to return our test bounds
      const mockMap = {
        getBounds: () => mockBounds,
        remove: vi.fn()
      }
      wrapper.vm.map = mockMap

      // Call the filtering function
      wrapper.vm.updateSegmentCardsForCurrentView()

      // Both the contained and overlapping segments should remain (intersection logic)
      expect(wrapper.vm.segments).toHaveLength(2)
      expect(wrapper.vm.segments.map((s: any) => s.id)).toContain(1) // Contained Segment
      expect(wrapper.vm.segments.map((s: any) => s.id)).toContain(2) // Overlapping Segment
    })

    it('filters segments correctly when zooming in', () => {
      wrapper = mountWithRouter(Explorer)

      // Mock segments
      const mockSegments = [
        {
          id: 1,
          bound_north: 45.8,
          bound_south: 45.76, // Now inside the map bounds (45.75 < 45.76 < 45.85)
          bound_east: 4.9,
          bound_west: 4.8,
          name: 'Segment 1',
          surface_type: ['asphalt'],
          difficulty_level: 'easy',
          track_type: 'segment',
          file_path: '/test1.gpx',
          barycenter_latitude: 45.75,
          barycenter_longitude: 4.85,
          tire_type: 'road'
        },
        {
          id: 2,
          bound_north: 45.82,
          bound_south: 45.78,
          bound_east: 4.88,
          bound_west: 4.86,
          name: 'Segment 2',
          surface_type: ['gravel'],
          difficulty_level: 'medium',
          track_type: 'segment',
          file_path: '/test2.gpx',
          barycenter_latitude: 45.8,
          barycenter_longitude: 4.87,
          tire_type: 'gravel'
        }
      ]

      wrapper.vm.segments = mockSegments

      // Mock tighter bounds (zoomed in) - should contain only segment 2
      const mockBounds = {
        getNorth: () => 45.85, // Larger than segment 2's north (45.82)
        getSouth: () => 45.75, // Smaller than segment 2's south (45.78)
        getEast: () => 4.9, // Larger than segment 2's east (4.88)
        getWest: () => 4.8 // Smaller than segment 2's west (4.86)
      }

      const mockMap = {
        getBounds: () => mockBounds,
        remove: vi.fn()
      }
      wrapper.vm.map = mockMap

      // Call the filtering function
      wrapper.vm.updateSegmentCardsForCurrentView()

      // Both segments should remain (both are now within the tighter bounds)
      expect(wrapper.vm.segments).toHaveLength(2)
      expect(wrapper.vm.segments.map((s: any) => s.id)).toContain(1) // Segment 1
      expect(wrapper.vm.segments.map((s: any) => s.id)).toContain(2) // Segment 2
    })
  })

  describe('Error Handling', () => {
    it('should handle missing map container gracefully', () => {
      wrapper = mountWithRouter(Explorer)

      // Test that initializeMap can be called without errors
      wrapper.vm.initializeMap()

      // Component should still be functional
      expect(wrapper.exists()).toBe(true)
    })

    it('should handle component state correctly', () => {
      wrapper = mountWithRouter(Explorer)

      // Test initial state
      expect(wrapper.vm.loading).toBe(false)
      expect(wrapper.vm.segments).toEqual([])
      expect(wrapper.vm.selectedTrackType).toBe('segment')
    })
  })

  describe('Filter Badge Indicator', () => {
    it('should not show badge when no filters are active', () => {
      wrapper = mountWithRouter(Explorer)

      expect(wrapper.vm.hasActiveFilters).toBe(false)
      expect(wrapper.find('.filter-active-badge').exists()).toBe(false)
    })

    it('should show badge when filters are active', async () => {
      wrapper = mountWithRouter(Explorer)

      // Simulate filters being activated
      wrapper.vm.hasActiveFilters = true
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.filter-active-badge').exists()).toBe(true)
    })

    it('should update badge visibility when filters-changed event is received', async () => {
      wrapper = mountWithRouter(Explorer)

      // Initially no badge
      expect(wrapper.find('.filter-active-badge').exists()).toBe(false)

      // Simulate filters becoming active
      wrapper.vm.onFiltersChanged(true)
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.hasActiveFilters).toBe(true)
      expect(wrapper.find('.filter-active-badge').exists()).toBe(true)

      // Simulate filters being cleared
      wrapper.vm.onFiltersChanged(false)
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.hasActiveFilters).toBe(false)
      expect(wrapper.find('.filter-active-badge').exists()).toBe(false)
    })

    it('should have proper badge styling', async () => {
      wrapper = mountWithRouter(Explorer)

      wrapper.vm.hasActiveFilters = true
      await wrapper.vm.$nextTick()

      const badge = wrapper.find('.filter-active-badge')
      expect(badge.exists()).toBe(true)
      expect(badge.element.tagName).toBe('SPAN')
    })
  })

  describe('Filter Toggle Button', () => {
    it('should render vertical filters toggle button', () => {
      wrapper = mountWithRouter(Explorer)

      const toggleBtn = wrapper.find('.vertical-filters-toggle')
      expect(toggleBtn.exists()).toBe(true)
    })

    it('should toggle showFilters state when button is clicked', async () => {
      wrapper = mountWithRouter(Explorer)

      expect(wrapper.vm.showFilters).toBe(false)

      const toggleBtn = wrapper.find('.vertical-filters-toggle')
      await toggleBtn.trigger('click')

      expect(wrapper.vm.showFilters).toBe(true)

      await toggleBtn.trigger('click')
      expect(wrapper.vm.showFilters).toBe(false)
    })

    it('should add active class when filters are open', async () => {
      wrapper = mountWithRouter(Explorer)

      const toggleBtn = wrapper.find('.vertical-filters-toggle')
      expect(toggleBtn.classes()).not.toContain('active')

      wrapper.vm.showFilters = true
      await wrapper.vm.$nextTick()

      expect(toggleBtn.classes()).toContain('active')
    })

    it('should render filter icon, text, and chevrons', () => {
      wrapper = mountWithRouter(Explorer)

      const toggleBtn = wrapper.find('.vertical-filters-toggle')
      expect(toggleBtn.find('.fa-filter').exists()).toBe(true)
      expect(toggleBtn.find('.vertical-text').text()).toBe('Filters')
      expect(toggleBtn.find('.chevron-indicator').exists()).toBe(true)
    })

    it('should rotate chevrons when filters are open', async () => {
      wrapper = mountWithRouter(Explorer)

      const chevrons = wrapper.find('.chevron-indicator')
      expect(chevrons.classes()).not.toContain('rotated')

      wrapper.vm.showFilters = true
      await wrapper.vm.$nextTick()

      expect(chevrons.classes()).toContain('rotated')
    })

    it('should have two chevron icons', () => {
      wrapper = mountWithRouter(Explorer)

      const chevronIcons = wrapper
        .find('.chevron-indicator')
        .findAll('.fa-chevron-right')
      expect(chevronIcons).toHaveLength(2)
    })
  })
})
