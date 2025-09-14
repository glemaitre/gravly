<template>
  <div id="app">
    <nav class="navbar">
      <div class="nav-container">
        <h1 class="nav-title">
          <i class="fa-solid fa-person-biking" aria-hidden="true"></i> Cycling Routes
        </h1>
        <div class="nav-right">
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
        </div>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { setLanguage, type MessageLanguages } from './i18n'

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

<style>
:root {
  /* Brand orange gradient palette */
  --brand-50: #ffe6d5ff;
  --brand-100: #ffccaaff;
  --brand-200: #ffb380ff;
  --brand-300: #ff9955ff;
  --brand-400: #ff7f2aff;
  --brand-500: #ff6600ff;

  --brand-gradient: linear-gradient(
    135deg,
    var(--brand-500) 0%,
    var(--brand-400) 20%,
    var(--brand-300) 45%,
    var(--brand-200) 70%,
    var(--brand-100) 100%
  );

  /* Common brand aliases */
  --brand-bg: var(--brand-gradient);
  --brand-primary: var(--brand-500);
  --brand-primary-hover: #e65c00;
  --brand-accent: var(--brand-300);
}

/* Global styles to prevent horizontal overflow */
* {
  box-sizing: border-box;
}

html,
body {
  overflow-x: hidden;
  max-width: 100vw;
}

#app {
  min-height: 100vh;
  background: var(--brand-bg);
  overflow-x: hidden;
}

/* Reusable brand utilities */
.bg-brand-gradient {
  background: var(--brand-gradient);
}
.text-brand {
  color: var(--brand-primary);
}
.border-brand {
  border-color: var(--brand-primary);
}
.btn-brand {
  background: var(--brand-primary);
  color: #fff;
}
.btn-brand:hover {
  background: var(--brand-primary-hover);
}

.navbar {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 9999;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.nav-title {
  margin: 0;
  color: #2d3748;
  font-size: 1.5rem;
  font-weight: 700;
}

.nav-link {
  color: #4a5568;
  text-decoration: none;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  transition: all 0.2s;
}

.nav-link:hover {
  background: rgba(255, 102, 0, 0.12);
  color: #2d3748;
}

.main-content {
  min-height: calc(100vh - 80px);
}

/* Language Dropdown Styles */
.language-dropdown {
  position: relative;
}

.language-dropdown-trigger.navbar-trigger {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  cursor: pointer;
  color: #374151;
  font-size: 0.875rem;
  text-align: left;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.language-dropdown-trigger.navbar-trigger:hover {
  background: rgba(255, 255, 255, 0.2);
}

.language-dropdown-trigger.navbar-trigger.active {
  background: rgba(255, 102, 0, 0.1);
  color: var(--brand-primary);
}

.language-dropdown-menu.navbar-menu {
  position: absolute;
  top: 100%;
  right: 0;
  left: auto;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-8px);
  transition: all 0.2s ease;
  margin-top: 4px;
  min-width: 140px;
}

.language-dropdown-menu.navbar-menu.open {
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
</style>
