<template>
  <div class="menu-dropdown" ref="menuDropdown">
    <button
      class="menu-trigger navbar-btn"
      @click="toggleMenu"
      :class="{ active: menuOpen }"
      :title="$t('menu.title')"
    >
      <i class="fa-solid fa-ellipsis-v"></i>
    </button>

    <div class="menu-dropdown-content" :class="{ open: menuOpen }">
      <!-- Strava Authentication Section -->
      <div class="menu-section">
        <div v-if="!isAuthenticated" class="strava-section">
          <button
            class="strava-login-btn menu-item"
            @click="handleStravaLogin"
            :disabled="isLoading"
          >
            <img
              :src="stravaConnectBtn"
              alt="Connect with Strava"
              class="strava-btn-image"
            />
          </button>
        </div>
        <div v-else class="user-info-section">
          <div class="user-info-header">
            <img
              v-if="athlete?.profile_medium"
              :src="athlete.profile_medium"
              :alt="athlete.firstname"
              class="user-avatar"
            />
            <i v-else class="fas fa-user-circle user-icon"></i>
            <div class="user-details">
              <div class="user-name">
                {{ athlete?.firstname }} {{ athlete?.lastname }}
              </div>
              <div class="user-location" v-if="athlete?.city">
                {{ athlete.city }}, {{ athlete.country }}
              </div>
            </div>
          </div>
          <button class="logout-btn menu-item" @click="handleLogout">
            <i class="fas fa-sign-out-alt"></i>
            <span>{{ $t('navbar.logout') }}</span>
          </button>
        </div>
      </div>

      <!-- Divider -->
      <hr class="menu-divider" />

      <!-- Settings Section -->
      <div class="menu-section">
        <div class="menu-section-title">{{ $t('menu.settings') }}</div>

        <!-- Language Button -->
        <button class="settings-button menu-item" @click="toggleLanguageDropdown">
          <i class="fa-solid fa-globe"></i>
          <span>{{ $t('settings.language') }}</span>
          <i
            class="fa-solid fa-chevron-down settings-chevron"
            :class="{ expanded: languageDropdownOpen }"
          ></i>
        </button>

        <!-- Language Dropdown -->
        <div v-if="languageDropdownOpen" class="settings-dropdown">
          <button
            v-for="(option, lang) in languageOptions"
            :key="lang"
            class="language-option menu-item"
            :class="{ active: currentLanguage === lang }"
            @click="
              (e) => {
                e.stopPropagation()
                changeLanguage(lang as MessageLanguages)
                languageDropdownOpen = false
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

        <!-- Theme Button -->
        <button class="settings-button menu-item" @click="toggleThemeDropdown">
          <i class="fa-solid fa-palette"></i>
          <span>{{ $t('settings.theme') }}</span>
          <i
            class="fa-solid fa-chevron-down settings-chevron"
            :class="{ expanded: themeDropdownOpen }"
          ></i>
        </button>

        <!-- Theme Dropdown -->
        <div v-if="themeDropdownOpen" class="settings-dropdown">
          <button
            v-for="(option, theme) in themeOptions"
            :key="theme"
            class="theme-option menu-item"
            :class="{ active: currentTheme === theme }"
            @click="
              (e) => {
                e.stopPropagation()
                changeTheme(theme as any)
                themeDropdownOpen = false
              }
            "
          >
            <i :class="option.icon" class="theme-icon"></i>
            <span class="theme-name">{{ option.name }}</span>
            <span v-if="currentTheme === theme" class="checkmark">
              <i class="fa-solid fa-check"></i>
            </span>
          </button>
        </div>
      </div>

      <!-- Divider -->
      <hr class="menu-divider" />

      <!-- Support Links Section -->
      <div class="menu-section">
        <div class="menu-section-title">{{ $t('menu.support') }}</div>
        <a
          href="https://github.com/glemaitre/gravly/issues"
          target="_blank"
          rel="noopener noreferrer"
          class="menu-item support-link"
          :title="$t('footer.reportIssue')"
        >
          <i class="fa-solid fa-bug"></i>
          <span>{{ $t('footer.reportIssue') }}</span>
        </a>
        <a
          href="https://github.com/glemaitre/gravly"
          target="_blank"
          rel="noopener noreferrer"
          class="menu-item support-link"
          :title="$t('footer.githubRepo')"
        >
          <i class="fa-brands fa-github"></i>
          <span>{{ $t('footer.githubRepo') }}</span>
        </a>
        <a
          href="https://github.com/glemaitre/gravly/blob/main/README.md"
          target="_blank"
          rel="noopener noreferrer"
          class="menu-item support-link"
          :title="$t('footer.documentation')"
        >
          <i class="fa-solid fa-book"></i>
          <span>{{ $t('footer.documentation') }}</span>
        </a>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useStravaApi } from '../composables/useStravaApi'
import { useLanguageDropdown } from '../composables/useLanguageDropdown'
import { useThemeSettings } from '../composables/useThemeSettings'
import type { MessageLanguages } from '../i18n'
import stravaConnectBtn from '../assets/images/btn_strava_connect.png'

const router = useRouter()

// Strava authentication
const {
  authState,
  isLoading,
  isAuthenticated: isAuthenticatedFn,
  getAuthUrl,
  clearAuth
} = useStravaApi()

// Language dropdown functionality
const { currentLanguage, languageOptions, changeLanguage } = useLanguageDropdown()

// Theme settings functionality
const { currentTheme, themeOptions, changeTheme } = useThemeSettings()

// Computed properties
const isAuthenticated = computed(() => isAuthenticatedFn())
const athlete = computed(() => authState.value.athlete)

// Menu state
const menuOpen = ref(false)
const menuDropdown = ref<HTMLElement | null>(null)
const languageDropdownOpen = ref(false)
const themeDropdownOpen = ref(false)

function toggleMenu(event: Event) {
  event.stopPropagation()
  menuOpen.value = !menuOpen.value
}

function closeMenu(event: MouseEvent) {
  if (menuDropdown.value && !menuDropdown.value.contains(event.target as Node)) {
    menuOpen.value = false
  }
}

function toggleLanguageDropdown(event: Event) {
  event.stopPropagation()
  languageDropdownOpen.value = !languageDropdownOpen.value
  themeDropdownOpen.value = false // Close theme dropdown when opening language
}

function toggleThemeDropdown(event: Event) {
  event.stopPropagation()
  themeDropdownOpen.value = !themeDropdownOpen.value
  languageDropdownOpen.value = false // Close language dropdown when opening theme
}

// Strava authentication functions
async function handleStravaLogin() {
  try {
    const currentRoute = router.currentRoute.value.fullPath
    const authUrl = await getAuthUrl(currentRoute)
    menuOpen.value = false
    window.location.href = authUrl
  } catch (error) {
    console.error('Failed to get Strava auth URL:', error)
  }
}

function handleLogout() {
  clearAuth()
  menuOpen.value = false
  router.push('/')
}

onMounted(() => {
  document.addEventListener('click', closeMenu)
})

onUnmounted(() => {
  document.removeEventListener('click', closeMenu)
})
</script>

<style scoped>
.menu-dropdown {
  position: relative;
}

.menu-trigger {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  padding: 0;
  border: 1px solid var(--border-primary);
  border-radius: 6px;
  background: var(--bg-primary);
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 1rem;
  transition: all 0.2s ease;
}

.menu-trigger:hover {
  background: var(--bg-hover);
  border-color: var(--border-secondary);
}

.menu-trigger.active {
  background: var(--brand-50);
  border-color: var(--brand-300);
  color: var(--brand-600);
  box-shadow: 0 0 0 3px rgba(var(--brand-primary-rgb), 0.1);
}

.menu-dropdown-content {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 280px;
  background: var(--card-bg);
  border: 1px solid var(--border-primary);
  border-radius: 8px;
  box-shadow: var(--shadow-xl);
  z-index: 1000;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-8px);
  transition: all 0.2s ease;
  max-height: 80vh;
  overflow-y: auto;
}

.menu-dropdown-content.open {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.menu-section {
  padding: 0.75rem;
}

.menu-section-title {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}

.menu-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 0.875rem;
  text-align: left;
  transition: background 0.2s ease;
  text-decoration: none;
}

.menu-item:hover {
  background: var(--bg-hover);
}

.menu-item:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.menu-divider {
  margin: 0;
  border: none;
  border-top: 1px solid var(--border-primary);
}

/* Strava Login Button in Menu */
.strava-login-btn {
  padding: 0.5rem;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  width: 100%;
  display: flex;
  justify-content: center;
}

.strava-login-btn:hover {
  background: var(--bg-hover);
  border: none;
}

.strava-btn-image {
  display: block;
  height: 32px;
  width: auto;
  max-width: 100%;
}

/* User Info Section */
.user-info-section {
  width: 100%;
}

.user-info-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: var(--bg-tertiary);
  border-radius: 6px;
  margin-bottom: 0.5rem;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}

.user-icon {
  font-size: 1.5em;
  color: var(--text-tertiary);
}

.user-details {
  flex: 1;
}

.user-details .user-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.875rem;
}

.user-details .user-location {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  margin-top: 0.125rem;
}

.logout-btn {
  color: var(--status-error);
  justify-content: flex-start;
}

.logout-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  color: var(--button-danger-hover);
}

/* Settings Buttons */
.settings-button {
  justify-content: space-between;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background 0.2s ease;
  margin-bottom: 0.25rem;
  text-align: left;
  display: flex;
  align-items: center;
}

.settings-button:hover {
  background: var(--bg-hover);
}

.settings-button span {
  flex: 1;
  text-align: left;
}

.settings-chevron {
  transition: transform 0.2s ease;
  color: var(--text-tertiary);
  font-size: 0.75rem;
}

.settings-chevron.expanded {
  transform: rotate(180deg);
}

/* Settings Dropdown */
.settings-dropdown {
  margin-left: 1.5rem;
  margin-bottom: 0.5rem;
  padding-left: 1rem;
  border-left: 2px solid var(--border-primary);
}

/* Language and Theme Options */
.language-option,
.theme-option {
  justify-content: flex-start;
  margin-bottom: 0.25rem;
}

.language-option.active,
.theme-option.active {
  background: var(--brand-50);
  color: var(--brand-600);
}

.language-flag {
  font-size: 1em;
  line-height: 1;
}

.theme-icon {
  font-size: 1em;
  line-height: 1;
  width: 1em;
  text-align: center;
}

.language-name,
.theme-name {
  flex: 1;
  white-space: nowrap;
}

.checkmark {
  color: var(--brand-500);
  font-size: 0.75em;
}

/* Support Links */
.support-link {
  justify-content: flex-start;
  color: var(--text-secondary);
}

.support-link:hover {
  color: var(--brand-primary);
}

.support-link i {
  font-size: 0.875rem;
  width: 16px;
  text-align: center;
}

/* Responsive Design */
@media (max-width: 768px) {
  .menu-dropdown-content {
    width: 260px;
  }
}

@media (max-width: 480px) {
  .menu-dropdown-content {
    width: 240px;
    right: 0;
  }

  .strava-btn-image {
    height: 28px;
  }
}
</style>
