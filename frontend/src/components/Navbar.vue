<template>
  <header class="navbar">
    <div class="navbar-container">
      <!-- Brand/Logo Section with Navigation -->
      <div class="navbar-brand">
        <img :src="logoUrl" alt="Cycling Segments" class="navbar-logo" />

        <!-- Navigation Menu -->
        <div class="nav-menu">
          <router-link to="/" class="nav-link" active-class="active">
            <i class="fa-solid fa-route"></i>
            <span>{{ $t('navbar.home') }}</span>
          </router-link>
          <router-link to="/route-planner" class="nav-link" active-class="active">
            <i class="fa-solid fa-map"></i>
            <span>{{ $t('navbar.routePlanner') }}</span>
          </router-link>
          <router-link
            v-if="isEditorAuthorized"
            to="/editor"
            class="nav-link"
            active-class="active"
          >
            <i class="fa-solid fa-edit"></i>
            <span>{{ $t('navbar.editor') }}</span>
          </router-link>
        </div>
      </div>

      <!-- Right Section -->
      <nav class="navbar-nav">
        <!-- Strava Authentication -->
        <div class="auth-section">
          <button
            v-if="!isAuthenticated"
            class="strava-login-btn navbar-btn"
            @click="handleStravaLogin"
            :disabled="isLoading"
          >
            <i class="fab fa-strava"></i>
            <span>{{ $t('navbar.login') }}</span>
          </button>

          <div v-else class="strava-user-dropdown" ref="userDropdown">
            <button
              class="strava-user-btn navbar-btn"
              @click="toggleUserDropdown"
              :class="{ active: userDropdownOpen }"
            >
              <img
                v-if="athlete?.profile_medium"
                :src="athlete.profile_medium"
                :alt="athlete.firstname"
                class="user-avatar"
              />
              <i v-else class="fas fa-user-circle user-icon"></i>
              <span class="user-name">{{ athlete?.firstname || 'User' }}</span>
              <span class="dropdown-arrow">
                <i
                  class="fa-solid fa-chevron-down"
                  :class="{ rotated: userDropdownOpen }"
                ></i>
              </span>
            </button>

            <div
              class="user-dropdown-menu navbar-menu"
              :class="{ open: userDropdownOpen }"
            >
              <div class="user-info">
                <div class="user-name">
                  {{ athlete?.firstname }} {{ athlete?.lastname }}
                </div>
                <div class="user-location" v-if="athlete?.city">
                  {{ athlete.city }}, {{ athlete.country }}
                </div>
              </div>
              <hr class="dropdown-divider" />
              <button class="user-option logout-option" @click="handleLogout">
                <i class="fas fa-sign-out-alt"></i>
                <span>{{ $t('navbar.logout') }}</span>
              </button>
            </div>
          </div>
        </div>

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
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { setLanguage, type MessageLanguages } from '../i18n'
import { useStravaApi } from '../composables/useStravaApi'
import { useAuthorization } from '../composables/useAuthorization'
import logoUrl from '../assets/images/logo.svg'

// i18n setup
const { locale } = useI18n()
const router = useRouter()
const currentLanguage = ref<MessageLanguages>('en')

// Strava authentication
const {
  authState,
  isLoading,
  isAuthenticated: isAuthenticatedFn,
  getAuthUrl,
  clearAuth
} = useStravaApi()

// Editor authorization
const { isAuthorizedForEditor } = useAuthorization()

// Computed properties for authentication
const isAuthenticated = computed(() => isAuthenticatedFn())
const athlete = computed(() => authState.value.athlete)
const isEditorAuthorized = computed(
  () => isAuthenticated.value && isAuthorizedForEditor.value
)

// Watch for locale changes to update currentLanguage
watch(
  locale,
  (newLocale) => {
    currentLanguage.value = newLocale as MessageLanguages
  },
  { immediate: true }
)

// Watch for authentication state changes (for debugging if needed)
// watch(
//   authState,
//   (newAuthState) => {
//     console.debug('Navbar authState changed:', newAuthState)
//   },
//   { deep: true }
// )

// Language dropdown state
const languageDropdownOpen = ref(false)

// User dropdown state
const userDropdownOpen = ref(false)

// Language options with flags
const languageOptions = {
  en: { flag: '🇺🇸', name: 'English' },
  fr: { flag: '🇫🇷', name: 'Français' }
}

// Close dropdown when clicking outside
const languageDropdown = ref<HTMLElement | null>(null)
const userDropdown = ref<HTMLElement | null>(null)

function closeLanguageDropdown(event: MouseEvent) {
  if (
    languageDropdown.value &&
    !languageDropdown.value.contains(event.target as Node)
  ) {
    languageDropdownOpen.value = false
  }
}

function closeUserDropdown(event: MouseEvent) {
  if (userDropdown.value && !userDropdown.value.contains(event.target as Node)) {
    userDropdownOpen.value = false
  }
}

function closeDropdowns(event: MouseEvent) {
  closeLanguageDropdown(event)
  closeUserDropdown(event)
}

// Toggle dropdown function that prevents event bubbling
function toggleLanguageDropdown(event: Event) {
  event.stopPropagation()
  languageDropdownOpen.value = !languageDropdownOpen.value
  userDropdownOpen.value = false // Close user dropdown when opening language
}

function toggleUserDropdown(event: Event) {
  event.stopPropagation()
  userDropdownOpen.value = !userDropdownOpen.value
  languageDropdownOpen.value = false // Close language dropdown when opening user
}

// Language switching function
function changeLanguage(lang: MessageLanguages) {
  currentLanguage.value = lang
  setLanguage(lang)
  languageDropdownOpen.value = false // Close dropdown after selection
}

// Strava authentication functions
async function handleStravaLogin() {
  try {
    // Store the current route so we can redirect back after authentication
    const currentRoute = router.currentRoute.value.fullPath
    const authUrl = await getAuthUrl(currentRoute)

    window.location.href = authUrl
  } catch (error) {
    console.error('Failed to get Strava auth URL:', error)
  }
}

function handleLogout() {
  clearAuth()
  userDropdownOpen.value = false
  // Redirect to home page after logout
  router.push('/')
}

onMounted(() => {
  document.addEventListener('click', closeDropdowns)
})

onUnmounted(() => {
  document.removeEventListener('click', closeDropdowns)
})
</script>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  width: 100%;
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
  gap: 0.75rem;
}

/* Authentication Section */
.auth-section {
  display: flex;
  align-items: center;
}

.navbar-btn {
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

.navbar-btn:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

.navbar-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Strava Login Button */
.strava-login-btn {
  background: linear-gradient(135deg, #fc4c02 0%, #ff6b35 100%);
  color: white;
  border-color: #fc4c02;
}

.strava-login-btn:hover {
  background: linear-gradient(135deg, #e63e00 0%, #ff5a2b 100%);
  border-color: #e63e00;
  color: white;
}

.strava-login-btn i {
  font-size: 1.1em;
}

/* User Dropdown */
.strava-user-dropdown {
  position: relative;
}

.strava-user-btn {
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

.strava-user-btn:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

.strava-user-btn.active {
  background: var(--brand-50);
  border-color: var(--brand-300);
  color: var(--brand-600);
  box-shadow: 0 0 0 3px rgba(255, 102, 0, 0.1);
}

.user-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  object-fit: cover;
}

.user-icon {
  font-size: 1.2em;
  color: #6b7280;
}

.user-name {
  font-weight: 500;
}

/* User Dropdown Menu */
.user-dropdown-menu {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  left: auto;
  transform-origin: top right;
  width: 220px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-8px);
  transition: all 0.2s ease;
}

.user-dropdown-menu.open {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.user-info {
  padding: 0.75rem;
}

.user-info .user-name {
  font-weight: 600;
  color: #111827;
  margin-bottom: 0.25rem;
}

.user-location {
  font-size: 0.75rem;
  color: #6b7280;
}

.dropdown-divider {
  margin: 0;
  border: none;
  border-top: 1px solid #e5e7eb;
}

.user-option {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border: none;
  background: transparent;
  cursor: pointer;
  color: #374151;
  font-size: 0.875rem;
  text-align: left;
  transition: background 0.2s ease;
}

.user-option:hover {
  background: #f3f4f6;
}

.logout-option {
  color: #dc2626;
}

.logout-option:hover {
  background: #fef2f2;
  color: #b91c1c;
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

.language-dropdown {
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
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-8px);
  transition: all 0.2s ease;
  min-width: 140px;
}

.language-dropdown-menu.navbar-menu {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: auto;
  transform-origin: top left;
  width: 100%;
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

  .navbar-btn {
    padding: 0.4rem 0.6rem;
    font-size: 0.85rem;
  }

  .strava-login-btn span {
    display: none;
  }

  .strava-user-btn .user-name {
    display: none;
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

  .navbar-btn {
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
