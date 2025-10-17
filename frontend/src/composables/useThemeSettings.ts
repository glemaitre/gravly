import { ref } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'system'

export function useThemeSettings() {
  const currentTheme = ref<ThemeMode>('system')

  // Theme options
  const themeOptions = {
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
  }

  // Get saved theme from localStorage or use system default
  function getSavedTheme(): ThemeMode {
    if (typeof localStorage === 'undefined') return 'system'
    try {
      const saved = localStorage.getItem('cycling-editor-theme')
      return saved && ['light', 'dark', 'system'].includes(saved)
        ? (saved as ThemeMode)
        : 'system'
    } catch {
      return 'system'
    }
  }

  // Initialize theme
  function initializeTheme() {
    currentTheme.value = getSavedTheme()
    applyTheme(currentTheme.value)
  }

  // Apply theme to document
  function applyTheme(theme: ThemeMode) {
    const root = document.documentElement

    if (theme === 'system') {
      // Use system preference
      const systemPrefersDark = window.matchMedia(
        '(prefers-color-scheme: dark)'
      ).matches
      root.setAttribute('data-theme', systemPrefersDark ? 'dark' : 'light')
    } else {
      root.setAttribute('data-theme', theme)
    }
  }

  // Change theme function
  function changeTheme(theme: ThemeMode) {
    currentTheme.value = theme
    applyTheme(theme)

    // Save to localStorage
    if (typeof localStorage !== 'undefined') {
      try {
        localStorage.setItem('cycling-editor-theme', theme)
      } catch {
        // Ignore localStorage errors
      }
    }
  }

  // Watch for system theme changes when in system mode
  function watchSystemTheme() {
    if (typeof window !== 'undefined' && currentTheme.value === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

      const handleChange = () => {
        if (currentTheme.value === 'system') {
          applyTheme('system')
        }
      }

      mediaQuery.addEventListener('change', handleChange)

      return () => {
        mediaQuery.removeEventListener('change', handleChange)
      }
    }
    return () => {}
  }

  return {
    currentTheme,
    themeOptions,
    initializeTheme,
    changeTheme,
    watchSystemTheme
  }
}
