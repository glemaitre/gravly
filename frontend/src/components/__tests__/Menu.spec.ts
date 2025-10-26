import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { ref } from 'vue'
import Menu from '../Menu.vue'
import { useStravaApi } from '../../composables/useStravaApi'
import { useWahooApi } from '../../composables/useWahooApi'
import { useLanguageDropdown } from '../../composables/useLanguageDropdown'
import { useThemeSettings } from '../../composables/useThemeSettings'

// Mock the composables
vi.mock('../../composables/useStravaApi')
vi.mock('../../composables/useWahooApi')
vi.mock('../../composables/useLanguageDropdown')
vi.mock('../../composables/useThemeSettings')

// Mock router
const mockPush = vi.fn()
const mockCurrentRoute = { value: { fullPath: '/test-path' } }
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush,
    currentRoute: mockCurrentRoute
  })
}))

// Mock window.location
const mockLocation = { href: '' }
Object.defineProperty(window, 'location', {
  writable: true,
  value: mockLocation
})

describe('Menu', () => {
  let wrapper: VueWrapper
  let i18n: ReturnType<typeof createI18n>

  const mockAuthState = {
    isAuthenticated: false,
    athlete: null,
    accessToken: null,
    refreshToken: null,
    expiresAt: null
  }

  const mockStravaApi = {
    authState: { value: mockAuthState },
    isLoading: { value: false },
    isAuthenticated: vi.fn(() => false),
    getAuthUrl: vi.fn().mockResolvedValue('https://strava.com/auth'),
    clearAuth: vi.fn()
  }

  const mockWahooApi = {
    authState: { value: { isAuthenticated: false, user: null } },
    isLoading: { value: false },
    isAuthenticated: vi.fn(() => false),
    getAuthUrl: vi.fn().mockResolvedValue('https://wahoo.com/auth'),
    deauthorize: vi.fn(),
    getUser: vi.fn()
  }

  const currentLanguageRef = ref('en')
  const mockLanguageDropdown = {
    currentLanguage: currentLanguageRef,
    languageOptions: {
      en: { name: 'English', flag: '🇬🇧' },
      fr: { name: 'Français', flag: '🇫🇷' }
    },
    changeLanguage: vi.fn()
  }

  const currentThemeRef = ref('system')
  const mockThemeSettings = {
    currentTheme: currentThemeRef,
    themeOptions: {
      light: { name: 'Light', icon: 'fa-solid fa-sun', description: 'Light theme' },
      dark: { name: 'Dark', icon: 'fa-solid fa-moon', description: 'Dark theme' },
      system: {
        name: 'System',
        icon: 'fa-solid fa-desktop',
        description: 'Use system default'
      }
    },
    changeTheme: vi.fn()
  }

  beforeEach(() => {
    vi.clearAllMocks()
    // Reset location.href
    mockLocation.href = ''

    // Reset mocks
    mockAuthState.isAuthenticated = false
    mockAuthState.athlete = null
    mockStravaApi.isAuthenticated.mockReturnValue(false)

    vi.mocked(useStravaApi).mockReturnValue(mockStravaApi as any)
    vi.mocked(useWahooApi).mockReturnValue(mockWahooApi as any)
    vi.mocked(useLanguageDropdown).mockReturnValue(mockLanguageDropdown as any)
    vi.mocked(useThemeSettings).mockReturnValue(mockThemeSettings as any)

    // Setup i18n
    i18n = createI18n({
      legacy: false,
      locale: 'en',
      messages: {
        en: {
          menu: {
            title: 'Menu',
            settings: 'Settings',
            support: 'Support'
          },
          settings: {
            language: 'Language',
            theme: 'Theme',
            light: 'Light',
            dark: 'Dark',
            system: 'System'
          },
          navbar: {
            logout: 'Logout'
          },
          footer: {
            reportIssue: 'Report Issue',
            githubRepo: 'GitHub Repository',
            documentation: 'Documentation'
          }
        }
      }
    })

    wrapper = mount(Menu, {
      global: {
        plugins: [i18n]
      }
    })
  })

  describe('Menu Toggle', () => {
    it('should render the menu trigger button', () => {
      const trigger = wrapper.find('.menu-trigger')
      expect(trigger.exists()).toBe(true)
      expect(trigger.find('i.fa-ellipsis-v').exists()).toBe(true)
    })

    it('should toggle menu when trigger is clicked', async () => {
      const trigger = wrapper.find('.menu-trigger')
      const dropdown = wrapper.find('.menu-dropdown-content')

      // Initially closed
      expect(dropdown.classes()).not.toContain('open')
      expect(trigger.classes()).not.toContain('active')

      // Open menu
      await trigger.trigger('click')
      expect(dropdown.classes()).toContain('open')
      expect(trigger.classes()).toContain('active')

      // Close menu
      await trigger.trigger('click')
      expect(dropdown.classes()).not.toContain('open')
      expect(trigger.classes()).not.toContain('active')
    })

    it('should close menu when clicking outside', async () => {
      const trigger = wrapper.find('.menu-trigger')

      // Open menu
      await trigger.trigger('click')
      expect(wrapper.find('.menu-dropdown-content').classes()).toContain('open')

      // Simulate click outside
      const clickEvent = new MouseEvent('click', { bubbles: true })
      document.dispatchEvent(clickEvent)
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.menu-dropdown-content').classes()).not.toContain('open')
    })

    it('should not close menu when clicking inside', async () => {
      const trigger = wrapper.find('.menu-trigger')

      // Open menu
      await trigger.trigger('click')
      expect(wrapper.find('.menu-dropdown-content').classes()).toContain('open')

      // Click inside menu
      const menuContent = wrapper.find('.menu-dropdown-content')
      await menuContent.trigger('click')

      expect(wrapper.find('.menu-dropdown-content').classes()).toContain('open')
    })
  })

  describe('Authentication - Not Logged In', () => {
    it('should show Strava login button when not authenticated', async () => {
      // Open menu first
      await wrapper.find('.menu-trigger').trigger('click')

      const stravaBtn = wrapper.find('.service-connect-btn')
      expect(stravaBtn.exists()).toBe(true)

      const stravaImage = stravaBtn.find('img.strava-btn-image-small')
      expect(stravaImage.exists()).toBe(true)
      expect(stravaImage.attributes('alt')).toBe('Connect with Strava')
    })

    it('should not show user info when not authenticated', async () => {
      // Open menu first
      await wrapper.find('.menu-trigger').trigger('click')

      expect(wrapper.find('.user-info-header').exists()).toBe(false)
      expect(wrapper.find('.service-disconnect-btn-compact').exists()).toBe(false)
    })

    it('should call getAuthUrl when Strava login button is clicked', async () => {
      // Open menu first
      await wrapper.find('.menu-trigger').trigger('click')
      await wrapper.vm.$nextTick()

      // Mock window.location.href
      const originalLocation = window.location
      delete (window as any).location
      window.location = { ...originalLocation, href: '' } as any

      // Call the handler directly to test the logic
      const vm = wrapper.vm as any
      await vm.handleStravaLogin()

      expect(mockStravaApi.getAuthUrl).toHaveBeenCalledWith('/test-path')
      expect(window.location.href).toBe('https://strava.com/auth')

      // Restore window.location
      ;(window as any).location = originalLocation
    })

    it('should disable login button when loading', async () => {
      // Open menu first
      await wrapper.find('.menu-trigger').trigger('click')

      mockStravaApi.isLoading.value = true
      await wrapper.vm.$nextTick()

      const stravaBtn = wrapper.find('.service-connect-btn')
      expect(stravaBtn.attributes('disabled')).toBeDefined()
    })

    it('should handle login error gracefully', async () => {
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
      mockStravaApi.getAuthUrl.mockRejectedValue(new Error('Auth failed'))

      // Call the handler directly to test error handling
      const vm = wrapper.vm as any
      await vm.handleStravaLogin()

      expect(consoleError).toHaveBeenCalledWith(
        'Failed to get Strava auth URL:',
        expect.any(Error)
      )

      consoleError.mockRestore()
    })
  })

  describe('Authentication - Logged In', () => {
    beforeEach(async () => {
      mockAuthState.isAuthenticated = true
      mockAuthState.athlete = {
        id: 12345,
        firstname: 'John',
        lastname: 'Doe',
        city: 'San Francisco',
        country: 'USA',
        profile_medium: 'https://example.com/avatar.jpg'
      } as any
      mockStravaApi.isAuthenticated.mockReturnValue(true)
      mockStravaApi.authState.value = mockAuthState

      wrapper = mount(Menu, {
        global: {
          plugins: [i18n]
        }
      })
      await wrapper.vm.$nextTick()
    })

    it('should show user info when authenticated', async () => {
      // Open menu first
      await wrapper.find('.menu-trigger').trigger('click')

      expect(wrapper.find('.user-info-header').exists()).toBe(true)
    })

    it('should display user avatar', async () => {
      // Open menu first
      await wrapper.find('.menu-trigger').trigger('click')

      const avatar = wrapper.find('.user-avatar')
      expect(avatar.exists()).toBe(true)
      expect(avatar.attributes('src')).toBe('https://example.com/avatar.jpg')
      expect(avatar.attributes('alt')).toBe('John')
    })

    it('should display user name and location', async () => {
      // Open menu first
      await wrapper.find('.menu-trigger').trigger('click')

      const userName = wrapper.find('.user-name')
      expect(userName.text()).toBe('John Doe')

      const userLocation = wrapper.find('.user-location')
      expect(userLocation.text()).toBe('San Francisco, USA')
    })

    it('should show default icon when no avatar', async () => {
      mockAuthState.athlete = {
        id: 12345,
        firstname: 'Jane',
        lastname: 'Smith',
        city: null,
        country: null,
        profile_medium: null
      } as any

      wrapper = mount(Menu, {
        global: {
          plugins: [i18n]
        }
      })
      await wrapper.vm.$nextTick()

      // Open menu first
      await wrapper.find('.menu-trigger').trigger('click')

      expect(wrapper.find('.user-avatar').exists()).toBe(false)
      expect(wrapper.find('.user-icon').exists()).toBe(true)
    })

    it('should show logout button when authenticated', async () => {
      // Open menu first
      await wrapper.find('.menu-trigger').trigger('click')

      const logoutBtn = wrapper.find('.service-disconnect-btn-compact')
      expect(logoutBtn.exists()).toBe(true)
    })

    it('should handle logout', async () => {
      // Open menu first
      await wrapper.find('.menu-trigger').trigger('click')

      const logoutBtn = wrapper.find('.service-disconnect-btn-compact')
      await logoutBtn.trigger('click')

      expect(mockStravaApi.clearAuth).toHaveBeenCalled()
      expect(mockLocation.href).toBe('/')

      // Menu should be closed
      expect(wrapper.find('.menu-dropdown-content').classes()).not.toContain('open')
    })

    it('should not show Strava login button when authenticated', async () => {
      // Open menu first
      await wrapper.find('.menu-trigger').trigger('click')

      // Check that there's no Strava connect button (the service-connect-btn with Strava image)
      const stravaButtons = wrapper.findAll('.service-connect-btn')
      const hasStravaConnectBtn = stravaButtons.some((btn) => {
        const img = btn.find('img.strava-btn-image-small')
        return img.exists()
      })
      expect(hasStravaConnectBtn).toBe(false)
    })
  })

  describe('Settings Section', () => {
    it('should display settings section title', () => {
      const settingsSection = wrapper.findAll('.menu-section')[1]
      expect(settingsSection.find('.menu-section-title').text()).toBe('Settings')
    })

    it('should display language and theme buttons', () => {
      const languageButton = wrapper.find('.settings-button')
      const themeButton = wrapper.findAll('.settings-button')[1]

      expect(languageButton.exists()).toBe(true)
      expect(languageButton.text()).toContain('Language')
      expect(languageButton.find('.fa-globe').exists()).toBe(true)

      expect(themeButton.exists()).toBe(true)
      expect(themeButton.text()).toContain('Theme')
      expect(themeButton.find('.fa-palette').exists()).toBe(true)
    })

    it('should have collapsed dropdowns by default', () => {
      expect(wrapper.find('.settings-dropdown').exists()).toBe(false)
    })

    describe('Language Button', () => {
      it('should expand language dropdown when clicked', async () => {
        const languageButton = wrapper.find('.settings-button')
        await languageButton.trigger('click')

        const languageDropdown = wrapper.find('.settings-dropdown')
        expect(languageDropdown.exists()).toBe(true)

        const chevron = languageButton.find('.settings-chevron')
        expect(chevron.classes()).toContain('expanded')
      })

      it('should render all language options when expanded', async () => {
        const languageButton = wrapper.find('.settings-button')
        await languageButton.trigger('click')

        const languageOptions = wrapper.findAll('.language-option')
        expect(languageOptions).toHaveLength(2)

        expect(languageOptions[0].text()).toContain('English')
        expect(languageOptions[0].text()).toContain('🇬🇧')

        expect(languageOptions[1].text()).toContain('Français')
        expect(languageOptions[1].text()).toContain('🇫🇷')
      })

      it('should mark current language as active', async () => {
        const languageButton = wrapper.find('.settings-button')
        await languageButton.trigger('click')

        const languageOptions = wrapper.findAll('.language-option')
        expect(languageOptions[0].classes()).toContain('active')
        expect(languageOptions[0].find('.checkmark').exists()).toBe(true)
      })

      it('should change language and close dropdown when option is clicked', async () => {
        const languageButton = wrapper.find('.settings-button')
        await languageButton.trigger('click')

        const languageOptions = wrapper.findAll('.language-option')
        await languageOptions[1].trigger('click')

        expect(mockLanguageDropdown.changeLanguage).toHaveBeenCalledWith('fr')
        expect(wrapper.find('.settings-dropdown').exists()).toBe(false)
      })

      it('should close theme dropdown when language dropdown is opened', async () => {
        // First open theme dropdown
        const themeButton = wrapper.findAll('.settings-button')[1]
        await themeButton.trigger('click')
        expect(wrapper.findAll('.settings-dropdown')).toHaveLength(1)

        // Then open language dropdown
        const languageButton = wrapper.find('.settings-button')
        await languageButton.trigger('click')
        expect(wrapper.findAll('.settings-dropdown')).toHaveLength(1) // Only one dropdown open
      })
    })

    describe('Theme Button', () => {
      it('should expand theme dropdown when clicked', async () => {
        const themeButton = wrapper.findAll('.settings-button')[1]
        await themeButton.trigger('click')

        const themeDropdown = wrapper.findAll('.settings-dropdown')[0]
        expect(themeDropdown.exists()).toBe(true)

        const chevron = themeButton.find('.settings-chevron')
        expect(chevron.classes()).toContain('expanded')
      })

      it('should render all theme options when expanded', async () => {
        const themeButton = wrapper.findAll('.settings-button')[1]
        await themeButton.trigger('click')

        const themeOptions = wrapper.findAll('.theme-option')
        expect(themeOptions).toHaveLength(3)

        expect(themeOptions[0].text()).toContain('Light')
        expect(themeOptions[0].find('.fa-sun').exists()).toBe(true)

        expect(themeOptions[1].text()).toContain('Dark')
        expect(themeOptions[1].find('.fa-moon').exists()).toBe(true)

        expect(themeOptions[2].text()).toContain('System')
        expect(themeOptions[2].find('.fa-desktop').exists()).toBe(true)
      })

      it('should mark current theme as active', async () => {
        const themeButton = wrapper.findAll('.settings-button')[1]
        await themeButton.trigger('click')

        const themeOptions = wrapper.findAll('.theme-option')
        expect(themeOptions[2].classes()).toContain('active') // System is default
        expect(themeOptions[2].find('.checkmark').exists()).toBe(true)
      })

      it('should change theme and close dropdown when option is clicked', async () => {
        const themeButton = wrapper.findAll('.settings-button')[1]
        await themeButton.trigger('click')

        const themeOptions = wrapper.findAll('.theme-option')
        await themeOptions[0].trigger('click') // Click Light

        expect(mockThemeSettings.changeTheme).toHaveBeenCalledWith('light')
        expect(wrapper.findAll('.settings-dropdown')).toHaveLength(0)
      })

      it('should close language dropdown when theme dropdown is opened', async () => {
        // First open language dropdown
        const languageButton = wrapper.find('.settings-button')
        await languageButton.trigger('click')
        expect(wrapper.findAll('.settings-dropdown')).toHaveLength(1)

        // Then open theme dropdown
        const themeButton = wrapper.findAll('.settings-button')[1]
        await themeButton.trigger('click')
        expect(wrapper.findAll('.settings-dropdown')).toHaveLength(1) // Only one dropdown open
      })
    })
  })

  describe('Support Links', () => {
    it('should display support section', () => {
      const sections = wrapper.findAll('.menu-section')
      const supportSection = sections[sections.length - 1]
      expect(supportSection.find('.menu-section-title').text()).toBe('Support')
    })

    it('should render all support links', () => {
      const supportLinks = wrapper.findAll('.support-link')
      expect(supportLinks).toHaveLength(3)
    })

    it('should have report issue link', () => {
      const reportLink = wrapper.findAll('.support-link')[0]
      expect(reportLink.text()).toContain('Report Issue')
      expect(reportLink.attributes('href')).toBe(
        'https://github.com/glemaitre/gravly/issues'
      )
      expect(reportLink.attributes('target')).toBe('_blank')
      expect(reportLink.attributes('rel')).toBe('noopener noreferrer')
      expect(reportLink.find('.fa-bug').exists()).toBe(true)
    })

    it('should have GitHub repository link', () => {
      const githubLink = wrapper.findAll('.support-link')[1]
      expect(githubLink.text()).toContain('GitHub Repository')
      expect(githubLink.attributes('href')).toBe('https://github.com/glemaitre/gravly')
      expect(githubLink.attributes('target')).toBe('_blank')
      expect(githubLink.find('.fa-github').exists()).toBe(true)
    })

    it('should have documentation link', () => {
      const docsLink = wrapper.findAll('.support-link')[2]
      expect(docsLink.text()).toContain('Documentation')
      expect(docsLink.attributes('href')).toBe(
        'https://github.com/glemaitre/gravly/blob/main/README.md'
      )
      expect(docsLink.attributes('target')).toBe('_blank')
      expect(docsLink.find('.fa-book').exists()).toBe(true)
    })
  })

  describe('Menu Structure', () => {
    it('should have proper dividers between sections', () => {
      const dividers = wrapper.findAll('.menu-divider')
      expect(dividers).toHaveLength(2)
    })

    it('should render menu dropdown content', () => {
      const dropdown = wrapper.find('.menu-dropdown-content')
      expect(dropdown.exists()).toBe(true)
      expect(dropdown.classes()).toContain('menu-dropdown-content')
    })
  })

  describe('Lifecycle', () => {
    it('should add click listener on mount', () => {
      const addEventListenerSpy = vi.spyOn(document, 'addEventListener')

      wrapper = mount(Menu, {
        global: {
          plugins: [i18n]
        }
      })

      expect(addEventListenerSpy).toHaveBeenCalledWith('click', expect.any(Function))
    })

    it('should remove click listener on unmount', () => {
      const removeEventListenerSpy = vi.spyOn(document, 'removeEventListener')

      wrapper.unmount()

      expect(removeEventListenerSpy).toHaveBeenCalledWith('click', expect.any(Function))
    })
  })

  describe('Accessibility', () => {
    it('should have title attribute on menu trigger', () => {
      const trigger = wrapper.find('.menu-trigger')
      expect(trigger.attributes('title')).toBe('Menu')
    })

    it('should have title attributes on support links', () => {
      const supportLinks = wrapper.findAll('.support-link')

      expect(supportLinks[0].attributes('title')).toBe('Report Issue')
      expect(supportLinks[1].attributes('title')).toBe('GitHub Repository')
      expect(supportLinks[2].attributes('title')).toBe('Documentation')
    })
  })
})
