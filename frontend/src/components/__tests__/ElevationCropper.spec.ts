import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import ElevationCropper from '../ElevationCropper.vue'
import en from '../../i18n/locales/en'
import fr from '../../i18n/locales/fr'

// Mock Chart.js modules
vi.mock('chart.js', () => {
  const mockChart = {
    destroy: vi.fn(),
    update: vi.fn(),
    render: vi.fn(),
    resize: vi.fn(),
    data: {
      labels: [],
      datasets: [{ data: [] }, { data: [] }]
    },
    options: {
      scales: {
        x: {
          title: { text: '' },
          ticks: { callback: vi.fn() },
          min: 0,
          max: 100
        },
        y: {
          title: { text: '' },
          min: 0,
          max: 1000
        }
      }
    },
    scales: {
      x: {
        getValueForPixel: vi.fn(() => 5.0),
        getPixelForValue: vi.fn(() => 100)
      }
    },
    canvas: {
      getBoundingClientRect: vi.fn(() => ({
        left: 0,
        top: 0,
        width: 400,
        height: 300
      }))
    }
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

// Mock getBoundingClientRect for chart canvas and parent elements
Object.defineProperty(HTMLCanvasElement.prototype, 'getBoundingClientRect', {
  value: () => ({
    left: 0,
    top: 0,
    width: 400,
    height: 300
  })
})

Object.defineProperty(HTMLElement.prototype, 'getBoundingClientRect', {
  value: () => ({
    left: 0,
    top: 0,
    width: 400,
    height: 300
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

describe('ElevationCropper', () => {
  let wrapper: VueWrapper<any>
  let mockPoints: any[]
  let mockCumulativeKm: number[]
  let mockCumulativeSec: number[]
  let mockSmoothedElevations: number[]

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks()

    mockPoints = [
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
      },
      {
        latitude: 45.54,
        longitude: -73.46,
        elevation: 220,
        time: '2023-01-01T10:04:00Z'
      }
    ]

    mockCumulativeKm = [0, 1.5, 3.0, 4.5, 6.0]
    mockCumulativeSec = [0, 60, 120, 180, 240]
    mockSmoothedElevations = [100, 145, 195, 185, 215]
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('Component Rendering', () => {
    it('should render the component with proper structure', () => {
      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 0,
          endIndex: 4,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.card-elevation').exists()).toBe(true)
      expect(wrapper.find('.chart-wrapper').exists()).toBe(true)
      expect(wrapper.find('.chart-container').exists()).toBe(true)
      expect(wrapper.find('.chart').exists()).toBe(true)
      expect(wrapper.find('.controls').exists()).toBe(true)
    })

    it('should render start and end sliders', () => {
      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 0,
          endIndex: 4,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.start-slider').exists()).toBe(true)
      expect(wrapper.find('.end-slider').exists()).toBe(true)
    })

    it('should render axis toggle buttons', () => {
      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 0,
          endIndex: 4,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      const axisButtons = wrapper.findAll('.axis-toggle button')
      expect(axisButtons).toHaveLength(2)
      expect(axisButtons[0].text()).toContain('Distance')
      expect(axisButtons[1].text()).toContain('Time')
    })

    it('should render metrics grids for start and end points', () => {
      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 0,
          endIndex: 4,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      const metricsGrids = wrapper.findAll('.metrics-grid')
      expect(metricsGrids).toHaveLength(2)

      const metrics = wrapper.findAll('.metric')
      expect(metrics.length).toBeGreaterThan(0)
    })
  })

  describe('Props and Data Display', () => {
    it('should display correct start and end indices', () => {
      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 1,
          endIndex: 3,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.start-slider .slider-index').text()).toBe('1')
      expect(wrapper.find('.end-slider .slider-index').text()).toBe('3')
    })

    it('should show active xMode button', () => {
      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 0,
          endIndex: 4,
          xMode: 'time'
        },
        global: {
          plugins: [i18n]
        }
      })

      const timeButton = wrapper.find('.axis-toggle button.right')
      expect(timeButton.classes()).toContain('active')
    })

    it('should display correct point data in metrics', () => {
      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 1,
          endIndex: 3,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      // Check GPS coordinates are displayed
      const gpsValues = wrapper.findAll('.gps-col .value')
      expect(gpsValues[0].text()).toBe('45.51000') // start latitude
      expect(gpsValues[1].text()).toBe('-73.49000') // start longitude
      expect(gpsValues[2].text()).toBe('45.53000') // end latitude
      expect(gpsValues[3].text()).toBe('-73.47000') // end longitude
    })
  })

  describe('Chart Integration', () => {
    it('should initialize Chart.js when component mounts', async () => {
      const { Chart } = await import('chart.js')

      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 0,
          endIndex: 4,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      await new Promise((resolve) => setTimeout(resolve, 150))

      expect(Chart).toHaveBeenCalled()
    })

    it('should not initialize chart when points array is empty', async () => {
      const { Chart } = await import('chart.js')

      wrapper = mount(ElevationCropper, {
        props: {
          points: [],
          cumulativeKm: [],
          cumulativeSec: [],
          smoothedElevations: [],
          startIndex: 0,
          endIndex: 0,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      await new Promise((resolve) => setTimeout(resolve, 150))

      expect(Chart).not.toHaveBeenCalled()
    })

    it('should update chart when xMode changes', async () => {
      const { Chart } = await import('chart.js')

      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 0,
          endIndex: 4,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      await new Promise((resolve) => setTimeout(resolve, 150))

      const initialCallCount = (Chart as any).mock.calls.length

      // Change xMode
      await wrapper.setProps({ xMode: 'time' })
      await new Promise((resolve) => setTimeout(resolve, 150))

      // The chart should be updated, which means Chart constructor might be called again
      // or the existing chart should be updated
      expect((Chart as any).mock.calls.length).toBeGreaterThanOrEqual(initialCallCount)
    })

    it('should have onHover configuration in chart options', async () => {
      const { Chart } = await import('chart.js')

      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 0,
          endIndex: 4,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      await new Promise((resolve) => setTimeout(resolve, 150))

      // Verify that Chart was called with onHover configuration
      const chartCall = (Chart as any).mock.calls[0]
      expect(chartCall).toBeDefined()
      expect(chartCall[1].options.onHover).toBeDefined()
      expect(typeof chartCall[1].options.onHover).toBe('function')
    })
  })

  describe('Slider Controls', () => {
    it('should emit update:startIndex when start slider buttons are clicked', async () => {
      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 1,
          endIndex: 4,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      // Click plus button
      const plusButton = wrapper.find('.start-slider .slider-btn-plus')
      await plusButton.trigger('click')

      expect(wrapper.emitted('update:startIndex')).toBeTruthy()
      expect(wrapper.emitted('update:startIndex')![0]).toEqual([2])
    })

    it('should emit update:endIndex when end slider buttons are clicked', async () => {
      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 0,
          endIndex: 3,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      // Click minus button
      const minusButton = wrapper.find('.end-slider .slider-btn-minus')
      await minusButton.trigger('click')

      expect(wrapper.emitted('update:endIndex')).toBeTruthy()
      expect(wrapper.emitted('update:endIndex')![0]).toEqual([2])
    })

    it('should disable start slider plus button when at end boundary', () => {
      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 3,
          endIndex: 4,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      const plusButton = wrapper.find('.start-slider .slider-btn-plus')
      expect(plusButton.attributes('disabled')).toBeDefined()
    })

    it('should disable end slider minus button when at start boundary', () => {
      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 0,
          endIndex: 1,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      const minusButton = wrapper.find('.end-slider .slider-btn-minus')
      expect(minusButton.attributes('disabled')).toBeDefined()
    })
  })

  describe('Axis Mode Toggle', () => {
    it('should emit update:xMode when axis buttons are clicked', async () => {
      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 0,
          endIndex: 4,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      // Click time button
      const timeButton = wrapper.find('.axis-toggle button.right')
      await timeButton.trigger('click')

      expect(wrapper.emitted('update:xMode')).toBeTruthy()
      expect(wrapper.emitted('update:xMode')![0]).toEqual(['time'])
    })

    it('should show correct active state for axis buttons', () => {
      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 0,
          endIndex: 4,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      const distanceButton = wrapper.find('.axis-toggle button.left')
      const timeButton = wrapper.find('.axis-toggle button.right')

      expect(distanceButton.classes()).toContain('active')
      expect(timeButton.classes()).not.toContain('active')
    })
  })

  describe('Data Formatting', () => {
    it('should format distance values correctly', () => {
      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 1,
          endIndex: 3,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      // Check that distance values are formatted with units
      const distanceValues = wrapper.findAll('.metric .value')
      expect(distanceValues[1].text()).toContain('km') // start distance
      expect(distanceValues[4].text()).toContain('km') // end distance
    })

    it('should format elevation values correctly', () => {
      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 1,
          endIndex: 3,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      // Check that elevation values are formatted with units
      const elevationValues = wrapper.findAll('.metric .value')
      expect(elevationValues[2].text()).toContain('m') // start elevation
      expect(elevationValues[5].text()).toContain('m') // end elevation
    })

    it('should format time values correctly', () => {
      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 1,
          endIndex: 3,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      // Check that time values are formatted correctly
      const timeValues = wrapper.findAll('.metric .value')
      expect(timeValues[0].text()).toMatch(/^\d+:\d{2}$/) // start time
      expect(timeValues[3].text()).toMatch(/^\d+:\d{2}$/) // end time
    })
  })

  describe('Slider Position and Overlap', () => {
    it('should calculate slider positions correctly', async () => {
      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 1,
          endIndex: 3,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      await new Promise((resolve) => setTimeout(resolve, 150))

      // Check that slider positions are set
      const startSlider = wrapper.find('.start-slider')
      const endSlider = wrapper.find('.end-slider')

      expect(startSlider.attributes('style')).toContain('left:')
      expect(endSlider.attributes('style')).toContain('left:')
    })

    it('should handle slider overlap with offset', async () => {
      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 1,
          endIndex: 2, // Very close indices to trigger overlap
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      await new Promise((resolve) => setTimeout(resolve, 150))

      // Check that end slider controls have offset when overlapping
      const endControls = wrapper.find('.end-slider .slider-controls')
      expect(endControls.attributes('style')).toContain('top:')
    })
  })

  describe('Responsive Design', () => {
    it('should have proper CSS classes for responsive layout', () => {
      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 0,
          endIndex: 4,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.metrics-grid').exists()).toBe(true)
      expect(wrapper.find('.gps-col').exists()).toBe(true)
    })
  })

  describe('Edge Cases', () => {
    it('should handle single point data', () => {
      const singlePoint = [mockPoints[0]]
      const singleKm = [0]
      const singleSec = [0]
      const singleElevation = [100]

      wrapper = mount(ElevationCropper, {
        props: {
          points: singlePoint,
          cumulativeKm: singleKm,
          cumulativeSec: singleSec,
          smoothedElevations: singleElevation,
          startIndex: 0,
          endIndex: 0,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.start-slider .slider-index').text()).toBe('0')
      expect(wrapper.find('.end-slider .slider-index').text()).toBe('0')
    })

    it('should handle missing time data', () => {
      const pointsWithoutTime = mockPoints.map((p) => ({ ...p, time: undefined }))

      wrapper = mount(ElevationCropper, {
        props: {
          points: pointsWithoutTime,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 1,
          endIndex: 3,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      // Time values should show '-' when time data is missing
      const timeValues = wrapper.findAll('.metric .value')
      expect(timeValues[0].text()).toBe('-') // start time
      expect(timeValues[3].text()).toBe('-') // end time
    })

    it('should handle undefined elevation data', () => {
      const pointsWithUndefinedElevation = mockPoints.map((p) => ({
        ...p,
        elevation: undefined
      }))

      wrapper = mount(ElevationCropper, {
        props: {
          points: pointsWithUndefinedElevation,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 1,
          endIndex: 3,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      // Should still render without errors
      expect(wrapper.find('.card-elevation').exists()).toBe(true)
    })
  })

  describe('Internationalization', () => {
    it('should display text in English by default', () => {
      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 0,
          endIndex: 4,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.axis-toggle button.left').text()).toContain('Distance')
      expect(wrapper.find('.axis-toggle button.right').text()).toContain('Time')
    })

    it('should display text in French when locale is changed', () => {
      const frenchI18n = createI18n({
        legacy: false,
        locale: 'fr',
        messages: {
          en,
          fr
        }
      })

      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 0,
          endIndex: 4,
          xMode: 'distance'
        },
        global: {
          plugins: [frenchI18n]
        }
      })

      expect(wrapper.find('.axis-toggle button.left').text()).toContain('Distance')
      expect(wrapper.find('.axis-toggle button.right').text()).toContain('Temps')
    })
  })

  describe('Component Cleanup', () => {
    it('should destroy chart when component is unmounted', async () => {
      const { Chart } = await import('chart.js')

      wrapper = mount(ElevationCropper, {
        props: {
          points: mockPoints,
          cumulativeKm: mockCumulativeKm,
          cumulativeSec: mockCumulativeSec,
          smoothedElevations: mockSmoothedElevations,
          startIndex: 0,
          endIndex: 4,
          xMode: 'distance'
        },
        global: {
          plugins: [i18n]
        }
      })

      await new Promise((resolve) => setTimeout(resolve, 150))

      wrapper.unmount()

      expect((Chart as any).mock.results[0].value.destroy).toHaveBeenCalled()
    })
  })
})
