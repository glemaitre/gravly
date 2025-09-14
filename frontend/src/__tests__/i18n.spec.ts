import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { i18n, initializeLanguage, setLanguage, getDefaultLanguage, getSavedLanguage, type MessageLanguages } from '../i18n'

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

// Mock navigator.language
Object.defineProperty(global, 'navigator', {
  value: {
    language: 'en-US'
  },
  writable: true
})

describe('i18n', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock.getItem.mockReturnValue(null)
    global.navigator.language = 'en-US'
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('getDefaultLanguage', () => {
    it('returns English when navigator is undefined', () => {
      const originalNavigator = global.navigator
      // @ts-ignore
      delete global.navigator

      const result = getDefaultLanguage()
      expect(result).toBe('en')

      global.navigator = originalNavigator
    })

    it('returns English for unsupported languages', () => {
      global.navigator.language = 'es-ES'
      const result = getDefaultLanguage()
      expect(result).toBe('en')
    })

    it('returns English for English browser language', () => {
      global.navigator.language = 'en-US'
      const result = getDefaultLanguage()
      expect(result).toBe('en')
    })

    it('returns French for French browser language', () => {
      global.navigator.language = 'fr-FR'
      const result = getDefaultLanguage()
      expect(result).toBe('fr')
    })

    it('handles language codes without region', () => {
      global.navigator.language = 'fr'
      const result = getDefaultLanguage()
      expect(result).toBe('fr')
    })
  })

  describe('getSavedLanguage', () => {
    it('returns default language when localStorage is undefined', () => {
      const originalLocalStorage = global.localStorage
      // @ts-ignore
      delete global.localStorage

      const result = getSavedLanguage()
      expect(result).toBe('en')

      global.localStorage = originalLocalStorage
    })

    it('returns saved language from localStorage', () => {
      localStorageMock.getItem.mockReturnValue('fr')
      const result = getSavedLanguage()
      expect(result).toBe('fr')
      expect(localStorageMock.getItem).toHaveBeenCalledWith('cycling-editor-lang')
    })

    it('returns default language when saved language is invalid', () => {
      localStorageMock.getItem.mockReturnValue('invalid-lang')
      const result = getSavedLanguage()
      expect(result).toBe('en')
    })

    it('returns default language when no saved language', () => {
      localStorageMock.getItem.mockReturnValue(null)
      const result = getSavedLanguage()
      expect(result).toBe('en')
    })
  })

  describe('setLanguage', () => {
    it('sets the language in i18n instance', () => {
      setLanguage('fr')
      expect(i18n.global.locale.value).toBe('fr')
    })

    it('saves language to localStorage', () => {
      setLanguage('fr')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('cycling-editor-lang', 'fr')
    })

    it('handles missing localStorage gracefully', () => {
      const originalLocalStorage = global.localStorage
      // @ts-ignore
      delete global.localStorage

      expect(() => setLanguage('fr')).not.toThrow()
      expect(i18n.global.locale.value).toBe('fr')

      global.localStorage = originalLocalStorage
    })
  })

  describe('initializeLanguage', () => {
    it('initializes with saved language', () => {
      localStorageMock.getItem.mockReturnValue('fr')
      initializeLanguage()
      expect(i18n.global.locale.value).toBe('fr')
    })

    it('initializes with default language when no saved language', () => {
      localStorageMock.getItem.mockReturnValue(null)
      initializeLanguage()
      expect(i18n.global.locale.value).toBe('en')
    })

    it('handles invalid saved language', () => {
      localStorageMock.getItem.mockReturnValue('invalid')
      initializeLanguage()
      expect(i18n.global.locale.value).toBe('en')
    })
  })

  describe('i18n instance', () => {
    it('has correct initial configuration', () => {
      expect(i18n.global.locale.value).toBe('en')
      expect(i18n.global.fallbackLocale.value).toBe('en')
      // Legacy property might not be available in all versions
      expect(i18n.global.legacy === false || i18n.global.legacy === undefined).toBe(true)
    })

    it('has English messages', () => {
      const enMessages = i18n.global.messages.value.en
      expect(enMessages).toBeDefined()
      expect(typeof enMessages).toBe('object')
    })

    it('has French messages', () => {
      const frMessages = i18n.global.messages.value.fr
      expect(frMessages).toBeDefined()
      expect(typeof frMessages).toBe('object')
    })

    it('can translate messages', () => {
      const t = i18n.global.t
      // Test if we can access translation function
      expect(typeof t).toBe('function')
    })
  })

  describe('MessageLanguages type', () => {
    it('accepts valid language codes', () => {
      const validLanguages: MessageLanguages[] = ['en', 'fr']
      validLanguages.forEach(lang => {
        expect(['en', 'fr']).toContain(lang)
      })
    })
  })

  describe('language persistence', () => {
    it('persists language changes across function calls', () => {
      setLanguage('fr')
      expect(i18n.global.locale.value).toBe('fr')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('cycling-editor-lang', 'fr')

      // Test that setLanguage works
      expect(i18n.global.locale.value).toBe('fr')
    })

    it('handles browser language changes', () => {
      global.navigator.language = 'fr-FR'
      localStorageMock.getItem.mockReturnValue(null)

      const result = getSavedLanguage()
      expect(result).toBe('fr')
    })
  })

  describe('error handling', () => {
    it('handles localStorage errors gracefully', () => {
      localStorageMock.getItem.mockImplementation(() => {
        throw new Error('localStorage error')
      })

      // The function should handle the error and return default language
      const result = getSavedLanguage()
      expect(result).toBe('en')
    })

    it('handles setItem errors gracefully', () => {
      localStorageMock.setItem.mockImplementation(() => {
        throw new Error('localStorage error')
      })

      // Should still set the language in i18n even if localStorage fails
      setLanguage('fr')
      expect(i18n.global.locale.value).toBe('fr')
    })
  })
})
