import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import RoutePlannerSidebar from '../components/RoutePlannerSidebar.vue'
import { createI18n } from 'vue-i18n'

// Create i18n instance
const i18n = createI18n({
  legacy: false,
  locale: 'en',
  fallbackLocale: 'en',
  messages: {
    en: {
      routePlanner: {
        routingMode: 'Routing Mode',
        standardMode: 'Standard Mode',
        standardModeDescription: 'Click anywhere on the map to add waypoints',
        startEndMode: 'Start/End Mode',
        startEndModeDescription: 'Set start and end points, then generate route',
        chooseNextWaypoint: 'Choose your next waypoint',
        guidedTodoList: 'Guided Route Planning',
        guidedTodoInstructions: 'Follow the steps below to plan your route',
        filters: 'Filters',
        clearFilters: 'Clear Filters',
        difficulty: 'Difficulty',
        surface: 'Surface',
        tire: 'Tire',
        dry: 'Dry',
        wet: 'Wet',
        selectedSegments: 'Selected Segments',
        noSegmentsSelectedMessage: 'No segments selected yet',
        removeSegment: 'Remove Segment',
        generateRoute: 'Generate Route',
        surfaceTypes: {
          bigStoneRoad: 'Big Stone Road',
          brokenPavedRoad: 'Broken Paved Road',
          dirtyRoad: 'Dirty Road',
          fieldTrail: 'Field Trail',
          forestTrail: 'Forest Trail',
          smallStoneRoad: 'Small Stone Road'
        },
        tireTypes: {
          slick: 'Slick',
          semiSlick: 'Semi-Slick',
          knobs: 'Knobs'
        }
      }
    }
  }
})

// Helper to create complete mock segment
const createMockSegment = (id: number, name: string, overrides = {}) => ({
  id,
  name,
  file_path: `/tracks/${id}.gpx`,
  bound_north: 46.862104,
  bound_south: 46.860104,
  bound_east: 3.980509,
  bound_west: 3.978509,
  barycenter_latitude: 46.861104,
  barycenter_longitude: 3.979509,
  track_type: 'gravel',
  difficulty_level: 3,
  surface_type: ['broken-paved-road'],
  tire_dry: 'slick',
  tire_wet: 'knobs',
  comments: '',
  ...overrides
})

describe('RoutePlannerSidebar', () => {
  const defaultProps = {
    showSidebar: false,
    routeMode: 'standard' as const,
    startWaypoint: null,
    endWaypoint: null,
    selectedSegments: [],
    segmentFilters: {
      difficultyMin: 1,
      difficultyMax: 5,
      surface: [],
      tireDry: [],
      tireWet: []
    },
    filtersExpanded: false,
    routeDistance: 0,
    elevationStats: {
      totalGain: 0,
      totalLoss: 0,
      maxElevation: 0,
      minElevation: 0
    },
    routeGenerationProgress: {
      isGenerating: false,
      current: 0,
      total: 0,
      message: ''
    }
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Component Rendering', () => {
    it('renders correctly', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: defaultProps,
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.sidebar-menu').exists()).toBe(true)
    })

    it('applies sidebar-open class when showSidebar is true', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          showSidebar: true
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.sidebar-menu').classes()).toContain('sidebar-open')
    })

    it('does not apply sidebar-open class when showSidebar is false', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: defaultProps,
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.sidebar-menu').classes()).not.toContain('sidebar-open')
    })
  })

  describe('Mode Toggle', () => {
    it('renders mode toggle', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: defaultProps,
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.mode-toggle').exists()).toBe(true)
    })

    it('emits toggle-mode event when mode toggle is changed', async () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: defaultProps,
        global: {
          plugins: [i18n]
        }
      })

      const checkbox = wrapper.find('input[type="checkbox"]')
      await checkbox.trigger('change')

      expect(wrapper.emitted('toggle-mode')).toBeTruthy()
      expect(wrapper.emitted('toggle-mode')).toHaveLength(1)
    })

    it('checkbox is checked when routeMode is startEnd', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd'
        },
        global: {
          plugins: [i18n]
        }
      })

      const checkbox = wrapper.find('input[type="checkbox"]')
      expect((checkbox.element as HTMLInputElement).checked).toBe(true)
    })

    it('checkbox is not checked when routeMode is standard', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: defaultProps,
        global: {
          plugins: [i18n]
        }
      })

      const checkbox = wrapper.find('input[type="checkbox"]')
      expect((checkbox.element as HTMLInputElement).checked).toBe(false)
    })
  })

  describe('Standard Mode Instructions', () => {
    it('shows instructions in standard mode', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: defaultProps,
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.free-mode-instructions').exists()).toBe(true)
    })

    it('does not show instructions in startEnd mode', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd'
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.free-mode-instructions').exists()).toBe(false)
    })
  })

  describe('Guided Mode Todo List', () => {
    it('shows todo list in startEnd mode', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd'
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.guided-todo-list').exists()).toBe(true)
    })

    it('does not show todo list in standard mode', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: defaultProps,
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.guided-todo-list').exists()).toBe(false)
    })

    it('shows completed checkmark for start waypoint when set', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 }
        },
        global: {
          plugins: [i18n]
        }
      })

      const todoItems = wrapper.findAll('.todo-item')
      const startTodoItem = todoItems[0]

      expect(startTodoItem.classes()).toContain('completed')
      expect(startTodoItem.find('.fa-check').exists()).toBe(true)
    })

    it('shows spinner for start waypoint when not set', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd'
        },
        global: {
          plugins: [i18n]
        }
      })

      const todoItems = wrapper.findAll('.todo-item')
      const startTodoItem = todoItems[0]

      expect(startTodoItem.classes()).not.toContain('completed')
      expect(startTodoItem.find('.fa-spinner').exists()).toBe(true)
    })

    it('shows completed checkmark for end waypoint when set', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          endWaypoint: { lat: 46.861104, lng: 3.979509 }
        },
        global: {
          plugins: [i18n]
        }
      })

      const todoItems = wrapper.findAll('.todo-item')
      const endTodoItem = todoItems[1]

      expect(endTodoItem.classes()).toContain('completed')
      expect(endTodoItem.find('.fa-check').exists()).toBe(true)
    })
  })

  describe('Segment Filters', () => {
    it('shows filters section when in startEnd mode with waypoints set', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 }
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.segment-filters-section').exists()).toBe(true)
    })

    it('does not show filters section in standard mode', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: defaultProps,
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.segment-filters-section').exists()).toBe(false)
    })

    it('emits toggle-filters event when filters toggle button is clicked', async () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 }
        },
        global: {
          plugins: [i18n]
        }
      })

      const toggleButton = wrapper.find('.filters-toggle-btn')
      await toggleButton.trigger('click')

      expect(wrapper.emitted('toggle-filters')).toBeTruthy()
    })

    it('emits clear-filters event when clear filters button is clicked', async () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 },
          segmentFilters: {
            difficultyMin: 2,
            difficultyMax: 4,
            surface: ['big-stone-road'],
            tireDry: [],
            tireWet: []
          }
        },
        global: {
          plugins: [i18n]
        }
      })

      const clearButton = wrapper.find('.clear-filters-btn')
      await clearButton.trigger('click')

      expect(wrapper.emitted('clear-filters')).toBeTruthy()
    })

    it('shows clear filters button when filters are active', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 },
          segmentFilters: {
            difficultyMin: 2,
            difficultyMax: 4,
            surface: [],
            tireDry: [],
            tireWet: []
          }
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.clear-filters-btn').exists()).toBe(true)
    })

    it('does not show clear filters button when no filters are active', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 }
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.clear-filters-btn').exists()).toBe(false)
    })
  })

  describe('Difficulty Filter', () => {
    it('renders difficulty sliders', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 },
          filtersExpanded: true
        },
        global: {
          plugins: [i18n]
        }
      })

      const sliders = wrapper.findAll('.difficulty-slider')
      expect(sliders).toHaveLength(2)
    })

    it('emits update:difficulty-min when min slider changes', async () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 },
          filtersExpanded: true
        },
        global: {
          plugins: [i18n]
        }
      })

      const minSlider = wrapper.find('.difficulty-slider-min')
      await minSlider.setValue('3')

      expect(wrapper.emitted('update:difficulty-min')).toBeTruthy()
      expect(wrapper.emitted('update:difficulty-min')?.[0]).toEqual([3])
    })

    it('emits update:difficulty-max when max slider changes', async () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 },
          filtersExpanded: true
        },
        global: {
          plugins: [i18n]
        }
      })

      const maxSlider = wrapper.find('.difficulty-slider-max')
      await maxSlider.setValue('4')

      expect(wrapper.emitted('update:difficulty-max')).toBeTruthy()
      expect(wrapper.emitted('update:difficulty-max')?.[0]).toEqual([4])
    })
  })

  describe('Surface Filter', () => {
    it('renders surface filter buttons', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 },
          filtersExpanded: true
        },
        global: {
          plugins: [i18n]
        }
      })

      // Should have 6 surface types
      const surfaceButtons = wrapper
        .findAll('.filter-btn-with-image')
        .filter((btn) => btn.find('.surface-filter-image').exists())
      expect(surfaceButtons.length).toBeGreaterThan(0)
    })

    it('emits toggle-filter event when surface filter is clicked', async () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 },
          filtersExpanded: true
        },
        global: {
          plugins: [i18n]
        }
      })

      const surfaceButton = wrapper
        .findAll('.filter-btn-with-image')
        .find((btn) => btn.find('.surface-filter-image').exists())

      if (surfaceButton) {
        await surfaceButton.trigger('click')
        expect(wrapper.emitted('toggle-filter')).toBeTruthy()
      }
    })

    it('shows active class for selected surface filters', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 },
          filtersExpanded: true,
          segmentFilters: {
            ...defaultProps.segmentFilters,
            surface: ['big-stone-road']
          }
        },
        global: {
          plugins: [i18n]
        }
      })

      // Find button with big-stone-road
      const activeButtons = wrapper.findAll('.filter-btn.active')
      expect(activeButtons.length).toBeGreaterThan(0)
    })
  })

  describe('Tire Filter', () => {
    it('renders dry tire filter buttons', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 },
          filtersExpanded: true
        },
        global: {
          plugins: [i18n]
        }
      })

      const tireButtons = wrapper
        .findAll('.filter-btn-with-image')
        .filter((btn) => btn.find('.tire-filter-image').exists())
      expect(tireButtons.length).toBeGreaterThan(0)
    })

    it('emits toggle-filter event when dry tire filter is clicked', async () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 },
          filtersExpanded: true
        },
        global: {
          plugins: [i18n]
        }
      })

      const tireButton = wrapper
        .findAll('.filter-btn-with-image')
        .find((btn) => btn.find('.tire-filter-image').exists())

      if (tireButton) {
        await tireButton.trigger('click')
        expect(wrapper.emitted('toggle-filter')).toBeTruthy()
      }
    })
  })

  describe('Selected Segments', () => {
    const mockSegments = [
      createMockSegment(1, 'Test Segment 1'),
      createMockSegment(2, 'Test Segment 2', {
        difficulty_level: 4,
        surface_type: ['dirty-road'],
        tire_dry: 'semi-slick'
      })
    ]

    it('shows selected segments section when in startEnd mode with waypoints', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 }
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.selected-segments-section').exists()).toBe(true)
    })

    it('shows empty state message when no segments selected', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 }
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.no-segments-message').exists()).toBe(true)
    })

    it('renders selected segments list', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 },
          selectedSegments: mockSegments
        },
        global: {
          plugins: [i18n]
        }
      })

      const segmentItems = wrapper.findAll('.selected-segment-item')
      expect(segmentItems).toHaveLength(2)
      expect(segmentItems[0].text()).toContain('Test Segment 1')
      expect(segmentItems[1].text()).toContain('Test Segment 2')
    })

    it('emits deselect-segment event when remove button is clicked', async () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 },
          selectedSegments: mockSegments
        },
        global: {
          plugins: [i18n]
        }
      })

      const removeButton = wrapper.find('.remove-segment-btn')
      await removeButton.trigger('click')

      expect(wrapper.emitted('deselect-segment')).toBeTruthy()
      expect(wrapper.emitted('deselect-segment')?.[0][0]).toEqual(mockSegments[0])
    })

    it('emits reverse-segment event when reverse button is clicked', async () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 },
          selectedSegments: mockSegments
        },
        global: {
          plugins: [i18n]
        }
      })

      const reverseButton = wrapper.find('.reverse-segment-btn')
      await reverseButton.trigger('click')

      expect(wrapper.emitted('reverse-segment')).toBeTruthy()
      expect(wrapper.emitted('reverse-segment')?.[0][0]).toEqual(mockSegments[0])
    })

    it('emits segment-hover event on mouseenter', async () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 },
          selectedSegments: mockSegments
        },
        global: {
          plugins: [i18n]
        }
      })

      const segmentItem = wrapper.find('.selected-segment-item')
      await segmentItem.trigger('mouseenter')

      expect(wrapper.emitted('segment-hover')).toBeTruthy()
      expect(wrapper.emitted('segment-hover')?.[0][0]).toEqual(mockSegments[0])
    })

    it('emits segment-leave event on mouseleave', async () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 },
          selectedSegments: mockSegments
        },
        global: {
          plugins: [i18n]
        }
      })

      const segmentItem = wrapper.find('.selected-segment-item')
      await segmentItem.trigger('mouseleave')

      expect(wrapper.emitted('segment-leave')).toBeTruthy()
      expect(wrapper.emitted('segment-leave')?.[0][0]).toEqual(mockSegments[0])
    })
  })

  describe('Drag and Drop', () => {
    const mockSegments = [createMockSegment(1, 'Test Segment 1')]

    it('emits drag-start event on dragstart', async () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 },
          selectedSegments: mockSegments
        },
        global: {
          plugins: [i18n]
        }
      })

      const segmentItem = wrapper.find('.selected-segment-item')
      await segmentItem.trigger('dragstart')

      expect(wrapper.emitted('drag-start')).toBeTruthy()
    })

    it('emits drag-over event on dragover', async () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 },
          selectedSegments: mockSegments
        },
        global: {
          plugins: [i18n]
        }
      })

      const segmentItem = wrapper.find('.selected-segment-item')
      await segmentItem.trigger('dragover')

      expect(wrapper.emitted('drag-over')).toBeTruthy()
    })

    it('emits drag-drop event on drop', async () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 },
          selectedSegments: mockSegments
        },
        global: {
          plugins: [i18n]
        }
      })

      const segmentItem = wrapper.find('.selected-segment-item')
      await segmentItem.trigger('drop')

      expect(wrapper.emitted('drag-drop')).toBeTruthy()
    })

    it('emits drag-end event on dragend', async () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 },
          selectedSegments: mockSegments
        },
        global: {
          plugins: [i18n]
        }
      })

      const segmentItem = wrapper.find('.selected-segment-item')
      await segmentItem.trigger('dragend')

      expect(wrapper.emitted('drag-end')).toBeTruthy()
    })
  })

  describe('Generate Route Button', () => {
    it('shows generate route button in startEnd mode', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd'
        },
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.generate-route-btn').exists()).toBe(true)
    })

    it('does not show generate route button in standard mode', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: defaultProps,
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.generate-route-btn').exists()).toBe(false)
    })

    it('button is disabled when waypoints are not set', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd'
        },
        global: {
          plugins: [i18n]
        }
      })

      const button = wrapper.find('.generate-route-btn')
      expect(button.attributes('disabled')).toBeDefined()
      expect(button.classes()).toContain('disabled')
    })

    it('button is enabled when both waypoints are set', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 }
        },
        global: {
          plugins: [i18n]
        }
      })

      const button = wrapper.find('.generate-route-btn')
      expect(button.attributes('disabled')).toBeUndefined()
      expect(button.classes()).not.toContain('disabled')
    })

    it('emits generate-route event when button is clicked', async () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: {
          ...defaultProps,
          routeMode: 'startEnd',
          startWaypoint: { lat: 46.860104, lng: 3.978509 },
          endWaypoint: { lat: 46.861104, lng: 3.979509 }
        },
        global: {
          plugins: [i18n]
        }
      })

      const button = wrapper.find('.generate-route-btn')
      await button.trigger('click')

      expect(wrapper.emitted('generate-route')).toBeTruthy()
    })
  })

  describe('Close Button', () => {
    it('renders close button', () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: defaultProps,
        global: {
          plugins: [i18n]
        }
      })

      expect(wrapper.find('.sidebar-close').exists()).toBe(true)
    })

    it('emits close event when close button is clicked', async () => {
      const wrapper = mount(RoutePlannerSidebar, {
        props: defaultProps,
        global: {
          plugins: [i18n]
        }
      })

      const closeButton = wrapper.find('.sidebar-close')
      await closeButton.trigger('click')

      expect(wrapper.emitted('close')).toBeTruthy()
    })
  })
})
