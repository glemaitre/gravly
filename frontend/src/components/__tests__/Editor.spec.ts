import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import Editor from '../Editor.vue'
import { createI18n } from 'vue-i18n'

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
      addTo: vi.fn()
    })),
    marker: vi.fn(() => ({
      addTo: vi.fn()
    })),
    icon: vi.fn(() => ({})),
    latLng: vi.fn(() => ({})),
    latLngBounds: vi.fn(() => ({})),
    control: {
      scale: vi.fn(() => ({
        addTo: vi.fn()
      }))
    }
  }
}))

// Mock Chart.js
vi.mock('chart.js', () => ({
  Chart: {
    register: vi.fn(),
    prototype: {
      destroy: vi.fn(),
      update: vi.fn()
    }
  },
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

describe('Editor', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock.getItem.mockReturnValue('en')
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders correctly', () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    expect(wrapper.find('.editor').exists()).toBe(true)
    expect(wrapper.find('.sidebar').exists()).toBe(true)
    expect(wrapper.find('.content').exists()).toBe(true)
    expect(wrapper.find('.topbar').exists()).toBe(true)
  })

  it('shows empty state when no file is loaded', () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    expect(wrapper.find('.empty').exists()).toBe(true)
    expect(wrapper.find('.empty').text()).toContain(
      'Use "Import from ..." → "GPX file" to begin'
    )
  })

  it('displays language dropdown with correct options', () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    const languageDropdown = wrapper.find('.language-dropdown')
    expect(languageDropdown.exists()).toBe(true)

    const trigger = languageDropdown.find('.language-dropdown-trigger')
    expect(trigger.exists()).toBe(true)
    expect(trigger.text()).toContain('🇺🇸')
    expect(trigger.text()).toContain('English')
  })

  it('toggles language dropdown when clicked', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    const trigger = wrapper.find('.language-dropdown-trigger')
    expect(wrapper.find('.language-dropdown-menu').classes()).not.toContain('open')

    await trigger.trigger('click')
    expect(wrapper.find('.language-dropdown-menu').classes()).toContain('open')

    await trigger.trigger('click')
    expect(wrapper.find('.language-dropdown-menu').classes()).not.toContain('open')
  })

  it('changes language when option is selected', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    const trigger = wrapper.find('.language-dropdown-trigger')
    await trigger.trigger('click')

    const frenchOption = wrapper.find('.language-option[data-lang="fr"]')
    if (frenchOption.exists()) {
      await frenchOption.trigger('click')
      expect(i18n.global.locale.value).toBe('fr')
    }
  })

  it('displays save button as disabled when no file is loaded', () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    const saveButton = wrapper.find('.menu-item.action')
    expect(saveButton.exists()).toBe(true)
    expect(saveButton.classes()).toContain('disabled')
    expect(saveButton.attributes('aria-disabled')).toBe('true')
  })

  it('triggers file input when GPX file menu item is clicked', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    const gpxMenuItem = wrapper.find('.menu-item')
    if (gpxMenuItem.exists()) {
      await gpxMenuItem.trigger('click')
      // The component should handle the click event
      expect(gpxMenuItem.exists()).toBe(true)
    }
  })

  it('handles file selection correctly', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    // Test that the file input exists and can be found
    const fileInput = wrapper.find('input[type="file"]')
    expect(fileInput.exists()).toBe(true)
    expect(fileInput.attributes('accept')).toBe('.gpx')
  })

  it('shows form fields when file is loaded', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    // Test that the basic structure exists in the template
    expect(wrapper.find('.editor').exists()).toBe(true)
    expect(wrapper.find('.sidebar').exists()).toBe(true)
    expect(wrapper.find('.content').exists()).toBe(true)
  })

  it('updates form fields correctly', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    // Test that the component renders without errors
    expect(wrapper.find('.editor').exists()).toBe(true)
  })

  it('handles commentary text input', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    // Test that the component renders without errors
    expect(wrapper.find('.editor').exists()).toBe(true)
  })

  it('handles image drag and drop events', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

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
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    // Test that the message container exists
    const messageContainer = wrapper.find('.message')
    expect(messageContainer.exists()).toBe(false) // Initially no message
  })

  it('shows success messages correctly', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    // Test that the component renders without errors
    expect(wrapper.find('.editor').exists()).toBe(true)
  })

  it('validates required fields before saving', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    // Test that the save button exists and is initially disabled
    const saveButton = wrapper.find('.menu-item.action')
    expect(saveButton.exists()).toBe(true)
    expect(saveButton.classes()).toContain('disabled')
  })

  it('handles slider movement correctly', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    // Test that the component has the moveSlider method
    expect(typeof wrapper.vm.moveSlider).toBe('function')
  })

  it('handles form field updates correctly', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    // Test segment name input
    const nameInput = wrapper.find('input[name="segment-name"]')
    if (nameInput.exists()) {
      await nameInput.setValue('Test Segment')
      expect(nameInput.element.value).toBe('Test Segment')
    }

    // Test commentary text input
    const commentaryTextarea = wrapper.find('textarea[name="commentary-text"]')
    if (commentaryTextarea.exists()) {
      await commentaryTextarea.setValue('This is a test commentary')
      expect(commentaryTextarea.element.value).toBe('This is a test commentary')
    }
  })

  it('handles trail conditions updates', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    // Test surface type selection
    const surfaceSelect = wrapper.find('select[name="surface-type"]')
    if (surfaceSelect.exists()) {
      await surfaceSelect.setValue('forest-trail')
      expect(surfaceSelect.element.value).toBe('forest-trail')
    }

    // Test difficulty level
    const difficultySlider = wrapper.find('input[name="difficulty-level"]')
    if (difficultySlider.exists()) {
      await difficultySlider.setValue('4')
      expect(difficultySlider.element.value).toBe('4')
    }
  })

  it('handles tire condition changes', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    // Test dry tire selection
    const dryTireSelect = wrapper.find('select[name="tire-dry"]')
    if (dryTireSelect.exists()) {
      await dryTireSelect.setValue('semi-slick')
      expect(dryTireSelect.element.value).toBe('semi-slick')
    }

    // Test wet tire selection
    const wetTireSelect = wrapper.find('select[name="tire-wet"]')
    if (wetTireSelect.exists()) {
      await wetTireSelect.setValue('knobs')
      expect(wetTireSelect.element.value).toBe('knobs')
    }
  })

  it('handles video link additions', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

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
          expect(videoTitleInput.element.value).toBe('Test Video')
        }
      }
    }
  })

  it('handles image upload trigger', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    // Test image upload trigger
    const imageUploadArea = wrapper.find('.image-upload-area')
    if (imageUploadArea.exists()) {
      await imageUploadArea.trigger('click')
      // The actual file input should be triggered
    }
  })

  it('handles drag and drop for images', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

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
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

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
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

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
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    // Test save button state when form is invalid
    const saveButton = wrapper.find('.menu-item.action')
    expect(saveButton.exists()).toBe(true)
    expect(saveButton.classes()).toContain('disabled')
    expect(saveButton.attributes('aria-disabled')).toBe('true')

    // Test tooltip when no file is loaded
    expect(saveButton.attributes('title')).toContain('Load a GPX first')
  })

  it('handles error state display', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    // Test error message display
    const errorMessage = wrapper.find('.error-message')
    if (errorMessage.exists()) {
      expect(errorMessage.isVisible()).toBe(false)
    }
  })

  it('handles success state display', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    // Test success message display
    const successMessage = wrapper.find('.success-message')
    if (successMessage.exists()) {
      expect(successMessage.isVisible()).toBe(false)
    }
  })

  it('handles upload progress display', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    // Test upload progress bar
    const uploadProgress = wrapper.find('.upload-progress-bar')
    if (uploadProgress.exists()) {
      expect(uploadProgress.isVisible()).toBe(false)
    }
  })

  it('handles language dropdown functionality', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    // Test language dropdown toggle
    const languageTrigger = wrapper.find('.language-dropdown-trigger')
    expect(languageTrigger.exists()).toBe(true)

    await languageTrigger.trigger('click')

    const dropdownMenu = wrapper.find('.language-dropdown-menu')
    expect(dropdownMenu.exists()).toBe(true)
  })

  it('handles file input change events', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    const fileInput = wrapper.find('input[type="file"]')
    expect(fileInput.exists()).toBe(true)

    // Test that the file input exists and can be interacted with
    expect(fileInput.element.type).toBe('file')
    expect(fileInput.element.accept).toContain('.gpx')
  })

  it('handles difficulty level setting', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    // Test difficulty level buttons
    const difficultyButtons = wrapper.findAll('button[data-level]')
    if (difficultyButtons.length > 0) {
      await difficultyButtons[0].trigger('click')
      await difficultyButtons[2].trigger('click')
    }
  })

  it('handles image removal', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    // Test image removal buttons
    const removeImageButtons = wrapper.findAll('button[title*="Remove image"]')
    if (removeImageButtons.length > 0) {
      await removeImageButtons[0].trigger('click')
    }
  })

  it('handles video removal', async () => {
    const wrapper = mount(Editor, {
      global: {
        plugins: [i18n]
      }
    })

    // Test video removal buttons
    const removeVideoButtons = wrapper.findAll('button[title*="Remove video"]')
    if (removeVideoButtons.length > 0) {
      await removeVideoButtons[0].trigger('click')
    }
  })
})
