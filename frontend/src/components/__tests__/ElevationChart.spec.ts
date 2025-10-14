import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import ElevationChart from '../ElevationChart.vue'
import type { GPXData } from '../../types'
import en from '../../i18n/locales/en'
import fr from '../../i18n/locales/fr'
import { Chart } from 'chart.js'

// Mock Chart.js modules
vi.mock('chart.js', () => {
  const mockChart = {
    destroy: vi.fn(),
    update: vi.fn(),
    render: vi.fn()
  }

  const mockChartConstructor = vi.fn(() => mockChart)
  ;(mockChartConstructor as any).register = vi.fn()

  return {
    Chart: mockChartConstructor,
    LineController: {},
    LineElement: {},
    PointElement: {},
    LinearScale: {},
    Title: {},
    CategoryScale: {},
    Filler: {},
    Tooltip: {}
  }
})

vi.mock('chartjs-plugin-annotation', () => ({
  default: {}
}))

// Mock getComputedStyle
Object.defineProperty(window, 'getComputedStyle', {
  value: () => ({
    getPropertyValue: (prop: string) => {
      if (prop === '--brand-primary') return '#ff6600'
      if (prop === '--brand-primary-rgb') return '255, 102, 0'
      return ''
    }
  })
})

// Create i18n instance for tests
const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en,
    fr
  }
})

describe('ElevationChart', () => {
  let wrapper: VueWrapper<any>
  let mockGPXData: GPXData

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks()

    mockGPXData = {
      file_id: '1',
      track_name: 'Test Segment',
      points: [
        {
          latitude: 45.5,
          longitude: -73.5,
          elevation: 100,
          time: '2023-01-01T10:00:00Z'
        },
        {
          latitude: 45.51,
          longitude: -73.49,
          elevation: 150,
          time: '2023-01-01T10:01:00Z'
        },
        {
          latitude: 45.52,
          longitude: -73.48,
          elevation: 200,
          time: '2023-01-01T10:02:00Z'
        },
        {
          latitude: 45.53,
          longitude: -73.47,
          elevation: 180,
          time: '2023-01-01T10:03:00Z'
        }
      ],
      total_stats: {
        total_points: 4,
        total_distance: 5000,
        total_elevation_gain: 100,
        total_elevation_loss: 20
      },
      bounds: {
        north: 45.53,
        south: 45.5,
        east: -73.47,
        west: -73.5,
        min_elevation: 100,
        max_elevation: 200
      }
    }
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('Component Rendering', () => {
    it('should render the component with card structure', () => {
      wrapper = mount(ElevationChart, {
        props: {
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.chart-card').exists()).toBe(true)
      expect(wrapper.find('.card-header').exists()).toBe(true)
      expect(wrapper.find('.card-content').exists()).toBe(true)
      expect(wrapper.find('.chart-container').exists()).toBe(true)
      expect(wrapper.find('.elevation-chart').exists()).toBe(true)
    })

    it('should display the chart header with icon and title', () => {
      wrapper = mount(ElevationChart, {
        props: {
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const header = wrapper.find('.card-header h3')
      expect(header.exists()).toBe(true)
      expect(header.find('i.fa-chart-line').exists()).toBe(true)
      expect(header.text()).toContain('Elevation')
    })

    it('should have a canvas element for the chart', () => {
      wrapper = mount(ElevationChart, {
        props: {
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const canvas = wrapper.find('canvas.elevation-chart')
      expect(canvas.exists()).toBe(true)
    })
  })

  describe('Chart Initialization', () => {
    it('should initialize Chart.js when component mounts', async () => {
      wrapper = mount(ElevationChart, {
        props: {
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      // Wait for async chart initialization
      await new Promise((resolve) => setTimeout(resolve, 150))

      expect(Chart).toHaveBeenCalled()
    })

    it('should create chart with correct configuration', async () => {
      wrapper = mount(ElevationChart, {
        props: {
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      await new Promise((resolve) => setTimeout(resolve, 150))

      expect(Chart).toHaveBeenCalledWith(
        expect.any(HTMLCanvasElement),
        expect.objectContaining({
          type: 'line',
          data: expect.objectContaining({
            datasets: expect.arrayContaining([
              expect.objectContaining({
                label: 'Elevation',
                borderColor: '#ff6600',
                backgroundColor: 'rgba(255, 102, 0, 0.1)',
                fill: true,
                tension: 0.1,
                pointRadius: 0,
                pointHoverRadius: 6,
                parsing: false
              })
            ])
          }),
          options: expect.objectContaining({
            responsive: true,
            maintainAspectRatio: false,
            animation: false
          })
        })
      )
    })

    it('should not initialize chart when gpxData is empty', async () => {
      const emptyGPXData = {
        ...mockGPXData,
        points: []
      }

      wrapper = mount(ElevationChart, {
        props: {
          gpxData: emptyGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      // Wait for potential async operations
      await new Promise((resolve) => setTimeout(resolve, 150))

      expect(Chart).not.toHaveBeenCalled()
    })

    it('should destroy existing chart before creating new one', async () => {
      wrapper = mount(ElevationChart, {
        props: {
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      await new Promise((resolve) => setTimeout(resolve, 150))

      // Trigger chart re-initialization by updating gpxData
      const newGPXData = {
        ...mockGPXData,
        points: [
          ...mockGPXData.points,
          {
            latitude: 45.54,
            longitude: -73.46,
            elevation: 220,
            time: '2023-01-01T10:04:00Z'
          }
        ]
      }

      await wrapper.setProps({ gpxData: newGPXData })
      await new Promise((resolve) => setTimeout(resolve, 150))

      expect((Chart as any).mock.results[0].value.destroy).toHaveBeenCalled()
    })
  })

  describe('Chart Data Processing', () => {
    it('should calculate cumulative distances correctly', async () => {
      wrapper = mount(ElevationChart, {
        props: {
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      await new Promise((resolve) => setTimeout(resolve, 150))

      const chartCall = (Chart as any).mock.calls[0]
      const chartConfig = chartCall[1]
      const chartData = chartConfig.data.datasets[0].data

      // Should have same number of data points as GPX points
      expect(chartData).toHaveLength(mockGPXData.points.length)

      // First point should be at distance 0
      expect(chartData[0].x).toBe(0)
      // Elevation values are now smoothed, so check they're reasonable
      expect(chartData[0].y).toBeGreaterThan(50)
      expect(chartData[0].y).toBeLessThan(200)

      // Subsequent points should have increasing x values (distance)
      for (let i = 1; i < chartData.length; i++) {
        expect(chartData[i].x).toBeGreaterThan(chartData[i - 1].x)
        // Elevation values are smoothed, so just check they're reasonable
        expect(chartData[i].y).toBeGreaterThan(50)
        expect(chartData[i].y).toBeLessThan(250)
      }
    })

    it('should handle single point data', async () => {
      const singlePointData = {
        ...mockGPXData,
        points: [mockGPXData.points[0]]
      }

      wrapper = mount(ElevationChart, {
        props: {
          gpxData: singlePointData
        },
        global: {
          plugins: [i18n]
        }
      })

      await new Promise((resolve) => setTimeout(resolve, 150))

      const chartCall = (Chart as any).mock.calls[0]
      const chartConfig = chartCall[1]
      const chartData = chartConfig.data.datasets[0].data

      expect(chartData).toHaveLength(1)
      expect(chartData[0]).toEqual({
        x: 0,
        y: singlePointData.points[0].elevation
      })
    })
  })

  describe('Chart Interaction', () => {
    it('should emit chartHover event when chart is hovered', async () => {
      wrapper = mount(ElevationChart, {
        props: {
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      await new Promise((resolve) => setTimeout(resolve, 150))

      const chartCall = (Chart as any).mock.calls[0]
      const chartConfig = chartCall[1]
      const onHoverHandler = chartConfig.options.onHover

      // Simulate hover event
      const mockEvent = {}
      const mockActiveElements = [{ index: 2 }]

      onHoverHandler(mockEvent, mockActiveElements)

      expect(wrapper.emitted('chartHover')).toBeTruthy()
      expect(wrapper.emitted('chartHover')![0]).toEqual([2])
    })

    it('should call onChartHover prop when provided', async () => {
      const onChartHoverSpy = vi.fn()

      wrapper = mount(ElevationChart, {
        props: {
          gpxData: mockGPXData,
          onChartHover: onChartHoverSpy
        },
        global: {
          plugins: [i18n]
        }
      })

      await new Promise((resolve) => setTimeout(resolve, 150))

      const chartCall = (Chart as any).mock.calls[0]
      const chartConfig = chartCall[1]
      const onHoverHandler = chartConfig.options.onHover

      // Simulate hover event
      const mockEvent = {}
      const mockActiveElements = [{ index: 1 }]

      onHoverHandler(mockEvent, mockActiveElements)

      expect(onChartHoverSpy).toHaveBeenCalledWith(1)
    })

    it('should not emit or call hover handler when no active elements', async () => {
      wrapper = mount(ElevationChart, {
        props: {
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      await new Promise((resolve) => setTimeout(resolve, 150))

      const chartCall = (Chart as any).mock.calls[0]
      const chartConfig = chartCall[1]
      const onHoverHandler = chartConfig.options.onHover

      // Simulate hover event with no active elements
      const mockEvent = {}
      const mockActiveElements: any[] = []

      onHoverHandler(mockEvent, mockActiveElements)

      expect(wrapper.emitted('chartHover')).toBeFalsy()
    })
  })

  describe('Chart Configuration', () => {
    it('should configure tooltip with correct format', async () => {
      wrapper = mount(ElevationChart, {
        props: {
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      await new Promise((resolve) => setTimeout(resolve, 150))

      const chartCall = (Chart as any).mock.calls[0]
      const chartConfig = chartCall[1]
      const tooltipCallbacks = chartConfig.options.plugins.tooltip.callbacks

      // Test title callback
      const titleResult = tooltipCallbacks.title([{ parsed: { x: 1.234 } }])
      expect(titleResult).toBe('1.23 km')

      // Test label callback
      const labelResult = tooltipCallbacks.label({ parsed: { y: 123.456 } })
      expect(labelResult).toBe('Elevation: 123 m')
    })

    it('should configure scales with correct properties', async () => {
      wrapper = mount(ElevationChart, {
        props: {
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      await new Promise((resolve) => setTimeout(resolve, 150))

      const chartCall = (Chart as any).mock.calls[0]
      const chartConfig = chartCall[1]
      const scales = chartConfig.options.scales

      // X-axis configuration
      expect(scales.x).toEqual({
        type: 'linear',
        display: true,
        title: {
          display: true,
          text: 'Distance (km)'
        },
        min: 0,
        max: expect.any(Number),
        ticks: {
          callback: expect.any(Function)
        }
      })

      // Y-axis configuration
      expect(scales.y).toEqual({
        display: true,
        title: {
          display: true,
          text: 'Elevation (m)'
        },
        min: expect.any(Number)
      })
    })

    it('should format x-axis ticks correctly', async () => {
      wrapper = mount(ElevationChart, {
        props: {
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      await new Promise((resolve) => setTimeout(resolve, 150))

      const chartCall = (Chart as any).mock.calls[0]
      const chartConfig = chartCall[1]
      const tickCallback = chartConfig.options.scales.x.ticks.callback

      expect(tickCallback(1.234)).toBe('1.2 km')
      expect(tickCallback(0.567)).toBe('0.6 km')
    })
  })

  describe('Reactive Updates', () => {
    it('should reinitialize chart when gpxData changes', async () => {
      wrapper = mount(ElevationChart, {
        props: {
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      await new Promise((resolve) => setTimeout(resolve, 150))

      const initialCallCount = (Chart as any).mock.calls.length

      // Update gpxData
      const newGPXData = {
        ...mockGPXData,
        points: [
          ...mockGPXData.points,
          {
            latitude: 45.54,
            longitude: -73.46,
            elevation: 250,
            time: '2023-01-01T10:04:00Z'
          }
        ]
      }

      await wrapper.setProps({ gpxData: newGPXData })
      await new Promise((resolve) => setTimeout(resolve, 150))

      expect((Chart as any).mock.calls.length).toBeGreaterThan(initialCallCount)
    })

    it('should handle gpxData with different elevation ranges', async () => {
      const highElevationData = {
        ...mockGPXData,
        points: mockGPXData.points.map((point) => ({
          ...point,
          elevation: point.elevation + 1000
        }))
      }

      wrapper = mount(ElevationChart, {
        props: {
          gpxData: highElevationData
        },
        global: {
          plugins: [i18n]
        }
      })

      await new Promise((resolve) => setTimeout(resolve, 150))

      const chartCall = (Chart as any).mock.calls[0]
      const chartConfig = chartCall[1]
      const chartData = chartConfig.data.datasets[0].data

      // Check that elevation values are correctly mapped (smoothed)
      // Original values were 1100 and 1150, smoothing will average nearby values
      expect(chartData[0].y).toBeGreaterThan(1050)
      expect(chartData[0].y).toBeLessThan(1200)
      expect(chartData[1].y).toBeGreaterThan(1050)
      expect(chartData[1].y).toBeLessThan(1200)
    })
  })

  describe('Component Cleanup', () => {
    it('should destroy chart when component is unmounted', async () => {
      wrapper = mount(ElevationChart, {
        props: {
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      await new Promise((resolve) => setTimeout(resolve, 150))

      wrapper.unmount()

      expect((Chart as any).mock.results[0].value.destroy).toHaveBeenCalled()
    })

    it('should handle unmount without initialized chart', () => {
      wrapper = mount(ElevationChart, {
        props: {
          gpxData: { ...mockGPXData, points: [] }
        },
        global: {
          plugins: [i18n]
        }
      })

      // Should not throw error when unmounting
      expect(() => wrapper.unmount()).not.toThrow()
    })
  })

  describe('Internationalization', () => {
    it('should display chart title in English by default', () => {
      wrapper = mount(ElevationChart, {
        props: {
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      const header = wrapper.find('.card-header h3')
      expect(header.text()).toContain('Elevation')
    })

    it('should display chart title in French when locale is changed', () => {
      const frenchI18n = createI18n({
        legacy: false,
        locale: 'fr',
        messages: {
          en,
          fr
        }
      })

      wrapper = mount(ElevationChart, {
        props: {
          gpxData: mockGPXData
        },
        global: {
          plugins: [frenchI18n]
        }
      })

      const header = wrapper.find('.card-header h3')
      expect(header.text()).toContain('Altitude')
    })
  })

  describe('Edge Cases', () => {
    it('should handle missing canvas element gracefully', () => {
      // Mock canvas as null
      const originalQuerySelector = document.querySelector
      document.querySelector = vi.fn(() => null)

      wrapper = mount(ElevationChart, {
        props: {
          gpxData: mockGPXData
        },
        global: {
          plugins: [i18n]
        }
      })

      // Should not throw error
      expect(() => wrapper.vm.$forceUpdate()).not.toThrow()

      // Restore original function
      document.querySelector = originalQuerySelector
    })

    it('should handle gpxData with identical points', async () => {
      const identicalPointsData = {
        ...mockGPXData,
        points: [
          {
            latitude: 45.5,
            longitude: -73.5,
            elevation: 100,
            time: '2023-01-01T10:00:00Z'
          },
          {
            latitude: 45.5,
            longitude: -73.5,
            elevation: 100,
            time: '2023-01-01T10:01:00Z'
          },
          {
            latitude: 45.5,
            longitude: -73.5,
            elevation: 100,
            time: '2023-01-01T10:02:00Z'
          }
        ]
      }

      wrapper = mount(ElevationChart, {
        props: {
          gpxData: identicalPointsData
        },
        global: {
          plugins: [i18n]
        }
      })

      await new Promise((resolve) => setTimeout(resolve, 150))

      expect(Chart).toHaveBeenCalled()
    })

    it('should handle very large elevation values', async () => {
      const largeElevationData = {
        ...mockGPXData,
        points: mockGPXData.points.map((point) => ({
          ...point,
          elevation: point.elevation * 1000
        }))
      }

      wrapper = mount(ElevationChart, {
        props: {
          gpxData: largeElevationData
        },
        global: {
          plugins: [i18n]
        }
      })

      await new Promise((resolve) => setTimeout(resolve, 150))

      const chartCall = (Chart as any).mock.calls[0]
      const chartConfig = chartCall[1]
      const chartData = chartConfig.data.datasets[0].data

      // Elevation values are smoothed, so check they're in reasonable range
      expect(chartData[0].y).toBeGreaterThan(90000)
      expect(chartData[0].y).toBeLessThan(200000)
      expect(chartData[1].y).toBeGreaterThan(90000)
      expect(chartData[1].y).toBeLessThan(200000)
    })
  })
})
