<template>
  <div class="landing-page">
    <div class="landing-content">
      <div class="map-section">
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

      <!-- Segment List Section -->
      <div class="segment-list-section">
        <div class="segment-list-container">
          <SegmentList
            :segments="segments"
            :loading="loading"
            @segment-click="onSegmentClick"
            @segment-hover="onSegmentHover"
            @segment-leave="onSegmentLeave"
            @track-type-change="onTrackTypeChange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, onUnmounted, ref, nextTick } from 'vue'
import L from 'leaflet'
import type { TrackResponse, TrackWithGPXDataResponse, GPXDataResponse } from '../types'
import { parseGPXData } from '../utils/gpxParser'
import SegmentList from './SegmentList.vue'

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

  // Add OpenStreetMap tiles
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(map)

  // Set initial view to Lyon, France
  map.setView([45.764, 4.8357], 12)

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
  map.on('moveend', handleMapMoveEnd)

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

// Handle map move end - only trigger search when bounds expand beyond previous search
function handleMapMoveEnd() {
  if (!map || !previousMapBounds) {
    debouncedSearchSegments()
    return
  }

  const currentBounds = map.getBounds()

  // Check if current bounds are completely within previous bounds (zooming in)
  const boundsWithinPrevious = previousMapBounds.contains(currentBounds)

  // Only trigger search if bounds expanded beyond previous bounds (zooming out or panning to new area)
  if (!boundsWithinPrevious) {
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

  // Filter existing segments to only show those visible in current bounds
  const visibleSegments = segments.value.filter((segment) => {
    return (
      segment.bound_north >= currentBounds.getSouth() &&
      segment.bound_south <= currentBounds.getNorth() &&
      segment.bound_east >= currentBounds.getWest() &&
      segment.bound_west <= currentBounds.getEast()
    )
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
  // Small delay to ensure DOM is ready
  setTimeout(() => {
    initializeMap()
  }, 100)
})

// Handle segment click from the segment list or map
function onSegmentClick(segment: TrackResponse) {
  if (!map) return

  // Focus the map on the selected segment
  const bounds = L.latLngBounds([
    [segment.bound_south, segment.bound_west],
    [segment.bound_north, segment.bound_east]
  ])
  map.fitBounds(bounds, { padding: [20, 20] })

  // Highlight the segment on the map
  const segmentId = segment.id.toString()
  const layerData = currentMapLayers.get(segmentId)
  if (layerData) {
    // Temporarily highlight the segment
    if (layerData.rectangle) {
      layerData.rectangle.setStyle({
        fillOpacity: 0.3,
        strokeWidth: 4,
        color: '#ff6b35'
      })

      // Reset after 3 seconds
      setTimeout(() => {
        if (layerData.rectangle) {
          layerData.rectangle.setStyle({
            fillOpacity: 0.1,
            strokeWidth: 2,
            color: '#3388ff'
          })
        }
      }, 3000)
    }

    // Also highlight the polyline if it exists
    if (layerData.polyline) {
      layerData.polyline.setStyle({
        weight: 5,
        opacity: 1,
        color: '#ff6b35'
      })

      // Reset after 3 seconds
      setTimeout(() => {
        if (layerData.polyline) {
          layerData.polyline.setStyle({
            weight: 3,
            opacity: 0.8,
            color: '#FF6600'
          })
        }
      }, 3000)
    }
  }
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

onUnmounted(() => {
  cleanupMap()
})
</script>

<style scoped>
.landing-page {
  height: calc(100vh - var(--navbar-height, 60px));
  background: #f8fafc;
  padding: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.segment-list-section {
  display: flex;
  justify-content: center;
  width: 100%;
  height: 30%;
  flex-shrink: 0;
  padding: 1rem;
  box-sizing: border-box;
}

.landing-content {
  width: 100%;
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
  background: linear-gradient(135deg, #ff6600, #ff7f2a);
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
  height: 70%;
  flex-shrink: 0;
}

.map-container {
  width: 100%;
  height: 100%;
}

.segment-list-container {
  width: 100%;
  height: 100%;
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
  box-shadow: 0 0 0 2px rgba(255, 102, 0, 0.1);
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

/* Responsive design with 60/40 split maintained */
@media (max-width: 1200px) {
  .landing-content {
    padding: 0 1rem;
  }

  .map-section {
    height: 70%;
  }

  .segment-list-section {
    height: 30%;
    padding: 0.75rem;
  }
}

@media (max-width: 1000px) {
  .map-section {
    height: 70%;
  }

  .segment-list-section {
    height: 30%;
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

  .map-section {
    height: 70%;
  }

  .segment-list-section {
    height: 30%;
    padding: 0.5rem;
  }
}

@media (max-width: 768px) {
  .landing-page {
    padding: 0;
  }

  .map-section {
    height: 70%;
  }

  .segment-list-section {
    height: 30%;
    padding: 0.5rem;
  }
}

@media (max-width: 576px) {
  .landing-page {
    padding: 0;
  }

  .map-section {
    height: 70%;
  }

  .segment-list-section {
    height: 30%;
    padding: 0.25rem;
  }
}

@media (max-width: 480px) {
  .map-section {
    height: 70%;
  }

  .segment-list-section {
    height: 30%;
    padding: 0.25rem;
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
