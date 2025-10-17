import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useThemeSettings } from '../composables/useThemeSettings'

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}

// Mock window.matchMedia
const mockMatchMedia = vi.fn()

// Mock document.documentElement
const mockDocumentElement = {
  setAttribute: vi.fn(),
  getAttribute: vi.fn()
}

// Mock MediaQueryList
const createMockMediaQueryList = (matches: boolean) => ({
  matches,
  media: '(prefers-color-scheme: dark)',
  onchange: null,
  addListener: vi.fn(),
  removeListener: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  dispatchEvent: vi.fn()
})

describe('useThemeSettings', () => {
  let composable: ReturnType<typeof useThemeSettings>

  beforeEach(() => {
    vi.clearAllMocks()

    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: mockLocalStorage,
      writable: true
    })

    // Mock window.matchMedia
    Object.defineProperty(window, 'matchMedia', {
      value: mockMatchMedia,
      writable: true
    })

    // Mock document.documentElement
    Object.defineProperty(document, 'documentElement', {
      value: mockDocumentElement,
      writable: true
    })

    // Reset mocks
    mockLocalStorage.getItem.mockReturnValue(null)
    mockLocalStorage.setItem.mockClear()
    mockDocumentElement.setAttribute.mockClear()
    mockMatchMedia.mockReturnValue(createMockMediaQueryList(false))
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Initialization', () => {
    it('should initialize with default values', () => {
      composable = useThemeSettings()

      expect(composable.currentTheme.value).toBe('system')
      expect(composable.themeOptions).toEqual({
        light: {
          name: 'Light',
          icon: 'fa-solid fa-sun',
          description: 'Light theme'
        },
        dark: {
          name: 'Dark',
          icon: 'fa-solid fa-moon',
          description: 'Dark theme'
        },
        system: {
          name: 'System',
          icon: 'fa-solid fa-desktop',
          description: 'Use system default'
        }
      })
    })

    it('should provide all required functions', () => {
      composable = useThemeSettings()

      expect(typeof composable.initializeTheme).toBe('function')
      expect(typeof composable.changeTheme).toBe('function')
      expect(typeof composable.watchSystemTheme).toBe('function')
    })
  })

  describe('getSavedTheme', () => {
    it('should return system when localStorage is undefined', () => {
      // Mock undefined localStorage
      Object.defineProperty(window, 'localStorage', {
        value: undefined,
        writable: true
      })

      composable = useThemeSettings()
      composable.initializeTheme()

      expect(composable.currentTheme.value).toBe('system')
    })

    it('should return system when localStorage throws error', () => {
      mockLocalStorage.getItem.mockImplementation(() => {
        throw new Error('localStorage error')
      })

      composable = useThemeSettings()
      composable.initializeTheme()

      expect(composable.currentTheme.value).toBe('system')
    })

    it('should return saved theme when valid', () => {
      mockLocalStorage.getItem.mockReturnValue('dark')

      composable = useThemeSettings()
      composable.initializeTheme()

      expect(composable.currentTheme.value).toBe('dark')
    })

    it('should return system when saved theme is invalid', () => {
      mockLocalStorage.getItem.mockReturnValue('invalid-theme')

      composable = useThemeSettings()
      composable.initializeTheme()

      expect(composable.currentTheme.value).toBe('system')
    })

    it('should return system when saved theme is null', () => {
      mockLocalStorage.getItem.mockReturnValue(null)

      composable = useThemeSettings()
      composable.initializeTheme()

      expect(composable.currentTheme.value).toBe('system')
    })

    it('should return system when saved theme is empty string', () => {
      mockLocalStorage.getItem.mockReturnValue('')

      composable = useThemeSettings()
      composable.initializeTheme()

      expect(composable.currentTheme.value).toBe('system')
    })
  })

  describe('initializeTheme', () => {
    it('should load theme from localStorage and apply it', () => {
      mockLocalStorage.getItem.mockReturnValue('light')
      mockMatchMedia.mockReturnValue(createMockMediaQueryList(false))

      composable = useThemeSettings()
      composable.initializeTheme()

      expect(composable.currentTheme.value).toBe('light')
      expect(mockDocumentElement.setAttribute).toHaveBeenCalledWith(
        'data-theme',
        'light'
      )
    })

    it('should apply system theme when system is selected', () => {
      mockLocalStorage.getItem.mockReturnValue('system')
      mockMatchMedia.mockReturnValue(createMockMediaQueryList(true))

      composable = useThemeSettings()
      composable.initializeTheme()

      expect(composable.currentTheme.value).toBe('system')
      expect(mockDocumentElement.setAttribute).toHaveBeenCalledWith(
        'data-theme',
        'dark'
      )
    })

    it('should apply light theme when system prefers light', () => {
      mockLocalStorage.getItem.mockReturnValue('system')
      mockMatchMedia.mockReturnValue(createMockMediaQueryList(false))

      composable = useThemeSettings()
      composable.initializeTheme()

      expect(composable.currentTheme.value).toBe('system')
      expect(mockDocumentElement.setAttribute).toHaveBeenCalledWith(
        'data-theme',
        'light'
      )
    })
  })

  describe('applyTheme (tested indirectly)', () => {
    beforeEach(() => {
      composable = useThemeSettings()
    })

    it('should apply light theme through changeTheme', () => {
      mockDocumentElement.setAttribute.mockClear()
      composable.changeTheme('light')

      expect(mockDocumentElement.setAttribute).toHaveBeenCalledWith(
        'data-theme',
        'light'
      )
    })

    it('should apply dark theme through changeTheme', () => {
      mockDocumentElement.setAttribute.mockClear()
      composable.changeTheme('dark')

      expect(mockDocumentElement.setAttribute).toHaveBeenCalledWith(
        'data-theme',
        'dark'
      )
    })

    it('should apply system theme based on media query through changeTheme', () => {
      mockDocumentElement.setAttribute.mockClear()
      mockMatchMedia.mockReturnValue(createMockMediaQueryList(true))
      composable.changeTheme('system')

      expect(mockMatchMedia).toHaveBeenCalledWith('(prefers-color-scheme: dark)')
      expect(mockDocumentElement.setAttribute).toHaveBeenCalledWith(
        'data-theme',
        'dark'
      )
    })

    it('should apply light theme when system prefers light through changeTheme', () => {
      mockDocumentElement.setAttribute.mockClear()
      mockMatchMedia.mockReturnValue(createMockMediaQueryList(false))
      composable.changeTheme('system')

      expect(mockMatchMedia).toHaveBeenCalledWith('(prefers-color-scheme: dark)')
      expect(mockDocumentElement.setAttribute).toHaveBeenCalledWith(
        'data-theme',
        'light'
      )
    })
  })

  describe('changeTheme', () => {
    beforeEach(() => {
      composable = useThemeSettings()
    })

    it('should change theme and save to localStorage', () => {
      composable.changeTheme('dark')

      expect(composable.currentTheme.value).toBe('dark')
      expect(mockDocumentElement.setAttribute).toHaveBeenCalledWith(
        'data-theme',
        'dark'
      )
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'cycling-editor-theme',
        'dark'
      )
    })

    it('should change theme to light', () => {
      composable.changeTheme('light')

      expect(composable.currentTheme.value).toBe('light')
      expect(mockDocumentElement.setAttribute).toHaveBeenCalledWith(
        'data-theme',
        'light'
      )
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'cycling-editor-theme',
        'light'
      )
    })

    it('should change theme to system', () => {
      mockMatchMedia.mockReturnValue(createMockMediaQueryList(false))
      composable.changeTheme('system')

      expect(composable.currentTheme.value).toBe('system')
      expect(mockDocumentElement.setAttribute).toHaveBeenCalledWith(
        'data-theme',
        'light'
      )
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'cycling-editor-theme',
        'system'
      )
    })

    it('should handle localStorage errors gracefully', () => {
      mockLocalStorage.setItem.mockImplementation(() => {
        throw new Error('localStorage error')
      })

      // Should not throw
      expect(() => {
        composable.changeTheme('dark')
      }).not.toThrow()

      expect(composable.currentTheme.value).toBe('dark')
      expect(mockDocumentElement.setAttribute).toHaveBeenCalledWith(
        'data-theme',
        'dark'
      )
    })

    it('should handle undefined localStorage', () => {
      Object.defineProperty(window, 'localStorage', {
        value: undefined,
        writable: true
      })

      // Should not throw
      expect(() => {
        composable.changeTheme('dark')
      }).not.toThrow()

      expect(composable.currentTheme.value).toBe('dark')
      expect(mockDocumentElement.setAttribute).toHaveBeenCalledWith(
        'data-theme',
        'dark'
      )
    })
  })

  describe('watchSystemTheme', () => {
    beforeEach(() => {
      composable = useThemeSettings()
    })

    it('should return cleanup function when window is undefined', () => {
      // Mock undefined window
      const originalWindow = global.window
      // @ts-ignore
      delete global.window

      const _cleanup = composable.watchSystemTheme()
      expect(typeof _cleanup).toBe('function')

      // Restore window
      global.window = originalWindow
    })

    it('should return cleanup function when not in system mode', () => {
      composable.currentTheme.value = 'light'
      const _cleanup = composable.watchSystemTheme()
      expect(typeof _cleanup).toBe('function')
    })

    it('should set up media query listener when in system mode', () => {
      composable.currentTheme.value = 'system'
      const mockMediaQueryList = createMockMediaQueryList(false)
      mockMatchMedia.mockReturnValue(mockMediaQueryList)

      const _cleanup = composable.watchSystemTheme()

      expect(mockMatchMedia).toHaveBeenCalledWith('(prefers-color-scheme: dark)')
      expect(mockMediaQueryList.addEventListener).toHaveBeenCalledWith(
        'change',
        expect.any(Function)
      )
      expect(typeof _cleanup).toBe('function')
    })

    it('should call applyTheme when system theme changes', () => {
      composable.currentTheme.value = 'system'
      const mockMediaQueryList = createMockMediaQueryList(false)
      mockMatchMedia.mockReturnValue(mockMediaQueryList)

      composable.watchSystemTheme()

      // Get the change handler
      const changeHandler = mockMediaQueryList.addEventListener.mock.calls[0][1]

      // Clear previous calls
      mockDocumentElement.setAttribute.mockClear()
      mockMatchMedia.mockClear()

      // Simulate system theme change
      mockMatchMedia.mockReturnValue(createMockMediaQueryList(true))
      changeHandler()

      expect(mockMatchMedia).toHaveBeenCalledWith('(prefers-color-scheme: dark)')
      expect(mockDocumentElement.setAttribute).toHaveBeenCalledWith(
        'data-theme',
        'dark'
      )
    })

    it('should not apply theme if current theme is no longer system', () => {
      composable.currentTheme.value = 'system'
      const mockMediaQueryList = createMockMediaQueryList(false)
      mockMatchMedia.mockReturnValue(mockMediaQueryList)

      composable.watchSystemTheme()

      // Change theme away from system
      composable.currentTheme.value = 'light'

      // Get the change handler
      const changeHandler = mockMediaQueryList.addEventListener.mock.calls[0][1]

      // Clear previous calls
      mockDocumentElement.setAttribute.mockClear()
      mockMatchMedia.mockClear()

      // Simulate system theme change
      changeHandler()

      // Should not call applyTheme since we're no longer in system mode
      expect(mockMatchMedia).not.toHaveBeenCalled()
      expect(mockDocumentElement.setAttribute).not.toHaveBeenCalled()
    })

    it('should remove event listener on cleanup', () => {
      composable.currentTheme.value = 'system'
      const mockMediaQueryList = createMockMediaQueryList(false)
      mockMatchMedia.mockReturnValue(mockMediaQueryList)

      const cleanup = composable.watchSystemTheme()

      // Get the change handler
      const changeHandler = mockMediaQueryList.addEventListener.mock.calls[0][1]

      // Call cleanup
      cleanup()

      expect(mockMediaQueryList.removeEventListener).toHaveBeenCalledWith(
        'change',
        changeHandler
      )
    })
  })

  describe('Theme options', () => {
    it('should have correct theme option structure', () => {
      composable = useThemeSettings()

      const { themeOptions } = composable

      // Test light theme option
      expect(themeOptions.light).toEqual({
        name: 'Light',
        icon: 'fa-solid fa-sun',
        description: 'Light theme'
      })

      // Test dark theme option
      expect(themeOptions.dark).toEqual({
        name: 'Dark',
        icon: 'fa-solid fa-moon',
        description: 'Dark theme'
      })

      // Test system theme option
      expect(themeOptions.system).toEqual({
        name: 'System',
        icon: 'fa-solid fa-desktop',
        description: 'Use system default'
      })
    })
  })

  describe('Integration tests', () => {
    it('should work end-to-end with localStorage persistence', () => {
      // Start with no saved theme
      mockLocalStorage.getItem.mockReturnValue(null)
      mockMatchMedia.mockReturnValue(createMockMediaQueryList(false))

      composable = useThemeSettings()
      composable.initializeTheme()

      // Should default to system
      expect(composable.currentTheme.value).toBe('system')
      expect(mockDocumentElement.setAttribute).toHaveBeenCalledWith(
        'data-theme',
        'light'
      )

      // Change to dark theme
      composable.changeTheme('dark')

      expect(composable.currentTheme.value).toBe('dark')
      expect(mockDocumentElement.setAttribute).toHaveBeenCalledWith(
        'data-theme',
        'dark'
      )
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'cycling-editor-theme',
        'dark'
      )

      // Simulate page reload - should load dark theme
      mockLocalStorage.getItem.mockReturnValue('dark')
      const newComposable = useThemeSettings()
      newComposable.initializeTheme()

      expect(newComposable.currentTheme.value).toBe('dark')
      expect(mockDocumentElement.setAttribute).toHaveBeenCalledWith(
        'data-theme',
        'dark'
      )
    })

    it('should handle system theme changes when watching', () => {
      composable = useThemeSettings()
      composable.currentTheme.value = 'system'

      const mockMediaQueryList = createMockMediaQueryList(false)
      mockMatchMedia.mockReturnValue(mockMediaQueryList)

      const _cleanup = composable.watchSystemTheme()

      // Simulate system changing to dark mode
      mockMatchMedia.mockReturnValue(createMockMediaQueryList(true))
      const changeHandler = mockMediaQueryList.addEventListener.mock.calls[0][1]
      changeHandler()

      expect(mockDocumentElement.setAttribute).toHaveBeenCalledWith(
        'data-theme',
        'dark'
      )

      // Cleanup
      _cleanup()
    })
  })

  describe('Edge cases and error handling', () => {
    it('should handle multiple theme changes', () => {
      composable = useThemeSettings()

      composable.changeTheme('light')
      expect(composable.currentTheme.value).toBe('light')

      composable.changeTheme('dark')
      expect(composable.currentTheme.value).toBe('dark')

      composable.changeTheme('system')
      expect(composable.currentTheme.value).toBe('system')
    })

    it('should handle rapid theme changes', () => {
      composable = useThemeSettings()

      // Rapid changes
      composable.changeTheme('light')
      composable.changeTheme('dark')
      composable.changeTheme('system')
      composable.changeTheme('light')

      expect(composable.currentTheme.value).toBe('light')
      expect(mockLocalStorage.setItem).toHaveBeenCalledTimes(4)
    })

    it('should handle invalid theme values gracefully', () => {
      // This tests the type safety - invalid values should be caught by TypeScript
      // but if they somehow get through, the functions should handle them
      composable = useThemeSettings()

      // These would be TypeScript errors in real usage, but testing runtime behavior
      expect(() => {
        // @ts-ignore - intentionally testing invalid input
        composable.changeTheme('invalid-theme')
      }).not.toThrow()
    })
  })
})
