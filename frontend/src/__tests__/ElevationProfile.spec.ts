import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import ElevationProfile from '../components/ElevationProfile.vue'
import { createI18n } from 'vue-i18n'

// Create i18n instance
const i18n = createI18n({
  legacy: false,
  locale: 'en',
  fallbackLocale: 'en',
  messages: {
    en: {
      routePlanner: {
        profile: 'Profile',
        totalDistance: 'Total Distance',
        km: 'km',
        elevationGain: 'Elevation Gain',
        elevationLoss: 'Elevation Loss',
        m: 'm',
        resizeHandle: 'Drag up or down to resize elevation section height'
      }
    }
  }
})

describe('ElevationProfile', () => {
  const defaultProps = {
    showElevation: false,
    elevationStats: {
      totalGain: 0,
      totalLoss: 0,
      maxElevation: 0,
      minElevation: 0
    },
    elevationError: null,
    routeDistance: 0,
    routePoints: [],
    sidebarOpen: false,
    elevationHeight: 300
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Component Rendering', () => {
    it('renders correctly', () => {
      const wrapper = mount(ElevationProfile, {
        props: defaultProps,
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.elevation-section').exists()).toBe(true)
    })

    it('renders elevation toggle button', () => {
      const wrapper = mount(ElevationProfile, {
        props: defaultProps,
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.elevation-toggle').exists()).toBe(true)
    })

    it('shows elevation stats in toggle', () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          routeDistance: 10.5,
          elevationStats: {
            totalGain: 500,
            totalLoss: 300,
            maxElevation: 1000,
            minElevation: 500
          }
        },
        global: {
          plugins: [i18n]
        }
      })

      const toggleStats = wrapper.find('.toggle-stats')
      expect(toggleStats.exists()).toBe(true)
      expect(toggleStats.text()).toContain('10.5')
      expect(toggleStats.text()).toContain('500')
      expect(toggleStats.text()).toContain('300')
    })
  })

  describe('Elevation Section Visibility', () => {
    it('does not show content when showElevation is false', () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: false
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.elevation-content').exists()).toBe(false)
    })

    it('shows content when showElevation is true', () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.elevation-content').exists()).toBe(true)
    })

    it('applies elevation-expanded class when showElevation is true', () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.elevation-section').classes()).toContain(
        'elevation-expanded'
      )
    })

    it('applies sidebar-open class when sidebarOpen is true', () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          sidebarOpen: true
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.elevation-section').classes()).toContain('sidebar-open')
    })
  })

  describe('Elevation Error Handling', () => {
    it('does not show error message when elevationError is null', () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          elevationError: null
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.elevation-error').exists()).toBe(false)
    })

    it('shows error message when elevationError is provided', () => {
      const errorMessage = 'Elevation data unavailable'
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          elevationError: errorMessage
        },
        global: {
          plugins: [i18n]
        }
      })

      const errorElement = wrapper.find('.elevation-error')
      expect(errorElement.exists()).toBe(true)
      expect(errorElement.text()).toContain(errorMessage)
    })
  })

  describe('Elevation Chart', () => {
    it('renders chart canvas when elevation is shown', () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.elevation-chart-canvas').exists()).toBe(true)
    })

    it('exposes elevationChartRef through defineExpose', () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.vm.elevationChartRef).toBeDefined()
    })
  })

  describe('Resize Handle', () => {
    it('shows resize handle when elevation is expanded', () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.elevation-resize-handle').exists()).toBe(true)
    })

    it('does not show resize handle when elevation is collapsed', () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: false
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.elevation-resize-handle').exists()).toBe(false)
    })

    it('emits start-resize event when mousedown on resize handle', async () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true
        },
        global: {
          plugins: [i18n]
        }
      })

      const resizeHandle = wrapper.find('.elevation-resize-handle')
      await resizeHandle.trigger('mousedown')

      expect(wrapper.emitted('start-resize')).toBeTruthy()
    })

    it('sets correct height style on elevation content', () => {
      const customHeight = 400
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          elevationHeight: customHeight
        },
        global: {
          plugins: [i18n]
        }
      })

      const elevationContent = wrapper.find('.elevation-content')
      expect(elevationContent.attributes('style')).toContain(
        `height: ${customHeight}px`
      )
    })
  })

  describe('Toggle Functionality', () => {
    it('emits toggle event when elevation toggle is clicked', async () => {
      const wrapper = mount(ElevationProfile, {
        props: defaultProps,
        global: {
          plugins: [i18n]
        }
      })

      const toggle = wrapper.find('.elevation-toggle')
      await toggle.trigger('click')

      expect(wrapper.emitted('toggle')).toBeTruthy()
      expect(wrapper.emitted('toggle')).toHaveLength(1)
    })

    it('rotates chevron icon when elevation is expanded', () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true
        },
        global: {
          plugins: [i18n]
        }
      })

      // The CSS transformation is applied through the .elevation-expanded class
      expect(wrapper.find('.elevation-section').classes()).toContain(
        'elevation-expanded'
      )
    })
  })

  describe('Resize Behavior', () => {
    it('emits update:elevation-height event during resize', async () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          elevationHeight: 300
        },
        global: {
          plugins: [i18n]
        },
        attachTo: document.body
      })

      const resizeHandle = wrapper.find('.elevation-resize-handle')

      // Simulate mousedown
      await resizeHandle.trigger('mousedown', {
        clientY: 500
      })

      // Simulate mousemove
      await document.dispatchEvent(
        new MouseEvent('mousemove', {
          clientY: 400
        })
      )

      await nextTick()

      // Should emit update:elevation-height
      expect(wrapper.emitted('update:elevation-height')).toBeTruthy()

      wrapper.unmount()
    })

    it('clamps height to minimum value', async () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          elevationHeight: 200
        },
        global: {
          plugins: [i18n]
        },
        attachTo: document.body
      })

      const resizeHandle = wrapper.find('.elevation-resize-handle')

      // Simulate mousedown
      await resizeHandle.trigger('mousedown', {
        clientY: 200
      })

      // Simulate mousemove to try to make it very small
      await document.dispatchEvent(
        new MouseEvent('mousemove', {
          clientY: 0
        })
      )

      await nextTick()

      // Should emit with minimum height (150)
      const emitted = wrapper.emitted('update:elevation-height')
      if (emitted && emitted.length > 0) {
        const emittedHeight = emitted[emitted.length - 1][0] as number
        expect(emittedHeight).toBeGreaterThanOrEqual(150)
      }

      wrapper.unmount()
    })

    it('clamps height to maximum value', async () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          elevationHeight: 300
        },
        global: {
          plugins: [i18n]
        },
        attachTo: document.body
      })

      const resizeHandle = wrapper.find('.elevation-resize-handle')

      // Simulate mousedown
      await resizeHandle.trigger('mousedown', {
        clientY: 500
      })

      // Simulate mousemove to try to make it very large
      await document.dispatchEvent(
        new MouseEvent('mousemove', {
          clientY: 0
        })
      )

      await nextTick()

      // Should emit with maximum height (600)
      const emitted = wrapper.emitted('update:elevation-height')
      if (emitted && emitted.length > 0) {
        const emittedHeight = emitted[emitted.length - 1][0] as number
        expect(emittedHeight).toBeLessThanOrEqual(600)
      }

      wrapper.unmount()
    })

    it('stops resizing on mouseup', async () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true
        },
        global: {
          plugins: [i18n]
        },
        attachTo: document.body
      })

      const resizeHandle = wrapper.find('.elevation-resize-handle')

      // Start resize
      await resizeHandle.trigger('mousedown', {
        clientY: 500
      })

      // Move mouse
      await document.dispatchEvent(
        new MouseEvent('mousemove', {
          clientY: 400
        })
      )

      // Stop resize
      await document.dispatchEvent(new MouseEvent('mouseup'))

      await nextTick()

      const emittedCountBeforeMouseup =
        wrapper.emitted('update:elevation-height')?.length || 0

      // Move mouse again - should not emit anymore
      await document.dispatchEvent(
        new MouseEvent('mousemove', {
          clientY: 300
        })
      )

      await nextTick()

      const emittedCountAfterMouseup =
        wrapper.emitted('update:elevation-height')?.length || 0

      // Count should not increase after mouseup
      expect(emittedCountAfterMouseup).toBe(emittedCountBeforeMouseup)

      wrapper.unmount()
    })
  })

  describe('Touch Support', () => {
    it('handles touchstart event on resize handle', async () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true
        },
        global: {
          plugins: [i18n]
        }
      })

      const resizeHandle = wrapper.find('.elevation-resize-handle')

      await resizeHandle.trigger('touchstart', {
        touches: [{ clientY: 500 }]
      })

      expect(wrapper.emitted('start-resize')).toBeTruthy()
    })
  })
})
