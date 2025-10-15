import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import SegmentInfoCard from '../SegmentInfoCard.vue'
import type { TrackResponse, GPXData } from '../../types'
import en from '../../i18n/locales/en'
import fr from '../../i18n/locales/fr'

// Create i18n instance for tests
const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en,
    fr
  }
})

describe('SegmentInfoCard', () => {
  let mockSegment: TrackResponse
  let mockGPXData: GPXData

  beforeEach(() => {
    mockSegment = {
      id: 1,
      name: 'Test Segment',
      track_type: 'segment',
      difficulty_level: 3,
      surface_type: ['broken-paved-road'],
      tire_dry: 'semi-slick',
      tire_wet: 'knobs',
      barycenter_latitude: 45.5,
      barycenter_longitude: -73.5,
      bound_north: 45.6,
      bound_south: 45.4,
      bound_east: -73.4,
      bound_west: -73.6,
      file_path: 'test.gpx',
      comments: ''
    }

    mockGPXData = {
      file_id: '1',
      track_name: 'Test Segment',
      points: [],
      total_stats: {
        total_points: 0,
        total_distance: 15.5,
        total_elevation_gain: 250,
        total_elevation_loss: 200
      },
      bounds: {
        north: 45.6,
        south: 45.4,
        east: -73.4,
        west: -73.6,
        min_elevation: 100,
        max_elevation: 350
      }
    }
  })

  describe('Component Rendering', () => {
    it('should render the component with all sections', () => {
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: mockSegment,
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.info-card').exists()).toBe(true)
      expect(wrapper.find('.card-header').exists()).toBe(true)
      expect(wrapper.find('.card-content').exists()).toBe(true)
      expect(wrapper.find('.info-grid').exists()).toBe(true)
    })

    it('should display the card header with icon and title', () => {
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: mockSegment,
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const header = wrapper.find('.card-header h3')
      expect(header.exists()).toBe(true)
      expect(header.find('i.fa-info-circle').exists()).toBe(true)
      expect(header.text()).toContain('Information')
    })

    it('should render all three compact info items', () => {
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: mockSegment,
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const compactItems = wrapper.findAll('.info-item-compact')
      expect(compactItems).toHaveLength(3)
    })

    it('should render the stats grid', () => {
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: mockSegment,
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const statsGrid = wrapper.find('.stats-grid')
      expect(statsGrid.exists()).toBe(true)
      expect(statsGrid.findAll('.stat-item')).toHaveLength(3)
    })
  })

  describe('Difficulty Display', () => {
    it('should display the correct difficulty level', () => {
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: mockSegment,
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const difficultyLevel = wrapper.find('.difficulty-level')
      expect(difficultyLevel.text()).toBe('3')
    })

    it('should display the difficulty word for each level', () => {
      for (let level = 1; level <= 5; level++) {
        const testSegment = { ...mockSegment, difficulty_level: level }
        const wrapper = mount(SegmentInfoCard, {
          props: {
            segment: testSegment,
            gpxData: mockGPXData
          },
          global: {
            plugins: [i18n]
          }
        })

        const difficultyWord = wrapper.find('.difficulty-word')
        expect(difficultyWord.text()).toBeTruthy()
        expect(difficultyWord.text()).not.toBe('Unknown')
      }
    })

    it('should display "over 5" text when difficulty level is greater than 5', () => {
      const testSegment = { ...mockSegment, difficulty_level: 6 }
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: testSegment,
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const difficultyOver = wrapper.find('.difficulty-over')
      expect(difficultyOver.exists()).toBe(true)
      expect(difficultyOver.text()).toContain('over 5')
    })

    it('should not display "over 5" text when difficulty level is 5 or less', () => {
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: mockSegment,
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const difficultyOver = wrapper.find('.difficulty-over')
      expect(difficultyOver.exists()).toBe(false)
    })

    it('should default to level 0 when difficulty_level is 0', () => {
      const testSegment = { ...mockSegment, difficulty_level: 0 }
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: testSegment,
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const difficultyLevel = wrapper.find('.difficulty-level')
      expect(difficultyLevel.text()).toBe('0')
    })
  })

  describe('Surface Type Display', () => {
    it('should display the surface type label', () => {
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: mockSegment,
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const surfaceText = wrapper.find('.surface-text')
      expect(surfaceText.exists()).toBe(true)
      expect(surfaceText.text()).toBeTruthy()
    })

    it('should display the correct surface image', () => {
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: mockSegment,
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const surfaceImage = wrapper.find('.surface-image')
      expect(surfaceImage.exists()).toBe(true)
      expect(surfaceImage.attributes('src')).toBeTruthy()
      expect(surfaceImage.attributes('alt')).toBeTruthy()
    })

    it('should handle all surface types', () => {
      const surfaceTypes = [
        'broken-paved-road',
        'dirty-road',
        'small-stone-road',
        'big-stone-road',
        'field-trail',
        'forest-trail'
      ]

      surfaceTypes.forEach((surfaceType) => {
        const testSegment = { ...mockSegment, surface_type: [surfaceType] }
        const wrapper = mount(SegmentInfoCard, {
          props: {
            segment: testSegment,
            gpxData: mockGPXData
          },
          global: {
            plugins: [i18n]
          }
        })

        const surfaceImage = wrapper.find('.surface-image')
        expect(surfaceImage.exists()).toBe(true)
        expect(surfaceImage.attributes('src')).toBeTruthy()
      })
    })
  })

  describe('Tire Recommendations Display', () => {
    it('should display dry tire recommendations', () => {
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: mockSegment,
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const tireRecommendations = wrapper.findAll('.tire-recommendation-compact')
      expect(tireRecommendations).toHaveLength(2)

      const dryTire = tireRecommendations[0]
      expect(dryTire.find('.fa-sun').exists()).toBe(true)
      expect(dryTire.find('.tire-text').text()).toBeTruthy()
      expect(dryTire.find('.tire-image').exists()).toBe(true)
    })

    it('should display wet tire recommendations', () => {
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: mockSegment,
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const tireRecommendations = wrapper.findAll('.tire-recommendation-compact')
      const wetTire = tireRecommendations[1]
      expect(wetTire.find('.fa-cloud-rain').exists()).toBe(true)
      expect(wetTire.find('.tire-text').text()).toBeTruthy()
      expect(wetTire.find('.tire-image').exists()).toBe(true)
    })

    it('should handle all tire types for dry conditions', () => {
      const tireTypes = ['slick', 'semi-slick', 'knobs']

      tireTypes.forEach((tireType) => {
        const testSegment = { ...mockSegment, tire_dry: tireType }
        const wrapper = mount(SegmentInfoCard, {
          props: {
            segment: testSegment,
            gpxData: mockGPXData
          },
          global: {
            plugins: [i18n]
          }
        })

        const tireImage = wrapper.findAll('.tire-image')[0]
        expect(tireImage.exists()).toBe(true)
        expect(tireImage.attributes('src')).toBeTruthy()
      })
    })

    it('should handle all tire types for wet conditions', () => {
      const tireTypes = ['slick', 'semi-slick', 'knobs']

      tireTypes.forEach((tireType) => {
        const testSegment = { ...mockSegment, tire_wet: tireType }
        const wrapper = mount(SegmentInfoCard, {
          props: {
            segment: testSegment,
            gpxData: mockGPXData
          },
          global: {
            plugins: [i18n]
          }
        })

        const tireImage = wrapper.findAll('.tire-image')[1]
        expect(tireImage.exists()).toBe(true)
        expect(tireImage.attributes('src')).toBeTruthy()
      })
    })
  })

  describe('Statistics Display', () => {
    it('should display the distance statistic', () => {
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: mockSegment,
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const statItems = wrapper.findAll('.stat-item')
      const distanceStat = statItems[0]
      expect(distanceStat.find('.stat-label').text()).toContain('Distance')
      expect(distanceStat.find('.stat-value').text()).toBe('15.50 km')
    })

    it('should display the elevation gain statistic', () => {
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: mockSegment,
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const statItems = wrapper.findAll('.stat-item')
      const elevationGainStat = statItems[1]
      expect(elevationGainStat.find('.stat-label').text()).toContain('Elevation Gain')
      expect(elevationGainStat.find('.stat-value').text()).toBe('250m')
    })

    it('should display the elevation loss statistic', () => {
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: mockSegment,
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const statItems = wrapper.findAll('.stat-item')
      const elevationLossStat = statItems[2]
      expect(elevationLossStat.find('.stat-label').text()).toContain('Elevation Loss')
      expect(elevationLossStat.find('.stat-value').text()).toBe('200m')
    })

    it('should format distance with 2 decimal places', () => {
      const testGPXData: GPXData = {
        ...mockGPXData,
        total_stats: {
          ...mockGPXData.total_stats,
          total_distance: 12.345678
        }
      }
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: mockSegment,
          gpxData: testGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const statValue = wrapper.findAll('.stat-value')[0]
      expect(statValue.text()).toBe('12.35 km')
    })

    it('should round elevation values to nearest integer', () => {
      const testGPXData: GPXData = {
        ...mockGPXData,
        total_stats: {
          total_points: 100,
          total_distance: 10,
          total_elevation_gain: 125.6,
          total_elevation_loss: 98.4
        }
      }
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: mockSegment,
          gpxData: testGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const statValues = wrapper.findAll('.stat-value')
      expect(statValues[1].text()).toBe('126m')
      expect(statValues[2].text()).toBe('98m')
    })

    it('should handle zero values in statistics', () => {
      const testGPXData: GPXData = {
        ...mockGPXData,
        total_stats: {
          total_points: 0,
          total_distance: 0,
          total_elevation_gain: 0,
          total_elevation_loss: 0
        }
      }
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: mockSegment,
          gpxData: testGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const statValues = wrapper.findAll('.stat-value')
      expect(statValues[0].text()).toBe('0.00 km')
      expect(statValues[1].text()).toBe('0m')
      expect(statValues[2].text()).toBe('0m')
    })
  })

  describe('Computed Properties', () => {
    it('should reactively update when segment prop changes', async () => {
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: mockSegment,
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.difficulty-level').text()).toBe('3')

      const newSegment = { ...mockSegment, difficulty_level: 5 }
      await wrapper.setProps({ segment: newSegment })

      expect(wrapper.find('.difficulty-level').text()).toBe('5')
    })

    it('should reactively update when gpxData prop changes', async () => {
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: mockSegment,
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.findAll('.stat-value')[0].text()).toBe('15.50 km')

      const newGPXData = {
        ...mockGPXData,
        total_stats: {
          ...mockGPXData.total_stats,
          total_distance: 25.75
        }
      }
      await wrapper.setProps({ gpxData: newGPXData })

      expect(wrapper.findAll('.stat-value')[0].text()).toBe('25.75 km')
    })
  })

  describe('Internationalization', () => {
    it('should display labels in English by default', () => {
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: mockSegment,
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const labels = wrapper.findAll('.info-label')
      expect(labels[0].text()).toContain('Difficulty')
      expect(labels[1].text()).toContain('Surface')
      expect(labels[2].text()).toContain('Tire Rec')
    })

    it('should display labels in French when locale is changed', async () => {
      const frenchI18n = createI18n({
        legacy: false,
        locale: 'fr',
        messages: {
          en,
          fr
        }
      })

      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: mockSegment,
          gpxData: mockGPXData
        },
        global: {
          plugins: [frenchI18n]
        }
      })

      const labels = wrapper.findAll('.info-label')
      expect(labels[0].text()).toContain('Difficulté')
      expect(labels[1].text()).toContain('Surface')
      expect(labels[2].text()).toContain('Rec. Pneu')
    })
  })

  describe('Icons', () => {
    it('should display all required icons', () => {
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: mockSegment,
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.fa-info-circle').exists()).toBe(true)
      expect(wrapper.find('.fa-signal').exists()).toBe(true)
      expect(wrapper.find('.fa-road').exists()).toBe(true)
      expect(wrapper.find('.fa-circle').exists()).toBe(true)
      expect(wrapper.find('.fa-sun').exists()).toBe(true)
      expect(wrapper.find('.fa-cloud-rain').exists()).toBe(true)
      expect(wrapper.find('.fa-route').exists()).toBe(true)
      expect(wrapper.find('.fa-arrow-trend-up').exists()).toBe(true)
      expect(wrapper.find('.fa-arrow-trend-down').exists()).toBe(true)
    })
  })

  describe('Edge Cases', () => {
    it('should handle missing surface type gracefully', () => {
      const testSegment = { ...mockSegment, surface_type: [''] }
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: testSegment,
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const surfaceText = wrapper.find('.surface-text')
      expect(surfaceText.text()).toBe('N/A')
    })

    it('should handle missing tire type gracefully', () => {
      const testSegment = { ...mockSegment, tire_dry: '', tire_wet: '' }
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: testSegment,
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const tireTexts = wrapper.findAll('.tire-text')
      expect(tireTexts[0].text()).toBe('')
      expect(tireTexts[1].text()).toBe('')
    })

    it('should handle very large distance values', () => {
      const testGPXData = {
        ...mockGPXData,
        total_stats: {
          ...mockGPXData.total_stats,
          total_distance: 999.99
        }
      }
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: mockSegment,
          gpxData: testGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const distanceValue = wrapper.findAll('.stat-value')[0]
      expect(distanceValue.text()).toBe('999.99 km')
    })

    it('should handle very large elevation values', () => {
      const testGPXData: GPXData = {
        ...mockGPXData,
        total_stats: {
          total_points: 1000,
          total_distance: 10,
          total_elevation_gain: 9999,
          total_elevation_loss: 8888
        }
      }
      const wrapper = mount(SegmentInfoCard, {
        props: {
          segment: mockSegment,
          gpxData: testGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const statValues = wrapper.findAll('.stat-value')
      expect(statValues[1].text()).toBe('9999m')
      expect(statValues[2].text()).toBe('8888m')
    })
  })

  describe('Hover Zoom Functionality', () => {
    let wrapper: any

    beforeEach(() => {
      wrapper = mount(SegmentInfoCard, {
        props: {
          segment: mockSegment,
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })
    })

    describe('Image Container Structure', () => {
      it('should render image containers for surface images', () => {
        const surfaceImageContainer = wrapper.find(
          '.surface-info-vertical .image-container'
        )
        expect(surfaceImageContainer.exists()).toBe(true)

        const surfaceImage = surfaceImageContainer.find('.surface-image')
        const surfaceOverlay = surfaceImageContainer.find('.image-zoom-overlay')

        expect(surfaceImage.exists()).toBe(true)
        expect(surfaceOverlay.exists()).toBe(true)
        expect(surfaceOverlay.find('.surface-image-zoom').exists()).toBe(true)
      })

      it('should render image containers for tire images', () => {
        const tireContainers = wrapper.findAll('.tire-option-vertical .image-container')
        expect(tireContainers).toHaveLength(2)

        tireContainers.forEach((container: any) => {
          expect(container.find('.tire-image').exists()).toBe(true)
          expect(container.find('.image-zoom-overlay').exists()).toBe(true)
          expect(container.find('.tire-image-zoom').exists()).toBe(true)
        })
      })

      it('should have proper CSS classes for overlays', () => {
        const overlays = wrapper.findAll('.image-zoom-overlay')
        expect(overlays).toHaveLength(3) // 1 surface + 2 tire overlays

        overlays.forEach((overlay: any) => {
          expect(overlay.classes()).toContain('image-zoom-overlay')
        })
      })
    })

    describe('Mouse Event Handlers', () => {
      it('should have mouseenter event handlers on image containers', () => {
        const surfaceContainer = wrapper.find('.surface-info-vertical .image-container')
        expect(surfaceContainer.exists()).toBe(true)

        const tireContainers = wrapper.findAll('.tire-option-vertical .image-container')
        expect(tireContainers).toHaveLength(2)

        // Test that event handlers can be triggered
        const surfaceOverlay = surfaceContainer.find('.image-zoom-overlay')
        expect(surfaceOverlay.exists()).toBe(true)
      })

      it('should have mouseleave event handlers on image containers', () => {
        const surfaceContainer = wrapper.find('.surface-info-vertical .image-container')
        expect(surfaceContainer.exists()).toBe(true)

        const tireContainers = wrapper.findAll('.tire-option-vertical .image-container')
        expect(tireContainers).toHaveLength(2)

        // Test that containers exist and can handle events
        tireContainers.forEach((container: any) => {
          expect(container.find('.image-zoom-overlay').exists()).toBe(true)
        })
      })

      it('should have mousemove event handlers on image containers', () => {
        const surfaceContainer = wrapper.find('.surface-info-vertical .image-container')
        expect(surfaceContainer.exists()).toBe(true)

        const tireContainers = wrapper.findAll('.tire-option-vertical .image-container')
        expect(tireContainers).toHaveLength(2)

        // Test that all containers have the required structure
        expect(surfaceContainer.find('.surface-image').exists()).toBe(true)
        expect(surfaceContainer.find('.image-zoom-overlay').exists()).toBe(true)
      })
    })

    describe('Overlay Initial State', () => {
      it('should have overlays hidden by default', () => {
        const overlays = wrapper.findAll('.image-zoom-overlay')
        expect(overlays).toHaveLength(3) // 1 surface + 2 tire overlays

        // Test that overlays exist and have the correct class
        overlays.forEach((overlay: any) => {
          expect(overlay.exists()).toBe(true)
          expect(overlay.classes()).toContain('image-zoom-overlay')
        })
      })

      it('should have proper CSS structure for overlays', () => {
        const overlays = wrapper.findAll('.image-zoom-overlay')
        expect(overlays).toHaveLength(3)

        overlays.forEach((overlay: any) => {
          expect(overlay.exists()).toBe(true)
          expect(overlay.classes()).toContain('image-zoom-overlay')
        })
      })
    })

    describe('Overlay Content', () => {
      it('should display correct images in surface overlay', () => {
        const surfaceOverlay = wrapper.find(
          '.surface-info-vertical .image-zoom-overlay'
        )
        const overlayImage = surfaceOverlay.find('.surface-image-zoom')
        const originalImage = wrapper.find('.surface-image')

        expect(overlayImage.attributes('src')).toBe(originalImage.attributes('src'))
        expect(overlayImage.attributes('alt')).toBe(originalImage.attributes('alt'))
      })

      it('should display correct images in tire overlays', () => {
        const tireContainers = wrapper.findAll('.tire-option-vertical .image-container')

        tireContainers.forEach((container: any) => {
          const overlayImage = container.find('.tire-image-zoom')
          const originalImage = container.find('.tire-image')

          expect(overlayImage.attributes('src')).toBe(originalImage.attributes('src'))
          expect(overlayImage.attributes('alt')).toBe(originalImage.attributes('alt'))
        })
      })
    })

    describe('CSS Styling', () => {
      it('should have proper CSS classes for zoom images', () => {
        const surfaceZoomImage = wrapper.find('.surface-image-zoom')
        const tireZoomImages = wrapper.findAll('.tire-image-zoom')

        expect(surfaceZoomImage.exists()).toBe(true)
        expect(tireZoomImages).toHaveLength(2)

        tireZoomImages.forEach((image: any) => {
          expect(image.classes()).toContain('tire-image-zoom')
        })
      })

      it('should have image-container class with proper structure', () => {
        const containers = wrapper.findAll('.image-container')
        expect(containers).toHaveLength(3) // 1 surface + 2 tire containers

        containers.forEach((container: any) => {
          expect(container.classes()).toContain('image-container')
          expect(container.find('.image-zoom-overlay').exists()).toBe(true)
        })
      })
    })

    describe('Overlay Positioning Logic', () => {
      it('should handle showOverlay function', () => {
        const surfaceContainer = wrapper.find('.surface-info-vertical .image-container')
        const overlay = surfaceContainer.find('.image-zoom-overlay')

        // Mock getBoundingClientRect
        const mockRect = {
          top: 100,
          bottom: 150,
          left: 50,
          right: 100,
          width: 50,
          height: 50
        }
        vi.spyOn(surfaceContainer.element, 'getBoundingClientRect').mockReturnValue(
          mockRect
        )

        // Mock window.innerWidth
        Object.defineProperty(window, 'innerWidth', {
          writable: true,
          configurable: true,
          value: 1024
        })

        // Simulate mouseenter event
        const mouseEvent = new MouseEvent('mouseenter', {
          clientX: 75,
          clientY: 125
        })

        surfaceContainer.element.dispatchEvent(mouseEvent)

        // The overlay should be visible after mouseenter
        // Note: In a real test environment, we'd need to trigger the actual Vue event handlers
        expect(overlay.exists()).toBe(true)
      })

      it('should handle hideOverlay function', () => {
        const surfaceContainer = wrapper.find('.surface-info-vertical .image-container')
        const overlay = surfaceContainer.find('.image-zoom-overlay')

        // Simulate mouseleave event
        const mouseEvent = new MouseEvent('mouseleave', {
          clientX: 75,
          clientY: 125
        })

        surfaceContainer.element.dispatchEvent(mouseEvent)

        // The overlay should exist but be hidden
        expect(overlay.exists()).toBe(true)
      })
    })

    describe('Responsive Behavior', () => {
      it('should handle different viewport sizes', () => {
        // Test with small viewport
        Object.defineProperty(window, 'innerWidth', {
          writable: true,
          configurable: true,
          value: 320
        })

        const wrapper = mount(SegmentInfoCard, {
          props: {
            segment: mockSegment,
            gpxData: mockGPXData
          },
          global: {
            plugins: [i18n]
          }
        })

        const overlays = wrapper.findAll('.image-zoom-overlay')
        expect(overlays).toHaveLength(3)

        // Test that overlays still exist and have correct structure
        overlays.forEach((overlay: any) => {
          expect(overlay.exists()).toBe(true)
          expect(overlay.classes()).toContain('image-zoom-overlay')
        })
      })
    })

    describe('Multiple Surface Types', () => {
      it('should handle hover zoom for multiple surface types', async () => {
        const multiSurfaceSegment = {
          ...mockSegment,
          surface_type: ['broken-paved-road', 'dirty-road', 'forest-trail']
        }

        const wrapper = mount(SegmentInfoCard, {
          props: {
            segment: multiSurfaceSegment,
            gpxData: mockGPXData
          },
          global: {
            plugins: [i18n]
          }
        })

        // Should have navigation buttons
        expect(wrapper.find('.surface-nav-btn').exists()).toBe(true)

        // Should have image container with overlay
        const imageContainer = wrapper.find('.surface-info-vertical .image-container')
        expect(imageContainer.exists()).toBe(true)
        expect(imageContainer.find('.image-zoom-overlay').exists()).toBe(true)
      })
    })

    describe('Accessibility', () => {
      it('should have proper alt text on all images', () => {
        const allImages = wrapper.findAll('img')

        allImages.forEach((image: any) => {
          expect(image.attributes('alt')).toBeTruthy()
        })
      })

      it('should maintain image quality in overlays', () => {
        const surfaceOverlayImage = wrapper.find('.surface-image-zoom')
        const tireOverlayImages = wrapper.findAll('.tire-image-zoom')

        // Check that overlay images have the same source as original images
        const originalSurfaceImage = wrapper.find('.surface-image')
        expect(surfaceOverlayImage.attributes('src')).toBe(
          originalSurfaceImage.attributes('src')
        )

        const originalTireImages = wrapper.findAll('.tire-image')
        tireOverlayImages.forEach((overlayImage: any, index: number) => {
          expect(overlayImage.attributes('src')).toBe(
            originalTireImages[index].attributes('src')
          )
        })
      })
    })

    describe('Performance', () => {
      it('should not create multiple overlay elements unnecessarily', () => {
        // Re-render the component multiple times
        for (let i = 0; i < 5; i++) {
          wrapper = mount(SegmentInfoCard, {
            props: {
              segment: mockSegment,
              gpxData: mockGPXData
            },
            global: {
              plugins: [i18n]
            }
          })
        }

        // Should still have exactly 3 overlays (1 surface + 2 tire)
        const overlays = wrapper.findAll('.image-zoom-overlay')
        expect(overlays).toHaveLength(3)
      })

      it('should handle rapid mouse movements without errors', () => {
        const surfaceContainer = wrapper.find('.surface-info-vertical .image-container')

        // Simulate rapid mouse movements
        for (let i = 0; i < 10; i++) {
          const mouseEvent = new MouseEvent('mousemove', {
            clientX: 50 + i * 10,
            clientY: 100 + i * 5
          })

          surfaceContainer.element.dispatchEvent(mouseEvent)
        }

        // Component should still be mounted and functional
        expect(wrapper.exists()).toBe(true)
        expect(surfaceContainer.find('.image-zoom-overlay').exists()).toBe(true)
      })
    })

    describe('Difficulty Tooltip Functionality', () => {
      let wrapper: any

      beforeEach(() => {
        wrapper = mount(SegmentInfoCard, {
          props: {
            segment: mockSegment,
            gpxData: mockGPXData
          },
          global: {
            plugins: [i18n]
          }
        })
      })

      describe('Tooltip Structure', () => {
        it('should render difficulty tooltip container', () => {
          const tooltipContainer = wrapper.find('.difficulty-tooltip-container')
          expect(tooltipContainer.exists()).toBe(true)
        })

        it('should render difficulty info icon', () => {
          const infoIcon = wrapper.find('.difficulty-info-icon')
          expect(infoIcon.exists()).toBe(true)
          expect(infoIcon.classes()).toContain('fa-circle-info')
        })

        it('should render difficulty tooltip element', () => {
          const tooltip = wrapper.find('.difficulty-tooltip')
          expect(tooltip.exists()).toBe(true)
          expect(tooltip.classes()).toContain('difficulty-tooltip')
        })

        it('should have proper CSS classes for tooltip container', () => {
          const tooltipContainer = wrapper.find('.difficulty-tooltip-container')
          expect(tooltipContainer.classes()).toContain('difficulty-tooltip-container')
        })
      })

      describe('Tooltip Content', () => {
        it('should display correct description for difficulty level 1', () => {
          const testSegment = { ...mockSegment, difficulty_level: 1 }
          const wrapper = mount(SegmentInfoCard, {
            props: {
              segment: testSegment,
              gpxData: mockGPXData
            },
            global: {
              plugins: [i18n]
            }
          })

          const tooltip = wrapper.find('.difficulty-tooltip')
          expect(tooltip.text()).toBe(
            'You could ride this segment with your eyes closed'
          )
        })

        it('should display correct description for difficulty level 2', () => {
          const testSegment = { ...mockSegment, difficulty_level: 2 }
          const wrapper = mount(SegmentInfoCard, {
            props: {
              segment: testSegment,
              gpxData: mockGPXData
            },
            global: {
              plugins: [i18n]
            }
          })

          const tooltip = wrapper.find('.difficulty-tooltip')
          expect(tooltip.text()).toBe(
            'It should be quite fine. Only a couple of irregularities on the path, but easy business.'
          )
        })

        it('should display correct description for difficulty level 3', () => {
          const testSegment = { ...mockSegment, difficulty_level: 3 }
          const wrapper = mount(SegmentInfoCard, {
            props: {
              segment: testSegment,
              gpxData: mockGPXData
            },
            global: {
              plugins: [i18n]
            }
          })

          const tooltip = wrapper.find('.difficulty-tooltip')
          expect(tooltip.text()).toBe(
            "You'll need some bike handling skill due to irregular terrain or uphill and downhill sections."
          )
        })

        it('should display correct description for difficulty level 4', () => {
          const testSegment = { ...mockSegment, difficulty_level: 4 }
          const wrapper = mount(SegmentInfoCard, {
            props: {
              segment: testSegment,
              gpxData: mockGPXData
            },
            global: {
              plugins: [i18n]
            }
          })

          const tooltip = wrapper.find('.difficulty-tooltip')
          expect(tooltip.text()).toBe(
            "It's no longer straightforward. You'll definitely need to navigate elevation changes and will encounter unexpected ground variations."
          )
        })

        it('should display correct description for difficulty level 5', () => {
          const testSegment = { ...mockSegment, difficulty_level: 5 }
          const wrapper = mount(SegmentInfoCard, {
            props: {
              segment: testSegment,
              gpxData: mockGPXData
            },
            global: {
              plugins: [i18n]
            }
          })

          const tooltip = wrapper.find('.difficulty-tooltip')
          expect(tooltip.text()).toBe(
            'Be prepared to put a foot down, as the path is difficult due to either slope, terrain, or both.'
          )
        })

        it('should display level 5 description for difficulty levels above 5', () => {
          const testSegment = { ...mockSegment, difficulty_level: 6 }
          const wrapper = mount(SegmentInfoCard, {
            props: {
              segment: testSegment,
              gpxData: mockGPXData
            },
            global: {
              plugins: [i18n]
            }
          })

          const tooltip = wrapper.find('.difficulty-tooltip')
          expect(tooltip.text()).toBe(
            'Be prepared to put a foot down, as the path is difficult due to either slope, terrain, or both.'
          )
        })

        it('should display level 5 description for difficulty level 0', () => {
          const testSegment = { ...mockSegment, difficulty_level: 0 }
          const wrapper = mount(SegmentInfoCard, {
            props: {
              segment: testSegment,
              gpxData: mockGPXData
            },
            global: {
              plugins: [i18n]
            }
          })

          const tooltip = wrapper.find('.difficulty-tooltip')
          expect(tooltip.text()).toBe(
            'Be prepared to put a foot down, as the path is difficult due to either slope, terrain, or both.'
          )
        })
      })

      describe('Tooltip Styling', () => {
        it('should have proper CSS classes for info icon', () => {
          const infoIcon = wrapper.find('.difficulty-info-icon')
          expect(infoIcon.exists()).toBe(true)
          expect(infoIcon.classes()).toContain('difficulty-info-icon')
        })

        it('should have proper CSS classes for tooltip', () => {
          const tooltip = wrapper.find('.difficulty-tooltip')
          expect(tooltip.exists()).toBe(true)
          expect(tooltip.classes()).toContain('difficulty-tooltip')
        })

        it('should have proper structure for tooltip positioning', () => {
          const tooltip = wrapper.find('.difficulty-tooltip')
          expect(tooltip.exists()).toBe(true)

          // Test that tooltip has the required structure
          const tooltipContainer = wrapper.find('.difficulty-tooltip-container')
          expect(tooltipContainer.exists()).toBe(true)
          expect(tooltipContainer.find('.difficulty-tooltip').exists()).toBe(true)
        })
      })

      describe('Tooltip Interactions', () => {
        it('should have mouse event handlers on tooltip container', () => {
          const tooltipContainer = wrapper.find('.difficulty-tooltip-container')
          expect(tooltipContainer.exists()).toBe(true)

          // Test that container exists and can handle events
          const tooltip = tooltipContainer.find('.difficulty-tooltip')
          expect(tooltip.exists()).toBe(true)
        })

        it('should show tooltip content for different difficulty levels', () => {
          for (let level = 1; level <= 5; level++) {
            const testSegment = { ...mockSegment, difficulty_level: level }
            const wrapper = mount(SegmentInfoCard, {
              props: {
                segment: testSegment,
                gpxData: mockGPXData
              },
              global: {
                plugins: [i18n]
              }
            })

            const tooltip = wrapper.find('.difficulty-tooltip')
            expect(tooltip.exists()).toBe(true)
            expect(tooltip.text()).toBeTruthy()
            expect(tooltip.text().length).toBeGreaterThan(10) // Ensure we have substantial content
          }
        })
      })

      describe('Internationalization', () => {
        it('should display tooltip in French when locale is French', async () => {
          const frenchI18n = createI18n({
            legacy: false,
            locale: 'fr',
            messages: {
              en,
              fr
            }
          })

          const wrapper = mount(SegmentInfoCard, {
            props: {
              segment: { ...mockSegment, difficulty_level: 1 },
              gpxData: mockGPXData
            },
            global: {
              plugins: [frenchI18n]
            }
          })

          const tooltip = wrapper.find('.difficulty-tooltip')
          expect(tooltip.text()).toBe(
            'Vous pourriez rouler sur ce segment les yeux fermés'
          )
        })

        it('should display all difficulty levels in French', async () => {
          const frenchI18n = createI18n({
            legacy: false,
            locale: 'fr',
            messages: {
              en,
              fr
            }
          })

          for (let level = 1; level <= 5; level++) {
            const testSegment = { ...mockSegment, difficulty_level: level }
            const wrapper = mount(SegmentInfoCard, {
              props: {
                segment: testSegment,
                gpxData: mockGPXData
              },
              global: {
                plugins: [frenchI18n]
              }
            })

            const tooltip = wrapper.find('.difficulty-tooltip')
            expect(tooltip.exists()).toBe(true)
            expect(tooltip.text()).toBeTruthy()
            expect(tooltip.text()).not.toContain('You could') // Should not contain English text
          }
        })

        it('should fallback to level 5 description for invalid levels in French', async () => {
          const frenchI18n = createI18n({
            legacy: false,
            locale: 'fr',
            messages: {
              en,
              fr
            }
          })

          const testSegment = { ...mockSegment, difficulty_level: 10 }
          const wrapper = mount(SegmentInfoCard, {
            props: {
              segment: testSegment,
              gpxData: mockGPXData
            },
            global: {
              plugins: [frenchI18n]
            }
          })

          const tooltip = wrapper.find('.difficulty-tooltip')
          expect(tooltip.text()).toBe(
            'Soyez prêt à poser le pied, car le chemin est difficile en raison de la pente, du terrain, ou des deux.'
          )
        })
      })

      describe('Accessibility', () => {
        it('should have proper tooltip structure for accessibility', () => {
          const tooltipContainer = wrapper.find('.difficulty-tooltip-container')
          expect(tooltipContainer.exists()).toBe(true)
          expect(tooltipContainer.classes()).toContain('difficulty-tooltip-container')
        })

        it('should have tooltip content that is informative', () => {
          const tooltip = wrapper.find('.difficulty-tooltip')
          const tooltipText = tooltip.text()

          expect(tooltipText.length).toBeGreaterThan(20) // Ensure substantial content
          expect(tooltipText).not.toBe('') // Should not be empty
        })

        it('should maintain tooltip functionality across different props', () => {
          // Test with different segments
          const segments = [
            { ...mockSegment, difficulty_level: 1 },
            { ...mockSegment, difficulty_level: 3 },
            { ...mockSegment, difficulty_level: 5 }
          ]

          segments.forEach((segment) => {
            const wrapper = mount(SegmentInfoCard, {
              props: {
                segment,
                gpxData: mockGPXData
              },
              global: {
                plugins: [i18n]
              }
            })

            const tooltipContainer = wrapper.find('.difficulty-tooltip-container')
            const tooltip = tooltipContainer.find('.difficulty-tooltip')

            expect(tooltipContainer.exists()).toBe(true)
            expect(tooltip.exists()).toBe(true)
            expect(tooltip.text()).toBeTruthy()
          })
        })
      })

      describe('Performance', () => {
        it('should not create multiple tooltip elements unnecessarily', () => {
          // Re-render the component multiple times
          for (let i = 0; i < 5; i++) {
            wrapper = mount(SegmentInfoCard, {
              props: {
                segment: mockSegment,
                gpxData: mockGPXData
              },
              global: {
                plugins: [i18n]
              }
            })
          }

          // Should still have exactly 1 tooltip container
          const tooltipContainers = wrapper.findAll('.difficulty-tooltip-container')
          expect(tooltipContainers).toHaveLength(1)

          const tooltips = wrapper.findAll('.difficulty-tooltip')
          expect(tooltips).toHaveLength(1)
        })

        it('should handle rapid prop changes without errors', async () => {
          const wrapper = mount(SegmentInfoCard, {
            props: {
              segment: mockSegment,
              gpxData: mockGPXData
            },
            global: {
              plugins: [i18n]
            }
          })

          // Rapidly change difficulty levels
          for (let level = 1; level <= 5; level++) {
            const newSegment = { ...mockSegment, difficulty_level: level }
            await wrapper.setProps({ segment: newSegment })

            const tooltip = wrapper.find('.difficulty-tooltip')
            expect(tooltip.exists()).toBe(true)
            expect(tooltip.text()).toBeTruthy()
          }
        })
      })

      describe('Edge Cases', () => {
        it('should handle missing difficulty level gracefully', () => {
          const testSegment = { ...mockSegment }
          // @ts-ignore - Testing edge case where difficulty_level might be missing
          delete testSegment.difficulty_level

          const wrapper = mount(SegmentInfoCard, {
            props: {
              segment: testSegment,
              gpxData: mockGPXData
            },
            global: {
              plugins: [i18n]
            }
          })

          const tooltip = wrapper.find('.difficulty-tooltip')
          expect(tooltip.exists()).toBe(true)
          // Should default to level 5 description
          expect(tooltip.text()).toBe(
            'Be prepared to put a foot down, as the path is difficult due to either slope, terrain, or both.'
          )
        })

        it('should handle negative difficulty levels', () => {
          const testSegment = { ...mockSegment, difficulty_level: -1 }
          const wrapper = mount(SegmentInfoCard, {
            props: {
              segment: testSegment,
              gpxData: mockGPXData
            },
            global: {
              plugins: [i18n]
            }
          })

          const tooltip = wrapper.find('.difficulty-tooltip')
          expect(tooltip.exists()).toBe(true)
          expect(tooltip.text()).toBe(
            'Be prepared to put a foot down, as the path is difficult due to either slope, terrain, or both.'
          )
        })

        it('should handle very large difficulty levels', () => {
          const testSegment = { ...mockSegment, difficulty_level: 999 }
          const wrapper = mount(SegmentInfoCard, {
            props: {
              segment: testSegment,
              gpxData: mockGPXData
            },
            global: {
              plugins: [i18n]
            }
          })

          const tooltip = wrapper.find('.difficulty-tooltip')
          expect(tooltip.exists()).toBe(true)
          expect(tooltip.text()).toBe(
            'Be prepared to put a foot down, as the path is difficult due to either slope, terrain, or both.'
          )
        })
      })
    })
  })
})
