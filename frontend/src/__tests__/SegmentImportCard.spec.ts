import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import SegmentImportCard from '../components/SegmentImportCard.vue'
import type { TrackResponse, GPXDataResponse } from '../types'

// Import real locale files
import en from '../i18n/locales/en'
import fr from '../i18n/locales/fr'

// Create i18n instance for testing
const i18n = createI18n({
  legacy: false,
  locale: 'en',
  fallbackLocale: 'en',
  messages: { en, fr }
})

// Mock fetch
global.fetch = vi.fn()

// Mock utility functions
vi.mock('../utils/gpxParser', () => ({
  parseGPXData: vi.fn(() => ({
    points: [
      {
        latitude: 46.942728,
        longitude: 4.033681,
        elevation: 100,
        time: '2023-01-01T00:00:00Z'
      }
    ],
    total_stats: {
      total_distance: 1500,
      total_elevation_gain: 75,
      total_elevation_loss: 45
    }
  }))
}))

describe('SegmentImportCard', () => {
  let wrapper: any

  const mockSegment: TrackResponse = {
    id: 1,
    file_path: '/path/to/segment.gpx',
    bound_north: 46.95,
    bound_south: 46.93,
    bound_east: 4.05,
    bound_west: 4.02,
    barycenter_latitude: 46.942728,
    barycenter_longitude: 4.033681,
    name: 'Test Segment',
    track_type: 'segment',
    difficulty_level: 3,
    surface_type: 'forest-trail',
    tire_dry: 'semi-slick',
    tire_wet: 'knobs',
    comments: 'Test comments'
  }

  const mockGPXResponse: GPXDataResponse = {
    gpx_xml_data: '<?xml version="1.0" encoding="UTF-8"?><gpx>...</gpx>'
  }

  beforeEach(() => {
    vi.clearAllMocks()

    // Mock successful fetch responses
    ;(global.fetch as any).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockGPXResponse)
    })

    wrapper = mount(SegmentImportCard, {
      props: {
        segment: mockSegment,
        distance: 1000
      },
      global: {
        plugins: [i18n]
      }
    })
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
    vi.restoreAllMocks()
  })

  describe('Component Rendering', () => {
    it('renders segment information correctly', () => {
      expect(wrapper.find('.segment-card').exists()).toBe(true)
      expect(wrapper.find('.segment-name').text()).toBe('Test Segment')
    })

    it('displays segment stats', () => {
      expect(wrapper.find('.segment-stats').exists()).toBe(true)
      expect(wrapper.findAll('.stat-item')).toHaveLength(3)
    })

    it('shows surface type information', () => {
      const surfaceInfo = wrapper.find('.info-section:first-child')
      expect(surfaceInfo.find('.info-label').text()).toBe('Surface')
      expect(surfaceInfo.find('.info-value').text()).toContain('Forest trail')
    })

    it('displays tire recommendations', () => {
      const tireSection = wrapper.findAll('.info-section')[1]
      expect(tireSection.find('.info-label').text()).toBe('Tires')
      expect(tireSection.find('.tire-recommendations').exists()).toBe(true)
    })

    it('shows difficulty level', () => {
      const difficultySection = wrapper.findAll('.info-section')[2]
      expect(difficultySection.find('.info-label').text()).toBe('Difficulty')
      expect(difficultySection.find('.info-value').text()).toBe('3/5')
    })
  })

  describe('User Interactions', () => {
    it('emits click event when card is clicked', async () => {
      const card = wrapper.find('.segment-card')
      await card.trigger('click')

      expect(wrapper.emitted('click')).toBeTruthy()
      expect(wrapper.emitted('click')[0]).toEqual([mockSegment])
    })

    it('emits hover event when card is hovered', async () => {
      const card = wrapper.find('.segment-card')
      await card.trigger('mouseenter')

      expect(wrapper.emitted('hover')).toBeTruthy()
      expect(wrapper.emitted('hover')[0]).toEqual([mockSegment])
    })

    it('emits leave event when card is left', async () => {
      const card = wrapper.find('.segment-card')
      await card.trigger('mouseleave')

      expect(wrapper.emitted('leave')).toBeTruthy()
    })

    it('applies hover styles when hovered', async () => {
      const card = wrapper.find('.segment-card')
      await card.trigger('mouseenter')

      expect(card.classes()).toContain('is-hovered')
    })

    it('removes hover styles when left', async () => {
      const card = wrapper.find('.segment-card')
      await card.trigger('mouseenter')
      await card.trigger('mouseleave')

      expect(card.classes()).not.toContain('is-hovered')
    })
  })

  describe('Data Fetching', () => {
    it('fetches segment stats on mount', () => {
      expect(global.fetch).toHaveBeenCalledWith(
        `http://localhost:8000/api/segments/${mockSegment.id}/gpx`
      )
    })

    it('fetches stats on hover if not already loaded', async () => {
      // Reset fetch mock
      vi.clearAllMocks()
      ;(global.fetch as any).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockGPXResponse)
      })

      // Create new wrapper with reset stats
      const newWrapper = mount(SegmentImportCard, {
        props: {
          segment: mockSegment,
          distance: 1000
        },
        global: {
          plugins: [i18n]
        }
      })

      // Reset stats by directly setting the component data
      ;(newWrapper.vm as any).segmentStats = {
        total_distance: 0,
        total_elevation_gain: 0,
        total_elevation_loss: 0
      }

      const card = newWrapper.find('.segment-card')
      await card.trigger('mouseenter')

      expect(global.fetch).toHaveBeenCalled()

      newWrapper.unmount()
    })

    it('does not fetch stats again if already loaded', async () => {
      // Reset fetch mock
      vi.clearAllMocks()
      ;(global.fetch as any).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockGPXResponse)
      })

      // Create new wrapper with loaded stats
      const newWrapper = mount(SegmentImportCard, {
        props: {
          segment: mockSegment,
          distance: 1000
        },
        global: {
          plugins: [i18n]
        }
      })

      // Set stats as already loaded and prevent fetch on mount
      ;(newWrapper.vm as any).segmentStats = {
        total_distance: 1000,
        total_elevation_gain: 50,
        total_elevation_loss: 30
      }
      ;(newWrapper.vm as any).isLoadingStats = false

      // Wait for any initial fetch to complete
      await newWrapper.vm.$nextTick()

      // Clear the fetch mock after initial setup
      vi.clearAllMocks()

      const card = newWrapper.find('.segment-card')
      await card.trigger('mouseenter')

      // Should not fetch again since stats are already loaded
      expect(global.fetch).not.toHaveBeenCalled()

      newWrapper.unmount()
    })
  })

  describe('Stats Display', () => {
    it('shows loading state while fetching stats', async () => {
      // Create new wrapper and set loading state
      const newWrapper = mount(SegmentImportCard, {
        props: {
          segment: mockSegment,
          distance: 1000
        },
        global: {
          plugins: [i18n]
        }
      })

      ;(newWrapper.vm as any).isLoadingStats = true
      await newWrapper.vm.$nextTick()

      const statValues = newWrapper.findAll('.stat-value')
      statValues.forEach((stat: any) => {
        expect(stat.text()).toBe('...')
      })

      newWrapper.unmount()
    })

    it('displays fetched stats when available', async () => {
      // Create new wrapper and set stats
      const newWrapper = mount(SegmentImportCard, {
        props: {
          segment: mockSegment,
          distance: 1000
        },
        global: {
          plugins: [i18n]
        }
      })

      ;(newWrapper.vm as any).segmentStats = {
        total_distance: 1500,
        total_elevation_gain: 75,
        total_elevation_loss: 45
      }
      ;(newWrapper.vm as any).isLoadingStats = false
      await newWrapper.vm.$nextTick()

      const statValues = newWrapper.findAll('.stat-value')
      expect(statValues[0].text()).toBe('1.5km')
      expect(statValues[1].text()).toBe('75m')
      expect(statValues[2].text()).toBe('45m')

      newWrapper.unmount()
    })

    it('shows fallback stats when fetch fails', async () => {
      ;(global.fetch as any).mockRejectedValue(new Error('Fetch failed'))

      // Wait for the component to process the error
      await wrapper.vm.$nextTick()

      // Should show some stats (fallback)
      const statValues = wrapper.findAll('.stat-value')
      statValues.forEach((stat: any) => {
        expect(stat.text()).not.toBe('...')
      })
    })
  })

  describe('Formatting Functions', () => {
    it('formats distance correctly', () => {
      expect(wrapper.vm.formatDistance(500)).toBe('500m')
      expect(wrapper.vm.formatDistance(1500)).toBe('1.5km')
      expect(wrapper.vm.formatDistance(2000)).toBe('2.0km')
    })

    it('formats elevation correctly', () => {
      expect(wrapper.vm.formatElevation(75)).toBe('75m')
      expect(wrapper.vm.formatElevation(150.7)).toBe('151m')
    })

    it('formats tire type correctly', () => {
      expect(wrapper.vm.formatTireType('semi-slick')).toBe('Semi Slick')
      expect(wrapper.vm.formatTireType('knobs')).toBe('Knobs')
      expect(wrapper.vm.formatTireType('')).toBe('')
    })
  })

  describe('Computed Properties', () => {
    it('computes surface type label correctly', () => {
      expect(wrapper.vm.surfaceTypeLabel).toBe('Forest trail')
    })

    it('computes tire dry label correctly', () => {
      expect(wrapper.vm.tireDryLabel).toBe('Semi Slick')
    })

    it('computes tire wet label correctly', () => {
      expect(wrapper.vm.tireWetLabel).toBe('Knobs')
    })
  })

  describe('GPX Data Processing', () => {
    it('processes GPX data when fetch succeeds', async () => {
      await wrapper.vm.fetchSegmentStats()

      expect(wrapper.vm.segmentStats.total_distance).toBe(1500)
      expect(wrapper.vm.segmentStats.total_elevation_gain).toBe(75)
      expect(wrapper.vm.segmentStats.total_elevation_loss).toBe(45)
    })

    it('emits showTrace event with GPX data', async () => {
      await wrapper.vm.fetchSegmentStats()

      expect(wrapper.emitted('showTrace')).toBeTruthy()
      expect(wrapper.emitted('showTrace')[0]).toHaveLength(2)
      expect(wrapper.emitted('showTrace')[0][0]).toEqual(mockSegment)
    })

    it('handles GPX parsing errors gracefully', async () => {
      // Mock parseGPXData to return null
      const { parseGPXData } = await import('../utils/gpxParser')
      vi.mocked(parseGPXData).mockReturnValue(null)

      await wrapper.vm.fetchSegmentStats()

      // Should generate fallback stats
      expect(wrapper.vm.segmentStats.total_distance).toBeGreaterThan(0)
    })
  })

  describe('Fallback Stats Generation', () => {
    it('generates fallback stats when GPX data is unavailable', async () => {
      ;(global.fetch as any).mockRejectedValue(new Error('Fetch failed'))

      await wrapper.vm.generateFallbackStats()

      expect(wrapper.vm.segmentStats.total_distance).toBeGreaterThan(0)
      expect(wrapper.vm.segmentStats.total_elevation_gain).toBeGreaterThan(0)
      expect(wrapper.vm.segmentStats.total_elevation_loss).toBeGreaterThan(0)
    })

    it('uses difficulty level for elevation calculation', async () => {
      const segmentWithDifficulty = { ...mockSegment, difficulty_level: 5 }
      await wrapper.setProps({ segment: segmentWithDifficulty })

      await wrapper.vm.generateFallbackStats()

      // Higher difficulty should result in higher elevation
      expect(wrapper.vm.segmentStats.total_elevation_gain).toBeGreaterThan(200)
    })
  })

  describe('Error Handling', () => {
    it('handles fetch errors gracefully', async () => {
      ;(global.fetch as any).mockRejectedValue(new Error('Network error'))

      await wrapper.vm.fetchSegmentStats()

      // Should not crash and should generate fallback stats
      expect(wrapper.vm.segmentStats.total_distance).toBeGreaterThan(0)
    })

    it('handles non-OK fetch responses', async () => {
      ;(global.fetch as any).mockResolvedValue({
        ok: false,
        statusText: 'Not Found'
      })

      await wrapper.vm.fetchSegmentStats()

      // Should generate fallback stats
      expect(wrapper.vm.segmentStats.total_distance).toBeGreaterThan(0)
    })

    it('handles JSON parsing errors', async () => {
      ;(global.fetch as any).mockResolvedValue({
        ok: true,
        json: () => Promise.reject(new Error('Invalid JSON'))
      })

      await wrapper.vm.fetchSegmentStats()

      // Should generate fallback stats
      expect(wrapper.vm.segmentStats.total_distance).toBeGreaterThan(0)
    })
  })

  describe('Loading States', () => {
    it('sets loading state during fetch', async () => {
      // Mock a delayed fetch
      // eslint-disable-next-line no-unused-vars
      let resolveFetch: (value: any) => void = () => {}
      const fetchPromise = new Promise((resolve) => {
        resolveFetch = resolve
      })
      ;(global.fetch as any).mockReturnValue(fetchPromise)

      const fetchPromise2 = wrapper.vm.fetchSegmentStats()

      expect(wrapper.vm.isLoadingStats).toBe(true)

      // Resolve the fetch
      resolveFetch({
        ok: true,
        json: () => Promise.resolve(mockGPXResponse)
      })

      await fetchPromise2

      expect(wrapper.vm.isLoadingStats).toBe(false)
    })

    it('prevents multiple simultaneous fetches', async () => {
      // Reset fetch mock
      vi.clearAllMocks()

      // Mock a delayed fetch
      // eslint-disable-next-line no-unused-vars
      let resolveFetch: (value: any) => void = () => {}
      const fetchPromise = new Promise((resolve) => {
        resolveFetch = resolve
      })
      ;(global.fetch as any).mockReturnValue(fetchPromise)

      // Create new wrapper to avoid interference from previous tests
      const newWrapper = mount(SegmentImportCard, {
        props: {
          segment: mockSegment,
          distance: 1000
        },
        global: {
          plugins: [i18n]
        }
      })

      // Start first fetch
      const fetch1 = (newWrapper.vm as any).fetchSegmentStats()

      // Try to start second fetch while first is in progress
      const fetch2 = (newWrapper.vm as any).fetchSegmentStats()

      // Resolve the fetch
      resolveFetch({
        ok: true,
        json: () => Promise.resolve(mockGPXResponse)
      })

      await Promise.all([fetch1, fetch2])

      // Should only fetch once
      expect(global.fetch).toHaveBeenCalledTimes(1)

      newWrapper.unmount()
    })
  })

  describe('Props Validation', () => {
    it('requires segment prop', () => {
      // Test that the component expects a segment prop
      // We'll test this by checking the component definition
      expect(SegmentImportCard.props).toBeDefined()
      expect(SegmentImportCard.props?.segment).toBeDefined()
    })

    it('requires distance prop', () => {
      // Test that the component expects a distance prop
      expect(SegmentImportCard.props).toBeDefined()
      expect(SegmentImportCard.props?.distance).toBeDefined()
    })

    it('accepts optional map prop', () => {
      const mapInstance = { test: 'map' }
      const wrapper = mount(SegmentImportCard, {
        props: {
          segment: mockSegment,
          distance: 1000,
          map: mapInstance
        },
        global: { plugins: [i18n] }
      })

      expect(wrapper.props('map')).toStrictEqual(mapInstance)
    })
  })

  describe('Accessibility', () => {
    it('has proper semantic structure', () => {
      expect(wrapper.find('.segment-card').exists()).toBe(true)
      expect(wrapper.find('.segment-name').exists()).toBe(true)
    })

    it('has descriptive text content', () => {
      const segmentName = wrapper.find('.segment-name')
      expect(segmentName.attributes('title')).toBe('Test Segment')
    })
  })

  describe('Styling and CSS Classes', () => {
    it('applies correct CSS classes', () => {
      const card = wrapper.find('.segment-card')
      expect(card.classes()).toContain('segment-card')
    })

    it('applies hover classes on hover', async () => {
      const card = wrapper.find('.segment-card')
      await card.trigger('mouseenter')

      expect(card.classes()).toContain('is-hovered')
    })

    it('has proper stat item structure', () => {
      const statItems = wrapper.findAll('.stat-item')
      expect(statItems).toHaveLength(3)

      statItems.forEach((item: any) => {
        expect(item.find('.stat-content').exists()).toBe(true)
        expect(item.find('.stat-label').exists()).toBe(true)
        expect(item.find('.stat-value').exists()).toBe(true)
      })
    })
  })

  describe('Internationalization', () => {
    it('uses correct translation keys', () => {
      expect(wrapper.vm.surfaceTypeLabel).toBe('Forest trail')
      expect(wrapper.vm.tireDryLabel).toBe('Semi Slick')
      expect(wrapper.vm.tireWetLabel).toBe('Knobs')
    })

    it('handles missing translations gracefully', async () => {
      // Test with unknown surface type
      const segmentWithUnknownSurface = {
        ...mockSegment,
        surface_type: 'unknown-surface'
      }
      await wrapper.setProps({ segment: segmentWithUnknownSurface })

      // Should not crash
      expect(wrapper.vm.surfaceTypeLabel).toBeDefined()
    })
  })
})
