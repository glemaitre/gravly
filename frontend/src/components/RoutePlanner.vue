<template>
  <div class="route-planner">
    <!-- Sidebar Menu -->
    <div class="sidebar-menu" :class="{ 'sidebar-open': showSidebar }">
      <div class="sidebar-content">
        <div class="sidebar-header">
          <button class="sidebar-close" @click="toggleSidebar">
            <i class="fa-solid fa-times"></i>
          </button>
        </div>

        <div class="sidebar-options">
          <h4 class="mode-toggle-title">{{ t('routePlanner.routingMode') }}</h4>
          <div class="mode-toggle-container">
            <div class="mode-toggle">
              <span class="toggle-label" :title="t('routePlanner.standardModeDesc')">
                {{ t('routePlanner.standardMode') }}
              </span>
              <label class="toggle-switch">
                <input
                  type="checkbox"
                  :checked="routeMode === 'startEnd'"
                  @change="onToggleMode"
                />
                <span class="toggle-slider"></span>
              </label>
              <span class="toggle-label" :title="t('routePlanner.startEndModeDesc')">
                {{ t('routePlanner.startEndMode') }}
              </span>
            </div>
          </div>
        </div>

        <!-- Guided Mode Todo List -->
        <div v-if="routeMode === 'startEnd'" class="guided-todo-list">
          <h4 class="todo-title">{{ t('routePlanner.guidedTodoList') }}</h4>
          <p class="todo-instructions">
            {{ t('routePlanner.guidedTodoInstructions') }}
          </p>
          <div class="todo-items">
            <div class="todo-item" :class="{ completed: startWaypoint }">
              <div class="todo-main-content">
                <div class="todo-checkbox">
                  <i v-if="startWaypoint" class="fa-solid fa-check"></i>
                  <i v-else class="fa-solid fa-spinner fa-spin waiting-icon"></i>
                </div>
                <div class="todo-content">
                  <span class="todo-text"> Set <strong>starting</strong> point </span>
                </div>
              </div>
              <div v-if="startWaypoint" class="todo-coordinates">
                <div class="coordinate-table">
                  <div class="coordinate-row">
                    <span class="coordinate-label">Lat:</span>
                    <span class="coordinate-value">{{
                      startWaypoint.lat.toFixed(6)
                    }}</span>
                  </div>
                  <div class="coordinate-row">
                    <span class="coordinate-label">Long:</span>
                    <span class="coordinate-value">{{
                      startWaypoint.lng.toFixed(6)
                    }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="todo-item" :class="{ completed: endWaypoint }">
              <div class="todo-main-content">
                <div class="todo-checkbox">
                  <i v-if="endWaypoint" class="fa-solid fa-check"></i>
                  <i v-else class="fa-solid fa-spinner fa-spin waiting-icon"></i>
                </div>
                <div class="todo-content">
                  <span class="todo-text"> Set <strong>ending</strong> point </span>
                </div>
              </div>
              <div v-if="endWaypoint" class="todo-coordinates">
                <div class="coordinate-table">
                  <div class="coordinate-row">
                    <span class="coordinate-label">Lat:</span>
                    <span class="coordinate-value">{{
                      endWaypoint.lat.toFixed(6)
                    }}</span>
                  </div>
                  <div class="coordinate-row">
                    <span class="coordinate-label">Long:</span>
                    <span class="coordinate-value">{{
                      endWaypoint.lng.toFixed(6)
                    }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Selected Segments -->
        <div
          v-if="routeMode === 'startEnd' && selectedSegments.length > 0"
          class="selected-segments-section"
        >
          <h4 class="selected-segments-title">
            {{ t('routePlanner.selectedSegments') }}
          </h4>
          <div class="selected-segments-list">
            <div
              v-for="segment in selectedSegments"
              :key="segment.id"
              class="selected-segment-item"
            >
              <div class="segment-info">
                <div class="segment-name">{{ segment.name }}</div>
                <div class="segment-meta">
                  <span class="segment-difficulty"
                    >{{ segment.difficulty_level }}/5</span
                  >
                  <span class="segment-type">{{ segment.track_type }}</span>
                </div>
              </div>
              <button
                class="remove-segment-btn"
                @click="deselectSegment(segment)"
                :title="t('routePlanner.removeSegment')"
              >
                <i class="fa-solid fa-times"></i>
              </button>
            </div>
          </div>
        </div>

        <!-- Generate Route Button -->
        <div
          v-if="routeMode === 'startEnd' && startWaypoint && endWaypoint"
          class="generate-route-section"
        >
          <button class="generate-route-btn" @click="generateStartEndRoute">
            <i class="fa-solid fa-route"></i>
            <span>{{ t('routePlanner.generateRoute') }}</span>
          </button>
        </div>
      </div>
    </div>

    <div class="map-container">
      <div id="route-map" class="map"></div>

      <!-- Top right corner controls -->
      <div class="map-controls">
        <div class="control-group">
          <button
            class="control-btn"
            @click="toggleSidebar"
            :title="t('routePlanner.routingMode')"
            :class="{ active: showSidebar }"
          >
            <i class="fa-solid fa-route"></i>
          </button>
          <button
            class="control-btn"
            @click="clearMap"
            :title="t('routePlanner.clearMap')"
          >
            <i class="fa-solid fa-trash"></i>
          </button>
          <button
            class="control-btn"
            @click="undo"
            :disabled="!canUndo"
            :title="t('routePlanner.undo')"
          >
            <i class="fa-solid fa-undo"></i>
          </button>
          <button
            class="control-btn"
            @click="redo"
            :disabled="!canRedo"
            :title="t('routePlanner.redo')"
          >
            <i class="fa-solid fa-redo"></i>
          </button>
        </div>
      </div>

      <!-- Bottom elevation section -->
      <div
        class="elevation-section"
        :class="{
          'elevation-expanded': showElevation,
          'sidebar-open': showSidebar
        }"
      >
        <!-- Resize Handle - Always visible when elevation is expanded -->
        <div
          v-if="showElevation"
          class="elevation-resize-handle"
          @mousedown="startElevationResize"
          @touchstart="startElevationResize"
          :title="t('routePlanner.resizeHandle')"
        >
          <div class="elevation-resize-handle-bar"></div>
        </div>

        <!-- Toggle button with integrated stats -->
        <div class="elevation-toggle" @click="toggleElevation">
          <div class="elevation-toggle-content">
            <div class="toggle-left">
              <i class="fa-solid fa-mountain"></i>
              <span class="elevation-toggle-text">{{ t('routePlanner.profile') }}</span>
              <div class="toggle-stats">
                <div class="toggle-stat" :title="t('routePlanner.totalDistance')">
                  <i class="fa-solid fa-route"></i>
                  <span>{{ routeDistance.toFixed(1) }} {{ t('routePlanner.km') }}</span>
                </div>
                <div class="toggle-stat" :title="t('routePlanner.elevationGain')">
                  <i class="fa-solid fa-arrow-trend-up"></i>
                  <span>{{ elevationStats.totalGain }}{{ t('routePlanner.m') }}</span>
                </div>
                <div class="toggle-stat" :title="t('routePlanner.elevationLoss')">
                  <i class="fa-solid fa-arrow-trend-down"></i>
                  <span>{{ elevationStats.totalLoss }}{{ t('routePlanner.m') }}</span>
                </div>
              </div>
            </div>
            <i class="fa-solid fa-chevron-up"></i>
          </div>
        </div>

        <!-- Elevation content -->
        <div
          class="elevation-content"
          v-if="showElevation"
          :style="{ height: elevationHeight + 'px' }"
        >
          <!-- Elevation error message -->
          <div v-if="elevationError" class="elevation-error">
            <i class="fa-solid fa-triangle-exclamation"></i>
            <span>{{ elevationError }}</span>
          </div>

          <!-- Elevation chart -->
          <div class="elevation-chart">
            <div class="chart-container">
              <canvas ref="elevationChartRef" class="elevation-chart-canvas"></canvas>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, onUnmounted, ref, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import L from 'leaflet'
import 'leaflet-routing-machine'
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  Title,
  CategoryScale,
  Filler,
  Tooltip
} from 'chart.js'
import type { TrackResponse, GPXDataResponse, TrackWithGPXDataResponse } from '../types'
import { parseGPXData } from '../utils/gpxParser'

// Register Chart.js components
Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  Title,
  CategoryScale,
  Filler,
  Tooltip
)
// Fix for Leaflet markers in Vite
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'
import markerRetina from 'leaflet/dist/images/marker-icon-2x.png'

// Fix Leaflet default markers
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerRetina,
  iconUrl: markerIcon,
  shadowUrl: markerShadow
})

const { t } = useI18n()

// Sidebar and mode state
const showSidebar = ref(false)
const routeMode = ref<'standard' | 'startEnd'>('standard')
const startWaypoint = ref<any>(null)
const endWaypoint = ref<any>(null)
const startEndMarkers: any[] = []

// Segment display state (for guided mode)
const availableSegments = ref<TrackResponse[]>([])
const selectedSegments = ref<TrackResponse[]>([])
const segmentMapLayers = new Map<string, { polyline: any; popup?: any }>()
const gpxDataCache = new Map<number, TrackWithGPXDataResponse>()
const loadingGPXData = new Set<number>()
const isSearchingSegments = ref(false)

// Map and routing state
let map: any = null
let routingControl: any = null
let waypoints: any[] = []
let routeLine: any = null
let routeToleranceBuffer: any = null // Invisible thick line for easier interaction
let waypointMarkers: any[] = []
let mapMarker: any = null // Marker for chart interaction

// Undo/Redo state management
const undoStack: any[][] = []
const redoStack: any[][] = []
const canUndo = ref(false)
const canRedo = ref(false)
const maxHistorySize = 50 // Limit history to prevent memory issues

// Elevation section state
const showElevation = ref(false)
const elevationStats = ref({
  totalGain: 0,
  totalLoss: 0,
  maxElevation: 0,
  minElevation: 0
})
const elevationError = ref<string | null>(null)

// Elevation section resize state
const elevationHeight = ref<number>(300) // Default height in pixels
const minElevationHeight = 150
const maxElevationHeight = 600
let isElevationResizing = false
let startY = 0
let startHeight = 0

// Chart data
const elevationChartRef = ref<HTMLCanvasElement | null>(null)
const elevationChart = ref<Chart | null>(null)
const routeDistance = ref(0)
const waypointChartIndices = ref<number[]>([]) // Indices of waypoints in the chart data
const currentPosition = ref<{
  lat: number
  lng: number
  distance: number
  elevation: number
} | null>(null)

// Chart event listeners for cleanup
let chartCanvasMouseLeaveListener: (() => void) | null = null
let chartContainerMouseLeaveListener: (() => void) | null = null

// Segment-based elevation system
interface ElevationSegment {
  startWaypointIndex: number
  endWaypointIndex: number
  startLatLng: any
  endLatLng: any
  distance: number
  sampledPoints: Array<{
    lat: number
    lng: number
    elevation: number
    distance: number
  }>
  isProcessed: boolean
  lastUpdated: number
  segmentHash: string // Unique hash for this segment
}

// Enhanced caching system with persistent storage
const elevationSegments = ref<ElevationSegment[]>([])
const elevationCache = new Map<
  string,
  Array<{ lat: number; lng: number; elevation: number; distance: number }>
>()
const actualRouteCoordinates = ref<Array<{ lat: number; lng: number }>>([]) // Store actual OSRM route coordinates

// Cache configuration
const CACHE_VERSION = '1.1' // Increment version to invalidate old cache with zeros
const CACHE_KEY = 'elevation_cache_v' + CACHE_VERSION
const MAX_SEGMENT_LENGTH = 5000 // 5km - segments longer than this will be chunked
const CHUNK_SIZE = 128 // Maximum points per API call

// Sentinel value to indicate failed elevation requests
const ELEVATION_FAILURE_SENTINEL = -9999

// Route persistence keys
const ROUTE_STORAGE_KEY = 'routePlanner_currentRoute'
const MAP_STATE_STORAGE_KEY = 'routePlanner_mapState' // eslint-disable-line no-unused-vars

// Cache management functions
function saveElevationCache() {
  try {
    const cacheData = {
      version: CACHE_VERSION,
      timestamp: Date.now(),
      cache: Object.fromEntries(elevationCache)
    }
    localStorage.setItem(CACHE_KEY, JSON.stringify(cacheData))
  } catch (error) {
    console.warn('Failed to save elevation cache:', error)
  }
}

function segmentHasFailedElevations(
  points: Array<{ lat: number; lng: number; elevation: number; distance: number }>
): boolean {
  return points.some((point) => point.elevation === ELEVATION_FAILURE_SENTINEL)
}

function loadElevationCache() {
  try {
    const cacheData = localStorage.getItem(CACHE_KEY)
    if (cacheData) {
      const parsed = JSON.parse(cacheData)
      if (parsed.version === CACHE_VERSION && parsed.cache) {
        elevationCache.clear()
        Object.entries(parsed.cache).forEach(([key, value]) => {
          elevationCache.set(
            key,
            value as Array<{
              lat: number
              lng: number
              elevation: number
              distance: number
            }>
          )
        })
        console.log(`Loaded ${elevationCache.size} cached elevation segments`)
      }
    }
  } catch (error) {
    console.warn('Failed to load elevation cache:', error)
  }
}

function createSegmentHash(
  startLat: number,
  startLng: number,
  endLat: number,
  endLng: number
): string {
  // Create a more precise hash using 7 decimal places for better accuracy
  const precision = 7
  const hash = `${startLat.toFixed(precision)},${startLng.toFixed(precision)}-${endLat.toFixed(precision)},${endLng.toFixed(precision)}`
  return hash
}

function shouldChunkSegment(distance: number): boolean {
  return distance > MAX_SEGMENT_LENGTH
}

function calculateOptimalSamplingDistance(distance: number): number {
  // Adaptive sampling: shorter segments get higher resolution
  if (distance < 1000) return 50 // 50m for < 1km
  if (distance < 5000) return 100 // 100m for 1-5km
  if (distance < 10000) return 200 // 200m for 5-10km
  return 300 // 300m for > 10km
}

function splitRouteIntoWaypointSegments(
  routeCoordinates: Array<{ lat: number; lng: number }>,
  waypoints: Array<{ latLng: any }>
): Array<Array<{ lat: number; lng: number }>> {
  const segments: Array<Array<{ lat: number; lng: number }>> = []

  for (let i = 0; i < waypoints.length - 1; i++) {
    const startWaypoint = waypoints[i].latLng
    const endWaypoint = waypoints[i + 1].latLng

    // Find the closest route points to each waypoint
    const startIndex = findClosestRoutePoint(routeCoordinates, startWaypoint)
    const endIndex = findClosestRoutePoint(routeCoordinates, endWaypoint)

    // Extract the segment between these points
    const segment = routeCoordinates.slice(startIndex, endIndex + 1)
    segments.push(segment)
  }

  return segments
}

function findClosestRoutePoint(
  routeCoordinates: Array<{ lat: number; lng: number }>,
  waypoint: { lat: number; lng: number }
): number {
  let closestIndex = 0
  let minDistance = Number.MAX_VALUE

  for (let i = 0; i < routeCoordinates.length; i++) {
    const distance =
      map?.distance(
        [routeCoordinates[i].lat, routeCoordinates[i].lng],
        [waypoint.lat, waypoint.lng]
      ) || Number.MAX_VALUE

    if (distance < minDistance) {
      minDistance = distance
      closestIndex = i
    }
  }

  return closestIndex
}

function sampleRouteSegmentEvery100Meters(
  segmentCoordinates: Array<{ lat: number; lng: number }>,
  startDistance: number
): Array<{ lat: number; lng: number; distance: number }> {
  if (segmentCoordinates.length < 2) {
    return []
  }

  const sampledPoints: Array<{ lat: number; lng: number; distance: number }> = []
  const targetInterval = 100 // 100 meters
  let totalDistance = startDistance
  let nextSampleDistance = Math.ceil(startDistance / targetInterval) * targetInterval // Round up to next 100m interval

  // Always include the first point if it's at the start distance
  if (startDistance === 0 || startDistance % targetInterval === 0) {
    sampledPoints.push({
      lat: segmentCoordinates[0].lat,
      lng: segmentCoordinates[0].lng,
      distance: startDistance
    })
  }

  for (let i = 1; i < segmentCoordinates.length; i++) {
    const prev = segmentCoordinates[i - 1]
    const curr = segmentCoordinates[i]

    // Calculate distance between consecutive points
    const segmentDistance = calculateDistance(prev.lat, prev.lng, curr.lat, curr.lng)
    const segmentStartDistance = totalDistance
    const segmentEndDistance = totalDistance + segmentDistance

    // Check if we need to sample points within this segment
    while (nextSampleDistance <= segmentEndDistance) {
      if (nextSampleDistance > segmentStartDistance) {
        // Interpolate point within this segment
        const ratio = (nextSampleDistance - segmentStartDistance) / segmentDistance
        const interpolatedLat = prev.lat + (curr.lat - prev.lat) * ratio
        const interpolatedLng = prev.lng + (curr.lng - prev.lng) * ratio

        sampledPoints.push({
          lat: interpolatedLat,
          lng: interpolatedLng,
          distance: nextSampleDistance
        })
      }
      nextSampleDistance += targetInterval
    }

    totalDistance += segmentDistance
  }

  // Always include the last point if it's not already included
  const lastCoord = segmentCoordinates[segmentCoordinates.length - 1]
  const lastSampledPoint = sampledPoints[sampledPoints.length - 1]
  if (
    !lastSampledPoint ||
    lastSampledPoint.lat !== lastCoord.lat ||
    lastSampledPoint.lng !== lastCoord.lng
  ) {
    sampledPoints.push({
      lat: lastCoord.lat,
      lng: lastCoord.lng,
      distance: totalDistance
    })
  }

  return sampledPoints
}

// Mouse interaction state
let mouseDownStartPoint: any = null
let mouseDownStartTime: number = 0
let isDragging = false
const dragThreshold = 5 // pixels
const clickTimeThreshold = 300 // milliseconds
let currentDragTarget: 'map' | 'waypoint' | 'route' | null = null
let draggedWaypointIndex: number = -1
let routeUpdateTimeout: any = null
let isWaypointDragActive = false // Flag to prevent marker rebuilding during drag
let markerUpdateTimeout: any = null // Throttle marker updates during drag

// Sidebar and mode management functions
function toggleSidebar() {
  showSidebar.value = !showSidebar.value
}

function onRouteModeChange() {
  if (routeMode.value === 'standard') {
    // Switch to standard mode - preserve route by converting start/end waypoints to regular waypoints
    preserveRouteFromStartEndMode()
    clearStartEndWaypoints(false) // Don't clear route - we're preserving it
  } else {
    // Switch to start/end mode - clear everything completely
    // We need to clear both regular waypoints AND start/end waypoints
    clearRoute() // Clear regular waypoints and routes
    clearStartEndWaypoints(true) // Clear start/end waypoints and any remaining routes
  }
}

function onToggleMode() {
  // Toggle between standard and startEnd modes
  routeMode.value = routeMode.value === 'standard' ? 'startEnd' : 'standard'
  onRouteModeChange()
}

function preserveRouteFromStartEndMode() {
  // If we have start and end waypoints, preserve ALL waypoints including intermediate ones
  if (startWaypoint.value && endWaypoint.value) {
    // Save state for undo functionality
    saveState()

    // Clear existing waypoint markers first (but preserve the waypoints array)
    waypointMarkers.forEach((marker) => {
      if (marker && map.hasLayer(marker)) {
        map.removeLayer(marker)
      }
    })
    waypointMarkers = []

    // If we have waypoints from guided mode (including intermediate ones created by dragging),
    // preserve them all. Otherwise, just use start and end waypoints.
    if (waypoints.length > 0) {
      // We have waypoints from guided mode - preserve them all
      // Rebuild markers for all preserved waypoints
      waypoints.forEach((waypoint, index) => {
        createWaypointMarker(index, waypoint.latLng)
      })
    } else {
      // No waypoints from guided mode - create waypoints from start/end points
      waypoints = []
      addWaypoint(startWaypoint.value)
      addWaypoint(endWaypoint.value)
    }

    // Update routing control with all waypoints
    if (routingControl) {
      routingControl.setWaypoints(waypoints)
    }

    // Save route after preserving waypoints
    saveCurrentRoute()
  }
}

function clearStartEndWaypoints(clearRoute = true) {
  startWaypoint.value = null
  endWaypoint.value = null

  // Remove start/end markers from map
  startEndMarkers.forEach((marker) => {
    if (marker && map.hasLayer(marker)) {
      map.removeLayer(marker)
    }
  })
  startEndMarkers.length = 0

  // Only clear route if explicitly requested
  if (clearRoute) {
    // Clear any route that was generated from start/end waypoints
    if (routeLine) {
      map.removeLayer(routeLine)
      routeLine = null
    }
    if (routeToleranceBuffer) {
      map.removeLayer(routeToleranceBuffer)
      routeToleranceBuffer = null
    }

    // Update routing control
    if (routingControl) {
      routingControl.setWaypoints([])
    }
  }
}

function addStartEndWaypoint(latlng: any) {
  if (!startWaypoint.value) {
    // Set start waypoint
    startWaypoint.value = latlng
    createStartEndMarker('start', latlng)
  } else if (!endWaypoint.value) {
    // Set end waypoint
    endWaypoint.value = latlng
    createStartEndMarker('end', latlng)
    // Don't generate route automatically - user will click the button
  } else {
    // Both waypoints are set, replace the end waypoint
    endWaypoint.value = latlng

    // Remove existing end marker
    const endMarker = startEndMarkers.find((marker) => marker.options.type === 'end')
    if (endMarker && map.hasLayer(endMarker)) {
      map.removeLayer(endMarker)
      const index = startEndMarkers.indexOf(endMarker)
      if (index > -1) {
        startEndMarkers.splice(index, 1)
      }
    }

    // Create new end marker
    createStartEndMarker('end', latlng)
    // Don't generate route automatically - user will click the button
  }
}

function createStartEndMarker(type: 'start' | 'end', latlng: any) {
  const isStart = type === 'start'
  const markerClass = isStart
    ? 'start-end-marker start-marker'
    : 'start-end-marker end-marker'
  const iconClass = isStart ? 'fa-play' : 'fa-stop'

  const markerIcon = L.divIcon({
    html: `<div class="${markerClass}"><i class="fa-solid ${iconClass}"></i></div>`,
    className: 'custom-start-end-marker',
    iconSize: [32, 32],
    iconAnchor: [16, 16]
  })

  const marker = L.marker(latlng, {
    icon: markerIcon,
    interactive: true,
    zIndexOffset: 600,
    type: type
  }).addTo(map)

  // Add click handler to remove waypoint
  marker.on('click', () => {
    removeStartEndWaypoint(type)
  })

  // Add hover effects
  marker.on('mouseover', () => {
    map.getContainer().style.cursor = 'pointer'
  })

  marker.on('mouseout', () => {
    map.getContainer().style.cursor =
      routeMode.value === 'standard' ? 'crosshair' : 'pointer'
  })

  startEndMarkers.push(marker)
}

function removeStartEndWaypoint(type: 'start' | 'end') {
  if (type === 'start') {
    startWaypoint.value = null
  } else {
    endWaypoint.value = null
  }

  // Remove marker from map
  const marker = startEndMarkers.find((m) => m.options.type === type)
  if (marker && map.hasLayer(marker)) {
    map.removeLayer(marker)
    const index = startEndMarkers.indexOf(marker)
    if (index > -1) {
      startEndMarkers.splice(index, 1)
    }
  }

  // Clear route if we remove a waypoint
  if (routeLine) {
    map.removeLayer(routeLine)
    routeLine = null
  }
  if (routeToleranceBuffer) {
    map.removeLayer(routeToleranceBuffer)
    routeToleranceBuffer = null
  }
}

function generateStartEndRoute() {
  if (!startWaypoint.value || !endWaypoint.value) {
    return
  }

  // Create waypoints for routing - start with start waypoint
  const routeWaypoints = [L.Routing.waypoint(startWaypoint.value)]

  // Add waypoints for selected segments
  if (selectedSegments.value.length > 0) {
    // Get segment waypoints from selected segments
    const segmentWaypoints = getSegmentWaypoints(selectedSegments.value)

    // Add segment waypoints to route
    routeWaypoints.push(...segmentWaypoints)
  }

  // Always end with the end waypoint
  routeWaypoints.push(L.Routing.waypoint(endWaypoint.value))

  // Update routing control to generate route using the same OSRM service
  if (routingControl) {
    routingControl.setWaypoints(routeWaypoints)
  }

  // Also update the waypoints array for consistency with standard mode
  waypoints = routeWaypoints

  // Clear any existing regular waypoint markers since we're in start/end mode
  waypointMarkers.forEach((marker) => {
    if (marker && map.hasLayer(marker)) {
      map.removeLayer(marker)
    }
  })
  waypointMarkers = []

  // Calculate route distance
  if (waypoints.length >= 2) {
    calculateRouteDistance()
  }

  // The route will be generated via the same 'routesfound' event handler
  // which will call createClickableRouteLine and calculateElevationStats
}

function getSegmentWaypoints(segments: TrackResponse[]): any[] {
  const waypoints: any[] = []

  for (const segment of segments) {
    // Get GPX data for this segment
    const gpxData = gpxDataCache.get(segment.id)
    if (!gpxData || !gpxData.gpx_xml_data) {
      console.warn(`No GPX data available for segment ${segment.id}`)
      continue
    }

    // Parse GPX data to get coordinates
    const fileId =
      segment.file_path.split('/').pop()?.replace('.gpx', '') || segment.id.toString()
    const parsedGPX = parseGPXData(gpxData.gpx_xml_data, fileId)

    if (!parsedGPX || !parsedGPX.points || parsedGPX.points.length === 0) {
      console.warn(`No valid GPX points found for segment ${segment.id}`)
      continue
    }

    // Use the start and end points of the segment as waypoints
    // This ensures the route passes through the segment
    const startPoint = parsedGPX.points[0]
    const endPoint = parsedGPX.points[parsedGPX.points.length - 1]

    if (startPoint && endPoint) {
      waypoints.push(L.Routing.waypoint([startPoint.latitude, startPoint.longitude]))
      waypoints.push(L.Routing.waypoint([endPoint.latitude, endPoint.longitude]))
    }
  }

  return waypoints
}

// Helper functions for segment popup formatting
function formatDistance(meters: number): string {
  if (meters < 1000) {
    return `${Math.round(meters)}m`
  }
  return `${(meters / 1000).toFixed(1)}km`
}

function formatElevation(meters: number): string {
  return `${Math.round(meters)}m`
}

function formatSurfaceType(surfaceType: string): string {
  return surfaceType.replace(/-/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
}

function formatTireType(tireType: string): string {
  if (!tireType) return ''
  return tireType.replace(/-/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
}

// Helper function to calculate zoom-responsive route line weight
function getZoomResponsiveWeight(zoomLevel: number): number {
  // 7px at zoom 18, decrease 1px per zoom level: weight = zoom - 11
  const baseWeight = zoomLevel - 11
  const minWeight = 3 // Minimum weight to keep line visible
  const maxWeight = 12 // Maximum weight to prevent too thick lines
  return Math.max(minWeight, Math.min(baseWeight, maxWeight))
}

// Helper function to calculate tolerance buffer weight for easier interaction
function getToleranceBufferWeight(zoomLevel: number): number {
  // Much more tolerance when zoomed out, moderate when zoomed in
  const baseBuffer = 30 - zoomLevel // Higher buffer at lower zoom levels
  const minBuffer = 12 // Increased minimum buffer for interaction
  const maxBuffer = 24 // Increased maximum buffer for better interaction
  return Math.max(minBuffer, Math.min(baseBuffer, maxBuffer))
}

// Initialize map
// Watch for elevation height changes to redraw chart
watch(elevationHeight, () => {
  if (elevationChart.value && showElevation.value) {
    setTimeout(() => {
      elevationChart.value?.resize()
    }, 100) // Small delay to ensure DOM has updated
  }
})

// Watch for route mode changes to load/clear segments
watch(routeMode, (newMode) => {
  if (newMode === 'startEnd') {
    // Don't load segments immediately - wait for both start and end waypoints to be set
    // loadSegmentsInBounds() - removed to delay search
  } else {
    // Clear segments when switching to free mode
    clearAllSegments()
  }

  // Update cursor when mode changes
  updateMapCursor()
})

// Watch for waypoint changes to update cursor in guided mode and load segments
watch([startWaypoint, endWaypoint], () => {
  if (routeMode.value === 'startEnd') {
    updateMapCursor()

    // Load segments when both start and end waypoints are set
    if (startWaypoint.value && endWaypoint.value) {
      loadSegmentsInBounds()
    } else {
      // Clear segments if either waypoint is removed
      clearAllSegments()
    }
  }
})

// Watch for map bounds changes to reload segments (debounced)
let segmentSearchTimeout: any = null
watch(
  () => map?.getBounds(),
  (newBounds) => {
    if (
      routeMode.value === 'startEnd' &&
      newBounds &&
      !isSearchingSegments.value &&
      startWaypoint.value &&
      endWaypoint.value
    ) {
      if (segmentSearchTimeout) {
        clearTimeout(segmentSearchTimeout)
      }
      segmentSearchTimeout = setTimeout(() => {
        loadSegmentsInBounds()
      }, 500) // Debounce for 500ms
    }
  },
  { deep: true }
)

onMounted(async () => {
  // Add CSS class to prevent scrollbars on the entire page
  document.body.classList.add('route-planner-active')
  document.documentElement.classList.add('route-planner-active')

  // Load elevation cache first
  loadElevationCache()

  await nextTick()
  initializeMap()

  // Load saved route after map is initialized
  loadSavedRoute()

  // Initialize route distance if there are waypoints
  if (waypoints.length >= 2) {
    calculateRouteDistance() // Calculate basic distance first
    // Don't calculate elevation stats here - wait for route to be fully loaded
  }
})

onUnmounted(() => {
  // Remove CSS class to restore normal scrolling
  document.body.classList.remove('route-planner-active')
  document.documentElement.classList.remove('route-planner-active')

  // Save current route and elevation cache before unmounting
  saveCurrentRoute()
  saveElevationCache()

  // Clean up elevation resize event listeners
  stopElevationResize()

  if (map) {
    map.remove()
  }
})

function initializeMap() {
  const mapContainer = document.getElementById('route-map')
  if (!mapContainer) return

  // Initialize map with OpenCycleMap tiles
  map = L.map('route-map', {
    center: [46.942728, 4.033681], // Mont-Beuvray parce que ca pique! (same as landing page)
    zoom: 14
    // zoomControl: true is the default, so we don't need to specify it
  })

  // Add OpenCycleMap tiles via backend proxy (secure API key handling)
  L.tileLayer('/api/map-tiles/{z}/{x}/{y}.png', {
    attribution:
      'Maps © <a href="https://www.thunderforest.com/">Thunderforest</a>, Data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18
  }).addTo(map!)

  // Add zoom change detection with logging
  map.on('zoomstart', () => {
    // eslint-disable-next-line no-unused-vars
    const _currentZoom = map.getZoom()
  })

  map.on('zoomend', () => {
    const newZoom = map.getZoom()
    const newWeight = getZoomResponsiveWeight(newZoom)
    const newBufferWeight = getToleranceBufferWeight(newZoom)

    if (routeLine && routeToleranceBuffer) {
      // Update both the visible route line and invisible tolerance buffer
      routeLine.setStyle({ weight: newWeight })
      routeToleranceBuffer.setStyle({ weight: newBufferWeight })
    } else {
      // No route line or buffer to update
    }
  })

  // Disable double-click waypoint addition
  map.on('dblclick', (e: any) => {
    e.originalEvent.preventDefault()
    e.originalEvent.stopPropagation()
    return false
  })

  // Prevent context menu on right click
  map.on('contextmenu', (e: any) => {
    e.originalEvent.preventDefault()
    return false
  })

  // Initialize routing control AFTER click handler
  initializeRoutingControl()

  // Initialize sophisticated mouse interaction system
  initializeMouseInteractions()

  // Set initial cursor based on current mode
  updateMapCursor()
}

function initializeMouseInteractions() {
  if (!map) return

  // Mouse down event handler
  map.on('mousedown', (e: any) => {
    mouseDownStartPoint = e.containerPoint
    mouseDownStartTime = Date.now()
    isDragging = false
    currentDragTarget = 'map' // Default to map

    // Add a tiny delay to allow route line handlers to fire first
    setTimeout(() => {}, 1)
  })

  // Mouse move event handler
  map.on('mousemove', (e: any) => {
    if (!mouseDownStartPoint) return

    const distance = e.containerPoint.distanceTo(mouseDownStartPoint)
    // eslint-disable-next-line no-unused-vars
    const _timeDiff = Date.now() - mouseDownStartTime

    if (!isDragging && distance > dragThreshold) {
      isDragging = true

      // Handle different drag targets
      if (currentDragTarget === 'waypoint' && draggedWaypointIndex >= 0) {
        handleWaypointDragStart(draggedWaypointIndex)
      } else if (currentDragTarget === 'route') {
        handleRouteDragStart(e)
      }
      // For map dragging, Leaflet handles it automatically
    }

    // Update dragged waypoint position
    if (isDragging && currentDragTarget === 'waypoint' && draggedWaypointIndex >= 0) {
      updateWaypointPosition(draggedWaypointIndex, e.latlng)
    }
  })

  // Mouse up event handler
  map.on('mouseup', (e: any) => {
    const timeDiff = Date.now() - mouseDownStartTime

    if (!isDragging && timeDiff < clickTimeThreshold && currentDragTarget === 'map') {
      // Simple click on map - handle based on mode
      if (routeMode.value === 'startEnd') {
        // In guided mode, only allow setting start/end waypoints if they're not already set
        if (!startWaypoint.value || !endWaypoint.value) {
          addStartEndWaypoint(e.latlng)
        }
        // If both start and end are set, clicks are ignored (only for segment selection)
      } else {
        addWaypoint(e.latlng)
      }
    } else if (isDragging) {
      // Handle drag end
      if (currentDragTarget === 'waypoint' && draggedWaypointIndex >= 0) {
        handleWaypointDragEnd(draggedWaypointIndex, e.latlng)
      } else if (currentDragTarget === 'route') {
        handleRouteDragEnd(e.latlng)
      }
    }
    // For clicks on waypoints or route lines, do nothing (as requested)

    // Reset interaction state
    resetMouseState()
  })
}

function resetMouseState() {
  // Clear any pending marker updates
  if (markerUpdateTimeout) {
    clearTimeout(markerUpdateTimeout)
    markerUpdateTimeout = null
  }

  // Re-enable map dragging if it was disabled during waypoint drag
  if (map && map.dragging && !map.dragging.enabled()) {
    map.dragging.enable()
  }

  // Reset cursor based on current mode
  updateMapCursor()

  mouseDownStartPoint = null
  mouseDownStartTime = 0
  isDragging = false
  currentDragTarget = null
  draggedWaypointIndex = -1
  isWaypointDragActive = false // Reset drag active flag
}

function handleWaypointDragStart(waypointIndex: number) {
  // Set drag active flag to prevent marker rebuilding
  isWaypointDragActive = true

  // CRITICAL: Disable map dragging to prevent interference
  if (map && map.dragging) {
    map.dragging.disable()
  }

  // Verify marker exists before drag
  if (waypointMarkers[waypointIndex]) {
    waypointMarkers[waypointIndex].getElement()?.classList.add('waypoint-dragging')
  } else {
    // Waypoint marker not found
  }

  // Change cursor to indicate dragging
  map.getContainer().style.cursor = 'grabbing'
}

function updateWaypointPosition(waypointIndex: number, newLatLng: any) {
  if (waypointIndex < 0 || waypointIndex >= waypoints.length) {
    return
  }

  // Update waypoint position
  waypoints[waypointIndex] = L.Routing.waypoint(newLatLng)

  // Throttle marker recreation to improve performance (but still be responsive)
  if (markerUpdateTimeout) {
    clearTimeout(markerUpdateTimeout)
  }

  markerUpdateTimeout = setTimeout(() => {
    // Remove existing marker if it exists
    if (
      waypointMarkers[waypointIndex] &&
      map.hasLayer(waypointMarkers[waypointIndex])
    ) {
      map.removeLayer(waypointMarkers[waypointIndex])
    }

    // Create new marker at the new position
    createWaypointMarkerDuringDrag(waypointIndex, newLatLng)
  }, 16) // ~60fps update rate
}

async function handleWaypointDragEnd(waypointIndex: number, finalLatLng: any) {
  // Save state after waypoint drag completes (position changed)
  saveState()

  // Clear any pending marker updates
  if (markerUpdateTimeout) {
    clearTimeout(markerUpdateTimeout)
    markerUpdateTimeout = null
  }

  // Reset drag active flag to allow marker rebuilding
  isWaypointDragActive = false

  // CRITICAL: Re-enable map dragging
  if (map && map.dragging) {
    map.dragging.enable()
  }

  // Recreate the marker with full interactivity restored
  createWaypointMarker(waypointIndex, finalLatLng)

  // Reset cursor
  map.getContainer().style.cursor = 'crosshair'

  // Force route update now that drag is complete
  if (routingControl) {
    routingControl.setWaypoints(waypoints)
  }

  // Update elevation chart if section is visible
  if (showElevation.value) {
    // Only update affected segments instead of recalculating everything
    await updateAffectedSegments(draggedWaypointIndex)
    await calculateStatsFromSegments()
    await updateChartFromSegments()
  }
}

function handleRouteDragStart(e: any) {
  // Disable map dragging for route drag operations too
  if (map && map.dragging) {
    map.dragging.disable()
  }

  // Save state before modifying waypoints
  saveState()

  // Find the best insertion point for a new waypoint
  const insertIndex = findBestInsertionPoint(e.latlng)

  // Create new waypoint at the drag start position
  const newWaypoint = L.Routing.waypoint(e.latlng)
  waypoints.splice(insertIndex, 0, newWaypoint)

  // CRITICAL: Rebuild all waypoint markers to keep indices in sync
  rebuildWaypointMarkers()

  // Save route after inserting waypoint
  saveCurrentRoute()

  // Set this new waypoint as the one being dragged
  draggedWaypointIndex = insertIndex
  currentDragTarget = 'waypoint' // Switch to waypoint dragging mode

  // Update routing control immediately with new waypoints
  if (routingControl) {
    routingControl.setWaypoints(waypoints)
  }

  // Change cursor
  map.getContainer().style.cursor = 'grabbing'
}

// eslint-disable-next-line no-unused-vars
function handleRouteDragEnd(_finalLatLng: any) {
  // Re-enable map dragging (safety check, should be handled by waypoint drag end)
  if (map && map.dragging && !map.dragging.enabled()) {
    map.dragging.enable()
  }

  debounceRouteUpdate()
}

function findBestInsertionPoint(clickLatLng: any): number {
  if (waypoints.length < 2) return waypoints.length

  let bestIndex = 1 // Default to insert after first waypoint
  let minDistance = Infinity

  // Find the route segment closest to the click point
  for (let i = 0; i < waypoints.length - 1; i++) {
    const start = waypoints[i].latLng
    const end = waypoints[i + 1].latLng

    // Calculate perpendicular distance to line segment
    const distance = calculateDistanceToLineSegment(clickLatLng, start, end)

    if (distance < minDistance) {
      minDistance = distance
      bestIndex = i + 1
    }
  }

  return bestIndex
}

function calculateDistanceToLineSegment(
  point: any,
  lineStart: any,
  lineEnd: any
): number {
  // Calculate the perpendicular distance from point to line segment
  const A = point.lat - lineStart.lat
  const B = point.lng - lineStart.lng
  const C = lineEnd.lat - lineStart.lat
  const D = lineEnd.lng - lineStart.lng

  const dot = A * C + B * D
  const lenSq = C * C + D * D

  // If the line segment has zero length, return distance to the point
  if (lenSq === 0) {
    return map.distance(point, lineStart)
  }

  const param = dot / lenSq

  let closestPoint
  if (param < 0) {
    // Closest point is before the start of the line segment
    closestPoint = lineStart
  } else if (param > 1) {
    // Closest point is after the end of the line segment
    closestPoint = lineEnd
  } else {
    // Closest point is on the line segment
    closestPoint = {
      lat: lineStart.lat + param * C,
      lng: lineStart.lng + param * D
    }
  }

  return map.distance(point, closestPoint)
}

function debounceRouteUpdate() {
  if (routeUpdateTimeout) {
    clearTimeout(routeUpdateTimeout)
  }

  // CRITICAL: Don't update route during active waypoint dragging
  if (isWaypointDragActive) {
    return
  }

  routeUpdateTimeout = setTimeout(() => {
    if (routingControl) {
      routingControl.setWaypoints(waypoints)
    }
  }, 200)
}

function initializeRoutingControl() {
  if (!map) return

  // Configure OSRM routing with annotations to get way IDs
  const routingOptions = {
    router: new L.Routing.OSRMv1({
      serviceUrl: 'https://routing.openstreetmap.de/routed-bike/route/v1',
      profile: 'cycling',
      useHints: false,
      // Add annotations parameter to get way IDs
      addWaypoints: false
    }),
    waypoints: waypoints,
    routeWhileDragging: false, // Disabled to prevent auto-zoom
    addWaypoints: false, // Disable automatic waypoint addition
    show: false, // Hide the routing control panel
    // Custom marker creation function to disable default markers
    // eslint-disable-next-line no-unused-vars
    createMarker: function (_i: number, _waypoint: any, _n: number) {
      // Return null to disable default markers - we handle our own
      return null
    },
    // Disable auto-zoom but keep route calculation
    fitSelectedRoutes: false,
    lineOptions: {
      styles: [{ color: '#ff6600', weight: 6, opacity: 0.8 }]
    }
  }

  routingControl = L.Routing.control(routingOptions).addTo(map!)

  // Listen for route changes
  routingControl.on('routesfound', (e: any) => {
    const routes = e.routes
    if (routes && routes.length > 0) {
      const route = routes[0]

      // Ensure all waypoints have markers - use rebuild to handle any index issues
      rebuildWaypointMarkers()

      // Create interactive route line
      setTimeout(() => {
        createClickableRouteLine(route)

        // Calculate elevation statistics after route line is created and route is fully processed
        setTimeout(() => {
          calculateElevationStats()
        }, 1000) // Give more time for route to be fully processed
      }, 100)
    }
  })

  // Listen for waypoint changes
  routingControl.on('waypointsspliced', (e: any) => {
    waypoints = e.waypoints

    // Save route when waypoints are modified by routing control
    saveCurrentRoute()
  })
}

function addWaypoint(latlng: any) {
  // Save state for undo functionality
  saveState()

  const newWaypoint = L.Routing.waypoint(latlng)
  const waypointIndex = waypoints.length
  waypoints.push(newWaypoint)

  // Save route after adding waypoint
  saveCurrentRoute()

  // Create draggable marker for this waypoint
  createWaypointMarker(waypointIndex, latlng)

  if (routingControl) {
    routingControl.setWaypoints(waypoints)
  }

  // Update route distance when waypoints change
  if (waypoints.length >= 2) {
    calculateRouteDistance() // Calculate basic distance first
    // Elevation stats will be calculated when route is fully loaded
  }

  // Auto-center on the newly added waypoint
  if (map) {
    map.setView([latlng.lat, latlng.lng], map.getZoom())
  }
}

function createWaypointMarker(index: number, latlng: any) {
  // Remove existing marker at this index if it exists
  if (waypointMarkers[index]) {
    map.removeLayer(waypointMarkers[index])
  }

  // Create custom waypoint marker
  const isStart = index === 0
  const isEnd = index === waypoints.length - 1 && waypoints.length > 1
  const markerClass = isStart
    ? 'waypoint-start'
    : isEnd
      ? 'waypoint-end'
      : 'waypoint-intermediate'

  const waypointIcon = L.divIcon({
    html: `<div class="waypoint-marker ${markerClass}">${index + 1}</div>`,
    className: 'custom-waypoint-marker',
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  })

  const marker = L.marker(latlng, {
    icon: waypointIcon,
    interactive: true,
    zIndexOffset: 500 // Lower z-index so route line (1500) can be clicked above it
  }).addTo(map)

  // Add mouse event handlers to the marker
  marker.on('mousedown', (e: any) => {
    L.DomEvent.stopPropagation(e)
    L.DomEvent.preventDefault(e)

    // Update mouse interaction state
    currentDragTarget = 'waypoint'
    draggedWaypointIndex = index
    mouseDownStartPoint = e.containerPoint
    mouseDownStartTime = Date.now()
    isDragging = false
  })

  // Add hover effects for waypoints
  marker.on('mouseover', () => {
    map.getContainer().style.cursor = 'grab'
  })

  marker.on('mouseout', () => {
    map.getContainer().style.cursor = 'crosshair'
  })

  // Store marker reference
  waypointMarkers[index] = marker

  // Update all existing markers to reflect new start/end positions
  updateWaypointMarkerStyles()
}

function createWaypointMarkerDuringDrag(index: number, latlng: any) {
  // Create custom waypoint marker with drag styling
  const isStart = index === 0
  const isEnd = index === waypoints.length - 1 && waypoints.length > 1
  const markerClass = isStart
    ? 'waypoint-start'
    : isEnd
      ? 'waypoint-end'
      : 'waypoint-intermediate'

  const waypointIcon = L.divIcon({
    html: `<div class="waypoint-marker ${markerClass} waypoint-dragging">${index + 1}</div>`,
    className: 'custom-waypoint-marker',
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  })

  const marker = L.marker(latlng, {
    icon: waypointIcon,
    interactive: false, // Disable interaction during drag to prevent conflicts
    zIndexOffset: 2000 // Higher z-index during drag to be above route line
  }).addTo(map)

  // Store marker reference
  waypointMarkers[index] = marker
}

function updateWaypointMarkerStyles() {
  waypointMarkers.forEach((marker, index) => {
    if (!marker) return

    const isStart = index === 0
    const isEnd = index === waypoints.length - 1 && waypoints.length > 1
    const markerClass = isStart
      ? 'waypoint-start'
      : isEnd
        ? 'waypoint-end'
        : 'waypoint-intermediate'

    const waypointIcon = L.divIcon({
      html: `<div class="waypoint-marker ${markerClass}">${index + 1}</div>`,
      className: 'custom-waypoint-marker',
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    })

    marker.setIcon(waypointIcon)
  })
}

function rebuildWaypointMarkers() {
  // CRITICAL: Don't rebuild markers during active waypoint dragging
  if (isWaypointDragActive) {
    return
  }

  // Clear all existing markers
  // eslint-disable-next-line no-unused-vars
  waypointMarkers.forEach((marker, _index) => {
    if (marker && map.hasLayer(marker)) {
      map.removeLayer(marker)
    }
  })
  waypointMarkers = []

  // Recreate markers for all waypoints
  waypoints.forEach((waypoint, index) => {
    if (waypoint && waypoint.latLng) {
      createWaypointMarker(index, waypoint.latLng)
    }
  })
}

// Helper functions for clean mouse interaction logic

// Create an interactive route line that supports dragging
function createClickableRouteLine(route: any) {
  // Remove existing route lines (both visible line and tolerance buffer)
  if (routeLine) {
    map.removeLayer(routeLine)
  }
  if (routeToleranceBuffer) {
    map.removeLayer(routeToleranceBuffer)
  }

  // Try to find existing route polyline on the map
  let existingPolyline = null
  map.eachLayer((layer: any) => {
    if (
      layer instanceof L.Polyline &&
      (layer.options.color === '#3388ff' || layer.options.color === '#ff6600')
    ) {
      // This is likely the routing control's polyline
      existingPolyline = layer
    }
  })

  let latLngs = []

  if (existingPolyline) {
    // Clone the existing polyline and make it interactive
    latLngs = (existingPolyline as any).getLatLngs()

    // Store the actual route coordinates for elevation calculation
    actualRouteCoordinates.value = latLngs.map((latlng: any) => ({
      lat: latlng.lat,
      lng: latlng.lng
    }))
  } else {
    // Fallback: try to extract coordinates from route data
    let coordinates = null

    // Method 1: Direct coordinates array
    if (route.coordinates && Array.isArray(route.coordinates)) {
      coordinates = route.coordinates
    }
    // Method 2: Routes array with coordinates
    else if (route.routes && Array.isArray(route.routes) && route.routes.length > 0) {
      if (route.routes[0].coordinates) {
        coordinates = route.routes[0].coordinates
      }
    }
    // Method 3: Instructions with coordinates
    else if (
      route.instructions &&
      Array.isArray(route.instructions) &&
      route.instructions.length > 0
    ) {
      if (route.instructions[0].coordinates) {
        coordinates = route.instructions[0].coordinates
      }
    }
    // Method 4: Check if route has latlngs property
    else if (route.latlngs && Array.isArray(route.latlngs)) {
      coordinates = route.latlngs
    }

    if (!coordinates || coordinates.length < 2) {
      return
    }

    // Convert coordinates to LatLng array
    try {
      if (
        coordinates[0] &&
        typeof coordinates[0] === 'object' &&
        'lat' in coordinates[0]
      ) {
        // Already LatLng objects
        latLngs = coordinates
      } else if (Array.isArray(coordinates[0]) && coordinates[0].length >= 2) {
        // Array of [lat, lng] pairs
        latLngs = coordinates.map((coord: any) => L.latLng(coord[0], coord[1]))
      } else {
        return
      }

      // Store the actual route coordinates for elevation calculation
      actualRouteCoordinates.value = latLngs.map((latlng: any) => ({
        lat: latlng.lat,
        lng: latlng.lng
      }))
      // eslint-disable-next-line no-unused-vars
    } catch (_error) {
      return
    }
  }

  if (latLngs.length < 2) {
    return
  }

  // Create two-layer route line system for better interaction tolerance
  const currentZoom = map.getZoom()
  const initialWeight = getZoomResponsiveWeight(currentZoom)
  const toleranceWeight = getToleranceBufferWeight(currentZoom)

  // 1. Create invisible tolerance buffer (thick, handles all mouse interactions)
  routeToleranceBuffer = L.polyline(latLngs, {
    color: '#ff6b35',
    weight: toleranceWeight,
    opacity: 0, // Completely invisible
    interactive: true,
    bubblingMouseEvents: false,
    pane: 'overlayPane'
  }).addTo(map)

  // 2. Create visible route line (thin, just for display)
  routeLine = L.polyline(latLngs, {
    color: '#ff6b35', // Orange color to distinguish from default
    weight: initialWeight,
    opacity: 0.7,
    interactive: false, // Not interactive - tolerance buffer handles interactions
    bubblingMouseEvents: false,
    pane: 'overlayPane'
  }).addTo(map)

  // Set higher z-index for both lines to be above waypoint markers
  if (routeToleranceBuffer._path) {
    routeToleranceBuffer._path.style.zIndex = '1500'
  }
  if (routeLine._path) {
    routeLine._path.style.zIndex = '1501' // Visible line slightly above tolerance buffer
  }

  // Log initial route line creation

  // Add mouse event handlers to the invisible tolerance buffer (better hit detection)
  routeToleranceBuffer.on('mousedown', (e: any) => {
    // CRITICAL: Stop propagation immediately to prevent map handler interference
    L.DomEvent.stopPropagation(e)
    L.DomEvent.preventDefault(e)

    // Force override the mouse interaction state for route dragging
    currentDragTarget = 'route'
    mouseDownStartPoint = e.containerPoint
    mouseDownStartTime = Date.now()
    isDragging = false

    return false // Additional event blocking
  })

  // Add hover effects - tolerance buffer detects hover, visible line changes appearance
  routeToleranceBuffer.on('mouseover', (e: any) => {
    if (routeLine && !isDragging) {
      const currentZoom = map.getZoom()
      const baseWeight = getZoomResponsiveWeight(currentZoom)
      // eslint-disable-next-line no-unused-vars
      const _bufferWeight = getToleranceBufferWeight(currentZoom)
      const hoverWeight = baseWeight + 5 // Add 5px for dramatic hover effect
      routeLine.setStyle({ opacity: 1.0, weight: hoverWeight })
      map.getContainer().style.cursor = 'grab'

      // Update cursor position on chart
      updateCursorPosition(e.latlng)
    }
  })

  routeToleranceBuffer.on('mouseout', () => {
    if (routeLine && !isDragging) {
      const currentZoom = map.getZoom()
      const baseWeight = getZoomResponsiveWeight(currentZoom)
      // eslint-disable-next-line no-unused-vars
      const _bufferWeight = getToleranceBufferWeight(currentZoom)
      routeLine.setStyle({ opacity: 0.7, weight: baseWeight })
      map.getContainer().style.cursor = 'crosshair'
    }
  })

  routeToleranceBuffer.on('mousemove', (e: any) => {
    if (routeLine && !isDragging) {
      // Update cursor position on chart as mouse moves
      updateCursorPosition(e.latlng)
    }
  })
}

// Utility functions

// Route persistence functions
function saveCurrentRoute() {
  if (waypoints.length === 0) {
    // Clear saved route if no waypoints
    localStorage.removeItem(ROUTE_STORAGE_KEY)
    return
  }

  const routeData = {
    waypoints: waypoints.map((wp) => ({
      lat: wp.latLng.lat,
      lng: wp.latLng.lng,
      name: wp.name || ''
    })),
    timestamp: new Date().toISOString()
  }

  try {
    localStorage.setItem(ROUTE_STORAGE_KEY, JSON.stringify(routeData))
  } catch (error) {
    console.error('Failed to save route to localStorage:', error)
  }
}

function loadSavedRoute() {
  try {
    const savedRoute = localStorage.getItem(ROUTE_STORAGE_KEY)
    if (!savedRoute) {
      return
    }

    const routeData = JSON.parse(savedRoute)
    if (!routeData.waypoints || routeData.waypoints.length === 0) {
      return
    }

    // Restore waypoints
    waypoints = routeData.waypoints.map((wpData: any) =>
      L.Routing.waypoint(L.latLng(wpData.lat, wpData.lng), wpData.name)
    )

    // Update routing control
    if (routingControl) {
      routingControl.setWaypoints(waypoints)
    }

    // Rebuild markers
    rebuildWaypointMarkers()

    // Center map on the restored route
    centerMapOnRoute()

    // Clear history stacks since we're loading a saved state
    undoStack.length = 0
    redoStack.length = 0
    updateHistoryButtonStates()
  } catch (error) {
    console.error('Failed to load saved route from localStorage:', error)
  }
}

function centerMapOnRoute() {
  if (!map || waypoints.length === 0) {
    return
  }

  try {
    // Create bounds from all waypoints
    const bounds = L.latLngBounds(waypoints.map((wp) => wp.latLng))

    // Fit map to show all waypoints with some padding
    map.fitBounds(bounds, {
      padding: [20, 20], // Add 20px padding around the route
      maxZoom: 16 // Don't zoom in too much for very short routes
    })
  } catch (error) {
    console.error('Failed to center map on route:', error)
  }
}

// History management functions
function saveState() {
  // Create deep copy of current waypoints
  const currentState = waypoints.map((wp) => ({
    lat: wp.latLng.lat,
    lng: wp.latLng.lng,
    name: wp.name || ''
  }))

  // Add to undo stack
  undoStack.push(currentState)

  // Limit stack size
  if (undoStack.length > maxHistorySize) {
    undoStack.shift()
  }

  // Clear redo stack when new action is performed
  redoStack.length = 0

  // Update button states
  updateHistoryButtonStates()
}

function undo() {
  if (undoStack.length === 0) return

  // Save current state to redo stack
  const currentState = waypoints.map((wp) => ({
    lat: wp.latLng.lat,
    lng: wp.latLng.lng,
    name: wp.name || ''
  }))
  redoStack.push(currentState)

  // Restore previous state
  const previousState = undoStack.pop()
  restoreWaypointsFromState(previousState!)

  updateHistoryButtonStates()
}

function redo() {
  if (redoStack.length === 0) return

  // Save current state to undo stack
  const currentState = waypoints.map((wp) => ({
    lat: wp.latLng.lat,
    lng: wp.latLng.lng,
    name: wp.name || ''
  }))
  undoStack.push(currentState)

  // Restore next state
  const nextState = redoStack.pop()
  restoreWaypointsFromState(nextState!)

  updateHistoryButtonStates()
}

function restoreWaypointsFromState(state: any[]) {
  // Clear current waypoints
  waypoints = []

  // Clear existing markers and routes
  waypointMarkers.forEach((marker) => {
    if (marker && map.hasLayer(marker)) {
      map.removeLayer(marker)
    }
  })
  waypointMarkers = []

  if (routeLine) {
    map.removeLayer(routeLine)
    routeLine = null
  }
  if (routeToleranceBuffer) {
    map.removeLayer(routeToleranceBuffer)
    routeToleranceBuffer = null
  }

  // Restore waypoints from state
  state.forEach((wpData: any) => {
    waypoints.push(L.Routing.waypoint(L.latLng(wpData.lat, wpData.lng), wpData.name))
  })

  // Update routing control
  if (routingControl) {
    routingControl.setWaypoints(waypoints)
  }

  // Calculate route distance when waypoints are restored
  if (waypoints.length >= 2) {
    calculateRouteDistance() // Calculate basic distance first
    // Elevation stats will be calculated when route is fully loaded
  }
}

function updateHistoryButtonStates() {
  canUndo.value = undoStack.length > 0
  canRedo.value = redoStack.length > 0
}

function clearMap() {
  // Save state before clearing
  if (waypoints.length > 0 || startWaypoint.value || endWaypoint.value) {
    saveState()
  }

  // Clear everything based on current mode
  if (routeMode.value === 'standard') {
    clearRoute()
  } else {
    clearStartEndWaypoints()
  }
}

// Elevation section functions
async function calculateElevationStats() {
  if (waypoints.length < 2) {
    elevationStats.value = {
      totalGain: 0,
      totalLoss: 0,
      maxElevation: 0,
      minElevation: 0
    }
    elevationSegments.value = []
    actualRouteCoordinates.value = []
    return
  }

  // Don't calculate elevation if we don't have actual route coordinates yet
  // This prevents premature API calls that cause CORS errors
  if (actualRouteCoordinates.value.length < 2) {
    console.log('Waiting for route coordinates before calculating elevation stats...')
    return
  }

  try {
    // Clear any previous elevation errors
    elevationError.value = null

    // Use intelligent elevation calculation with caching
    if (actualRouteCoordinates.value.length >= 2) {
      // Use actual route coordinates for better accuracy, but with caching
      await calculateElevationFromActualRouteWithCaching()
    } else {
      // Fall back to waypoint-based segments
      await updateElevationSegments()
      await calculateStatsFromSegments()
      await updateChartFromSegments()
    }
  } catch (error) {
    console.error('Failed to calculate elevation stats:', error)
    // Set zero stats and show error instead of using mock data
    elevationStats.value = {
      totalGain: 0,
      totalLoss: 0,
      maxElevation: 0,
      minElevation: 0
    }
    // Show user-friendly error message
    elevationError.value = t('routePlanner.elevationDataUnavailable')
  }
}

async function updateElevationChart(
  elevations: number[],
  sampledPoints?: Array<{ lat: number; lng: number; distance: number }>
) {
  if (elevations.length < 2 || !elevationChartRef.value) {
    // Don't reset routeDistance here - preserve the basic distance calculation
    return
  }

  let totalDistance: number
  let chartData: Array<{ x: number; y: number }>

  if (sampledPoints && sampledPoints.length > 0) {
    // Use detailed sampled points data
    totalDistance = sampledPoints[sampledPoints.length - 1].distance
    routeDistance.value = totalDistance / 1000 // Convert to km

    // Generate chart data from sampled points
    chartData = elevations.map((elevation, index) => ({
      x: (sampledPoints[index]?.distance || 0) / 1000, // Convert to km
      y: elevation
    }))
  } else {
    // Fallback to waypoint-based calculation
    const distances: number[] = [0]
    totalDistance = 0

    for (let i = 1; i < waypoints.length; i++) {
      const distance =
        map?.distance(waypoints[i - 1].latLng, waypoints[i].latLng) || 1000
      totalDistance += distance
      distances.push(totalDistance)
    }

    routeDistance.value = totalDistance / 1000 // Convert to km

    // Generate chart data from waypoint data
    chartData = elevations.map((elevation, index) => ({
      x: distances[index] / 1000, // Convert to km
      y: elevation
    }))
  }

  // Update waypoint chart indices for marker display
  if (sampledPoints && sampledPoints.length > 0) {
    // Find waypoint indices in segment-based sampled data
    waypointChartIndices.value = []

    for (const segment of elevationSegments.value) {
      if (!segment.isProcessed || segment.sampledPoints.length === 0) continue

      // Find start waypoint index in chart data
      const startWaypointIndex = waypointChartIndices.value.length
      if (startWaypointIndex === 0) {
        // First waypoint is at the beginning
        waypointChartIndices.value.push(0)
      }
    }

    // Add end waypoint index
    if (waypoints.length > 1) {
      waypointChartIndices.value.push(chartData.length - 1)
    }
  } else {
    // For waypoint-based data, each point corresponds to a waypoint
    waypointChartIndices.value = chartData.map((_, index) => index)
  }

  // Create or update Chart.js chart
  await initializeElevationChart(chartData, elevations, sampledPoints)
}

// eslint-disable-next-line no-unused-vars
function _getWaypointColor(index: number): string {
  const isStart = index === 0
  const isEnd = index === waypoints.length - 1 && waypoints.length > 1

  if (isStart) return '#f97316' // Orange
  if (isEnd) return '#ff6600' // Orange
  return '#6b7280' // Gray
}

function calculateNiceElevationScale(elevations: number[]) {
  // Filter out sentinel values before calculating scale
  const validElevations = elevations.filter(
    (elevation) => elevation !== ELEVATION_FAILURE_SENTINEL
  )

  if (validElevations.length === 0) {
    return {
      min: 0,
      max: 100,
      ticks: {
        stepSize: 20,
        callback: function (value: any) {
          return `${Math.round(value)}m`
        }
      }
    }
  }

  const minElev = Math.min(...validElevations)
  const maxElev = Math.max(...validElevations)

  // Use a fixed range to prevent chart expansion
  // Add padding but keep it reasonable
  const padding = Math.max(50, (maxElev - minElev) * 0.1) // 10% padding or minimum 50m
  const fixedMin = Math.max(0, minElev - padding)
  const fixedMax = maxElev + padding

  // Calculate nice tick interval based on the fixed range
  const range = fixedMax - fixedMin
  let tickInterval: number
  if (range <= 100) {
    tickInterval = 20
  } else if (range <= 200) {
    tickInterval = 50
  } else if (range <= 500) {
    tickInterval = 100
  } else {
    tickInterval = 200
  }

  return {
    min: fixedMin,
    max: fixedMax,
    ticks: {
      stepSize: tickInterval,
      callback: function (value: any) {
        return `${Math.round(value)}m`
      }
    }
  }
}

async function initializeElevationChart(
  chartData: Array<{ x: number; y: number }>,
  elevations: number[],
  sampledPoints?: Array<{ lat: number; lng: number; distance: number }>
) {
  if (!elevationChartRef.value) {
    return
  }

  // Check if chart is already initialized
  if (elevationChart.value) {
    elevationChart.value.destroy()
    elevationChart.value = null
  }

  // Clean up chart event listeners
  cleanupChartEventListeners()

  // Ensure canvas has proper dimensions
  // Let Chart.js handle canvas sizing automatically
  // Don't manually set canvas.width and canvas.height as it can cause infinite growth

  // Create chart
  elevationChart.value = new Chart(elevationChartRef.value, {
    type: 'line',
    data: {
      datasets: [
        {
          label: t('routePlanner.chartElevationLabel'),
          data: chartData,
          borderColor: '#ff6600',
          backgroundColor: 'rgba(255, 102, 0, 0.1)',
          fill: true,
          tension: 0.1,
          pointRadius: 0,
          pointHoverRadius: 6,
          parsing: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      resizeDelay: 0,
      interaction: {
        intersect: false,
        mode: 'index'
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: function (context) {
              const xValue = context[0].parsed.x
              return `${xValue.toFixed(2)} km`
            },
            label: function (context) {
              const yValue = context.parsed.y
              return `Elevation: ${Math.round(yValue)} m`
            }
          }
        }
      },
      scales: {
        x: {
          type: 'linear',
          display: true,
          title: {
            display: true,
            text: t('routePlanner.chartDistance')
          },
          min: 0,
          max: chartData[chartData.length - 1]?.x || 1,
          ticks: {
            callback: function (value: any) {
              return `${Number(value).toFixed(1)} ${t('routePlanner.km')}`
            }
          }
        },
        y: {
          display: true,
          title: {
            display: true,
            text: t('routePlanner.chartElevation')
          },
          ...calculateNiceElevationScale(elevations)
        }
      },
      onHover: (event: any, activeElements: any) => {
        if (activeElements.length > 0) {
          const pointIndex = activeElements[0].index
          updateCursorPositionFromChart(pointIndex, sampledPoints)
        } else {
          // Hide the chart marker when mouse leaves the chart (no active elements)
          hideChartMarker()
        }
      }
    }
  })

  // Add explicit mouse event listeners to the chart canvas for better detection
  if (elevationChartRef.value) {
    const canvas = elevationChartRef.value

    // Clean up existing listeners if any
    cleanupChartEventListeners()

    // Create new listeners
    chartCanvasMouseLeaveListener = () => {
      hideChartMarker()
    }

    chartContainerMouseLeaveListener = () => {
      hideChartMarker()
    }

    // Hide marker when mouse leaves the canvas
    canvas.addEventListener('mouseleave', chartCanvasMouseLeaveListener)

    // Hide marker when mouse leaves the chart container
    const chartContainer = canvas.closest('.chart-container')
    if (chartContainer) {
      chartContainer.addEventListener('mouseleave', chartContainerMouseLeaveListener)
    }
  }
}

function updateCursorPositionFromChart(
  pointIndex: number,
  sampledPoints?: Array<{ lat: number; lng: number; distance: number }>
) {
  if (!sampledPoints || pointIndex < 0 || pointIndex >= sampledPoints.length) return

  // Only show marker if elevation section is visible
  if (!showElevation.value) {
    hideChartMarker()
    return
  }

  const point = sampledPoints[pointIndex]

  // Update current position
  currentPosition.value = {
    lat: point.lat,
    lng: point.lng,
    distance: point.distance / 1000, // Convert to km
    elevation: 0 // Will be updated when we have elevation data
  }

  // Update marker position with animation
  if (mapMarker) {
    mapMarker.setLatLng([point.lat, point.lng])
  } else {
    // Create marker if it doesn't exist
    const markerIcon = L.divIcon({
      html: '<div class="chart-marker"></div>',
      className: 'custom-chart-marker',
      iconSize: [12, 12],
      iconAnchor: [6, 6]
    })

    mapMarker = L.marker([point.lat, point.lng], {
      icon: markerIcon,
      zIndexOffset: 1000
    }).addTo(map)
  }
}

function hideChartMarker() {
  // Hide the chart marker when not hovering over the chart
  if (mapMarker && map) {
    map.removeLayer(mapMarker)
    mapMarker = null
  }
  // Clear current position
  currentPosition.value = null
}

function cleanupChartEventListeners() {
  // Clean up chart event listeners
  if (elevationChartRef.value && chartCanvasMouseLeaveListener) {
    elevationChartRef.value.removeEventListener(
      'mouseleave',
      chartCanvasMouseLeaveListener
    )
    chartCanvasMouseLeaveListener = null
  }
  if (elevationChartRef.value && chartContainerMouseLeaveListener) {
    const chartContainer = elevationChartRef.value.closest('.chart-container')
    if (chartContainer) {
      chartContainer.removeEventListener('mouseleave', chartContainerMouseLeaveListener)
    }
    chartContainerMouseLeaveListener = null
  }
}

function updateCursorPosition(latlng: any) {
  // Only show marker if elevation section is visible
  if (!showElevation.value) {
    hideChartMarker()
    return
  }

  // Use actual route coordinates if available, otherwise fall back to segments
  let sampledPoints: Array<{
    lat: number
    lng: number
    distance: number
    elevation?: number
  }> = []

  if (actualRouteCoordinates.value.length >= 2) {
    // Use actual route coordinates sampled at 100m intervals
    sampledPoints = sampleRouteEvery100Meters(actualRouteCoordinates.value)
  } else {
    // Fallback: Get all sampled points from segments
    let cumulativeDistance = 0

    for (const segment of elevationSegments.value) {
      if (!segment.isProcessed || segment.sampledPoints.length === 0) continue

      // Add points with cumulative distance
      const segmentPoints = segment.sampledPoints.map((point) => ({
        ...point,
        distance: cumulativeDistance + point.distance
      }))

      sampledPoints.push(...segmentPoints)
      cumulativeDistance += segment.distance
    }
  }

  if (sampledPoints.length === 0) return

  // Find closest point on the actual route
  let closestPoint = sampledPoints[0]
  let minDistance = Infinity

  for (let i = 0; i < sampledPoints.length; i++) {
    const point = sampledPoints[i]
    const distance = map?.distance(latlng, [point.lat, point.lng]) || Infinity
    if (distance < minDistance) {
      minDistance = distance
      closestPoint = point
    }
  }

  // Update current position
  currentPosition.value = {
    lat: closestPoint.lat,
    lng: closestPoint.lng,
    distance: closestPoint.distance / 1000, // Convert to km
    elevation: closestPoint.elevation || 0
  }

  // Update marker position with animation
  if (mapMarker) {
    mapMarker.setLatLng([closestPoint.lat, closestPoint.lng])
  }
}

// Segment-based elevation functions
async function updateElevationSegments() {
  console.log('Updating elevation segments with intelligent caching...')
  const newSegments: ElevationSegment[] = []
  let segmentsProcessed = 0
  let segmentsFromCache = 0

  for (let i = 0; i < waypoints.length - 1; i++) {
    const startPoint = waypoints[i].latLng
    const endPoint = waypoints[i + 1].latLng
    const distance = map?.distance(startPoint, endPoint) || 1000

    // Create unique segment hash
    const segmentHash = createSegmentHash(
      startPoint.lat,
      startPoint.lng,
      endPoint.lat,
      endPoint.lng
    )

    // Check if we already have this exact segment processed
    const existingSegment = elevationSegments.value.find(
      (seg) => seg.segmentHash === segmentHash && seg.isProcessed
    )

    if (existingSegment) {
      // Segment is identical and processed, reuse it
      newSegments.push(existingSegment)
      segmentsFromCache++
      continue
    }

    // Create new segment
    const segment: ElevationSegment = {
      startWaypointIndex: i,
      endWaypointIndex: i + 1,
      startLatLng: startPoint,
      endLatLng: endPoint,
      distance,
      sampledPoints: [],
      isProcessed: false,
      lastUpdated: Date.now(),
      segmentHash
    }

    // Check cache first
    if (elevationCache.has(segmentHash)) {
      const cachedPoints = elevationCache.get(segmentHash)!

      // Check if cached segment contains failed elevation requests
      if (segmentHasFailedElevations(cachedPoints)) {
        console.log(`Segment ${i}-${i + 1} has failed elevations, retrying`)
        // Process segment to retry failed elevation requests
        try {
          segment.sampledPoints = await processSegmentElevationIntelligent(segment)
          elevationCache.set(segmentHash, segment.sampledPoints)
          segment.isProcessed = true
          segmentsProcessed++
          console.log(
            `Retried and updated segment ${i}-${i + 1} with ${segment.sampledPoints.length} points`
          )
          // Save cache after successful retry
          saveElevationCache()
        } catch (error) {
          // If retry fails, keep using cached data (including sentinel values)
          console.error(
            `Retry failed for segment ${i}-${i + 1}, using cached data:`,
            error
          )
          segment.sampledPoints = cachedPoints
          segment.isProcessed = true
        }
      } else {
        segment.sampledPoints = cachedPoints
        segment.isProcessed = true
        segmentsFromCache++
        console.log(`Loaded segment ${i}-${i + 1} from cache`)
      }
    } else {
      // Process new segment with intelligent chunking
      try {
        segment.sampledPoints = await processSegmentElevationIntelligent(segment)
        elevationCache.set(segmentHash, segment.sampledPoints)
        segment.isProcessed = true
        segmentsProcessed++
        console.log(
          `Processed new segment ${i}-${i + 1} (${segment.sampledPoints.length} points)`
        )

        // Save cache after each successful segment
        saveElevationCache()
      } catch (error) {
        console.error(`Failed to process segment ${i}-${i + 1}:`, error)
        // Don't throw error, continue with other segments
        segment.sampledPoints = []
        segment.isProcessed = false
      }
    }

    newSegments.push(segment)
  }

  elevationSegments.value = newSegments
  console.log(
    `Segment update complete: ${segmentsFromCache} from cache, ${segmentsProcessed} newly processed`
  )
}

async function processSegmentElevationIntelligent(
  segment: ElevationSegment
): Promise<Array<{ lat: number; lng: number; elevation: number; distance: number }>> {
  // Use adaptive sampling based on segment length
  const samplingDistance = calculateOptimalSamplingDistance(segment.distance)
  const numSamples = Math.max(2, Math.ceil(segment.distance / samplingDistance))

  console.log(
    `Processing segment ${segment.startWaypointIndex}-${segment.endWaypointIndex}: ${segment.distance.toFixed(0)}m with ${numSamples} samples`
  )

  // Check if we need to chunk this segment
  if (shouldChunkSegment(segment.distance)) {
    return await processChunkedSegmentElevation(segment, numSamples)
  }

  const sampledPoints: Array<{ lat: number; lng: number; distance: number }> = []

  // Generate sample points along the segment
  for (let i = 0; i <= numSamples; i++) {
    const t = i / numSamples
    const lat =
      segment.startLatLng.lat + (segment.endLatLng.lat - segment.startLatLng.lat) * t
    const lng =
      segment.startLatLng.lng + (segment.endLatLng.lng - segment.startLatLng.lng) * t
    const distance = segment.distance * t

    sampledPoints.push({ lat, lng, distance })
  }

  // Get elevation data for these points
  const elevations = await getElevationData(sampledPoints)

  // Combine with elevation data
  return sampledPoints.map((point, index) => ({
    ...point,
    elevation: elevations[index] || 0
  }))
}

async function processChunkedSegmentElevation(
  segment: ElevationSegment,
  totalSamples: number
): Promise<Array<{ lat: number; lng: number; elevation: number; distance: number }>> {
  console.log(
    `Chunking large segment ${segment.startWaypointIndex}-${segment.endWaypointIndex} (${totalSamples} samples)`
  )

  const allSampledPoints: Array<{
    lat: number
    lng: number
    elevation: number
    distance: number
  }> = []

  // Split into chunks
  const chunkSize = CHUNK_SIZE
  const numChunks = Math.ceil(totalSamples / chunkSize)

  for (let chunkIndex = 0; chunkIndex < numChunks; chunkIndex++) {
    const startIndex = chunkIndex * chunkSize
    const endIndex = Math.min(startIndex + chunkSize, totalSamples)
    const chunkSamples = endIndex - startIndex

    if (chunkSamples < 1) continue

    // Generate points for this chunk
    const chunkPoints: Array<{ lat: number; lng: number; distance: number }> = []

    for (let i = 0; i < chunkSamples; i++) {
      const globalIndex = startIndex + i
      const t = globalIndex / (totalSamples - 1)
      const lat =
        segment.startLatLng.lat + (segment.endLatLng.lat - segment.startLatLng.lat) * t
      const lng =
        segment.startLatLng.lng + (segment.endLatLng.lng - segment.startLatLng.lng) * t
      const distance = segment.distance * t

      chunkPoints.push({ lat, lng, distance })
    }

    // Get elevation data for this chunk
    try {
      const chunkElevations = await getElevationData(chunkPoints)
      const chunkWithElevations = chunkPoints.map((point, index) => ({
        ...point,
        elevation: chunkElevations[index] || 0
      }))

      allSampledPoints.push(...chunkWithElevations)

      // Small delay between chunks to respect rate limits
      if (chunkIndex < numChunks - 1) {
        await new Promise((resolve) => setTimeout(resolve, 200))
      }
    } catch (error) {
      console.error(`Failed to process chunk ${chunkIndex + 1}/${numChunks}:`, error)
      // Fill with zeros for failed chunks
      const chunkWithZeros = chunkPoints.map((point) => ({ ...point, elevation: 0 }))
      allSampledPoints.push(...chunkWithZeros)
    }
  }

  return allSampledPoints
}

async function updateAffectedSegments(changedWaypointIndex: number) {
  console.log(
    `Updating affected segments due to waypoint ${changedWaypointIndex} change`
  )

  // Find segments that need to be updated based on the changed waypoint
  const segmentsToUpdate: number[] = []

  // The segment ending at the changed waypoint and the segment starting from it
  if (changedWaypointIndex > 0) {
    segmentsToUpdate.push(changedWaypointIndex - 1) // Previous segment
  }
  if (changedWaypointIndex < waypoints.length - 1) {
    segmentsToUpdate.push(changedWaypointIndex) // Current segment
  }

  // Update only the affected segments
  for (const segmentIndex of segmentsToUpdate) {
    if (segmentIndex < elevationSegments.value.length) {
      const segment = elevationSegments.value[segmentIndex]
      const startPoint = waypoints[segmentIndex].latLng
      const endPoint = waypoints[segmentIndex + 1].latLng

      // Create new segment hash
      const newSegmentHash = createSegmentHash(
        startPoint.lat,
        startPoint.lng,
        endPoint.lat,
        endPoint.lng
      )

      // Check if the segment has actually changed
      if (segment.segmentHash === newSegmentHash && segment.isProcessed) {
        console.log(`Segment ${segmentIndex} unchanged, skipping`)
        continue
      }

      // Clear old cache entry if hash changed
      if (segment.segmentHash && segment.segmentHash !== newSegmentHash) {
        elevationCache.delete(segment.segmentHash)
        console.log(`Cleared cache for changed segment ${segmentIndex}`)
      }

      // Update segment data
      segment.startLatLng = startPoint
      segment.endLatLng = endPoint
      segment.distance = map?.distance(startPoint, endPoint) || 1000
      segment.segmentHash = newSegmentHash
      segment.isProcessed = false
      segment.lastUpdated = Date.now()

      // Process the updated segment
      try {
        segment.sampledPoints = await processSegmentElevationIntelligent(segment)
        elevationCache.set(newSegmentHash, segment.sampledPoints)
        segment.isProcessed = true

        // Save cache after successful update
        saveElevationCache()
        console.log(
          `Updated segment ${segmentIndex} with ${segment.sampledPoints.length} points`
        )
      } catch (error) {
        console.error(`Failed to update segment ${segmentIndex}:`, error)
        // Don't throw error, continue with other segments
        segment.sampledPoints = []
        segment.isProcessed = false
      }
    }
  }
}

async function calculateStatsFromSegments() {
  const allElevations: number[] = []

  // Collect all elevations from segments
  for (const segment of elevationSegments.value) {
    if (!segment.isProcessed || segment.sampledPoints.length === 0) continue
    allElevations.push(...segment.sampledPoints.map((p) => p.elevation))
  }

  if (allElevations.length === 0) {
    elevationStats.value = {
      totalGain: 0,
      totalLoss: 0,
      maxElevation: 0,
      minElevation: 0
    }
    return
  }

  // Apply smoothing to all elevations before calculating stats
  const smoothedElevations = smoothElevationData(allElevations, 5)

  // Calculate gain/loss using smoothed elevations
  let totalGain = 0
  let totalLoss = 0

  for (let i = 1; i < smoothedElevations.length; i++) {
    const diff = smoothedElevations[i] - smoothedElevations[i - 1]
    if (diff > 0) {
      totalGain += diff
    } else {
      totalLoss += Math.abs(diff)
    }
  }

  elevationStats.value = {
    totalGain: Math.round(totalGain),
    totalLoss: Math.round(totalLoss),
    maxElevation: Math.round(Math.max(...smoothedElevations)),
    minElevation: Math.round(Math.min(...smoothedElevations))
  }
}

async function updateChartFromSegments() {
  // Combine all segment data into a single array
  const allPoints: Array<{
    lat: number
    lng: number
    elevation: number
    distance: number
  }> = []
  let cumulativeDistance = 0

  for (const segment of elevationSegments.value) {
    if (!segment.isProcessed || segment.sampledPoints.length === 0) continue

    // Add points with cumulative distance
    const segmentPoints = segment.sampledPoints.map((point) => ({
      ...point,
      distance: cumulativeDistance + point.distance
    }))

    allPoints.push(...segmentPoints)
    cumulativeDistance += segment.distance
  }

  if (allPoints.length === 0) {
    // Don't reset routeDistance here - preserve the basic distance calculation
    return
  }

  routeDistance.value = cumulativeDistance / 1000 // Convert to km

  // Apply smoothing to elevations before updating chart
  const originalElevations = allPoints.map((p) => p.elevation)
  const smoothedElevations = smoothElevationData(originalElevations, 5)

  // Update chart data with smoothed elevations
  const smoothedPoints = allPoints.map((point, index) => ({
    ...point,
    elevation: smoothedElevations[index] || point.elevation
  }))

  // Update chart with smoothed combined data
  updateElevationChart(smoothedElevations, smoothedPoints)
}

async function getElevationData(
  points: Array<{ lat: number; lng: number; distance: number }>
): Promise<number[]> {
  try {
    // Use OpenTopoData API (free elevation service)
    const elevations: number[] = []

    // Use the configured chunk size for consistency
    const batchSize = CHUNK_SIZE
    const batches = []

    for (let i = 0; i < points.length; i += batchSize) {
      batches.push(points.slice(i, i + batchSize))
    }

    console.log(
      `Processing ${points.length} elevation points in ${batches.length} batches of ${batchSize} points each`
    )

    for (let batchIndex = 0; batchIndex < batches.length; batchIndex++) {
      const batch = batches[batchIndex]
      const locations = batch.map((p) => `${p.lat},${p.lng}`).join('|')
      const url = `https://api.open-elevation.com/api/v1/lookup?locations=${locations}`

      let retryCount = 0
      const maxRetries = 3
      let success = false

      while (!success && retryCount <= maxRetries) {
        try {
          if (retryCount > 0) {
            // Exponential backoff: 1s, 2s, 4s
            const delay = Math.pow(2, retryCount - 1) * 1000
            console.log(
              `Retrying batch ${batchIndex + 1} after ${delay}ms delay (attempt ${retryCount + 1}/${maxRetries + 1})`
            )
            await new Promise((resolve) => setTimeout(resolve, delay))
          }

          const response = await fetch(url)

          if (!response.ok) {
            if (response.status === 429) {
              // Rate limited - wait longer before retry
              if (retryCount < maxRetries) {
                retryCount++
                continue
              }
            }
            throw new Error(`HTTP ${response.status}: ${response.statusText}`)
          }

          const data = await response.json()

          if (!data.results || !Array.isArray(data.results)) {
            throw new Error('Invalid API response format - missing results array')
          }

          const batchElevations = data.results.map((result: any) => result.elevation)
          elevations.push(...batchElevations)
          success = true

          console.log(
            `Successfully fetched elevation data for batch ${batchIndex + 1}/${batches.length}`
          )
        } catch (error) {
          retryCount++
          if (retryCount > maxRetries) {
            console.error(
              `Failed to fetch elevation data for batch ${batchIndex + 1} after ${maxRetries} retries:`,
              error
            )
            // Fill with sentinel values to indicate failed elevation requests
            // This allows us to retry these specific points later when conditions improve
            const batchElevations = new Array(batch.length).fill(
              ELEVATION_FAILURE_SENTINEL
            )
            elevations.push(...batchElevations)
            console.warn(
              `Using sentinel values for failed batch ${batchIndex + 1} - will retry later`
            )
            success = true
          }
        }
      }

      // Increased delay between batches to respect rate limits
      if (batchIndex < batches.length - 1) {
        await new Promise((resolve) => setTimeout(resolve, 500))
      }
    }

    return elevations
  } catch (error) {
    console.error('Complete failure to get elevation data:', error)
    throw new Error(
      `Failed to fetch elevation data: ${error instanceof Error ? error.message : String(error)}`
    )
  }
}

// Enhanced clearRoute to work with history
function clearRoute() {
  waypoints = []

  // Clear saved route from localStorage
  localStorage.removeItem(ROUTE_STORAGE_KEY)

  // Clear waypoint markers
  waypointMarkers.forEach((marker) => {
    if (marker && map.hasLayer(marker)) {
      map.removeLayer(marker)
    }
  })
  waypointMarkers = []

  if (routingControl) {
    routingControl.setWaypoints([])
  }

  // Remove route lines (both visible line and tolerance buffer)
  if (routeLine) {
    map.removeLayer(routeLine)
    routeLine = null
  }
  if (routeToleranceBuffer) {
    map.removeLayer(routeToleranceBuffer)
    routeToleranceBuffer = null
  }

  // Clear elevation chart data
  if (elevationChart.value) {
    elevationChart.value.destroy()
    elevationChart.value = null
  }

  // Clean up chart event listeners
  cleanupChartEventListeners()
  if (mapMarker) {
    map.removeLayer(mapMarker)
    mapMarker = null
  }
  routeDistance.value = 0
  waypointChartIndices.value = []
  currentPosition.value = null
  elevationSegments.value = []
  elevationCache.clear()
  actualRouteCoordinates.value = []
  elevationStats.value = {
    totalGain: 0,
    totalLoss: 0,
    maxElevation: 0,
    minElevation: 0
  }
}

// Toggle elevation section visibility
function toggleElevation() {
  showElevation.value = !showElevation.value
  if (showElevation.value) {
    // Show existing elevation data if available, don't recompute
    if (
      elevationSegments.value.length > 0 &&
      elevationSegments.value.some((seg) => seg.isProcessed)
    ) {
      console.log('Showing cached elevation data from segments')
      // Just display the existing data - no recomputation needed
      nextTick(() => {
        updateChartFromSegments()
      })
    } else if (actualRouteCoordinates.value.length >= 2) {
      console.log('No cached elevation data, calculating for first time')
      calculateElevationStats()
    } else {
      console.log(
        'Route not ready yet, elevation stats will be calculated when route is loaded'
      )
      // Set up a retry mechanism to calculate elevation when route becomes available
      const checkRouteReady = () => {
        if (actualRouteCoordinates.value.length >= 2) {
          calculateElevationStats()
        } else {
          // Retry after a short delay
          setTimeout(checkRouteReady, 500)
        }
      }
      setTimeout(checkRouteReady, 500)
    }
  } else {
    // Hide chart marker when elevation section is closed
    hideChartMarker()
  }
}

// Calculate elevation using actual OSRM route coordinates with intelligent segment-based caching
async function calculateElevationFromActualRouteWithCaching() {
  if (actualRouteCoordinates.value.length < 2 || waypoints.length < 2) {
    return
  }

  console.log('Calculating elevation from actual route with segment-based caching...')

  try {
    // Split the actual route into segments based on waypoints
    const routeSegments = splitRouteIntoWaypointSegments(
      actualRouteCoordinates.value,
      waypoints
    )

    const allElevationData: Array<{
      lat: number
      lng: number
      elevation: number
      distance: number
    }> = []
    let segmentsFromCache = 0
    let segmentsProcessed = 0
    let cumulativeDistance = 0

    for (let i = 0; i < routeSegments.length; i++) {
      const segment = routeSegments[i]
      const waypointStart = waypoints[i].latLng
      const waypointEnd = waypoints[i + 1].latLng

      // Create segment hash based on waypoint coordinates
      const segmentHash = createSegmentHash(
        waypointStart.lat,
        waypointStart.lng,
        waypointEnd.lat,
        waypointEnd.lng
      )

      let segmentElevationData: Array<{
        lat: number
        lng: number
        elevation: number
        distance: number
      }>

      // Check cache first
      if (elevationCache.has(segmentHash)) {
        const cachedData = elevationCache.get(segmentHash)!

        // Check if cached segment contains failed elevation requests
        if (segmentHasFailedElevations(cachedData)) {
          console.log(
            `Segment ${i}-${i + 1} has failed elevations, retrying for stats calculation`
          )
          try {
            // Retry elevation data for failed segments
            const sampledPoints = sampleRouteSegmentEvery100Meters(
              segment,
              cumulativeDistance
            )
            const elevations = await getElevationData(sampledPoints)
            segmentElevationData = sampledPoints.map((point: any, index: number) => ({
              ...point,
              elevation: elevations[index] || ELEVATION_FAILURE_SENTINEL
            }))

            // Update cache with retried data
            elevationCache.set(segmentHash, segmentElevationData)
            console.log(
              `Retried and cached segment ${i}-${i + 1} (${segmentElevationData.length} points)`
            )
          } catch (error) {
            console.error(
              `Retry failed for segment ${i}-${i + 1} stats, using cached data:`,
              error
            )
            segmentElevationData = cachedData
          }
        } else {
          segmentElevationData = cachedData
          segmentsFromCache++
          console.log(
            `Loaded segment ${i}-${i + 1} from cache (${segmentElevationData.length} points)`
          )
        }
      } else {
        // Process new segment
        console.log(
          `Processing new segment ${i}-${i + 1} (${segment.length} route points)`
        )

        // Sample points along this segment of the actual route
        const sampledPoints = sampleRouteSegmentEvery100Meters(
          segment,
          cumulativeDistance
        )

        // Get elevation data for sampled points
        const elevations = await getElevationData(sampledPoints)

        // Combine elevations with sampled points
        segmentElevationData = sampledPoints.map((point, index) => ({
          ...point,
          elevation: elevations[index] || 0
        }))

        // Store in cache
        elevationCache.set(segmentHash, segmentElevationData)
        segmentsProcessed++
        console.log(
          `Processed and cached segment ${i}-${i + 1} (${segmentElevationData.length} points)`
        )
      }

      // Add to combined data (distances are already cumulative from the sampling function)
      allElevationData.push(...segmentElevationData)

      // Update cumulative distance for next segment
      if (segmentElevationData.length > 0) {
        cumulativeDistance =
          segmentElevationData[segmentElevationData.length - 1].distance
      }
    }

    // Save cache after processing all segments
    if (segmentsProcessed > 0) {
      saveElevationCache()
    }

    console.log(
      `Segment processing complete: ${segmentsFromCache} from cache, ${segmentsProcessed} newly processed`
    )

    if (allElevationData.length === 0) {
      console.warn('No elevation data available')
      return
    }

    // Extract elevations for stats calculation
    const elevations = allElevationData.map((point) => point.elevation)

    // Apply smoothing and calculate stats
    const smoothedElevations = smoothElevationData(elevations, 5)
    await calculateStatsFromElevations(elevations)

    // Update chart with smoothed data
    const smoothedElevationData = allElevationData.map((point, index) => ({
      ...point,
      elevation: smoothedElevations[index] || point.elevation
    }))
    await updateElevationChart(smoothedElevations, smoothedElevationData)
  } catch (error) {
    console.error('Error calculating elevation from actual route:', error)
    throw error
  }
}

// Calculate distance between two lat/lng points in meters
function calculateDistance(
  lat1: number,
  lng1: number,
  lat2: number,
  lng2: number
): number {
  const R = 6371000 // Earth's radius in meters
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLng = ((lng2 - lng1) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLng / 2) *
      Math.sin(dLng / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

// Calculate basic route distance from waypoints
function calculateRouteDistance() {
  if (waypoints.length < 2) {
    routeDistance.value = 0
    return
  }

  let totalDistance = 0
  for (let i = 1; i < waypoints.length; i++) {
    const prev = waypoints[i - 1]
    const curr = waypoints[i]

    if (prev.latLng && curr.latLng) {
      const distance = calculateDistance(
        prev.latLng.lat,
        prev.latLng.lng,
        curr.latLng.lat,
        curr.latLng.lng
      )
      totalDistance += distance
    }
  }

  routeDistance.value = totalDistance / 1000 // Convert to km
}

// Sample points every 100 meters along the actual route
function sampleRouteEvery100Meters(
  coordinates: Array<{ lat: number; lng: number }>
): Array<{ lat: number; lng: number; distance: number }> {
  const sampledPoints: Array<{ lat: number; lng: number; distance: number }> = []
  const targetInterval = 100 // 100 meters
  let totalDistance = 0
  let nextSampleDistance = 0

  // Always include the first point
  sampledPoints.push({
    lat: coordinates[0].lat,
    lng: coordinates[0].lng,
    distance: 0
  })

  for (let i = 1; i < coordinates.length; i++) {
    const prev = coordinates[i - 1]
    const curr = coordinates[i]

    // Calculate distance between consecutive points
    const segmentDistance = calculateDistance(prev.lat, prev.lng, curr.lat, curr.lng)
    const segmentStartDistance = totalDistance
    const segmentEndDistance = totalDistance + segmentDistance

    // Check if we need to sample points within this segment
    while (nextSampleDistance <= segmentEndDistance) {
      if (nextSampleDistance > segmentStartDistance) {
        // Interpolate point within this segment
        const ratio = (nextSampleDistance - segmentStartDistance) / segmentDistance
        const interpolatedLat = prev.lat + (curr.lat - prev.lat) * ratio
        const interpolatedLng = prev.lng + (curr.lng - prev.lng) * ratio

        sampledPoints.push({
          lat: interpolatedLat,
          lng: interpolatedLng,
          distance: nextSampleDistance
        })
      }
      nextSampleDistance += targetInterval
    }

    totalDistance += segmentDistance
  }

  // Always include the last point if it's not already included
  const lastCoord = coordinates[coordinates.length - 1]
  const lastSampledPoint = sampledPoints[sampledPoints.length - 1]
  if (
    lastSampledPoint.lat !== lastCoord.lat ||
    lastSampledPoint.lng !== lastCoord.lng
  ) {
    sampledPoints.push({
      lat: lastCoord.lat,
      lng: lastCoord.lng,
      distance: totalDistance
    })
  }

  return sampledPoints
}

// Apply moving average smoothing to reduce elevation noise
function smoothElevationData(elevations: number[], windowSize: number = 5): number[] {
  if (elevations.length <= windowSize) {
    return elevations
  }

  const smoothed: number[] = []
  const halfWindow = Math.floor(windowSize / 2)

  // Handle first few points (use available points for average)
  for (let i = 0; i < halfWindow; i++) {
    const availablePoints = elevations.slice(0, i + halfWindow + 1)
    const average =
      availablePoints.reduce((sum, val) => sum + val, 0) / availablePoints.length
    smoothed.push(average)
  }

  // Handle middle points (full window available)
  for (let i = halfWindow; i < elevations.length - halfWindow; i++) {
    const window = elevations.slice(i - halfWindow, i + halfWindow + 1)
    const average = window.reduce((sum, val) => sum + val, 0) / window.length
    smoothed.push(average)
  }

  // Handle last few points (use available points for average)
  for (let i = elevations.length - halfWindow; i < elevations.length; i++) {
    const availablePoints = elevations.slice(i - halfWindow)
    const average =
      availablePoints.reduce((sum, val) => sum + val, 0) / availablePoints.length
    smoothed.push(average)
  }

  return smoothed
}

// Calculate statistics from elevation array
async function calculateStatsFromElevations(elevations: number[]) {
  // Filter out sentinel values (failed elevation requests)
  const validElevations = elevations.filter(
    (elevation) => elevation !== ELEVATION_FAILURE_SENTINEL
  )

  if (validElevations.length === 0) {
    elevationStats.value = {
      totalGain: 0,
      totalLoss: 0,
      maxElevation: 0,
      minElevation: 0
    }
    return
  }

  // Apply smoothing to reduce noise before calculating statistics
  const smoothedElevations = smoothElevationData(validElevations, 5) // 5-point moving average

  let totalGain = 0
  let totalLoss = 0
  const maxElevation = Math.max(...smoothedElevations)
  const minElevation = Math.min(...smoothedElevations)

  // Calculate gain and loss using smoothed data
  for (let i = 1; i < smoothedElevations.length; i++) {
    const prevElevation = smoothedElevations[i - 1]
    const currentElevation = smoothedElevations[i]
    const diff = currentElevation - prevElevation

    if (diff > 0) {
      totalGain += diff
    } else {
      totalLoss += Math.abs(diff)
    }
  }

  const finalStats = {
    totalGain: Math.round(totalGain),
    totalLoss: Math.round(totalLoss),
    maxElevation: Math.round(maxElevation),
    minElevation: Math.round(minElevation)
  }

  elevationStats.value = finalStats
}

// Elevation section resize functionality
function startElevationResize(event: MouseEvent | TouchEvent) {
  isElevationResizing = true
  const clientY = 'touches' in event ? event.touches[0].clientY : event.clientY
  startY = clientY
  startHeight = elevationHeight.value

  // Add global event listeners
  document.addEventListener('mousemove', handleElevationResize)
  document.addEventListener('mouseup', stopElevationResize)
  document.addEventListener('touchmove', handleElevationResize)
  document.addEventListener('touchend', stopElevationResize)

  // Prevent default to avoid text selection
  event.preventDefault()
}

function handleElevationResize(event: MouseEvent | TouchEvent) {
  if (!isElevationResizing) return

  const clientY = 'touches' in event ? event.touches[0].clientY : event.clientY
  const deltaY = startY - clientY // Inverted because we're resizing from bottom
  const newHeight = startHeight + deltaY

  // Constrain height within bounds
  elevationHeight.value = Math.max(
    minElevationHeight,
    Math.min(maxElevationHeight, newHeight)
  )

  // Invalidate map size to ensure proper rendering
  if (map) {
    setTimeout(() => {
      map.invalidateSize()
    }, 0)
  }

  // Update chart if it exists
  if (elevationChart.value) {
    setTimeout(() => {
      elevationChart.value?.resize()
    }, 0)
  }

  event.preventDefault()
}

function stopElevationResize() {
  isElevationResizing = false

  // Remove global event listeners
  document.removeEventListener('mousemove', handleElevationResize)
  document.removeEventListener('mouseup', stopElevationResize)
  document.removeEventListener('touchmove', handleElevationResize)
  document.removeEventListener('touchend', stopElevationResize)
}

function updateMapCursor() {
  if (!map) return

  if (routeMode.value === 'standard') {
    map.getContainer().style.cursor = 'crosshair'
  } else {
    // In guided mode, use pointer cursor when both waypoints are set (for segment selection)
    // or crosshair when waypoints still need to be set
    map.getContainer().style.cursor =
      startWaypoint.value && endWaypoint.value ? 'pointer' : 'crosshair'
  }
}

// Segment management functions for guided mode
async function loadSegmentsInBounds() {
  if (!map || routeMode.value !== 'startEnd' || isSearchingSegments.value) {
    return
  }

  isSearchingSegments.value = true

  try {
    const bounds = map.getBounds()
    const params = new URLSearchParams({
      north: bounds.getNorth().toString(),
      south: bounds.getSouth().toString(),
      east: bounds.getEast().toString(),
      west: bounds.getWest().toString(),
      track_type: 'segment',
      limit: '50'
    })

    const url = `http://localhost:8000/api/segments/search?${params}`
    const response = await fetch(url)

    if (!response.ok) {
      console.warn(`Failed to fetch segments: ${response.statusText}`)
      return
    }

    // Clear existing segments
    clearAllSegments()

    // Parse streaming response
    const reader = response.body?.getReader()
    if (!reader) return

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.trim().startsWith('data: ')) {
          const jsonData = line.slice(6) // Remove 'data: ' prefix

          // Skip [DONE] message from streaming API
          if (jsonData.trim() === '[DONE]') {
            continue
          }

          try {
            const segment: TrackResponse = JSON.parse(jsonData)

            // Validate segment has required properties
            if (!segment.id) {
              console.warn('Segment missing ID, skipping:', segment)
              continue
            }

            availableSegments.value.push(segment)

            // Load GPX data and render segment
            await loadSegmentGPXData(segment)
          } catch (error) {
            console.warn('Failed to parse segment data:', error, 'Raw line:', line)
          }
        }
      }
    }
  } catch (error) {
    console.error('Error loading segments:', error)
  } finally {
    isSearchingSegments.value = false
  }
}

async function loadSegmentGPXData(segment: TrackResponse) {
  // Validate segment has required properties
  if (!segment || !segment.id) {
    console.warn('Invalid segment data, cannot load GPX:', segment)
    return
  }

  // Check if we already have this GPX data cached
  if (gpxDataCache.has(segment.id)) {
    const cachedSegment = gpxDataCache.get(segment.id)!
    renderSegmentOnMap(cachedSegment)
    return
  }

  // Check if we're already loading this GPX data
  if (loadingGPXData.has(segment.id)) {
    return
  }

  loadingGPXData.add(segment.id)

  try {
    const response = await fetch(`http://localhost:8000/api/segments/${segment.id}/gpx`)
    if (!response.ok) {
      console.warn(
        `Failed to fetch GPX data for segment ${segment.id}: ${response.statusText}`
      )
      return
    }

    const gpxResponse: GPXDataResponse = await response.json()

    // Create a TrackWithGPXDataResponse object for caching and rendering
    const segmentWithGPX: TrackWithGPXDataResponse = {
      ...segment,
      gpx_data: null,
      gpx_xml_data: gpxResponse.gpx_xml_data
    }

    // Cache the GPX data
    gpxDataCache.set(segment.id, segmentWithGPX)

    // Render the segment on map
    renderSegmentOnMap(segmentWithGPX)
  } catch (error) {
    console.warn(`Error fetching GPX data for segment ${segment.id}:`, error)
  } finally {
    loadingGPXData.delete(segment.id)
  }
}

function renderSegmentOnMap(segment: TrackWithGPXDataResponse) {
  if (!segment.gpx_xml_data || !map) {
    return
  }

  // Parse GPX data
  const fileId =
    segment.file_path.split('/').pop()?.replace('.gpx', '') || segment.id.toString()
  const gpxData = parseGPXData(segment.gpx_xml_data, fileId)

  if (!gpxData || !gpxData.points || gpxData.points.length === 0) {
    return
  }

  // Convert GPX points to Leaflet lat/lng format
  const trackPoints = gpxData.points.map((point: any) => [
    point.latitude,
    point.longitude
  ])

  // Create polyline for the segment - black color as requested
  const polyline = L.polyline(trackPoints, {
    color: '#000000', // Black color as requested
    weight: 3,
    opacity: 0.8
  }).addTo(map)

  // Add a tooltip to indicate clickability for selection
  polyline.bindTooltip('Click to select segment for route', {
    permanent: false,
    direction: 'top',
    offset: [0, -10]
  })

  // Create popup with segment details
  const popupContent = createSegmentPopup(segment)
  const popup = L.popup({
    maxWidth: 340, // Match the card width
    className: 'segment-hover-popup',
    closeButton: false // Remove the close cross
  }).setContent(popupContent)

  // Add hover effects and popup trigger
  polyline.on('mouseover', () => {
    polyline.setStyle({
      weight: 5,
      opacity: 1
    })
    // Show popup on hover
    popup.setLatLng(polyline.getBounds().getCenter()).openOn(map)
  })

  polyline.on('mouseout', () => {
    polyline.setStyle({
      weight: 3,
      opacity: 0.8
    })
    // Close popup on mouseout (with small delay to prevent flickering)
    setTimeout(() => {
      if (map && popup) {
        map.closePopup(popup)
      }
    }, 100)
  })

  // Add click handler to select segment only
  polyline.on('click', () => {
    // Select the segment for route generation
    selectSegment(segment)
  })

  // Store the layer reference
  const segmentId = segment.id.toString()
  segmentMapLayers.set(segmentId, {
    polyline: polyline,
    popup: popup
  })
}

function createSegmentPopup(segment: TrackResponse): string {
  const isSelected = selectedSegments.value.some((s) => s.id === segment.id)

  // Get cached GPX data for stats
  const gpxData = gpxDataCache.get(segment.id)
  let statsHtml = ''

  if (gpxData && gpxData.gpx_xml_data) {
    const fileId =
      segment.file_path.split('/').pop()?.replace('.gpx', '') || segment.id.toString()
    const parsedGPX = parseGPXData(gpxData.gpx_xml_data, fileId)

    if (parsedGPX && parsedGPX.total_stats) {
      const stats = parsedGPX.total_stats
      statsHtml = `
        <div class="segment-stats">
          <div class="stat-item">
            <i class="fa-solid fa-route"></i>
            <div class="stat-content">
              <span class="stat-value">${formatDistance(stats.total_distance)}</span>
              <span class="stat-label">Distance</span>
            </div>
          </div>
          <div class="stat-item">
            <i class="fa-solid fa-arrow-trend-up"></i>
            <div class="stat-content">
              <span class="stat-value">${formatElevation(stats.total_elevation_gain)}</span>
              <span class="stat-label">Elevation Gain</span>
            </div>
          </div>
          <div class="stat-item">
            <i class="fa-solid fa-arrow-trend-down"></i>
            <div class="stat-content">
              <span class="stat-value">${formatElevation(stats.total_elevation_loss)}</span>
              <span class="stat-label">Elevation Loss</span>
            </div>
          </div>
        </div>
      `
    }
  }

  // If no stats available, show loading or fallback
  if (!statsHtml) {
    statsHtml = `
      <div class="segment-stats">
        <div class="stat-item">
          <i class="fa-solid fa-route"></i>
          <div class="stat-content">
            <span class="stat-value">...</span>
            <span class="stat-label">Distance</span>
          </div>
        </div>
        <div class="stat-item">
          <i class="fa-solid fa-arrow-trend-up"></i>
          <div class="stat-content">
            <span class="stat-value">...</span>
            <span class="stat-label">Elevation Gain</span>
          </div>
        </div>
        <div class="stat-item">
          <i class="fa-solid fa-arrow-trend-down"></i>
          <div class="stat-content">
            <span class="stat-value">...</span>
            <span class="stat-label">Elevation Loss</span>
          </div>
        </div>
      </div>
    `
  }

  return `
    <div class="segment-popup-card ${isSelected ? 'selected' : ''}">
      <div class="segment-card-header">
        <h4 class="segment-name" title="${segment.name}">
          ${segment.name}
        </h4>
      </div>

      <div class="segment-card-content">
        ${statsHtml}
      </div>

      <div class="segment-card-footer">
        <div class="segment-info-grid">
          <div class="info-section">
            <div class="info-label">Surface</div>
            <div class="info-value">
              <i class="fa-solid fa-road"></i>
              <span>${formatSurfaceType(segment.surface_type)}</span>
            </div>
          </div>

          <div class="info-section">
            <div class="info-label">Tires</div>
            <div class="tire-recommendations">
              <div class="tire-recommendation">
                <i class="fa-solid fa-sun"></i>
                <span class="tire-badge">${formatTireType(segment.tire_dry)}</span>
              </div>
              <div class="tire-recommendation">
                <i class="fa-solid fa-cloud-rain"></i>
                <span class="tire-badge">${formatTireType(segment.tire_wet)}</span>
              </div>
            </div>
          </div>

          <div class="info-section">
            <div class="info-label">Difficulty</div>
            <div class="info-value difficulty">
              <i class="fa-solid fa-signal"></i>
              <span>${segment.difficulty_level}/5</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
}

function selectSegment(segment: TrackResponse) {
  const existingIndex = selectedSegments.value.findIndex((s) => s.id === segment.id)

  if (existingIndex >= 0) {
    // Deselect segment
    selectedSegments.value.splice(existingIndex, 1)
  } else {
    // Select segment
    selectedSegments.value.push(segment)
  }

  // Update popup content to reflect new selection status
  const segmentId = segment.id.toString()
  const layerData = segmentMapLayers.get(segmentId)
  if (layerData && layerData.popup) {
    layerData.popup.setContent(createSegmentPopup(segment))
  }

  // Update polyline style to show selection
  if (layerData && layerData.polyline) {
    const isSelected = selectedSegments.value.some((s) => s.id === segment.id)
    layerData.polyline.setStyle({
      color: isSelected ? '#ff6600' : '#000000', // Orange when selected, black when not
      weight: isSelected ? 4 : 3
    })
  }
}

function deselectSegment(segment: TrackResponse) {
  const existingIndex = selectedSegments.value.findIndex((s) => s.id === segment.id)

  if (existingIndex >= 0) {
    // Remove from selected segments
    selectedSegments.value.splice(existingIndex, 1)

    // Update popup content to reflect new selection status
    const segmentId = segment.id.toString()
    const layerData = segmentMapLayers.get(segmentId)
    if (layerData && layerData.popup) {
      layerData.popup.setContent(createSegmentPopup(segment))
    }

    // Update polyline style to show deselection
    if (layerData && layerData.polyline) {
      layerData.polyline.setStyle({
        color: '#000000', // Black when not selected
        weight: 3
      })
    }
  }
}

function clearAllSegments() {
  // Remove all segment layers from map
  segmentMapLayers.forEach((layerData) => {
    if (layerData.polyline && map.hasLayer(layerData.polyline)) {
      map.removeLayer(layerData.polyline)
    }
  })

  // Clear all data structures
  segmentMapLayers.clear()
  availableSegments.value = []
  selectedSegments.value = []
  gpxDataCache.clear()
  loadingGPXData.clear()

  // Clear any pending search timeout
  if (segmentSearchTimeout) {
    clearTimeout(segmentSearchTimeout)
    segmentSearchTimeout = null
  }
}
</script>

<style scoped>
/* Global styles for route planner page - prevent scrollbars */
:global(body.route-planner-active) {
  overflow: hidden;
  height: 100vh;
  max-height: 100vh;
}

:global(html.route-planner-active) {
  overflow: hidden;
  height: 100vh;
  max-height: 100vh;
}
.route-planner {
  /* Use calc to subtract navbar height from viewport height */
  height: calc(100vh - var(--navbar-height));
  /* Use 100vw but ensure no horizontal overflow */
  width: 100vw;
  max-width: 100vw;
  /* Position absolutely to break out of normal flow */
  position: fixed;
  top: var(--navbar-height);
  left: 0;
  right: 0;
  bottom: 0;
  /* Ensure no scrollbars */
  overflow: hidden;
}

.map-container {
  width: 100%;
  height: 100%;
  position: relative;
  /* Ensure no overflow */
  overflow: hidden;
}

.map {
  width: 100%;
  height: 100%;
  /* Ensure map doesn't cause overflow */
  overflow: hidden;
}

/* Hide Leaflet Routing Machine control panel */
:global(.leaflet-routing-container) {
  display: none !important;
}

/* Hide zoom controls when sidebar is open */
.route-planner:has(.sidebar-menu.sidebar-open) :global(.leaflet-control-zoom) {
  display: none !important;
}

/* Map cursor styling */
.map {
  cursor: crosshair !important;
}

.map:active {
  cursor: grabbing !important;
}

/* Sidebar Menu Styles */
.sidebar-menu {
  position: fixed;
  top: var(--navbar-height);
  left: 0;
  width: 300px;
  height: calc(100vh - var(--navbar-height));
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-right: 1px solid rgba(229, 231, 235, 0.5);
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
  z-index: 2000;
  transform: translateX(-100%);
  transition: transform 0.3s ease-in-out;
  overflow-y: auto;
}

.sidebar-menu.sidebar-open {
  transform: translateX(0);
}

.sidebar-content {
  padding: 1.5rem;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
}

.sidebar-close {
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.sidebar-close:hover {
  background: rgba(239, 68, 68, 0.2);
  transform: scale(1.05);
}

.sidebar-options {
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid rgba(229, 231, 235, 0.5);
}

.mode-toggle-title {
  margin: 0 0 1rem 0;
  color: #374151;
  font-size: 1rem;
  font-weight: 600;
  text-align: center;
}

.mode-toggle-container {
  margin-bottom: 0;
  padding: 1rem;
  background: rgba(248, 250, 252, 0.8);
  border-radius: 8px;
  border: 1px solid rgba(229, 231, 235, 0.3);
  transition: all 0.2s ease;
}

.mode-toggle-container:hover {
  background: rgba(248, 250, 252, 1);
  border-color: rgba(255, 102, 0, 0.3);
}

.mode-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.toggle-label {
  font-weight: 500;
  color: #374151;
  font-size: 0.875rem;
  cursor: pointer;
  transition: color 0.2s ease;
}

.toggle-label:hover {
  color: var(--brand-primary);
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 24px;
  cursor: pointer;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #d1d5db;
  transition: 0.3s;
  border-radius: 24px;
}

.toggle-slider:before {
  position: absolute;
  content: '';
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.toggle-switch input:checked + .toggle-slider {
  background-color: var(--brand-primary);
}

.toggle-switch input:checked + .toggle-slider:before {
  transform: translateX(24px);
}

.guided-todo-list {
  background: rgba(255, 102, 0, 0.05);
  border: 1px solid rgba(255, 102, 0, 0.2);
  border-radius: 8px;
  padding: 1rem;
}

.todo-title {
  margin: 0 0 0.5rem 0;
  color: #374151;
  font-size: 1rem;
  font-weight: 600;
  text-align: center;
}

.todo-instructions {
  margin: 0 0 1rem 0;
  color: #6b7280;
  font-size: 0.75rem;
  text-align: center;
  font-style: italic;
}

.todo-items {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.todo-item {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 6px;
  border: 1px solid rgba(229, 231, 235, 0.5);
  transition: all 0.3s ease;
}

.todo-item:hover {
  background: rgba(255, 255, 255, 0.9);
  border-color: rgba(59, 130, 246, 0.3);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.todo-item.completed {
  background: rgba(34, 197, 94, 0.1);
  border-color: rgba(34, 197, 94, 0.3);
}

.todo-item.completed .todo-text {
  color: #059669;
  text-decoration: line-through;
  opacity: 0.8;
}

.todo-checkbox {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.todo-item:not(.completed) .todo-checkbox {
  color: #6b7280;
}

.todo-item.completed .todo-checkbox {
  color: #059669;
  background: rgba(34, 197, 94, 0.2);
}

.todo-checkbox i {
  font-size: 12px;
}

.todo-main-content {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.todo-content {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1;
}

.todo-text {
  color: #374151;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.3s ease;
  line-height: 1.4;
}

.todo-text strong {
  font-weight: 700;
  color: #1f2937;
}

.todo-coordinates {
  font-size: 0.75rem;
  color: #6b7280;
  font-family: 'Courier New', monospace;
  background: rgba(249, 250, 251, 0.8);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  border: 1px solid rgba(229, 231, 235, 0.5);
  transition: all 0.3s ease;
}

.todo-coordinates {
  width: 100%;
  margin-top: 0.5rem;
  text-align: center;
}

.coordinate-table {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.coordinate-row {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
}

.coordinate-label {
  font-weight: 500;
  color: #374151;
  min-width: 35px;
  text-align: right;
}

.coordinate-value {
  font-family: 'Courier New', monospace;
  color: #6b7280;
  min-width: 80px;
  text-align: left;
}

.waiting-icon {
  color: #ff6600;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Generate Route Section */
.generate-route-section {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
}

.generate-route-btn {
  width: 100%;
  padding: 0.75rem 1rem;
  background: #ff6600;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(255, 102, 0, 0.2);
}

.generate-route-btn:hover {
  background: #e65c00;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(255, 102, 0, 0.3);
}

.generate-route-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(255, 102, 0, 0.2);
}

.generate-route-btn i {
  font-size: 1rem;
}

/* Start/End Marker Styles */
:global(.custom-start-end-marker) {
  background: transparent;
  border: none;
}

:global(.start-end-marker) {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  transition: all 0.2s ease;
  border: 3px solid white;
  font-size: 0.75rem;
}

:global(.start-end-marker:hover) {
  transform: scale(1.2);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

:global(.start-marker) {
  background: #22c55e; /* Green for start */
  border-color: white;
}

:global(.end-marker) {
  background: #ef4444; /* Red for end */
  border-color: white;
}

/* Responsive adjustments for sidebar */
@media (max-width: 768px) {
  .sidebar-menu {
    width: 280px;
  }

  .sidebar-toggle {
    left: 0.75rem;
    width: 36px;
    height: 36px;
  }

  .sidebar-content {
    padding: 1rem;
  }

  .mode-toggle {
    flex-direction: column;
    gap: 0.75rem;
    text-align: center;
  }

  .toggle-label {
    font-size: 0.8rem;
  }

  .mode-toggle-container {
    padding: 0.75rem;
  }
}

/* Custom waypoint markers */
:global(.custom-waypoint-marker) {
  background: transparent;
  border: none;
}

:global(.waypoint-marker) {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: white;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  transition: all 0.2s ease;
  border: 2px solid white;
}

:global(.waypoint-marker:hover) {
  transform: scale(1.2);
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.4);
}

:global(.waypoint-start) {
  background: #f97316; /* Orange */
  border: 2px solid white;
}

:global(.waypoint-end) {
  background: #ff6600; /* Orange */
  border: 2px solid white;
}

:global(.waypoint-intermediate) {
  background: #6b7280; /* Gray */
  border: 2px solid white;
}

:global(.waypoint-dragging) {
  z-index: 1000;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
  }
}

/* Map controls in top right corner */
.map-controls {
  position: absolute;
  top: 1rem;
  right: 1rem;
  z-index: 1000;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.control-btn {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 6px;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  color: #374151;
}

.control-btn:hover:not(:disabled) {
  background: #f3f4f6;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.control-btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.control-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  color: #9ca3af;
}

/* Special styling for clear button */
.control-btn:first-child {
  background: #fff7ed;
  color: #ea580c;
}

.control-btn:first-child:hover:not(:disabled) {
  background: #fed7aa;
  color: #c2410c;
}

/* Active state for route button */
.control-btn.active {
  background: var(--brand-primary);
  border: 1px solid var(--brand-primary);
  color: white;
}

.control-btn.active:hover:not(:disabled) {
  background: var(--brand-primary-hover);
  border-color: var(--brand-primary-hover);
  color: white;
}

.control-btn.active i {
  color: white;
}

/* Elevation section styles */
.elevation-section {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border-top: 1px solid rgba(229, 231, 235, 0.5);
  box-shadow: 0 -4px 6px -1px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  transition: all 0.3s ease-in-out;
  transform: translateY(
    calc(100% - 30px)
  ); /* Show only toggle by default (30px height) */
  /* Ensure section doesn't exceed viewport height */
  max-height: calc(
    100vh - var(--navbar-height) - 100px
  ); /* Reserve space for map controls */
  overflow: hidden; /* Prevent content overflow */
  display: flex;
  flex-direction: column;
}

.elevation-expanded {
  transform: translateY(0); /* Show full content when expanded */
  background: rgba(255, 255, 255, 0.95); /* More opaque when expanded */
}

.elevation-section.sidebar-open {
  left: 300px; /* Start from the right edge of the sidebar */
}

.elevation-toggle {
  height: 30px;
  background: rgba(248, 250, 252, 0.8);
  backdrop-filter: blur(4px);
  border-bottom: 1px solid rgba(229, 231, 235, 0.5);
  cursor: pointer;
  display: flex;
  align-items: center;
  padding: 0 1rem;
  transition: background-color 0.2s ease;
}

.elevation-toggle:hover {
  background: rgba(241, 245, 249, 0.9);
}

.elevation-toggle-content {
  display: flex;
  align-items: center;
  gap: 1rem;
  width: 100%;
  justify-content: space-between;
}

.toggle-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
}

.toggle-stats {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-left: 0.5rem;
  flex-wrap: wrap;
}

.toggle-stat {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: #374151;
  font-weight: 500;
}

.toggle-stat i {
  font-size: 0.7rem;
  color: #6b7280;
  opacity: 0.9;
}

.elevation-toggle-content i:first-child {
  color: var(--brand-primary);
  font-size: 1.25rem;
}

.elevation-toggle-text {
  font-weight: 600;
  color: #374151;
  flex: 1;
  text-align: left;
  margin-left: 0.5rem;
}

.elevation-toggle-content i:last-child {
  color: #6b7280;
  font-size: 0.875rem;
  transition: transform 0.2s ease;
}

.elevation-expanded .elevation-toggle-content i:last-child {
  transform: rotate(180deg);
}

.elevation-content {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
  overflow: hidden; /* Prevent content overflow */
  display: flex;
  flex-direction: column;
  /* Height is now controlled by the :style binding */
}

/* Elevation Resize Handle */
.elevation-resize-handle {
  height: 8px;
  background: #ff6600;
  cursor: ns-resize;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(255, 102, 0, 0.2);
  border-radius: 4px;
  margin: 2px 8px; /* Reduced margin for smaller handle */
}

.elevation-resize-handle:hover {
  background: #e55a00;
  box-shadow: 0 2px 6px rgba(255, 102, 0, 0.3);
  transform: scaleY(1.2);
}

.elevation-resize-handle:active {
  background: #cc4d00;
  box-shadow: 0 1px 2px rgba(255, 102, 0, 0.4);
  transform: scaleY(1.1);
}

.elevation-resize-handle-bar {
  width: 40px;
  height: 4px;
  background: white;
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 10px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  position: relative;
}

.elevation-resize-handle:hover .elevation-resize-handle-bar {
  background: #fff5f0;
  transform: scale(1.05);
}

/* Vertical arrows to indicate resize direction */
.elevation-resize-handle-bar::before,
.elevation-resize-handle-bar::after {
  content: '';
  position: absolute;
  width: 0;
  height: 0;
  border-left: 3px solid transparent;
  border-right: 3px solid transparent;
}

.elevation-resize-handle-bar::before {
  top: -4px;
  border-bottom: 4px solid white;
}

.elevation-resize-handle-bar::after {
  bottom: -4px;
  border-top: 4px solid white;
}

.elevation-resize-handle:hover .elevation-resize-handle-bar::before,
.elevation-resize-handle:hover .elevation-resize-handle-bar::after {
  border-bottom-color: #fff5f0;
  border-top-color: #fff5f0;
}

.elevation-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 0.75rem 1rem;
  margin: 0.5rem;
  border-radius: 0.375rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.elevation-error i {
  font-size: 1rem;
  flex-shrink: 0;
}

.elevation-chart {
  padding: 0.3rem;
  flex: 1; /* Take remaining space in elevation-content */
  display: flex;
  flex-direction: column;
  min-height: 0; /* Allow flex item to shrink */
}

.chart-container {
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  flex: 1; /* Take remaining space in elevation-chart */
  position: relative;
  min-height: 120px; /* Minimum height for chart visibility */
}

.elevation-chart-canvas {
  width: 100%;
  height: 100%; /* Fill the container */
  display: block;
}

.chart-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #f8fafc;
  border-top: 1px solid #e5e7eb;
  font-size: 0.875rem;
  color: #6b7280;
}

.chart-distance {
  font-weight: 600;
  color: var(--brand-primary);
}

.chart-elevation-range {
  font-weight: 500;
}

/* Chart marker styling */
:global(.custom-chart-marker) {
  background: transparent;
  border: none;
}

:global(.chart-marker) {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #ff6600;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.7;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .elevation-section {
    /* Ensure mobile viewport fit */
    max-height: calc(100vh - var(--navbar-height) - 80px);
  }

  .elevation-section.sidebar-open {
    left: 280px; /* Adjusted for mobile sidebar width */
  }

  .elevation-stats {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
    padding: 1rem;
  }

  .elevation-stat {
    padding: 0.75rem;
  }

  .stat-value {
    font-size: 1.25rem;
  }

  .elevation-chart {
    padding: 1rem;
  }

  .elevation-chart-canvas {
    height: 100%; /* Fill the container on mobile */
  }
}

@media (max-width: 480px) {
  .elevation-section {
    max-height: calc(100vh - var(--navbar-height) - 60px);
  }

  .toggle-left {
    gap: 0.5rem;
  }

  .toggle-stats {
    gap: 0.5rem;
    margin-left: 0.25rem;
  }

  .toggle-stat {
    font-size: 0.7rem;
    gap: 0.2rem;
  }

  .toggle-stat i {
    font-size: 0.65rem;
  }

  .elevation-chart {
    padding: 0.75rem;
  }

  .elevation-chart-canvas {
    height: 100%; /* Fill the container on very small screens */
  }
}

/* Segment hover popup styles - compact version of SegmentImportCard */
:global(.segment-hover-popup .leaflet-popup-content-wrapper) {
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e1e5e9;
  padding: 0;
}

:global(.segment-hover-popup .leaflet-popup-content) {
  margin: 0;
  padding: 0;
}
:global(.segment-popup-card) {
  border: 1px solid #e1e5e9;
  border-radius: 6px;
  padding: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  position: relative;
  font-family: inherit;
  background: white;
  width: 340px; /* Increased width to 340px */
}

:global(.segment-popup-card.selected) {
  box-shadow: 0 3px 8px rgba(255, 107, 53, 0.3);
  transform: translateY(-1px);
  border-color: #ff6b35;
}

:global(.segment-card-header) {
  margin-bottom: 8px;
}

:global(.segment-name) {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: color 0.2s ease;
  line-height: 1.2;
}

:global(.segment-popup-card.selected .segment-name) {
  color: #ff6b35;
}

:global(.segment-card-content) {
  margin-bottom: 8px;
}

:global(.segment-stats) {
  display: flex;
  gap: 8px;
}

:global(.stat-item) {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  background: #f8fafc;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
  transition: background-color 0.2s ease;
  flex: 1;
}

:global(.stat-item i) {
  width: 20px;
  height: 20px;
  background: #f97316;
  color: white;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  flex-shrink: 0;
}

:global(.stat-content) {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

:global(.stat-label) {
  font-size: 0.6rem;
  color: #666;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

:global(.stat-value) {
  font-size: 0.75rem;
  color: #333;
  font-weight: 600;
}

:global(.segment-card-footer) {
  border-top: 1px solid #f0f0f0;
  padding-top: 8px;
  position: relative;
}

:global(.segment-info-grid) {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 8px;
}

:global(.info-section) {
  display: flex;
  flex-direction: column;
  gap: 2px;
  align-items: center;
  text-align: center;
}

:global(.info-label) {
  color: #666;
  font-weight: 500;
  font-size: 0.6rem;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  margin-bottom: 1px;
}

:global(.info-value) {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  font-size: 0.65rem;
  color: #333;
  font-weight: 500;
}

:global(.info-value i) {
  font-size: 0.7rem;
  color: #666;
}

:global(.info-value.difficulty) {
  color: #e67e22;
  font-weight: 600;
}

:global(.tire-recommendations) {
  display: flex;
  gap: 6px;
}

:global(.tire-recommendation) {
  display: flex;
  align-items: center;
  gap: 3px;
}

:global(.tire-recommendation i) {
  font-size: 0.7rem;
}

:global(.tire-recommendation .fa-sun) {
  color: #ff6600;
}

:global(.tire-recommendation .fa-cloud-rain) {
  color: #3b82f6;
}

:global(.tire-badge) {
  background-color: #f5f5f5;
  padding: 1px 4px;
  border-radius: 2px;
  font-size: 0.6rem;
  color: #333;
  font-weight: 500;
}

/* Selected segments section styles */
.selected-segments-section {
  background: rgba(255, 102, 0, 0.05);
  border: 1px solid rgba(255, 102, 0, 0.2);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.selected-segments-title {
  margin: 0 0 1rem 0;
  color: #374151;
  font-size: 1rem;
  font-weight: 600;
  text-align: center;
}

.selected-segments-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.selected-segment-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 6px;
  border: 1px solid rgba(229, 231, 235, 0.5);
  transition: all 0.2s ease;
}

.selected-segment-item:hover {
  background: rgba(255, 255, 255, 1);
  border-color: rgba(255, 102, 0, 0.3);
}

.segment-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.selected-segment-item .segment-name {
  font-weight: 600;
  color: #374151;
  font-size: 0.875rem;
  line-height: 1.2;
}

.segment-meta {
  display: flex;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: #6b7280;
}

.segment-difficulty {
  font-weight: 500;
  color: #ff6600;
}

.segment-type {
  font-weight: 500;
  color: #6b7280;
  text-transform: capitalize;
}

.remove-segment-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.remove-segment-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #dc2626;
}

.remove-segment-btn i {
  font-size: 0.75rem;
}
</style>
