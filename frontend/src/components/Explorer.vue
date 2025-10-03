<template>
  <div class="landing-page">
    <div class="landing-content">
      <div class="content-wrapper">
        <!-- Fixed Map Section with Resizable Height -->
        <div class="map-section" :style="{ height: mapHeight + 'px' }">
          <div class="map-container">
            <div class="card card-map">
              <div id="landing-map" class="map"></div>
              <!-- Fixed Center Marker -->
              <div class="fixed-center-marker" title="Search Center">📍</div>
              <!-- Max Results Control - Bottom Left Corner -->
              <div class="map-controls">
                <div class="limit-control">
                  <label for="limit-select" class="limit-label">
                    <i class="fa-solid fa-list-ol"></i>
                    Max Results:
                  </label>
                  <select
                    id="limit-select"
                    v-model="searchLimit"
                    @change="onLimitChange"
                    class="limit-select"
                  >
                    <option value="25">25</option>
                    <option value="50">50</option>
                    <option value="75">75</option>
                    <option value="100">100</option>
                  </select>
                </div>
              </div>

              <!-- Loading Indicator - Top Right -->
              <div v-if="loading" class="loading-indicator">
                <div class="loading-text">🔍 Loading segments...</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Resizable Handle -->
        <div
          class="resize-handle"
          @mousedown="startResize"
          @touchstart="startResize"
          title="Drag up or down to resize map height"
        >
          <div class="resize-handle-bar"></div>
        </div>

        <!-- Segment List Section -->
        <div class="segment-list-section">
          <div class="segment-list-container">
            <SegmentList
              :segments="sortedSegments"
              :loading="loading"
              :get-distance-from-center="getSegmentDistanceFromCenter"
              @segment-click="onSegmentClick"
              @segment-hover="onSegmentHover"
              @segment-leave="onSegmentLeave"
              @track-type-change="onTrackTypeChange"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, onUnmounted, ref, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import L from 'leaflet'
import type { TrackResponse, TrackWithGPXDataResponse, GPXDataResponse } from '../types'
import { parseGPXData } from '../utils/gpxParser'
import { haversineDistance, getBoundingBoxCenter } from '../utils/distance'
import { useMapState } from '../composables/useMapState'
import SegmentList from './SegmentList.vue'

const router = useRouter()

// Map state management
const { savedMapState, saveMapState, extractMapState, applyMapState } = useMapState()

// Map instance
let map: any = null

// Segments data from API
const segments = ref<TrackResponse[]>([])
const loading = ref(false)
const totalTracks = ref(0)
const loadedTracks = ref(0)

// Current search session tracking
const currentSearchTotal = ref(0)
const currentSearchLoaded = ref(0)
let eventSource: EventSource | null = null
let isSearching = false
let searchTimeout: number | null = null
let pendingTracks: TrackResponse[] = []

// Track type filter
const selectedTrackType = ref<'segment' | 'route'>('segment')

// Limit for search results
const searchLimit = ref<number>(50)

// Map height control
const mapHeight = ref<number>(400) // Default height in pixels
const minMapHeight = 200
const maxMapHeight = 800
let isResizing = false
let startY = 0
let startHeight = 0

let previousMapBounds: any = null

// Cache for GPX data to avoid refetching
const gpxDataCache = new Map<number, TrackWithGPXDataResponse>()
const loadingGPXData = new Set<number>()

// Hover rectangle for card hover effect
let hoverRectangle: any = null

// Resize handler for cleanup
let resizeHandler: (() => void) | null = null

// Track currently drawn layers by segment ID to avoid redrawing
const currentMapLayers = new Map<string, any>()

// Fixed center marker - no need to track state

// Computed property to sort segments by distance from map center
const sortedSegments = computed(() => {
  if (!map || segments.value.length === 0 || typeof map.getCenter !== 'function') {
    return segments.value
  }

  try {
    const mapCenter = map.getCenter()
    const centerLat = mapCenter.lat
    const centerLng = mapCenter.lng

    return [...segments.value].sort((a, b) => {
      // Calculate center of each segment's bounding box
      const centerA = getBoundingBoxCenter(
        a.bound_north,
        a.bound_south,
        a.bound_east,
        a.bound_west
      )
      const centerB = getBoundingBoxCenter(
        b.bound_north,
        b.bound_south,
        b.bound_east,
        b.bound_west
      )

      // Calculate distances from map center
      const distanceA = haversineDistance(
        centerLat,
        centerLng,
        centerA.lat,
        centerA.lng
      )
      const distanceB = haversineDistance(
        centerLat,
        centerLng,
        centerB.lat,
        centerB.lng
      )

      return distanceA - distanceB
    })
  } catch (error) {
    // If there's any error getting map center, return unsorted segments
    console.warn('Error calculating segment distances:', error)
    return segments.value
  }
})

// Function to get distance from map center for a segment
const getSegmentDistanceFromCenter = (segment: TrackResponse): number => {
  if (!map || typeof map.getCenter !== 'function') return 0

  try {
    const mapCenter = map.getCenter()
    const segmentCenter = getBoundingBoxCenter(
      segment.bound_north,
      segment.bound_south,
      segment.bound_east,
      segment.bound_west
    )

    return haversineDistance(
      mapCenter.lat,
      mapCenter.lng,
      segmentCenter.lat,
      segmentCenter.lng
    )
  } catch (error) {
    console.warn('Error calculating distance for segment:', segment.id, error)
    return 0
  }
}

function initializeMap() {
  if (map) {
    return
  }

  const container = document.getElementById('landing-map')
  if (!container) {
    return
  }

  // Ensure container has proper dimensions
  if (container.offsetHeight === 0) {
    // Wait for next tick to ensure DOM is fully rendered
    nextTick(() => {
      // Add a small delay to ensure CSS has been applied
      setTimeout(() => {
        initializeMap()
      }, 100)
    })
    return
  }

  // Initialize map
  map = L.map(container, {
    zoomControl: true,
    scrollWheelZoom: true,
    doubleClickZoom: true,
    boxZoom: true,
    keyboard: true,
    dragging: true,
    touchZoom: true
  })

  // Add OpenCycleMap tiles
  const apiKey = import.meta.env.THUNDERFOREST_API_KEY || 'demo'
  L.tileLayer(
    `https://{s}.tile.thunderforest.com/cycle/{z}/{x}/{y}.png?apikey=${apiKey}`,
    {
      attribution:
        'Maps © <a href="https://www.thunderforest.com/">Thunderforest</a>, Data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19
    }
  ).addTo(map)

  // Set initial view - restore saved state or default to Lyon, France
  if (savedMapState.value) {
    applyMapState(map, savedMapState.value)
  } else {
    // Mont-Beuvray parce que ca pique!
    map.setView([46.942728, 4.033681], 14)
  }

  // Add scale control
  L.control
    .scale({
      position: 'bottomright',
      metric: true,
      imperial: false
    })
    .addTo(map)

  // Ensure map renders properly
  map.invalidateSize()

  // Process any pending tracks that arrived before map was ready
  processPendingTracks()

  // Search for segments when map view changes
  searchSegmentsInView()

  // Add event listeners for map movement with debouncing
  // Only trigger database search when bounds expand beyond previous search
  // When zooming in, filter existing segments without re-fetching GPX data
  previousMapBounds = map.getBounds()

  // Listen to multiple events to ensure we catch all map movements
  map.on('moveend', () => {
    handleMapMoveEnd()
  })
  map.on('dragend', () => {
    handleMapMoveEnd()
  }) // Additional event for panning
  map.on('viewreset', () => {
    handleMapMoveEnd()
  }) // Additional event for view changes

  // Add zoom event listener to update circle sizes and segment cards
  map.on('zoomend', () => {
    updateCircleSizes()
    // Update segment cards for current view (may trigger search if bounds expanded)
    handleMapMoveEnd()
  })

  // Add window resize listener to ensure map updates properly
  resizeHandler = () => {
    if (map) {
      map.invalidateSize()
    }
  }
  window.addEventListener('resize', resizeHandler)
}

// Process tracks that arrived before map was ready
function processPendingTracks() {
  if (pendingTracks.length === 0) return

  for (const track of pendingTracks) {
    processTrack(track)
  }

  // Clear the pending tracks
  pendingTracks = []
}

// Handle map move end - trigger search when bounds expand or move significantly
function handleMapMoveEnd() {
  if (!map || !previousMapBounds) {
    debouncedSearchSegments()
    return
  }

  const currentBounds = map.getBounds()

  // Check if current bounds are completely within previous bounds (zooming in)
  const boundsWithinPrevious = previousMapBounds.contains(currentBounds)

  // Check if bounds have moved significantly (panning to new area)
  const centerMoved = !previousMapBounds.contains(currentBounds.getCenter())

  // Check if bounds have expanded beyond previous bounds (zooming out)
  const boundsExpanded = !boundsWithinPrevious

  // Trigger search if bounds expanded OR if we've panned to a new area
  if (boundsExpanded || centerMoved) {
    debouncedSearchSegments()
  } else {
    // Even when zooming in, we need to update the segment cards to remove
    // segments that are no longer visible, but without re-fetching GPX data
    updateSegmentCardsForCurrentView()
  }

  // Update previous bounds for next comparison
  previousMapBounds = currentBounds
}

// Update segment cards to show only segments visible in current view (without database request)
function updateSegmentCardsForCurrentView() {
  if (!map) return

  const currentBounds = map.getBounds()

  // Filter existing segments to only show those at least partially visible in current bounds
  const visibleSegments = segments.value.filter((segment) => {
    const isVisible =
      segment.bound_north > currentBounds.getSouth() && // Track's northern boundary is south of map's southern edge
      segment.bound_south < currentBounds.getNorth() && // Track's southern boundary is north of map's northern edge
      segment.bound_east > currentBounds.getWest() && // Track's eastern boundary is west of map's western edge
      segment.bound_west < currentBounds.getEast() // Track's western boundary is east of map's eastern edge

    return isVisible
  })

  // Update segments array to only show visible ones
  segments.value = visibleSegments

  // Remove map layers for segments that are no longer visible
  const visibleSegmentIds = new Set(visibleSegments.map((s) => s.id.toString()))

  // Remove layers for segments not in visible list
  for (const [segmentId, layerData] of currentMapLayers.entries()) {
    if (!visibleSegmentIds.has(segmentId)) {
      if (layerData.rectangle) {
        map.removeLayer(layerData.rectangle)
      }
      currentMapLayers.delete(segmentId)
    }
  }
}

// Update circle sizes based on current zoom level
function updateCircleSizes() {
  if (!map) return

  const currentZoom = map.getZoom()
  const baseRadius = 6
  const maxRadius = 10
  const minRadius = 2
  // Scale radius with zoom level - smaller circles when zoomed out, larger when zoomed in
  const dynamicRadius = Math.max(
    minRadius,
    Math.min(maxRadius, baseRadius + (currentZoom - 10) * 0.4)
  )

  // Update all existing circle markers
  currentMapLayers.forEach((layerData) => {
    if (layerData.startMarker) {
      layerData.startMarker.setRadius(dynamicRadius)
    }
    if (layerData.endMarker) {
      layerData.endMarker.setRadius(dynamicRadius)
    }
  })
}

// Debounced search function to prevent too many requests
function debouncedSearchSegments() {
  // Clear any existing timeout
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }

  // Set a new timeout to search after 200ms of inactivity (optimized from 500ms)
  searchTimeout = window.setTimeout(() => {
    searchSegmentsInView()
  }, 200)
}

// Search for segments within current map bounds using streaming
function searchSegmentsInView() {
  if (!map) return

  // Prevent multiple simultaneous searches
  if (isSearching) {
    return
  }

  // Clear any pending search timeout
  if (searchTimeout) {
    clearTimeout(searchTimeout)
    searchTimeout = null
  }

  // Close any existing event source
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }

  isSearching = true
  loading.value = true

  // Don't clear existing segments - we'll add new ones to existing ones
  // Only clear if this is the first search or if we're switching track types
  const isFirstSearch = segments.value.length === 0
  const currentTrackType = selectedTrackType.value

  // Check if we're switching track types by looking at existing segments
  const isTrackTypeSwitch =
    segments.value.length > 0 &&
    segments.value.some((segment) => {
      // Check if any existing segment has a different track type
      return segment.track_type !== currentTrackType
    })

  if (isFirstSearch || isTrackTypeSwitch) {
    segments.value = []
    totalTracks.value = 0
    loadedTracks.value = 0
    pendingTracks = []
  }

  // Reset current search tracking for every new search
  currentSearchTotal.value = 0
  currentSearchLoaded.value = 0

  const bounds = map.getBounds()

  const params = new URLSearchParams({
    north: bounds.getNorth().toString(),
    south: bounds.getSouth().toString(),
    east: bounds.getEast().toString(),
    west: bounds.getWest().toString(),
    track_type: selectedTrackType.value,
    limit: searchLimit.value.toString()
  })

  // Only clear all layers if this is the first search or switching track types
  if (isFirstSearch || isTrackTypeSwitch) {
    map.eachLayer((layer: any) => {
      if (
        layer instanceof L.Rectangle ||
        layer instanceof L.Polyline ||
        layer instanceof L.CircleMarker
      ) {
        map.removeLayer(layer)
      }
    })

    // Clear the layers tracking map
    currentMapLayers.clear()
  }

  // Clear hover rectangle when starting new search
  if (hoverRectangle) {
    map.removeLayer(hoverRectangle)
    hoverRectangle = null
  }

  // Create EventSource for streaming
  const url = `http://localhost:8000/api/segments/search?${params}`

  // Small delay to ensure backend is ready (removed backend connectivity test for performance)
  setTimeout(() => {
    eventSource = new EventSource(url)

    eventSource.onopen = () => {
      // Connection established
    }

    eventSource.onmessage = (event) => {
      try {
        const data = event.data

        // Check if this is the total count message
        if (!isNaN(Number(data))) {
          totalTracks.value = Number(data)
          currentSearchTotal.value = Number(data)
          return
        }

        // Check if this is the completion message
        if (data === '[DONE]') {
          // Update bounds after search completes for next optimization check
          if (map) {
            previousMapBounds = map.getBounds()
          }

          loading.value = false
          isSearching = false
          eventSource?.close()
          eventSource = null
          return
        }

        // Parse track data
        try {
          const track: TrackResponse = JSON.parse(data)

          // Check if this segment is already loaded to avoid duplicates
          const existingSegment = segments.value.find((s) => s.id === track.id)
          if (!existingSegment) {
            segments.value.push(track)
            loadedTracks.value++
            currentSearchLoaded.value++

            // Process the track (add bounding box first, then fetch GPX data for rendering)
            processTrack(track)
          }
        } catch {
          // Error parsing track data
        }
      } catch {
        // Error parsing streamed data
      }
    }

    eventSource.onerror = () => {
      loading.value = false
      isSearching = false
      if (eventSource) {
        eventSource.close()
        eventSource = null
      }
    }
  }, 100)
}

// Process a track (add bounding box first, then fetch GPX data for detailed rendering)
async function processTrack(track: TrackResponse) {
  // Check if track is already drawn to avoid duplicates
  const segmentId = track.id.toString()
  if (currentMapLayers.has(segmentId)) {
    return
  }

  if (!map || typeof map.addLayer !== 'function' || typeof map.setView !== 'function') {
    pendingTracks.push(track)
    return
  }

  // First, add bounding box immediately for quick visual feedback
  addBoundingBoxToMap(track, map)

  // Then fetch GPX data asynchronously for detailed rendering
  await fetchAndRenderGPXData(track)
}

// Fetch GPX data for a track and render it on the map
async function fetchAndRenderGPXData(track: TrackResponse) {
  // Check if we already have this GPX data cached
  if (gpxDataCache.has(track.id)) {
    const cachedTrack = gpxDataCache.get(track.id)!
    renderGPXTrackOnMap(cachedTrack)
    return
  }

  // Check if we're already loading this GPX data
  if (loadingGPXData.has(track.id)) {
    return
  }

  loadingGPXData.add(track.id)

  try {
    const response = await fetch(`http://localhost:8000/api/segments/${track.id}/gpx`)
    if (!response.ok) {
      console.warn(
        `Failed to fetch GPX data for track ${track.id}: ${response.statusText}`
      )
      return
    }

    const gpxResponse: GPXDataResponse = await response.json()

    // Create a TrackWithGPXDataResponse object for caching and rendering
    const trackWithGPX: TrackWithGPXDataResponse = {
      ...track,
      gpx_data: null,
      gpx_xml_data: gpxResponse.gpx_xml_data
    }

    // Cache the GPX data
    gpxDataCache.set(track.id, trackWithGPX)

    // Render the detailed GPX track
    renderGPXTrackOnMap(trackWithGPX)
  } catch (error) {
    console.warn(`Error fetching GPX data for track ${track.id}:`, error)
  } finally {
    loadingGPXData.delete(track.id)
  }
}

// Render GPX track on map (replaces bounding box with detailed track)
function renderGPXTrackOnMap(track: TrackWithGPXDataResponse) {
  if (!track.gpx_xml_data) {
    return
  }

  // Remove the existing bounding box layer for this track
  const segmentId = track.id.toString()
  const existingLayer = currentMapLayers.get(segmentId)
  if (existingLayer && existingLayer.rectangle) {
    map.removeLayer(existingLayer.rectangle)
  }

  // Parse GPX data
  const fileId =
    track.file_path.split('/').pop()?.replace('.gpx', '') || track.id.toString()
  const gpxData = parseGPXData(track.gpx_xml_data, fileId)

  // Add detailed GPX track to map
  if (gpxData && gpxData.points && gpxData.points.length > 0) {
    addGPXTrackToMap(track, gpxData, map)
  }
}

// Add GPX track to map - simplified version
function addGPXTrackToMap(
  segment: TrackWithGPXDataResponse,
  gpxData: any,
  mapInstance: any
) {
  if (!mapInstance) {
    return
  }

  // Validate that map is a proper Leaflet map object
  if (
    typeof mapInstance.addLayer !== 'function' ||
    typeof mapInstance.setView !== 'function'
  ) {
    return
  }

  if (!gpxData || !gpxData.points.length) {
    return
  }

  // Convert GPX points to Leaflet lat/lng format
  const trackPoints = gpxData.points.map((point: any) => [
    point.latitude,
    point.longitude
  ])

  // Create polyline for the track - simplified orange color
  const polyline = L.polyline(trackPoints, {
    color: '#FF6600', // Orange color
    weight: 3,
    opacity: 0.8
  }).addTo(mapInstance)

  // Add click handler to zoom in on the segment
  polyline.on('click', () => {
    onSegmentClick(segment)
  })

  // Track the drawn layers to avoid duplicates
  const segmentId = segment.id.toString()
  currentMapLayers.set(segmentId, {
    polyline: polyline
  })
}

// Add bounding box to map (immediate visual feedback while GPX data loads)
function addBoundingBoxToMap(segment: TrackResponse, mapInstance: any) {
  if (!mapInstance) {
    return
  }

  // Validate that map is a proper Leaflet map object
  if (
    typeof mapInstance.addLayer !== 'function' ||
    typeof mapInstance.setView !== 'function'
  ) {
    return
  }

  const segmentBounds = L.latLngBounds(
    [segment.bound_south, segment.bound_west],
    [segment.bound_north, segment.bound_east]
  )

  const rectangle = L.rectangle(segmentBounds, {
    color: '#FF6600', // Orange color
    weight: 2,
    fillOpacity: 0.1
  }).addTo(mapInstance)

  // Add click handler to zoom in on the segment
  rectangle.on('click', () => {
    onSegmentClick(segment)
  })

  // Track the drawn layers to avoid duplicates
  const segmentId = segment.id.toString()
  currentMapLayers.set(segmentId, {
    rectangle: rectangle
  })
}

function cleanupMap() {
  // Clear any pending search timeout
  if (searchTimeout) {
    clearTimeout(searchTimeout)
    searchTimeout = null
  }

  // Close event source if active
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }

  if (map) {
    // Clear hover rectangle before removing map
    if (hoverRectangle) {
      map.removeLayer(hoverRectangle)
      hoverRectangle = null
    }

    map.remove()
    map = null
  }

  // Clear GPX data cache
  gpxDataCache.clear()
  loadingGPXData.clear()

  // Remove resize listener
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
    resizeHandler = null
  }

  isSearching = false
}

onMounted(() => {
  // Check if we need to redirect after Strava authentication
  const redirectDestination = localStorage.getItem('strava_redirect_after_auth')
  if (redirectDestination) {
    console.info(`Redirecting to stored destination: ${redirectDestination}`)
    localStorage.removeItem('strava_redirect_after_auth')
    // Small delay to ensure navbar is loaded
    setTimeout(() => {
      router.push(redirectDestination)
    }, 500)
    return // Don't initialize map if we're redirecting
  }

  // Small delay to ensure DOM is ready
  setTimeout(() => {
    initializeMap()
  }, 100)
})

// Handle segment click from the segment list or map
function onSegmentClick(segment: TrackResponse) {
  // Save current map state before navigating
  if (map) {
    const mapState = extractMapState(map)
    if (mapState) {
      saveMapState(mapState)
    }
  }

  // Navigate to segment detail view
  router.push(`/segment/${segment.id}`)
}

// Handle segment hover from the segment list
function onSegmentHover(segment: TrackResponse) {
  if (!map) return

  // Remove any existing hover rectangle
  if (hoverRectangle) {
    map.removeLayer(hoverRectangle)
    hoverRectangle = null
  }

  // Create a new temporary rectangle using the segment's bounding box data
  const segmentBounds = L.latLngBounds(
    [segment.bound_south, segment.bound_west],
    [segment.bound_north, segment.bound_east]
  )

  // Draw a temporary hover rectangle
  hoverRectangle = L.rectangle(segmentBounds, {
    color: '#ff6b35',
    weight: 4,
    fillOpacity: 0.2,
    dashArray: '8, 8', // Dashed border for better visibility
    interactive: false // Don't interfere with map interactions
  }).addTo(map)

  // Bring to front to ensure it's visible
  hoverRectangle.bringToFront()
}

// Handle segment leave from the segment list
function onSegmentLeave() {
  if (!map) return

  // Remove the hover rectangle
  if (hoverRectangle) {
    map.removeLayer(hoverRectangle)
    hoverRectangle = null
  }
}

function onTrackTypeChange(trackType: 'segment' | 'route') {
  selectedTrackType.value = trackType
  // Trigger a new search with the updated track type filter
  if (map) {
    searchSegmentsInView()
  }
}

function onLimitChange() {
  // Trigger a new search with the new limit
  if (map) {
    searchSegmentsInView()
  }
}

// Resize functionality
function startResize(event: MouseEvent | TouchEvent) {
  isResizing = true
  const clientY = 'touches' in event ? event.touches[0].clientY : event.clientY
  startY = clientY
  startHeight = mapHeight.value

  // Add global event listeners
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  document.addEventListener('touchmove', handleResize)
  document.addEventListener('touchend', stopResize)

  // Prevent default to avoid text selection
  event.preventDefault()
}

function handleResize(event: MouseEvent | TouchEvent) {
  if (!isResizing) return

  const clientY = 'touches' in event ? event.touches[0].clientY : event.clientY
  const deltaY = clientY - startY
  const newHeight = startHeight + deltaY

  // Constrain height within bounds
  mapHeight.value = Math.max(minMapHeight, Math.min(maxMapHeight, newHeight))

  // Invalidate map size to ensure proper rendering
  if (map) {
    setTimeout(() => {
      map.invalidateSize()
    }, 0)
  }

  event.preventDefault()
}

function stopResize() {
  isResizing = false

  // Remove global event listeners
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
  document.removeEventListener('touchmove', handleResize)
  document.removeEventListener('touchend', stopResize)
}

// Initialize map height based on viewport
function initializeMapHeight() {
  const viewportHeight = window.innerHeight
  const navbarHeight = 60 // Approximate navbar height
  const availableHeight = viewportHeight - navbarHeight

  // Set initial map height to 50% of available height
  mapHeight.value = Math.max(
    minMapHeight,
    Math.min(maxMapHeight, availableHeight * 0.5)
  )
}

onMounted(() => {
  // Initialize map height
  initializeMapHeight()

  // Small delay to ensure DOM is ready
  setTimeout(() => {
    initializeMap()
  }, 100)
})

onUnmounted(() => {
  cleanupMap()
  // Clean up resize event listeners
  stopResize()
})
</script>

<style scoped>
.landing-page {
  height: calc(100vh - var(--navbar-height, 60px));
  background: #f8fafc;
  padding: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* Prevent overall page scrolling */
}

.segment-list-section {
  display: flex;
  justify-content: center;
  width: 100%;
  padding: 1rem;
  box-sizing: border-box;
  flex: 1;
  overflow: hidden; /* Prevent scrolling at this level */
  min-height: 0; /* Allow flex item to shrink below content size */
}

.landing-content {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.content-wrapper {
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.hero-section {
  text-align: center;
  color: #2d3748;
  margin-bottom: 0.5rem;
  padding: 0.5rem 0;
  flex-shrink: 0;
}

.hero-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
  background: linear-gradient(135deg, var(--brand-primary), #ff7f2a);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 1.1rem;
  color: #6b7280;
  margin: 0;
}

.map-section {
  display: flex;
  justify-content: center;
  width: 100%;
  flex-shrink: 0;
  transition: height 0.2s ease;
}

.map-container {
  width: 100%;
  height: 100%;
}

.segment-list-container {
  width: 100%;
  height: 100%;
  overflow: hidden; /* Contain scrolling within the component */
  display: flex;
  flex-direction: column;
}

/* Resize Handle */
.resize-handle {
  height: 16px;
  background: var(--brand-primary);
  cursor: ns-resize;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
  box-shadow: 0 2px 4px rgba(var(--brand-primary-rgb), 0.2);
  border-radius: 8px;
  margin: 4px 8px; /* Add some margin for rounded appearance */
}

.resize-handle:hover {
  background: var(--brand-primary-hover);
  box-shadow: 0 4px 8px rgba(var(--brand-primary-rgb), 0.3);
  transform: scaleY(1.1);
}

.resize-handle:active {
  background: var(--brand-primary-hover);
  box-shadow: 0 1px 2px rgba(var(--brand-primary-rgb), 0.4);
  transform: scaleY(1.05);
}

.resize-handle-bar {
  width: 60px;
  height: 8px;
  background: white;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  position: relative;
}

.resize-handle:hover .resize-handle-bar {
  background: #fff5f0;
  transform: scale(1.05);
}

/* Vertical arrows to indicate resize direction */
.resize-handle-bar::before,
.resize-handle-bar::after {
  content: '';
  position: absolute;
  width: 0;
  height: 0;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
}

.resize-handle-bar::before {
  top: -6px;
  border-bottom: 6px solid white;
}

.resize-handle-bar::after {
  bottom: -6px;
  border-top: 6px solid white;
}

.resize-handle:hover .resize-handle-bar::before,
.resize-handle:hover .resize-handle-bar::after {
  border-bottom-color: #fff5f0;
  border-top-color: #fff5f0;
}

/* Card styles matching Editor */
.card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow:
    0 1px 3px 0 rgba(0, 0, 0, 0.1),
    0 1px 2px 0 rgba(0, 0, 0, 0.06);
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.card-map {
  padding: 0;
  overflow: hidden;
  height: 100%;
  position: relative;
}

.map {
  height: 100%; /* Fill the map-section container */
  width: 100%; /* Full width */
}

/* Map Controls - Bottom Left Corner */
.map-controls {
  position: absolute;
  bottom: 10px;
  left: 10px;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  padding: 8px 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(10px);
}

.limit-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.limit-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  color: #374151;
  white-space: nowrap;
}

.limit-select {
  padding: 4px 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 12px;
  background: white;
  color: #374151;
  cursor: pointer;
  min-width: 60px;
}

.limit-select:focus {
  outline: none;
  border-color: var(--brand-primary);
  box-shadow: 0 0 0 2px rgba(var(--brand-primary-rgb), 0.1);
}

/* Loading Indicator Styles - Top Right */
.loading-indicator {
  position: absolute;
  top: 10px; /* Position at top of map */
  right: 10px; /* Position at right side of map */
  z-index: 1000;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  padding: 8px 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(10px);
}

.loading-text {
  font-size: 12px;
  color: #666;
}

/* Custom marker styles */
:global(.custom-div-icon) {
  background: transparent;
  border: none;
}

:global(.marker-icon) {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  font-size: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* Responsive design with max-width container */
@media (max-width: 1200px) {
  .content-wrapper {
    padding: 0 1rem;
  }

  .segment-list-section {
    padding: 0.75rem;
  }
}

@media (max-width: 1000px) {
  .segment-list-section {
    padding: 0.5rem;
  }
}

@media (max-width: 992px) {
  .landing-page {
    padding: 0;
  }

  .hero-title {
    font-size: 2.5rem;
  }

  .hero-subtitle {
    font-size: 1.125rem;
  }

  .segment-list-section {
    padding: 0.5rem;
  }
}

@media (max-width: 768px) {
  .content-wrapper {
    padding: 0 0.5rem;
  }

  .segment-list-section {
    padding: 0.5rem;
  }
}

@media (max-width: 576px) {
  .content-wrapper {
    padding: 0 0.25rem;
  }

  .segment-list-section {
    padding: 0.25rem;
  }
}

@media (max-width: 480px) {
  .content-wrapper {
    padding: 0 0.125rem;
  }

  .segment-list-section {
    padding: 0.125rem;
  }
}

/* Ensure map is properly sized on all devices */
:global(.leaflet-container) {
  height: 100%;
  width: 100%;
}

/* Scale control styling */
:global(.leaflet-control-scale) {
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 2px 5px;
  font-size: 11px;
  line-height: 1.2;
  color: #333;
}

/* Segment rectangle styling */
:global(.segment-rectangle) {
  cursor: pointer;
  transition: all 0.2s ease;
}

/* GPX track styling */
:global(.gpx-track) {
  cursor: pointer;
  transition: all 0.2s ease;
}

:global(.gpx-track:hover) {
  opacity: 1 !important;
  stroke-width: 4 !important;
}

:global(.segment-rectangle:hover) {
  fill-opacity: 0.2 !important;
  stroke-width: 3 !important;
}

/* Segment popup styling */
:global(.segment-popup) {
  min-width: 200px;
}

:global(.segment-popup h3) {
  margin: 0 0 8px 0;
  color: #2d3748;
  font-size: 16px;
}

:global(.segment-popup p) {
  margin: 4px 0;
  font-size: 14px;
  color: #4a5568;
}

/* Marker popup styling */
:global(.marker-popup) {
  font-size: 14px;
  color: #2d3748;
  text-align: center;
  padding: 4px;
}

:global(.marker-popup strong) {
  color: #1f2937;
}

/* Fixed center marker styling */
.fixed-center-marker {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 1000;
  pointer-events: none;
  font-size: 24px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    transform: translate(-50%, -50%) scale(1);
    opacity: 1;
  }
  50% {
    transform: translate(-50%, -50%) scale(1.1);
    opacity: 0.8;
  }
  100% {
    transform: translate(-50%, -50%) scale(1);
    opacity: 1;
  }
}
</style>
