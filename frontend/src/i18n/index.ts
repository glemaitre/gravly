import { createI18n } from 'vue-i18n'
import en from './locales/en'
import fr from './locales/fr'

export type MessageLanguages = 'en' | 'fr'

export type MessageSchema = typeof en

// Get the browser's default language or fallback to English
function getDefaultLanguage(): MessageLanguages {
  if (typeof navigator === 'undefined') return 'en'
  const browserLang = navigator.language.substring(0, 2)
  return ['en', 'fr'].includes(browserLang) ? (browserLang as MessageLanguages) : 'en'
}

// Get language from localStorage or use browser default
function getSavedLanguage(): MessageLanguages {
  if (typeof localStorage === 'undefined') return getDefaultLanguage()
  const saved = localStorage.getItem('cycling-editor-lang')
  return saved && ['en', 'fr'].includes(saved) ? (saved as MessageLanguages) : getDefaultLanguage()
}

export const i18n = createI18n<[MessageSchema], MessageLanguages>({
  legacy: false, // Use Composition API mode
  locale: 'en', // Start with English, we'll set the correct locale after mount
  fallbackLocale: 'en',
  messages: {
    en,
    fr
  }
})

// Initialize language after app is mounted
export function initializeLanguage() {
  const savedLang = getSavedLanguage()
  i18n.global.locale.value = savedLang
}

// Helper function to save language preference
export function setLanguage(lang: MessageLanguages) {
  i18n.global.locale.value = lang
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem('cycling-editor-lang', lang)
  }
}
