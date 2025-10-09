import { describe, it, expect, beforeEach } from 'vitest'
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
})
