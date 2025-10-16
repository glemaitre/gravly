import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { setLanguage, type MessageLanguages } from '../i18n'

export function useLanguageDropdown() {
  const { locale } = useI18n()
  const currentLanguage = ref<MessageLanguages>('en')
  const languageDropdownOpen = ref(false)

  // Language options with flags
  const languageOptions = {
    en: { flag: '🇺🇸', name: 'English' },
    fr: { flag: '🇫🇷', name: 'Français' }
  }

  // Watch for locale changes to update currentLanguage
  watch(
    locale,
    (newLocale) => {
      currentLanguage.value = newLocale as MessageLanguages
    },
    { immediate: true }
  )

  // Toggle dropdown function that prevents event bubbling
  function toggleLanguageDropdown(event: Event) {
    event.stopPropagation()
    languageDropdownOpen.value = !languageDropdownOpen.value
  }

  // Language switching function
  function changeLanguage(lang: MessageLanguages) {
    currentLanguage.value = lang
    setLanguage(lang)
    languageDropdownOpen.value = false // Close dropdown after selection
  }

  // Close dropdown when clicking outside
  function closeLanguageDropdown(event: MouseEvent, dropdownRef: HTMLElement | null) {
    if (dropdownRef && !dropdownRef.contains(event.target as Node)) {
      languageDropdownOpen.value = false
    }
  }

  return {
    currentLanguage,
    languageDropdownOpen,
    languageOptions,
    toggleLanguageDropdown,
    changeLanguage,
    closeLanguageDropdown
  }
}
