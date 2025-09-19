import { ref, onMounted, getCurrentInstance } from 'vue'
import L from 'leaflet'

export interface MapState {
  center: {
    lat: number
    lng: number
  }
  zoom: number
  bounds?: {
    north: number
    south: number
    east: number
    west: number
  }
}

const STORAGE_KEY = 'gravly_map_state'

export function useMapState() {
  const savedMapState = ref<MapState | null>(null)

  // Load saved map state from localStorage
  function loadMapState(): MapState | null {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        // Validate the structure
        if (
          parsed &&
          parsed.center &&
          typeof parsed.center.lat === 'number' &&
          typeof parsed.center.lng === 'number' &&
          typeof parsed.zoom === 'number'
        ) {
          return parsed
        }
      }
    } catch (error) {
      console.warn('Failed to load map state from localStorage:', error)
    }
    return null
  }

  // Save map state to localStorage
  function saveMapState(mapState: MapState) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(mapState))
      savedMapState.value = mapState
    } catch (error) {
      console.warn('Failed to save map state to localStorage:', error)
    }
  }

  // Clear saved map state
  function clearMapState() {
    try {
      localStorage.removeItem(STORAGE_KEY)
      savedMapState.value = null
    } catch (error) {
      console.warn('Failed to clear map state from localStorage:', error)
    }
  }

  // Extract map state from Leaflet map instance
  function extractMapState(map: any): MapState | null {
    if (
      !map ||
      typeof map.getCenter !== 'function' ||
      typeof map.getZoom !== 'function'
    ) {
      return null
    }

    try {
      const center = map.getCenter()
      const zoom = map.getZoom()
      const bounds = map.getBounds()

      return {
        center: {
          lat: center.lat,
          lng: center.lng
        },
        zoom: zoom,
        bounds: {
          north: bounds.getNorth(),
          south: bounds.getSouth(),
          east: bounds.getEast(),
          west: bounds.getWest()
        }
      }
    } catch (error) {
      console.warn('Failed to extract map state:', error)
      return null
    }
  }

  // Apply map state to Leaflet map instance
  function applyMapState(map: any, mapState: MapState) {
    if (!map || !mapState) return

    try {
      if (mapState.bounds) {
        // Use bounds if available for more precise restoration
        const bounds = L.latLngBounds(
          [mapState.bounds.south, mapState.bounds.west],
          [mapState.bounds.north, mapState.bounds.east]
        )
        map.fitBounds(bounds)
      } else {
        // Fallback to center and zoom
        map.setView([mapState.center.lat, mapState.center.lng], mapState.zoom)
      }

      // Ensure map renders properly after state change
      setTimeout(() => {
        map.invalidateSize()
      }, 100)
    } catch (error) {
      console.warn('Failed to apply map state:', error)
    }
  }

  // Load map state on composable initialization
  // Only call onMounted if we're in a component context
  const instance = getCurrentInstance()
  if (instance) {
    onMounted(() => {
      savedMapState.value = loadMapState()
    })
  } else {
    // If not in component context (e.g., in tests), load state immediately
    savedMapState.value = loadMapState()
  }

  return {
    savedMapState,
    loadMapState,
    saveMapState,
    clearMapState,
    extractMapState,
    applyMapState
  }
}
