import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SegmentCard from '../components/SegmentCard.vue'
import type { TrackResponse } from '../types'

describe('SegmentCard', () => {
  const createMockSegment = (
    id: number,
    name: string,
    overrides?: Partial<TrackResponse>
  ): TrackResponse => ({
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
    comments: `Test segment ${id}`,
    ...overrides
  })

  const createMockStats = () => ({
    total_distance: 5000, // 5km
    total_elevation_gain: 250,
    total_elevation_loss: 230
  })

  describe('Rendering', () => {
    it('should render segment card with basic information', () => {
      const segment = createMockSegment(1, 'Test Segment')
      const stats = createMockStats()

      const wrapper = mount(SegmentCard, {
        props: { segment, stats }
      })

      expect(wrapper.find('.segment-card').exists()).toBe(true)
      expect(wrapper.find('.segment-name').text()).toBe('Test Segment')
    })

    it('should render without stats', () => {
      const segment = createMockSegment(1, 'Test Segment')

      const wrapper = mount(SegmentCard, {
        props: { segment }
      })

      expect(wrapper.find('.segment-card').exists()).toBe(true)
      expect(wrapper.find('.segment-name').text()).toBe('Test Segment')
    })

    it('should render with null stats', () => {
      const segment = createMockSegment(1, 'Test Segment')

      const wrapper = mount(SegmentCard, {
        props: { segment, stats: null }
      })

      expect(wrapper.find('.segment-card').exists()).toBe(true)
    })
  })

  describe('Segment Name', () => {
    it('should display segment name', () => {
      const segment = createMockSegment(1, 'Mountain Trail')
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats() }
      })

      expect(wrapper.find('.segment-name').text()).toBe('Mountain Trail')
    })

    it('should apply hovered class when isHovered is true', () => {
      const segment = createMockSegment(1, 'Test Segment')
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats(), isHovered: true }
      })

      expect(wrapper.find('.segment-name').classes()).toContain('hovered')
    })

    it('should not apply hovered class when isHovered is false', () => {
      const segment = createMockSegment(1, 'Test Segment')
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats(), isHovered: false }
      })

      expect(wrapper.find('.segment-name').classes()).not.toContain('hovered')
    })

    it('should handle very long segment names', () => {
      const segment = createMockSegment(
        1,
        'This is a very long segment name that might cause layout issues'
      )
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats() }
      })

      expect(wrapper.find('.segment-name').text()).toBe(
        'This is a very long segment name that might cause layout issues'
      )
    })
  })

  describe('Metrics Display', () => {
    it('should display distance metric', () => {
      const segment = createMockSegment(1, 'Test Segment')
      const stats = { ...createMockStats(), total_distance: 5000 }

      const wrapper = mount(SegmentCard, {
        props: { segment, stats }
      })

      const metrics = wrapper.findAll('.metric')
      expect(metrics.length).toBeGreaterThan(0)

      const distanceMetric = metrics.find(
        (m) => m.find('.metric-label').text() === 'Distance'
      )
      expect(distanceMetric?.find('.metric-value').text()).toBe('5.0km')
    })

    it('should display elevation gain metric', () => {
      const segment = createMockSegment(1, 'Test Segment')
      const stats = { ...createMockStats(), total_elevation_gain: 250 }

      const wrapper = mount(SegmentCard, {
        props: { segment, stats }
      })

      const metrics = wrapper.findAll('.metric')
      const elevationGainMetric = metrics.find((m) =>
        m.find('.metric-label').text().includes('Elevation Gain')
      )
      expect(elevationGainMetric?.find('.metric-value').text()).toBe('250m')
    })

    it('should display elevation loss metric', () => {
      const segment = createMockSegment(1, 'Test Segment')
      const stats = { ...createMockStats(), total_elevation_loss: 230 }

      const wrapper = mount(SegmentCard, {
        props: { segment, stats }
      })

      const metrics = wrapper.findAll('.metric')
      const elevationLossMetric = metrics.find((m) =>
        m.find('.metric-label').text().includes('Elevation Loss')
      )
      expect(elevationLossMetric?.find('.metric-value').text()).toBe('230m')
    })

    it('should display 0m when stats are missing', () => {
      const segment = createMockSegment(1, 'Test Segment')

      const wrapper = mount(SegmentCard, {
        props: { segment }
      })

      const metrics = wrapper.findAll('.metric-value')
      metrics.forEach((metric) => {
        expect(metric.text()).toBe('0m')
      })
    })

    it('should format distance in meters when less than 1km', () => {
      const segment = createMockSegment(1, 'Test Segment')
      const stats = { ...createMockStats(), total_distance: 500 }

      const wrapper = mount(SegmentCard, {
        props: { segment, stats }
      })

      const metrics = wrapper.findAll('.metric')
      const distanceMetric = metrics.find(
        (m) => m.find('.metric-label').text() === 'Distance'
      )
      expect(distanceMetric?.find('.metric-value').text()).toBe('500m')
    })

    it('should format distance in kilometers when 1km or more', () => {
      const segment = createMockSegment(1, 'Test Segment')
      const stats = { ...createMockStats(), total_distance: 15432 }

      const wrapper = mount(SegmentCard, {
        props: { segment, stats }
      })

      const metrics = wrapper.findAll('.metric')
      const distanceMetric = metrics.find(
        (m) => m.find('.metric-label').text() === 'Distance'
      )
      expect(distanceMetric?.find('.metric-value').text()).toBe('15.4km')
    })
  })

  describe('Surface Type', () => {
    it('should display formatted surface type', () => {
      const segment = createMockSegment(1, 'Test Segment', {
        surface_type: 'forest-trail'
      })
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats() }
      })

      const surfaceInfo = wrapper.find('.info-section .info-value span')
      expect(surfaceInfo.text()).toBe('Forest Trail')
    })

    it('should format different surface types correctly', () => {
      const testCases = [
        { input: 'forest-trail', expected: 'Forest Trail' },
        { input: 'big-stone-road', expected: 'Big Stone Road' },
        { input: 'gravel', expected: 'Gravel' }
      ]

      testCases.forEach(({ input, expected }) => {
        const segment = createMockSegment(1, 'Test Segment', { surface_type: input })
        const wrapper = mount(SegmentCard, {
          props: { segment, stats: createMockStats() }
        })

        const surfaceInfo = wrapper.find('.info-section .info-value span')
        expect(surfaceInfo.text()).toBe(expected)
      })
    })

    it('should handle empty surface type', () => {
      const segment = createMockSegment(1, 'Test Segment', { surface_type: '' })
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats() }
      })

      const surfaceInfo = wrapper.find('.info-section .info-value span')
      expect(surfaceInfo.text()).toBe('')
    })

    it('should display surface type icon', () => {
      const segment = createMockSegment(1, 'Test Segment')
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats() }
      })

      const surfaceIcon = wrapper.find('.info-section .info-value .fa-road')
      expect(surfaceIcon.exists()).toBe(true)
    })
  })

  describe('Tire Recommendations', () => {
    it('should display dry tire recommendation', () => {
      const segment = createMockSegment(1, 'Test Segment', { tire_dry: 'semi-slick' })
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats() }
      })

      const tireBadges = wrapper.findAll('.tire-badge')
      expect(tireBadges[0].text()).toBe('Semi Slick')
    })

    it('should display wet tire recommendation', () => {
      const segment = createMockSegment(1, 'Test Segment', { tire_wet: 'knobs' })
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats() }
      })

      const tireBadges = wrapper.findAll('.tire-badge')
      expect(tireBadges[1].text()).toBe('Knobs')
    })

    it('should format tire types with multiple words', () => {
      const segment = createMockSegment(1, 'Test Segment', {
        tire_dry: 'super-knobs',
        tire_wet: 'mega-grip'
      })
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats() }
      })

      const tireBadges = wrapper.findAll('.tire-badge')
      expect(tireBadges[0].text()).toBe('Super Knobs')
      expect(tireBadges[1].text()).toBe('Mega Grip')
    })

    it('should display tire recommendation icons', () => {
      const segment = createMockSegment(1, 'Test Segment')
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats() }
      })

      const sunIcon = wrapper.find('.fa-sun')
      const cloudIcon = wrapper.find('.fa-cloud-rain')
      expect(sunIcon.exists()).toBe(true)
      expect(cloudIcon.exists()).toBe(true)
    })

    it('should handle empty tire types', () => {
      const segment = createMockSegment(1, 'Test Segment', {
        tire_dry: '',
        tire_wet: ''
      })
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats() }
      })

      const tireBadges = wrapper.findAll('.tire-badge')
      expect(tireBadges[0].text()).toBe('')
      expect(tireBadges[1].text()).toBe('')
    })
  })

  describe('Difficulty Level', () => {
    it('should display difficulty level', () => {
      const segment = createMockSegment(1, 'Test Segment', { difficulty_level: 3 })
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats() }
      })

      const difficultyInfo = wrapper.find('.difficulty span')
      expect(difficultyInfo.text()).toBe('3/5')
    })

    it('should display different difficulty levels', () => {
      const levels = [1, 2, 3, 4, 5]

      levels.forEach((level) => {
        const segment = createMockSegment(1, 'Test Segment', {
          difficulty_level: level
        })
        const wrapper = mount(SegmentCard, {
          props: { segment, stats: createMockStats() }
        })

        const difficultyInfo = wrapper.find('.difficulty span')
        expect(difficultyInfo.text()).toBe(`${level}/5`)
      })
    })

    it('should display difficulty icon', () => {
      const segment = createMockSegment(1, 'Test Segment')
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats() }
      })

      const difficultyIcon = wrapper.find('.difficulty .fa-signal')
      expect(difficultyIcon.exists()).toBe(true)
    })
  })

  describe('Distance from Center', () => {
    it('should display distance from center when provided', () => {
      const segment = createMockSegment(1, 'Test Segment')
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats(), distanceFromCenter: 1500 }
      })

      const distanceElement = wrapper.find('.segment-distance')
      expect(distanceElement.exists()).toBe(true)
      expect(distanceElement.text()).toContain('to📍')
    })

    it('should not display distance from center when not provided', () => {
      const segment = createMockSegment(1, 'Test Segment')
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats() }
      })

      const distanceElement = wrapper.find('.segment-distance')
      expect(distanceElement.exists()).toBe(false)
    })

    it('should have proper title attribute', () => {
      const segment = createMockSegment(1, 'Test Segment')
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats(), distanceFromCenter: 1500 }
      })

      const distanceElement = wrapper.find('.segment-distance')
      expect(distanceElement.attributes('title')).toBe('Distance from map center')
    })
  })

  describe('Event Handling', () => {
    it('should emit click event when card is clicked', async () => {
      const segment = createMockSegment(1, 'Test Segment')
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats() }
      })

      await wrapper.find('.segment-card').trigger('click')

      expect(wrapper.emitted('click')).toBeTruthy()
      expect(wrapper.emitted('click')?.[0]).toEqual([segment])
    })

    it('should emit mouseenter event when card is hovered', async () => {
      const segment = createMockSegment(1, 'Test Segment')
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats() }
      })

      await wrapper.find('.segment-card').trigger('mouseenter')

      expect(wrapper.emitted('mouseenter')).toBeTruthy()
      expect(wrapper.emitted('mouseenter')?.[0]).toEqual([segment])
    })

    it('should emit mouseleave event when card is left', async () => {
      const segment = createMockSegment(1, 'Test Segment')
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats() }
      })

      await wrapper.find('.segment-card').trigger('mouseleave')

      expect(wrapper.emitted('mouseleave')).toBeTruthy()
      expect(wrapper.emitted('mouseleave')?.[0]).toEqual([segment])
    })
  })

  describe('Card Structure', () => {
    it('should have proper card structure', () => {
      const segment = createMockSegment(1, 'Test Segment')
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats() }
      })

      expect(wrapper.find('.segment-card-header').exists()).toBe(true)
      expect(wrapper.find('.segment-card-content').exists()).toBe(true)
      expect(wrapper.find('.segment-card-footer').exists()).toBe(true)
    })

    it('should have metrics grid with 3 columns', () => {
      const segment = createMockSegment(1, 'Test Segment')
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats() }
      })

      const metrics = wrapper.findAll('.metric')
      expect(metrics.length).toBe(3)
    })

    it('should have info grid with 3 sections', () => {
      const segment = createMockSegment(1, 'Test Segment')
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats() }
      })

      const infoSections = wrapper.findAll('.info-section')
      expect(infoSections.length).toBe(3)
    })
  })

  describe('Edge Cases', () => {
    it('should handle zero distance', () => {
      const segment = createMockSegment(1, 'Test Segment')
      const stats = { ...createMockStats(), total_distance: 0 }

      const wrapper = mount(SegmentCard, {
        props: { segment, stats }
      })

      const metrics = wrapper.findAll('.metric')
      const distanceMetric = metrics.find(
        (m) => m.find('.metric-label').text() === 'Distance'
      )
      expect(distanceMetric?.find('.metric-value').text()).toBe('0m')
    })

    it('should handle zero elevation', () => {
      const segment = createMockSegment(1, 'Test Segment')
      const stats = {
        ...createMockStats(),
        total_elevation_gain: 0,
        total_elevation_loss: 0
      }

      const wrapper = mount(SegmentCard, {
        props: { segment, stats }
      })

      const metrics = wrapper.findAll('.metric')
      const elevationGainMetric = metrics.find((m) =>
        m.find('.metric-label').text().includes('Elevation Gain')
      )
      const elevationLossMetric = metrics.find((m) =>
        m.find('.metric-label').text().includes('Elevation Loss')
      )

      expect(elevationGainMetric?.find('.metric-value').text()).toBe('0m')
      expect(elevationLossMetric?.find('.metric-value').text()).toBe('0m')
    })

    it('should handle very large numbers', () => {
      const segment = createMockSegment(1, 'Test Segment')
      const stats = {
        total_distance: 999999,
        total_elevation_gain: 9999,
        total_elevation_loss: 9999
      }

      const wrapper = mount(SegmentCard, {
        props: { segment, stats }
      })

      expect(wrapper.find('.segment-card').exists()).toBe(true)
    })

    it('should handle special characters in segment name', () => {
      const segment = createMockSegment(1, "Test & Segment <with> 'quotes'")
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats() }
      })

      expect(wrapper.find('.segment-name').text()).toBe(
        "Test & Segment <with> 'quotes'"
      )
    })

    it('should handle special characters in surface and tire types', () => {
      const segment = createMockSegment(1, 'Test Segment', {
        surface_type: 'test-surface-type',
        tire_dry: 'test-tire-dry',
        tire_wet: 'test-tire-wet'
      })
      const wrapper = mount(SegmentCard, {
        props: { segment, stats: createMockStats() }
      })

      expect(wrapper.find('.segment-card').exists()).toBe(true)
    })
  })
})
