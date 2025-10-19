import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createI18n } from 'vue-i18n'
import { ref } from 'vue'

import WahooCallback from '../WahooCallback.vue'

// Import real locale files
import en from '../../i18n/locales/en'
import fr from '../../i18n/locales/fr'

// Mock the useWahooApi composable
const mockExchangeCode = vi.fn()
const mockIsLoading = ref(false)
const mockError = ref<string | null>(null)

vi.mock('../../composables/useWahooApi', () => ({
  useWahooApi: () => ({
    exchangeCode: mockExchangeCode,
    isLoading: mockIsLoading,
    error: mockError
  })
}))

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock window.location
const mockLocation = {
  search: '',
  href: ''
}
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true
})

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn()
}
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
  writable: true
})

// Mock window.location.href assignment
Object.defineProperty(window.location, 'href', {
  writable: true,
  value: ''
})

describe('WahooCallback', () => {
  let wrapper: VueWrapper<any>
  let router: any
  let i18n: any

  const createWrapper = () => {
    return mount(WahooCallback, {
      global: {
        plugins: [router, i18n],
        stubs: {
          'font-awesome-icon': true
        }
      }
    })
  }

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks()
    mockExchangeCode.mockClear()
    mockIsLoading.value = false
    mockError.value = null
    mockLocation.search = ''
    mockLocation.href = ''
    mockLocalStorage.getItem.mockClear()
    mockLocalStorage.setItem.mockClear()
    mockLocalStorage.removeItem.mockClear()

    // Create router
    router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/', component: { template: '<div>Home</div>' } },
        { path: '/wahoo-callback', component: WahooCallback }
      ]
    })

    // Create i18n
    i18n = createI18n({
      legacy: false,
      locale: 'en',
      fallbackLocale: 'en',
      messages: {
        en,
        fr
      }
    })
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('Component Structure', () => {
    it('should render the callback component', () => {
      wrapper = createWrapper()
      expect(wrapper.find('.wahoo-callback').exists()).toBe(true)
      expect(wrapper.find('.callback-content').exists()).toBe(true)
    })
  })

  describe('Successful Callback Flow', () => {
    it('should handle successful callback with authorization code', async () => {
      const testCode = 'test_authorization_code_123'
      mockLocation.search = `?code=${testCode}`
      mockExchangeCode.mockResolvedValue(undefined)

      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      await new Promise((resolve) => setTimeout(resolve, 100))

      expect(mockExchangeCode).toHaveBeenCalledWith(testCode)
      expect(wrapper.find('.success').exists()).toBe(true)
      expect(wrapper.text()).toContain('Successfully logged in to Wahoo')
    })

    it('should redirect to home page after successful callback', async () => {
      const testCode = 'test_authorization_code_123'
      mockLocation.search = `?code=${testCode}`
      mockExchangeCode.mockResolvedValue(undefined)

      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      await new Promise((resolve) => setTimeout(resolve, 100))

      expect(wrapper.find('.success').exists()).toBe(true)
      expect(wrapper.text()).toContain('Redirecting...')
    })
  })

  describe('Error Handling', () => {
    it('should handle missing authorization code', async () => {
      mockLocation.search = '?error=access_denied'
      mockExchangeCode.mockRejectedValue(new Error('No authorization code received'))

      // Simulate error state from composable
      mockError.value = 'No authorization code received'

      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      await new Promise((resolve) => setTimeout(resolve, 100))

      expect(wrapper.find('.error').exists()).toBe(true)
      expect(wrapper.text()).toContain('Failed to login to Wahoo')
    })

    it('should have continue button in error state', async () => {
      mockLocation.search = '?error=access_denied'
      mockExchangeCode.mockRejectedValue(new Error('No authorization code received'))

      // Simulate error state from composable
      mockError.value = 'No authorization code received'

      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      await new Promise((resolve) => setTimeout(resolve, 100))

      const continueButton = wrapper.find('.btn.btn-primary')
      expect(continueButton.exists()).toBe(true)
      expect(continueButton.text()).toContain('Continue')
    })
  })

  describe('Internationalization', () => {
    it('should display success messages in correct language', async () => {
      const testCode = 'test_authorization_code_123'
      mockLocation.search = `?code=${testCode}`
      mockExchangeCode.mockResolvedValue(undefined)

      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      await new Promise((resolve) => setTimeout(resolve, 100))

      expect(wrapper.text()).toContain('Successfully logged in to Wahoo')
      expect(wrapper.text()).toContain('Redirecting...')
    })

    it('should display error messages in correct language', async () => {
      mockLocation.search = '?error=access_denied'
      mockExchangeCode.mockRejectedValue(new Error('No authorization code received'))

      // Simulate error state from composable
      mockError.value = 'No authorization code received'

      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      await new Promise((resolve) => setTimeout(resolve, 100))

      expect(wrapper.text()).toContain('Failed to login to Wahoo')
    })
  })
})
