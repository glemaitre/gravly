<template>
  <header class="navbar">
    <div class="navbar-container">
      <!-- Brand/Logo Section with Navigation -->
      <div class="navbar-brand">
        <img :src="logoUrl" alt="Cycling Segments" class="navbar-logo" />

        <!-- Navigation Menu -->
        <div class="nav-menu">
          <router-link to="/" class="nav-link" active-class="active">
            <i class="fa-solid fa-home"></i>
            <span>{{ $t('navbar.home') }}</span>
          </router-link>
          <router-link to="/editor" class="nav-link" active-class="active">
            <i class="fa-solid fa-edit"></i>
            <span>{{ $t('navbar.editor') }}</span>
          </router-link>
        </div>
      </div>

      <!-- Right Section -->
      <nav class="navbar-nav">
        <div class="language-dropdown" ref="languageDropdown">
          <button
            class="language-dropdown-trigger navbar-trigger"
            @click="toggleLanguageDropdown"
            :class="{ active: languageDropdownOpen }"
          >
            <span class="language-flag">{{
              languageOptions[currentLanguage].flag
            }}</span>
            <span class="language-name">{{
              languageOptions[currentLanguage].name
            }}</span>
            <span class="dropdown-arrow">
              <i
                class="fa-solid fa-chevron-down"
                :class="{ rotated: languageDropdownOpen }"
              ></i>
            </span>
          </button>
          <div
            class="language-dropdown-menu navbar-menu"
            :class="{ open: languageDropdownOpen }"
          >
            <button
              v-for="(option, lang) in languageOptions"
              :key="lang"
              class="language-option"
              :class="{ active: currentLanguage === lang }"
              @click="
                (e) => {
                  e.stopPropagation()
                  changeLanguage(lang as MessageLanguages)
                }
              "
            >
              <span class="language-flag">{{ option.flag }}</span>
              <span class="language-name">{{ option.name }}</span>
              <span v-if="currentLanguage === lang" class="checkmark">
                <i class="fa-solid fa-check"></i>
              </span>
            </button>
          </div>
        </div>
      </nav>
    </div>
  </header>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { setLanguage, type MessageLanguages } from '../i18n'
import logoUrl from '../assets/images/logo.svg'

// i18n setup
const { locale } = useI18n()
const currentLanguage = ref<MessageLanguages>('en')

// Watch for locale changes to update currentLanguage
watch(
  locale,
  (newLocale) => {
    currentLanguage.value = newLocale as MessageLanguages
  },
  { immediate: true }
)

// Language dropdown state
const languageDropdownOpen = ref(false)

// Language options with flags
const languageOptions = {
  en: { flag: '🇺🇸', name: 'English' },
  fr: { flag: '🇫🇷', name: 'Français' }
}

// Close dropdown when clicking outside
const languageDropdown = ref<HTMLElement | null>(null)

function closeLanguageDropdown(event: MouseEvent) {
  if (
    languageDropdown.value &&
    !languageDropdown.value.contains(event.target as Node)
  ) {
    languageDropdownOpen.value = false
  }
}

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

onMounted(() => {
  document.addEventListener('click', closeLanguageDropdown)
})

onUnmounted(() => {
  document.removeEventListener('click', closeLanguageDropdown)
})
</script>

<style scoped>
/* CSS Variables for consistency */
:root {
  --navbar-height: 80px;
}

.navbar {
  position: sticky;
  top: 0;
  z-index: 9999;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  box-shadow:
    0 1px 3px 0 rgba(0, 0, 0, 0.1),
    0 1px 2px 0 rgba(0, 0, 0, 0.06);
  min-height: var(--navbar-height);
}

.navbar-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0.75rem 1.5rem;
  min-height: var(--navbar-height);
  box-sizing: border-box;
}

.navbar-brand {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  margin-right: 1rem;
  gap: 2rem;
}

.navbar-logo {
  height: 32px;
  width: auto;
  max-width: 200px;
  object-fit: contain;
  display: block;
}

.navbar-nav {
  display: flex;
  align-items: center;
  margin-left: auto;
}

.nav-menu {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  text-decoration: none;
  color: #374151;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.nav-link:hover {
  background: #f9fafb;
  color: var(--brand-primary);
}

.nav-link.active {
  background: var(--brand-50);
  color: var(--brand-primary);
  box-shadow: 0 0 0 3px rgba(255, 102, 0, 0.1);
}

.nav-link i {
  font-size: 0.875rem;
}

.nav .language-dropdown {
  position: relative;
}

.navbar-nav .language-dropdown-trigger.navbar-trigger {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #ffffff;
  cursor: pointer;
  color: #374151;
  font-size: 0.875rem;
  text-align: left;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.navbar-nav .language-dropdown-trigger.navbar-trigger:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

.navbar-nav .language-dropdown-trigger.navbar-trigger.active {
  background: var(--brand-50);
  border-color: var(--brand-300);
  color: var(--brand-600);
  box-shadow: 0 0 0 3px rgba(255, 102, 0, 0.1);
}

.navbar-menu {
  position: absolute;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-8px);
  transition: all 0.2s ease;
  margin-top: 4px;
  min-width: 140px;
}

.navbar-nav .language-dropdown-menu.navbar-menu {
  top: 100%;
  right: 0;
  left: auto;
}

.navbar-nav .language-dropdown-menu.navbar-menu.open {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.language-flag {
  font-size: 1.1em;
  line-height: 1;
}

.language-name {
  flex: 1;
  white-space: nowrap;
}

.dropdown-arrow {
  font-size: 0.75em;
  transition: transform 0.2s ease;
  opacity: 0.7;
}

.dropdown-arrow .fa-chevron-down.rotated {
  transform: rotate(180deg);
}

.language-option {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.5rem 0.75rem;
  border: none;
  background: transparent;
  cursor: pointer;
  color: #111827;
  font-size: 0.8rem;
  text-align: left;
  transition: background 0.2s ease;
}

.language-option:first-child {
  border-top-left-radius: 7px;
  border-top-right-radius: 7px;
}

.language-option:last-child {
  border-bottom-left-radius: 7px;
  border-bottom-right-radius: 7px;
}

.language-option:hover {
  background: #f3f4f6;
}

.language-option.active {
  background: var(--brand-50);
  color: var(--brand-primary);
  font-weight: 500;
}

.language-option.active:hover {
  background: var(--brand-100);
}

.language-option .language-flag {
  font-size: 1.1em;
}

.language-option .language-name {
  flex: 1;
}

.checkmark {
  font-size: 0.75em;
  color: var(--brand-primary);
}

/* Responsive Design */
@media (max-width: 1200px) {
  .navbar-container {
    max-width: 100%;
    padding: 0.75rem 1.25rem;
  }
}

@media (max-width: 992px) {
  .navbar-container {
    padding: 0.75rem 1rem;
  }

  .navbar-logo {
    max-width: 180px;
  }

  .navbar-brand {
    gap: 1.5rem;
  }
}

@media (max-width: 768px) {
  .navbar-container {
    padding: 0.75rem 0.75rem;
  }

  .navbar-logo {
    max-width: 150px;
    height: 28px;
  }

  .navbar-brand {
    gap: 1rem;
  }

  .nav-link span {
    display: none;
  }

  .nav-link {
    padding: 0.4rem 0.6rem;
  }

  .navbar-nav .language-dropdown-trigger.navbar-trigger {
    padding: 0.4rem 0.6rem;
    font-size: 0.85rem;
  }
}

@media (max-width: 576px) {
  .navbar-container {
    padding: 0.75rem 0.75rem;
  }

  .navbar-logo {
    max-width: 120px;
    height: 24px;
  }

  .navbar-brand {
    gap: 0.75rem;
  }

  .navbar-nav .language-dropdown-trigger.navbar-trigger {
    padding: 0.3rem 0.5rem;
    font-size: 0.8rem;
  }

  .language-name {
    display: none;
  }
}

@media (max-width: 480px) {
  .navbar-logo {
    max-width: 100px;
    height: 22px;
  }

  .navbar-brand {
    gap: 0.5rem;
  }
}
</style>
