<template>
  <header class="navbar">
    <div class="navbar-container">
      <!-- Brand/Logo Section with Navigation -->
      <div class="navbar-brand">
        <router-link to="/" class="logo-link">
          <img :src="logoUrl" alt="Gravly" class="navbar-logo" />
        </router-link>

        <!-- Navigation Menu -->
        <div class="nav-menu">
          <router-link to="/explorer" class="nav-link" active-class="active">
            <i class="fa-solid fa-route"></i>
            <span>{{ $t('navbar.explorer') }}</span>
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
        <!-- Menu with Strava Authentication, Language, and Support -->
        <Menu />
      </nav>
    </div>
  </header>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import { useStravaApi } from '../composables/useStravaApi'
import { useAuthorization } from '../composables/useAuthorization'
import Menu from './Menu.vue'
import logoUrl from '../assets/images/logo.svg'

// Strava authentication (needed for editor authorization)
const { isAuthenticated: isAuthenticatedFn } = useStravaApi()

// Editor authorization
const { isAuthorizedForEditor } = useAuthorization()

// Computed properties for authentication
const isAuthenticated = computed(() => isAuthenticatedFn())
const isEditorAuthorized = computed(
  () => isAuthenticated.value && isAuthorizedForEditor.value
)
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

.logo-link {
  display: flex;
  align-items: center;
  text-decoration: none;
  transition: opacity 0.2s ease;
}

.logo-link:hover {
  opacity: 0.8;
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

/* Navigation Menu Styles - keeping only the nav menu styles */

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
  box-shadow: 0 0 0 3px rgba(var(--brand-primary-rgb), 0.1);
}

.nav-link i {
  font-size: 0.875rem;
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

  /* Responsive adjustments for menu component */
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

  /* Responsive adjustments for menu component */
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
