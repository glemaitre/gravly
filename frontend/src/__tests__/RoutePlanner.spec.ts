import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import RoutePlanner from '../components/RoutePlanner.vue'
import { createI18n } from 'vue-i18n'

// Mock Leaflet and leaflet-routing-machine
vi.mock('leaflet', () => ({
  default: {
    map: vi.fn(
      () =>
        ({
          setView: vi.fn(),
          getZoom: vi.fn(() => 14),
          on: vi.fn(),
          off: vi.fn(),
          remove: vi.fn(),
          addLayer: vi.fn(),
          removeLayer: vi.fn(),
          hasLayer: vi.fn(() => false),
          eachLayer: vi.fn(),
          distance: vi.fn(() => 1000),
          fitBounds: vi.fn(),
          getContainer: vi.fn(() => ({
            style: { cursor: 'crosshair' }
          })),
          dragging: {
            enable: vi.fn(),
            disable: vi.fn(),
            enabled: vi.fn(() => true)
          }
        }) as any
    ),
    tileLayer: Object.assign(
      vi.fn(() => ({
        addTo: vi.fn(),
        wms: vi.fn()
      })),
      {
        wms: vi.fn()
      }
    ) as any,
    marker: vi.fn(
      () =>
        ({
          setLatLng: vi.fn(),
          addTo: vi.fn(),
          remove: vi.fn(),
          on: vi.fn(),
          getElement: vi.fn(() => ({
            classList: {
              add: vi.fn(),
              remove: vi.fn(),
              contains: vi.fn(() => false)
            }
          }))
        }) as any
    ),
    polyline: vi.fn(
      () =>
        ({
          setStyle: vi.fn(),
          addTo: vi.fn(),
          remove: vi.fn(),
          on: vi.fn(),
          _path: { style: { zIndex: '1500' } }
        }) as any
    ),
    divIcon: vi.fn(() => ({}) as any),
    latLng: vi.fn((lat: any, lng?: any, alt?: any) => {
      if (typeof lat === 'object' && lat !== null) {
        // Handle object input
        return {
          lat: lat.lat || lat[0],
          lng: lat.lng || lat[1],
          alt: lat.alt || lat[2]
        } as any
      }
      // Handle individual parameters
      return { lat, lng, alt } as any
    }),
    latLngBounds: vi.fn(
      () =>
        ({
          extend: vi.fn()
        }) as any
    ),
    Routing: {
      control: vi.fn(() => ({
        setWaypoints: vi.fn(),
        on: vi.fn(),
        addTo: vi.fn()
      })),
      waypoint: vi.fn(() => ({
        latLng: { lat: 46.860104, lng: 3.978509 }
      })),
      OSRMv1: vi.fn()
    },
    DomEvent: {
      stopPropagation: vi.fn(),
      preventDefault: vi.fn()
    } as any,
    Class: {
      extend: vi.fn()
    } as any,
    Icon: Object.assign(
      {
        Default: {
          prototype: {
            _getIconUrl: vi.fn()
          },
          mergeOptions: vi.fn()
        }
      },
      {
        prototype: {},
        extend: vi.fn(),
        include: vi.fn(),
        mergeOptions: vi.fn(),
        addInitHook: vi.fn(),
        callInitHooks: vi.fn()
      }
    ) as any
  }
}))

vi.mock('leaflet-routing-machine', () => ({
  default: {}
}))

// Mock Chart.js
vi.mock('chart.js', () => ({
  Chart: Object.assign(
    vi.fn(() => ({
      destroy: vi.fn(),
      update: vi.fn(),
      on: vi.fn(),
      register: vi.fn()
    })),
    {
      register: vi.fn()
    }
  ),
  LineController: {},
  LineElement: {},
  PointElement: {},
  LinearScale: {},
  Title: {},
  CategoryScale: {},
  Filler: {},
  Tooltip: {}
}))

// Mock fetch for elevation API
global.fetch = vi.fn()

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
})

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn()
  }))
})

// Create i18n instance
const i18n = createI18n({
  legacy: false,
  locale: 'en',
  fallbackLocale: 'en',
  messages: {
    en: {
      'Clear Map': 'Clear Map',
      Undo: 'Undo',
      Redo: 'Redo',
      'Elevation Profile': 'Elevation Profile'
    }
  }
})

describe('RoutePlanner', () => {
  let wrapper: any

  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock.getItem.mockImplementation((key: string) => {
      switch (key) {
        case 'routePlanner_currentRoute':
          return null
        case 'routePlanner_mapState':
          return null
        default:
          return null
      }
    })

    // Mock successful elevation API response
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            results: [{ elevation: 100 }, { elevation: 150 }, { elevation: 200 }]
          })
      })
    ) as any

    // Set up global L object for leaflet-routing-machine
    global.L = {
      map: vi.fn(
        () =>
          ({
            setView: vi.fn(),
            getZoom: vi.fn(() => 14),
            on: vi.fn(),
            off: vi.fn(),
            remove: vi.fn(),
            addLayer: vi.fn(),
            removeLayer: vi.fn(),
            hasLayer: vi.fn(() => false),
            eachLayer: vi.fn(),
            distance: vi.fn(() => 1000),
            fitBounds: vi.fn(),
            getContainer: vi.fn(() => ({
              style: { cursor: 'crosshair' }
            })),
            dragging: {
              enable: vi.fn(),
              disable: vi.fn(),
              enabled: vi.fn(() => true)
            }
          }) as any
      ),
      tileLayer: Object.assign(
        vi.fn(() => ({
          addTo: vi.fn(),
          wms: vi.fn()
        })),
        {
          wms: vi.fn()
        }
      ) as any,
      marker: vi.fn(
        () =>
          ({
            setLatLng: vi.fn(),
            addTo: vi.fn(),
            remove: vi.fn(),
            on: vi.fn(),
            getElement: vi.fn(() => ({
              classList: {
                add: vi.fn(),
                remove: vi.fn(),
                contains: vi.fn(() => false)
              }
            }))
          }) as any
      ),
      polyline: vi.fn(
        () =>
          ({
            setStyle: vi.fn(),
            addTo: vi.fn(),
            remove: vi.fn(),
            on: vi.fn(),
            _path: { style: { zIndex: '1500' } }
          }) as any
      ),
      divIcon: vi.fn(() => ({}) as any),
      latLng: vi.fn((lat: any, lng?: any, alt?: any) => {
        if (typeof lat === 'object' && lat !== null) {
          // Handle object input
          return {
            lat: lat.lat || lat[0],
            lng: lat.lng || lat[1],
            alt: lat.alt || lat[2]
          } as any
        }
        // Handle individual parameters
        return { lat, lng, alt } as any
      }),
      latLngBounds: vi.fn(
        () =>
          ({
            extend: vi.fn()
          }) as any
      ),
      Routing: {
        control: vi.fn(() => ({
          setWaypoints: vi.fn(),
          on: vi.fn(),
          addTo: vi.fn()
        })),
        waypoint: vi.fn(() => ({
          latLng: { lat: 46.860104, lng: 3.978509 }
        })),
        OSRMv1: vi.fn()
      },
      DomEvent: {
        stopPropagation: vi.fn(),
        preventDefault: vi.fn()
      } as any,
      Class: {
        extend: vi.fn()
      } as any,
      Icon: Object.assign(
        {
          Default: {
            prototype: {
              _getIconUrl: vi.fn()
            },
            mergeOptions: vi.fn()
          }
        },
        {
          prototype: {},
          extend: vi.fn(),
          include: vi.fn(),
          mergeOptions: vi.fn(),
          addInitHook: vi.fn(),
          callInitHooks: vi.fn()
        }
      ) as any
    } as any
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
    vi.restoreAllMocks()
  })

  describe('Component Mounting', () => {
    it('renders correctly', async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()

      expect(wrapper.find('.route-planner').exists()).toBe(true)
      expect(wrapper.find('.map-container').exists()).toBe(true)
      expect(wrapper.find('#route-map').exists()).toBe(true)
      expect(wrapper.find('.elevation-section').exists()).toBe(true)
    })

    it('initializes map on mount', async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()

      // The map should be initialized
      expect(wrapper.vm.map).toBeDefined()
    })

    it('adds CSS classes to body and html on mount', async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()

      expect(document.body.classList.contains('route-planner-active')).toBe(true)
      expect(document.documentElement.classList.contains('route-planner-active')).toBe(
        true
      )
    })
  })

  describe('Map Controls', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('renders map control buttons', () => {
      expect(wrapper.find('.map-controls').exists()).toBe(true)
      expect(wrapper.find('.control-group').exists()).toBe(true)
      expect(wrapper.findAll('.control-btn')).toHaveLength(3)
    })

    it('has clear map button', () => {
      const clearButton = wrapper.find('.control-btn:first-child')
      expect(clearButton.exists()).toBe(true)
      expect(clearButton.find('i').classes()).toContain('fa-trash')
    })

    it('has undo button', () => {
      const undoButton = wrapper.findAll('.control-btn')[1]
      expect(undoButton.exists()).toBe(true)
      expect(undoButton.find('i').classes()).toContain('fa-undo')
    })

    it('has redo button', () => {
      const redoButton = wrapper.findAll('.control-btn')[2]
      expect(redoButton.exists()).toBe(true)
      expect(redoButton.find('i').classes()).toContain('fa-redo')
    })

    it('disables undo/redo buttons initially', () => {
      const undoButton = wrapper.findAll('.control-btn')[1]
      const redoButton = wrapper.findAll('.control-btn')[2]

      expect(undoButton.attributes('disabled')).toBeDefined()
      expect(redoButton.attributes('disabled')).toBeDefined()
    })
  })

  describe('Elevation Section', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('renders elevation section', () => {
      expect(wrapper.find('.elevation-section').exists()).toBe(true)
      expect(wrapper.find('.elevation-toggle').exists()).toBe(true)
    })

    it('shows elevation toggle button', () => {
      const toggle = wrapper.find('.elevation-toggle')
      expect(toggle.find('.elevation-toggle-text').text()).toBe('Elevation Profile')
      expect(toggle.find('i.fa-mountain').exists()).toBe(true)
    })

    it('shows elevation stats in toggle', () => {
      const stats = wrapper.find('.toggle-stats')
      expect(stats.exists()).toBe(true)
      expect(stats.findAll('.toggle-stat')).toHaveLength(3)
    })

    it('toggles elevation section visibility', async () => {
      const toggle = wrapper.find('.elevation-toggle')

      // Initially collapsed
      expect(wrapper.find('.elevation-content').exists()).toBe(false)

      // Click to expand
      await toggle.trigger('click')
      await nextTick()

      expect(wrapper.find('.elevation-content').exists()).toBe(true)
      expect(wrapper.find('.elevation-section').classes()).toContain(
        'elevation-expanded'
      )
    })

    it('shows chart when elevation section is expanded', async () => {
      const toggle = wrapper.find('.elevation-toggle')
      await toggle.trigger('click')
      await nextTick()

      expect(wrapper.find('.elevation-chart').exists()).toBe(true)
      expect(wrapper.find('.chart-container').exists()).toBe(true)
      expect(wrapper.find('.elevation-chart-canvas').exists()).toBe(true)
    })
  })

  describe('Waypoint Management', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('starts with no waypoints', () => {
      expect(wrapper.vm.waypoints).toHaveLength(0)
      expect(wrapper.vm.routeDistance).toBe(0)
    })

    it('calculates route distance when waypoints are added', async () => {
      // Add waypoints directly to test distance calculation
      wrapper.vm.waypoints = [
        { latLng: { lat: 46.860104, lng: 3.978509 } },
        { latLng: { lat: 46.861104, lng: 3.979509 } }
      ]

      wrapper.vm.calculateRouteDistance()

      expect(wrapper.vm.routeDistance).toBeGreaterThan(0)
    })
  })

  describe('Elevation Statistics', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('initializes with zero elevation stats', () => {
      expect(wrapper.vm.elevationStats.totalGain).toBe(0)
      expect(wrapper.vm.elevationStats.totalLoss).toBe(0)
      expect(wrapper.vm.elevationStats.maxElevation).toBe(0)
      expect(wrapper.vm.elevationStats.minElevation).toBe(0)
    })

    it('does not calculate elevation stats without route coordinates', async () => {
      wrapper.vm.actualRouteCoordinates = []

      await wrapper.vm.calculateElevationStats()

      // Should not make API calls
      expect(global.fetch).not.toHaveBeenCalled()
    })
  })

  describe('Chart Marker Functionality', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('hides chart marker when elevation section is closed', () => {
      wrapper.vm.showElevation = false
      wrapper.vm.hideChartMarker()

      expect(wrapper.vm.mapMarker).toBeNull()
      expect(wrapper.vm.currentPosition).toBeNull()
    })

    it('does not show chart marker when elevation section is closed', () => {
      wrapper.vm.showElevation = false
      wrapper.vm.actualRouteCoordinates = [
        { lat: 46.860104, lng: 3.978509 },
        { lat: 46.861104, lng: 3.979509 }
      ]

      const sampledPoints = [
        { lat: 46.860104, lng: 3.978509, distance: 0, elevation: 100 },
        { lat: 46.861104, lng: 3.979509, distance: 1000, elevation: 150 }
      ]

      wrapper.vm.updateCursorPositionFromChart(0, sampledPoints)

      expect(wrapper.vm.mapMarker).toBeNull()
    })
  })

  describe('Route Persistence', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('saves route to localStorage', () => {
      wrapper.vm.waypoints = [
        { latLng: { lat: 46.860104, lng: 3.978509 } },
        { latLng: { lat: 46.861104, lng: 3.979509 } }
      ]

      wrapper.vm.saveCurrentRoute()

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'routePlanner_currentRoute',
        expect.stringContaining('waypoints')
      )
    })

    it('handles invalid saved route gracefully', () => {
      localStorageMock.getItem.mockReturnValue('invalid json')

      expect(() => wrapper.vm.loadSavedRoute()).not.toThrow()
    })
  })

  describe('History Management', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('saves state for undo functionality', () => {
      wrapper.vm.waypoints = [{ latLng: { lat: 46.860104, lng: 3.978509 } }]

      wrapper.vm.saveState()

      expect(wrapper.vm.undoStack).toHaveLength(1)
    })

    it('enables undo button when state is saved', () => {
      wrapper.vm.waypoints = [{ latLng: { lat: 46.860104, lng: 3.978509 } }]

      wrapper.vm.saveState()
      wrapper.vm.updateHistoryButtonStates()

      expect(wrapper.vm.canUndo).toBe(true)
    })
  })

  describe('Error Handling', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('handles elevation API errors gracefully', async () => {
      global.fetch = vi.fn(() => Promise.reject(new Error('API Error')))

      wrapper.vm.actualRouteCoordinates = [
        { lat: 46.860104, lng: 3.978509 },
        { lat: 46.861104, lng: 3.979509 }
      ]

      await wrapper.vm.calculateElevationStats()

      // Should not throw error
      expect(wrapper.vm.elevationStats.totalGain).toBe(0)
    })

    it('handles missing route coordinates gracefully', async () => {
      wrapper.vm.actualRouteCoordinates = []

      await wrapper.vm.calculateElevationStats()

      // Should not make API calls
      expect(global.fetch).not.toHaveBeenCalled()
    })
  })

  describe('Responsive Design', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('has correct CSS classes for styling', () => {
      expect(wrapper.find('.route-planner').exists()).toBe(true)
      expect(wrapper.find('.map-container').exists()).toBe(true)
      expect(wrapper.find('.map').exists()).toBe(true)
      expect(wrapper.find('.elevation-section').exists()).toBe(true)
    })

    it('applies elevation-expanded class when section is open', async () => {
      const toggle = wrapper.find('.elevation-toggle')
      await toggle.trigger('click')
      await nextTick()

      expect(wrapper.find('.elevation-section').classes()).toContain(
        'elevation-expanded'
      )
    })
  })

  describe('Integration Tests', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('completes full workflow: add waypoints, calculate route, show elevation', async () => {
      // Add waypoints
      wrapper.vm.waypoints = [
        { latLng: { lat: 46.860104, lng: 3.978509 } },
        { latLng: { lat: 46.861104, lng: 3.979509 } }
      ]

      // Calculate route distance
      wrapper.vm.calculateRouteDistance()
      expect(wrapper.vm.routeDistance).toBeGreaterThan(0)

      // Mock route coordinates
      wrapper.vm.actualRouteCoordinates = [
        { lat: 46.860104, lng: 3.978509 },
        { lat: 46.861104, lng: 3.979509 }
      ]

      // Open elevation section
      const toggle = wrapper.find('.elevation-toggle')
      await toggle.trigger('click')
      await nextTick()

      expect(wrapper.find('.elevation-content').exists()).toBe(true)

      // Calculate elevation stats
      await wrapper.vm.calculateElevationStats()
      // Note: fetch might not be called if no elevation data is available due to route length
    })
  })

  describe('Elevation Caching System', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()

      // Clear localStorage before each test
      localStorage.clear()
    })

    afterEach(() => {
      localStorage.clear()
    })

    describe('Cache Management Functions', () => {
      it('should create correct segment hash', () => {
        const component = wrapper.vm as any
        const hash = component.createSegmentHash(
          46.860104,
          3.978509,
          46.861104,
          3.979509
        )
        expect(hash).toBe('46.8601040,3.9785090-46.8611040,3.9795090')
      })

      it('should handle elevation cache initialization', () => {
        const component = wrapper.vm as any

        // Test that elevationCache is initialized
        expect(component.elevationCache).toBeDefined()
        expect(component.elevationCache instanceof Map).toBe(true)
      })
    })

    describe('Segment Processing Functions', () => {
      beforeEach(() => {
        wrapper.vm.actualRouteCoordinates = [
          { lat: 46.860104, lng: 3.978509 },
          { lat: 46.860504, lng: 3.978809 },
          { lat: 46.861004, lng: 3.979209 },
          { lat: 46.861104, lng: 3.979509 }
        ]

        wrapper.vm.waypoints = [
          { latLng: { lat: 46.860104, lng: 3.978509 } },
          { latLng: { lat: 46.861104, lng: 3.979509 } }
        ]
      })

      it('should split route into waypoint segments', () => {
        const component = wrapper.vm as any
        const segments = component.splitRouteIntoWaypointSegments(
          wrapper.vm.actualRouteCoordinates,
          wrapper.vm.waypoints
        )

        expect(segments).toHaveLength(1) // One segment between two waypoints
        expect(Array.isArray(segments[0])).toBe(true)
      })

      it('should find closest route point to waypoint', () => {
        const component = wrapper.vm as any
        const waypoint = { lat: 46.860104, lng: 3.978509 }
        const index = component.findClosestRoutePoint(
          wrapper.vm.actualRouteCoordinates,
          waypoint
        )

        expect(index).toBe(0) // First point should be closest
      })

      it('should sample route segment with distance calculation', () => {
        const component = wrapper.vm as any
        const segment = [
          { lat: 46.860104, lng: 3.978509 },
          { lat: 46.861104, lng: 3.979509 }
        ]

        const sampledPoints = component.sampleRouteSegmentEvery100Meters(segment, 0)

        expect(sampledPoints.length).toBeGreaterThanOrEqual(1)
        expect(sampledPoints[0].distance).toBe(0)
        expect(sampledPoints[0].lat).toBe(46.860104)
      })
    })

    describe('Error Handling', () => {
      it('should handle elevation error state', () => {
        // Test that elevationError can be set and accessed
        wrapper.vm.elevationError = 'Test error'
        expect(wrapper.vm.elevationError).toBe('Test error')

        // Test that elevationError can be cleared
        wrapper.vm.elevationError = null
        expect(wrapper.vm.elevationError).toBeNull()
      })
    })
  })
})
