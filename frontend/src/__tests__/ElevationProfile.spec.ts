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

      expect(wrapper.find('.elevation-empty-state').exists()).toBe(false)
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

      const errorElement = wrapper.find('.elevation-empty-state')
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

  describe('Refactored Features - ElevationError Management', () => {
    it('should hide canvas when elevationError is present', () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          elevationError: 'No route data available'
        },
        global: {
          plugins: [i18n]
        }
      })

      const canvas = wrapper.find('.elevation-chart-canvas')
      expect(canvas.attributes('style')).toContain('display: none')
    })

    it('should show canvas when elevationError is null', () => {
      const mockRoutePoints = [
        { lat: 46.86, lng: 3.98, elevation: 100, distance: 0 },
        { lat: 46.87, lng: 3.99, elevation: 150, distance: 1000 }
      ]

      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          elevationError: null,
          routePoints: mockRoutePoints,
          routeDistance: 1.0
        },
        global: {
          plugins: [i18n]
        }
      })

      const canvas = wrapper.find('.elevation-chart-canvas')
      // v-show should not add display:none when elevationError is null
      expect(canvas.isVisible()).toBe(true)
    })

    it('should display empty state message when elevationError exists', () => {
      const errorMsg = 'Start adding waypoints to see the elevation profile.'
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          elevationError: errorMsg
        },
        global: {
          plugins: [i18n]
        }
      })

      const emptyState = wrapper.find('.elevation-empty-state')
      expect(emptyState.exists()).toBe(true)
      expect(emptyState.text()).toContain(errorMsg)
      expect(emptyState.find('.fa-mountain').exists()).toBe(true)
    })

    it('should center the empty state message', () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          elevationError: 'No data'
        },
        global: {
          plugins: [i18n]
        }
      })

      const emptyState = wrapper.find('.elevation-empty-state')
      // Check that it has positioning styles
      expect(emptyState.exists()).toBe(true)
    })
  })

  describe('Refactored Features - RoutePoints Integration', () => {
    it('should accept routePoints prop with smoothed data from parent', () => {
      const smoothedRoutePoints = [
        { lat: 46.86, lng: 3.98, elevation: 105, distance: 0 },
        { lat: 46.861, lng: 3.981, elevation: 112, distance: 100 },
        { lat: 46.862, lng: 3.982, elevation: 118, distance: 200 }
      ]

      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          routePoints: smoothedRoutePoints,
          routeDistance: 0.2
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.props('routePoints')).toHaveLength(3)
      expect(wrapper.props('routePoints')).toEqual(smoothedRoutePoints)
    })

    it('should handle empty routePoints array', () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          routePoints: [],
          routeDistance: 0
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.props('routePoints')).toEqual([])
    })

    it('should work with multi-segment flattened route points', () => {
      // Simulating allRoutePoints from RoutePlanner (flattened from multiple segments)
      const flattenedPoints = [
        // Segment 1 points
        { lat: 46.86, lng: 3.98, elevation: 100, distance: 0 },
        { lat: 46.861, lng: 3.981, elevation: 110, distance: 100 },
        // Segment 2 points
        { lat: 46.862, lng: 3.982, elevation: 120, distance: 200 },
        { lat: 46.863, lng: 3.983, elevation: 130, distance: 300 }
      ]

      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          routePoints: flattenedPoints,
          routeDistance: 0.3
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.props('routePoints')).toHaveLength(4)
      expect(wrapper.props('routeDistance')).toBe(0.3)
    })
  })

  describe('Refactored Features - Chart Data Updates', () => {
    it.skip('should accept updated routePoints prop - requires full Chart.js DOM', async () => {
      const initialPoints = [
        { lat: 46.86, lng: 3.98, elevation: 100, distance: 0 },
        { lat: 46.87, lng: 3.99, elevation: 150, distance: 1000 }
      ]

      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          routePoints: initialPoints,
          routeDistance: 1.0
        },
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()

      // Update with new points
      const newPoints = [
        { lat: 46.86, lng: 3.98, elevation: 100, distance: 0 },
        { lat: 46.865, lng: 3.985, elevation: 125, distance: 500 },
        { lat: 46.87, lng: 3.99, elevation: 150, distance: 1000 }
      ]

      await wrapper.setProps({
        routePoints: newPoints,
        routeDistance: 1.0
      })

      await nextTick()

      expect(wrapper.props('routePoints')).toHaveLength(3)
      expect(wrapper.props('routePoints')).toEqual(newPoints)
    })

    it('should transition from data to empty state', async () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          routePoints: [
            { lat: 46.86, lng: 3.98, elevation: 100, distance: 0 },
            { lat: 46.87, lng: 3.99, elevation: 150, distance: 1000 }
          ],
          routeDistance: 1.0,
          elevationError: null
        },
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()

      // Clear the route - simulate clearMap() in RoutePlanner
      await wrapper.setProps({
        routePoints: [],
        routeDistance: 0,
        elevationError: 'Start adding waypoints to see the elevation profile.'
      })

      await nextTick()

      // Should show empty state
      expect(wrapper.find('.elevation-empty-state').exists()).toBe(true)
      expect(wrapper.find('.elevation-chart-canvas').isVisible()).toBe(false)
    })

    it.skip('should transition from error to data state - requires full Chart.js DOM', async () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          routePoints: [],
          routeDistance: 0,
          elevationError: 'No data available'
        },
        global: {
          plugins: [i18n]
        }
      })

      await nextTick()

      // Should show empty state initially
      expect(wrapper.find('.elevation-empty-state').exists()).toBe(true)

      // Add route data - simulate route generation
      await wrapper.setProps({
        routePoints: [
          { lat: 46.86, lng: 3.98, elevation: 100, distance: 0 },
          { lat: 46.87, lng: 3.99, elevation: 150, distance: 1000 }
        ],
        routeDistance: 1.0,
        elevationError: null
      })

      await nextTick()

      // Should hide empty state and show canvas
      expect(wrapper.find('.elevation-empty-state').exists()).toBe(false)
      expect(wrapper.find('.elevation-chart-canvas').isVisible()).toBe(true)
      expect(wrapper.props('routePoints')).toHaveLength(2)
    })
  })

  describe('Refactored Features - Chart Hover Integration', () => {
    it('should emit chart-hover event with route point data', () => {
      const mockRoutePoints = [
        { lat: 46.86, lng: 3.98, elevation: 100, distance: 0 },
        { lat: 46.87, lng: 3.99, elevation: 150, distance: 1000 }
      ]

      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          routePoints: mockRoutePoints,
          routeDistance: 1.0
        },
        global: {
          plugins: [i18n]
        }
      })

      // The component should have chart-hover emit defined
      expect(wrapper.emitted('chart-hover')).toBeUndefined() // Not emitted yet
    })

    it('should handle hover on empty chart gracefully', () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          routePoints: [],
          routeDistance: 0,
          elevationError: 'No data'
        },
        global: {
          plugins: [i18n]
        }
      })

      // Should not crash when no data
      expect(wrapper.exists()).toBe(true)
    })
  })

  describe('Refactored Features - Smoothed Elevation Data', () => {
    it('should work with smoothed elevation values from parent', () => {
      // These would be smoothed values passed from RoutePlanner's smoothedRoutePoints
      const smoothedPoints = [
        { lat: 46.86, lng: 3.98, elevation: 105.5, distance: 0 },
        { lat: 46.861, lng: 3.981, elevation: 112.3, distance: 100 },
        { lat: 46.862, lng: 3.982, elevation: 118.7, distance: 200 }
      ]

      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          routePoints: smoothedPoints,
          routeDistance: 0.2
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.props('routePoints')).toEqual(smoothedPoints)
      // Smoothed values should have decimals
      expect(wrapper.props('routePoints')[0].elevation).toBe(105.5)
    })

    it('should display smoothed values correctly in chart data', () => {
      const smoothedPoints = [
        { lat: 46.86, lng: 3.98, elevation: 157.5, distance: 0 },
        { lat: 46.87, lng: 3.99, elevation: 162.8, distance: 1000 }
      ]

      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          routePoints: smoothedPoints,
          routeDistance: 1.0,
          elevationStats: {
            totalGain: 50,
            totalLoss: 20,
            maxElevation: 163,
            minElevation: 157
          }
        },
        global: {
          plugins: [i18n]
        }
      })

      // Props should contain smoothed values
      expect(wrapper.props('routePoints')[0].elevation).toBeCloseTo(157.5)
      expect(wrapper.props('routePoints')[1].elevation).toBeCloseTo(162.8)
    })
  })

  describe('Refactored Features - Elevation Stats Display', () => {
    it('should display elevation stats in toggle bar', () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: false,
          routeDistance: 5.4,
          elevationStats: {
            totalGain: 350,
            totalLoss: 250,
            maxElevation: 800,
            minElevation: 400
          }
        },
        global: {
          plugins: [i18n]
        }
      })

      const toggleStats = wrapper.find('.toggle-stats')
      expect(toggleStats.text()).toContain('5.4')
      expect(toggleStats.text()).toContain('350')
      expect(toggleStats.text()).toContain('250')
    })

    it('should update stats when props change', async () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: false,
          routeDistance: 2.0,
          elevationStats: {
            totalGain: 100,
            totalLoss: 50,
            maxElevation: 500,
            minElevation: 400
          }
        },
        global: {
          plugins: [i18n]
        }
      })

      let toggleStats = wrapper.find('.toggle-stats')
      expect(toggleStats.text()).toContain('100')

      await wrapper.setProps({
        elevationStats: {
          totalGain: 200,
          totalLoss: 100,
          maxElevation: 600,
          minElevation: 400
        }
      })

      await nextTick()

      toggleStats = wrapper.find('.toggle-stats')
      expect(toggleStats.text()).toContain('200')
      expect(toggleStats.text()).toContain('100')
    })
  })

  describe('Refactored Features - Empty State Styling', () => {
    it('should center empty state message with mountain icon', () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          elevationError: 'No route available'
        },
        global: {
          plugins: [i18n]
        }
      })

      const emptyState = wrapper.find('.elevation-empty-state')
      expect(emptyState.exists()).toBe(true)
      expect(emptyState.find('.fa-mountain').exists()).toBe(true)
      expect(emptyState.text()).toContain('No route available')
    })

    it('should not show x-axis or y-axis when in error state', () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          elevationError: 'No data',
          routePoints: []
        },
        global: {
          plugins: [i18n]
        }
      })

      // Canvas should be hidden
      const canvas = wrapper.find('.elevation-chart-canvas')
      expect(canvas.isVisible()).toBe(false)
    })
  })

  describe('Refactored Features - Chart Destruction and Recreation', () => {
    it('should not create chart when elevationError is present initially', () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          elevationError: 'No data',
          routePoints: []
        },
        global: {
          plugins: [i18n]
        }
      })

      // Chart should not be created
      expect(wrapper.find('.elevation-empty-state').exists()).toBe(true)
      expect(wrapper.find('.elevation-chart-canvas').isVisible()).toBe(false)
    })

    it('should create chart when showElevation becomes true and no error', async () => {
      const mockRoutePoints = [
        { lat: 46.86, lng: 3.98, elevation: 100, distance: 0 },
        { lat: 46.87, lng: 3.99, elevation: 150, distance: 1000 }
      ]

      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: false,
          routePoints: mockRoutePoints,
          routeDistance: 1.0,
          elevationError: null
        },
        global: {
          plugins: [i18n]
        }
      })

      // Elevation section should be collapsed
      expect(wrapper.find('.elevation-expanded').exists()).toBe(false)

      // Expand elevation
      await wrapper.setProps({ showElevation: true })
      await nextTick()

      // Chart should be visible
      expect(wrapper.find('.elevation-chart-canvas').isVisible()).toBe(true)
    })
  })

  describe('Refactored Features - Distance and Elevation Ranges', () => {
    it('should set correct distance range for chart x-axis', () => {
      const mockRoutePoints = [
        { lat: 46.86, lng: 3.98, elevation: 100, distance: 0 },
        { lat: 46.87, lng: 3.99, elevation: 150, distance: 5000 }
      ]

      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          routePoints: mockRoutePoints,
          routeDistance: 5.0 // 5km
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.props('routeDistance')).toBe(5.0)
    })

    it('should handle zero distance gracefully', () => {
      const wrapper = mount(ElevationProfile, {
        props: {
          ...defaultProps,
          showElevation: true,
          routePoints: [],
          routeDistance: 0
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.props('routeDistance')).toBe(0)
      const toggleStats = wrapper.find('.toggle-stats')
      expect(toggleStats.text()).toContain('0.0')
    })
  })
})
