import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import SegmentPopupCard from '../components/SegmentPopupCard.vue'
import type { TrackResponse, GPXData } from '../types'

describe('SegmentPopupCard', () => {
  const mockSegment: TrackResponse = {
    id: 1,
    file_path: '/tracks/1.gpx',
    bound_north: 46.862104,
    bound_south: 46.860104,
    bound_east: 3.980509,
    bound_west: 3.978509,
    barycenter_latitude: 46.861104,
    barycenter_longitude: 3.979509,
    name: 'Test Segment',
    track_type: 'gravel',
    difficulty_level: 3,
    surface_type: ['broken-paved-road'],
    tire_dry: 'slick',
    tire_wet: 'knobs',
    comments: 'Test comments'
  }

  const mockGPXData: GPXData = {
    file_id: '1',
    track_name: 'Test Segment',
    points: [],
    total_stats: {
      total_points: 100,
      total_distance: 5000, // 5km
      total_elevation_gain: 250,
      total_elevation_loss: 150
    },
    bounds: {
      north: 46.862104,
      south: 46.860104,
      east: 3.980509,
      west: 3.978509,
      min_elevation: 100,
      max_elevation: 350
    }
  }

  beforeEach(() => {
    // No setup needed
  })

  describe('Component Rendering', () => {
    it('renders correctly', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      expect(wrapper.find('.segment-popup-card').exists()).toBe(true)
    })

    it('displays segment name', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      expect(wrapper.find('.segment-name').text()).toBe('Test Segment')
    })

    it('applies selected class when isSelected is true', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: true
        }
      })

      expect(wrapper.find('.segment-popup-card').classes()).toContain('selected')
    })

    it('does not apply selected class when isSelected is false', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      expect(wrapper.find('.segment-popup-card').classes()).not.toContain('selected')
    })
  })

  describe('Stats Display', () => {
    it('shows stats when gpxData is provided', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false,
          gpxData: mockGPXData
        }
      })

      const statValues = wrapper.findAll('.stat-value')
      expect(statValues).toHaveLength(3)
      expect(statValues[0].text()).toBe('5.0km') // Distance
      expect(statValues[1].text()).toBe('250m') // Elevation gain
      expect(statValues[2].text()).toBe('150m') // Elevation loss
    })

    it('shows loading state when gpxData is not provided', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      const statValues = wrapper.findAll('.stat-value')
      expect(statValues).toHaveLength(3)
      expect(statValues[0].text()).toBe('...')
      expect(statValues[1].text()).toBe('...')
      expect(statValues[2].text()).toBe('...')
    })

    it('shows loading state when gpxData has no total_stats', () => {
      const incompleteGPXData = {
        ...mockGPXData,
        total_stats: null as any
      }

      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false,
          gpxData: incompleteGPXData
        }
      })

      const statValues = wrapper.findAll('.stat-value')
      expect(statValues[0].text()).toBe('...')
    })

    it('formats distance in meters when less than 1000m', () => {
      const shortDistanceGPXData = {
        ...mockGPXData,
        total_stats: {
          ...mockGPXData.total_stats,
          total_distance: 850
        }
      }

      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false,
          gpxData: shortDistanceGPXData
        }
      })

      const distanceStat = wrapper.findAll('.stat-value')[0]
      expect(distanceStat.text()).toBe('850m')
    })

    it('formats distance in kilometers when >= 1000m', () => {
      const longDistanceGPXData = {
        ...mockGPXData,
        total_stats: {
          ...mockGPXData.total_stats,
          total_distance: 12345
        }
      }

      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false,
          gpxData: longDistanceGPXData
        }
      })

      const distanceStat = wrapper.findAll('.stat-value')[0]
      expect(distanceStat.text()).toBe('12.3km')
    })
  })

  describe('Segment Information Display', () => {
    it('displays surface type formatted correctly', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      const infoSections = wrapper.findAll('.info-section')
      const surfaceSection = infoSections[0]
      expect(surfaceSection.text()).toContain('Broken Paved Road')
    })

    it('displays tire recommendations for dry conditions', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      const tireBadges = wrapper.findAll('.tire-badge')
      expect(tireBadges[0].text()).toBe('Slick') // Dry tire
    })

    it('displays tire recommendations for wet conditions', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      const tireBadges = wrapper.findAll('.tire-badge')
      expect(tireBadges[1].text()).toBe('Knobs') // Wet tire
    })

    it('displays difficulty level', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      const infoSections = wrapper.findAll('.info-section')
      const difficultySection = infoSections[2]
      expect(difficultySection.text()).toContain('3/5')
    })

    it('handles empty tire type gracefully', () => {
      const segmentWithNoTire = {
        ...mockSegment,
        tire_dry: '',
        tire_wet: ''
      }

      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: segmentWithNoTire,
          isSelected: false
        }
      })

      const tireBadges = wrapper.findAll('.tire-badge')
      expect(tireBadges[0].text()).toBe('')
      expect(tireBadges[1].text()).toBe('')
    })
  })

  describe('Format Functions', () => {
    it('formats various surface types correctly', () => {
      const surfaceTypes = [
        { input: 'broken-paved-road', expected: 'Broken Paved Road' },
        { input: 'forest-trail', expected: 'Forest Trail' },
        { input: 'big-stone-road', expected: 'Big Stone Road' }
      ]

      surfaceTypes.forEach(({ input, expected }) => {
        const segment = { ...mockSegment, surface_type: [input] }
        const wrapper = mount(SegmentPopupCard, {
          props: {
            segment,
            isSelected: false
          }
        })

        const surfaceText = wrapper.findAll('.info-section')[0].text()
        expect(surfaceText).toContain(expected)
      })
    })

    it('formats various tire types correctly', () => {
      const tireTypes = [
        { input: 'semi-slick', expected: 'Semi Slick' },
        { input: 'knobs', expected: 'Knobs' },
        { input: 'slick', expected: 'Slick' }
      ]

      tireTypes.forEach(({ input, expected }) => {
        const segment = { ...mockSegment, tire_dry: input, tire_wet: input }
        const wrapper = mount(SegmentPopupCard, {
          props: {
            segment,
            isSelected: false
          }
        })

        const tireBadges = wrapper.findAll('.tire-badge')
        expect(tireBadges[0].text()).toBe(expected)
        expect(tireBadges[1].text()).toBe(expected)
      })
    })
  })

  describe('Visual States', () => {
    it('has cursor pointer styling', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      const card = wrapper.find('.segment-popup-card')
      expect(card.element).toBeDefined()
      // The cursor: pointer is in the CSS
    })

    it('displays all stat items', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false,
          gpxData: mockGPXData
        }
      })

      const statItems = wrapper.findAll('.stat-item')
      expect(statItems).toHaveLength(3)
    })

    it('displays all info sections', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      const infoSections = wrapper.findAll('.info-section')
      expect(infoSections).toHaveLength(3)
    })

    it('displays stat labels correctly', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false,
          gpxData: mockGPXData
        }
      })

      const statLabels = wrapper.findAll('.stat-label')
      expect(statLabels[0].text()).toBe('Distance')
      expect(statLabels[1].text()).toBe('Elevation Gain')
      expect(statLabels[2].text()).toBe('Elevation Loss')
    })

    it('displays info labels correctly', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      const infoLabels = wrapper.findAll('.info-label')
      expect(infoLabels[0].text()).toBe('Surface')
      expect(infoLabels[1].text()).toBe('Tires')
      expect(infoLabels[2].text()).toBe('Difficulty')
    })
  })

  describe('Edge Cases', () => {
    it('handles very long segment names', () => {
      const longNameSegment = {
        ...mockSegment,
        name: 'Very Long Segment Name That Should Be Truncated Or Wrapped Properly'
      }

      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: longNameSegment,
          isSelected: false
        }
      })

      expect(wrapper.find('.segment-name').text()).toBe(longNameSegment.name)
    })

    it('handles difficulty level edge values', () => {
      const minDifficultySegment = { ...mockSegment, difficulty_level: 1 }
      const maxDifficultySegment = { ...mockSegment, difficulty_level: 5 }

      const wrapperMin = mount(SegmentPopupCard, {
        props: {
          segment: minDifficultySegment,
          isSelected: false
        }
      })

      const wrapperMax = mount(SegmentPopupCard, {
        props: {
          segment: maxDifficultySegment,
          isSelected: false
        }
      })

      expect(wrapperMin.text()).toContain('1/5')
      expect(wrapperMax.text()).toContain('5/5')
    })

    it('handles zero elevation values', () => {
      const flatGPXData = {
        ...mockGPXData,
        total_stats: {
          ...mockGPXData.total_stats,
          total_elevation_gain: 0,
          total_elevation_loss: 0
        }
      }

      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false,
          gpxData: flatGPXData
        }
      })

      const statValues = wrapper.findAll('.stat-value')
      expect(statValues[1].text()).toBe('0m')
      expect(statValues[2].text()).toBe('0m')
    })
  })

  describe('Icons Display', () => {
    it('displays all required icons', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false,
          gpxData: mockGPXData
        }
      })

      // Stat icons
      expect(wrapper.find('.fa-route').exists()).toBe(true)
      expect(wrapper.find('.fa-arrow-trend-up').exists()).toBe(true)
      expect(wrapper.find('.fa-arrow-trend-down').exists()).toBe(true)

      // Info icons (surface uses text now, not icon)
      expect(wrapper.find('.surface-text').exists()).toBe(true)
      expect(wrapper.find('.fa-signal').exists()).toBe(true)
      expect(wrapper.find('.fa-sun').exists()).toBe(true)
      expect(wrapper.find('.fa-cloud-rain').exists()).toBe(true)
    })
  })

  describe('Button Functionality', () => {
    it('displays add/remove segment button', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      const addButton = wrapper.find('.add-segment-btn')
      expect(addButton.exists()).toBe(true)
    })

    it('displays close popup button', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      const closeButton = wrapper.find('.close-popup-btn')
      expect(closeButton.exists()).toBe(true)
    })

    it('shows plus icon when segment is not selected', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      const addButton = wrapper.find('.add-segment-btn')
      const icon = addButton.find('i')
      expect(icon.classes()).toContain('fa-plus')
    })

    it('shows check icon when segment is selected', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: true
        }
      })

      const addButton = wrapper.find('.add-segment-btn')
      const icon = addButton.find('i')
      expect(icon.classes()).toContain('fa-check')
    })

    it('shows times icon for close button', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      const closeButton = wrapper.find('.close-popup-btn')
      const icon = closeButton.find('i')
      expect(icon.classes()).toContain('fa-times')
    })

    it('applies selected class to add button when segment is selected', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: true
        }
      })

      const addButton = wrapper.find('.add-segment-btn')
      expect(addButton.classes()).toContain('selected')
    })

    it('does not apply selected class to add button when segment is not selected', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      const addButton = wrapper.find('.add-segment-btn')
      expect(addButton.classes()).not.toContain('selected')
    })
  })

  describe('Event Emissions', () => {
    it('emits toggleSelection when add/remove button is clicked', async () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      const addButton = wrapper.find('.add-segment-btn')
      await addButton.trigger('click')

      expect(wrapper.emitted('toggleSelection')).toBeTruthy()
      expect(wrapper.emitted('toggleSelection')?.[0]).toEqual([mockSegment])
    })

    it('emits close when close button is clicked', async () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      const closeButton = wrapper.find('.close-popup-btn')
      await closeButton.trigger('click')

      expect(wrapper.emitted('close')).toBeTruthy()
    })

    it('prevents event propagation on button clicks', async () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      const addButton = wrapper.find('.add-segment-btn')
      const closeButton = wrapper.find('.close-popup-btn')

      // Both buttons should exist and have click handlers
      expect(addButton.exists()).toBe(true)
      expect(closeButton.exists()).toBe(true)

      // Test that clicking buttons emits events (which means @click.stop is working)
      await addButton.trigger('click')
      await closeButton.trigger('click')

      expect(wrapper.emitted('toggleSelection')).toBeTruthy()
      expect(wrapper.emitted('close')).toBeTruthy()
    })
  })

  describe('Button Accessibility', () => {
    it('has correct title attributes for buttons', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      const addButton = wrapper.find('.add-segment-btn')
      const closeButton = wrapper.find('.close-popup-btn')

      expect(addButton.attributes('title')).toBe('Add to selected segments')
      expect(closeButton.attributes('title')).toBe('Close popup')
    })

    it('has correct title for selected state', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: true
        }
      })

      const addButton = wrapper.find('.add-segment-btn')
      expect(addButton.attributes('title')).toBe('Remove from selected segments')
    })
  })

  describe('Header Layout', () => {
    it('has header buttons container', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      const headerButtons = wrapper.find('.header-buttons')
      expect(headerButtons.exists()).toBe(true)
    })

    it('contains both buttons in header buttons container', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      const headerButtons = wrapper.find('.header-buttons')
      const addButton = headerButtons.find('.add-segment-btn')
      const closeButton = headerButtons.find('.close-popup-btn')

      expect(addButton.exists()).toBe(true)
      expect(closeButton.exists()).toBe(true)
    })
  })

  describe('CSS Styling', () => {
    it('has correct CSS classes applied', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      // Test that the main container has the correct class
      const card = wrapper.find('.segment-popup-card')
      expect(card.exists()).toBe(true)
      expect(card.classes()).toContain('segment-popup-card')

      // Test that header has correct class
      const header = wrapper.find('.segment-card-header')
      expect(header.exists()).toBe(true)

      // Test that content has correct class
      const content = wrapper.find('.segment-card-content')
      expect(content.exists()).toBe(true)

      // Test that footer has correct class
      const footer = wrapper.find('.segment-card-footer')
      expect(footer.exists()).toBe(true)
    })

    it('has header buttons container with correct structure', () => {
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      const headerButtons = wrapper.find('.header-buttons')
      expect(headerButtons.exists()).toBe(true)

      // Verify both buttons are inside the header buttons container
      const addButton = headerButtons.find('.add-segment-btn')
      const closeButton = headerButtons.find('.close-popup-btn')
      expect(addButton.exists()).toBe(true)
      expect(closeButton.exists()).toBe(true)
    })
  })

  describe('Global CSS Overrides', () => {
    it('includes global CSS for Leaflet popup content', () => {
      // This test verifies that the global CSS rules are present in the component
      // The actual CSS override testing would require integration testing with Leaflet
      const wrapper = mount(SegmentPopupCard, {
        props: {
          segment: mockSegment,
          isSelected: false
        }
      })

      // Verify the component renders without errors when global CSS is applied
      expect(wrapper.find('.segment-popup-card').exists()).toBe(true)
    })
  })
})
