<template>
  <div id="app">
    <Navbar />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script lang="ts" setup>
import Navbar from './components/Navbar.vue'
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

  /* RGB values for use with rgba() */
  --brand-primary-rgb: 255, 102, 0;
  --bg-primary-rgb: 255, 255, 255;
  --bg-secondary-rgb: 248, 250, 252;
  --bg-tertiary-rgb: 241, 245, 249;

  --navbar-height: 60px;

  /* Light theme colors */
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --bg-tertiary: #f1f5f9;
  --bg-hover: #f3f4f6;
  --bg-active: #e5e7eb;

  --text-primary: #111827;
  --text-secondary: #374151;
  --text-tertiary: #6b7280;
  --text-muted: #9ca3af;

  --border-primary: #e5e7eb;
  --border-secondary: #d1d5db;
  --border-muted: #f3f4f6;

  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  --shadow-xl:
    0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);

  --card-bg: #ffffff;
  --card-border: #e5e7eb;
  --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);

  --input-bg: #ffffff;
  --input-border: #d1d5db;
  --input-border-focus: var(--brand-primary);
  --input-text: #111827;
  --input-placeholder: #9ca3af;

  --button-primary-bg: var(--brand-primary);
  --button-primary-text: #ffffff;
  --button-primary-hover: var(--brand-primary-hover);

  --button-secondary-bg: #f3f4f6;
  --button-secondary-text: #374151;
  --button-secondary-hover: #e5e7eb;

  --button-danger-bg: #dc2626;
  --button-danger-text: #ffffff;
  --button-danger-hover: #b91c1c;

  --status-success: #10b981;
  --status-warning: #f59e0b;
  --status-error: #ef4444;
  --status-info: #3b82f6;
}

/* Dark theme colors */
[data-theme='dark'] {
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-tertiary: #334155;
  --bg-hover: #475569;
  --bg-active: #64748b;

  --text-primary: #f8fafc;
  --text-secondary: #e2e8f0;
  --text-tertiary: #cbd5e1;
  --text-muted: #94a3b8;

  --border-primary: #334155;
  --border-secondary: #475569;
  --border-muted: #1e293b;

  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.3);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 10px 10px -5px rgba(0, 0, 0, 0.3);

  --card-bg: #1e293b;
  --card-border: #334155;
  --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);

  --input-bg: #1e293b;
  --input-border: #475569;
  --input-border-focus: var(--brand-primary);
  --input-text: #f8fafc;
  --input-placeholder: #64748b;

  --button-primary-bg: var(--brand-primary);
  --button-primary-text: #ffffff;
  --button-primary-hover: var(--brand-primary-hover);

  --button-secondary-bg: #334155;
  --button-secondary-text: #e2e8f0;
  --button-secondary-hover: #475569;

  --button-danger-bg: #dc2626;
  --button-danger-text: #ffffff;
  --button-danger-hover: #b91c1c;

  --status-success: #10b981;
  --status-warning: #f59e0b;
  --status-error: #ef4444;
  --status-info: #3b82f6;

  /* Dark theme RGB values */
  --bg-primary-rgb: 15, 23, 42;
  --bg-secondary-rgb: 30, 41, 59;
  --bg-tertiary-rgb: 51, 65, 85;
}

/* Global styles to prevent horizontal overflow */
* {
  box-sizing: border-box;
}

html,
body {
  margin: 0;
  padding: 0;
  min-height: 100vh;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  transition:
    background-color 0.3s ease,
    color 0.3s ease;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-primary);
  color: var(--text-primary);
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

/* Theme-aware utility classes */
.bg-primary {
  background-color: var(--bg-primary);
}
.bg-secondary {
  background-color: var(--bg-secondary);
}
.bg-tertiary {
  background-color: var(--bg-tertiary);
}
.bg-hover {
  background-color: var(--bg-hover);
}

.text-primary {
  color: var(--text-primary);
}
.text-secondary {
  color: var(--text-secondary);
}
.text-tertiary {
  color: var(--text-tertiary);
}
.text-muted {
  color: var(--text-muted);
}

.border-primary {
  border-color: var(--border-primary);
}
.border-secondary {
  border-color: var(--border-secondary);
}
.border-muted {
  border-color: var(--border-muted);
}

.shadow-sm {
  box-shadow: var(--shadow-sm);
}
.shadow-md {
  box-shadow: var(--shadow-md);
}
.shadow-lg {
  box-shadow: var(--shadow-lg);
}
.shadow-xl {
  box-shadow: var(--shadow-xl);
}

.main-content {
  flex: 1;
  padding-top: var(--navbar-height);
  min-height: calc(100vh - var(--navbar-height));
  background-color: var(--bg-primary);
}
</style>
