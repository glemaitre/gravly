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

.main-content {
  min-height: calc(100vh - 80px);
}
</style>
