import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import RouteInfoCard from '../RouteInfoCard.vue'
import type { SurfaceType } from '../../types'
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

interface RouteStats {
  distance: number
  difficulty: number
  elevationGain: number
  elevationLoss: number
  surfaceTypes: SurfaceType[]
  tireDry: 'slick' | 'semi-slick' | 'knobs'
  tireWet: 'slick' | 'semi-slick' | 'knobs'
}

describe('RouteInfoCard', () => {
  let mockStats: RouteStats

  beforeEach(() => {
    mockStats = {
      distance: 25.5,
      difficulty: 3.5,
      elevationGain: 450,
      elevationLoss: 380,
      surfaceTypes: ['broken-paved-road', 'forest-trail'],
      tireDry: 'semi-slick',
      tireWet: 'knobs'
    }
  })

  describe('Component Rendering', () => {
    it('should render the component with all sections', () => {
      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: mockStats,
          hasSegmentData: true
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.route-info-card').exists()).toBe(true)
      expect(wrapper.find('.info-grid').exists()).toBe(true)
      expect(wrapper.find('.info-row').exists()).toBe(true)
    })

    it('should display difficulty information as integer', () => {
      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: mockStats,
          hasSegmentData: true
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.difficulty-level').text()).toBe('4') // 3.5 rounded to 4
      expect(wrapper.find('.difficulty-word').exists()).toBe(true)
    })

    it('should display surface type information', () => {
      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: mockStats,
          hasSegmentData: true
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.surface-image').exists()).toBe(true)
      expect(wrapper.find('.surface-text').exists()).toBe(true)
    })

    it('should display tire recommendations', () => {
      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: mockStats,
          hasSegmentData: true
        },
        global: {
          plugins: [i18n]
        }
      })

      const tireImages = wrapper.findAll('.tire-image')
      expect(tireImages).toHaveLength(2) // dry and wet
    })

    it('should display statistics', () => {
      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: mockStats,
          hasSegmentData: true
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.stats-grid').exists()).toBe(true)
      const statItems = wrapper.findAll('.stat-item')
      expect(statItems).toHaveLength(3) // distance, elevation gain, elevation loss
    })
  })

  describe('No Segment Data', () => {
    it('should show "No segment data" when hasSegmentData is false', () => {
      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: mockStats,
          hasSegmentData: false
        },
        global: {
          plugins: [i18n]
        }
      })

      const noDataElements = wrapper.findAll('.no-data')
      expect(noDataElements.length).toBeGreaterThan(0)
    })

    it('should still show statistics when hasSegmentData is false', () => {
      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: mockStats,
          hasSegmentData: false
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.stats-grid').exists()).toBe(true)
    })
  })

  describe('Distance Formatting', () => {
    it('should format distance in kilometers when >= 1km', () => {
      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: { ...mockStats, distance: 15.5 },
          hasSegmentData: true
        },
        global: {
          plugins: [i18n]
        }
      })

      const statValues = wrapper.findAll('.stat-value')
      expect(statValues[0].text()).toContain('15.5')
      expect(statValues[0].text()).toContain('km')
    })

    it('should format distance in meters when < 1km', () => {
      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: { ...mockStats, distance: 0.5 },
          hasSegmentData: true
        },
        global: {
          plugins: [i18n]
        }
      })

      const statValues = wrapper.findAll('.stat-value')
      expect(statValues[0].text()).toContain('500')
      expect(statValues[0].text()).toContain('m')
    })
  })

  describe('Surface Type Navigation', () => {
    it('should show navigation buttons when multiple surface types', () => {
      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: mockStats,
          hasSegmentData: true
        },
        global: {
          plugins: [i18n]
        }
      })

      const navButtons = wrapper.findAll('.surface-nav-btn')
      expect(navButtons).toHaveLength(2) // previous and next
    })

    it('should not show navigation buttons when single surface type', () => {
      const singleSurfaceStats = {
        ...mockStats,
        surfaceTypes: ['broken-paved-road' as SurfaceType]
      }

      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: singleSurfaceStats,
          hasSegmentData: true
        },
        global: {
          plugins: [i18n]
        }
      })

      const navButtons = wrapper.findAll('.surface-nav-btn')
      expect(navButtons).toHaveLength(0)
    })

    it('should navigate to next surface type', async () => {
      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: mockStats,
          hasSegmentData: true
        },
        global: {
          plugins: [i18n]
        }
      })

      const indicator = wrapper.find('.surface-indicator')
      expect(indicator.text()).toBe('1/2')

      const nextButton = wrapper.findAll('.surface-nav-btn')[1]
      await nextButton.trigger('click')

      expect(indicator.text()).toBe('2/2')
    })

    it('should navigate to previous surface type', async () => {
      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: mockStats,
          hasSegmentData: true
        },
        global: {
          plugins: [i18n]
        }
      })

      // Navigate to second surface
      const nextButton = wrapper.findAll('.surface-nav-btn')[1]
      await nextButton.trigger('click')

      const indicator = wrapper.find('.surface-indicator')
      expect(indicator.text()).toBe('2/2')

      // Navigate back to first
      const prevButton = wrapper.findAll('.surface-nav-btn')[0]
      await prevButton.trigger('click')

      expect(indicator.text()).toBe('1/2')
    })

    it('should disable previous button at first surface', () => {
      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: mockStats,
          hasSegmentData: true
        },
        global: {
          plugins: [i18n]
        }
      })

      const prevButton = wrapper.findAll('.surface-nav-btn')[0]
      expect(prevButton.attributes('disabled')).toBeDefined()
    })

    it('should disable next button at last surface', async () => {
      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: mockStats,
          hasSegmentData: true
        },
        global: {
          plugins: [i18n]
        }
      })

      // Navigate to last surface
      const nextButton = wrapper.findAll('.surface-nav-btn')[1]
      await nextButton.trigger('click')

      expect(nextButton.attributes('disabled')).toBeDefined()
    })
  })

  describe('Tire Types', () => {
    it('should display slick tires correctly', () => {
      const slickStats = {
        ...mockStats,
        tireDry: 'slick' as const,
        tireWet: 'slick' as const
      }

      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: slickStats,
          hasSegmentData: true
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.html()).toContain('slick')
    })

    it('should display semi-slick tires correctly', () => {
      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: mockStats,
          hasSegmentData: true
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.html()).toContain('semi')
    })

    it('should display knobs tires correctly', () => {
      const knobsStats = {
        ...mockStats,
        tireDry: 'knobs' as const,
        tireWet: 'knobs' as const
      }

      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: knobsStats,
          hasSegmentData: true
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.html()).toContain('knobs')
    })
  })

  describe('Difficulty Levels', () => {
    it('should display difficulty level 1 correctly as integer', () => {
      const easyStats = { ...mockStats, difficulty: 1 }

      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: easyStats,
          hasSegmentData: true
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.difficulty-level').text()).toBe('1')
    })

    it('should display difficulty level 5 correctly as integer', () => {
      const hardStats = { ...mockStats, difficulty: 5 }

      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: hardStats,
          hasSegmentData: true
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.difficulty-level').text()).toBe('5')
    })

    it('should round difficulty level for display and word', () => {
      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: { ...mockStats, difficulty: 3.6 },
          hasSegmentData: true
        },
        global: {
          plugins: [i18n]
        }
      })

      // Should round 3.6 to 4 for display
      expect(wrapper.find('.difficulty-level').text()).toBe('4')
      const difficultyWord = wrapper.find('.difficulty-word')
      expect(difficultyWord.exists()).toBe(true)
    })

    it('should round difficulty level down when below 0.5', () => {
      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: { ...mockStats, difficulty: 2.4 },
          hasSegmentData: true
        },
        global: {
          plugins: [i18n]
        }
      })

      // Should round 2.4 to 2 for display
      expect(wrapper.find('.difficulty-level').text()).toBe('2')
    })
  })

  describe('Elevation Formatting', () => {
    it('should format elevation gain correctly', () => {
      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: { ...mockStats, elevationGain: 1250 },
          hasSegmentData: true
        },
        global: {
          plugins: [i18n]
        }
      })

      const statValues = wrapper.findAll('.stat-value')
      expect(statValues[1].text()).toContain('1250')
      expect(statValues[1].text()).toContain('m')
    })

    it('should format elevation loss correctly', () => {
      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: { ...mockStats, elevationLoss: 980 },
          hasSegmentData: true
        },
        global: {
          plugins: [i18n]
        }
      })

      const statValues = wrapper.findAll('.stat-value')
      expect(statValues[2].text()).toContain('980')
      expect(statValues[2].text()).toContain('m')
    })

    it('should round elevation values', () => {
      const wrapper = mount(RouteInfoCard, {
        props: {
          stats: { ...mockStats, elevationGain: 123.7 },
          hasSegmentData: true
        },
        global: {
          plugins: [i18n]
        }
      })

      const statValues = wrapper.findAll('.stat-value')
      expect(statValues[1].text()).toContain('124') // rounded
    })
  })
})
