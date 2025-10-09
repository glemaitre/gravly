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

      const secondRow = wrapper.findAll('.info-row')[1]
      expect(secondRow.exists()).toBe(true)
      const statItems = secondRow.findAll('.info-item-compact')
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

      const secondRow = wrapper.findAll('.info-row')[1]
      expect(secondRow.exists()).toBe(true)
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

  describe('Editing Functionality', () => {
    describe('Editable Prop', () => {
      it('should show edit icons when editable is true', () => {
        const wrapper = mount(RouteInfoCard, {
          props: {
            stats: mockStats,
            hasSegmentData: true,
            editable: true
          },
          global: {
            plugins: [i18n]
          }
        })

        const editIcons = wrapper.findAll('.edit-icon')
        expect(editIcons.length).toBeGreaterThan(0)
      })

      it('should not show edit icons when editable is false', () => {
        const wrapper = mount(RouteInfoCard, {
          props: {
            stats: mockStats,
            hasSegmentData: true,
            editable: false
          },
          global: {
            plugins: [i18n]
          }
        })

        const editIcons = wrapper.findAll('.edit-icon')
        expect(editIcons).toHaveLength(0)
      })

      it('should add editable class when editable is true', () => {
        const wrapper = mount(RouteInfoCard, {
          props: {
            stats: mockStats,
            hasSegmentData: true,
            editable: true
          },
          global: {
            plugins: [i18n]
          }
        })

        const editableItems = wrapper.findAll('.info-item-compact.editable')
        expect(editableItems.length).toBeGreaterThan(0)
      })
    })

    describe('Difficulty Editor', () => {
      it('should open difficulty editor when clicking on difficulty item', async () => {
        const wrapper = mount(RouteInfoCard, {
          props: {
            stats: mockStats,
            hasSegmentData: true,
            editable: true
          },
          global: {
            plugins: [i18n]
          }
        })

        const difficultyItem = wrapper.findAll('.info-item-compact.editable')[0]
        await difficultyItem.trigger('click')

        expect(wrapper.find('.difficulty-editor').exists()).toBe(true)
      })

      it('should show 5 difficulty buttons', async () => {
        const wrapper = mount(RouteInfoCard, {
          props: {
            stats: mockStats,
            hasSegmentData: true,
            editable: true
          },
          global: {
            plugins: [i18n]
          }
        })

        const difficultyItem = wrapper.findAll('.info-item-compact.editable')[0]
        await difficultyItem.trigger('click')

        const buttons = wrapper.findAll('.difficulty-btn')
        expect(buttons).toHaveLength(5)
      })

      it('should emit update:difficulty event when selecting a difficulty', async () => {
        const wrapper = mount(RouteInfoCard, {
          props: {
            stats: mockStats,
            hasSegmentData: true,
            editable: true
          },
          global: {
            plugins: [i18n]
          }
        })

        const difficultyItem = wrapper.findAll('.info-item-compact.editable')[0]
        await difficultyItem.trigger('click')

        const button = wrapper.findAll('.difficulty-btn')[2] // Select level 3
        await button.trigger('click')

        expect(wrapper.emitted('update:difficulty')).toBeTruthy()
        expect(wrapper.emitted('update:difficulty')![0]).toEqual([3])
      })

      it('should close difficulty editor when clicking close button', async () => {
        const wrapper = mount(RouteInfoCard, {
          props: {
            stats: mockStats,
            hasSegmentData: true,
            editable: true
          },
          global: {
            plugins: [i18n]
          }
        })

        const difficultyItem = wrapper.findAll('.info-item-compact.editable')[0]
        await difficultyItem.trigger('click')

        expect(wrapper.find('.difficulty-editor').exists()).toBe(true)

        const closeButton = wrapper.find('.close-editor-btn')
        await closeButton.trigger('click')

        expect(wrapper.find('.difficulty-editor').exists()).toBe(false)
      })
    })

    describe('Surface Editor', () => {
      it('should open surface editor when clicking on surface item', async () => {
        const wrapper = mount(RouteInfoCard, {
          props: {
            stats: mockStats,
            hasSegmentData: true,
            editable: true
          },
          global: {
            plugins: [i18n]
          }
        })

        const surfaceItem = wrapper.findAll('.info-item-compact.editable')[1]
        await surfaceItem.trigger('click')

        expect(wrapper.find('.surface-editor').exists()).toBe(true)
      })

      it('should show all surface options', async () => {
        const wrapper = mount(RouteInfoCard, {
          props: {
            stats: mockStats,
            hasSegmentData: true,
            editable: true
          },
          global: {
            plugins: [i18n]
          }
        })

        const surfaceItem = wrapper.findAll('.info-item-compact.editable')[1]
        await surfaceItem.trigger('click')

        const surfaceOptions = wrapper.findAll('.surface-option-compact')
        expect(surfaceOptions.length).toBe(6) // 6 surface types
      })

      it('should emit update:surfaceTypes event when toggling a surface', async () => {
        const wrapper = mount(RouteInfoCard, {
          props: {
            stats: mockStats,
            hasSegmentData: true,
            editable: true
          },
          global: {
            plugins: [i18n]
          }
        })

        const surfaceItem = wrapper.findAll('.info-item-compact.editable')[1]
        await surfaceItem.trigger('click')

        const surfaceOption = wrapper.findAll('.surface-option-compact')[0]
        const checkbox = surfaceOption.find('input[type="checkbox"]')
        await checkbox.trigger('change')

        expect(wrapper.emitted('update:surfaceTypes')).toBeTruthy()
      })

      it('should close surface editor when clicking close button', async () => {
        const wrapper = mount(RouteInfoCard, {
          props: {
            stats: mockStats,
            hasSegmentData: true,
            editable: true
          },
          global: {
            plugins: [i18n]
          }
        })

        const surfaceItem = wrapper.findAll('.info-item-compact.editable')[1]
        await surfaceItem.trigger('click')

        expect(wrapper.find('.surface-editor').exists()).toBe(true)

        const closeButton = wrapper.find('.close-editor-btn')
        await closeButton.trigger('click')

        expect(wrapper.find('.surface-editor').exists()).toBe(false)
      })
    })

    describe('Tire Editor', () => {
      it('should open tire editor when clicking on tire item', async () => {
        const wrapper = mount(RouteInfoCard, {
          props: {
            stats: mockStats,
            hasSegmentData: true,
            editable: true
          },
          global: {
            plugins: [i18n]
          }
        })

        const tireItem = wrapper.findAll('.info-item-compact.editable')[2]
        await tireItem.trigger('click')

        expect(wrapper.find('.tire-editor').exists()).toBe(true)
      })

      it('should show tire options for dry and wet conditions', async () => {
        const wrapper = mount(RouteInfoCard, {
          props: {
            stats: mockStats,
            hasSegmentData: true,
            editable: true
          },
          global: {
            plugins: [i18n]
          }
        })

        const tireItem = wrapper.findAll('.info-item-compact.editable')[2]
        await tireItem.trigger('click')

        const tireOptions = wrapper.findAll('.tire-option-compact')
        expect(tireOptions.length).toBe(6) // 3 options x 2 conditions
      })

      it('should emit update:tireDry event when selecting dry tire', async () => {
        const wrapper = mount(RouteInfoCard, {
          props: {
            stats: mockStats,
            hasSegmentData: true,
            editable: true
          },
          global: {
            plugins: [i18n]
          }
        })

        const tireItem = wrapper.findAll('.info-item-compact.editable')[2]
        await tireItem.trigger('click')

        const dryTireOption = wrapper.findAll('.tire-option-compact')[0]
        const radio = dryTireOption.find('input[type="radio"]')
        await radio.trigger('change')

        expect(wrapper.emitted('update:tireDry')).toBeTruthy()
      })

      it('should emit update:tireWet event when selecting wet tire', async () => {
        const wrapper = mount(RouteInfoCard, {
          props: {
            stats: mockStats,
            hasSegmentData: true,
            editable: true
          },
          global: {
            plugins: [i18n]
          }
        })

        const tireItem = wrapper.findAll('.info-item-compact.editable')[2]
        await tireItem.trigger('click')

        const wetTireOption = wrapper.findAll('.tire-option-compact')[3]
        const radio = wetTireOption.find('input[type="radio"]')
        await radio.trigger('change')

        expect(wrapper.emitted('update:tireWet')).toBeTruthy()
      })

      it('should close tire editor when clicking close button', async () => {
        const wrapper = mount(RouteInfoCard, {
          props: {
            stats: mockStats,
            hasSegmentData: true,
            editable: true
          },
          global: {
            plugins: [i18n]
          }
        })

        const tireItem = wrapper.findAll('.info-item-compact.editable')[2]
        await tireItem.trigger('click')

        expect(wrapper.find('.tire-editor').exists()).toBe(true)

        const closeButton = wrapper.find('.close-editor-btn')
        await closeButton.trigger('click')

        expect(wrapper.find('.tire-editor').exists()).toBe(false)
      })
    })

    describe('Editor Mutual Exclusivity', () => {
      it('should close difficulty editor when opening surface editor', async () => {
        const wrapper = mount(RouteInfoCard, {
          props: {
            stats: mockStats,
            hasSegmentData: true,
            editable: true
          },
          global: {
            plugins: [i18n]
          }
        })

        // Open difficulty editor
        const difficultyItem = wrapper.findAll('.info-item-compact.editable')[0]
        await difficultyItem.trigger('click')
        expect(wrapper.find('.difficulty-editor').exists()).toBe(true)

        // Open surface editor
        const surfaceItem = wrapper.findAll('.info-item-compact.editable')[1]
        await surfaceItem.trigger('click')

        expect(wrapper.find('.difficulty-editor').exists()).toBe(false)
        expect(wrapper.find('.surface-editor').exists()).toBe(true)
      })

      it('should close surface editor when opening tire editor', async () => {
        const wrapper = mount(RouteInfoCard, {
          props: {
            stats: mockStats,
            hasSegmentData: true,
            editable: true
          },
          global: {
            plugins: [i18n]
          }
        })

        // Open surface editor
        const surfaceItem = wrapper.findAll('.info-item-compact.editable')[1]
        await surfaceItem.trigger('click')
        expect(wrapper.find('.surface-editor').exists()).toBe(true)

        // Open tire editor
        const tireItem = wrapper.findAll('.info-item-compact.editable')[2]
        await tireItem.trigger('click')

        expect(wrapper.find('.surface-editor').exists()).toBe(false)
        expect(wrapper.find('.tire-editor').exists()).toBe(true)
      })
    })

    describe('Non-editable Mode', () => {
      it('should not open editors when editable is false', async () => {
        const wrapper = mount(RouteInfoCard, {
          props: {
            stats: mockStats,
            hasSegmentData: true,
            editable: false
          },
          global: {
            plugins: [i18n]
          }
        })

        const items = wrapper.findAll('.info-item-compact')
        await items[0].trigger('click')

        expect(wrapper.find('.difficulty-editor').exists()).toBe(false)
        expect(wrapper.find('.surface-editor').exists()).toBe(false)
        expect(wrapper.find('.tire-editor').exists()).toBe(false)
      })

      it('should not open editors when hasSegmentData is false', async () => {
        const wrapper = mount(RouteInfoCard, {
          props: {
            stats: mockStats,
            hasSegmentData: false,
            editable: true
          },
          global: {
            plugins: [i18n]
          }
        })

        const items = wrapper.findAll('.info-item-compact')
        await items[0].trigger('click')

        expect(wrapper.find('.difficulty-editor').exists()).toBe(false)
        expect(wrapper.find('.surface-editor').exists()).toBe(false)
        expect(wrapper.find('.tire-editor').exists()).toBe(false)
      })
    })
  })
})
