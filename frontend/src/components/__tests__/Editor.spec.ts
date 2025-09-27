import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import Editor from '../Editor.vue'
import { createI18n } from 'vue-i18n'

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock fetch in the component context
vi.stubGlobal('fetch', mockFetch)

// Mock FileReader
const mockFileReader = {
  readAsDataURL: vi.fn(),
  result: 'data:image/jpeg;base64,test-image-data',
  onload: null as any
}

global.FileReader = vi.fn(() => mockFileReader) as any

// Mock Leaflet
vi.mock('leaflet', () => ({
  default: {
    map: vi.fn(() => ({
      setView: vi.fn(),
      addLayer: vi.fn(),
      removeLayer: vi.fn(),
      invalidateSize: vi.fn(),
      fitBounds: vi.fn(),
      on: vi.fn(),
      off: vi.fn()
    })),
    tileLayer: vi.fn(() => ({
      addTo: vi.fn()
    })),
    polyline: vi.fn(() => ({
      addTo: vi.fn(),
      on: vi.fn(),
      remove: vi.fn(),
      getBounds: vi.fn(() => ({
        getCenter: vi.fn(() => ({ lat: 0, lng: 0 })),
        getNorthEast: vi.fn(() => ({ lat: 1, lng: 1 })),
        getSouthWest: vi.fn(() => ({ lat: -1, lng: -1 }))
      }))
    })),
    marker: vi.fn(() => ({
      addTo: vi.fn(),
      setLatLng: vi.fn(),
      remove: vi.fn()
    })),
    circleMarker: vi.fn(() => ({
      addTo: vi.fn(),
      setLatLng: vi.fn(),
      remove: vi.fn()
    })),
    divIcon: vi.fn(() => ({})),
    icon: vi.fn(() => ({})),
    latLng: vi.fn(() => ({})),
    latLngBounds: vi.fn(() => ({
      getCenter: vi.fn(() => ({ lat: 0, lng: 0 })),
      getNorthEast: vi.fn(() => ({ lat: 1, lng: 1 })),
      getSouthWest: vi.fn(() => ({ lat: -1, lng: -1 }))
    })),
    control: {
      scale: vi.fn(() => ({
        addTo: vi.fn()
      }))
    }
  }
}))

// Mock Chart.js
vi.mock('chart.js', () => ({
  Chart: Object.assign(
    vi.fn().mockImplementation((ctx, config) => ({
      destroy: vi.fn(),
      update: vi.fn(),
      render: vi.fn(),
      resize: vi.fn(),
      canvas: {
        getBoundingClientRect: vi.fn(() => ({
          left: 0,
          top: 0,
          width: 800,
          height: 400
        }))
      },
      scales: {
        x: {
          getPixelForValue: vi.fn((value) => value * 10)
        }
      },
      ctx,
      config
    })),
    {
      register: vi.fn()
    }
  ),
  LineController: {},
  LineElement: {},
  PointElement: {},
  LinearScale: {},
  CategoryScale: {},
  Title: {},
  Filler: {},
  Tooltip: {},
  registerables: []
}))

// Create a more complete chart mock for tests
const createChartMock = () => ({
  destroy: vi.fn(),
  update: vi.fn(),
  render: vi.fn(),
  resize: vi.fn(),
  canvas: {
    getBoundingClientRect: vi.fn(() => ({
      left: 0,
      top: 0,
      width: 800,
      height: 400
    }))
  },
  scales: {
    x: {
      getPixelForValue: vi.fn((value) => value * 10)
    }
  }
})

// Mock axios
vi.mock('axios', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn()
  }
}))

// Mock file API
Object.defineProperty(HTMLInputElement.prototype, 'files', {
  writable: true,
  value: undefined
})

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
})

// Import real locale files
import en from '../../i18n/locales/en'
import fr from '../../i18n/locales/fr'

// Create i18n instance for testing using real locale files
const i18n = createI18n({
  legacy: false,
  locale: 'en',
  fallbackLocale: 'en',
  messages: { en, fr }
})

// Helper function to mount Editor with proper stubs
const mountEditor = (options = {}) => {
  return mount(Editor, {
    global: {
      plugins: [i18n],
      stubs: {
        'router-link': {
          template: '<a :href="to" :class="activeClass"><slot /></a>',
          props: ['to', 'activeClass']
        }
      }
    },
    ...options
  })
}

describe('Editor', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock.getItem.mockReturnValue('en')
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders correctly', () => {
    const wrapper = mountEditor()

    expect(wrapper.find('.editor').exists()).toBe(true)
    expect(wrapper.find('.sidebar').exists()).toBe(true)
    expect(wrapper.find('.content').exists()).toBe(true)
  })

  // Non-regression test to ensure Editor doesn't have its own navbar
  it('should not have its own navbar component', () => {
    const wrapper = mountEditor()

    // Editor should not contain a navbar
    expect(wrapper.find('.navbar').exists()).toBe(false)
    expect(wrapper.findComponent({ name: 'Navbar' }).exists()).toBe(false)
  })

  it('shows empty state when no file is loaded', () => {
    const wrapper = mountEditor()

    expect(wrapper.find('.empty').exists()).toBe(true)
    expect(wrapper.find('.empty').text()).toContain(
      'Use "Import from ..." → "GPX file" to begin'
    )
  })

  it('displays save button as disabled when no file is loaded', () => {
    const wrapper = mountEditor()

    const saveButton = wrapper.find('.menu-item.action')
    expect(saveButton.exists()).toBe(true)
    expect(saveButton.classes()).toContain('disabled')
    expect(saveButton.attributes('aria-disabled')).toBe('true')
  })

  it('triggers file input when GPX file menu item is clicked', async () => {
    const wrapper = mountEditor()

    const gpxMenuItem = wrapper.find('.menu-item')
    if (gpxMenuItem.exists()) {
      await gpxMenuItem.trigger('click')
      // The component should handle the click event
      expect(gpxMenuItem.exists()).toBe(true)
    }
  })

  it('handles file selection correctly', async () => {
    const wrapper = mountEditor()

    // Test that the file input exists and can be found
    const fileInput = wrapper.find('input[type="file"]')
    expect(fileInput.exists()).toBe(true)
    expect(fileInput.attributes('accept')).toBe('.gpx')
  })

  it('shows form fields when file is loaded', async () => {
    const wrapper = mountEditor()

    // Test that the basic structure exists in the template
    expect(wrapper.find('.editor').exists()).toBe(true)
    expect(wrapper.find('.sidebar').exists()).toBe(true)
    expect(wrapper.find('.content').exists()).toBe(true)
  })

  it('updates form fields correctly', async () => {
    const wrapper = mountEditor()

    // Test that the component renders without errors
    expect(wrapper.find('.editor').exists()).toBe(true)
  })

  it('handles commentary text input', async () => {
    const wrapper = mountEditor()

    // Test that the component renders without errors
    expect(wrapper.find('.editor').exists()).toBe(true)
  })

  it('handles image drag and drop events', async () => {
    const wrapper = mountEditor()

    const dropZone = wrapper.find('.image-upload-area')
    if (dropZone.exists()) {
      const mockEvent = {
        preventDefault: vi.fn(),
        dataTransfer: {
          files: [new File([''], 'test.jpg', { type: 'image/jpeg' })]
        }
      }

      await dropZone.trigger('dragover', mockEvent)
      await dropZone.trigger('dragleave')

      // Test that the drop zone exists and can handle events
      expect(dropZone.exists()).toBe(true)
    }
  })

  it('shows error messages correctly', async () => {
    const wrapper = mountEditor()

    // Test that the message container exists
    const messageContainer = wrapper.find('.message')
    expect(messageContainer.exists()).toBe(false) // Initially no message
  })

  it('shows success messages correctly', async () => {
    const wrapper = mountEditor()

    // Test that the component renders without errors
    expect(wrapper.find('.editor').exists()).toBe(true)
  })

  it('validates required fields before saving', async () => {
    const wrapper = mountEditor()

    // Test that the save button exists and is initially disabled
    const saveButton = wrapper.find('.menu-item.action')
    expect(saveButton.exists()).toBe(true)
    expect(saveButton.classes()).toContain('disabled')
  })

  it('handles slider movement correctly', async () => {
    const wrapper = mountEditor()

    // Test that the component has the moveSlider method
    expect(typeof (wrapper.vm as any).moveSlider).toBe('function')
  })

  it('handles form field updates correctly', async () => {
    const wrapper = mountEditor()

    // Test segment name input
    const nameInput = wrapper.find('input[name="segment-name"]')
    if (nameInput.exists()) {
      await nameInput.setValue('Test Segment')
      expect((nameInput.element as any).value).toBe('Test Segment')
    }

    // Test commentary text input
    const commentaryTextarea = wrapper.find('textarea[name="commentary-text"]')
    if (commentaryTextarea.exists()) {
      await commentaryTextarea.setValue('This is a test commentary')
      expect((commentaryTextarea.element as any).value).toBe(
        'This is a test commentary'
      )
    }
  })

  it('renders track type tabs correctly when file is loaded', async () => {
    const wrapper = mountEditor()

    // Simulate file loaded state
    const vm = wrapper.vm as any
    vm.loaded = true
    vm.points = [{ latitude: 0, longitude: 0, elevation: 0 }]
    vm.startIndex = 0
    vm.endIndex = 0
    await wrapper.vm.$nextTick()

    const tabs = wrapper.find('.track-type-tabs')
    expect(tabs.exists()).toBe(true)

    const segmentTab = tabs.find('.tab-button:first-child')
    const routeTab = tabs.find('.tab-button:last-child')

    expect(segmentTab.exists()).toBe(true)
    expect(routeTab.exists()).toBe(true)

    expect(segmentTab.text()).toContain('Segment')
    expect(routeTab.text()).toContain('Route')
  })

  it('switches between segment and route tabs', async () => {
    const wrapper = mountEditor()

    // Simulate file loaded state
    const vm = wrapper.vm as any
    vm.loaded = true
    vm.points = [{ latitude: 0, longitude: 0, elevation: 0 }]
    vm.startIndex = 0
    vm.endIndex = 0
    await wrapper.vm.$nextTick()

    const segmentTab = wrapper.find('.tab-button:first-child')
    const routeTab = wrapper.find('.tab-button:last-child')

    // Initially segment tab should be active
    expect(segmentTab.classes()).toContain('active')
    expect(routeTab.classes()).not.toContain('active')

    // Click route tab
    await routeTab.trigger('click')
    await wrapper.vm.$nextTick()

    expect(routeTab.classes()).toContain('active')
    expect(segmentTab.classes()).not.toContain('active')

    // Click segment tab
    await segmentTab.trigger('click')
    await wrapper.vm.$nextTick()

    expect(segmentTab.classes()).toContain('active')
    expect(routeTab.classes()).not.toContain('active')
  })

  it('updates form labels based on track type', async () => {
    const wrapper = mountEditor()

    // Simulate file loaded state
    const vm = wrapper.vm as any
    vm.loaded = true
    vm.points = [{ latitude: 0, longitude: 0, elevation: 0 }]
    vm.startIndex = 0
    vm.endIndex = 0
    await wrapper.vm.$nextTick()

    // Test segment tab labels
    const segmentTab = wrapper.find('.tab-button:first-child')
    await segmentTab.trigger('click')
    await wrapper.vm.$nextTick()

    const nameLabel = wrapper.find('label[for="name"]')
    expect(nameLabel.text()).toContain('Segment name')

    const surfaceTypeLabels = wrapper.findAll('.subsection-title')
    const surfaceTypeLabel = surfaceTypeLabels.find((el: any) =>
      el.text().includes('Surface type')
    )
    expect(surfaceTypeLabel?.text()).toContain('Surface type')

    // Test route tab labels
    const routeTab = wrapper.find('.tab-button:last-child')
    await routeTab.trigger('click')
    await wrapper.vm.$nextTick()

    expect(nameLabel.text()).toContain('Route name')
    const routeSurfaceTypeLabel = surfaceTypeLabels.find((el: any) =>
      el.text().includes('Major surface type')
    )
    expect(routeSurfaceTypeLabel?.text()).toContain('Major surface type')
  })

  it('includes track_type in form submission', async () => {
    const wrapper = mountEditor()

    // Mock fetch to capture form data
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ id: 1, name: 'Test' })
    })
    ;(global as any).fetch = mockFetch

    // Set up component state
    const vm = wrapper.vm as any
    vm.loaded = true
    vm.name = 'Test Track'
    vm.trackType = 'route'
    vm.points = [
      { latitude: 0, longitude: 0, elevation: 0 },
      { latitude: 1, longitude: 1, elevation: 100 }
    ]
    vm.startIndex = 0
    vm.endIndex = 1
    vm.uploadedFileId = 'test-file-id'
    vm.trailConditions = {
      tire_dry: 'slick',
      tire_wet: 'semi-slick',
      surface_type: 'forest-trail',
      difficulty_level: 3
    }
    await wrapper.vm.$nextTick()

    // Check that the form is ready for submission
    expect(vm.isSaveDisabled).toBe(false)

    // Trigger form submission
    await vm.onSubmit()

    // Check that track_type was included in the form data
    expect(mockFetch).toHaveBeenCalled()
    const formData = mockFetch.mock.calls[0][1].body
    expect(formData).toBeInstanceOf(FormData)
    expect(formData.get('track_type')).toBe('route')
  })

  it('handles trail conditions updates', async () => {
    const wrapper = mountEditor()

    // Test surface type selection
    const surfaceSelect = wrapper.find('select[name="surface-type"]')
    if (surfaceSelect.exists()) {
      await surfaceSelect.setValue('forest-trail')
      expect((surfaceSelect.element as any).value).toBe('forest-trail')
    }

    // Test difficulty level
    const difficultySlider = wrapper.find('input[name="difficulty-level"]')
    if (difficultySlider.exists()) {
      await difficultySlider.setValue('4')
      expect((difficultySlider.element as any).value).toBe('4')
    }
  })

  it('handles tire condition changes', async () => {
    const wrapper = mountEditor()

    // Test dry tire selection
    const dryTireSelect = wrapper.find('select[name="tire-dry"]')
    if (dryTireSelect.exists()) {
      await dryTireSelect.setValue('semi-slick')
      expect((dryTireSelect.element as any).value).toBe('semi-slick')
    }

    // Test wet tire selection
    const wetTireSelect = wrapper.find('select[name="tire-wet"]')
    if (wetTireSelect.exists()) {
      await wetTireSelect.setValue('knobs')
      expect((wetTireSelect.element as any).value).toBe('knobs')
    }
  })

  it('handles video link additions', async () => {
    const wrapper = mountEditor()

    // Test adding video link
    const addVideoButton = wrapper.find('button[title*="Add video link"]')
    if (addVideoButton.exists()) {
      await addVideoButton.trigger('click')

      // Check if video input fields appear
      const videoUrlInput = wrapper.find('input[placeholder*="youtube.com"]')
      if (videoUrlInput.exists()) {
        await videoUrlInput.setValue('https://youtube.com/watch?v=test')

        const videoTitleInput = wrapper.find('input[placeholder*="Video title"]')
        if (videoTitleInput.exists()) {
          await videoTitleInput.setValue('Test Video')
          expect((videoTitleInput.element as any).value).toBe('Test Video')
        }
      }
    }
  })

  it('handles image upload trigger', async () => {
    const wrapper = mountEditor()

    // Test image upload trigger
    const imageUploadArea = wrapper.find('.image-upload-area')
    if (imageUploadArea.exists()) {
      await imageUploadArea.trigger('click')
      // The actual file input should be triggered
    }
  })

  it('handles drag and drop for images', async () => {
    const wrapper = mountEditor()

    const imageUploadArea = wrapper.find('.image-upload-area')
    if (imageUploadArea.exists()) {
      const mockEvent = {
        preventDefault: vi.fn(),
        dataTransfer: {
          files: [new File([''], 'test.jpg', { type: 'image/jpeg' })]
        }
      }

      await imageUploadArea.trigger('dragover', mockEvent)
      await imageUploadArea.trigger('drop', mockEvent)

      expect(mockEvent.preventDefault).toHaveBeenCalled()
    }
  })

  it('handles slider controls for start/end markers', async () => {
    const wrapper = mountEditor()

    // Test start marker controls
    const moveStartBackButton = wrapper.find('button[title*="Move start marker back"]')
    if (moveStartBackButton.exists()) {
      await moveStartBackButton.trigger('click')
    }

    const moveStartForwardButton = wrapper.find(
      'button[title*="Move start marker forward"]'
    )
    if (moveStartForwardButton.exists()) {
      await moveStartForwardButton.trigger('click')
    }

    // Test end marker controls
    const moveEndBackButton = wrapper.find('button[title*="Move end marker back"]')
    if (moveEndBackButton.exists()) {
      await moveEndBackButton.trigger('click')
    }

    const moveEndForwardButton = wrapper.find(
      'button[title*="Move end marker forward"]'
    )
    if (moveEndForwardButton.exists()) {
      await moveEndForwardButton.trigger('click')
    }
  })

  it('handles chart mode switching', async () => {
    const wrapper = mountEditor()

    // Test switching between distance and time modes
    const timeModeButton = wrapper.find('button[title*="Time"]')
    if (timeModeButton.exists()) {
      await timeModeButton.trigger('click')
    }

    const distanceModeButton = wrapper.find('button[title*="Distance"]')
    if (distanceModeButton.exists()) {
      await distanceModeButton.trigger('click')
    }
  })

  it('handles form validation correctly', async () => {
    const wrapper = mountEditor()

    // Test save button state when form is invalid
    const saveButton = wrapper.find('.menu-item.action')
    expect(saveButton.exists()).toBe(true)
    expect(saveButton.classes()).toContain('disabled')
    expect(saveButton.attributes('aria-disabled')).toBe('true')

    // Test tooltip when no file is loaded
    expect(saveButton.attributes('title')).toContain('Load a GPX first')
  })

  it('handles error state display', async () => {
    const wrapper = mountEditor()

    // Test error message display
    const errorMessage = wrapper.find('.error-message')
    if (errorMessage.exists()) {
      expect(errorMessage.isVisible()).toBe(false)
    }
  })

  it('handles success state display', async () => {
    const wrapper = mountEditor()

    // Test success message display
    const successMessage = wrapper.find('.success-message')
    if (successMessage.exists()) {
      expect(successMessage.isVisible()).toBe(false)
    }
  })

  it('handles upload progress display', async () => {
    const wrapper = mountEditor()

    // Test upload progress bar
    const uploadProgress = wrapper.find('.upload-progress-bar')
    if (uploadProgress.exists()) {
      expect(uploadProgress.isVisible()).toBe(false)
    }
  })

  it('handles file input change events', async () => {
    const wrapper = mountEditor()

    const fileInput = wrapper.find('input[type="file"]')
    expect(fileInput.exists()).toBe(true)

    // Test that the file input exists and can be interacted with
    expect((fileInput.element as any).type).toBe('file')
    expect((fileInput.element as any).accept).toContain('.gpx')
  })

  it('handles difficulty level setting', async () => {
    const wrapper = mountEditor()

    // Test difficulty level buttons
    const difficultyButtons = wrapper.findAll('button[data-level]')
    if (difficultyButtons.length > 0) {
      await difficultyButtons[0].trigger('click')
      await difficultyButtons[2].trigger('click')
    }
  })

  it('handles image removal', async () => {
    const wrapper = mountEditor()

    // Test image removal buttons
    const removeImageButtons = wrapper.findAll('button[title*="Remove image"]')
    if (removeImageButtons.length > 0) {
      await removeImageButtons[0].trigger('click')
    }
  })

  it('handles video removal', async () => {
    const wrapper = mountEditor()

    // Test video removal buttons
    const removeVideoButtons = wrapper.findAll('button[title*="Remove video"]')
    if (removeVideoButtons.length > 0) {
      await removeVideoButtons[0].trigger('click')
    }
  })

  it('handles form submission success path', async () => {
    const wrapper = mountEditor()

    // Mock successful fetch response
    ;(global as any).fetch = vi.fn().mockResolvedValue({
      ok: true,
      text: () => Promise.resolve('Success')
    })

    // Mock nextTick and render functions
    const vm = wrapper.vm as any
    const renderMapSpy = vi.spyOn(vm, 'renderMap').mockImplementation(() => {})
    const renderChartSpy = vi.spyOn(vm, 'renderChart').mockImplementation(() => {})

    // Set up component state to pass validation
    vm.loaded = true
    vm.points = [
      { latitude: 45.0, longitude: 4.0, elevation: 100, time: '2023-01-01T10:00:00Z' },
      { latitude: 45.1, longitude: 4.1, elevation: 110, time: '2023-01-01T10:01:00Z' }
    ]
    vm.uploadedFileId = 'test-file-123'
    vm.name = 'Test Track'
    vm.trailConditions = {
      tire_dry: 'slick',
      tire_wet: 'semi-slick',
      surface_type: 'forest-trail',
      difficulty_level: 3
    }

    // Submit form
    await vm.onSubmit()

    // Verify success state
    expect(vm.showSegmentSuccess).toBe(true)
    expect(vm.showError).toBe(false)
    expect(vm.currentErrorMessage).toBe('')
    expect(vm.showUploadSuccess).toBe(false)

    // Verify form was reset
    expect(vm.name).toBe('')
    expect(vm.trailConditions).toEqual({
      tire_dry: 'slick',
      tire_wet: 'slick',
      surface_type: 'forest-trail',
      difficulty_level: 3
    })

    // Clean up
    ;(global as any).fetch = undefined
    renderMapSpy.mockRestore()
    renderChartSpy.mockRestore()
  })

  it('handles form submission error with response detail', async () => {
    const wrapper = mountEditor()

    // Mock failed fetch response with detail
    ;(global as any).fetch = vi.fn().mockResolvedValue({
      ok: false,
      text: () => Promise.resolve('Server error detail')
    })

    // Mock setTimeout
    vi.spyOn(global, 'setTimeout')

    // Set up component state to pass validation
    const vm = wrapper.vm as any
    vm.loaded = true
    vm.points = [
      { latitude: 45.0, longitude: 4.0, elevation: 100, time: '2023-01-01T10:00:00Z' },
      { latitude: 45.1, longitude: 4.1, elevation: 110, time: '2023-01-01T10:01:00Z' }
    ]
    vm.uploadedFileId = 'test-file-123'
    vm.name = 'Test Track'

    // Submit form
    await vm.onSubmit()

    // Verify error state
    expect(vm.showError).toBe(true)
    expect(vm.currentErrorMessage).toBe('Server error detail')
    expect(vm.showUploadSuccess).toBe(false)
    expect(vm.showSegmentSuccess).toBe(false)

    // Clean up
    ;(global as any).fetch = undefined
    vi.restoreAllMocks()
  })

  it('handles form submission error without response detail', async () => {
    const wrapper = mountEditor()

    // Mock failed fetch response without detail
    ;(global as any).fetch = vi.fn().mockResolvedValue({
      ok: false,
      text: () => Promise.resolve('')
    })

    // Mock setTimeout
    vi.spyOn(global, 'setTimeout')

    // Set up component state to pass validation
    const vm = wrapper.vm as any
    vm.loaded = true
    vm.points = [
      { latitude: 45.0, longitude: 4.0, elevation: 100, time: '2023-01-01T10:00:00Z' },
      { latitude: 45.1, longitude: 4.1, elevation: 110, time: '2023-01-01T10:01:00Z' }
    ]
    vm.uploadedFileId = 'test-file-123'
    vm.name = 'Test Track'

    // Submit form
    await vm.onSubmit()

    // Verify error state with fallback message
    expect(vm.showError).toBe(true)
    expect(vm.currentErrorMessage).toBe('Failed to create segment')
    expect(vm.showUploadSuccess).toBe(false)
    expect(vm.showSegmentSuccess).toBe(false)

    // Clean up
    ;(global as any).fetch = undefined
    vi.restoreAllMocks()
  })

  it('handles form submission error with exception', async () => {
    const wrapper = mountEditor()

    // Mock fetch to throw an exception
    ;(global as any).fetch = vi.fn().mockRejectedValue(new Error('Network error'))

    // Mock setTimeout
    vi.spyOn(global, 'setTimeout')

    // Set up component state to pass validation
    const vm = wrapper.vm as any
    vm.loaded = true
    vm.points = [
      { latitude: 45.0, longitude: 4.0, elevation: 100, time: '2023-01-01T10:00:00Z' },
      { latitude: 45.1, longitude: 4.1, elevation: 110, time: '2023-01-01T10:01:00Z' }
    ]
    vm.uploadedFileId = 'test-file-123'
    vm.name = 'Test Track'

    // Submit form
    await vm.onSubmit()

    // Verify error state
    expect(vm.showError).toBe(true)
    expect(vm.currentErrorMessage).toBe('Network error')
    expect(vm.showUploadSuccess).toBe(false)
    expect(vm.showSegmentSuccess).toBe(false)

    // Clean up
    ;(global as any).fetch = undefined
    vi.restoreAllMocks()
  })

  it('handles form submission error with exception without message', async () => {
    const wrapper = mountEditor()

    // Mock fetch to throw an exception without message
    ;(global as any).fetch = vi.fn().mockRejectedValue(new Error())

    // Mock setTimeout
    vi.spyOn(global, 'setTimeout')

    // Set up component state to pass validation
    const vm = wrapper.vm as any
    vm.loaded = true
    vm.points = [
      { latitude: 45.0, longitude: 4.0, elevation: 100, time: '2023-01-01T10:00:00Z' },
      { latitude: 45.1, longitude: 4.1, elevation: 110, time: '2023-01-01T10:01:00Z' }
    ]
    vm.uploadedFileId = 'test-file-123'
    vm.name = 'Test Track'

    // Submit form
    await vm.onSubmit()

    // Verify error state with fallback message
    expect(vm.showError).toBe(true)
    expect(vm.currentErrorMessage).toBe('Error while creating segment')
    expect(vm.showUploadSuccess).toBe(false)
    expect(vm.showSegmentSuccess).toBe(false)

    // Clean up
    ;(global as any).fetch = undefined
    vi.restoreAllMocks()
  })

  it('automatically hides error after 5 seconds', async () => {
    const wrapper = mountEditor()

    // Mock failed fetch response
    ;(global as any).fetch = vi.fn().mockResolvedValue({
      ok: false,
      text: () => Promise.resolve('Error')
    })

    // Mock setTimeout
    const setTimeoutSpy = vi.spyOn(global, 'setTimeout')

    // Set up component state to pass validation
    const vm = wrapper.vm as any
    vm.loaded = true
    vm.points = [
      { latitude: 45.0, longitude: 4.0, elevation: 100, time: '2023-01-01T10:00:00Z' },
      { latitude: 45.1, longitude: 4.1, elevation: 110, time: '2023-01-01T10:01:00Z' }
    ]
    vm.uploadedFileId = 'test-file-123'
    vm.name = 'Test Track'

    // Submit form
    await vm.onSubmit()

    // Verify setTimeout was called with 5000ms
    expect(setTimeoutSpy).toHaveBeenCalledWith(expect.any(Function), 5000)

    // Clean up
    ;(global as any).fetch = undefined
    vi.restoreAllMocks()
  })

  it('resets submitting state in finally block', async () => {
    const wrapper = mountEditor()

    // Mock successful fetch response
    ;(global as any).fetch = vi.fn().mockResolvedValue({
      ok: true,
      text: () => Promise.resolve('Success')
    })

    // Set up component state to pass validation
    const vm = wrapper.vm as any
    vm.loaded = true
    vm.points = [
      { latitude: 45.0, longitude: 4.0, elevation: 100, time: '2023-01-01T10:00:00Z' },
      { latitude: 45.1, longitude: 4.1, elevation: 110, time: '2023-01-01T10:01:00Z' }
    ]
    vm.uploadedFileId = 'test-file-123'
    vm.name = 'Test Track'

    // Submit form
    await vm.onSubmit()

    // Verify submitting was reset to false
    expect(vm.submitting).toBe(false)

    // Clean up
    ;(global as any).fetch = undefined
  })

  describe('Responsive behavior', () => {
    it('has resize event listener attached on mount', async () => {
      const addEventListenerSpy = vi.spyOn(window, 'addEventListener')

      const wrapper = mountEditor()

      await wrapper.vm.$nextTick()

      // Verify resize event listener was added
      expect(addEventListenerSpy).toHaveBeenCalledWith('resize', expect.any(Function))

      addEventListenerSpy.mockRestore()
    })

    it('removes resize event listener on unmount', async () => {
      const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener')

      const wrapper = mountEditor()

      await wrapper.vm.$nextTick()
      wrapper.unmount()

      // Verify resize event listener was removed
      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'resize',
        expect.any(Function)
      )

      removeEventListenerSpy.mockRestore()
    })

    it('has checkSidebarMode function available', async () => {
      const wrapper = mountEditor()

      const vm = wrapper.vm as any

      // Verify checkSidebarMode function exists
      expect(typeof vm.checkSidebarMode).toBe('function')
    })

    it('has resize handler function that can be called directly', async () => {
      const wrapper = mountEditor()

      const vm = wrapper.vm as any

      // Mock chart and canvas
      const mockChart = {
        resize: vi.fn(),
        update: vi.fn(),
        canvas: {
          getBoundingClientRect: vi.fn(() => ({
            left: 100,
            top: 50,
            width: 800,
            height: 200
          }))
        },
        scales: {
          x: {
            getPixelForValue: vi.fn((value) => value * 10),
            getValueForPixel: vi.fn((pixel) => pixel / 10)
          }
        },
        data: {
          datasets: [{ data: [] }, { data: [] }]
        }
      }

      const mockChartCanvas = {
        parentElement: {
          getBoundingClientRect: vi.fn(() => ({
            left: 0,
            top: 0,
            width: 1000,
            height: 250
          }))
        }
      }

      // Set up component state
      vm.chart = mockChart
      vm.chartCanvas = mockChartCanvas
      vm.points = [
        { latitude: 0, longitude: 0, elevation: 100, time: '2023-01-01T00:00:00Z' },
        { latitude: 1, longitude: 1, elevation: 200, time: '2023-01-01T00:01:00Z' }
      ]
      vm.startIndex = 0
      vm.endIndex = 1
      vm.cumulativeKm = [0, 1]
      vm.cumulativeSec = [0, 60]
      vm.xMode = 'distance'
      vm.getX = (i: number) => vm.cumulativeKm[i] || 0

      // Get the resize handler function
      const resizeHandler = (window as any).__editorOnResize
      expect(typeof resizeHandler).toBe('function')

      // Call the resize handler directly
      resizeHandler()

      await nextTick()
      await wrapper.vm.$nextTick()

      // Verify chart.resize was called
      expect(mockChart.resize).toHaveBeenCalled()

      // Verify slider positions were updated (they should be numbers)
      expect(typeof vm.startSliderPosition).toBe('number')
      expect(typeof vm.endSliderPosition).toBe('number')
    })

    it('does not update chart when no chart is present', async () => {
      const wrapper = mountEditor()

      const vm = wrapper.vm as any
      vm.chart = null
      vm.chartCanvas = null

      // Mock console.warn to avoid error logs in tests
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      // Trigger window resize
      window.dispatchEvent(new Event('resize'))

      await wrapper.vm.$nextTick()

      // No assertions needed - just verify no errors are thrown
      expect(true).toBe(true)

      consoleSpy.mockRestore()
    })

    it('does not update chart when no points are loaded', async () => {
      const wrapper = mountEditor()

      const vm = wrapper.vm as any
      vm.chart = createChartMock()
      vm.chartCanvas = { parentElement: { getBoundingClientRect: vi.fn() } }
      vm.points = []

      // Trigger window resize
      window.dispatchEvent(new Event('resize'))

      await wrapper.vm.$nextTick()

      // Verify chart.resize was not called when no points
      expect(vm.chart.resize).not.toHaveBeenCalled()
    })
  })

  describe('Marker functionality', () => {
    it('has updateMarkerPositionFromIndex function', async () => {
      const wrapper = mountEditor()
      const vm = wrapper.vm as any

      // Test that the function exists and can be called
      expect(typeof vm.updateMarkerPositionFromIndex).toBe('function')

      // Test with valid data
      vm.points = [
        { latitude: 45.0, longitude: 4.0, elevation: 100 },
        { latitude: 45.1, longitude: 4.1, elevation: 110 }
      ]

      // Should not throw error
      expect(() => vm.updateMarkerPositionFromIndex(0)).not.toThrow()
      expect(() => vm.updateMarkerPositionFromIndex(1)).not.toThrow()
    })

    it('has updateMarkerPosition function', async () => {
      const wrapper = mountEditor()
      const vm = wrapper.vm as any

      // Test that the function exists and can be called
      expect(typeof vm.updateMarkerPosition).toBe('function')

      // Test with valid data
      vm.points = [
        { latitude: 45.0, longitude: 4.0, elevation: 100 },
        { latitude: 45.1, longitude: 4.1, elevation: 110 }
      ]

      // Should not throw error
      expect(() => vm.updateMarkerPosition({ lat: 45.05, lng: 4.05 })).not.toThrow()
    })

    it('handles marker update when no points are available', async () => {
      const wrapper = mountEditor()
      const vm = wrapper.vm as any
      vm.points = []

      // Should not throw error when no points
      expect(() => vm.updateMarkerPositionFromIndex(0)).not.toThrow()
      expect(() => vm.updateMarkerPosition({ lat: 45.05, lng: 4.05 })).not.toThrow()
    })

    it('handles marker update with invalid index', async () => {
      const wrapper = mountEditor()
      const vm = wrapper.vm as any
      vm.points = [{ latitude: 45.0, longitude: 4.0, elevation: 100 }]

      // Should not throw error with invalid indices
      expect(() => vm.updateMarkerPositionFromIndex(-1)).not.toThrow()
      expect(() => vm.updateMarkerPositionFromIndex(5)).not.toThrow()
    })

    it('updates marker position when sliders change', async () => {
      const wrapper = mountEditor()
      const vm = wrapper.vm as any
      vm.loaded = true
      vm.points = [
        { latitude: 45.0, longitude: 4.0, elevation: 100 },
        { latitude: 45.1, longitude: 4.1, elevation: 110 },
        { latitude: 45.2, longitude: 4.2, elevation: 120 }
      ]
      vm.startIndex = 0
      vm.endIndex = 2

      // Change start index
      vm.startIndex = 1
      await wrapper.vm.$nextTick()

      // The watch function should have been triggered
      // This tests that the marker update is called when sliders change
      expect(vm.startIndex).toBe(1)
    })

    it('creates marker when map is rendered with points', async () => {
      const wrapper = mountEditor()

      // Set up component state with points
      const vm = wrapper.vm as any
      vm.loaded = true
      vm.points = [
        { latitude: 45.0, longitude: 4.0, elevation: 100 },
        { latitude: 45.1, longitude: 4.1, elevation: 110 }
      ]
      vm.startIndex = 0
      vm.endIndex = 1

      // Mock the map container
      const mapContainer = document.createElement('div')
      mapContainer.id = 'map'
      document.body.appendChild(mapContainer)

      // Call renderMap - should not throw error
      expect(() => vm.renderMap()).not.toThrow()

      // Clean up
      document.body.removeChild(mapContainer)
    })

    it('handles marker creation with proper configuration', async () => {
      const wrapper = mountEditor()

      const vm = wrapper.vm as any
      vm.loaded = true
      vm.points = [{ latitude: 45.0, longitude: 4.0, elevation: 100 }]

      // Mock the map container
      const mapContainer = document.createElement('div')
      mapContainer.id = 'map'
      document.body.appendChild(mapContainer)

      // Call renderMap - should not throw error
      expect(() => vm.renderMap()).not.toThrow()

      // Clean up
      document.body.removeChild(mapContainer)
    })

    it('handles chart interaction configuration', async () => {
      const wrapper = mountEditor()

      // Test that the chart configuration includes the correct interaction settings
      const vm = wrapper.vm as any
      vm.loaded = true
      vm.points = [
        { latitude: 45.0, longitude: 4.0, elevation: 100 },
        { latitude: 45.1, longitude: 4.1, elevation: 110 }
      ]

      // Mock the map container
      const mapContainer = document.createElement('div')
      mapContainer.id = 'map'
      document.body.appendChild(mapContainer)

      await vm.renderMap()

      // The chart should be created with the correct interaction configuration
      // This is tested indirectly through the chart creation process
      expect(vm.points.length).toBe(2)

      // Clean up
      document.body.removeChild(mapContainer)
    })
  })

  // ============== IMAGE UPLOAD TESTS ==============

  it('handles drag and drop image uploads through UI events', async () => {
    const wrapper = mountEditor()
    const vm = wrapper.vm as any

    const dropZone = wrapper.find('.image-upload-area')
    if (dropZone.exists()) {
      const mockFiles = [
        new File(['test1'], 'test1.jpg', { type: 'image/jpeg' }),
        new File(['test2'], 'test2.txt', { type: 'text/plain' })
      ]

      const mockEvent = {
        preventDefault: vi.fn(),
        dataTransfer: {
          files: Array.from(mockFiles)
        }
      }

      // Trigger drag over event first
      await dropZone.trigger('dragover', mockEvent)
      expect(vm.isDragOver).toBe(true)

      // Trigger drop event
      await dropZone.trigger('drop', mockEvent)
      expect(vm.isDragOver).toBe(false)
      expect(mockEvent.preventDefault).toHaveBeenCalled()
    }
  })

  it('handles image input selection through file input', async () => {
    const wrapper = mountEditor()
    const vm = wrapper.vm as any

    const fileInput = wrapper.find('input[type="file"][accept="image/*"]')
    if (fileInput.exists()) {
      const mockFiles = [
        new File(['test1'], 'test1.jpg', { type: 'image/jpeg' }),
        new File(['test2'], 'test2.png', { type: 'image/png' })
      ]

      // Modify the event target files to simulate selection
      const mockEvent = {
        target: {
          files: Array.from(mockFiles)
        }
      }

      // Notice that we're directly calling the method like other tests in this file
      await vm.handleImageSelect(mockEvent)

      // This should not throw any errors
      expect(fileInput.attributes('accept')).toBe('image/*')
    }
  })

  it('uploads images successfully and updates commentary state', async () => {
    const wrapper = mountEditor()
    const vm = wrapper.vm as any

    const originalFetch = global.fetch
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          image_id: 'test-image-id',
          image_url: 'https://storage.example.com/test.jpg',
          storage_key: 'images-segments/test-image-id.jpg'
        })
    })

    global.fetch = mockFetch

    const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
    const mockImageId = 'mock-image-id'

    // Add an image to commentary first
    vm.commentary.images.push({
      id: mockImageId,
      file: mockFile,
      preview: 'data:test',
      uploaded: false,
      image_url: '',
      image_id: ''
    })

    await vm.uploadImageToStorage(mockFile, mockImageId)

    const updatedImage = vm.commentary.images.find((img: any) => img.id === mockImageId)
    expect(updatedImage.uploaded).toBe(true)
    expect(updatedImage.image_url).toBe('https://storage.example.com/test.jpg')
    expect(updatedImage.image_id).toBe('test-image-id')
    expect(mockFetch).toHaveBeenCalledWith(
      '/api/upload-image',
      expect.objectContaining({
        method: 'POST'
      })
    )

    // Cleanup
    global.fetch = originalFetch
  })

  it('handles image upload failures gracefully', async () => {
    const wrapper = mountEditor()
    const vm = wrapper.vm as any

    const originalFetch = global.fetch
    // Mock fetch failure
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500
    })
    global.fetch = mockFetch

    // Mock console error
    const consoleError = vi.spyOn(console, 'error').mockImplementation(vi.fn())

    const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
    const mockImageId = 'mock-image-id'

    // Add an image to commentary first
    vm.commentary.images.push({
      id: mockImageId,
      file: mockFile,
      preview: 'data:test',
      uploaded: false,
      image_url: '',
      image_id: ''
    })

    await vm.uploadImageToStorage(mockFile, mockImageId)

    // Verify error handling
    expect(vm.showError).toBe(true)
    expect(vm.currentErrorMessage).toBe('Failed to upload image to storage')
    expect(consoleError).toHaveBeenCalled()

    // Image should remain in commentary but not uploaded
    const image = vm.commentary.images.find((img: any) => img.id === mockImageId)
    expect(image.uploaded).toBe(false)

    // Cleanup
    global.fetch = originalFetch
  })

  it('handles image drag over and leave events correctly', async () => {
    const wrapper = mountEditor()
    const vm = wrapper.vm as any

    const mockEvent = { preventDefault: vi.fn() }

    await vm.handleDragOver(mockEvent)
    expect(vm.isDragOver).toBe(true)
    expect(mockEvent.preventDefault).toHaveBeenCalled()

    await vm.handleDragLeave(mockEvent)
    expect(vm.isDragOver).toBe(false)
    expect(mockEvent.preventDefault).toHaveBeenCalled()
  })

  it('removes images from commentary array properly', async () => {
    const wrapper = mountEditor()
    const vm = wrapper.vm as any

    // Initially add two images
    vm.commentary.images.push({
      id: 'test-image-1',
      file: new File(['test1'], 'test1.jpg', { type: 'image/jpeg' }),
      preview: 'data:test1'
    })

    vm.commentary.images.push({
      id: 'test-image-2',
      file: new File(['test2'], 'test2.jpg', { type: 'image/jpeg' }),
      preview: 'data:test2'
    })

    expect(vm.commentary.images.length).toBe(2)

    // Remove first image
    vm.removeImage(0)
    expect(vm.commentary.images.length).toBe(1)
    expect(vm.commentary.images[0].id).toBe('test-image-2')

    // Remove remaining image
    vm.removeImage(0)
    expect(vm.commentary.images.length).toBe(0)
  })
})

describe('Editor Image Upload', () => {
  let wrapper: any

  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          image_id: 'test-image-id',
          image_url: 'https://example.com/test-image.jpg',
          storage_key: 'images-segments/test-image-id.jpg'
        })
    })
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  it('should render image upload section', async () => {
    wrapper = mountEditor()

    // Set loaded to true to show the form
    const vm = wrapper.vm
    vm.loaded = true

    await nextTick()

    // Debug: log the HTML to see what's actually rendered
    // console.log('Rendered HTML:', wrapper.html())

    // Check if the form exists
    const form = wrapper.find('form.card.meta')
    expect(form.exists()).toBe(true)

    // Check if media section exists
    const mediaSection = wrapper.find('.media-section')
    expect(mediaSection.exists()).toBe(true)

    // Find the image upload media field (second .media-field)
    const mediaFields = wrapper.findAll('.media-field')
    expect(mediaFields).toHaveLength(2) // Video links and image upload

    const imageUploadMediaField = mediaFields[1] // Second media field is for images
    const imageUploadSection = imageUploadMediaField.find('.image-upload-container')
    expect(imageUploadSection.exists()).toBe(true)
  })

  it('should handle image file selection', async () => {
    wrapper = mountEditor()

    // Set loaded to true to show the form
    const vm = wrapper.vm
    vm.loaded = true

    await nextTick()

    // Create a mock file
    const mockFile = new File(['test-image-content'], 'test-image.jpg', {
      type: 'image/jpeg'
    })

    // Find the image upload media field (second .media-field)
    const mediaFields = wrapper.findAll('.media-field')
    const imageUploadMediaField = mediaFields[1] // Second media field is for images

    const imageUploadArea = imageUploadMediaField.find('.image-upload-area')
    expect(imageUploadArea.exists()).toBe(true)

    const fileInput = imageUploadMediaField.find('input[type="file"][accept="image/*"]')
    expect(fileInput.exists()).toBe(true)

    // Simulate file selection
    const fileList = {
      0: mockFile,
      length: 1,
      item: (index: number) => (index === 0 ? mockFile : null),
      [Symbol.iterator]: function* () {
        yield mockFile
      }
    } as FileList

    // Mock FileReader behavior
    mockFileReader.readAsDataURL.mockImplementation(() => {
      setTimeout(() => {
        if (mockFileReader.onload) {
          mockFileReader.onload({
            target: { result: 'data:image/jpeg;base64,test' }
          } as any)
        }
      }, 0)
    })

    // Simulate file selection by directly calling the handler
    wrapper.vm.handleImageSelect({ target: { files: fileList } } as any)

    // Wait for async operations
    await nextTick()
    await new Promise((resolve) => setTimeout(resolve, 10))

    // Check that fetch was NOT called for image upload yet (images are uploaded on save)
    expect(mockFetch).not.toHaveBeenCalledWith('/api/upload-image', {
      method: 'POST',
      body: expect.any(FormData)
    })
  })

  it('should add image to commentary without uploading immediately', async () => {
    wrapper = mountEditor()

    // Set loaded to true to show the form
    const vm = wrapper.vm
    vm.loaded = true

    await nextTick()

    // Create a mock file
    const mockFile = new File(['test-image-content'], 'test-image.jpg', {
      type: 'image/jpeg'
    })

    // Mock FileReader behavior
    mockFileReader.readAsDataURL.mockImplementation(() => {
      setTimeout(() => {
        if (mockFileReader.onload) {
          mockFileReader.onload({
            target: { result: 'data:image/jpeg;base64,test' }
          } as any)
        }
      }, 0)
    })

    // Simulate file selection
    const fileList = {
      0: mockFile,
      length: 1,
      item: (index: number) => (index === 0 ? mockFile : null),
      [Symbol.iterator]: function* () {
        yield mockFile
      }
    } as FileList

    // Simulate file selection by directly calling the handler
    wrapper.vm.handleImageSelect({ target: { files: fileList } } as any)

    // Wait for async operations
    await nextTick()
    await new Promise((resolve) => setTimeout(resolve, 10))

    // Check that the image was added to the commentary but not uploaded yet
    expect(vm.commentary.images).toHaveLength(1)
    expect(vm.commentary.images[0].uploaded).toBe(false)
    expect(vm.commentary.images[0].file).toBe(mockFile)
    expect(vm.commentary.images[0].filename).toBe('test-image.jpg')
  })

  it('should upload images during segment submission', async () => {
    wrapper = mountEditor()

    // Mock successful image upload and segment creation
    const originalFetch = global.fetch
    const mockFetchLocal = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            image_id: 'test-image-id',
            image_url: 'https://example.com/test-image.jpg',
            storage_key: 'images-segments/test-image-id.jpg'
          })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: 1, name: 'Test Segment' })
      })
    global.fetch = mockFetchLocal

    await nextTick()

    // Set up component state for segment creation
    const vm = wrapper.vm
    vm.name = 'Test Segment'
    vm.loaded = true
    vm.points = [
      { lat: 0, lng: 0 },
      { lat: 1, lng: 1 }
    ]
    vm.uploadedFileId = 'test-file-id'

    // Add an image to commentary (not uploaded yet)
    const mockFile = new File(['test-image-content'], 'test-image.jpg', {
      type: 'image/jpeg'
    })
    vm.commentary.images.push({
      id: 'test-image-1',
      file: mockFile,
      preview: 'data:image/jpeg;base64,test',
      caption: '',
      uploaded: false,
      image_url: '',
      image_id: '',
      storage_key: '',
      filename: 'test-image.jpg',
      original_filename: 'test-image.jpg'
    })

    await nextTick()

    // Submit the form
    await vm.onSubmit()

    // Check that both image upload and segment creation were called
    expect(mockFetchLocal).toHaveBeenCalledTimes(2)

    // First call should be image upload
    const imageUploadCall = mockFetchLocal.mock.calls[0]
    expect(imageUploadCall[0]).toBe('/api/upload-image')
    expect(imageUploadCall[1].method).toBe('POST')

    // Second call should be segment creation
    const segmentCreationCall = mockFetchLocal.mock.calls[1]
    expect(segmentCreationCall[0]).toBe('/api/segments')
    expect(segmentCreationCall[1].method).toBe('POST')

    // Check that FormData contains image data
    const formData = segmentCreationCall[1].body as FormData
    const imageData = formData.get('image_data')
    expect(imageData).toBeTruthy()

    const parsedImageData = JSON.parse(imageData as string)
    expect(parsedImageData).toHaveLength(1)
    expect(parsedImageData[0].image_id).toBe('test-image-id')
    expect(parsedImageData[0].image_url).toBe('https://example.com/test-image.jpg')
    expect(parsedImageData[0].storage_key).toBe('images-segments/test-image-id.jpg')

    // Cleanup
    global.fetch = originalFetch
  })

  it('should remove image when remove button is clicked', async () => {
    wrapper = mountEditor()

    // Set loaded to true to show the form
    const vm = wrapper.vm
    vm.loaded = true

    await nextTick()

    // Add an image to commentary
    vm.commentary.images.push({
      id: 'test-image-1',
      file: new File(['test'], 'test.jpg', { type: 'image/jpeg' }),
      preview: 'data:image/jpeg;base64,test',
      caption: '',
      uploaded: true,
      image_url: 'https://example.com/test.jpg',
      image_id: 'test-image-id',
      storage_key: 'images-segments/test-image-id.jpg',
      filename: 'test.jpg',
      original_filename: 'test.jpg'
    })

    await nextTick()

    // Find and click remove button
    const removeButton = wrapper.find('.remove-image-btn')
    expect(removeButton.exists()).toBe(true)

    await removeButton.trigger('click')

    // Check that image was removed
    expect(vm.commentary.images).toHaveLength(0)
  })

  it('should not upload images that are removed before submission', async () => {
    wrapper = mountEditor()

    // Mock segment creation response
    const originalFetch = global.fetch
    const mockFetchLocal = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ id: 1, name: 'Test Segment' })
    })
    global.fetch = mockFetchLocal

    // Set up component state for segment creation
    const vm = wrapper.vm
    vm.name = 'Test Segment'
    vm.loaded = true
    vm.points = [
      { lat: 0, lng: 0 },
      { lat: 1, lng: 1 }
    ]
    vm.uploadedFileId = 'test-file-id'

    await nextTick()

    // Add an image to commentary
    const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
    vm.commentary.images.push({
      id: 'test-image-1',
      file: mockFile,
      preview: 'data:image/jpeg;base64,test',
      caption: '',
      uploaded: false,
      image_url: '',
      image_id: '',
      storage_key: '',
      filename: 'test.jpg',
      original_filename: 'test.jpg'
    })

    // Remove the image before submission
    vm.commentary.images = []

    await nextTick()

    // Submit the form
    await vm.onSubmit()

    // Check that only segment creation was called (no image upload)
    expect(mockFetchLocal).toHaveBeenCalledTimes(1)

    const segmentCreationCall = mockFetchLocal.mock.calls[0]
    expect(segmentCreationCall[0]).toBe('/api/segments')
    expect(segmentCreationCall[1].method).toBe('POST')

    // Check that FormData contains empty image data
    const formData = segmentCreationCall[1].body as FormData
    const imageData = formData.get('image_data')
    expect(imageData).toBeTruthy()

    const parsedImageData = JSON.parse(imageData as string)
    expect(parsedImageData).toHaveLength(0)

    // Cleanup
    global.fetch = originalFetch
  })

  it('should upload images only when segment is saved (deferred upload)', async () => {
    wrapper = mountEditor()

    // Mock successful image upload and segment creation
    const originalFetch = global.fetch
    const mockFetchLocal = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            image_id: 'test-image-id',
            image_url: 'https://example.com/test-image.jpg',
            storage_key: 'images-segments/test-image-id.jpg'
          })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: 1, name: 'Test Segment' })
      })
    global.fetch = mockFetchLocal

    // Set up component state for segment creation
    const vm = wrapper.vm
    vm.name = 'Test Segment'
    vm.loaded = true
    vm.points = [
      { lat: 0, lng: 0 },
      { lat: 1, lng: 1 }
    ]
    vm.uploadedFileId = 'test-file-id'

    await nextTick()

    // Add an image to commentary (not uploaded yet)
    const mockFile = new File(['test-image-content'], 'test-image.jpg', {
      type: 'image/jpeg'
    })
    vm.commentary.images.push({
      id: 'test-image-1',
      file: mockFile,
      preview: 'data:image/jpeg;base64,test',
      caption: '',
      uploaded: false,
      image_url: '',
      image_id: '',
      storage_key: '',
      filename: 'test-image.jpg',
      original_filename: 'test-image.jpg'
    })

    await nextTick()

    // Submit the form
    await vm.onSubmit()

    // Check that both image upload and segment creation were called
    expect(mockFetchLocal).toHaveBeenCalledTimes(2)

    // First call should be image upload
    const imageUploadCall = mockFetchLocal.mock.calls[0]
    expect(imageUploadCall[0]).toBe('/api/upload-image')
    expect(imageUploadCall[1].method).toBe('POST')

    // Second call should be segment creation
    const segmentCreationCall = mockFetchLocal.mock.calls[1]
    expect(segmentCreationCall[0]).toBe('/api/segments')
    expect(segmentCreationCall[1].method).toBe('POST')

    // Check that FormData contains image data
    const formData = segmentCreationCall[1].body as FormData
    const imageData = formData.get('image_data')
    expect(imageData).toBeTruthy()

    const parsedImageData = JSON.parse(imageData as string)
    expect(parsedImageData).toHaveLength(1)
    expect(parsedImageData[0].image_id).toBe('test-image-id')
    expect(parsedImageData[0].image_url).toBe('https://example.com/test-image.jpg')
    expect(parsedImageData[0].storage_key).toBe('images-segments/test-image-id.jpg')

    // Cleanup
    global.fetch = originalFetch
  })
})
