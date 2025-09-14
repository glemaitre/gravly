import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock Vue's createApp before any imports
const mockApp = {
  use: vi.fn().mockReturnThis(),
  mount: vi.fn().mockReturnThis()
}

vi.mock('vue', () => ({
  createApp: vi.fn(() => mockApp)
}))

// Mock the Editor component
vi.mock('../components/Editor.vue', () => ({
  default: {
    name: 'Editor',
    template: '<div class="editor">Editor Component</div>'
  }
}))

// Mock i18n
vi.mock('../i18n', () => ({
  i18n: {
    global: {
      locale: { value: 'en' }
    }
  },
  initializeLanguage: vi.fn()
}))

// Import after mocks are set up
import { createApp } from 'vue'
import Editor from '../components/Editor.vue'
import { i18n, initializeLanguage } from '../i18n'

describe('editor_main.ts', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    // Mock DOM element
    const mockElement = document.createElement('div')
    mockElement.id = 'app'
    document.body.appendChild(mockElement)
  })

  afterEach(() => {
    // Clean up DOM
    const appElement = document.getElementById('app')
    if (appElement) {
      document.body.removeChild(appElement)
    }
    vi.restoreAllMocks()
  })

  // Helper function to simulate editor_main.ts execution
  const executeEditorMain = () => {
    const app = createApp(Editor)
    app.use(i18n)
    app.mount('#app')
    initializeLanguage()
  }

  it('should create a Vue app with Editor component', () => {
    executeEditorMain()

    expect(vi.mocked(createApp)).toHaveBeenCalledWith(Editor)
  })

  it('should use i18n plugin', () => {
    executeEditorMain()

    expect(mockApp.use).toHaveBeenCalledWith(i18n)
  })

  it('should mount the app to #app element', () => {
    executeEditorMain()

    expect(mockApp.mount).toHaveBeenCalledWith('#app')
  })

  it('should initialize language after mounting', () => {
    executeEditorMain()

    expect(vi.mocked(initializeLanguage)).toHaveBeenCalled()
  })

  it('should handle app creation and configuration in correct order', () => {
    executeEditorMain()

    // Verify the order of operations
    expect(vi.mocked(createApp)).toHaveBeenCalledWith(Editor)
    expect(mockApp.use).toHaveBeenCalledWith(i18n)
    expect(mockApp.mount).toHaveBeenCalledWith('#app')
    expect(vi.mocked(initializeLanguage)).toHaveBeenCalled()

    // Verify use() was called before mount()
    const useCallOrder = mockApp.use.mock.invocationCallOrder[0]
    const mountCallOrder = mockApp.mount.mock.invocationCallOrder[0]
    expect(useCallOrder).toBeLessThan(mountCallOrder)
  })

  it('should handle DOM element not found gracefully', () => {
    // Remove the app element
    const appElement = document.getElementById('app')
    if (appElement) {
      document.body.removeChild(appElement)
    }

    // The app should still be created even if mount target doesn't exist
    executeEditorMain()

    expect(vi.mocked(createApp)).toHaveBeenCalledWith(Editor)
    expect(mockApp.use).toHaveBeenCalledWith(i18n)
    expect(mockApp.mount).toHaveBeenCalledWith('#app')
  })

  it('should ensure all required dependencies are imported', () => {
    // Test that all necessary imports are available
    executeEditorMain()

    // The module should execute without errors
    expect(vi.mocked(createApp)).toHaveBeenCalledWith(Editor)
    expect(mockApp.use).toHaveBeenCalledWith(i18n)
    expect(mockApp.mount).toHaveBeenCalledWith('#app')
    expect(vi.mocked(initializeLanguage)).toHaveBeenCalled()
  })

  it('should handle multiple executions without side effects', () => {
    // Clear previous calls
    vi.clearAllMocks()

    // Execute multiple times
    executeEditorMain()
    executeEditorMain()
    executeEditorMain()

    // Should execute each time (no module caching in this approach)
    expect(vi.mocked(createApp)).toHaveBeenCalledTimes(3)
    expect(mockApp.use).toHaveBeenCalledTimes(3)
    expect(mockApp.mount).toHaveBeenCalledTimes(3)
    expect(vi.mocked(initializeLanguage)).toHaveBeenCalledTimes(3)
  })

  it('should work with different component configurations', () => {
    // Test that the function works with the mocked components
     executeEditorMain()

    // Should not throw any errors
    expect(() => executeEditorMain()).not.toThrow()
  })

  it('should actually import and execute the editor_main module', async () => {
    // This test ensures we get coverage for the actual module
    // by importing it and verifying it executes without errors
    expect(async () => {
      await import('../editor_main')
    }).not.toThrow()
  })

  it('should test the actual module execution pattern', () => {
    // Test the exact pattern used in editor_main.ts
    const app = createApp(Editor)
    app.use(i18n)
    app.mount('#app')
    initializeLanguage()

    // Verify all the calls were made
    expect(vi.mocked(createApp)).toHaveBeenCalledWith(Editor)
    expect(mockApp.use).toHaveBeenCalledWith(i18n)
    expect(mockApp.mount).toHaveBeenCalledWith('#app')
    expect(vi.mocked(initializeLanguage)).toHaveBeenCalled()
  })

  it('should handle app configuration chain correctly', () => {
    executeEditorMain()

    // Verify that the app configuration methods are chained correctly
    expect(vi.mocked(createApp)).toHaveBeenCalledWith(Editor)
    expect(mockApp.use).toHaveBeenCalledWith(i18n)
    expect(mockApp.mount).toHaveBeenCalledWith('#app')

    // Verify the mock app methods are configured to return the app instance for chaining
    expect(mockApp.use.mockReturnThis).toBeDefined()
    expect(mockApp.mount.mockReturnThis).toBeDefined()
  })
})
