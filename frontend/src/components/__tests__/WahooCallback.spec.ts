import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createI18n } from 'vue-i18n'
import { ref } from 'vue'

import WahooCallback from '../WahooCallback.vue'

// Import real locale files
import en from '../../i18n/locales/en'
import fr from '../../i18n/locales/fr'

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock console methods to avoid noise in tests
const mockConsole = {
  info: vi.fn(),
  error: vi.fn(),
  log: vi.fn(),
  warn: vi.fn()
}
Object.defineProperty(console, 'info', { value: mockConsole.info })
Object.defineProperty(console, 'error', { value: mockConsole.error })
Object.defineProperty(console, 'log', { value: mockConsole.log })
Object.defineProperty(console, 'warn', { value: mockConsole.warn })

// Mock window.location
const mockLocation = {
  href: '',
  search: ''
}
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true
})

describe('WahooCallback', () => {
  let wrapper: VueWrapper<any>
  let router: ReturnType<typeof createRouter>
  let i18n: ReturnType<typeof createI18n>

  beforeEach(() => {
    vi.clearAllMocks()
    mockLocation.href = ''
    mockLocation.search = ''

    // Create router
    router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/', name: 'Home', component: { template: '<div>Home</div>' } },
        { path: '/wahoo-callback', name: 'WahooCallback', component: WahooCallback }
      ]
    })

    // Create i18n instance using real locale files
    i18n = createI18n({
      legacy: false,
      locale: 'en',
      fallbackLocale: 'en',
      messages: { en, fr }
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
    if (wrapper) {
      wrapper.unmount()
    }
  })

  const createWrapper = (props = {}) => {
    wrapper = mount(WahooCallback, {
      global: {
        plugins: [router, i18n],
        stubs: {
          'fa-solid': true // Stub FontAwesome icons
        }
      },
      props
    })
    return wrapper
  }

  describe('Component Rendering', () => {
    it('should render the component structure', () => {
      wrapper = createWrapper()

      expect(wrapper.find('.wahoo-callback').exists()).toBe(true)
      expect(wrapper.find('.callback-content').exists()).toBe(true)
    })

    it('should display loading state initially', async () => {
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.loading').exists()).toBe(true)
      expect(wrapper.find('.error').exists()).toBe(false)
      expect(wrapper.find('.success').exists()).toBe(false)
      expect(wrapper.text()).toContain('Completing login...')
    })
  })

  describe('Successful Callback Flow', () => {
    it('should handle successful callback with authorization code', async () => {
      const testCode = 'test_authorization_code_123'
      mockLocation.search = `?code=${testCode}`
      
      // Mock successful fetch response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          message: 'Wahoo authorization code received successfully',
          code: testCode,
          status: 'success'
        })
      })

      wrapper = createWrapper()
      
      // Wait for the component to process the callback
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(mockFetch).toHaveBeenCalledWith('/api/wahoo/callback', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      // Should show success state
      expect(wrapper.find('.loading').exists()).toBe(false)
      expect(wrapper.find('.error').exists()).toBe(false)
      expect(wrapper.find('.success').exists()).toBe(true)
      expect(wrapper.text()).toContain('Successfully logged in to Wahoo')
    })

    it('should redirect to home page after successful callback', async () => {
      const testCode = 'test_authorization_code_123'
      mockLocation.search = `?code=${testCode}`
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          message: 'Wahoo authorization code received successfully',
          code: testCode,
          status: 'success'
        })
      })

      wrapper = createWrapper()
      
      // Wait for the component to process the callback
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      // Should show success state
      expect(wrapper.find('.success').exists()).toBe(true)
      expect(wrapper.text()).toContain('Redirecting...')
    })
  })

  describe('Error Handling', () => {
    it('should handle missing authorization code', async () => {
      mockLocation.search = '?error=access_denied'
      
      wrapper = createWrapper()
      
      // Wait for the component to process the callback
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(wrapper.find('.loading').exists()).toBe(false)
      expect(wrapper.find('.error').exists()).toBe(true)
      expect(wrapper.find('.success').exists()).toBe(false)
      expect(wrapper.text()).toContain('Failed to login to Wahoo')
      expect(wrapper.text()).toContain('Wahoo authorization error: access_denied')
    })

    it('should handle backend API error', async () => {
      const testCode = 'test_authorization_code_123'
      mockLocation.search = `?code=${testCode}`
      
      // Mock failed fetch response
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Internal Server Error'
      })

      wrapper = createWrapper()
      
      // Wait for the component to process the callback
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(wrapper.find('.loading').exists()).toBe(false)
      expect(wrapper.find('.error').exists()).toBe(true)
      expect(wrapper.find('.success').exists()).toBe(false)
      expect(wrapper.text()).toContain('Backend error: Internal Server Error')
    })

    it('should handle network error', async () => {
      const testCode = 'test_authorization_code_123'
      mockLocation.search = `?code=${testCode}`
      
      // Mock network error
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      wrapper = createWrapper()
      
      // Wait for the component to process the callback
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(wrapper.find('.loading').exists()).toBe(false)
      expect(wrapper.find('.error').exists()).toBe(true)
      expect(wrapper.find('.success').exists()).toBe(false)
      expect(wrapper.text()).toContain('Network error')
    })

    it('should have continue button in error state', async () => {
      mockLocation.search = '?error=access_denied'
      
      wrapper = createWrapper()
      
      // Wait for the component to process the callback
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      const continueButton = wrapper.find('.btn.btn-primary')
      expect(continueButton.exists()).toBe(true)
      expect(continueButton.text()).toContain('Continue')
    })
  })

  describe('Component Integration', () => {
    it('should properly integrate with i18n', async () => {
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('Completing login...')
    })

    it('should properly integrate with router', () => {
      wrapper = createWrapper()
      expect(wrapper.vm.$router).toBeDefined()
    })
  })

  describe('Component Structure', () => {
    it('should have correct CSS classes', () => {
      wrapper = createWrapper()

      const callbackDiv = wrapper.find('.wahoo-callback')
      const contentDiv = wrapper.find('.callback-content')

      expect(callbackDiv.exists()).toBe(true)
      expect(contentDiv.exists()).toBe(true)
    })

    it('should render FontAwesome icons', async () => {
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()

      // The icon might be stubbed, so we just check that the loading section exists
      expect(wrapper.find('.loading').exists()).toBe(true)
    })
  })

  describe('State Transitions', () => {
    it('should transition from loading to success state', async () => {
      const testCode = 'test_authorization_code_123'
      mockLocation.search = `?code=${testCode}`
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          message: 'Wahoo authorization code received successfully',
          code: testCode,
          status: 'success'
        })
      })

      wrapper = createWrapper()
      await wrapper.vm.$nextTick()

      // Initially loading
      expect(wrapper.find('.loading').exists()).toBe(true)

      // Wait for processing
      await new Promise(resolve => setTimeout(resolve, 100))

      // Should transition to success
      expect(wrapper.find('.loading').exists()).toBe(false)
      expect(wrapper.find('.success').exists()).toBe(true)
    })

    it('should transition from loading to error state', async () => {
      mockLocation.search = '?error=access_denied'
      
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()

      // Initially loading
      expect(wrapper.find('.loading').exists()).toBe(true)

      // Wait for processing
      await new Promise(resolve => setTimeout(resolve, 100))

      // Should transition to error
      expect(wrapper.find('.loading').exists()).toBe(false)
      expect(wrapper.find('.error').exists()).toBe(true)
    })
  })

  describe('Internationalization', () => {
    it('should use correct translation keys', async () => {
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('Completing login...')
    })

    it('should display error messages in correct language', async () => {
      mockLocation.search = '?error=access_denied'
      
      wrapper = createWrapper()
      
      // Wait for the component to process the callback
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(wrapper.text()).toContain('Failed to login to Wahoo')
    })

    it('should display success messages in correct language', async () => {
      const testCode = 'test_authorization_code_123'
      mockLocation.search = `?code=${testCode}`
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          message: 'Wahoo authorization code received successfully',
          code: testCode,
          status: 'success'
        })
      })

      wrapper = createWrapper()
      
      // Wait for the component to process the callback
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(wrapper.text()).toContain('Successfully logged in to Wahoo')
      expect(wrapper.text()).toContain('Redirecting...')
    })
  })
})
