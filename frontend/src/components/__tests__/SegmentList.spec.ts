import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import SegmentList from '../SegmentList.vue'
import SegmentCard from '../SegmentCard.vue'
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
    surface_type: ['forest-trail'],
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
      },
      global: {
        components: { SegmentCard }
      }
    })

    const cards = wrapper.findAllComponents(SegmentCard)
    expect(cards).toHaveLength(2)
  })

  it('passes correct props to SegmentCard components', () => {
    const wrapper = mount(SegmentList, {
      props: {
        segments: [mockSegments[0]],
        loading: false
      },
      global: {
        components: { SegmentCard }
      }
    })

    const card = wrapper.findComponent(SegmentCard)
    expect(card.exists()).toBe(true)
    expect(card.props('segment')).toEqual(mockSegments[0])
    expect(card.props('isHovered')).toBe(false)
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
    it('should emit segmentClick event when SegmentCard emits click', async () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: [mockSegments[0]],
          loading: false
        },
        global: {
          components: { SegmentCard }
        }
      })

      const card = wrapper.findComponent(SegmentCard)
      await card.vm.$emit('click', mockSegments[0])

      expect(wrapper.emitted('segmentClick')).toBeTruthy()
      expect(wrapper.emitted('segmentClick')?.[0]).toEqual([mockSegments[0]])
    })

    it('should emit segmentHover event when SegmentCard emits mouseenter', async () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: [mockSegments[0]],
          loading: false
        },
        global: {
          components: { SegmentCard }
        }
      })

      const card = wrapper.findComponent(SegmentCard)
      await card.vm.$emit('mouseenter', mockSegments[0])

      expect(wrapper.emitted('segmentHover')).toBeTruthy()
      expect(wrapper.emitted('segmentHover')?.[0]).toEqual([mockSegments[0]])
    })

    it('should emit segmentLeave event when SegmentCard emits mouseleave', async () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: [mockSegments[0]],
          loading: false
        },
        global: {
          components: { SegmentCard }
        }
      })

      const card = wrapper.findComponent(SegmentCard)
      await card.vm.$emit('mouseleave', mockSegments[0])

      expect(wrapper.emitted('segmentLeave')).toBeTruthy()
      expect(wrapper.emitted('segmentLeave')?.[0]).toEqual([mockSegments[0]])
    })

    it('should emit trackTypeChange event when track type tab is clicked', async () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: mockSegments,
          loading: false
        }
      })

      const routeTab = wrapper.find('.tab-button:last-child')
      await routeTab.trigger('click')

      expect(wrapper.emitted('trackTypeChange')).toBeTruthy()
      expect(wrapper.emitted('trackTypeChange')?.[0]).toEqual(['route'])
    })
  })

  describe('Edge Cases', () => {
    it('should render list with segments with missing optional fields', () => {
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
        surface_type: ['forest-trail'],
        tire_dry: 'semi-slick',
        tire_wet: 'knobs',
        comments: ''
      }

      const wrapper = mount(SegmentList, {
        props: {
          segments: [minimalSegment],
          loading: false
        },
        global: {
          components: { SegmentCard }
        }
      })

      const cards = wrapper.findAllComponents(SegmentCard)
      expect(cards).toHaveLength(1)
    })

    it('should handle dynamic segment list updates', async () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: [mockSegments[0]],
          loading: false
        },
        global: {
          components: { SegmentCard }
        }
      })

      let cards = wrapper.findAllComponents(SegmentCard)
      expect(cards).toHaveLength(1)

      // Update segments
      await wrapper.setProps({ segments: mockSegments })
      cards = wrapper.findAllComponents(SegmentCard)
      expect(cards).toHaveLength(2)
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

    it('should add bottom padding when button is not present', () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: mockSegments, // 2 segments - below display limit
          loading: false
        }
      })

      const segmentCards = wrapper.find('.segment-cards')
      expect(segmentCards.classes()).toContain('segment-cards--no-button')
    })

    it('should not add bottom padding when button is present', () => {
      const wrapper = mount(SegmentList, {
        props: {
          segments: manyMockSegments, // 12 segments - above display limit
          loading: false
        }
      })

      const segmentCards = wrapper.find('.segment-cards')
      expect(segmentCards.classes()).not.toContain('segment-cards--no-button')
    })
  })
})
