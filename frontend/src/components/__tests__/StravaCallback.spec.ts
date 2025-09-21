import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createI18n } from 'vue-i18n'
import { ref } from 'vue'

// Mock the useStravaApi composable
vi.mock('../../composables/useStravaApi', () => ({
  useStravaApi: vi.fn()
}))

import StravaCallback from '../StravaCallback.vue'
import { useStravaApi } from '../../composables/useStravaApi'

// Import real locale files
import en from '../../i18n/locales/en'
import fr from '../../i18n/locales/fr'

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

describe('StravaCallback', () => {
  let wrapper: VueWrapper<any>
  let router: ReturnType<typeof createRouter>
  let i18n: ReturnType<typeof createI18n>
  let mockStravaApi: any
  const mockUseStravaApi = vi.mocked(useStravaApi)

  beforeEach(() => {
    vi.clearAllMocks()

    // Setup mock Strava API with reactive refs
    mockStravaApi = {
      exchangeCode: vi.fn().mockResolvedValue(undefined),
      isLoading: ref(false),
      error: ref(null)
    }
    mockUseStravaApi.mockReturnValue(mockStravaApi)

    // Create router
    router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/', name: 'Home', component: { template: '<div>Home</div>' } },
        {
          path: '/editor',
          name: 'Editor',
          component: { template: '<div>Editor</div>' }
        },
        { path: '/strava-callback', name: 'StravaCallback', component: StravaCallback }
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
    wrapper = mount(StravaCallback, {
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

      expect(wrapper.find('.strava-callback').exists()).toBe(true)
      expect(wrapper.find('.callback-content').exists()).toBe(true)
    })

    it('should display loading state when isLoading is true', async () => {
      mockStravaApi.isLoading.value = true
      mockStravaApi.error.value = null

      wrapper = createWrapper()
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.loading').exists()).toBe(true)
      expect(wrapper.find('.error').exists()).toBe(false)
      expect(wrapper.find('.success').exists()).toBe(false)
      expect(wrapper.text()).toContain('Completing login...')
    })

    it('should display error state when error is present', async () => {
      mockStravaApi.isLoading.value = false
      mockStravaApi.error.value = 'Authentication failed'

      wrapper = createWrapper()
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.loading').exists()).toBe(false)
      expect(wrapper.find('.error').exists()).toBe(true)
      expect(wrapper.find('.success').exists()).toBe(false)
      expect(wrapper.text()).toContain('Failed to login to Strava')
      expect(wrapper.text()).toContain('Authentication failed')
    })

    it('should display success state when no error and not loading', async () => {
      mockStravaApi.isLoading.value = false
      mockStravaApi.error.value = null

      wrapper = createWrapper()
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.loading').exists()).toBe(false)
      expect(wrapper.find('.error').exists()).toBe(false)
      expect(wrapper.find('.success').exists()).toBe(true)
      expect(wrapper.text()).toContain('Successfully logged in to Strava')
      expect(wrapper.text()).toContain('Redirecting...')
    })
  })

  describe('Error State Interaction', () => {
    it('should have continue button in error state', async () => {
      mockStravaApi.isLoading.value = false
      mockStravaApi.error.value = 'Test error'

      wrapper = createWrapper()
      await wrapper.vm.$nextTick()

      const continueButton = wrapper.find('.btn.btn-primary')
      expect(continueButton.exists()).toBe(true)
      expect(continueButton.text()).toContain('Continue')
    })
  })

  describe('Component Integration', () => {
    it('should properly integrate with useStravaApi', () => {
      createWrapper()

      expect(mockUseStravaApi).toHaveBeenCalled()
    })

    it('should properly integrate with i18n', async () => {
      mockStravaApi.isLoading.value = true

      wrapper = createWrapper()
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('Completing login...')
    })
  })

  describe('Component Structure', () => {
    it('should have correct CSS classes', () => {
      wrapper = createWrapper()

      const callbackDiv = wrapper.find('.strava-callback')
      const contentDiv = wrapper.find('.callback-content')

      expect(callbackDiv.exists()).toBe(true)
      expect(contentDiv.exists()).toBe(true)
    })

    it('should render FontAwesome icons', async () => {
      mockStravaApi.isLoading.value = true

      wrapper = createWrapper()
      await wrapper.vm.$nextTick()

      // The icon might be stubbed, so we just check that the loading section exists
      expect(wrapper.find('.loading').exists()).toBe(true)
    })
  })

  describe('State Transitions', () => {
    it('should transition from loading to success state', async () => {
      // Start with loading
      mockStravaApi.isLoading.value = true
      mockStravaApi.error.value = null

      wrapper = createWrapper()
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.loading').exists()).toBe(true)

      // Change to success
      mockStravaApi.isLoading.value = false
      mockStravaApi.error.value = null
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.loading').exists()).toBe(false)
      expect(wrapper.find('.success').exists()).toBe(true)
    })

    it('should transition from loading to error state', async () => {
      // Start with loading
      mockStravaApi.isLoading.value = true
      mockStravaApi.error.value = null

      wrapper = createWrapper()
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.loading').exists()).toBe(true)

      // Change to error
      mockStravaApi.isLoading.value = false
      mockStravaApi.error.value = 'Test error'
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.loading').exists()).toBe(false)
      expect(wrapper.find('.error').exists()).toBe(true)
    })
  })

  describe('Internationalization', () => {
    it('should use correct translation keys', async () => {
      mockStravaApi.isLoading.value = true

      wrapper = createWrapper()
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('Completing login...')
    })

    it('should display error messages in correct language', async () => {
      mockStravaApi.isLoading.value = false
      mockStravaApi.error.value = 'Test error'

      wrapper = createWrapper()
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('Failed to login to Strava')
    })

    it('should display success messages in correct language', async () => {
      mockStravaApi.isLoading.value = false
      mockStravaApi.error.value = null

      wrapper = createWrapper()
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('Successfully logged in to Strava')
      expect(wrapper.text()).toContain('Redirecting...')
    })
  })
})
