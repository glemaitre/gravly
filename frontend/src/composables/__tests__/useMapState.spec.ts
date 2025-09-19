import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useMapState, type MapState } from '../useMapState'

// Mock Leaflet
const mockMapInstance = {
  getCenter: vi.fn(() => ({ lat: 45.764, lng: 4.8357 })),
  getZoom: vi.fn(() => 12),
  getBounds: vi.fn(() => ({
    getNorth: vi.fn(() => 46.0),
    getSouth: vi.fn(() => 45.5),
    getEast: vi.fn(() => 5.0),
    getWest: vi.fn(() => 4.5)
  })),
  setView: vi.fn(),
  fitBounds: vi.fn(),
  invalidateSize: vi.fn()
}

// Mock Leaflet module
vi.mock('leaflet', () => ({
  default: {
    latLngBounds: vi.fn((southWest, northEast) => ({
      getNorth: vi.fn(() => northEast[0]),
      getSouth: vi.fn(() => southWest[0]),
      getEast: vi.fn(() => northEast[1]),
      getWest: vi.fn(() => southWest[1])
    }))
  }
}))

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
})

// Test component to use the composable (unused but kept for reference)
// const TestComponent = {
//   template: '<div></div>',
//   setup() {
//     return useMapState()
//   }
// }

describe('useMapState', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock.getItem.mockReturnValue(null)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('loadMapState', () => {
    it('should return null when no saved state exists', () => {
      localStorageMock.getItem.mockReturnValue(null)

      const { loadMapState } = useMapState()
      const result = loadMapState()

      expect(result).toBeNull()
    })

    it('should load valid saved state from localStorage', () => {
      const mockState: MapState = {
        center: { lat: 45.0, lng: 5.0 },
        zoom: 10,
        bounds: {
          north: 46.0,
          south: 44.0,
          east: 6.0,
          west: 4.0
        }
      }

      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockState))

      const { loadMapState } = useMapState()
      const result = loadMapState()

      expect(result).toEqual(mockState)
    })

    it('should handle invalid JSON in localStorage gracefully', () => {
      localStorageMock.getItem.mockReturnValue('invalid json')

      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      const { loadMapState } = useMapState()
      const result = loadMapState()

      expect(result).toBeNull()
      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to load map state from localStorage:',
        expect.any(Error)
      )

      consoleSpy.mockRestore()
    })

    it('should handle malformed state data gracefully', () => {
      const invalidState = {
        center: { lat: 'invalid', lng: 5.0 },
        zoom: 'invalid'
      }

      localStorageMock.getItem.mockReturnValue(JSON.stringify(invalidState))

      const { loadMapState } = useMapState()
      const result = loadMapState()

      expect(result).toBeNull()
    })
  })

  describe('saveMapState', () => {
    it('should save valid map state to localStorage', () => {
      const { saveMapState } = useMapState()

      const mockState: MapState = {
        center: { lat: 45.0, lng: 5.0 },
        zoom: 10,
        bounds: {
          north: 46.0,
          south: 44.0,
          east: 6.0,
          west: 4.0
        }
      }

      saveMapState(mockState)

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'gravly_map_state',
        JSON.stringify(mockState)
      )
    })

    it('should handle localStorage errors gracefully', () => {
      const { saveMapState } = useMapState()

      localStorageMock.setItem.mockImplementation(() => {
        throw new Error('Storage quota exceeded')
      })

      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      const mockState: MapState = {
        center: { lat: 45.0, lng: 5.0 },
        zoom: 10
      }

      saveMapState(mockState)

      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to save map state to localStorage:',
        expect.any(Error)
      )

      consoleSpy.mockRestore()
    })
  })

  describe('clearMapState', () => {
    it('should clear map state from localStorage', () => {
      const { clearMapState } = useMapState()

      clearMapState()

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('gravly_map_state')
    })

    it('should handle localStorage errors gracefully', () => {
      const { clearMapState } = useMapState()

      localStorageMock.removeItem.mockImplementation(() => {
        throw new Error('Storage error')
      })

      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      clearMapState()

      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to clear map state from localStorage:',
        expect.any(Error)
      )

      consoleSpy.mockRestore()
    })
  })

  describe('extractMapState', () => {
    it('should extract map state from valid map instance', () => {
      const { extractMapState } = useMapState()

      const result = extractMapState(mockMapInstance)

      expect(result).toEqual({
        center: { lat: 45.764, lng: 4.8357 },
        zoom: 12,
        bounds: {
          north: 46.0,
          south: 45.5,
          east: 5.0,
          west: 4.5
        }
      })
    })

    it('should return null for invalid map instance', () => {
      const { extractMapState } = useMapState()

      expect(extractMapState(null)).toBeNull()
      expect(extractMapState(undefined)).toBeNull()
      expect(extractMapState({})).toBeNull()
    })

    it('should handle map instance errors gracefully', () => {
      const { extractMapState } = useMapState()

      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      const faultyMap = {
        getCenter: vi.fn(() => {
          throw new Error('Map error')
        }),
        getZoom: vi.fn(() => 12),
        getBounds: vi.fn(() => ({
          getNorth: vi.fn(() => 46.0),
          getSouth: vi.fn(() => 45.5),
          getEast: vi.fn(() => 5.0),
          getWest: vi.fn(() => 4.5)
        }))
      }

      const result = extractMapState(faultyMap)

      expect(result).toBeNull()
      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to extract map state:',
        expect.any(Error)
      )

      consoleSpy.mockRestore()
    })
  })

  describe('applyMapState', () => {
    it('should apply map state with bounds to map instance', async () => {
      const { applyMapState } = useMapState()

      const mapState: MapState = {
        center: { lat: 45.0, lng: 5.0 },
        zoom: 10,
        bounds: {
          north: 46.0,
          south: 44.0,
          east: 6.0,
          west: 4.0
        }
      }

      applyMapState(mockMapInstance, mapState)

      expect(mockMapInstance.fitBounds).toHaveBeenCalled()

      // Wait for setTimeout to complete
      await new Promise((resolve) => setTimeout(resolve, 150))
      expect(mockMapInstance.invalidateSize).toHaveBeenCalled()
    })

    it('should apply map state with center and zoom when bounds not available', async () => {
      const { applyMapState } = useMapState()

      const mapState: MapState = {
        center: { lat: 45.0, lng: 5.0 },
        zoom: 10
      }

      applyMapState(mockMapInstance, mapState)

      expect(mockMapInstance.setView).toHaveBeenCalledWith([45.0, 5.0], 10)

      // Wait for setTimeout to complete
      await new Promise((resolve) => setTimeout(resolve, 150))
      expect(mockMapInstance.invalidateSize).toHaveBeenCalled()
    })

    it('should handle null map instance gracefully', () => {
      const { applyMapState } = useMapState()

      const mapState: MapState = {
        center: { lat: 45.0, lng: 5.0 },
        zoom: 10
      }

      applyMapState(null, mapState)

      expect(mockMapInstance.setView).not.toHaveBeenCalled()
    })

    it('should handle null map state gracefully', () => {
      const { applyMapState } = useMapState()

      applyMapState(mockMapInstance, null as any)

      expect(mockMapInstance.setView).not.toHaveBeenCalled()
    })

    it('should handle map instance errors gracefully', () => {
      const { applyMapState } = useMapState()

      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      const faultyMap = {
        setView: vi.fn(() => {
          throw new Error('Map error')
        }),
        fitBounds: vi.fn(),
        invalidateSize: vi.fn()
      }

      const mapState: MapState = {
        center: { lat: 45.0, lng: 5.0 },
        zoom: 10
      }

      applyMapState(faultyMap, mapState)

      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to apply map state:',
        expect.any(Error)
      )

      consoleSpy.mockRestore()
    })
  })

  describe('integration tests', () => {
    it('should complete full save and load cycle', () => {
      const { saveMapState, loadMapState, extractMapState } = useMapState()

      // Extract state from mock map
      const extractedState = extractMapState(mockMapInstance)
      expect(extractedState).not.toBeNull()

      // Save the state
      saveMapState(extractedState!)

      // Verify it was saved
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'gravly_map_state',
        JSON.stringify(extractedState)
      )

      // Mock the saved state for loading
      localStorageMock.getItem.mockReturnValue(JSON.stringify(extractedState))

      // Load the state
      const loadedState = loadMapState()
      expect(loadedState).toEqual(extractedState)
    })

    it('should handle complete workflow with error recovery', () => {
      const { saveMapState, loadMapState, clearMapState, applyMapState } = useMapState()

      // Test with localStorage errors
      localStorageMock.setItem.mockImplementation(() => {
        throw new Error('Storage error')
      })

      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      const mapState: MapState = {
        center: { lat: 45.0, lng: 5.0 },
        zoom: 10
      }

      // Should handle save error gracefully
      saveMapState(mapState)
      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to save map state to localStorage:',
        expect.any(Error)
      )

      // Should still be able to load (returns null due to error)
      const loadedState = loadMapState()
      expect(loadedState).toBeNull()

      // Should be able to clear
      clearMapState()

      // Should be able to apply state
      applyMapState(mockMapInstance, mapState)
      expect(mockMapInstance.setView).toHaveBeenCalledWith([45.0, 5.0], 10)

      consoleSpy.mockRestore()
    })
  })

  describe('MapState interface validation', () => {
    it('should validate MapState structure correctly', () => {
      const { loadMapState } = useMapState()

      // Test valid state
      const validState = {
        center: { lat: 45.0, lng: 5.0 },
        zoom: 10,
        bounds: {
          north: 46.0,
          south: 44.0,
          east: 6.0,
          west: 4.0
        }
      }

      localStorageMock.getItem.mockReturnValue(JSON.stringify(validState))
      expect(loadMapState()).toEqual(validState)

      // Test invalid state - missing center
      const invalidState1 = {
        zoom: 10
      }

      localStorageMock.getItem.mockReturnValue(JSON.stringify(invalidState1))
      expect(loadMapState()).toBeNull()

      // Test invalid state - wrong center type
      const invalidState2 = {
        center: { lat: 'invalid', lng: 5.0 },
        zoom: 10
      }

      localStorageMock.getItem.mockReturnValue(JSON.stringify(invalidState2))
      expect(loadMapState()).toBeNull()

      // Test invalid state - wrong zoom type
      const invalidState3 = {
        center: { lat: 45.0, lng: 5.0 },
        zoom: 'invalid'
      }

      localStorageMock.getItem.mockReturnValue(JSON.stringify(invalidState3))
      expect(loadMapState()).toBeNull()
    })
  })
})
