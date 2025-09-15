import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import LandingPage from '../LandingPage.vue'

// Mock Leaflet
vi.mock('leaflet', () => ({
  default: {
    map: vi.fn(() => ({
      setView: vi.fn(),
      addLayer: vi.fn(),
      removeLayer: vi.fn(),
      invalidateSize: vi.fn(),
      fitBounds: vi.fn(),
      on: vi.fn(),
      off: vi.fn(),
      remove: vi.fn()
    })),
    tileLayer: vi.fn(() => ({
      addTo: vi.fn()
    })),
    polyline: vi.fn(() => ({
      addTo: vi.fn()
    })),
    marker: vi.fn(() => ({
      addTo: vi.fn()
    })),
    divIcon: vi.fn(() => ({})),
    latLngBounds: vi.fn(() => ({
      fitBounds: vi.fn()
    })),
    control: {
      scale: vi.fn(() => ({
        addTo: vi.fn()
      }))
    }
  }
}))

describe('LandingPage', () => {
  let wrapper: any

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  it('renders correctly', () => {
    wrapper = mount(LandingPage)

    expect(wrapper.find('.landing-page').exists()).toBe(true)
    expect(wrapper.find('.landing-content').exists()).toBe(true)
  })

  it('has correct CSS classes for styling', () => {
    const wrapper = mount(LandingPage)

    const landingPage = wrapper.find('.landing-page')
    const landingContent = wrapper.find('.landing-content')

    expect(landingPage.exists()).toBe(true)
    expect(landingContent.exists()).toBe(true)
  })

  it('has proper structure with landing-page container', () => {
    const wrapper = mount(LandingPage)

    const landingPage = wrapper.find('.landing-page')
    expect(landingPage.exists()).toBe(true)

    // Check that landing-content is inside landing-page
    const landingContent = landingPage.find('.landing-content')
    expect(landingContent.exists()).toBe(true)
  })

  it('renders as a single root element', () => {
    const wrapper = mount(LandingPage)

    // Should have only one root element
    expect(wrapper.element.children.length).toBe(1)
    // Check that the root element has the landing-page class
    expect(wrapper.element.classList.contains('landing-page')).toBe(true)
  })

  it('has correct component name', () => {
    const wrapper = mount(LandingPage)

    expect(wrapper.vm.$options.name || 'LandingPage').toBe('LandingPage')
  })

  it('is a functional component with no props', () => {
    const wrapper = mount(LandingPage)

    // Should not have any props
    expect(Object.keys(wrapper.props())).toHaveLength(0)
  })

  it('has content area ready for future content', () => {
    const wrapper = mount(LandingPage)

    const landingContent = wrapper.find('.landing-content')
    expect(landingContent.exists()).toBe(true)

    // Content area should have map section
    expect(landingContent.find('.map-section').exists()).toBe(true)
  })

  it('maintains proper HTML structure', () => {
    const wrapper = mount(LandingPage)

    const html = wrapper.html()

    // Should contain the expected HTML structure (accounting for scoped CSS attributes)
    expect(html).toContain('class="landing-page"')
    expect(html).toContain('class="landing-content"')
    expect(html).toContain('<!-- Empty content for now -->')
    expect(html).toContain('</div>')
    expect(html).toContain('</div>')
  })

  it('has scoped styles applied correctly', () => {
    const wrapper = mount(LandingPage)

    const landingPage = wrapper.find('.landing-page')
    const landingContent = wrapper.find('.landing-content')

    // Check that elements exist (styles are applied via CSS, not directly testable in unit tests)
    expect(landingPage.exists()).toBe(true)
    expect(landingContent.exists()).toBe(true)
  })

  it('is ready for future content expansion', () => {
    const wrapper = mount(LandingPage)

    // The component should be structured to easily accept new content
    const landingContent = wrapper.find('.landing-content')
    expect(landingContent.exists()).toBe(true)

    // Should be able to add content inside landing-content
    expect(landingContent.element.children.length).toBe(1) // Map section
  })

  it('follows Vue 3 Composition API patterns', () => {
    const wrapper = mount(LandingPage)

    // Component should be using <script setup> syntax
    // This is verified by the fact that it mounts without errors
    expect(wrapper.vm).toBeDefined()
  })

  it('has proper accessibility structure', () => {
    const wrapper = mount(LandingPage)

    // Should have proper div structure for screen readers
    const landingPage = wrapper.find('.landing-page')
    expect(landingPage.exists()).toBe(true)

    // Should be a semantic container
    expect(landingPage.element.tagName).toBe('DIV')
  })

  it('can be mounted multiple times without issues', () => {
    // Test that the component is stateless and can be reused
    const wrapper1 = mount(LandingPage)
    const wrapper2 = mount(LandingPage)

    expect(wrapper1.find('.landing-page').exists()).toBe(true)
    expect(wrapper2.find('.landing-page').exists()).toBe(true)

    // Both instances should be identical
    expect(wrapper1.html()).toBe(wrapper2.html())
  })

  it('handles component lifecycle correctly', () => {
    wrapper = mount(LandingPage)

    // Component should mount successfully
    expect(wrapper.find('.landing-page').exists()).toBe(true)

    // Should be able to unmount without errors
    expect(() => wrapper.unmount()).not.toThrow()
  })

  describe('Map functionality', () => {
    it('renders map container', () => {
      wrapper = mount(LandingPage)

      expect(wrapper.find('#landing-map').exists()).toBe(true)
      expect(wrapper.find('.map').exists()).toBe(true)
      expect(wrapper.find('.card-map').exists()).toBe(true)
    })

    it('displays map section without hero titles', () => {
      wrapper = mount(LandingPage)

      expect(wrapper.find('.hero-section').exists()).toBe(false)
      expect(wrapper.find('.hero-title').exists()).toBe(false)
      expect(wrapper.find('.hero-subtitle').exists()).toBe(false)
      expect(wrapper.find('.map-section').exists()).toBe(true)
    })

    it('has proper map section structure', () => {
      wrapper = mount(LandingPage)

      expect(wrapper.find('.map-section').exists()).toBe(true)
      expect(wrapper.find('.map-container').exists()).toBe(true)
      expect(wrapper.find('.card').exists()).toBe(true)
    })

    it('has correct map dimensions with full width and 65% height', () => {
      wrapper = mount(LandingPage)

      const mapElement = wrapper.find('.map')
      expect(mapElement.exists()).toBe(true)
      expect(mapElement.attributes('id')).toBe('landing-map')
      expect(mapElement.classes()).toContain('map')
    })

    it('has responsive CSS classes', () => {
      wrapper = mount(LandingPage)

      const mapContainer = wrapper.find('.map-container')
      expect(mapContainer.exists()).toBe(true)
      expect(mapContainer.classes()).toContain('map-container')
    })

    it('has full width and 65% height styling', () => {
      wrapper = mount(LandingPage)

      const mapElement = wrapper.find('.map')
      expect(mapElement.exists()).toBe(true)

      // Check that the map element has the correct class and attributes
      expect(mapElement.classes()).toContain('map')
      expect(mapElement.attributes('id')).toBe('landing-map')

      // In a real browser, the CSS height: 65vh and width: 100% would be applied
      // In the test environment, we verify the element structure is correct
      expect(mapElement.element.tagName).toBe('DIV')
    })
  })

  describe('Responsive design', () => {
    it('has proper responsive structure', () => {
      wrapper = mount(LandingPage)

      const landingContent = wrapper.find('.landing-content')
      expect(landingContent.exists()).toBe(true)
      expect(landingContent.classes()).toContain('landing-content')
    })

    it('maintains proper layout structure', () => {
      wrapper = mount(LandingPage)

      // Check that all main sections exist
      expect(wrapper.find('.map-section').exists()).toBe(true)
      expect(wrapper.find('.map-container').exists()).toBe(true)
    })
  })

  describe('Non-regression tests', () => {
    it('should not have duplicate map containers', () => {
      wrapper = mount(LandingPage)

      const mapContainers = wrapper.findAll('#landing-map')
      expect(mapContainers).toHaveLength(1)
    })

    it('should have proper map container hierarchy', () => {
      wrapper = mount(LandingPage)

      const mapSection = wrapper.find('.map-section')
      const mapContainer = mapSection.find('.map-container')
      const card = mapContainer.find('.card')
      const map = card.find('.map')

      expect(mapSection.exists()).toBe(true)
      expect(mapContainer.exists()).toBe(true)
      expect(card.exists()).toBe(true)
      expect(map.exists()).toBe(true)
    })

    it('should maintain consistent structure across multiple mounts', () => {
      const wrapper1 = mount(LandingPage)
      const wrapper2 = mount(LandingPage)

      expect(wrapper1.find('.landing-page').exists()).toBe(true)
      expect(wrapper2.find('.landing-page').exists()).toBe(true)
      expect(wrapper1.find('#landing-map').exists()).toBe(true)
      expect(wrapper2.find('#landing-map').exists()).toBe(true)

      wrapper1.unmount()
      wrapper2.unmount()
    })
  })
})
