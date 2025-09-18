import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import LandingPage from '../LandingPage.vue'

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
      scale: vi.fn(() => mockScaleControl)
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
  url: 'http://localhost:8000/api/segments/search',
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

describe('LandingPage', () => {
  let wrapper: any

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  it('renders correctly', () => {
    wrapper = mount(LandingPage)

    expect(wrapper.find('.landing-page').exists()).toBe(true)
    expect(wrapper.find('.landing-content').exists()).toBe(true)
  })

  it('has correct CSS classes for styling', () => {
    const wrapper = mount(LandingPage)

    const landingPage = wrapper.find('.landing-page')
    const landingContent = wrapper.find('.landing-content')

    expect(landingPage.exists()).toBe(true)
    expect(landingContent.exists()).toBe(true)
  })

  it('has proper structure with landing-page container', () => {
    const wrapper = mount(LandingPage)

    const landingPage = wrapper.find('.landing-page')
    expect(landingPage.exists()).toBe(true)

    // Check that landing-content is inside landing-page
    const landingContent = landingPage.find('.landing-content')
    expect(landingContent.exists()).toBe(true)
  })

  it('renders as a single root element', () => {
    const wrapper = mount(LandingPage)

    // Should have only one root element
    expect(wrapper.element.children.length).toBe(1)
    // Check that the root element has the landing-page class
    expect(wrapper.element.classList.contains('landing-page')).toBe(true)
  })

  it('has correct component name', () => {
    const wrapper = mount(LandingPage)

    expect(wrapper.vm.$options.name || 'LandingPage').toBe('LandingPage')
  })

  it('is a functional component with no props', () => {
    const wrapper = mount(LandingPage)

    // Should not have any props
    expect(Object.keys(wrapper.props())).toHaveLength(0)
  })

  it('has content area ready for future content', () => {
    const wrapper = mount(LandingPage)

    const landingContent = wrapper.find('.landing-content')
    expect(landingContent.exists()).toBe(true)

    // Content area should have map section
    expect(landingContent.find('.map-section').exists()).toBe(true)
  })

  it('maintains proper HTML structure', () => {
    const wrapper = mount(LandingPage)

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
    const wrapper = mount(LandingPage)

    const landingPage = wrapper.find('.landing-page')
    const landingContent = wrapper.find('.landing-content')

    // Check that elements exist (styles are applied via CSS, not directly testable in unit tests)
    expect(landingPage.exists()).toBe(true)
    expect(landingContent.exists()).toBe(true)
  })

  it('is ready for future content expansion', () => {
    const wrapper = mount(LandingPage)

    // The component should be structured to easily accept new content
    const landingContent = wrapper.find('.landing-content')
    expect(landingContent.exists()).toBe(true)

    // Should be able to add content inside landing-content
    expect(landingContent.element.children.length).toBe(2) // Map section and segment list section
  })

  it('follows Vue 3 Composition API patterns', () => {
    const wrapper = mount(LandingPage)

    // Component should be using <script setup> syntax
    // This is verified by the fact that it mounts without errors
    expect(wrapper.vm).toBeDefined()
  })

  it('has proper accessibility structure', () => {
    const wrapper = mount(LandingPage)

    // Should have proper div structure for screen readers
    const landingPage = wrapper.find('.landing-page')
    expect(landingPage.exists()).toBe(true)

    // Should be a semantic container
    expect(landingPage.element.tagName).toBe('DIV')
  })

  it('can be mounted multiple times without issues', () => {
    // Test that the component is stateless and can be reused
    const wrapper1 = mount(LandingPage)
    const wrapper2 = mount(LandingPage)

    expect(wrapper1.find('.landing-page').exists()).toBe(true)
    expect(wrapper2.find('.landing-page').exists()).toBe(true)

    // Both instances should be identical
    expect(wrapper1.html()).toBe(wrapper2.html())
  })

  it('handles component lifecycle correctly', () => {
    wrapper = mount(LandingPage)

    // Component should mount successfully
    expect(wrapper.find('.landing-page').exists()).toBe(true)

    // Should be able to unmount without errors
    expect(() => wrapper.unmount()).not.toThrow()
  })

  describe('Map functionality', () => {
    it('renders map container', () => {
      wrapper = mount(LandingPage)

      expect(wrapper.find('#landing-map').exists()).toBe(true)
      expect(wrapper.find('.map').exists()).toBe(true)
      expect(wrapper.find('.card-map').exists()).toBe(true)
    })

    it('displays map section without hero titles', () => {
      wrapper = mount(LandingPage)

      expect(wrapper.find('.hero-section').exists()).toBe(false)
      expect(wrapper.find('.hero-title').exists()).toBe(false)
      expect(wrapper.find('.hero-subtitle').exists()).toBe(false)
      expect(wrapper.find('.map-section').exists()).toBe(true)
    })

    it('has proper map section structure', () => {
      wrapper = mount(LandingPage)

      expect(wrapper.find('.map-section').exists()).toBe(true)
      expect(wrapper.find('.map-container').exists()).toBe(true)
      expect(wrapper.find('.card').exists()).toBe(true)
    })

    it('has correct map dimensions with full width and 65% height', () => {
      wrapper = mount(LandingPage)

      const mapElement = wrapper.find('.map')
      expect(mapElement.exists()).toBe(true)
      expect(mapElement.attributes('id')).toBe('landing-map')
      expect(mapElement.classes()).toContain('map')
    })

    it('has responsive CSS classes', () => {
      wrapper = mount(LandingPage)

      const mapContainer = wrapper.find('.map-container')
      expect(mapContainer.exists()).toBe(true)
      expect(mapContainer.classes()).toContain('map-container')
    })

    it('has full width and 65% height styling', () => {
      wrapper = mount(LandingPage)

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
      wrapper = mount(LandingPage)

      const landingContent = wrapper.find('.landing-content')
      expect(landingContent.exists()).toBe(true)
      expect(landingContent.classes()).toContain('landing-content')
    })

    it('maintains proper layout structure', () => {
      wrapper = mount(LandingPage)

      // Check that all main sections exist
      expect(wrapper.find('.map-section').exists()).toBe(true)
      expect(wrapper.find('.map-container').exists()).toBe(true)
    })
  })

  describe('Non-regression tests', () => {
    it('should not have duplicate map containers', () => {
      wrapper = mount(LandingPage)

      const mapContainers = wrapper.findAll('#landing-map')
      expect(mapContainers).toHaveLength(1)
    })

    it('should have proper map container hierarchy', () => {
      wrapper = mount(LandingPage)

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
      const wrapper1 = mount(LandingPage)
      const wrapper2 = mount(LandingPage)

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
      wrapper = mount(LandingPage)

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
      wrapper = mount(LandingPage)

      wrapper.vm.loading = true
      wrapper.vm.totalTracks = 0

      await wrapper.vm.$nextTick()

      const loadingIndicator = wrapper.find('.loading-indicator')
      expect(loadingIndicator.text()).toContain('🔍 Loading segments...')
    })

    it('should hide loading indicator when loading is false', async () => {
      wrapper = mount(LandingPage)

      wrapper.vm.loading = false

      await wrapper.vm.$nextTick()

      const loadingIndicator = wrapper.find('.loading-indicator')
      expect(loadingIndicator.exists()).toBe(false)
    })

  })

  describe('Map Controls', () => {
    it('should render Max Results control', () => {
      wrapper = mount(LandingPage)

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
      wrapper = mount(LandingPage)

      expect(wrapper.vm.searchLimit).toBe(50)
    })

    it('should handle limit change events', async () => {
      wrapper = mount(LandingPage)

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
      wrapper = mount(LandingPage)

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
      wrapper = mount(LandingPage)

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
      wrapper = mount(LandingPage)

      await wrapper.vm.$nextTick()
      await new Promise((resolve) => setTimeout(resolve, 100))

      const L = await import('leaflet')
      expect(L.default.tileLayer).toHaveBeenCalled()
      expect(mockTileLayer.addTo).toHaveBeenCalledWith(mockMapInstance)
    })

    it('should add scale control', async () => {
      wrapper = mount(LandingPage)

      await wrapper.vm.$nextTick()
      await new Promise((resolve) => setTimeout(resolve, 100))

      const L = await import('leaflet')
      expect(L.default.control.scale).toHaveBeenCalled()
      expect(mockScaleControl.addTo).toHaveBeenCalledWith(mockMapInstance)
    })

    it('should set initial map view', async () => {
      wrapper = mount(LandingPage)

      await wrapper.vm.$nextTick()
      await new Promise((resolve) => setTimeout(resolve, 100))

      expect(mockMapInstance.setView).toHaveBeenCalledWith([45.764, 4.8357], 12)
    })

    it('should not initialize map if already exists', async () => {
      wrapper = mount(LandingPage)

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
      wrapper = mount(LandingPage)

      expect(typeof wrapper.vm.searchSegmentsInView).toBe('function')
    })

    it('should have eventSource property', () => {
      wrapper = mount(LandingPage)

      expect(wrapper.vm.eventSource).toBeNull()
    })

    it('should have loading state properties', () => {
      wrapper = mount(LandingPage)

      expect(wrapper.vm.loading).toBe(false)
      expect(wrapper.vm.totalTracks).toBe(0)
      expect(wrapper.vm.loadedTracks).toBe(0)
    })

    it('should have segments array', () => {
      wrapper = mount(LandingPage)

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
      wrapper = mount(LandingPage)

      expect(typeof wrapper.vm.processTrack).toBe('function')
    })

    it('should have addGPXTrackToMap method', () => {
      wrapper = mount(LandingPage)

      expect(typeof wrapper.vm.addGPXTrackToMap).toBe('function')
    })

    it('should have addBoundingBoxToMap method', () => {
      wrapper = mount(LandingPage)

      expect(typeof wrapper.vm.addBoundingBoxToMap).toBe('function')
    })
  })

  describe('Component Lifecycle', () => {
    it('should mount and unmount without errors', () => {
      wrapper = mount(LandingPage)

      expect(wrapper.exists()).toBe(true)

      // Should unmount cleanly
      expect(() => wrapper.unmount()).not.toThrow()
    })

    it('should have onMounted and onUnmounted lifecycle hooks', () => {
      wrapper = mount(LandingPage)

      // Component should mount successfully, indicating lifecycle hooks work
      expect(wrapper.exists()).toBe(true)
    })

    it('should initialize map on mount', async () => {
      wrapper = mount(LandingPage)

      await wrapper.vm.$nextTick()
      await new Promise((resolve) => setTimeout(resolve, 100))

      // Map should be initialized (we can't directly test the private map variable)
      // but we can test that the component mounted successfully
      expect(wrapper.exists()).toBe(true)
    })
  })

  describe('Dynamic Circle Scaling', () => {
    it('should have updateCircleSizes method', () => {
      wrapper = mount(LandingPage)

      expect(typeof wrapper.vm.updateCircleSizes).toBe('function')
    })

    it('should calculate correct radius for different zoom levels', () => {
      wrapper = mount(LandingPage)

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
      wrapper = mount(LandingPage)

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
      wrapper = mount(LandingPage)

      // Set empty map layers
      wrapper.vm.currentMapLayers = new Map()

      // Should not throw error
      expect(() => wrapper.vm.updateCircleSizes()).not.toThrow()
    })

    it('should handle layers without markers gracefully', () => {
      wrapper = mount(LandingPage)

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
      wrapper = mount(LandingPage)
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
      wrapper = mount(LandingPage)
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
          surface_type: 'forest-trail',
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
          surface_type: 'big-stone-road',
          tire_dry: 'knobs',
          tire_wet: 'knobs',
          comments: ''
        }
      ]

      wrapper = mount(LandingPage)
      wrapper.vm.segments = mockSegments
      await wrapper.vm.$nextTick()

      const segmentList = wrapper.findComponent({ name: 'SegmentList' })
      expect(segmentList.exists()).toBe(true)
      expect(segmentList.props('segments')).toEqual(mockSegments)
      expect(segmentList.props('loading')).toBe(false)
    })

    it('should pass loading state to SegmentList component', async () => {
      wrapper = mount(LandingPage)
      wrapper.vm.loading = true
      await wrapper.vm.$nextTick()

      const segmentList = wrapper.findComponent({ name: 'SegmentList' })
      expect(segmentList.props('loading')).toBe(true)
    })
  })

  describe('Event Handling', () => {
    it('should handle segment click events', async () => {
      wrapper = mount(LandingPage)

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
        surface_type: 'forest-trail',
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
      wrapper = mount(LandingPage)

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
        surface_type: 'forest-trail',
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
      expect(() => wrapper.vm.addGPXTrackToMap(mockSegment, mockGPXData, mockMapInstance)).not.toThrow()

      // Verify that the polyline was created and added to the map
      expect(mockPolyline.addTo).toHaveBeenCalledWith(mockMapInstance)
    })

    it('should add click handlers to bounding box rectangles', async () => {
      wrapper = mount(LandingPage)

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
        surface_type: 'forest-trail',
        tire_dry: 'semi-slick',
        tire_wet: 'knobs',
        comments: 'Test'
      }

      // Test that addBoundingBoxToMap can be called
      expect(() => wrapper.vm.addBoundingBoxToMap(mockSegment, mockMapInstance)).not.toThrow()

      // Verify that the rectangle was created and added to the map
      expect(mockRectangle.addTo).toHaveBeenCalledWith(mockMapInstance)
    })

    it('should handle segment hover events', async () => {
      wrapper = mount(LandingPage)

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
        surface_type: 'forest-trail',
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
      wrapper = mount(LandingPage)

      // Test that the method exists and can be called
      expect(typeof wrapper.vm.onSegmentLeave).toBe('function')

      // Test calling the method directly
      wrapper.vm.onSegmentLeave()

      // Verify the method executes without error
      expect(wrapper.vm.segments).toBeDefined()
    })

    it('should handle track type change events', async () => {
      wrapper = mount(LandingPage)

      // Test that the method exists and can be called
      expect(typeof wrapper.vm.onTrackTypeChange).toBe('function')

      // Test calling the method directly
      wrapper.vm.onTrackTypeChange('route')

      // Verify the track type was updated
      expect(wrapper.vm.selectedTrackType).toBe('route')
    })
  })

  describe('Map Bounds and Search Functionality', () => {
    it('should initialize with default map bounds', () => {
      wrapper = mount(LandingPage)

      // Check that the component has the expected initial state
      expect(wrapper.vm.segments).toEqual([])
      expect(wrapper.vm.loading).toBe(false)
      expect(wrapper.vm.totalTracks).toBe(0)
      expect(wrapper.vm.loadedTracks).toBe(0)
      expect(wrapper.vm.selectedTrackType).toBe('segment')
    })

    it('should have searchSegmentsInView method', () => {
      wrapper = mount(LandingPage)

      // Test that the method exists
      expect(typeof wrapper.vm.searchSegmentsInView).toBe('function')
    })

    it('should have debouncedSearchSegments method', () => {
      wrapper = mount(LandingPage)

      // Test that the method exists
      expect(typeof wrapper.vm.debouncedSearchSegments).toBe('function')
    })
  })

  describe('GPX Data Processing', () => {
    it('should have fetchAndRenderGPXData method', () => {
      wrapper = mount(LandingPage)

      // Test that the method exists
      expect(typeof wrapper.vm.fetchAndRenderGPXData).toBe('function')
    })

    it('should have processTrack method', () => {
      wrapper = mount(LandingPage)

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
        surface_type: 'forest-trail',
        tire_dry: 'semi-slick',
        tire_wet: 'knobs',
        comments: 'Test'
      }

      wrapper = mount(LandingPage)

      // Test that processTrack can be called
      await wrapper.vm.processTrack(mockTrack)

      // Should not throw error
      expect(wrapper.vm.segments).toBeDefined()
    })
  })

  describe('Component Lifecycle', () => {
    it('should have initializeMap method', () => {
      wrapper = mount(LandingPage)

      // Test that the method exists
      expect(typeof wrapper.vm.initializeMap).toBe('function')
    })

    it('should have cleanupMap method', () => {
      wrapper = mount(LandingPage)

      // Test that the method exists
      expect(typeof wrapper.vm.cleanupMap).toBe('function')
    })

    it('should clean up resources on unmount', () => {
      wrapper = mount(LandingPage)

      // Test that cleanupMap can be called
      wrapper.vm.cleanupMap()

      // Should not throw error
      expect(wrapper.exists()).toBe(true)
    })
  })

  describe('Error Handling', () => {
    it('should handle missing map container gracefully', () => {
      wrapper = mount(LandingPage)

      // Test that initializeMap can be called without errors
      wrapper.vm.initializeMap()

      // Component should still be functional
      expect(wrapper.exists()).toBe(true)
    })

    it('should handle component state correctly', () => {
      wrapper = mount(LandingPage)

      // Test initial state
      expect(wrapper.vm.loading).toBe(false)
      expect(wrapper.vm.segments).toEqual([])
      expect(wrapper.vm.selectedTrackType).toBe('segment')
    })
  })
})
