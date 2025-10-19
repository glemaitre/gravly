import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import Labs from '../Labs.vue'

// Import real locale files
import en from '../../i18n/locales/en'
import fr from '../../i18n/locales/fr'

// Create i18n instance for testing
const i18n = createI18n({
  legacy: false,
  locale: 'en',
  fallbackLocale: 'en',
  messages: { en, fr }
})

// Mock useAuthorization composable
const mockUseAuthorization = {
  isAuthorized: { value: true }
}

vi.mock('../../composables/useAuthorization', () => ({
  useAuthorization: () => mockUseAuthorization
}))

// Mock fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock window.location
const mockLocation = {
  href: ''
}
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true
})

describe('Labs', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockLocation.href = ''
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders the Labs page with correct title and description', () => {
    const wrapper = mount(Labs, {
      global: {
        plugins: [i18n]
      }
    })

    expect(wrapper.find('.labs-title').text()).toContain('Labs')
    expect(wrapper.find('.labs-description').text()).toContain('Experimental features')
  })

  it('renders Wahoo integration section', () => {
    const wrapper = mount(Labs, {
      global: {
        plugins: [i18n]
      }
    })

    expect(wrapper.find('.section-title').text()).toContain('Wahoo Integration')
    expect(wrapper.find('.section-description').text()).toContain(
      'Connect your Wahoo device'
    )
  })

  it('renders authorization button', () => {
    const wrapper = mount(Labs, {
      global: {
        plugins: [i18n]
      }
    })

    const authButton = wrapper.find('.wahoo-auth-btn')
    expect(authButton.exists()).toBe(true)
    expect(authButton.text()).toContain('Authorize with Wahoo')
  })

  it('handles successful Wahoo authorization', async () => {
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({
        status: 'success',
        authorization_url: 'https://api.wahooligan.com/oauth/authorize?test=123'
      })
    }
    mockFetch.mockResolvedValue(mockResponse)

    const wrapper = mount(Labs, {
      global: {
        plugins: [i18n]
      }
    })

    const authButton = wrapper.find('.wahoo-auth-btn')
    await authButton.trigger('click')

    expect(mockFetch).toHaveBeenCalledWith('/api/wahoo/authorization-url', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    expect(mockLocation.href).toBe(
      'https://api.wahooligan.com/oauth/authorize?test=123'
    )
  })

  it('handles Wahoo authorization error', async () => {
    const mockResponse = {
      ok: false,
      statusText: 'Internal Server Error'
    }
    mockFetch.mockResolvedValue(mockResponse)

    const wrapper = mount(Labs, {
      global: {
        plugins: [i18n]
      }
    })

    const authButton = wrapper.find('.wahoo-auth-btn')
    await authButton.trigger('click')

    await wrapper.vm.$nextTick()

    const errorStatus = wrapper.find('.status-indicator.error')
    expect(errorStatus.exists()).toBe(true)
    expect(errorStatus.text()).toContain('Failed to get authorization URL')
  })

  it('shows loading state during authorization', async () => {
    // Mock a slow response to test loading state
    const mockResponse = {
      ok: true,
      json: vi.fn().mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  status: 'success',
                  authorization_url:
                    'https://api.wahooligan.com/oauth/authorize?test=123'
                }),
              100
            )
          )
      )
    }
    mockFetch.mockResolvedValue(mockResponse)

    const wrapper = mount(Labs, {
      global: {
        plugins: [i18n]
      }
    })

    const authButton = wrapper.find('.wahoo-auth-btn')
    await authButton.trigger('click')

    // Check loading state immediately after click
    expect(authButton.text()).toContain('Authorizing...')
    expect(authButton.attributes('disabled')).toBeDefined()
  })

  it('redirects to home if not authorized for editor', () => {
    mockUseAuthorization.isAuthorized.value = false
    mockLocation.href = ''

    mount(Labs, {
      global: {
        plugins: [i18n]
      }
    })

    expect(mockLocation.href).toBe('/')
  })

  it('renders info section about Labs', () => {
    const wrapper = mount(Labs, {
      global: {
        plugins: [i18n]
      }
    })

    const infoSection = wrapper
      .findAll('.section-title')
      .find((title) => title.text().includes('About Labs'))
    expect(infoSection).toBeDefined()

    const infoList = wrapper.find('.info-list')
    expect(infoList.exists()).toBe(true)
    expect(infoList.findAll('li')).toHaveLength(3)
  })

  it('handles network error during authorization', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'))

    const wrapper = mount(Labs, {
      global: {
        plugins: [i18n]
      }
    })

    const authButton = wrapper.find('.wahoo-auth-btn')
    await authButton.trigger('click')

    await wrapper.vm.$nextTick()

    const errorStatus = wrapper.find('.status-indicator.error')
    expect(errorStatus.exists()).toBe(true)
    expect(errorStatus.text()).toContain('Network error')
  })

  it('handles invalid response from server', async () => {
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({
        status: 'error',
        message: 'Invalid response'
      })
    }
    mockFetch.mockResolvedValue(mockResponse)

    const wrapper = mount(Labs, {
      global: {
        plugins: [i18n]
      }
    })

    const authButton = wrapper.find('.wahoo-auth-btn')
    await authButton.trigger('click')

    await wrapper.vm.$nextTick()

    const errorStatus = wrapper.find('.status-indicator.error')
    expect(errorStatus.exists()).toBe(true)
    expect(errorStatus.text()).toContain('Invalid response from server')
  })
})
