import { describe, it, expect, vi } from 'vitest'

// Mock the i18n setLanguage function
vi.mock('../../i18n', () => ({
  setLanguage: vi.fn(),
  MessageLanguages: ['en', 'fr'] as const
}))

// Mock useI18n
vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    locale: { value: 'en' }
  })
}))

// Import after mocks
import { useLanguageDropdown } from '../useLanguageDropdown'

describe('useLanguageDropdown', () => {
  it('returns an object with required properties', () => {
    const result = useLanguageDropdown()

    expect(result).toHaveProperty('currentLanguage')
    expect(result).toHaveProperty('languageDropdownOpen')
    expect(result).toHaveProperty('languageOptions')
    expect(result).toHaveProperty('toggleLanguageDropdown')
    expect(result).toHaveProperty('changeLanguage')
    expect(result).toHaveProperty('closeLanguageDropdown')
  })

  it('provides language options', () => {
    const { languageOptions } = useLanguageDropdown()

    expect(languageOptions).toHaveProperty('en')
    expect(languageOptions).toHaveProperty('fr')
    expect(languageOptions.en).toHaveProperty('flag')
    expect(languageOptions.en).toHaveProperty('name')
    expect(languageOptions.fr).toHaveProperty('flag')
    expect(languageOptions.fr).toHaveProperty('name')
  })

  it('has toggle function that can be called', () => {
    const { toggleLanguageDropdown } = useLanguageDropdown()

    const mockEvent = { stopPropagation: vi.fn() }
    expect(() => toggleLanguageDropdown(mockEvent as unknown as Event)).not.toThrow()
  })

  it('has changeLanguage function that can be called', () => {
    const { changeLanguage } = useLanguageDropdown()

    expect(() => changeLanguage('en')).not.toThrow()
    expect(() => changeLanguage('fr')).not.toThrow()
  })

  it('has closeLanguageDropdown function that can be called', () => {
    const { closeLanguageDropdown } = useLanguageDropdown()

    const mockEvent = { target: document.createElement('div') } as unknown as MouseEvent
    expect(() =>
      closeLanguageDropdown(mockEvent, document.createElement('div'))
    ).not.toThrow()
  })
})
