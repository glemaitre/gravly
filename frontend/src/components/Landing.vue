<template>
  <div class="landing-page">
    <section class="hero">
      <div class="hero-content">
        <img :src="logoUrl" alt="Gravly" class="hero-logo" />
        <p class="hero-subtitle">
          {{ $t('landing.subtitle') }}
        </p>
        <div class="hero-actions">
          <router-link to="/explorer" class="btn btn-primary">
            <i class="fa-solid fa-route"></i>
            <span>{{ $t('landing.exploreSegments') }}</span>
          </router-link>
          <router-link to="/route-planner" class="btn btn-secondary">
            <i class="fa-solid fa-map"></i>
            <span>{{ $t('landing.planRoute') }}</span>
          </router-link>
        </div>
      </div>
    </section>

    <section class="problem-section">
      <div class="problem-container">
        <h2 class="section-title">{{ $t('landing.problemTitle') }}</h2>
        <p class="problem-description">{{ $t('landing.problemDescription') }}</p>
      </div>
    </section>

    <section class="features">
      <div class="features-container">
        <h2 class="section-title">{{ $t('landing.whyGravly') }}</h2>
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon">
              <i class="fa-solid fa-route"></i>
            </div>
            <h3 class="feature-title">{{ $t('landing.feature1Title') }}</h3>
            <p class="feature-description">{{ $t('landing.feature1Description') }}</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">
              <i class="fa-solid fa-map-marked-alt"></i>
            </div>
            <h3 class="feature-title">{{ $t('landing.feature2Title') }}</h3>
            <p class="feature-description">{{ $t('landing.feature2Description') }}</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">
              <i class="fa-solid fa-share-alt"></i>
            </div>
            <h3 class="feature-title">{{ $t('landing.feature3Title') }}</h3>
            <p class="feature-description">{{ $t('landing.feature3Description') }}</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script lang="ts" setup>
import logoUrl from '../assets/images/logo.svg'
</script>

<style scoped>
.landing-page {
  min-height: calc(100vh - var(--navbar-height));
  display: flex;
  flex-direction: column;
}

/* Hero Section */
.hero {
  background: var(--brand-gradient);
  color: white;
  padding: 4rem 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.hero-content {
  max-width: 800px;
  text-align: center;
}

.hero-logo {
  max-width: 400px;
  width: 100%;
  height: auto;
  margin: 0 auto 2rem auto;
  display: block;
  filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1));
}

.hero-subtitle {
  font-size: 1.25rem;
  margin: 0 0 2rem 0;
  opacity: 0.95;
  line-height: 1.6;
}

.hero-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.875rem 1.75rem;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
  font-size: 1rem;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.btn i {
  font-size: 1.1em;
}

.btn-primary {
  background: white;
  color: var(--brand-primary);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  background: #f9fafb;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 2px solid white;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

/* Problem Section */
.problem-section {
  padding: 4rem 2rem;
  background: white;
  border-bottom: 1px solid #e5e7eb;
}

.problem-container {
  max-width: 900px;
  margin: 0 auto;
  text-align: center;
}

.problem-description {
  font-size: 1.125rem;
  line-height: 1.75;
  color: #4b5563;
  margin: 1.5rem 0 0 0;
}

/* Features Section */
.features {
  padding: 4rem 2rem;
  background: #f9fafb;
}

.features-container {
  max-width: 1200px;
  margin: 0 auto;
}

.section-title {
  font-size: 2.25rem;
  font-weight: 700;
  text-align: center;
  margin: 0 0 3rem 0;
  color: #111827;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
}

.feature-card {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.feature-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  background: var(--brand-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.5rem;
  color: white;
  font-size: 1.75rem;
}

.feature-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
  color: #111827;
}

.feature-description {
  font-size: 1rem;
  line-height: 1.6;
  margin: 0;
  color: #6b7280;
}

/* Responsive Design */
@media (max-width: 768px) {
  .hero {
    padding: 3rem 1.5rem;
    min-height: 300px;
  }

  .hero-logo {
    max-width: 300px;
    margin-bottom: 1.5rem;
  }

  .hero-subtitle {
    font-size: 1rem;
  }

  .btn {
    padding: 0.75rem 1.5rem;
    font-size: 0.9rem;
  }

  .problem-section {
    padding: 3rem 1.5rem;
  }

  .problem-description {
    font-size: 1rem;
    line-height: 1.6;
  }

  .features {
    padding: 3rem 1.5rem;
  }

  .section-title {
    font-size: 1.75rem;
    margin-bottom: 2rem;
  }

  .features-grid {
    gap: 1.5rem;
  }

  .feature-card {
    padding: 1.5rem;
  }

  .feature-icon {
    width: 56px;
    height: 56px;
    font-size: 1.5rem;
  }

  .feature-title {
    font-size: 1.25rem;
  }
}

@media (max-width: 480px) {
  .hero-logo {
    max-width: 250px;
    margin-bottom: 1rem;
  }

  .hero-actions {
    flex-direction: column;
    width: 100%;
  }

  .btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
