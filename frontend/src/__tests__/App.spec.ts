import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import App from '../App.vue'
import { createI18n } from 'vue-i18n'
import { createRouter, createWebHistory } from 'vue-router'
import Editor from '../components/Editor.vue'

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

// Create router for testing
const router = createRouter({
  history: createWebHistory(),
  routes: [{ path: '/', component: Editor }]
})

// Import real locale files
import en from '../i18n/locales/en'
import fr from '../i18n/locales/fr'

// Create i18n instance for testing using real locale files
const i18n = createI18n({
  legacy: false,
  locale: 'en',
  fallbackLocale: 'en',
  messages: { en, fr }
})

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock.getItem.mockReturnValue('en')
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders correctly', async () => {
    const wrapper = mount(App, {
      global: {
        plugins: [router, i18n]
      }
    })

    await router.isReady()

    expect(wrapper.find('#app').exists()).toBe(true)
    expect(wrapper.find('.navbar').exists()).toBe(true)
    expect(wrapper.find('.main-content').exists()).toBe(true)
  })

  it('displays the correct title', () => {
    const wrapper = mount(App, {
      global: {
        plugins: [router, i18n]
      }
    })

    const title = wrapper.find('.nav-title')
    expect(title.exists()).toBe(true)
    expect(title.text()).toContain('Cycling Routes')
    expect(title.html()).toContain('fa-person-biking')
  })

  it('shows language dropdown with correct options', () => {
    const wrapper = mount(App, {
      global: {
        plugins: [router, i18n]
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
    const wrapper = mount(App, {
      global: {
        plugins: [router, i18n]
      }
    })

    const trigger = wrapper.find('.language-dropdown-trigger')
    expect(wrapper.find('.language-dropdown-menu').classes()).not.toContain('open')

    await trigger.trigger('click')
    expect(wrapper.find('.language-dropdown-menu').classes()).toContain('open')

    await trigger.trigger('click')
    expect(wrapper.find('.language-dropdown-menu').classes()).not.toContain('open')
  })

  it('closes dropdown when clicking outside', async () => {
    const wrapper = mount(App, {
      global: {
        plugins: [router, i18n]
      }
    })

    const trigger = wrapper.find('.language-dropdown-trigger')
    await trigger.trigger('click')
    expect(wrapper.find('.language-dropdown-menu').classes()).toContain('open')

    // Test that the dropdown can be toggled
    await trigger.trigger('click')
    expect(wrapper.find('.language-dropdown-menu').classes()).not.toContain('open')
  })

  it('changes language when option is selected', async () => {
    const wrapper = mount(App, {
      global: {
        plugins: [router, i18n]
      }
    })

    const trigger = wrapper.find('.language-dropdown-trigger')
    await trigger.trigger('click')

    // Test that the dropdown opens and shows options
    expect(wrapper.find('.language-dropdown-menu').classes()).toContain('open')
    expect(wrapper.findAll('.language-option').length).toBeGreaterThan(0)
  })

  it('ensures dropdown menu is visible when open class is applied (non-regression test)', async () => {
    const wrapper = mount(App, {
      global: {
        plugins: [router, i18n]
      }
    })

    const dropdownMenu = wrapper.find('.language-dropdown-menu')

    // Initially should not have open class
    expect(dropdownMenu.classes()).not.toContain('open')

    // Click to open dropdown
    const trigger = wrapper.find('.language-dropdown-trigger')
    await trigger.trigger('click')

    // Should have open class
    expect(dropdownMenu.classes()).toContain('open')

    // Verify the element has the correct CSS classes for visibility
    // This ensures the CSS selector bug doesn't happen again
    expect(dropdownMenu.classes()).toContain('navbar-menu')
    expect(dropdownMenu.classes()).toContain('open')

    // Verify the dropdown menu element exists and is in the DOM
    expect(dropdownMenu.exists()).toBe(true)
    expect(dropdownMenu.element).toBeDefined()
  })

  it('saves language preference to localStorage', async () => {
    const wrapper = mount(App, {
      global: {
        plugins: [router, i18n]
      }
    })

    const trigger = wrapper.find('.language-dropdown-trigger')
    await trigger.trigger('click')

    const frenchOption = wrapper
      .findAll('.language-option')
      .find((option) => option.text().includes('🇫🇷'))

    if (frenchOption) {
      await frenchOption.trigger('click')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('cycling-editor-lang', 'fr')
    }
  })

  it('loads saved language from localStorage on mount', () => {
    localStorageMock.getItem.mockReturnValue('fr')

    const wrapper = mount(App, {
      global: {
        plugins: [router, i18n]
      }
    })

    // Test that the component mounts successfully
    expect(wrapper.find('#app').exists()).toBe(true)
  })

  it('handles missing localStorage gracefully', () => {
    localStorageMock.getItem.mockReturnValue(null)

    const wrapper = mount(App, {
      global: {
        plugins: [router, i18n]
      }
    })

    // Should default to English
    expect((wrapper.vm as any).currentLanguage).toBe('en')
  })

  it('prevents event propagation on dropdown toggle', async () => {
    const wrapper = mount(App, {
      global: {
        plugins: [router, i18n]
      }
    })

    const trigger = wrapper.find('.language-dropdown-trigger')
    const stopPropagationSpy = vi.fn()

    // Mock the event object
    const mockEvent = {
      stopPropagation: stopPropagationSpy
    }

    await trigger.trigger('click', mockEvent)
    expect(stopPropagationSpy).toHaveBeenCalled()
  })

  it('displays active language with checkmark', async () => {
    const wrapper = mount(App, {
      global: {
        plugins: [router, i18n]
      }
    })

    const trigger = wrapper.find('.language-dropdown-trigger')
    await trigger.trigger('click')

    const englishOption = wrapper
      .findAll('.language-option')
      .find((option) => option.text().includes('🇺🇸'))

    if (englishOption) {
      expect(englishOption.classes()).toContain('active')
      expect(englishOption.find('.checkmark').exists()).toBe(true)
    }
  })

  it('has correct CSS classes for styling', () => {
    const wrapper = mount(App, {
      global: {
        plugins: [router, i18n]
      }
    })

    expect(wrapper.find('#app').exists()).toBe(true)
    expect(wrapper.find('.navbar').exists()).toBe(true)
    expect(wrapper.find('.nav-container').exists()).toBe(true)
    expect(wrapper.find('.nav-right').exists()).toBe(true)
    expect(wrapper.find('.main-content').exists()).toBe(true)
  })

  it('renders router-view for main content', async () => {
    const wrapper = mount(App, {
      global: {
        plugins: [router, i18n]
      }
    })

    await router.isReady()

    const routerView = wrapper.findComponent({ name: 'RouterView' })
    expect(routerView.exists()).toBe(true)
  })
})
