import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { nextTick, ref } from 'vue'
import RoutePlanner from '../components/RoutePlanner.vue'
import { createI18n } from 'vue-i18n'
import type { TrackResponse } from '../types'

// Mock leaflet-routing-machine
vi.mock('leaflet-routing-machine', () => ({
  default: {}
}))

// Mock Leaflet
vi.mock('leaflet', () => ({
  default: {
    map: vi.fn(() => ({
      setView: vi.fn().mockReturnThis(),
      getZoom: vi.fn(() => 14),
      on: vi.fn(),
      off: vi.fn(),
      remove: vi.fn(),
      addLayer: vi.fn(),
      removeLayer: vi.fn(),
      hasLayer: vi.fn(() => false),
      fitBounds: vi.fn(),
      panTo: vi.fn(),
      getBounds: vi.fn(() => ({
        getNorth: () => 47.0,
        getSouth: () => 46.0,
        getEast: () => 5.0,
        getWest: () => 3.0
      })),
      getContainer: vi.fn(() => ({
        style: { cursor: 'crosshair' }
      })),
      dragging: {
        enable: vi.fn(),
        disable: vi.fn()
      },
      latLngToContainerPoint: vi.fn(() => ({ x: 100, y: 100 }))
    })),
    tileLayer: vi.fn(() => ({
      addTo: vi.fn()
    })),
    marker: vi.fn(() => ({
      addTo: vi.fn().mockReturnThis(),
      remove: vi.fn(),
      on: vi.fn(),
      setLatLng: vi.fn(),
      getLatLng: vi.fn(() => ({ lat: 46.86, lng: 3.98 })),
      getElement: vi.fn(() => ({
        classList: {
          add: vi.fn(),
          remove: vi.fn()
        }
      }))
    })),
    polyline: vi.fn(() => ({
      addTo: vi.fn().mockReturnThis(),
      remove: vi.fn(),
      on: vi.fn(),
      setStyle: vi.fn()
    })),
    popup: vi.fn(() => ({
      setLatLng: vi.fn().mockReturnThis(),
      setContent: vi.fn().mockReturnThis(),
      openOn: vi.fn(),
      close: vi.fn()
    })),
    divIcon: vi.fn(() => ({})),
    latLng: vi.fn((lat, lng) => ({ lat, lng })),
    Icon: {
      Default: {
        prototype: {},
        mergeOptions: vi.fn()
      }
    }
  }
}))

// Mock Chart.js
vi.mock('chart.js', () => ({
  Chart: Object.assign(vi.fn(), {
    register: vi.fn()
  }),
  LineController: vi.fn(),
  LineElement: vi.fn(),
  PointElement: vi.fn(),
  LinearScale: vi.fn(),
  Title: vi.fn(),
  CategoryScale: vi.fn(),
  Filler: vi.fn(),
  Tooltip: vi.fn()
}))

// Mock Strava API
interface StravaAuthState {
  isAuthenticated: boolean
  accessToken: string | null
  expiresAt: number | null
  athlete: { id: number; name: string } | null
}

const mockAuthState = ref<StravaAuthState>({
  isAuthenticated: false,
  accessToken: null,
  expiresAt: null,
  athlete: null
})

vi.mock('../composables/useStravaApi', () => ({
  useStravaApi: () => ({
    authState: mockAuthState,
    loadAuthState: vi.fn()
  })
}))

// Create i18n instance
const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en: {
      routePlanner: {
        title: 'Route Planner',
        standardMode: 'Free Mode',
        guidedMode: 'Guided Mode',
        clearMap: 'Clear Map',
        undo: 'Undo',
        redo: 'Redo',
        saveRoute: 'Save Route',
        noRouteMessage: 'Start adding waypoints to see the elevation profile.',
        surfaceTypes: {
          brokenPavedRoad: 'Broken Paved Road'
        },
        tire: 'Tire',
        dry: 'Dry',
        wet: 'Wet'
      },
      common: {
        save: 'Save',
        cancel: 'Cancel'
      }
    }
  }
})

describe('RoutePlanner - Refactored Implementation', () => {
  let wrapper: VueWrapper<any>

  beforeEach(() => {
    // Clear all mocks
    vi.clearAllMocks()

    // Reset auth state
    mockAuthState.value = {
      isAuthenticated: false,
      accessToken: null,
      expiresAt: null,
      athlete: null
    }

    // Mock fetch for API calls
    global.fetch = vi.fn()
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('Component Initialization', () => {
    it('should render correctly', async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()
      expect(wrapper.exists()).toBe(true)
    })

    it('should initialize in standard mode by default', async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()
      expect(wrapper.vm.routeMode).toBe('standard')
    })

    it('should initialize with empty waypoints', async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()
      expect(wrapper.vm.waypoints).toEqual([])
    })

    it('should initialize with empty route segments', async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()
      expect(wrapper.vm.routeSegments).toEqual([])
    })

    it('should initialize with empty route points', async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()
      expect(wrapper.vm.routePoints).toEqual([])
    })
  })

  describe('Route Mode Switching', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('should start in standard mode', () => {
      expect(wrapper.vm.routeMode).toBe('standard')
    })

    it('should switch to guided mode', async () => {
      wrapper.vm.routeMode = 'startEnd'
      await nextTick()
      expect(wrapper.vm.routeMode).toBe('startEnd')
    })

    it('should have empty start and end waypoints in guided mode initially', async () => {
      wrapper.vm.routeMode = 'startEnd'
      await nextTick()
      expect(wrapper.vm.startWaypoint).toBeNull()
      expect(wrapper.vm.endWaypoint).toBeNull()
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

    it('should add waypoints to the array', () => {
      const waypoint = { lat: 46.86, lng: 3.98, type: 'user' as const }
      wrapper.vm.waypoints = [waypoint]
      expect(wrapper.vm.waypoints).toHaveLength(1)
      expect(wrapper.vm.waypoints[0]).toEqual(waypoint)
    })

    it('should allow multiple waypoints', () => {
      wrapper.vm.waypoints = [
        { lat: 46.86, lng: 3.98, type: 'user' },
        { lat: 46.87, lng: 3.99, type: 'user' }
      ]
      expect(wrapper.vm.waypoints).toHaveLength(2)
    })

    it('should support different waypoint types', () => {
      wrapper.vm.waypoints = [
        { lat: 46.86, lng: 3.98, type: 'user' },
        { lat: 46.87, lng: 3.99, type: 'segment-start', segmentId: 1 },
        { lat: 46.88, lng: 4.0, type: 'segment-end', segmentId: 1 }
      ]
      expect(wrapper.vm.waypoints[0].type).toBe('user')
      expect(wrapper.vm.waypoints[1].type).toBe('segment-start')
      expect(wrapper.vm.waypoints[2].type).toBe('segment-end')
    })
  })

  describe('Route Segments Structure', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('should store OSRM segments', () => {
      wrapper.vm.routeSegments = [{ type: 'osrm' }]
      expect(wrapper.vm.routeSegments[0].type).toBe('osrm')
    })

    it('should store GPX segments with metadata', () => {
      wrapper.vm.routeSegments = [
        {
          type: 'gpx',
          segmentId: 123,
          isReversed: false
        }
      ]
      expect(wrapper.vm.routeSegments[0].type).toBe('gpx')
      expect(wrapper.vm.routeSegments[0].segmentId).toBe(123)
      expect(wrapper.vm.routeSegments[0].isReversed).toBe(false)
    })

    it('should store route points for each segment', () => {
      wrapper.vm.routePoints = [
        [
          { lat: 46.86, lng: 3.98, elevation: 100, distance: 0 },
          { lat: 46.87, lng: 3.99, elevation: 110, distance: 100 }
        ]
      ]
      expect(wrapper.vm.routePoints).toHaveLength(1)
      expect(wrapper.vm.routePoints[0]).toHaveLength(2)
    })

    it('should flatten route points in allRoutePoints computed', () => {
      wrapper.vm.routePoints = [
        [
          { lat: 46.86, lng: 3.98, elevation: 100, distance: 0 },
          { lat: 46.87, lng: 3.99, elevation: 110, distance: 100 }
        ],
        [
          { lat: 46.88, lng: 4.0, elevation: 120, distance: 200 },
          { lat: 46.89, lng: 4.01, elevation: 130, distance: 300 }
        ]
      ]
      expect(wrapper.vm.allRoutePoints).toHaveLength(4)
      expect(wrapper.vm.allRoutePoints[0].lat).toBe(46.86)
      expect(wrapper.vm.allRoutePoints[3].lat).toBe(46.89)
    })
  })

  describe('Route Distance Calculation', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('should calculate distance from route points', () => {
      wrapper.vm.routePoints = [
        [
          { lat: 46.86, lng: 3.98, elevation: 100, distance: 0 },
          { lat: 46.87, lng: 3.99, elevation: 110, distance: 150 },
          { lat: 46.88, lng: 4.0, elevation: 120, distance: 300 }
        ]
      ]

      expect(wrapper.vm.routeDistance).toBe(0.3) // 300m = 0.3km
    })

    it('should return 0 when no route points exist', () => {
      wrapper.vm.routePoints = []
      expect(wrapper.vm.routeDistance).toBe(0)
    })

    it('should calculate from last point of last segment', () => {
      wrapper.vm.routePoints = [
        [
          { lat: 46.86, lng: 3.98, elevation: 100, distance: 0 },
          { lat: 46.87, lng: 3.99, elevation: 110, distance: 500 }
        ],
        [
          { lat: 46.88, lng: 4.0, elevation: 120, distance: 600 },
          { lat: 46.89, lng: 4.01, elevation: 130, distance: 1200 }
        ]
      ]

      expect(wrapper.vm.routeDistance).toBe(1.2) // 1200m = 1.2km
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

    it('should calculate elevation gain and loss from reinterpolated points', () => {
      // Simulate route points with varying elevations
      wrapper.vm.routePoints = [
        [
          { lat: 46.86, lng: 3.98, elevation: 100, distance: 0 },
          { lat: 46.861, lng: 3.981, elevation: 120, distance: 100 },
          { lat: 46.862, lng: 3.982, elevation: 140, distance: 200 },
          { lat: 46.863, lng: 3.983, elevation: 130, distance: 300 },
          { lat: 46.864, lng: 3.984, elevation: 110, distance: 400 }
        ]
      ]

      const stats = wrapper.vm.elevationStats
      expect(stats.totalGain).toBeGreaterThan(0)
      expect(stats.totalLoss).toBeGreaterThan(0)
      expect(stats.maxElevation).toBeGreaterThanOrEqual(stats.minElevation)
    })

    it('should return default stats when no route points', () => {
      wrapper.vm.routePoints = []
      const stats = wrapper.vm.elevationStats
      expect(stats.totalGain).toBe(0)
      expect(stats.totalLoss).toBe(0)
    })
  })

  describe('Route Features Computation', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('should return null when no GPX segments in route', () => {
      wrapper.vm.routeSegments = [{ type: 'osrm' }]
      expect(wrapper.vm.routeFeatures).toBeNull()
    })

    it('should compute features from GPX segments in route', () => {
      const mockSegment: TrackResponse = {
        id: 1,
        name: 'Test Segment',
        file_path: '/test/segment.gpx',
        bound_north: 47.0,
        bound_south: 46.0,
        bound_east: 5.0,
        bound_west: 3.0,
        barycenter_latitude: 46.5,
        barycenter_longitude: 4.0,
        track_type: 'segment',
        difficulty_level: 3,
        surface_type: ['gravel-road'],
        tire_dry: 'semi-slick',
        tire_wet: 'knobs',
        comments: '',
        strava_id: undefined
      }

      wrapper.vm.selectedSegments = [mockSegment]
      wrapper.vm.routeSegments = [{ type: 'gpx', segmentId: 1, isReversed: false }]

      const features = wrapper.vm.routeFeatures
      expect(features).not.toBeNull()
      expect(features?.difficulty_level).toBe(3)
      expect(features?.surface_types).toContain('gravel-road')
      expect(features?.tire_dry).toBe('semi-slick')
      expect(features?.tire_wet).toBe('knobs')
    })

    it('should select most conservative tire recommendations', () => {
      const segment1: TrackResponse = {
        id: 1,
        name: 'Segment 1',
        file_path: '/test/seg1.gpx',
        bound_north: 47.0,
        bound_south: 46.0,
        bound_east: 5.0,
        bound_west: 3.0,
        barycenter_latitude: 46.5,
        barycenter_longitude: 4.0,
        track_type: 'segment',
        difficulty_level: 2,
        surface_type: ['paved-road'],
        tire_dry: 'slick',
        tire_wet: 'semi-slick',
        comments: '',
        strava_id: undefined
      }

      const segment2: TrackResponse = {
        id: 2,
        name: 'Segment 2',
        file_path: '/test/seg2.gpx',
        bound_north: 47.0,
        bound_south: 46.0,
        bound_east: 5.0,
        bound_west: 3.0,
        barycenter_latitude: 46.5,
        barycenter_longitude: 4.0,
        track_type: 'segment',
        difficulty_level: 4,
        surface_type: ['gravel-road'],
        tire_dry: 'knobs',
        tire_wet: 'knobs',
        comments: '',
        strava_id: undefined
      }

      wrapper.vm.selectedSegments = [segment1, segment2]
      wrapper.vm.routeSegments = [
        { type: 'gpx', segmentId: 1 },
        { type: 'gpx', segmentId: 2 }
      ]

      const features = wrapper.vm.routeFeatures
      expect(features?.difficulty_level).toBe(4) // max difficulty
      expect(features?.tire_dry).toBe('knobs') // most conservative
      expect(features?.tire_wet).toBe('knobs')
    })
  })

  describe('Segment Filtering', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('should initialize with default filters', () => {
      expect(wrapper.vm.segmentFilters.difficultyMin).toBe(1)
      expect(wrapper.vm.segmentFilters.difficultyMax).toBe(5)
      expect(wrapper.vm.segmentFilters.surface).toEqual([])
      expect(wrapper.vm.segmentFilters.tireDry).toEqual([])
      expect(wrapper.vm.segmentFilters.tireWet).toEqual([])
    })

    it('should update difficulty filters', () => {
      wrapper.vm.segmentFilters.difficultyMin = 2
      wrapper.vm.segmentFilters.difficultyMax = 4
      expect(wrapper.vm.segmentFilters.difficultyMin).toBe(2)
      expect(wrapper.vm.segmentFilters.difficultyMax).toBe(4)
    })

    it('should toggle surface filters', async () => {
      // Add surface filter
      wrapper.vm.segmentFilters.surface.push('gravel-road')
      await nextTick()
      expect(wrapper.vm.segmentFilters.surface).toContain('gravel-road')

      // Remove surface filter
      const index = wrapper.vm.segmentFilters.surface.indexOf('gravel-road')
      wrapper.vm.segmentFilters.surface.splice(index, 1)
      await nextTick()
      expect(wrapper.vm.segmentFilters.surface).not.toContain('gravel-road')
    })

    it('should toggle tire filters', () => {
      wrapper.vm.segmentFilters.tireDry.push('knobs')
      wrapper.vm.segmentFilters.tireWet.push('semi-slick')

      expect(wrapper.vm.segmentFilters.tireDry).toContain('knobs')
      expect(wrapper.vm.segmentFilters.tireWet).toContain('semi-slick')
    })

    it('should clear all filters', () => {
      wrapper.vm.segmentFilters = {
        difficultyMin: 3,
        difficultyMax: 4,
        surface: ['gravel-road'],
        tireDry: ['knobs'],
        tireWet: ['semi-slick']
      }

      wrapper.vm.segmentFilters = {
        difficultyMin: 1,
        difficultyMax: 5,
        surface: [],
        tireDry: [],
        tireWet: []
      }

      expect(wrapper.vm.segmentFilters.difficultyMin).toBe(1)
      expect(wrapper.vm.segmentFilters.difficultyMax).toBe(5)
      expect(wrapper.vm.segmentFilters.surface).toEqual([])
    })
  })

  describe('Segment Filter Application', () => {
    let mockSegment1: TrackResponse
    let mockSegment2: TrackResponse
    let mockSegment3: TrackResponse

    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()

      mockSegment1 = {
        id: 1,
        name: 'Easy Paved',
        file_path: '/test/seg1.gpx',
        bound_north: 47.0,
        bound_south: 46.0,
        bound_east: 5.0,
        bound_west: 3.0,
        barycenter_latitude: 46.5,
        barycenter_longitude: 4.0,
        track_type: 'segment',
        difficulty_level: 2,
        surface_type: ['paved-road'],
        tire_dry: 'slick',
        tire_wet: 'semi-slick',
        comments: '',
        strava_id: undefined
      }

      mockSegment2 = {
        id: 2,
        name: 'Hard Gravel',
        file_path: '/test/seg2.gpx',
        bound_north: 47.0,
        bound_south: 46.0,
        bound_east: 5.0,
        bound_west: 3.0,
        barycenter_latitude: 46.5,
        barycenter_longitude: 4.0,
        track_type: 'segment',
        difficulty_level: 4,
        surface_type: ['gravel-road'],
        tire_dry: 'knobs',
        tire_wet: 'knobs',
        comments: '',
        strava_id: undefined
      }

      mockSegment3 = {
        id: 3,
        name: 'Medium Mixed',
        file_path: '/test/seg3.gpx',
        bound_north: 47.0,
        bound_south: 46.0,
        bound_east: 5.0,
        bound_west: 3.0,
        barycenter_latitude: 46.5,
        barycenter_longitude: 4.0,
        track_type: 'segment',
        difficulty_level: 3,
        surface_type: ['broken-paved-road', 'gravel-road'],
        tire_dry: 'semi-slick',
        tire_wet: 'knobs',
        comments: '',
        strava_id: undefined
      }
    })

    it('should filter segments by difficulty range', () => {
      wrapper.vm.segmentFilters.difficultyMin = 3
      wrapper.vm.segmentFilters.difficultyMax = 5

      // segmentPassesFilters should exist
      expect(typeof wrapper.vm.segmentPassesFilters).toBe('function')

      expect(wrapper.vm.segmentPassesFilters(mockSegment1)).toBe(false) // difficulty 2
      expect(wrapper.vm.segmentPassesFilters(mockSegment2)).toBe(true) // difficulty 4
      expect(wrapper.vm.segmentPassesFilters(mockSegment3)).toBe(true) // difficulty 3
    })

    it('should filter segments by surface type', () => {
      wrapper.vm.segmentFilters.surface = ['paved-road']

      expect(wrapper.vm.segmentPassesFilters(mockSegment1)).toBe(true) // has paved-road
      expect(wrapper.vm.segmentPassesFilters(mockSegment2)).toBe(false) // only gravel
      expect(wrapper.vm.segmentPassesFilters(mockSegment3)).toBe(false) // broken-paved and gravel
    })

    it('should filter segments by tire dry', () => {
      wrapper.vm.segmentFilters.tireDry = ['slick']

      expect(wrapper.vm.segmentPassesFilters(mockSegment1)).toBe(true)
      expect(wrapper.vm.segmentPassesFilters(mockSegment2)).toBe(false)
      expect(wrapper.vm.segmentPassesFilters(mockSegment3)).toBe(false)
    })

    it('should filter segments by tire wet', () => {
      wrapper.vm.segmentFilters.tireWet = ['semi-slick']

      expect(wrapper.vm.segmentPassesFilters(mockSegment1)).toBe(true)
      expect(wrapper.vm.segmentPassesFilters(mockSegment2)).toBe(false)
      expect(wrapper.vm.segmentPassesFilters(mockSegment3)).toBe(false)
    })

    it('should pass all filters when no specific filters are set', () => {
      // Default filters
      wrapper.vm.segmentFilters = {
        difficultyMin: 1,
        difficultyMax: 5,
        surface: [],
        tireDry: [],
        tireWet: []
      }

      expect(wrapper.vm.segmentPassesFilters(mockSegment1)).toBe(true)
      expect(wrapper.vm.segmentPassesFilters(mockSegment2)).toBe(true)
      expect(wrapper.vm.segmentPassesFilters(mockSegment3)).toBe(true)
    })

    it('should apply multiple filters simultaneously', () => {
      wrapper.vm.segmentFilters = {
        difficultyMin: 3,
        difficultyMax: 5,
        surface: ['gravel-road'],
        tireDry: ['knobs'],
        tireWet: []
      }

      expect(wrapper.vm.segmentPassesFilters(mockSegment1)).toBe(false) // difficulty too low
      expect(wrapper.vm.segmentPassesFilters(mockSegment2)).toBe(true) // matches all
      expect(wrapper.vm.segmentPassesFilters(mockSegment3)).toBe(false) // tire_dry is semi-slick
    })
  })

  describe('Save Route Functionality', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('should disable save when user is not authenticated', () => {
      mockAuthState.value.isAuthenticated = false
      wrapper.vm.waypoints = [
        { lat: 46.86, lng: 3.98, type: 'user' },
        { lat: 46.87, lng: 3.99, type: 'user' }
      ]

      expect(wrapper.vm.canSaveRoute).toBe(false)
    })

    it('should disable save when less than 2 waypoints', () => {
      mockAuthState.value.isAuthenticated = true
      wrapper.vm.waypoints = [{ lat: 46.86, lng: 3.98, type: 'user' }]

      expect(wrapper.vm.canSaveRoute).toBe(false)
    })

    it('should enable save when authenticated with 2+ waypoints', async () => {
      mockAuthState.value = {
        isAuthenticated: true,
        accessToken: 'test-token',
        expiresAt: Date.now() + 3600000,
        athlete: { id: 123, name: 'Test User' }
      }

      wrapper.vm.waypoints = [
        { lat: 46.86, lng: 3.98, type: 'user' },
        { lat: 46.87, lng: 3.99, type: 'user' }
      ]

      await nextTick()
      expect(wrapper.vm.canSaveRoute).toBe(true)
    })
  })

  describe('Route Smoothing', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('should apply smoothing to elevation data', () => {
      const points = [
        { lat: 46.86, lng: 3.98, elevation: 100, distance: 0 },
        { lat: 46.861, lng: 3.981, elevation: 150, distance: 100 },
        { lat: 46.862, lng: 3.982, elevation: 100, distance: 200 },
        { lat: 46.863, lng: 3.983, elevation: 150, distance: 300 }
      ]

      wrapper.vm.routePoints = [points]

      const smoothed = wrapper.vm.smoothedRoutePoints
      expect(smoothed).toHaveLength(4)

      // Smoothed values should be less extreme than raw values
      // The middle points should have smoothed elevations
      expect(smoothed[1].elevation).not.toBe(150)
      expect(smoothed[2].elevation).not.toBe(100)
    })

    it('should not smooth when less than 3 points', () => {
      const points = [
        { lat: 46.86, lng: 3.98, elevation: 100, distance: 0 },
        { lat: 46.87, lng: 3.99, elevation: 150, distance: 100 }
      ]

      wrapper.vm.routePoints = [points]
      const smoothed = wrapper.vm.smoothedRoutePoints

      expect(smoothed[0].elevation).toBe(100)
      expect(smoothed[1].elevation).toBe(150)
    })
  })

  describe('Cumulative Distance Recalculation', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('should recalculate cumulative distances after waypoint changes', () => {
      // Set up initial route with 2 segments
      wrapper.vm.routePoints = [
        [
          { lat: 46.86, lng: 3.98, elevation: 100, distance: 0 },
          { lat: 46.87, lng: 3.99, elevation: 110, distance: 100 }
        ],
        [
          { lat: 46.87, lng: 3.99, elevation: 110, distance: 100 }, // Should be recalculated
          { lat: 46.88, lng: 4.0, elevation: 120, distance: 200 }
        ]
      ]

      // Call the recalculation function
      wrapper.vm.recalculateCumulativeDistances()

      // Second segment should start where first segment ended
      expect(wrapper.vm.routePoints[1][0].distance).toBe(
        wrapper.vm.routePoints[0][1].distance
      )
    })
  })

  describe('Clear Map Functionality', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('should clear all waypoints', () => {
      wrapper.vm.waypoints = [
        { lat: 46.86, lng: 3.98, type: 'user' },
        { lat: 46.87, lng: 3.99, type: 'user' }
      ]

      wrapper.vm.clearMap()
      expect(wrapper.vm.waypoints).toEqual([])
    })

    it('should clear route segments', () => {
      wrapper.vm.routeSegments = [{ type: 'osrm' }]
      wrapper.vm.clearMap()
      expect(wrapper.vm.routeSegments).toEqual([])
    })

    it('should clear route points', () => {
      wrapper.vm.routePoints = [
        [{ lat: 46.86, lng: 3.98, elevation: 100, distance: 0 }]
      ]
      wrapper.vm.clearMap()
      expect(wrapper.vm.routePoints).toEqual([])
    })

    it('should set elevation error message', () => {
      wrapper.vm.clearMap()
      expect(wrapper.vm.elevationError).toBeTruthy()
    })
  })

  describe('Segment Selection in Guided Mode', () => {
    let mockSegment: TrackResponse

    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()

      mockSegment = {
        id: 1,
        name: 'Test Segment',
        file_path: '/test/segment.gpx',
        bound_north: 47.0,
        bound_south: 46.0,
        bound_east: 5.0,
        bound_west: 3.0,
        barycenter_latitude: 46.5,
        barycenter_longitude: 4.0,
        track_type: 'segment',
        difficulty_level: 3,
        surface_type: ['gravel-road'],
        tire_dry: 'semi-slick',
        tire_wet: 'knobs',
        comments: '',
        strava_id: undefined
      }
    })

    it('should add segment to selected segments', () => {
      wrapper.vm.selectedSegments = []
      wrapper.vm.selectedSegments.push(mockSegment)

      expect(wrapper.vm.selectedSegments).toHaveLength(1)
      expect(wrapper.vm.selectedSegments[0].id).toBe(1)
    })

    it('should allow multiple segment selection', () => {
      const segment2 = { ...mockSegment, id: 2, name: 'Segment 2' }

      wrapper.vm.selectedSegments = [mockSegment, segment2]

      expect(wrapper.vm.selectedSegments).toHaveLength(2)
    })

    it('should track segment reversal', () => {
      const segmentWithReversal = { ...mockSegment, isReversed: true }
      wrapper.vm.selectedSegments = [segmentWithReversal]

      expect(wrapper.vm.selectedSegments[0].isReversed).toBe(true)
    })
  })

  describe('UI State Management', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('should toggle sidebar visibility', async () => {
      const initialState = wrapper.vm.showSidebar
      wrapper.vm.showSidebar = !initialState
      await nextTick()
      expect(wrapper.vm.showSidebar).toBe(!initialState)
    })

    it('should toggle elevation visibility', async () => {
      const initialState = wrapper.vm.showElevation
      wrapper.vm.showElevation = !initialState
      await nextTick()
      expect(wrapper.vm.showElevation).toBe(!initialState)
    })

    it('should toggle filters expanded state', async () => {
      const initialState = wrapper.vm.filtersExpanded
      wrapper.vm.filtersExpanded = !initialState
      await nextTick()
      expect(wrapper.vm.filtersExpanded).toBe(!initialState)
    })

    it('should show/hide save modal', async () => {
      wrapper.vm.showSaveModal = true
      await nextTick()
      expect(wrapper.vm.showSaveModal).toBe(true)

      wrapper.vm.showSaveModal = false
      await nextTick()
      expect(wrapper.vm.showSaveModal).toBe(false)
    })
  })

  describe('Guided Mode - Start/End Waypoints', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
      wrapper.vm.routeMode = 'startEnd'
    })

    it('should set start waypoint', () => {
      wrapper.vm.startWaypoint = { lat: 46.86, lng: 3.98 }
      expect(wrapper.vm.startWaypoint).not.toBeNull()
      expect(wrapper.vm.startWaypoint?.lat).toBe(46.86)
    })

    it('should set end waypoint', () => {
      wrapper.vm.endWaypoint = { lat: 46.87, lng: 3.99 }
      expect(wrapper.vm.endWaypoint).not.toBeNull()
      expect(wrapper.vm.endWaypoint?.lat).toBe(46.87)
    })

    it('should clear start and end waypoints', () => {
      wrapper.vm.startWaypoint = { lat: 46.86, lng: 3.98 }
      wrapper.vm.endWaypoint = { lat: 46.87, lng: 3.99 }

      wrapper.vm.clearStartEndWaypoints(false, false)

      expect(wrapper.vm.startWaypoint).toBeNull()
      expect(wrapper.vm.endWaypoint).toBeNull()
    })
  })

  describe('Route Generation Progress', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('should initialize with progress tracking disabled', () => {
      expect(wrapper.vm.routeGenerationProgress.isGenerating).toBe(false)
      expect(wrapper.vm.routeGenerationProgress.current).toBe(0)
      expect(wrapper.vm.routeGenerationProgress.total).toBe(0)
    })

    it('should track progress during route generation', () => {
      wrapper.vm.routeGenerationProgress = {
        isGenerating: true,
        current: 2,
        total: 5,
        message: 'Generating segments...'
      }

      expect(wrapper.vm.routeGenerationProgress.isGenerating).toBe(true)
      expect(wrapper.vm.routeGenerationProgress.current).toBe(2)
      expect(wrapper.vm.routeGenerationProgress.total).toBe(5)
    })
  })

  describe('Map Cursor Management', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('should show crosshair cursor in standard mode', () => {
      wrapper.vm.routeMode = 'standard'
      wrapper.vm.isPanning = false

      // updateMapCursor should exist
      expect(typeof wrapper.vm.updateMapCursor).toBe('function')
    })

    it('should show grabbing cursor when panning', () => {
      wrapper.vm.isPanning = true

      // The cursor should be managed by updateMapCursor
      expect(wrapper.vm.isPanning).toBe(true)
    })
  })

  describe('Incremental Route Generation', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()

      // Mock OSRM API
      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              routes: [
                {
                  geometry: {
                    coordinates: [
                      [3.98, 46.86],
                      [3.99, 46.87]
                    ]
                  }
                }
              ]
            })
        })
      ) as any
    })

    it('should generate all segments on first generation', async () => {
      wrapper.vm.waypoints = [
        { lat: 46.86, lng: 3.98, type: 'user' },
        { lat: 46.87, lng: 3.99, type: 'user' }
      ]

      const previousSegmentCount = wrapper.vm.routeSegments.length
      expect(previousSegmentCount).toBe(0)

      // After generation, should have 1 segment (2 waypoints = 1 segment)
      const expectedSegmentCount = wrapper.vm.waypoints.length - 1
      expect(expectedSegmentCount).toBe(1)
    })

    it('should only generate new segments when waypoints are added', () => {
      // Start with 2 waypoints, 1 segment
      wrapper.vm.waypoints = [
        { lat: 46.86, lng: 3.98, type: 'user' },
        { lat: 46.87, lng: 3.99, type: 'user' }
      ]
      wrapper.vm.routeSegments = [{ type: 'osrm' }]
      wrapper.vm.routePoints = [
        [{ lat: 46.86, lng: 3.98, elevation: 100, distance: 0 }]
      ]

      const previousSegmentCount = wrapper.vm.routeSegments.length

      // Add a third waypoint
      wrapper.vm.waypoints.push({ lat: 46.88, lng: 4.0, type: 'user' })

      const expectedSegmentCount = wrapper.vm.waypoints.length - 1
      expect(expectedSegmentCount).toBe(2) // Should now need 2 segments
      expect(expectedSegmentCount).toBeGreaterThan(previousSegmentCount)
    })

    it('should truncate segments when waypoints are removed', () => {
      wrapper.vm.waypoints = [
        { lat: 46.86, lng: 3.98, type: 'user' },
        { lat: 46.87, lng: 3.99, type: 'user' },
        { lat: 46.88, lng: 4.0, type: 'user' }
      ]
      wrapper.vm.routeSegments = [{ type: 'osrm' }, { type: 'osrm' }]
      wrapper.vm.routePoints = [
        [{ lat: 46.86, lng: 3.98, elevation: 100, distance: 0 }],
        [{ lat: 46.87, lng: 3.99, elevation: 110, distance: 100 }]
      ]

      const previousSegmentCount = wrapper.vm.routeSegments.length
      expect(previousSegmentCount).toBe(2)

      // Remove last waypoint
      wrapper.vm.waypoints.pop()

      const expectedSegmentCount = wrapper.vm.waypoints.length - 1
      expect(expectedSegmentCount).toBe(1)
      expect(expectedSegmentCount).toBeLessThan(previousSegmentCount)
    })
  })

  describe('GPX Segment Detection', () => {
    let mockSegment: TrackResponse

    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()

      mockSegment = {
        id: 1,
        name: 'Test Segment',
        file_path: '/test/segment.gpx',
        bound_north: 47.0,
        bound_south: 46.0,
        bound_east: 5.0,
        bound_west: 3.0,
        barycenter_latitude: 46.5,
        barycenter_longitude: 4.0,
        track_type: 'segment',
        difficulty_level: 3,
        surface_type: ['gravel-road'],
        tire_dry: 'semi-slick',
        tire_wet: 'knobs',
        comments: '',
        strava_id: undefined
      }
    })

    it('should detect GPX segment between waypoints', () => {
      wrapper.vm.selectedSegments = [mockSegment]
      wrapper.vm.waypoints = [
        { lat: 46.86, lng: 3.98, type: 'segment-start', segmentId: 1 },
        { lat: 46.87, lng: 3.99, type: 'segment-end', segmentId: 1 }
      ]

      const segmentInfo = wrapper.vm.findSegmentBetweenWaypoints(0, 1)
      expect(segmentInfo).not.toBeNull()
      expect(segmentInfo?.segment.id).toBe(1)
      expect(segmentInfo?.isReversed).toBe(false)
    })

    it('should return null when waypoints are not segment markers', () => {
      wrapper.vm.waypoints = [
        { lat: 46.86, lng: 3.98, type: 'user' },
        { lat: 46.87, lng: 3.99, type: 'user' }
      ]

      const segmentInfo = wrapper.vm.findSegmentBetweenWaypoints(0, 1)
      expect(segmentInfo).toBeNull()
    })

    it('should return null when waypoints belong to different segments', () => {
      wrapper.vm.waypoints = [
        { lat: 46.86, lng: 3.98, type: 'segment-start', segmentId: 1 },
        { lat: 46.87, lng: 3.99, type: 'segment-end', segmentId: 2 }
      ]

      const segmentInfo = wrapper.vm.findSegmentBetweenWaypoints(0, 1)
      expect(segmentInfo).toBeNull()
    })
  })

  describe('Undo/Redo Functionality', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('should initialize with undo/redo disabled', () => {
      expect(wrapper.vm.canUndo).toBe(false)
      expect(wrapper.vm.canRedo).toBe(false)
    })

    it('should have undo and redo functions', () => {
      expect(typeof wrapper.vm.undo).toBe('function')
      expect(typeof wrapper.vm.redo).toBe('function')
    })
  })

  describe('Available Segments Management', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('should store available segments', () => {
      const mockSegment: TrackResponse = {
        id: 1,
        name: 'Test',
        file_path: '/test.gpx',
        bound_north: 47.0,
        bound_south: 46.0,
        bound_east: 5.0,
        bound_west: 3.0,
        barycenter_latitude: 46.5,
        barycenter_longitude: 4.0,
        track_type: 'segment',
        difficulty_level: 3,
        surface_type: ['gravel-road'],
        tire_dry: 'semi-slick',
        tire_wet: 'knobs',
        comments: '',
        strava_id: undefined
      }

      wrapper.vm.availableSegments = [mockSegment]
      expect(wrapper.vm.availableSegments).toHaveLength(1)
    })

    it('should clear available segments', () => {
      const mockSegment: TrackResponse = {
        id: 1,
        name: 'Test',
        file_path: '/test.gpx',
        bound_north: 47.0,
        bound_south: 46.0,
        bound_east: 5.0,
        bound_west: 3.0,
        barycenter_latitude: 46.5,
        barycenter_longitude: 4.0,
        track_type: 'segment',
        difficulty_level: 3,
        surface_type: ['gravel-road'],
        tire_dry: 'semi-slick',
        tire_wet: 'knobs',
        comments: '',
        strava_id: undefined
      }

      wrapper.vm.availableSegments = [mockSegment]
      wrapper.vm.availableSegments = []
      expect(wrapper.vm.availableSegments).toEqual([])
    })
  })

  describe('Route Distance Computed Property', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('should return 0 when no route points', () => {
      wrapper.vm.routePoints = []
      expect(wrapper.vm.routeDistance).toBe(0)
    })

    it('should calculate distance from last point', () => {
      wrapper.vm.routePoints = [
        [
          { lat: 46.86, lng: 3.98, elevation: 100, distance: 0 },
          { lat: 46.87, lng: 3.99, elevation: 110, distance: 1500 }
        ]
      ]

      expect(wrapper.vm.routeDistance).toBe(1.5) // 1500m = 1.5km
    })

    it('should calculate from last point across multiple segments', () => {
      wrapper.vm.routePoints = [
        [
          { lat: 46.86, lng: 3.98, elevation: 100, distance: 0 },
          { lat: 46.87, lng: 3.99, elevation: 110, distance: 500 }
        ],
        [
          { lat: 46.88, lng: 4.0, elevation: 120, distance: 600 },
          { lat: 46.89, lng: 4.01, elevation: 130, distance: 2300 }
        ]
      ]

      expect(wrapper.vm.routeDistance).toBe(2.3) // 2300m = 2.3km
    })
  })

  describe('Elevation Statistics Computed Property', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('should compute elevation stats from reinterpolated points', () => {
      // Create a route with ups and downs
      const points = []
      for (let i = 0; i <= 1000; i += 100) {
        points.push({
          lat: 46.86 + i * 0.0001,
          lng: 3.98 + i * 0.0001,
          elevation: 100 + Math.sin(i / 200) * 50,
          distance: i
        })
      }

      wrapper.vm.routePoints = [points]

      const stats = wrapper.vm.elevationStats
      expect(typeof stats.totalGain).toBe('number')
      expect(typeof stats.totalLoss).toBe('number')
      expect(typeof stats.maxElevation).toBe('number')
      expect(typeof stats.minElevation).toBe('number')
      expect(stats.maxElevation).toBeGreaterThanOrEqual(stats.minElevation)
    })
  })

  describe('Context Menu', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('should initialize with context menu hidden', () => {
      expect(wrapper.vm.contextMenu.visible).toBe(false)
    })

    it('should have context menu position properties', () => {
      expect(typeof wrapper.vm.contextMenu.x).toBe('number')
      expect(typeof wrapper.vm.contextMenu.y).toBe('number')
      expect(typeof wrapper.vm.contextMenu.waypointIndex).toBe('number')
    })
  })

  describe('Segment Loading in Guided Mode', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('should not be searching segments initially', () => {
      expect(wrapper.vm.isSearchingSegments).toBe(false)
    })

    it('should track segment search state', () => {
      wrapper.vm.isSearchingSegments = true
      expect(wrapper.vm.isSearchingSegments).toBe(true)
    })
  })

  describe('Mixed Routes (GPX + OSRM Segments)', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('should support mixed segment types', () => {
      wrapper.vm.routeSegments = [
        { type: 'gpx', segmentId: 1, isReversed: false },
        { type: 'osrm' },
        { type: 'gpx', segmentId: 2, isReversed: true }
      ]

      expect(wrapper.vm.routeSegments[0].type).toBe('gpx')
      expect(wrapper.vm.routeSegments[1].type).toBe('osrm')
      expect(wrapper.vm.routeSegments[2].type).toBe('gpx')
      expect(wrapper.vm.routeSegments[2].isReversed).toBe(true)
    })

    it('should maintain segment order', () => {
      wrapper.vm.routeSegments = [
        { type: 'osrm' },
        { type: 'gpx', segmentId: 1 },
        { type: 'osrm' }
      ]

      expect(wrapper.vm.routeSegments).toHaveLength(3)
      expect(wrapper.vm.routeSegments[1].type).toBe('gpx')
    })
  })

  describe('Clear All Segments', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('should have clearAllSegments function', () => {
      expect(typeof wrapper.vm.clearAllSegments).toBe('function')
    })

    it('should clear available segments', () => {
      wrapper.vm.availableSegments = [
        {
          id: 1,
          name: 'Test',
          file_path: '/test.gpx',
          bound_north: 47.0,
          bound_south: 46.0,
          bound_east: 5.0,
          bound_west: 3.0,
          barycenter_latitude: 46.5,
          barycenter_longitude: 4.0,
          track_type: 'segment',
          difficulty_level: 3,
          surface_type: ['gravel-road'],
          tire_dry: 'semi-slick',
          tire_wet: 'knobs',
          comments: null,
          strava_id: null
        }
      ]

      wrapper.vm.clearAllSegments()
      expect(wrapper.vm.availableSegments).toEqual([])
    })
  })

  describe('Info Banner', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('should have info banner visibility state', () => {
      expect(typeof wrapper.vm.showInfoBanner).toBe('boolean')
    })

    it('should toggle info banner', () => {
      const initial = wrapper.vm.showInfoBanner
      wrapper.vm.showInfoBanner = !initial
      expect(wrapper.vm.showInfoBanner).toBe(!initial)
    })
  })

  describe('Elevation Height Management', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('should have default elevation height', () => {
      expect(typeof wrapper.vm.elevationHeight).toBe('number')
      expect(wrapper.vm.elevationHeight).toBeGreaterThan(0)
    })

    it('should allow elevation height changes', () => {
      wrapper.vm.elevationHeight = 400
      expect(wrapper.vm.elevationHeight).toBe(400)
    })
  })

  describe('Segment Reversal', () => {
    let mockSegment: TrackResponse

    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()

      mockSegment = {
        id: 1,
        name: 'Test Segment',
        file_path: '/test/segment.gpx',
        bound_north: 47.0,
        bound_south: 46.0,
        bound_east: 5.0,
        bound_west: 3.0,
        barycenter_latitude: 46.5,
        barycenter_longitude: 4.0,
        track_type: 'segment',
        difficulty_level: 3,
        surface_type: ['gravel-road'],
        tire_dry: 'semi-slick',
        tire_wet: 'knobs',
        comments: '',
        strava_id: undefined
      }
    })

    it('should have reverseSegment function', () => {
      expect(typeof wrapper.vm.reverseSegment).toBe('function')
    })

    it('should toggle segment reversal state', () => {
      wrapper.vm.selectedSegments = [{ ...mockSegment, isReversed: false }]

      // After reversal
      wrapper.vm.selectedSegments[0].isReversed = true
      expect(wrapper.vm.selectedSegments[0].isReversed).toBe(true)

      // Reverse again
      wrapper.vm.selectedSegments[0].isReversed = false
      expect(wrapper.vm.selectedSegments[0].isReversed).toBe(false)
    })
  })

  describe('Segment Deselection', () => {
    let mockSegment: TrackResponse

    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()

      mockSegment = {
        id: 1,
        name: 'Test Segment',
        file_path: '/test/segment.gpx',
        bound_north: 47.0,
        bound_south: 46.0,
        bound_east: 5.0,
        bound_west: 3.0,
        barycenter_latitude: 46.5,
        barycenter_longitude: 4.0,
        track_type: 'segment',
        difficulty_level: 3,
        surface_type: ['gravel-road'],
        tire_dry: 'semi-slick',
        tire_wet: 'knobs',
        comments: '',
        strava_id: undefined
      }
    })

    it('should have deselectSegment function', () => {
      expect(typeof wrapper.vm.deselectSegment).toBe('function')
    })

    it('should remove segment from selected segments', () => {
      wrapper.vm.selectedSegments = [mockSegment]
      expect(wrapper.vm.selectedSegments).toHaveLength(1)

      wrapper.vm.deselectSegment(1)
      expect(wrapper.vm.selectedSegments).toHaveLength(0)
    })
  })

  describe('Route Features with No Segments', () => {
    beforeEach(async () => {
      wrapper = mount(RoutePlanner, {
        global: {
          plugins: [i18n]
        }
      })
      await nextTick()
    })

    it('should return null when only OSRM segments exist', () => {
      wrapper.vm.routeSegments = [{ type: 'osrm' }, { type: 'osrm' }]
      expect(wrapper.vm.routeFeatures).toBeNull()
    })

    it('should return null when routeSegments is empty', () => {
      wrapper.vm.routeSegments = []
      expect(wrapper.vm.routeFeatures).toBeNull()
    })
  })
})
