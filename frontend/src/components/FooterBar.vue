<template>
  <footer class="footer-bar">
    <div class="footer-container">
      <!-- Left side - Language dropdown (flag only when folded) -->
      <div class="footer-left">
        <div class="language-dropdown" ref="languageDropdown">
          <button
            class="language-dropdown-trigger"
            @click="toggleLanguageDropdown"
            :class="{ active: languageDropdownOpen }"
            :title="languageOptions[currentLanguage].name"
          >
            <span class="language-flag">{{
              languageOptions[currentLanguage].flag
            }}</span>
            <span class="dropdown-arrow">
              <i
                class="fa-solid fa-chevron-down"
                :class="{ rotated: languageDropdownOpen }"
              ></i>
            </span>
          </button>
          <div class="language-dropdown-menu" :class="{ open: languageDropdownOpen }">
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

      <!-- Right side - Links with tooltips -->
      <div class="footer-right">
        <a
          href="https://github.com/glemaitre/gravly/issues"
          target="_blank"
          rel="noopener noreferrer"
          class="footer-link"
          :title="$t('footer.reportIssue')"
        >
          <i class="fa-solid fa-bug"></i>
        </a>
        <a
          href="https://github.com/glemaitre/gravly"
          target="_blank"
          rel="noopener noreferrer"
          class="footer-link"
          :title="$t('footer.githubRepo')"
        >
          <i class="fa-brands fa-github"></i>
        </a>
        <a
          href="https://github.com/glemaitre/gravly/blob/main/README.md"
          target="_blank"
          rel="noopener noreferrer"
          class="footer-link"
          :title="$t('footer.documentation')"
        >
          <i class="fa-solid fa-book"></i>
        </a>
      </div>
    </div>
  </footer>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useLanguageDropdown } from '../composables/useLanguageDropdown'
import type { MessageLanguages } from '../i18n'

const {
  currentLanguage,
  languageDropdownOpen,
  languageOptions,
  toggleLanguageDropdown,
  changeLanguage,
  closeLanguageDropdown
} = useLanguageDropdown()

const languageDropdown = ref<HTMLElement | null>(null)

function handleClickOutside(event: MouseEvent) {
  closeLanguageDropdown(event, languageDropdown.value)
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.footer-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  width: 100%;
  z-index: 9998;
  background: #ffffff;
  border-top: 1px solid #e5e7eb;
  box-shadow:
    0 -1px 3px 0 rgba(0, 0, 0, 0.1),
    0 -1px 2px 0 rgba(0, 0, 0, 0.06);
  min-height: var(--footer-height);
}

.footer-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0.1rem 1.5rem;
  min-height: var(--footer-height);
  box-sizing: border-box;
}

.footer-left,
.footer-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.footer-right {
  margin-left: auto;
}

/* Language Dropdown Styles */
.language-dropdown {
  position: relative;
}

.language-dropdown-trigger {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  background: #ffffff;
  cursor: pointer;
  color: #374151;
  font-size: 0.75rem;
  text-align: left;
  transition: all 0.2s ease;
  white-space: nowrap;
  min-width: 40px;
  justify-content: center;
}

.language-dropdown-trigger:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

.language-dropdown-trigger.active {
  background: var(--brand-50);
  border-color: var(--brand-300);
  color: var(--brand-600);
  box-shadow: 0 0 0 2px rgba(var(--brand-primary-rgb), 0.1);
}

.language-flag {
  font-size: 1em;
  line-height: 1;
}

.dropdown-arrow {
  font-size: 0.625em;
  transition: transform 0.2s ease;
  opacity: 0.7;
}

.dropdown-arrow .fa-chevron-down.rotated {
  transform: rotate(180deg);
}

.language-dropdown-menu {
  position: absolute;
  bottom: calc(100% + 4px);
  left: 0;
  right: auto;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  opacity: 0;
  visibility: hidden;
  transform: translateY(4px);
  transition: all 0.2s ease;
  min-width: 120px;
  transform-origin: bottom left;
}

.language-dropdown-menu.open {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.language-option {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.5rem;
  border: none;
  background: transparent;
  cursor: pointer;
  color: #111827;
  font-size: 0.75rem;
  text-align: left;
  transition: background 0.2s ease;
}

.language-option:first-child {
  border-top-left-radius: 5px;
  border-top-right-radius: 5px;
}

.language-option:last-child {
  border-bottom-left-radius: 5px;
  border-bottom-right-radius: 5px;
}

.language-option:hover {
  background: #f9fafb;
}

.language-option.active {
  background: var(--brand-50);
  color: var(--brand-600);
}

.language-name {
  flex: 1;
  white-space: nowrap;
}

.checkmark {
  color: var(--brand-500);
  font-size: 0.75em;
}

/* Footer Links */
.footer-link {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  color: #6b7280;
  text-decoration: none;
  border-radius: 4px;
  transition: all 0.2s ease;
  font-size: 0.875rem;
}

.footer-link:hover {
  background: #f3f4f6;
  color: var(--brand-500);
  transform: translateY(-1px);
}

/* Responsive Design */
@media (max-width: 768px) {
  .footer-container {
    padding: 0.375rem 1rem;
  }

  .footer-left,
  .footer-right {
    gap: 0.5rem;
  }

  .language-dropdown-trigger {
    padding: 0.25rem 0.375rem;
    font-size: 0.6875rem;
    min-width: 36px;
  }

  .footer-link {
    width: 28px;
    height: 28px;
    font-size: 0.75rem;
  }
}

@media (max-width: 480px) {
  .footer-container {
    padding: 0.25rem 0.75rem;
  }
}
</style>
