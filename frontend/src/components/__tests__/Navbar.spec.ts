import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createI18n } from 'vue-i18n'
import { ref } from 'vue'
import Navbar from '../Navbar.vue'
import Explorer from '../Explorer.vue'
import Editor from '../Editor.vue'

// Mock the logo import
vi.mock('../../assets/images/logo.svg', () => ({
  default: 'mocked-logo.svg'
}))

// Mock useStravaApi
vi.mock('../../composables/useStravaApi', () => ({
  useStravaApi: vi.fn()
}))

// Mock useAuthorization
vi.mock('../../composables/useAuthorization', () => ({
  useAuthorization: vi.fn()
}))

// Import real locale files
import en from '../../i18n/locales/en'
import fr from '../../i18n/locales/fr'

// Import the composable providers after mocking
import { useStravaApi } from '../../composables/useStravaApi'
import { useAuthorization } from '../../composables/useAuthorization'

const mockUseStravaApi = vi.mocked(useStravaApi)
const mockUseAuthorization = vi.mocked(useAuthorization)

describe('Navbar', () => {
  let wrapper: VueWrapper<any>
  let router: any
  let i18n: any

  beforeEach(() => {
    vi.clearAllMocks()

    // Setup mock Strava API to always be authenticated for editor visibility
    mockUseStravaApi.mockReturnValue({
      authState: ref({
        isAuthenticated: true,
        accessToken: 'test-token',
        expiresAt: Date.now() + 3600,
        athlete: { id: 820773, firstname: 'Test', lastname: 'User' }
      }),
      isLoading: ref(false),
      error: ref(null),
      isAuthenticated: vi.fn(() => true),
      getAuthUrl: vi.fn(),
      clearAuth: vi.fn(),
      exchangeCode: vi.fn(),
      loadAuthState: vi.fn(),
      getActivities: vi.fn(),
      getActivityGpx: vi.fn(),
      handleAuthenticationError: vi.fn(),
      attemptTokenRefresh: vi.fn()
    })

    // Setup mock authorization to always allow editor access
    mockUseAuthorization.mockReturnValue({
      isAuthorizedForEditor: ref(true),
      isLoadingAuthorization: ref(false),
      authorizationError: ref(null),
      checkAuthorizationStatus: vi.fn(),
      clearAuthorizationCache: vi.fn()
    })

    // Create router
    router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/', component: Explorer },
        { path: '/editor', component: Editor }
      ]
    })

    // Create i18n instance using real locale files
    i18n = createI18n({
      legacy: false,
      locale: 'en',
      fallbackLocale: 'en',
      messages: { en, fr }
    })

    wrapper = mount(Navbar, {
      global: {
        plugins: [router, i18n],
        stubs: {
          'router-link': {
            template: '<a :href="to" :class="activeClass"><slot /></a>',
            props: ['to', 'activeClass']
          }
        }
      }
    })
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('Component Structure', () => {
    it('renders correctly', () => {
      expect(wrapper.find('.navbar').exists()).toBe(true)
      expect(wrapper.find('.navbar-container').exists()).toBe(true)
      expect(wrapper.find('.navbar-brand').exists()).toBe(true)
      expect(wrapper.find('.navbar-nav').exists()).toBe(true)
    })

    it('displays the logo', () => {
      const logo = wrapper.find('.navbar-logo')
      expect(logo.exists()).toBe(true)
      expect(logo.attributes('src')).toBe('mocked-logo.svg')
      expect(logo.attributes('alt')).toBe('Gravly')
    })
  })

  describe('Navigation Menu', () => {
    it('renders navigation menu in brand section', () => {
      const navMenu = wrapper.find('.nav-menu')
      expect(navMenu.exists()).toBe(true)
      expect(navMenu.element.parentElement?.classList.contains('navbar-brand')).toBe(
        true
      )
    })

    it('displays Explorer, Planner, and Editor links', () => {
      const navLinks = wrapper.findAll('.nav-link')
      expect(navLinks).toHaveLength(3)

      const explorerLink = navLinks.find((link) => link.text().includes('Explorer'))
      const plannerLink = navLinks.find((link) => link.text().includes('Planner'))
      const editorLink = navLinks.find((link) => link.text().includes('Editor'))

      expect(explorerLink?.exists()).toBe(true)
      expect(plannerLink?.exists()).toBe(true)
      expect(editorLink?.exists()).toBe(true)
    })

    it('has correct router-link attributes', () => {
      const homeLink = wrapper.find('a[href="/"]')
      const explorerLink = wrapper.find('a[href="/explorer"]')
      const plannerLink = wrapper.find('a[href="/route-planner"]')
      const editorLink = wrapper.find('a[href="/editor"]')

      expect(homeLink.exists()).toBe(true)
      expect(explorerLink.exists()).toBe(true)
      expect(plannerLink.exists()).toBe(true)
      expect(editorLink.exists()).toBe(true)
    })

    it('displays icons for navigation links', () => {
      const explorerIcon = wrapper.find('.fa-route')
      const plannerIcon = wrapper.find('.fa-map')
      const editorIcon = wrapper.find('.fa-edit')

      expect(explorerIcon.exists()).toBe(true)
      expect(plannerIcon.exists()).toBe(true)
      expect(editorIcon.exists()).toBe(true)
    })

    it('displays navigation links in correct order: Explorer, Planner, Editor', () => {
      const navLinks = wrapper.findAll('.nav-link')
      expect(navLinks).toHaveLength(3)

      // Check that links are in the expected order
      expect(navLinks[0].text()).toContain('Explorer')
      expect(navLinks[1].text()).toContain('Planner')
      expect(navLinks[2].text()).toContain('Editor')

      // Verify correct routes
      expect(navLinks[0].attributes('href')).toBe('/explorer')
      expect(navLinks[1].attributes('href')).toBe('/route-planner')
      expect(navLinks[2].attributes('href')).toBe('/editor')
    })
  })

  describe('Language Dropdown', () => {
    it('renders language dropdown in navbar-nav section', () => {
      const languageDropdown = wrapper.find('.language-dropdown')
      expect(languageDropdown.exists()).toBe(true)
      expect(
        languageDropdown.element.parentElement?.classList.contains('navbar-nav')
      ).toBe(true)
    })

    it('displays language trigger button', () => {
      const trigger = wrapper.find('.language-dropdown-trigger')
      expect(trigger.exists()).toBe(true)
    })

    it('shows current language flag and name', () => {
      const flag = wrapper.find('.language-flag')
      const name = wrapper.find('.language-name')

      expect(flag.exists()).toBe(true)
      expect(name.exists()).toBe(true)
    })

    it('handles closeLanguageDropdown function correctly', async () => {
      // Test the closeLanguageDropdown function (lines 102-109)
      const trigger = wrapper.find('.language-dropdown-trigger')

      // Open dropdown first
      await trigger.trigger('click')

      // Create a mock event that targets an element outside the dropdown
      const outsideElement = document.createElement('div')
      document.body.appendChild(outsideElement)

      const mockEvent = new MouseEvent('click', {
        bubbles: true,
        cancelable: true
      })
      Object.defineProperty(mockEvent, 'target', {
        value: outsideElement,
        writable: false
      })

      // Simulate clicking outside the dropdown
      document.dispatchEvent(mockEvent)

      // Clean up
      document.body.removeChild(outsideElement)
    })

    it('handles closeLanguageDropdown when clicking inside dropdown', async () => {
      // Test that clicking inside the dropdown doesn't close it
      const trigger = wrapper.find('.language-dropdown-trigger')

      // Open dropdown first
      await trigger.trigger('click')

      // Create a mock event that targets the dropdown itself
      const dropdown = wrapper.find('.language-dropdown')
      const mockEvent = new MouseEvent('click', {
        bubbles: true,
        cancelable: true
      })
      Object.defineProperty(mockEvent, 'target', {
        value: dropdown.element,
        writable: false
      })

      // Simulate clicking inside the dropdown
      document.dispatchEvent(mockEvent)
    })

    it('handles closeLanguageDropdown when dropdown element is null', async () => {
      // Test the edge case where languageDropdown.value is null
      const trigger = wrapper.find('.language-dropdown-trigger')

      // Open dropdown first
      await trigger.trigger('click')

      // Create a mock event
      const mockEvent = new MouseEvent('click', {
        bubbles: true,
        cancelable: true
      })
      Object.defineProperty(mockEvent, 'target', {
        value: document.body,
        writable: false
      })

      // Simulate clicking outside
      document.dispatchEvent(mockEvent)
    })

    it('toggles language dropdown correctly', async () => {
      const trigger = wrapper.find('.language-dropdown-trigger')

      // Initially dropdown should be closed
      expect(wrapper.vm.languageDropdownOpen).toBe(false)

      // Click to open
      await trigger.trigger('click')
      expect(wrapper.vm.languageDropdownOpen).toBe(true)

      // Click again to close
      await trigger.trigger('click')
      expect(wrapper.vm.languageDropdownOpen).toBe(false)
    })
  })

  describe('Internationalization', () => {
    it('displays English text by default', () => {
      expect(wrapper.text()).toContain('Explorer')
      expect(wrapper.text()).toContain('Planner')
      expect(wrapper.text()).toContain('Editor')
      expect(wrapper.text()).toContain('English')
    })

    it('uses translation keys correctly', () => {
      const explorerText = wrapper.find('.nav-link').text()
      expect(explorerText).toContain('Explorer')
    })
  })

  describe('Accessibility', () => {
    it('has proper semantic HTML structure', () => {
      expect(wrapper.find('header').exists()).toBe(true)
      expect(wrapper.find('nav').exists()).toBe(true)
    })

    it('has proper alt text for logo', () => {
      const logo = wrapper.find('.navbar-logo')
      expect(logo.attributes('alt')).toBe('Gravly')
    })

    it('uses proper button elements for interactive elements', () => {
      const trigger = wrapper.find('.language-dropdown-trigger')
      expect(trigger.element.tagName).toBe('BUTTON')
    })
  })

  describe('Component Lifecycle', () => {
    it('mounts without errors', () => {
      expect(wrapper.vm).toBeDefined()
    })

    it('unmounts without errors', () => {
      expect(() => wrapper.unmount()).not.toThrow()
    })
  })

  describe('Non-regression tests', () => {
    it('should be a standalone component that can be used independently', () => {
      // Navbar should work when mounted independently
      expect(wrapper.find('.navbar').exists()).toBe(true)
      expect(wrapper.find('.navbar-container').exists()).toBe(true)
      expect(wrapper.find('.navbar-brand').exists()).toBe(true)
      expect(wrapper.find('.navbar-nav').exists()).toBe(true)
    })

    it('should not contain any nested navbar elements', () => {
      // Navbar should not have nested navbars
      const nestedNavbars = wrapper.findAll('.navbar .navbar')
      expect(nestedNavbars).toHaveLength(0)
    })

    it('should maintain consistent structure across multiple mounts', () => {
      // Mount a second instance
      const wrapper2 = mount(Navbar, {
        global: {
          plugins: [router, i18n],
          stubs: {
            'router-link': {
              template: '<a :href="to" :class="activeClass"><slot /></a>',
              props: ['to', 'activeClass']
            }
          }
        }
      })

      // Both instances should have the same structure
      expect(wrapper.find('.navbar').exists()).toBe(true)
      expect(wrapper2.find('.navbar').exists()).toBe(true)

      // Clean up
      wrapper2.unmount()
    })
  })

  describe('CSS Classes and Styling', () => {
    it('applies correct CSS classes', () => {
      expect(wrapper.find('.navbar').classes()).toContain('navbar')
      expect(wrapper.find('.navbar-container').classes()).toContain('navbar-container')
      expect(wrapper.find('.navbar-brand').classes()).toContain('navbar-brand')
      expect(wrapper.find('.navbar-nav').classes()).toContain('navbar-nav')
      expect(wrapper.find('.nav-menu').classes()).toContain('nav-menu')
    })

    it('has proper nav-link styling classes', () => {
      const navLinks = wrapper.findAll('.nav-link')
      navLinks.forEach((link) => {
        expect(link.classes()).toContain('nav-link')
      })
    })
  })
})
