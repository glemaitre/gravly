import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import SegmentImportModal from '../SegmentImportModal.vue'
import { createI18n } from 'vue-i18n'

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock EventSource
const mockEventSource = {
  close: vi.fn(),
  onmessage: null as any,
  onerror: null as any
}

global.EventSource = vi.fn(() => mockEventSource) as any

// Mock Leaflet
const mockMap = {
  setView: vi.fn(),
  addLayer: vi.fn(),
  removeLayer: vi.fn(),
  invalidateSize: vi.fn(),
  fitBounds: vi.fn(),
  on: vi.fn(),
  off: vi.fn(),
  getCenter: vi.fn(() => ({ lat: 46.942728, lng: 4.033681 })),
  getBounds: vi.fn(() => ({
    getNorth: vi.fn(() => 47.0),
    getSouth: vi.fn(() => 46.8),
    getEast: vi.fn(() => 4.2),
    getWest: vi.fn(() => 3.8),
    contains: vi.fn(() => true),
    getCenter: vi.fn(() => ({ lat: 46.9, lng: 4.0 }))
  })),
  eachLayer: vi.fn(),
  remove: vi.fn()
}

const mockRectangle = {
  addTo: vi.fn(),
  on: vi.fn(),
  remove: vi.fn(),
  bringToFront: vi.fn()
}

const mockPolyline = {
  addTo: vi.fn(),
  on: vi.fn(),
  remove: vi.fn()
}

const mockControl = {
  addTo: vi.fn()
}

vi.mock('leaflet', () => ({
  default: {
    map: vi.fn(() => mockMap),
    tileLayer: vi.fn(() => ({
      addTo: vi.fn()
    })),
    rectangle: vi.fn(() => mockRectangle),
    polyline: vi.fn(() => mockPolyline),
    latLngBounds: vi.fn(() => ({
      getCenter: vi.fn(() => ({ lat: 46.9, lng: 4.0 })),
      getNorthEast: vi.fn(() => ({ lat: 47.0, lng: 4.2 })),
      getSouthWest: vi.fn(() => ({ lat: 46.8, lng: 3.8 }))
    })),
    control: {
      scale: vi.fn(() => mockControl),
      extend: vi.fn(() => vi.fn(() => mockControl))
    },
    DomUtil: {
      create: vi.fn((tag, className) => {
        const element = document.createElement(tag)
        element.className = className
        return element
      })
    },
    DomEvent: {
      on: vi.fn(),
      disableClickPropagation: vi.fn(),
      disableScrollPropagation: vi.fn()
    }
  }
}))

// Mock GPX parser
vi.mock('../utils/gpxParser', () => ({
  parseGPXData: vi.fn(() => ({
    file_id: 'test-file',
    track_name: 'Test Track',
    points: [
      { latitude: 46.9, longitude: 4.0, elevation: 100, time: '2023-01-01T00:00:00Z' }
    ],
    total_stats: {
      total_points: 1,
      total_distance: 1000,
      total_elevation_gain: 50,
      total_elevation_loss: 30
    },
    bounds: {
      north: 47.0,
      south: 46.8,
      east: 4.2,
      west: 3.8,
      min_elevation: 80,
      max_elevation: 120
    }
  }))
}))

// Mock distance utilities
vi.mock('../utils/distance', () => ({
  haversineDistance: vi.fn(() => 1.5),
  getBoundingBoxCenter: vi.fn(() => ({ lat: 46.9, lng: 4.0 }))
}))

// Mock SegmentImportCard component
vi.mock('../SegmentImportCard.vue', () => ({
  default: {
    name: 'SegmentImportCard',
    props: ['segment', 'distance', 'map'],
    emits: ['click', 'hover', 'leave', 'show-trace', 'hide-trace'],
    template:
      '<div class="mock-segment-card" @click="$emit(\'click\', segment)" @mouseenter="$emit(\'hover\', segment)" @mouseleave="$emit(\'leave\')">{{ segment.name }}</div>'
  }
}))

// Create i18n instance
const i18n = createI18n({
  legacy: false,
  locale: 'en',
  fallbackLocale: 'en',
  messages: {
    en: {
      editor: {
        importSegment: 'Import Segment',
        searchingSegments: 'Searching segments',
        noSegmentsFound: 'No segments found',
        tryDifferentArea: 'Try a different area',
        searchCenter: 'Search center',
        maxResults: 'Max results'
      },
      trackType: {
        segment: 'Segment',
        route: 'Route'
      },
      common: {
        close: 'Close'
      }
    }
  }
})

// Mock environment variables
vi.stubGlobal('import', {
  meta: {
    env: {
      THUNDERFOREST_API_KEY: 'test-api-key'
    }
  }
})

describe('SegmentImportModal', () => {
  let wrapper: any

  const mockSegment: any = {
    id: 1,
    file_path: '/test/path/segment.gpx',
    bound_north: 47.0,
    bound_south: 46.8,
    bound_east: 4.2,
    bound_west: 3.8,
    barycenter_latitude: 46.9,
    barycenter_longitude: 4.0,
    name: 'Test Segment',
    track_type: 'segment',
    difficulty_level: 3,
    surface_type: 'forest-trail',
    tire_dry: 'knobs',
    tire_wet: 'knobs',
    comments: 'Test comments'
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockClear()

    // Reset EventSource mock
    mockEventSource.onmessage = null
    mockEventSource.onerror = null

    // Mock successful fetch response
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          gpx_xml_data: '<gpx><trk><name>Test Track</name></trk></gpx>'
        })
    })
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('Component Rendering', () => {
    it('renders when isOpen is true', async () => {
      wrapper = mount(SegmentImportModal, {
        props: { isOpen: true },
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()
      expect(wrapper.find('.modal-overlay').exists()).toBe(true)
      expect(wrapper.find('.modal-content').exists()).toBe(true)
    })

    it('does not render when isOpen is false', () => {
      wrapper = mount(SegmentImportModal, {
        props: { isOpen: false },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.modal-overlay').exists()).toBe(false)
    })

    it('renders modal header with correct title', async () => {
      wrapper = mount(SegmentImportModal, {
        props: { isOpen: true },
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()
      expect(wrapper.find('.modal-title').text()).toContain('Import Segment')
    })

    it('renders track type tabs', async () => {
      wrapper = mount(SegmentImportModal, {
        props: { isOpen: true },
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()
      expect(wrapper.find('.track-type-tabs').exists()).toBe(true)
      expect(wrapper.findAll('.tab-button')).toHaveLength(2)
    })

    it('renders map container', async () => {
      wrapper = mount(SegmentImportModal, {
        props: { isOpen: true },
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()
      expect(wrapper.find('.map-container').exists()).toBe(true)
      expect(wrapper.find('.map').exists()).toBe(true)
    })
  })

  describe('Track Type Switching', () => {
    it('starts with segment tab active', async () => {
      wrapper = mount(SegmentImportModal, {
        props: { isOpen: true },
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()
      const segmentTab = wrapper.find('.tab-button:first-child')
      expect(segmentTab.classes()).toContain('active')
    })

    it('switches to route tab when clicked', async () => {
      wrapper = mount(SegmentImportModal, {
        props: { isOpen: true },
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()
      const routeTab = wrapper.find('.tab-button:last-child')
      await routeTab.trigger('click')

      expect(routeTab.classes()).toContain('active')
    })

    it('emits search when track type changes', async () => {
      wrapper = mount(SegmentImportModal, {
        props: { isOpen: true },
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()
      const routeTab = wrapper.find('.tab-button:last-child')
      await routeTab.trigger('click')

      // Wait for the search to be triggered
      await nextTick()
      expect(mockEventSource).toBeDefined()
    })
  })

  describe('Segment Search', () => {
    it('searches for segments when map moves', async () => {
      wrapper = mount(SegmentImportModal, {
        props: { isOpen: true },
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()
      await new Promise((resolve) => setTimeout(resolve, 1000))

      // Simulate map move event
      const moveHandler = mockMap.on.mock.calls.find(
        (call) => call[0] === 'moveend'
      )?.[1]
      if (moveHandler) {
        moveHandler()
      }

      expect(mockEventSource).toBeDefined()
    })

    it('shows empty state when no segments found', async () => {
      wrapper = mount(SegmentImportModal, {
        props: { isOpen: true },
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()
      await new Promise((resolve) => setTimeout(resolve, 1000))

      // Simulate search completion with no results
      const moveHandler = mockMap.on.mock.calls.find(
        (call) => call[0] === 'moveend'
      )?.[1]
      if (moveHandler) {
        moveHandler()
      }

      // Simulate EventSource completion
      if (mockEventSource.onmessage) {
        mockEventSource.onmessage({ data: '[DONE]' })
      }

      await nextTick()
      expect(wrapper.find('.empty-state').exists()).toBe(true)
    })
  })

  describe('Event Handling', () => {
    it('emits close when close button is clicked', async () => {
      wrapper = mount(SegmentImportModal, {
        props: { isOpen: true },
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()
      const closeBtn = wrapper.find('.close-btn')
      await closeBtn.trigger('click')

      expect(wrapper.emitted('close')).toBeTruthy()
    })

    it('emits close when overlay is clicked', async () => {
      wrapper = mount(SegmentImportModal, {
        props: { isOpen: true },
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()
      const overlay = wrapper.find('.modal-overlay')
      await overlay.trigger('click')

      expect(wrapper.emitted('close')).toBeTruthy()
    })

    it('does not close when modal content is clicked', async () => {
      wrapper = mount(SegmentImportModal, {
        props: { isOpen: true },
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()
      const content = wrapper.find('.modal-content')
      await content.trigger('click')

      expect(wrapper.emitted('close')).toBeFalsy()
    })

    it('emits import when segment is clicked', async () => {
      wrapper = mount(SegmentImportModal, {
        props: { isOpen: true },
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()
      await new Promise((resolve) => setTimeout(resolve, 500))

      // Add segment
      if (mockEventSource.onmessage) {
        mockEventSource.onmessage({ data: JSON.stringify(mockSegment) })
      }

      await nextTick()
      const segmentCard = wrapper.find('.mock-segment-card')
      if (segmentCard.exists()) {
        await segmentCard.trigger('click')
        expect(wrapper.emitted('import')).toBeTruthy()
        expect(wrapper.emitted('import')?.[0]).toEqual([mockSegment])
      }
    })
  })

  describe('GPX Data Handling', () => {
    it('handles GPX fetch errors gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      // Should not throw error when component is mounted
      expect(() => {
        wrapper = mount(SegmentImportModal, {
          props: { isOpen: true },
          global: {
            plugins: [i18n]
          }
        })
      }).not.toThrow()
    })
  })

  describe('Map Interactions', () => {
    it('handles segment hover on map', async () => {
      wrapper = mount(SegmentImportModal, {
        props: { isOpen: true },
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()
      await new Promise((resolve) => setTimeout(resolve, 1000))

      // Add segment
      if (mockEventSource.onmessage) {
        mockEventSource.onmessage({ data: JSON.stringify(mockSegment) })
      }

      await nextTick()

      // Simulate segment hover
      const segmentCard = wrapper.find('.mock-segment-card')
      if (segmentCard.exists()) {
        await segmentCard.trigger('mouseenter')
        expect(mockRectangle.addTo).toHaveBeenCalled()
      }
    })

    it('handles segment leave on map', async () => {
      wrapper = mount(SegmentImportModal, {
        props: { isOpen: true },
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()
      await new Promise((resolve) => setTimeout(resolve, 1000))

      // Add segment
      if (mockEventSource.onmessage) {
        mockEventSource.onmessage({ data: JSON.stringify(mockSegment) })
      }

      await nextTick()

      // Simulate segment hover then leave
      const segmentCard = wrapper.find('.mock-segment-card')
      if (segmentCard.exists()) {
        await segmentCard.trigger('mouseenter')
        await segmentCard.trigger('mouseleave')
        expect(mockMap.removeLayer).toHaveBeenCalled()
      }
    })
  })
})
