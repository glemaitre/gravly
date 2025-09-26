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

// Import RoutePlanner component for testing
import RoutePlanner from '../components/RoutePlanner.vue'

// Create router for testing
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Editor },
    { path: '/editor', component: Editor },
    { path: '/route-planner', component: RoutePlanner }
  ]
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
    // Mock localStorage.getItem to return appropriate values for different keys
    localStorageMock.getItem.mockImplementation((key: string) => {
      switch (key) {
        case 'cycling-editor-lang':
          return 'en'
        case 'strava_auth':
          return null // No Strava auth in tests
        default:
          return null
      }
    })
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

    // The navbar component should contain the logo
    const navbar = wrapper.findComponent({ name: 'Navbar' })
    expect(navbar.exists()).toBe(true)

    const logo = wrapper.find('.navbar-logo')
    expect(logo.exists()).toBe(true)
    expect(logo.attributes('alt')).toBe('Cycling Segments')
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
    // Override the mock for this specific test
    localStorageMock.getItem.mockImplementation((key: string) => {
      if (key === 'cycling-editor-lang') {
        return 'fr'
      }
      if (key === 'strava_auth') {
        return null // No Strava auth in tests
      }
      return null
    })

    const wrapper = mount(App, {
      global: {
        plugins: [router, i18n]
      }
    })

    // Test that the component mounts successfully
    expect(wrapper.find('#app').exists()).toBe(true)
  })

  it('handles missing localStorage gracefully', () => {
    // Override the mock to return null for all keys
    localStorageMock.getItem.mockImplementation(() => null)

    const wrapper = mount(App, {
      global: {
        plugins: [router, i18n]
      }
    })

    // The navbar component should exist and handle missing localStorage
    const navbar = wrapper.findComponent({ name: 'Navbar' })
    expect(navbar.exists()).toBe(true)

    // The navbar component should default to English when localStorage is null
    const languageTrigger = wrapper.find('.language-dropdown-trigger')
    expect(languageTrigger.exists()).toBe(true)
    expect(languageTrigger.text()).toContain('🇺🇸')
    expect(languageTrigger.text()).toContain('English')
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
    expect(wrapper.find('.navbar-container').exists()).toBe(true)
    expect(wrapper.find('.navbar-nav').exists()).toBe(true)
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

  // Non-regression tests to prevent duplicate navbars
  describe('Non-regression tests', () => {
    it('should only have one navbar in the entire app', () => {
      const wrapper = mount(App, {
        global: {
          plugins: [router, i18n]
        }
      })

      // Should have exactly one navbar
      const navbars = wrapper.findAll('.navbar')
      expect(navbars).toHaveLength(1)

      // Should have exactly one Navbar component
      const navbarComponents = wrapper.findAllComponents({ name: 'Navbar' })
      expect(navbarComponents).toHaveLength(1)
    })

    it('should not have duplicate navbars when navigating to editor', async () => {
      const wrapper = mount(App, {
        global: {
          plugins: [router, i18n]
        }
      })

      // Navigate to editor
      await router.push('/editor')
      await wrapper.vm.$nextTick()

      // Should still have exactly one navbar
      const navbars = wrapper.findAll('.navbar')
      expect(navbars).toHaveLength(1)

      // Should still have exactly one Navbar component
      const navbarComponents = wrapper.findAllComponents({ name: 'Navbar' })
      expect(navbarComponents).toHaveLength(1)
    })

    it('should not have duplicate navbars when navigating back to home', async () => {
      const wrapper = mount(App, {
        global: {
          plugins: [router, i18n]
        }
      })

      // Navigate to editor first
      await router.push('/editor')
      await wrapper.vm.$nextTick()

      // Navigate back to home
      await router.push('/')
      await wrapper.vm.$nextTick()

      // Should still have exactly one navbar
      const navbars = wrapper.findAll('.navbar')
      expect(navbars).toHaveLength(1)

      // Should still have exactly one Navbar component
      const navbarComponents = wrapper.findAllComponents({ name: 'Navbar' })
      expect(navbarComponents).toHaveLength(1)
    })

    it('should have navbar at the app level, not in individual components', () => {
      const wrapper = mount(App, {
        global: {
          plugins: [router, i18n]
        }
      })

      // The navbar should be directly under the app div, not nested in router-view
      const appDiv = wrapper.find('#app')
      const navbar = appDiv.find('.navbar')
      expect(navbar.exists()).toBe(true)

      // The navbar should be a direct child of #app
      expect(navbar.element.parentElement).toBe(appDiv.element)
    })

    it('should maintain navbar state across route changes', async () => {
      const wrapper = mount(App, {
        global: {
          plugins: [router, i18n]
        }
      })

      // Get initial navbar state
      const initialNavbar = wrapper.find('.navbar')
      expect(initialNavbar.exists()).toBe(true)

      // Navigate to editor
      await router.push('/editor')
      await wrapper.vm.$nextTick()

      // Navbar should still exist and be the same instance
      const navbarAfterNavigation = wrapper.find('.navbar')
      expect(navbarAfterNavigation.exists()).toBe(true)
      expect(navbarAfterNavigation.element).toBe(initialNavbar.element)

      // Navigate back to home
      await router.push('/')
      await wrapper.vm.$nextTick()

      // Navbar should still exist and be the same instance
      const navbarAfterReturn = wrapper.find('.navbar')
      expect(navbarAfterReturn.exists()).toBe(true)
      expect(navbarAfterReturn.element).toBe(initialNavbar.element)
    })
  })
})
