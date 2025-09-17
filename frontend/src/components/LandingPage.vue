<template>
  <div class="landing-page">
    <div class="landing-content">
      <!-- Empty content for now -->
      <div class="map-section">
        <div class="map-container">
          <div class="card card-map">
            <div id="landing-map" class="map"></div>
            <div class="loading-indicator" :class="{ show: loading }">
              <div v-if="totalTracks > 0">
                🔍 Loading segments... {{ loadedTracks }}/{{ totalTracks }}
              </div>
              <div v-else>🔍 Searching segments...</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, onUnmounted, ref } from 'vue'
import L from 'leaflet'
import type { TrackResponse, TrackWithGPXDataResponse, GPXDataResponse } from '../types'
import { parseGPXData } from '../utils/gpxParser'

// Map instance
let map: any = null

// Segments data from API
const segments = ref<TrackResponse[]>([])
const loading = ref(false)
const totalTracks = ref(0)
const loadedTracks = ref(0)
let eventSource: EventSource | null = null
let isSearching = false
let searchTimeout: number | null = null
let pendingTracks: TrackResponse[] = []
let previousMapBounds: any = null

// Cache for GPX data to avoid refetching
const gpxDataCache = new Map<number, TrackWithGPXDataResponse>()
const loadingGPXData = new Set<number>()

// Track currently drawn layers by segment ID to avoid redrawing
const currentMapLayers = new Map<string, any>()

function initializeMap() {
  if (map) {
    return
  }

  const container = document.getElementById('landing-map')
  if (!container) {
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

  // Process any pending tracks that arrived before map was ready
  processPendingTracks()

  // Search for segments when map view changes
  searchSegmentsInView()

  // Add event listeners for map movement with debouncing
  // OPTIMIZATION: Only trigger search when panning (center changes), not when zooming (center stays same)
  // Initialize previous bounds for comparison
  previousMapBounds = map.getBounds()
  map.on('moveend', handleMapMoveEnd)

  // Add zoom event listener to update circle sizes
  map.on('zoomend', updateCircleSizes)
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

// Handle map move end - check if new bounds are within previous bounds (zooming in)
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
  }

  // Update previous bounds for next comparison
  previousMapBounds = currentBounds
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

  // Don't clear segments array - we'll add to it incrementally
  // segments.value = [] // Commented out for incremental updates
  totalTracks.value = 0
  loadedTracks.value = 0
  pendingTracks = [] // Clear any pending tracks from previous search

  const bounds = map.getBounds()

  const params = new URLSearchParams({
    north: bounds.getNorth().toString(),
    south: bounds.getSouth().toString(),
    east: bounds.getEast().toString(),
    west: bounds.getWest().toString()
  })

  // Only clear layers if this is the first search (no layers drawn yet)
  if (currentMapLayers.size === 0) {
    map.eachLayer((layer: any) => {
      if (
        layer instanceof L.Rectangle ||
        layer instanceof L.Polyline ||
        layer instanceof L.CircleMarker
      ) {
        map.removeLayer(layer)
      }
    })
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

          segments.value.push(track)
          loadedTracks.value++

          // Process the track (add bounding box first, then fetch GPX data for rendering)
          processTrack(track)
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

  // Add start and end markers
  let startMarker: any = null
  let endMarker: any = null

  if (trackPoints.length > 0) {
    // Calculate dynamic radius based on zoom level
    const currentZoom = mapInstance.getZoom()
    const baseRadius = 6
    const maxRadius = 10
    const minRadius = 2
    // Scale radius with zoom level - smaller circles when zoomed out, larger when zoomed in
    const dynamicRadius = Math.max(
      minRadius,
      Math.min(maxRadius, baseRadius + (currentZoom - 10) * 0.4)
    )

    // Start marker (orange)
    startMarker = L.circleMarker(trackPoints[0], {
      radius: dynamicRadius,
      fillColor: '#ff6600', // Orange color
      color: '#ffffff',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.8
    }).addTo(mapInstance)

    // Add start marker popup
    startMarker.bindPopup(
      `<div class="marker-popup"><strong>Start:</strong> ${segment.name}</div>`
    )

    // End marker (blue)
    endMarker = L.circleMarker(trackPoints[trackPoints.length - 1], {
      radius: dynamicRadius,
      fillColor: '#3b82f6', // Blue color
      color: '#ffffff',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.8
    }).addTo(mapInstance)

    // Add end marker popup
    endMarker.bindPopup(
      `<div class="marker-popup"><strong>End:</strong> ${segment.name}</div>`
    )
  }

  // Track the drawn layers to avoid duplicates
  const segmentId = segment.id.toString()
  currentMapLayers.set(segmentId, {
    polyline: polyline,
    startMarker: trackPoints.length > 0 ? startMarker : null,
    endMarker: trackPoints.length > 0 ? endMarker : null
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
    map.remove()
    map = null
  }

  // Clear GPX data cache
  gpxDataCache.clear()
  loadingGPXData.clear()

  isSearching = false
}

onMounted(() => {
  // Small delay to ensure DOM is ready
  setTimeout(() => {
    initializeMap()
  }, 100)
})

onUnmounted(() => {
  cleanupMap()
})
</script>

<style scoped>
.landing-page {
  min-height: calc(100vh - 80px);
  background: #f8fafc;
  padding: 2rem;
}

.landing-content {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.hero-section {
  text-align: center;
  color: #2d3748;
  margin-bottom: 1rem;
}

.hero-title {
  font-size: 3rem;
  font-weight: 700;
  margin: 0 0 1rem 0;
  background: linear-gradient(135deg, #ff6600, #ff7f2a);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 1.25rem;
  color: #6b7280;
  margin: 0;
}

.map-section {
  display: flex;
  justify-content: center;
  width: 100%;
}

.map-container {
  width: 100%;
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
}

.map {
  height: 65vh; /* 65% of viewport height */
  width: 100%; /* Full width */
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

:global(.start-marker) {
  background: #ff6600; /* Orange color */
  color: white;
}

:global(.end-marker) {
  background: #3b82f6; /* Blue color */
  color: white;
}

/* Responsive design with 1:1 aspect ratio scaling */
@media (max-width: 1200px) {
  .landing-content {
    padding: 0 1rem;
  }
}

@media (max-width: 1000px) {
  .map {
    height: 65vh; /* Maintain 65% viewport height */
  }
}

@media (max-width: 992px) {
  .landing-page {
    padding: 1.5rem 1rem;
  }

  .hero-title {
    font-size: 2.5rem;
  }

  .hero-subtitle {
    font-size: 1.125rem;
  }
}

@media (max-width: 768px) {
  .landing-page {
    padding: 1rem 0.75rem;
  }

  .map {
    height: 65vh; /* Maintain 65% viewport height */
  }
}

@media (max-width: 576px) {
  .landing-page {
    padding: 0.75rem 0.5rem;
  }

  .map {
    height: 65vh; /* Maintain 65% viewport height */
  }
}

@media (max-width: 480px) {
  .map {
    height: 65vh; /* Maintain 65% viewport height */
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

/* Loading indicator */
.loading-indicator {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(255, 255, 255, 0.9);
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
  z-index: 1000;
  display: none;
}

.loading-indicator.show {
  display: block;
}
</style>
