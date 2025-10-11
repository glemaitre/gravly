import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createRouter, createMemoryHistory, Router } from 'vue-router'
import { createI18n } from 'vue-i18n'
import Landing from '../components/Landing.vue'
import en from '../i18n/locales/en'

// Mock the logo import
vi.mock('../assets/images/logo.svg', () => ({
  default: 'mocked-logo.svg'
}))

describe('Landing', () => {
  let wrapper: VueWrapper
  let router: Router

  beforeEach(async () => {
    // Create router with memory history
    router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', component: Landing },
        { path: '/explorer', component: { template: '<div>Explorer</div>' } },
        { path: '/route-planner', component: { template: '<div>Route Planner</div>' } }
      ]
    })

    // Create i18n instance
    const i18n = createI18n({
      legacy: false,
      locale: 'en',
      messages: { en }
    })

    // Mount component with router and i18n
    wrapper = mount(Landing, {
      global: {
        plugins: [router, i18n]
      }
    })

    // Wait for router to be ready
    await router.isReady()
  })

  it('renders the landing page', () => {
    expect(wrapper.exists()).toBe(true)
  })

  it('displays the Gravly logo in hero section', () => {
    const heroLogo = wrapper.find('.hero-logo')
    expect(heroLogo.exists()).toBe(true)
    expect(heroLogo.attributes('alt')).toBe('Gravly')
    // The src will be a module path from Vite
    expect(heroLogo.attributes('src')).toBeTruthy()
  })

  it('displays the hero subtitle', () => {
    const subtitle = wrapper.find('.hero-subtitle')
    expect(subtitle.exists()).toBe(true)
    expect(subtitle.text()).toContain('Plan gravel routes with confidence')
  })

  it('displays call-to-action buttons', () => {
    const buttons = wrapper.findAll('.btn')
    expect(buttons.length).toBe(2)
    expect(buttons[0].text()).toContain('Explore Segments')
    expect(buttons[1].text()).toContain('Plan a Route')
  })

  it('has correct links for CTA buttons', () => {
    const buttons = wrapper.findAll('.btn')
    expect(buttons[0].attributes('href')).toBe('/explorer')
    expect(buttons[1].attributes('href')).toBe('/route-planner')
  })

  it('displays the problem section', () => {
    const problemSection = wrapper.find('.problem-section')
    expect(problemSection.exists()).toBe(true)

    const problemTitle = wrapper.find('.problem-section .section-title')
    expect(problemTitle.text()).toBe("We've All Been There")

    const problemDescription = wrapper.find('.problem-description')
    expect(problemDescription.exists()).toBe(true)
    expect(problemDescription.text()).toContain('pushing your bike')
    expect(problemDescription.text()).toContain('guesswork')
  })

  it('displays the features section', () => {
    const featuresSection = wrapper.find('.features')
    expect(featuresSection.exists()).toBe(true)

    const sectionTitle = wrapper.find('.features .section-title')
    expect(sectionTitle.text()).toBe('Why Gravly?')
  })

  it('displays three feature cards', () => {
    const featureCards = wrapper.findAll('.feature-card')
    expect(featureCards.length).toBe(3)
  })

  it('displays feature titles', () => {
    const featureTitles = wrapper.findAll('.feature-title')
    expect(featureTitles.length).toBe(3)
    expect(featureTitles[0].text()).toBe('Real Gravel Intelligence')
    expect(featureTitles[1].text()).toBe('Plan With Precision')
    expect(featureTitles[2].text()).toBe('Save & Share Your Routes')
  })

  it('displays feature descriptions', () => {
    const featureDescriptions = wrapper.findAll('.feature-description')
    expect(featureDescriptions.length).toBe(3)
    expect(featureDescriptions[0].text()).toContain('No more surprises')
    expect(featureDescriptions[1].text()).toContain('You stay in control')
    expect(featureDescriptions[2].text()).toContain('rides you can trust')
  })

  it('displays feature icons', () => {
    const featureIcons = wrapper.findAll('.feature-icon')
    expect(featureIcons.length).toBe(3)

    const icons = wrapper.findAll('.feature-icon i')
    expect(icons[0].classes()).toContain('fa-route')
    expect(icons[1].classes()).toContain('fa-map-marked-alt')
    expect(icons[2].classes()).toContain('fa-share-alt')
  })

  it('has proper structure with hero, problem, and features sections', () => {
    const landingPage = wrapper.find('.landing-page')
    expect(landingPage.exists()).toBe(true)

    const hero = landingPage.find('.hero')
    const problem = landingPage.find('.problem-section')
    const features = landingPage.find('.features')

    expect(hero.exists()).toBe(true)
    expect(problem.exists()).toBe(true)
    expect(features.exists()).toBe(true)
  })
})
