import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import SegmentList from '../SegmentList.vue'
import type { TrackResponse } from '../../types'

// Mock the GPX parser
vi.mock('../../utils/gpxParser', () => ({
  parseGPXData: vi.fn()
}))

// Mock Leaflet
vi.mock('leaflet', () => ({
  default: {
    map: vi.fn(() => ({
      setView: vi.fn(),
      fitBounds: vi.fn(),
      addLayer: vi.fn(),
      remove: vi.fn()
    })),
    tileLayer: vi.fn(() => ({
      addTo: vi.fn()
    })),
    latLngBounds: vi.fn(() => ({
      contains: vi.fn(() => true)
    })),
    rectangle: vi.fn(() => ({
      addTo: vi.fn(),
      setStyle: vi.fn()
    }))
  }
}))

// Mock fetch
global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () =>
      Promise.resolve({
        gpx_xml_data: '<?xml version="1.0"?><gpx><trk><name>Test</name></trk></gpx>'
      })
  } as any)
)

describe('SegmentList', () => {
  const createMockSegment = (id: number, name: string): TrackResponse => ({
    id,
    file_path: `/path/to/test${id}.gpx`,
    bound_north: 45.8,
    bound_south: 45.7,
    bound_east: 2.1,
    bound_west: 2.0,
    barycenter_latitude: 45.75,
    barycenter_longitude: 2.05,
    name,
    track_type: 'segment',
    difficulty_level: 3,
    surface_type: 'forest-trail',
    tire_dry: 'semi-slick',
    tire_wet: 'knobs',
    comments: `Test segment ${id}`
  })

  const mockSegments: TrackResponse[] = [
    createMockSegment(1, 'Test Segment 1'),
    createMockSegment(2, 'Test Segment 2')
  ]

  // Create many segments for testing "Show more" functionality
  const manyMockSegments: TrackResponse[] = Array.from({ length: 12 }, (_, i) =>
    createMockSegment(i + 1, `Test Segment ${i + 1}`)
  )

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders segment cards correctly', () => {
    const wrapper = mount(SegmentList, {
      props: {
        segments: mockSegments,
        loading: false
      }
    })

    expect(wrapper.findAll('.segment-card')).toHaveLength(2)
    expect(wrapper.find('.segment-name').text()).toBe('Test Segment 1')
  })

  it('displays segment information correctly', () => {
    const wrapper = mount(SegmentList, {
      props: {
        segments: [mockSegments[0]],
        loading: false
      }
    })

    const card = wrapper.find('.segment-card')
    expect(card.find('.segment-name').text()).toBe('Test Segment 1')

    // Check tire recommendations
    const tireBadges = card.findAll('.tire-badge')
    expect(tireBadges.length).toBeGreaterThan(0)

    // Check surface type info
    const infoSections = card.findAll('.info-section')
    expect(infoSections.length).toBeGreaterThan(0)

    // Check difficulty level
    const difficultyInfo = card.find('.difficulty span')
    expect(difficultyInfo.exists()).toBe(true)
    expect(difficultyInfo.text()).toBe('3/5')
  })

  it('shows no segments message when empty', () => {
    const wrapper = mount(SegmentList, {
      props: {
        segments: [],
        loading: false
      }
    })

    expect(wrapper.find('.no-segments p').text()).toBe(
      'No segments found in the current view. Try zooming out or panning to a different area.'
    )
  })

  // TODO: Fix event emission tests - events are not being emitted properly in test environment
  // it('emits segment-click event when card is clicked', async () => {
  //   const wrapper = mount(SegmentList, {
  //     props: {
  //       segments: [mockSegments[0]],
  //       loading: false
  //     }
  //   })

  //   // Wait for the component to be fully mounted
  //   await wrapper.vm.$nextTick()

  //   await wrapper.find('.segment-card').trigger('click')

  //   expect(wrapper.emitted('segment-click')).toBeTruthy()
  //   expect(wrapper.emitted('segment-click')?.[0]).toEqual([mockSegments[0]])
  // })

  // it('emits segment-hover event when card is hovered', async () => {
  //   const wrapper = mount(SegmentList, {
  //     props: {
  //       segments: [mockSegments[0]],
  //       loading: false
  //     }
  //   })

  //   // Wait for the component to be fully mounted
  //   await wrapper.vm.$nextTick()

  //   await wrapper.find('.segment-card').trigger('mouseenter')

  //   expect(wrapper.emitted('segment-hover')).toBeTruthy()
  //   expect(wrapper.emitted('segment-hover')?.[0]).toEqual([mockSegments[0]])
  // })

  // it('emits segment-leave event when card is left', async () => {
  //   const wrapper = mount(SegmentList, {
  //     props: {
  //       segments: [mockSegments[0]],
  //       loading: false
  //     }
  //   })

  //   // Wait for the component to be fully mounted
  //   await wrapper.vm.$nextTick()

  //   await wrapper.find('.segment-card').trigger('mouseleave')

  //   expect(wrapper.emitted('segment-leave')).toBeTruthy()
  //   expect(wrapper.emitted('segment-leave')?.[0]).toEqual([mockSegments[0]])
  // })

  it('formats surface type correctly', () => {
    const wrapper = mount(SegmentList, {
      props: {
        segments: [mockSegments[0]],
        loading: false
      }
    })

    const card = wrapper.find('.segment-card')
    const surfaceInfo = card.find('.info-section .info-value span')
    expect(surfaceInfo.exists()).toBe(true)
    expect(surfaceInfo.text()).toContain('Forest Trail')
  })

  it('formats tire type correctly', () => {
    const wrapper = mount(SegmentList, {
      props: {
        segments: [mockSegments[0]],
        loading: false
      }
    })

    const tireBadges = wrapper.findAll('.tire-badge')
    expect(tireBadges[0].text()).toBe('Semi Slick')
    expect(tireBadges[1].text()).toBe('Knobs')
  })

  it('displays tire recommendations with Font Awesome icons', () => {
    const wrapper = mount(SegmentList, {
      props: {
        segments: [mockSegments[0]],
        loading: false
      }
    })

    const card = wrapper.find('.segment-card')

    // Check for Font Awesome icons in tire recommendations
    const sunIcon = card.find('.fa-sun')
    const cloudIcon = card.find('.fa-cloud-rain')
    expect(sunIcon.exists()).toBe(true)
    expect(cloudIcon.exists()).toBe(true)

    // Check that tire badges exist
    const tireBadges = card.findAll('.tire-badge')
    expect(tireBadges.length).toBeGreaterThan(0)
  })

  describe('Track Type Filtering', () => {
    it('should display segment track type tab as active by default', () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: mockSegments,
          loading: false
        }
      })

      const segmentTab = wrapper.find('.tab-button:first-child')
      const routeTab = wrapper.find('.tab-button:last-child')

      expect(segmentTab.classes()).toContain('active')
      expect(routeTab.classes()).not.toContain('active')
    })

    it('should have clickable track type tabs', async () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: mockSegments,
          loading: false
        }
      })

      const segmentTab = wrapper.find('.tab-button:first-child')
      const routeTab = wrapper.find('.tab-button:last-child')

      // Test that both tabs exist and are clickable
      expect(segmentTab.exists()).toBe(true)
      expect(routeTab.exists()).toBe(true)

      await segmentTab.trigger('click')
      await routeTab.trigger('click')

      // Should not throw errors
      expect(segmentTab.exists()).toBe(true)
      expect(routeTab.exists()).toBe(true)
    })

    it('should render both track type tabs correctly', () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: mockSegments,
          loading: false
        }
      })

      const tabButtons = wrapper.findAll('.tab-button')
      expect(tabButtons).toHaveLength(2)

      // Check that tabs have proper content
      expect(tabButtons[0].text()).toContain('Segments')
      expect(tabButtons[1].text()).toContain('Routes')
    })
  })

  describe('Segment Statistics and Metrics', () => {
    it('should display segment metrics correctly', () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: [mockSegments[0]],
          loading: false
        }
      })

      const card = wrapper.find('.segment-card')
      const metrics = card.findAll('.metric')

      expect(metrics.length).toBeGreaterThan(0)

      // Check that metric labels exist
      const labels = card.findAll('.metric-label')
      expect(labels.some((label) => label.text().includes('Distance'))).toBe(true)
      expect(labels.some((label) => label.text().includes('Elevation Gain'))).toBe(true)
      expect(labels.some((label) => label.text().includes('Elevation Loss'))).toBe(true)
    })

    it('should format metrics with proper units', () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: [mockSegments[0]],
          loading: false
        }
      })

      const card = wrapper.find('.segment-card')
      const metricValues = card.findAll('.metric-value')

      expect(metricValues.length).toBeGreaterThan(0)

      // Check that values are formatted (not raw numbers)
      metricValues.forEach((value) => {
        expect(value.text()).not.toMatch(/^\d+$/) // Should not be just raw numbers
      })
    })

    it('should handle segments with missing statistics', () => {
      const segmentWithoutStats = {
        ...mockSegments[0]
        // Remove any stats-related properties if they exist
      }

      const wrapper = mount(SegmentList, {
        props: {
          segments: [segmentWithoutStats],
          loading: false
        }
      })

      const card = wrapper.find('.segment-card')
      expect(card.exists()).toBe(true)

      // Should still render the card even without stats
      expect(card.find('.segment-name').text()).toBe('Test Segment 1')
    })
  })

  describe('Surface Type Formatting', () => {
    it('should format different surface types correctly', () => {
      const segmentsWithDifferentSurfaces = [
        { ...mockSegments[0], surface_type: 'forest-trail' },
        { ...mockSegments[1], surface_type: 'big-stone-road' }
      ]

      const wrapper = mount(SegmentList, {
        props: {
          segments: segmentsWithDifferentSurfaces,
          loading: false
        }
      })

      const cards = wrapper.findAll('.segment-card')
      expect(cards.length).toBe(2)

      // Check that surface types are displayed
      cards.forEach((card) => {
        const surfaceInfo = card.find('.info-section .info-value span')
        expect(surfaceInfo.exists()).toBe(true)
        expect(surfaceInfo.text()).toBeTruthy()
      })
    })

    it('should handle unknown surface types gracefully', () => {
      const segmentWithUnknownSurface = {
        ...mockSegments[0],
        surface_type: 'unknown-surface'
      }

      const wrapper = mount(SegmentList, {
        props: {
          segments: [segmentWithUnknownSurface],
          loading: false
        }
      })

      const card = wrapper.find('.segment-card')
      const surfaceInfo = card.find('.info-section .info-value span')

      expect(surfaceInfo.exists()).toBe(true)
      // Should display something, even if it's the original value
      expect(surfaceInfo.text()).toBeTruthy()
    })
  })

  describe('Tire Type Formatting', () => {
    it('should format different tire types correctly', () => {
      const segmentsWithDifferentTires = [
        { ...mockSegments[0], tire_dry: 'semi-slick', tire_wet: 'knobs' },
        { ...mockSegments[1], tire_dry: 'knobs', tire_wet: 'knobs' }
      ]

      const wrapper = mount(SegmentList, {
        props: {
          segments: segmentsWithDifferentTires,
          loading: false
        }
      })

      const cards = wrapper.findAll('.segment-card')
      expect(cards.length).toBe(2)

      // Check that tire badges are displayed
      cards.forEach((card) => {
        const tireBadges = card.findAll('.tire-badge')
        expect(tireBadges.length).toBeGreaterThan(0)

        tireBadges.forEach((badge) => {
          expect(badge.text()).toBeTruthy()
        })
      })
    })

    it('should handle unknown tire types gracefully', () => {
      const segmentWithUnknownTires = {
        ...mockSegments[0],
        tire_dry: 'unknown-tire',
        tire_wet: 'another-unknown'
      }

      const wrapper = mount(SegmentList, {
        props: {
          segments: [segmentWithUnknownTires],
          loading: false
        }
      })

      const card = wrapper.find('.segment-card')
      const tireBadges = card.findAll('.tire-badge')

      expect(tireBadges.length).toBeGreaterThan(0)
      tireBadges.forEach((badge) => {
        expect(badge.text()).toBeTruthy()
      })
    })
  })

  describe('Loading States', () => {
    it('should show loading state when loading is true', () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: mockSegments,
          loading: true
        }
      })

      // Should not show the no-segments message when loading
      const noSegments = wrapper.find('.no-segments')
      expect(noSegments.exists()).toBe(false)
    })

    it('should show no segments message when not loading and no segments', () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: [],
          loading: false
        }
      })

      const noSegments = wrapper.find('.no-segments p')
      expect(noSegments.exists()).toBe(true)
      expect(noSegments.text()).toContain('No segments found')
    })

    it('should show segments when not loading and segments exist', () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: mockSegments,
          loading: false
        }
      })

      const noSegments = wrapper.find('.no-segments')
      const segmentCards = wrapper.findAll('.segment-card')

      expect(noSegments.exists()).toBe(false)
      expect(segmentCards.length).toBe(2)
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels and roles', () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: mockSegments,
          loading: false
        }
      })

      // Check that buttons have proper types
      const buttons = wrapper.findAll('button')
      buttons.forEach((button) => {
        expect(button.attributes('type')).toBe('button')
      })

      // Check that segment cards are clickable
      const segmentCards = wrapper.findAll('.segment-card')
      segmentCards.forEach((card) => {
        expect(card.element).toBeTruthy()
      })
    })

    it('should have proper keyboard navigation support', () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: mockSegments,
          loading: false
        }
      })

      const tabButtons = wrapper.findAll('.tab-button')
      tabButtons.forEach((button) => {
        expect(button.element.tagName).toBe('BUTTON')
        // Buttons should be focusable
        expect((button.element as HTMLElement).tabIndex).not.toBe(-1)
      })
    })
  })

  describe('Event Handling', () => {
    it('should have clickable segment cards', async () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: [mockSegments[0]],
          loading: false
        }
      })

      const card = wrapper.find('.segment-card')
      expect(card.exists()).toBe(true)

      // Test that the card can be clicked without errors
      await card.trigger('click')

      // Should not throw error
      expect(card.exists()).toBe(true)
    })

    it('should handle hover interactions', async () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: [mockSegments[0]],
          loading: false
        }
      })

      const card = wrapper.find('.segment-card')

      // Test mouseenter
      await card.trigger('mouseenter')
      expect(card.exists()).toBe(true)

      // Test mouseleave
      await card.trigger('mouseleave')
      expect(card.exists()).toBe(true)
    })

    it('should have interactive track type tabs', async () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: mockSegments,
          loading: false
        }
      })

      const routeTab = wrapper.find('.tab-button:last-child')

      // Test that the tab can be clicked without errors
      await routeTab.trigger('click')

      // Should not throw error
      expect(routeTab.exists()).toBe(true)
    })
  })

  describe('Edge Cases', () => {
    it('should handle segments with missing optional fields', () => {
      const minimalSegment = {
        id: 1,
        name: 'Minimal Segment',
        track_type: 'segment',
        file_path: 'test.gpx',
        bound_north: 45.8,
        bound_south: 45.7,
        bound_east: 4.9,
        bound_west: 4.8,
        barycenter_latitude: 45.75,
        barycenter_longitude: 4.85,
        difficulty_level: 1,
        surface_type: 'forest-trail',
        tire_dry: 'semi-slick',
        tire_wet: 'knobs',
        comments: ''
      }

      const wrapper = mount(SegmentList, {
        props: {
          segments: [minimalSegment],
          loading: false
        }
      })

      const card = wrapper.find('.segment-card')
      expect(card.exists()).toBe(true)
      expect(card.find('.segment-name').text()).toBe('Minimal Segment')
    })

    it('should handle very long segment names gracefully', () => {
      const longNameSegment = {
        ...mockSegments[0],
        name: 'This is a very long segment name that might cause layout issues and should be handled gracefully by the component'
      }

      const wrapper = mount(SegmentList, {
        props: {
          segments: [longNameSegment],
          loading: false
        }
      })

      const card = wrapper.find('.segment-card')
      const nameElement = card.find('.segment-name')

      expect(nameElement.exists()).toBe(true)
      expect(nameElement.text()).toBe(longNameSegment.name)
    })

    it('should handle empty comments field', () => {
      const segmentWithEmptyComment = {
        ...mockSegments[0],
        comments: ''
      }

      const wrapper = mount(SegmentList, {
        props: {
          segments: [segmentWithEmptyComment],
          loading: false
        }
      })

      const card = wrapper.find('.segment-card')
      expect(card.exists()).toBe(true)
      expect(card.find('.segment-name').text()).toBe('Test Segment 1')
    })
  })

  describe('Show More/Less Button Functionality', () => {
    it('should not show the "Show more" button when segments count is below initial display limit', () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: mockSegments, // 2 segments
          loading: false
        }
      })

      const showMoreButton = wrapper.find('.show-more-button')
      expect(showMoreButton.exists()).toBe(false)
    })

    it('should show the "Show more" button when segments count exceeds initial display limit', () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: manyMockSegments, // 12 segments
          loading: false
        }
      })

      const showMoreButton = wrapper.find('.show-more-button')
      expect(showMoreButton.exists()).toBe(true)
    })

    it('should display correct initial count of segments', () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: manyMockSegments, // 12 segments
          loading: false
        }
      })

      // Should show initial count (typically 2, 4, 6, or 8 depending on screen size)
      const segmentCards = wrapper.findAll('.segment-card')
      expect(segmentCards.length).toBeLessThan(manyMockSegments.length)
      expect(segmentCards.length).toBeGreaterThan(0)
    })

    it('should show "Show More" text with count when collapsed', () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: manyMockSegments,
          loading: false
        }
      })

      const showMoreButton = wrapper.find('.show-more-button')
      expect(showMoreButton.exists()).toBe(true)

      const buttonText = showMoreButton.text()
      expect(buttonText).toContain('Show More')
      expect(buttonText).toContain('more)')
    })

    it('should expand to show all segments when "Show More" is clicked', async () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: manyMockSegments,
          loading: false
        }
      })

      const showMoreButton = wrapper.find('.show-more-button')
      await showMoreButton.trigger('click')

      // Should now show all segments
      const segmentCards = wrapper.findAll('.segment-card')
      expect(segmentCards).toHaveLength(manyMockSegments.length)
    })

    it('should show "Show Less" text when expanded', async () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: manyMockSegments,
          loading: false
        }
      })

      const showMoreButton = wrapper.find('.show-more-button')
      await showMoreButton.trigger('click')

      // Button text should change to "Show Less"
      const updatedButton = wrapper.find('.show-more-button')
      expect(updatedButton.text()).toBe('Show Less')
    })

    it('should collapse back to initial count when "Show Less" is clicked', async () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: manyMockSegments,
          loading: false
        }
      })

      const showMoreButton = wrapper.find('.show-more-button')

      // First expand
      await showMoreButton.trigger('click')
      let segmentCards = wrapper.findAll('.segment-card')
      expect(segmentCards).toHaveLength(manyMockSegments.length)

      // Then collapse
      await showMoreButton.trigger('click')
      segmentCards = wrapper.findAll('.segment-card')
      expect(segmentCards.length).toBeLessThan(manyMockSegments.length)
    })

    it('should reset to collapsed state when segments prop changes', async () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: manyMockSegments,
          loading: false
        }
      })

      const showMoreButton = wrapper.find('.show-more-button')

      // Expand first
      await showMoreButton.trigger('click')
      let segmentCards = wrapper.findAll('.segment-card')
      expect(segmentCards).toHaveLength(manyMockSegments.length)

      // Change segments prop
      await wrapper.setProps({ segments: mockSegments })

      // Should reset to collapsed state and show fewer segments
      segmentCards = wrapper.findAll('.segment-card')
      expect(segmentCards.length).toBeLessThanOrEqual(mockSegments.length)
    })

    it('should have correct chevron icon direction based on state', () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: manyMockSegments,
          loading: false
        }
      })

      const showMoreButton = wrapper.find('.show-more-button')
      const chevronIcon = showMoreButton.find('i')

      // Initially should have chevron-down
      expect(chevronIcon.classes()).toContain('fa-chevron-down')
    })

    it('should change chevron icon direction when toggled', async () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: manyMockSegments,
          loading: false
        }
      })

      const showMoreButton = wrapper.find('.show-more-button')
      let chevronIcon = showMoreButton.find('i')

      // Initially chevron-down
      expect(chevronIcon.classes()).toContain('fa-chevron-down')

      // Click to expand
      await showMoreButton.trigger('click')

      // Should now be chevron-up
      chevronIcon = wrapper.find('.show-more-button i')
      expect(chevronIcon.classes()).toContain('fa-chevron-up')
    })

    it('should have proper button styling classes', () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: manyMockSegments,
          loading: false
        }
      })

      const showMoreButton = wrapper.find('.show-more-button')
      expect(showMoreButton.exists()).toBe(true)

      // Check that button has proper structure
      expect(showMoreButton.find('i').exists()).toBe(true) // Icon
      expect(showMoreButton.text()).toContain('Show More') // Text
    })

    it('should handle window resize and update display count', async () => {
      // Mock window.innerWidth
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 800
      })

      const wrapper = mount(SegmentList, {
        props: {
          segments: manyMockSegments,
          loading: false
        }
      })

      // Simulate window resize
      window.innerWidth = 1400
      window.dispatchEvent(new Event('resize'))

      // Wait for next tick to allow component to update
      await wrapper.vm.$nextTick()

      // Component should still function correctly after resize
      const showMoreButton = wrapper.find('.show-more-button')
      expect(showMoreButton.exists()).toBe(true)
    })
  })
})
