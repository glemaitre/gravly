<template>
  <div id="app">
    <nav class="navbar">
      <div class="nav-container">
        <h1 class="nav-title"><i class="fa-solid fa-person-biking" aria-hidden="true"></i> Cycling Routes</h1>
        <router-link to="/" class="nav-link">Home</router-link>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script>
export default {
  name: 'App'
}
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

  --brand-gradient: linear-gradient(135deg, var(--brand-500) 0%, var(--brand-400) 20%, var(--brand-300) 45%, var(--brand-200) 70%, var(--brand-100) 100%);

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

html, body {
  overflow-x: hidden;
  max-width: 100vw;
}

#app {
  min-height: 100vh;
  background: var(--brand-bg);
  overflow-x: hidden;
}

/* Reusable brand utilities */
.bg-brand-gradient { background: var(--brand-gradient); }
.text-brand { color: var(--brand-primary); }
.border-brand { border-color: var(--brand-primary); }
.btn-brand { background: var(--brand-primary); color: #fff; }
.btn-brand:hover { background: var(--brand-primary-hover); }

.navbar {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
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
</style>
