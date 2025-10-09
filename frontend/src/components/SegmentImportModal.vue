<template>
  <div v-if="isOpen" class="modal-overlay" @click="closeModal">
    <div class="modal-content" @click.stop>
      <!-- Modal Header -->
      <div class="modal-header">
        <h3 class="modal-title">
          <i class="fa-solid fa-database"></i>
          {{ t('editor.importSegment') }}
        </h3>
        <button @click="closeModal" class="close-btn" :title="t('common.close')">
          <i class="fa-solid fa-times"></i>
        </button>
      </div>

      <!-- Track Type Toggle -->
      <div class="track-type-tabs">
        <button
          type="button"
          class="tab-button"
          :class="{ active: selectedTrackType === 'segment' }"
          @click="onTrackTypeChange('segment')"
        >
          <i class="fa-solid fa-route"></i>
          {{ t('trackType.segment') }} ({{ segmentCount }})
        </button>
        <button
          type="button"
          class="tab-button"
          :class="{ active: selectedTrackType === 'route' }"
          @click="onTrackTypeChange('route')"
        >
          <i class="fa-solid fa-map"></i>
          {{ t('trackType.route') }} ({{ routeCount }})
        </button>
      </div>

      <!-- Main Content -->
      <div class="modal-body">
        <!-- Left Column: Segment List -->
        <div class="segment-list-column">
          <div class="segment-list-container">
            <div v-if="loading" class="loading-state">
              <div class="loading-spinner">
                <i class="fa-solid fa-spinner fa-spin"></i>
              </div>
              <p>{{ t('editor.searchingSegments') }}...</p>
            </div>

            <div v-else-if="segments.length === 0" class="empty-state">
              <i class="fa-solid fa-search"></i>
              <p>{{ t('editor.noSegmentsFound') }}</p>
              <small>{{ t('editor.tryDifferentArea') }}</small>
            </div>

            <div v-else class="segment-cards">
              <SegmentImportCard
                v-for="segment in sortedSegments"
                :key="segment.id"
                :segment="segment"
                :distance="getSegmentDistanceFromCenter(segment)"
                :map="map"
                @click="onSegmentClick"
                @hover="onSegmentHover"
                @leave="onSegmentLeave"
                @show-trace="onShowTrace"
                @hide-trace="onHideTrace"
              />
            </div>
          </div>
        </div>

        <!-- Right Column: Map -->
        <div class="map-column">
          <div class="map-container">
            <div ref="mapContainer" class="map"></div>
            <!-- Fixed Center Marker -->
            <div class="fixed-center-marker" :title="t('editor.searchCenter')">📍</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, onUnmounted, ref, nextTick, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import L from 'leaflet'
import type { TrackResponse, GPXDataResponse } from '../types'
import { haversineDistance, getBoundingBoxCenter } from '../utils/distance'
import { parseGPXData } from '../utils/gpxParser'
import { useStravaApi } from '../composables/useStravaApi'
import SegmentImportCard from './SegmentImportCard.vue'

const { t } = useI18n()

// Strava authentication
const { authState, isAuthenticated } = useStravaApi()

// Props
const props = defineProps<{
  isOpen: boolean
}>()

// Emits
const emit = defineEmits<{
  close: []
  import: [segment: TrackResponse]
}>()

// Map instance
const mapContainer = ref<HTMLElement | null>(null)
let map: any = null

// Segments data
const segments = ref<TrackResponse[]>([])
const loading = ref(false)
const selectedTrackType = ref<'segment' | 'route'>('segment')
const searchLimit = ref<number>(50)

// Map state
let previousMapBounds: any = null
let hoverRectangle: any = null
let tracePolyline: any = null
const currentMapLayers = new Map<string, any>()
let searchTimeout: number | null = null
let eventSource: EventSource | null = null
let isSearching = false

// GPX data cache
const gpxDataCache = new Map<number, any>()
const loadingGPXData = new Set<number>()

// Computed properties for counts
const segmentCount = computed(() => {
  return segments.value.filter((segment) => segment.track_type === 'segment').length
})

const routeCount = computed(() => {
  return segments.value.filter((segment) => segment.track_type === 'route').length
})

// Computed property to sort segments by distance from map center and apply limit
const sortedSegments = computed(() => {
  if (!map || segments.value.length === 0 || typeof map.getCenter !== 'function') {
    return segments.value.slice(0, searchLimit.value)
  }

  try {
    const mapCenter = map.getCenter()
    const centerLat = mapCenter.lat
    const centerLng = mapCenter.lng

    const sorted = [...segments.value].sort((a, b) => {
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

    // Apply the limit after sorting
    return sorted.slice(0, searchLimit.value)
  } catch (error) {
    console.warn('Error calculating segment distances:', error)
    return segments.value.slice(0, searchLimit.value)
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

// Initialize map
const initializeMap = async () => {
  if (!mapContainer.value) {
    return
  }

  await nextTick()

  // Destroy existing map
  if (map) {
    map.remove()
  }

  if (!mapContainer.value || mapContainer.value.offsetHeight === 0) {
    nextTick(() => {
      setTimeout(() => {
        initializeMap()
      }, 100)
    })
    return
  }

  try {
    map = L.map(mapContainer.value, {
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

    // Set initial view to Lyon, France
    map.setView([46.942728, 4.033681], 14)

    // Add scale control
    L.control
      .scale({
        position: 'bottomright',
        metric: true,
        imperial: false
      })
      .addTo(map)

    // Add custom Max results control
    const MaxResultsControl = L.Control.extend({
      onAdd: function () {
        const container = L.DomUtil.create('div', 'max-results-control')

        const label = L.DomUtil.create('label', 'max-results-label', container)
        label.innerHTML = `<i class="fa-solid fa-list-ol"></i> ${t('editor.maxResults')}:`

        const select = L.DomUtil.create('select', 'max-results-select', container)
        select.id = 'limit-select'
        select.value = searchLimit.value.toString()

        const options = [
          { value: '25', text: '25' },
          { value: '50', text: '50' },
          { value: '75', text: '75' },
          { value: '100', text: '100' }
        ]

        options.forEach((option) => {
          const optionElement = L.DomUtil.create('option', '', select)
          optionElement.value = option.value
          optionElement.textContent = option.text
        })

        // Add event listener
        L.DomEvent.on(select, 'change', function () {
          searchLimit.value = parseInt(select.value)
          onLimitChange()
        })

        // Prevent map events when interacting with control
        L.DomEvent.disableClickPropagation(container)
        L.DomEvent.disableScrollPropagation(container)

        return container
      }
    })

    new MaxResultsControl({ position: 'bottomleft' }).addTo(map)

    // Force map to recalculate its size
    setTimeout(() => {
      if (map) {
        map.invalidateSize()
      }
    }, 100)

    previousMapBounds = map.getBounds()

    // Add event listeners
    map.on('moveend', handleMapMoveEnd)
    map.on('dragend', handleMapMoveEnd)
    map.on('viewreset', handleMapMoveEnd)
    map.on('zoomend', handleMapMoveEnd)

    // Initial search
    searchSegmentsInView()
  } catch (error) {
    console.error('Error initializing map:', error)
  }
}

// Handle map movement
function handleMapMoveEnd() {
  if (!map || !previousMapBounds) {
    debouncedSearchSegments()
    return
  }

  const currentBounds = map.getBounds()
  const boundsWithinPrevious = previousMapBounds.contains(currentBounds)
  const centerMoved = !previousMapBounds.contains(currentBounds.getCenter())
  const boundsExpanded = !boundsWithinPrevious

  if (boundsExpanded || centerMoved) {
    debouncedSearchSegments()
  } else {
    updateSegmentCardsForCurrentView()
  }

  previousMapBounds = currentBounds
}

// Update segment cards for current view
function updateSegmentCardsForCurrentView() {
  if (!map) return

  const currentBounds = map.getBounds()
  const visibleSegments = segments.value.filter((segment) => {
    return (
      segment.bound_north > currentBounds.getSouth() &&
      segment.bound_south < currentBounds.getNorth() &&
      segment.bound_east > currentBounds.getWest() &&
      segment.bound_west < currentBounds.getEast()
    )
  })

  segments.value = visibleSegments

  const visibleSegmentIds = new Set(visibleSegments.map((s) => s.id.toString()))
  for (const [segmentId, layerData] of currentMapLayers.entries()) {
    if (!visibleSegmentIds.has(segmentId)) {
      if (layerData.rectangle) {
        map.removeLayer(layerData.rectangle)
      }
      currentMapLayers.delete(segmentId)
    }
  }
}

// Debounced search
function debouncedSearchSegments() {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }

  searchTimeout = window.setTimeout(() => {
    searchSegmentsInView()
  }, 200)
}

// Search segments in view
function searchSegmentsInView() {
  if (!map || isSearching) return

  if (searchTimeout) {
    clearTimeout(searchTimeout)
    searchTimeout = null
  }

  if (eventSource) {
    eventSource.close()
    eventSource = null
  }

  isSearching = true
  loading.value = true

  const isFirstSearch = segments.value.length === 0
  const isTrackTypeSwitch =
    segments.value.length > 0 &&
    segments.value.some((segment) => segment.track_type !== selectedTrackType.value)

  if (isFirstSearch || isTrackTypeSwitch) {
    segments.value = []
    map.eachLayer((layer: any) => {
      if (
        layer instanceof L.Rectangle ||
        layer instanceof L.Polyline ||
        layer instanceof L.CircleMarker
      ) {
        map.removeLayer(layer)
      }
    })
    currentMapLayers.clear()
    gpxDataCache.clear()
    loadingGPXData.clear()
  }

  if (hoverRectangle) {
    map.removeLayer(hoverRectangle)
    hoverRectangle = null
  }

  if (tracePolyline) {
    map.removeLayer(tracePolyline)
    tracePolyline = null
  }

  const bounds = map.getBounds()
  const params = new URLSearchParams({
    north: bounds.getNorth().toString(),
    south: bounds.getSouth().toString(),
    east: bounds.getEast().toString(),
    west: bounds.getWest().toString(),
    track_type: selectedTrackType.value,
    limit: searchLimit.value.toString()
  })

  // Add user_strava_id if authenticated and searching for routes
  if (
    selectedTrackType.value === 'route' &&
    isAuthenticated() &&
    authState.value.athlete?.id
  ) {
    params.append('user_strava_id', authState.value.athlete.id.toString())
  }

  const url = `http://localhost:8000/api/segments/search?${params}`

  setTimeout(() => {
    eventSource = new EventSource(url)

    eventSource.onmessage = (event) => {
      try {
        const data = event.data

        if (!isNaN(Number(data))) {
          return
        }

        if (data === '[DONE]') {
          if (map) {
            previousMapBounds = map.getBounds()
          }
          loading.value = false
          isSearching = false
          eventSource?.close()
          eventSource = null
          return
        }

        try {
          const track: TrackResponse = JSON.parse(data)
          const existingSegment = segments.value.find((s) => s.id === track.id)
          if (!existingSegment) {
            segments.value.push(track)
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

// Process track
function processTrack(track: TrackResponse) {
  const segmentId = track.id.toString()
  if (currentMapLayers.has(segmentId)) return

  if (!map) return

  // First, add bounding box immediately for quick visual feedback
  addBoundingBoxToMap(track, map)

  // Then fetch GPX data asynchronously for detailed rendering
  fetchAndRenderGPXData(track)
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
    const trackWithGPX = {
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
function renderGPXTrackOnMap(track: any) {
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

// Add GPX track to map
function addGPXTrackToMap(segment: any, gpxData: any, mapInstance: any) {
  if (!mapInstance) {
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

  // Create polyline for the track
  const polyline = L.polyline(trackPoints, {
    color: '#FF6600', // Orange color
    weight: 3,
    opacity: 0.8
  }).addTo(mapInstance)

  // Add click handler to import the segment
  polyline.on('click', () => {
    onSegmentClick(segment)
  })

  // Track the drawn layers to avoid duplicates
  const segmentId = segment.id.toString()
  currentMapLayers.set(segmentId, {
    polyline: polyline
  })
}

// Add bounding box to map
function addBoundingBoxToMap(segment: TrackResponse, mapInstance: any) {
  if (!mapInstance) return

  const segmentBounds = L.latLngBounds(
    [segment.bound_south, segment.bound_west],
    [segment.bound_north, segment.bound_east]
  )

  const rectangle = L.rectangle(segmentBounds, {
    color: '#FF6600',
    weight: 2,
    fillOpacity: 0.1
  }).addTo(mapInstance)

  rectangle.on('click', () => {
    onSegmentClick(segment)
  })

  const segmentId = segment.id.toString()
  currentMapLayers.set(segmentId, {
    rectangle: rectangle
  })
}

// Event handlers
function onSegmentClick(segment: TrackResponse) {
  emit('import', segment)
}

function onSegmentHover(segment: TrackResponse) {
  if (!map) return

  if (hoverRectangle) {
    map.removeLayer(hoverRectangle)
    hoverRectangle = null
  }

  const segmentBounds = L.latLngBounds(
    [segment.bound_south, segment.bound_west],
    [segment.bound_north, segment.bound_east]
  )

  hoverRectangle = L.rectangle(segmentBounds, {
    color: '#ff6b35',
    weight: 4,
    fillOpacity: 0.2,
    dashArray: '8, 8',
    interactive: false
  }).addTo(map)

  hoverRectangle.bringToFront()
}

function onSegmentLeave() {
  if (!map) return

  if (hoverRectangle) {
    map.removeLayer(hoverRectangle)
    hoverRectangle = null
  }
}

function onShowTrace() {
  // This function is no longer needed since traces are shown by default
  // It's kept for compatibility with SegmentImportCard but does nothing
}

function onHideTrace() {
  // This function is no longer needed since traces are shown by default
  // It's kept for compatibility with SegmentImportCard but does nothing
}

function onLimitChange() {
  if (map) {
    searchSegmentsInView()
  }
}

function onTrackTypeChange(newType: 'segment' | 'route') {
  selectedTrackType.value = newType
  if (map) {
    searchSegmentsInView()
  }
}

function closeModal() {
  emit('close')
}

// Cleanup
const destroyMap = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
    searchTimeout = null
  }

  if (eventSource) {
    eventSource.close()
    eventSource = null
  }

  if (map) {
    if (hoverRectangle) {
      map.removeLayer(hoverRectangle)
      hoverRectangle = null
    }
    if (tracePolyline) {
      map.removeLayer(tracePolyline)
      tracePolyline = null
    }
    map.remove()
    map = null
  }

  currentMapLayers.clear()
  isSearching = false
}

// Watch for modal open/close
watch(
  () => props.isOpen,
  (isOpen) => {
    if (isOpen) {
      // Reset all state when modal opens to ensure fresh data
      segments.value = []
      loading.value = false
      previousMapBounds = null
      gpxDataCache.clear()
      loadingGPXData.clear()
      isSearching = false

      nextTick(() => {
        if (!mapContainer.value) {
          // Wait a bit longer for the DOM to be fully rendered
          setTimeout(() => {
            if (mapContainer.value) {
              initializeMap()
            }
          }, 100)
        } else {
          initializeMap()
        }
      })
    } else {
      destroyMap()
    }
  },
  { immediate: true }
)

onMounted(() => {
  // Map initialization is handled by the watch function when modal opens
})

onUnmounted(() => {
  destroyMap()
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: white;
  border-radius: 12px;
  box-shadow:
    0 20px 25px -5px rgba(0, 0, 0, 0.1),
    0 10px 10px -5px rgba(0, 0, 0, 0.04);
  max-width: 95vw;
  height: 75vh;
  width: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

@media (min-width: 1200px) {
  .modal-content {
    max-width: 1200px;
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.modal-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #111827;
}

.modal-title i {
  color: var(--brand-500);
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: #f3f4f6;
  color: #6b7280;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: #e5e7eb;
  color: #374151;
}

.track-type-tabs {
  display: flex;
  gap: 0.5rem;
  padding: 0.2rem;
  background: #f8fafc;
  border-bottom: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.tab-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #6b7280;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  flex: 1;
}

.tab-button:hover {
  background: #e5e7eb;
  color: #374151;
}

.tab-button.active {
  background: #ffffff;
  color: var(--brand-primary);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #ffb366;
}

.tab-button i {
  font-size: 0.875rem;
}

.modal-body {
  display: grid;
  grid-template-columns: 1fr 1fr;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

.segment-list-column {
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e5e7eb;
  overflow: hidden;
}

.segment-list-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #6b7280;
  text-align: center;
}

.loading-spinner {
  font-size: 2rem;
  color: var(--brand-500);
  margin-bottom: 1rem;
}

.empty-state i {
  font-size: 3rem;
  color: #d1d5db;
  margin-bottom: 1rem;
}

.segment-cards {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.map-column {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.map-container {
  position: relative;
  flex: 1;
  overflow: hidden;
}

.map {
  height: 100%;
  width: 100%;
}

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

/* Max results control styles */
:global(.max-results-control) {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 8px 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 140px;
  backdrop-filter: blur(4px);
}

:global(.max-results-control:hover) {
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

:global(.max-results-label) {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #374151;
  font-weight: 500;
  white-space: nowrap;
  margin: 0;
  cursor: pointer;
}

:global(.max-results-label i) {
  color: #374151;
  font-size: 11px;
}

:global(.max-results-select) {
  padding: 4px 6px;
  border: 1px solid #d1d5db;
  border-radius: 3px;
  font-size: 11px;
  background: white;
  color: #374151;
  cursor: pointer;
  min-width: 50px;
  outline: none;
}

:global(.max-results-select:focus) {
  border-color: var(--brand-primary);
  box-shadow: 0 0 0 2px rgba(var(--brand-primary-rgb), 0.1);
}

:global(.max-results-select:hover) {
  border-color: #9ca3af;
}

/* Responsive design */
@media (max-width: 768px) {
  .modal-body {
    grid-template-columns: 1fr;
    grid-template-rows: 1fr 1fr;
  }

  .segment-list-column {
    border-right: none;
    border-bottom: 1px solid #e5e7eb;
  }
}
</style>
