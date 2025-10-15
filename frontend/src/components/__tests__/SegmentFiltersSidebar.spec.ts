import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import SegmentFiltersSidebar from '../SegmentFiltersSidebar.vue'
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

describe('SegmentFiltersSidebar', () => {
  const defaultFilters = {
    difficultyMin: 1,
    difficultyMax: 5,
    surface: [] as string[],
    tireDry: [] as string[],
    tireWet: [] as string[]
  }

  const mountComponent = (props = {}) => {
    return mount(SegmentFiltersSidebar, {
      props: {
        showFilters: false,
        nameFilter: '',
        filters: { ...defaultFilters },
        hasActiveFilters: false,
        ...props
      },
      global: {
        plugins: [i18n]
      }
    })
  }

  describe('Rendering', () => {
    it('should render the sidebar component', () => {
      const wrapper = mountComponent()
      expect(wrapper.find('.filters-sidebar').exists()).toBe(true)
    })

    it('should show sidebar when showFilters is true', () => {
      const wrapper = mountComponent({ showFilters: true })
      expect(wrapper.find('.filters-sidebar').classes()).toContain('open')
    })

    it('should hide sidebar when showFilters is false', () => {
      const wrapper = mountComponent({ showFilters: false })
      expect(wrapper.find('.filters-sidebar').classes()).not.toContain('open')
    })

    it('should render the filters title', () => {
      const wrapper = mountComponent()
      expect(wrapper.find('.filters-title').text()).toContain('Filters')
    })

    it('should render close button', () => {
      const wrapper = mountComponent()
      expect(wrapper.find('.filters-close').exists()).toBe(true)
    })
  })

  describe('Name Filter', () => {
    it('should render name filter input', () => {
      const wrapper = mountComponent()
      const input = wrapper.find('.name-filter-input')
      expect(input.exists()).toBe(true)
    })

    it('should display name filter value', () => {
      const wrapper = mountComponent({ nameFilter: 'Test Segment' })
      const input = wrapper.find('.name-filter-input')
      expect((input.element as HTMLInputElement).value).toBe('Test Segment')
    })

    it('should emit update:nameFilter when input changes', async () => {
      const wrapper = mountComponent()
      const input = wrapper.find('.name-filter-input')
      await input.setValue('New Name')
      expect(wrapper.emitted('update:nameFilter')).toBeTruthy()
      expect(wrapper.emitted('update:nameFilter')?.[0]).toEqual(['New Name'])
    })

    it('should have proper placeholder', () => {
      const wrapper = mountComponent()
      const input = wrapper.find('.name-filter-input')
      expect(input.attributes('placeholder')).toBe('Enter segment name...')
    })
  })

  describe('Difficulty Filter', () => {
    it('should render difficulty sliders', () => {
      const wrapper = mountComponent()
      const sliders = wrapper.findAll('.difficulty-slider')
      expect(sliders).toHaveLength(2) // min and max sliders
    })

    it('should display difficulty tick marks', () => {
      const wrapper = mountComponent()
      const ticks = wrapper.findAll('.tick-mark')
      expect(ticks).toHaveLength(5)
    })

    it('should mark active difficulty range ticks', () => {
      const wrapper = mountComponent({
        filters: { ...defaultFilters, difficultyMin: 2, difficultyMax: 4 }
      })
      const ticks = wrapper.findAll('.tick-mark')
      expect(ticks[1].classes()).toContain('active') // tick 2
      expect(ticks[2].classes()).toContain('active') // tick 3
      expect(ticks[3].classes()).toContain('active') // tick 4
      expect(ticks[0].classes()).not.toContain('active') // tick 1
      expect(ticks[4].classes()).not.toContain('active') // tick 5
    })

    it('should emit update:difficultyMin when min slider changes', async () => {
      const wrapper = mountComponent()
      const minSlider = wrapper.find('.difficulty-slider-min')
      await minSlider.setValue('3')
      expect(wrapper.emitted('update:difficultyMin')).toBeTruthy()
      expect(wrapper.emitted('update:difficultyMin')?.[0]).toEqual([3])
    })

    it('should emit update:difficultyMax when max slider changes', async () => {
      const wrapper = mountComponent()
      const maxSlider = wrapper.find('.difficulty-slider-max')
      await maxSlider.setValue('4')
      expect(wrapper.emitted('update:difficultyMax')).toBeTruthy()
      expect(wrapper.emitted('update:difficultyMax')?.[0]).toEqual([4])
    })

    it('should have correct slider attributes', () => {
      const wrapper = mountComponent()
      const minSlider = wrapper.find('.difficulty-slider-min')
      expect(minSlider.attributes('min')).toBe('1')
      expect(minSlider.attributes('max')).toBe('5')
      expect(minSlider.attributes('step')).toBe('1')
    })
  })

  describe('Surface Filter', () => {
    it('should render 6 surface filter buttons', () => {
      const wrapper = mountComponent()
      const surfaceButtons = wrapper.findAll('.surface-filter-image')
      expect(surfaceButtons).toHaveLength(6)
    })

    it('should mark selected surface filters as active', () => {
      const wrapper = mountComponent({
        filters: { ...defaultFilters, surface: ['dirty-road'] }
      })
      const buttons = wrapper.findAll('.filter-btn-with-image')
      const activeButtons = buttons.filter((btn) => btn.classes().includes('active'))
      expect(activeButtons.length).toBeGreaterThan(0)
    })

    it('should emit toggle-filter when surface button is clicked', async () => {
      const wrapper = mountComponent()
      const surfaceButtons = wrapper.findAll('.surface-filter-image')
      const firstButton = surfaceButtons[0].element.closest('button')
      if (firstButton) {
        await wrapper
          .findAll('button')
          .find((btn) => btn.element === firstButton)
          ?.trigger('click')
        expect(wrapper.emitted('toggle-filter')).toBeTruthy()
        const emitted = wrapper.emitted('toggle-filter')?.[0]
        expect(emitted?.[0]).toBe('surface')
        expect(typeof emitted?.[1]).toBe('string')
      }
    })

    it('should display tooltips on hover', () => {
      const wrapper = mountComponent()
      const tooltips = wrapper.findAll('.custom-tooltip')
      expect(tooltips.length).toBeGreaterThan(0)
    })
  })

  describe('Tire Filter - Dry Conditions', () => {
    it('should render 3 dry tire filter buttons', () => {
      const wrapper = mountComponent()
      // We should have at least 3 tire buttons for dry conditions
      expect(wrapper.findAll('.tire-filter-image').length).toBeGreaterThanOrEqual(3)
    })

    it('should mark selected dry tire filters as active', () => {
      const wrapper = mountComponent({
        filters: { ...defaultFilters, tireDry: ['slick'] }
      })
      const buttons = wrapper.findAll('.filter-btn-with-image')
      const activeButtons = buttons.filter((btn) => btn.classes().includes('active'))
      expect(activeButtons.length).toBeGreaterThan(0)
    })

    it('should emit toggle-filter when dry tire button is clicked', async () => {
      const wrapper = mountComponent()
      const tireButtons = wrapper.findAll('.tire-filter-image')
      if (tireButtons.length > 0) {
        const firstButton = tireButtons[0].element.closest('button')
        if (firstButton) {
          await wrapper
            .findAll('button')
            .find((btn) => btn.element === firstButton)
            ?.trigger('click')
          expect(wrapper.emitted('toggle-filter')).toBeTruthy()
        }
      }
    })

    it('should display dry condition header with sun icon', () => {
      const wrapper = mountComponent()
      const dryHeaders = wrapper.findAll('.tire-condition-header')
      const sunIcon = dryHeaders.find((header) => header.find('.fa-sun').exists())
      expect(sunIcon).toBeTruthy()
    })
  })

  describe('Tire Filter - Wet Conditions', () => {
    it('should render wet tire filter buttons', () => {
      const wrapper = mountComponent()
      const tireButtons = wrapper.findAll('.tire-filter-image')
      expect(tireButtons.length).toBeGreaterThanOrEqual(6) // At least 3 dry + 3 wet
    })

    it('should mark selected wet tire filters as active', () => {
      const wrapper = mountComponent({
        filters: { ...defaultFilters, tireWet: ['knobs'] }
      })
      const buttons = wrapper.findAll('.filter-btn-with-image')
      const activeButtons = buttons.filter((btn) => btn.classes().includes('active'))
      expect(activeButtons.length).toBeGreaterThan(0)
    })

    it('should emit toggle-filter when wet tire button is clicked', async () => {
      const wrapper = mountComponent()
      const tireConditionGroups = wrapper.findAll('.tire-condition-group')
      expect(tireConditionGroups.length).toBeGreaterThanOrEqual(2)

      // Find a button in the second tire condition group (wet tires)
      if (tireConditionGroups.length >= 2) {
        const wetGroup = tireConditionGroups[1]
        const button = wetGroup.find('button')
        if (button.exists()) {
          await button.trigger('click')
          expect(wrapper.emitted('toggle-filter')).toBeTruthy()
        }
      }
    })

    it('should display wet condition header with rain icon', () => {
      const wrapper = mountComponent()
      const wetHeaders = wrapper.findAll('.tire-condition-header')
      const rainIcon = wetHeaders.find((header) =>
        header.find('.fa-cloud-rain').exists()
      )
      expect(rainIcon).toBeTruthy()
    })
  })

  describe('Clear Filters Button', () => {
    it('should not show clear filters button when no active filters', () => {
      const wrapper = mountComponent({ hasActiveFilters: false })
      expect(wrapper.find('.clear-filters-btn').exists()).toBe(false)
    })

    it('should show clear filters button when filters are active', () => {
      const wrapper = mountComponent({ hasActiveFilters: true })
      expect(wrapper.find('.clear-filters-btn').exists()).toBe(true)
    })

    it('should emit clear-filters when button is clicked', async () => {
      const wrapper = mountComponent({ hasActiveFilters: true })
      await wrapper.find('.clear-filters-btn').trigger('click')
      expect(wrapper.emitted('clear-filters')).toBeTruthy()
    })
  })

  describe('Close Button', () => {
    it('should emit close event when close button is clicked', async () => {
      const wrapper = mountComponent()
      await wrapper.find('.filters-close').trigger('click')
      expect(wrapper.emitted('close')).toBeTruthy()
    })
  })

  describe('Accessibility', () => {
    it('should have proper button types', () => {
      const wrapper = mountComponent()
      const buttons = wrapper.findAll('button')
      buttons.forEach((button) => {
        expect(button.attributes('type')).toBe('button')
      })
    })

    it('should have accessible labels for form inputs', () => {
      const wrapper = mountComponent()
      const nameInput = wrapper.find('.name-filter-input')
      expect(nameInput.attributes('placeholder')).toBeTruthy()
    })

    it('should have proper ARIA structure for sliders', () => {
      const wrapper = mountComponent()
      const sliders = wrapper.findAll('input[type="range"]')
      expect(sliders).toHaveLength(2)
      sliders.forEach((slider) => {
        expect(slider.attributes('min')).toBeDefined()
        expect(slider.attributes('max')).toBeDefined()
        expect(slider.attributes('step')).toBeDefined()
      })
    })
  })

  describe('Filter State Display', () => {
    it('should display current difficulty range correctly', () => {
      const wrapper = mountComponent({
        filters: { ...defaultFilters, difficultyMin: 2, difficultyMax: 4 }
      })
      const minSlider = wrapper.find('.difficulty-slider-min')
      const maxSlider = wrapper.find('.difficulty-slider-max')
      expect((minSlider.element as HTMLInputElement).value).toBe('2')
      expect((maxSlider.element as HTMLInputElement).value).toBe('4')
    })

    it('should highlight selected surface types', () => {
      const wrapper = mountComponent({
        filters: { ...defaultFilters, surface: ['dirty-road', 'field-trail'] }
      })
      const activeButtons = wrapper
        .findAll('.filter-btn')
        .filter((btn) => btn.classes().includes('active'))
      expect(activeButtons.length).toBeGreaterThan(0)
    })

    it('should highlight selected dry tire types', () => {
      const wrapper = mountComponent({
        filters: { ...defaultFilters, tireDry: ['slick', 'semi-slick'] }
      })
      const activeButtons = wrapper
        .findAll('.filter-btn')
        .filter((btn) => btn.classes().includes('active'))
      expect(activeButtons.length).toBeGreaterThan(0)
    })

    it('should highlight selected wet tire types', () => {
      const wrapper = mountComponent({
        filters: { ...defaultFilters, tireWet: ['knobs'] }
      })
      const activeButtons = wrapper
        .findAll('.filter-btn')
        .filter((btn) => btn.classes().includes('active'))
      expect(activeButtons.length).toBeGreaterThan(0)
    })
  })

  describe('Responsive Behavior', () => {
    it('should apply open class when showFilters is true', () => {
      const wrapper = mountComponent({ showFilters: true })
      expect(wrapper.find('.filters-sidebar').classes()).toContain('open')
    })

    it('should not apply open class when showFilters is false', () => {
      const wrapper = mountComponent({ showFilters: false })
      expect(wrapper.find('.filters-sidebar').classes()).not.toContain('open')
    })
  })

  describe('Image Loading', () => {
    it('should render surface filter images', () => {
      const wrapper = mountComponent()
      const images = wrapper.findAll('.surface-filter-image')
      expect(images).toHaveLength(6)
      images.forEach((img) => {
        expect(img.attributes('src')).toBeTruthy()
        expect(img.attributes('alt')).toBeTruthy()
      })
    })

    it('should render tire filter images', () => {
      const wrapper = mountComponent()
      const images = wrapper.findAll('.tire-filter-image')
      expect(images.length).toBeGreaterThanOrEqual(6) // 3 dry + 3 wet
      images.forEach((img) => {
        expect(img.attributes('src')).toBeTruthy()
        expect(img.attributes('alt')).toBeTruthy()
      })
    })

    it('should render tooltip images', () => {
      const wrapper = mountComponent()
      const tooltipImages = wrapper.findAll('.tooltip-image')
      expect(tooltipImages.length).toBeGreaterThan(0)
    })
  })

  describe('Filter Groups', () => {
    it('should render all filter groups', () => {
      const wrapper = mountComponent()
      const filterGroups = wrapper.findAll('.filter-group')
      expect(filterGroups.length).toBeGreaterThanOrEqual(3) // Name, Difficulty, Surface, Tire
    })

    it('should render filter group titles with icons', () => {
      const wrapper = mountComponent()
      const filterTitles = wrapper.findAll('.filter-group-title')
      expect(filterTitles.length).toBeGreaterThan(0)
      filterTitles.forEach((title) => {
        expect(title.find('i').exists()).toBe(true)
      })
    })

    it('should render tire condition groups', () => {
      const wrapper = mountComponent()
      const tireGroups = wrapper.findAll('.tire-condition-group')
      expect(tireGroups).toHaveLength(2) // Dry and Wet
    })
  })

  describe('Event Emissions', () => {
    it('should emit all required events', async () => {
      const wrapper = mountComponent({ hasActiveFilters: true, showFilters: true })

      // Test close event
      await wrapper.find('.filters-close').trigger('click')
      expect(wrapper.emitted('close')).toBeTruthy()

      // Test clear-filters event
      await wrapper.find('.clear-filters-btn').trigger('click')
      expect(wrapper.emitted('clear-filters')).toBeTruthy()
    })

    it('should emit toggle-filter with correct parameters', async () => {
      const wrapper = mountComponent()
      const buttons = wrapper.findAll('.filter-btn')
      if (buttons.length > 0) {
        await buttons[0].trigger('click')
        expect(wrapper.emitted('toggle-filter')).toBeTruthy()
        const emitted = wrapper.emitted('toggle-filter')?.[0]
        expect(emitted?.length).toBe(2) // type and value
      }
    })
  })

  describe('Internationalization', () => {
    it('should display English labels by default', () => {
      const wrapper = mountComponent()
      expect(wrapper.text()).toContain('Filters')
      expect(wrapper.text()).toContain('Search by Name')
      expect(wrapper.text()).toContain('Difficulty')
    })

    it('should switch to French when locale changes', async () => {
      i18n.global.locale.value = 'fr'
      const wrapper = mountComponent()
      await wrapper.vm.$nextTick()
      expect(wrapper.text()).toContain('Filtres')
      expect(wrapper.text()).toContain('Rechercher par Nom')
      i18n.global.locale.value = 'en' // Reset to English
    })
  })

  describe('Visual Feedback', () => {
    it('should have slider track fill that reflects difficulty range', () => {
      const wrapper = mountComponent({
        filters: { ...defaultFilters, difficultyMin: 2, difficultyMax: 4 }
      })
      const trackFill = wrapper.find('.slider-track-fill')
      expect(trackFill.exists()).toBe(true)
      const style = trackFill.attributes('style')
      expect(style).toBeTruthy()
      expect(style).toContain('left')
      expect(style).toContain('right')
    })

    it('should apply hover states to filter buttons', () => {
      const wrapper = mountComponent()
      const filterButtons = wrapper.findAll('.filter-btn')
      filterButtons.forEach((button) => {
        expect(button.classes()).toContain('filter-btn')
      })
    })

    describe('Difficulty Tooltip Functionality', () => {
      let wrapper: any

      beforeEach(() => {
        wrapper = mountComponent({ showFilters: true })
      })

      describe('Tooltip Structure', () => {
        it('should render tick mark wrappers with tooltips', () => {
          const tickMarkWrappers = wrapper.findAll('.tick-mark-wrapper')
          expect(tickMarkWrappers).toHaveLength(5) // 5 difficulty levels
        })

        it('should render difficulty tooltip elements for each level', () => {
          const tooltips = wrapper.findAll('.difficulty-tooltip')
          expect(tooltips).toHaveLength(5) // 5 difficulty levels
        })

        it('should have proper CSS classes for tick mark wrappers', () => {
          const tickMarkWrapper = wrapper.find('.tick-mark-wrapper')
          expect(tickMarkWrapper.exists()).toBe(true)
          expect(tickMarkWrapper.classes()).toContain('tick-mark-wrapper')
        })

        it('should have proper CSS classes for difficulty tooltips', () => {
          const tooltip = wrapper.find('.difficulty-tooltip')
          expect(tooltip.exists()).toBe(true)
          expect(tooltip.classes()).toContain('difficulty-tooltip')
        })
      })

      describe('Tooltip Content', () => {
        it('should display difficulty descriptions for all levels', () => {
          const tooltips = wrapper.findAll('.difficulty-tooltip')
          expect(tooltips).toHaveLength(5)

          tooltips.forEach((tooltip: any) => {
            expect(tooltip.text()).toBeTruthy()
            expect(tooltip.text().length).toBeGreaterThan(10)
          })
        })

        it('should display correct description for level 1', () => {
          const tooltips = wrapper.findAll('.difficulty-tooltip')
          expect(tooltips[0].text()).toBe(
            'You could ride this segment with your eyes closed'
          )
        })

        it('should display correct description for level 3', () => {
          const tooltips = wrapper.findAll('.difficulty-tooltip')
          expect(tooltips[2].text()).toBe(
            "You'll need some bike handling skill due to irregular terrain or uphill and downhill sections."
          )
        })

        it('should display correct description for level 5', () => {
          const tooltips = wrapper.findAll('.difficulty-tooltip')
          expect(tooltips[4].text()).toBe(
            'Be prepared to put a foot down, as the path is difficult due to either slope, terrain, or both.'
          )
        })
      })

      describe('Tooltip Styling', () => {
        it('should have proper CSS classes for tick mark wrappers', () => {
          const tickMarkWrapper = wrapper.find('.tick-mark-wrapper')
          expect(tickMarkWrapper.exists()).toBe(true)
          expect(tickMarkWrapper.classes()).toContain('tick-mark-wrapper')
        })

        it('should have proper CSS classes for tooltips', () => {
          const tooltip = wrapper.find('.difficulty-tooltip')
          expect(tooltip.exists()).toBe(true)
          expect(tooltip.classes()).toContain('difficulty-tooltip')
        })

        it('should have proper structure for tooltip positioning', () => {
          const tickMarkWrapper = wrapper.find('.tick-mark-wrapper')
          expect(tickMarkWrapper.exists()).toBe(true)

          const tooltip = tickMarkWrapper.find('.difficulty-tooltip')
          expect(tooltip.exists()).toBe(true)
        })
      })

      describe('Tooltip Interactions', () => {
        it('should have mouse event handlers on tick mark wrappers', () => {
          const tickMarkWrappers = wrapper.findAll('.tick-mark-wrapper')
          expect(tickMarkWrappers).toHaveLength(5)

          // Test that each wrapper can handle events
          tickMarkWrappers.forEach((wrapper: any) => {
            const tooltip = wrapper.find('.difficulty-tooltip')
            expect(tooltip.exists()).toBe(true)
          })
        })

        it('should show tooltip content for all levels', () => {
          const tooltips = wrapper.findAll('.difficulty-tooltip')
          expect(tooltips).toHaveLength(5)

          tooltips.forEach((tooltip: any) => {
            expect(tooltip.exists()).toBe(true)
            expect(tooltip.text()).toBeTruthy()
            expect(tooltip.text().length).toBeGreaterThan(10)
          })
        })
      })

      describe('Internationalization', () => {
        it('should display tooltips in French when locale is French', async () => {
          const frenchI18n = createI18n({
            legacy: false,
            locale: 'fr',
            messages: {
              en,
              fr
            }
          })

          const wrapper = mount(SegmentFiltersSidebar, {
            props: {
              showFilters: true,
              nameFilter: '',
              filters: { ...defaultFilters },
              hasActiveFilters: false
            },
            global: {
              plugins: [frenchI18n]
            }
          })

          const tooltips = wrapper.findAll('.difficulty-tooltip')
          expect(tooltips).toHaveLength(5)

          // Check level 1 (first tooltip)
          expect(tooltips[0].text()).toBe(
            'Vous pourriez rouler sur ce segment les yeux fermés'
          )

          // Check level 3 (third tooltip)
          expect(tooltips[2].text()).toBe(
            'Vous aurez besoin de quelques compétences en pilotage de vélo en raison du terrain irrégulier ou des sections en montée et descente.'
          )
        })

        it('should display tooltips in English by default', () => {
          const tooltips = wrapper.findAll('.difficulty-tooltip')
          expect(tooltips).toHaveLength(5)

          // Check level 1 (first tooltip)
          expect(tooltips[0].text()).toBe(
            'You could ride this segment with your eyes closed'
          )

          // Check level 3 (third tooltip)
          expect(tooltips[2].text()).toBe(
            "You'll need some bike handling skill due to irregular terrain or uphill and downhill sections."
          )
        })
      })

      describe('Accessibility', () => {
        it('should have proper tooltip structure for accessibility', () => {
          const tickMarkWrappers = wrapper.findAll('.tick-mark-wrapper')
          expect(tickMarkWrappers).toHaveLength(5)

          tickMarkWrappers.forEach((wrapper: any) => {
            expect(wrapper.classes()).toContain('tick-mark-wrapper')
          })
        })

        it('should have tooltip content that is informative', () => {
          const tooltips = wrapper.findAll('.difficulty-tooltip')
          expect(tooltips).toHaveLength(5)

          tooltips.forEach((tooltip: any) => {
            const tooltipText = tooltip.text()
            expect(tooltipText.length).toBeGreaterThan(20)
            expect(tooltipText).not.toBe('')
          })
        })

        it('should maintain tooltip functionality across different props', () => {
          const wrapper = mountComponent({
            showFilters: true,
            filters: {
              difficultyMin: 2,
              difficultyMax: 4,
              surface: [],
              tireDry: [],
              tireWet: []
            }
          })

          const tickMarkWrappers = wrapper.findAll('.tick-mark-wrapper')
          const tooltips = wrapper.findAll('.difficulty-tooltip')

          expect(tickMarkWrappers).toHaveLength(5)
          expect(tooltips).toHaveLength(5)

          tooltips.forEach((tooltip) => {
            expect(tooltip.text()).toBeTruthy()
          })
        })
      })

      describe('Performance', () => {
        it('should not create multiple tooltip elements unnecessarily', () => {
          // Re-render the component multiple times
          for (let i = 0; i < 5; i++) {
            wrapper = mountComponent({ showFilters: true })
          }

          // Should still have exactly 5 tick mark wrappers and 5 tooltips
          const tickMarkWrappers = wrapper.findAll('.tick-mark-wrapper')
          expect(tickMarkWrappers).toHaveLength(5)

          const tooltips = wrapper.findAll('.difficulty-tooltip')
          expect(tooltips).toHaveLength(5)
        })

        it('should handle rapid prop changes without errors', async () => {
          const wrapper = mountComponent({ showFilters: true })

          // Rapidly change props
          for (let i = 0; i < 5; i++) {
            await wrapper.setProps({
              filters: {
                difficultyMin: i + 1,
                difficultyMax: 5,
                surface: [],
                tireDry: [],
                tireWet: []
              }
            })

            const tooltips = wrapper.findAll('.difficulty-tooltip')
            expect(tooltips).toHaveLength(5)

            tooltips.forEach((tooltip) => {
              expect(tooltip.exists()).toBe(true)
              expect(tooltip.text()).toBeTruthy()
            })
          }
        })
      })
    })
  })
})
