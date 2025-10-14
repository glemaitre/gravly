<template>
  <div class="route-planner">
    <!-- Route Planner Sidebar Component -->
    <RoutePlannerSidebar
      :show-sidebar="showSidebar"
      :route-mode="routeMode"
      :start-waypoint="startWaypoint"
      :end-waypoint="endWaypoint"
      :selected-segments="selectedSegments"
      :segment-filters="segmentFilters"
      :filters-expanded="filtersExpanded"
      :route-distance="routeDistance"
      :elevation-stats="elevationStats"
      @close="toggleSidebar"
      @toggle-mode="onToggleMode"
      @toggle-filters="filtersExpanded = !filtersExpanded"
      @toggle-filter="toggleFilter"
      @update:difficulty-min="onDifficultyMinChangeFromSidebar"
      @update:difficulty-max="onDifficultyMaxChangeFromSidebar"
      @clear-filters="clearFilters"
      @deselect-segment="(segment: TrackResponse) => deselectSegment(segment.id)"
      @reverse-segment="(segment: TrackResponse) => reverseSegment(segment.id)"
      @drag-start="handleDragStart"
      @drag-over="handleDragOver"
      @drag-drop="handleDrop"
      @drag-end="handleDragEnd"
      @segment-hover="handleSegmentItemHover"
      @segment-leave="handleSegmentItemLeave"
      @generate-route="generateStartEndRoute"
      @route-saved="handleRouteSaved"
    />

    <div class="map-container">
      <div id="route-map" class="map"></div>

      <!-- Info Banner -->
      <div v-if="showInfoBanner" class="info-banner">
        <div class="info-banner-content">
          <i class="fa-solid fa-info-circle info-banner-icon"></i>
          <span class="info-banner-message">
            Click on
            <i class="fa-solid fa-route banner-route-icon"></i>
            to choose the routing mode!
          </span>
        </div>
        <button class="info-banner-close" @click="dismissInfoBanner">
          <i class="fa-solid fa-times"></i>
        </button>
      </div>

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
            @click="showSaveModal = true"
            :disabled="!canSaveRoute"
            :title="
              !authState.isAuthenticated
                ? t('routePlanner.loginToSaveRoute')
                : canSaveRoute
                  ? t('routePlanner.saveRoute')
                  : t('routePlanner.noRouteToSave')
            "
          >
            <i class="fa-solid fa-save"></i>
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

      <!-- Elevation Profile Component -->
      <ElevationProfile
        ref="elevationProfileRef"
        :show-elevation="showElevation"
        :elevation-stats="elevationStats"
        :elevation-error="elevationError"
        :route-distance="routeDistance"
        :route-points="smoothedRoutePoints"
        :sidebar-open="showSidebar"
        :elevation-height="elevationHeight"
        @toggle="toggleElevation"
        @update:elevation-height="elevationHeight = $event"
        @start-resize="startElevationResize"
        @chart-hover="handleChartHover"
      />
    </div>

    <!-- Route Save Modal -->
    <RouteSaveModal
      v-if="showSaveModal"
      :route-distance="routeDistance"
      :elevation-stats="elevationStats"
      :route-track-points="allRoutePoints"
      :route-features="routeFeatures"
      :show="showSaveModal"
      @route-saved="handleRouteSaved"
      @close="showSaveModal = false"
    />

    <!-- Waypoint Context Menu -->
    <div
      v-if="contextMenu.visible"
      class="waypoint-context-menu"
      :style="{
        left: contextMenu.x + 'px',
        top: contextMenu.y + 'px'
      }"
      @click.stop
    >
      <div class="context-menu-item" @click="handleDeleteWaypoint">
        <i class="fa-solid fa-trash"></i>
        <span>{{ t('routePlanner.deleteWaypoint') }}</span>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, onUnmounted, ref, computed, watch, createApp } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useStravaApi } from '../composables/useStravaApi'
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
import ElevationProfile from './ElevationProfile.vue'
import RoutePlannerSidebar from './RoutePlannerSidebar.vue'
import RouteSaveModal from './RouteSaveModal.vue'
import SegmentPopupCard from './SegmentPopupCard.vue'
import type { TrackResponse, TrackWithGPXDataResponse } from '../types'
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

delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerRetina,
  iconUrl: markerIcon,
  shadowUrl: markerShadow
})

const { t } = useI18n()
const router = useRouter()
const { authState, loadAuthState } = useStravaApi()

// ============================================================================
// NEW CLEAN DATA STRUCTURES
// ============================================================================

/**
 * Waypoint definition - can be user-defined or from a segment
 */
interface Waypoint {
  lat: number
  lng: number
  type: 'user' | 'segment-start' | 'segment-end'
  segmentId?: number // If from a segment
  name?: string
}

/**
 * Route segment definition between two waypoints
 */
interface RouteSegment {
  type: 'gpx' | 'osrm'
  segmentId?: number // If type is 'gpx', this is the segment from database
  isReversed?: boolean // If GPX segment is reversed
}

/**
 * Route point with coordinates and elevation
 */
interface RoutePoint {
  lat: number
  lng: number
  elevation: number
  distance: number // Cumulative distance in meters
}

// Core route data
const waypoints = ref<Waypoint[]>([])
const routeSegments = ref<RouteSegment[]>([])
const routePoints = ref<RoutePoint[][]>([]) // Array of arrays - one per segment

// Computed: All points flattened
const allRoutePoints = computed<RoutePoint[]>(() => {
  return routePoints.value.flat()
})

// Computed: Smoothed elevation data for display
const smoothedRoutePoints = computed<RoutePoint[]>(() => {
  const points = allRoutePoints.value
  if (points.length < 3) return points

  // Apply moving average smoothing with larger window for smoother chart
  const windowSize = 30 // Increased for stronger smoothing
  const smoothed: RoutePoint[] = []

  for (let i = 0; i < points.length; i++) {
    const start = Math.max(0, i - Math.floor(windowSize / 2))
    const end = Math.min(points.length, i + Math.ceil(windowSize / 2))
    const window = points.slice(start, end)

    const avgElevation = window.reduce((sum, p) => sum + p.elevation, 0) / window.length

    smoothed.push({
      ...points[i],
      elevation: avgElevation
    })
  }

  return smoothed
})

// Computed: Reinterpolated points at 100m intervals for accurate gain/loss
const reinterpolatedPoints = computed<RoutePoint[]>(() => {
  const points = allRoutePoints.value
  if (points.length < 2) return points

  const INTERVAL = 100 // meters
  const resampled: RoutePoint[] = []
  const totalDistance = points[points.length - 1].distance

  // Always include first point
  resampled.push(points[0])

  // Add points at regular 100m intervals
  for (
    let targetDistance = INTERVAL;
    targetDistance < totalDistance;
    targetDistance += INTERVAL
  ) {
    // Find the two points that bracket this distance
    let i = 0
    while (i < points.length && points[i].distance < targetDistance) {
      i++
    }

    if (i === 0 || i >= points.length) continue

    const p1 = points[i - 1]
    const p2 = points[i]

    // Linear interpolation
    const ratio = (targetDistance - p1.distance) / (p2.distance - p1.distance)

    resampled.push({
      lat: p1.lat + (p2.lat - p1.lat) * ratio,
      lng: p1.lng + (p2.lng - p1.lng) * ratio,
      elevation: p1.elevation + (p2.elevation - p1.elevation) * ratio,
      distance: targetDistance
    })
  }

  // Always include last point
  if (resampled[resampled.length - 1].distance !== points[points.length - 1].distance) {
    resampled.push(points[points.length - 1])
  }

  // Apply smoothing to resampled points
  if (resampled.length < 3) return resampled

  const windowSize = 3 // Smaller window for resampled data
  const smoothed: RoutePoint[] = []

  for (let i = 0; i < resampled.length; i++) {
    const start = Math.max(0, i - Math.floor(windowSize / 2))
    const end = Math.min(resampled.length, i + Math.ceil(windowSize / 2))
    const window = resampled.slice(start, end)

    const avgElevation = window.reduce((sum, p) => sum + p.elevation, 0) / window.length

    smoothed.push({
      ...resampled[i],
      elevation: avgElevation
    })
  }

  return smoothed
})

// ============================================================================
// UI STATE
// ============================================================================

const showSidebar = ref(false)
const showSaveModal = ref(false)
const routeMode = ref<'standard' | 'startEnd'>('standard')
const showInfoBanner = ref(true)

// Elevation display
const showElevation = ref(false)
const elevationHeight = ref<number>(300)
const elevationProfileRef = ref<InstanceType<typeof ElevationProfile> | null>(null)
const elevationError = ref<string | null>(null)

// Context menu
const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  waypointIndex: -1
})

// ============================================================================
// SEGMENT STATE (for guided mode)
// ============================================================================

const selectedSegments = ref<TrackResponse[]>([])
const availableSegments = ref<TrackResponse[]>([])
const gpxDataCache = new Map<number, TrackWithGPXDataResponse>()
const loadingGPXData = new Set<number>()
const isSearchingSegments = ref(false)
const segmentMapLayers = new Map<
  string,
  { polyline: any; popup?: any; startMarker?: any; endMarker?: any; closeTimeout?: any }
>()

// Segment filters
const segmentFilters = ref({
  difficultyMin: 1,
  difficultyMax: 5,
  surface: [] as string[],
  tireDry: [] as string[],
  tireWet: [] as string[]
})
const filtersExpanded = ref(false)

// Drag and drop for segment reordering
const draggedIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)

// Start/end waypoints for guided mode
const startWaypoint = ref<{ lat: number; lng: number } | null>(null)
const endWaypoint = ref<{ lat: number; lng: number } | null>(null)

// ============================================================================
// COMPUTED PROPERTIES
// ============================================================================

const routeDistance = computed(() => {
  const points = allRoutePoints.value
  if (points.length === 0) return 0
  return points[points.length - 1].distance / 1000 // Convert to kilometers
})

const elevationStats = computed(() => {
  // Use reinterpolated points at 100m intervals for accurate gain/loss
  const points = reinterpolatedPoints.value
  if (points.length === 0) {
    return {
      totalGain: 0,
      totalLoss: 0,
      maxElevation: 0,
      minElevation: 0
    }
  }

  // Apply threshold-based elevation calculation to filter noise
  // This prevents counting tiny variations as gain/loss
  const ELEVATION_THRESHOLD = 1 // meters - only count changes > 1m

  let totalGain = 0
  let totalLoss = 0
  let maxElev = points[0].elevation
  let minElev = points[0].elevation

  // Track cumulative elevation change to apply threshold
  let cumulativeChange = 0
  let lastSignificantElevation = points[0].elevation

  for (let i = 1; i < points.length; i++) {
    const currentElevation = points[i].elevation
    const diff = currentElevation - lastSignificantElevation

    cumulativeChange += diff

    // Only count the change if it exceeds the threshold
    if (Math.abs(cumulativeChange) >= ELEVATION_THRESHOLD) {
      if (cumulativeChange > 0) {
        totalGain += cumulativeChange
      } else {
        totalLoss += Math.abs(cumulativeChange)
      }

      // Reset for next accumulation
      lastSignificantElevation = currentElevation
      cumulativeChange = 0
    }

    // Track max/min regardless of threshold
    maxElev = Math.max(maxElev, currentElevation)
    minElev = Math.min(minElev, currentElevation)
  }

  // Add any remaining cumulative change
  if (Math.abs(cumulativeChange) > 0) {
    if (cumulativeChange > 0) {
      totalGain += cumulativeChange
    } else {
      totalLoss += Math.abs(cumulativeChange)
    }
  }

  return {
    totalGain: Math.round(totalGain),
    totalLoss: Math.round(totalLoss),
    maxElevation: Math.round(maxElev),
    minElevation: Math.round(minElev)
  }
})

const routeFeatures = computed(() => {
  if (selectedSegments.value.length === 0) return null

  // Compute from selected segments
  const maxDifficulty = Math.max(
    ...selectedSegments.value.map((s) => s.difficulty_level)
  )
  const allSurfaces = [
    ...new Set(selectedSegments.value.flatMap((s) => s.surface_type))
  ]

  // Most conservative tire recommendations
  const tires = selectedSegments.value.map((s) => ({
    dry: s.tire_dry,
    wet: s.tire_wet
  }))

  return {
    difficulty_level: maxDifficulty,
    surface_types: allSurfaces,
    tire_dry: getMostConservativeTire(tires.map((t) => t.dry)),
    tire_wet: getMostConservativeTire(tires.map((t) => t.wet))
  }
})

const canSaveRoute = computed(() => {
  return waypoints.value.length >= 2 && authState.value.isAuthenticated
})

const canUndo = ref(false)
const canRedo = ref(false)

// ============================================================================
// MAP STATE
// ============================================================================

let map: any = null
let routeLine: any = null
let waypointMarkers: any[] = []
const startEndMarkers: any[] = []
let chartCursorMarker: any = null // Marker for chart interaction

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function getMostConservativeTire(tires: string[]): string {
  // Order: slick < semi-slick < knobs
  if (tires.includes('knobs')) return 'knobs'
  if (tires.includes('semi-slick')) return 'semi-slick'
  return 'slick'
}

function calculateDistance(
  lat1: number,
  lng1: number,
  lat2: number,
  lng2: number
): number {
  const R = 6371e3 // Earth radius in meters
  const φ1 = (lat1 * Math.PI) / 180
  const φ2 = (lat2 * Math.PI) / 180
  const Δφ = ((lat2 - lat1) * Math.PI) / 180
  const Δλ = ((lng2 - lng1) * Math.PI) / 180

  const a =
    Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
    Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) * Math.sin(Δλ / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))

  return R * c
}

// ============================================================================
// WAYPOINT MANAGEMENT
// ============================================================================

function addWaypoint(lat: number, lng: number, type: Waypoint['type'] = 'user') {
  waypoints.value.push({ lat, lng, type })

  // Create numbered circle marker
  const index = waypoints.value.length - 1
  createWaypointMarker(index, lat, lng)

  // If we have 2+ waypoints, generate route
  if (waypoints.value.length >= 2) {
    generateRoute()
  }
}

function createWaypointMarker(index: number, lat: number, lng: number) {
  // Determine marker style based on position
  const isStart = index === 0
  const isEnd = index === waypoints.value.length - 1 && waypoints.value.length > 1
  const markerClass = isStart
    ? 'waypoint-start'
    : isEnd
      ? 'waypoint-end'
      : 'waypoint-intermediate'

  // Get zoom-based sizes
  const zoom = map!.getZoom()
  const { size, fontSize, border } = getMarkerSizeForZoom(zoom)

  const waypointIcon = L.divIcon({
    html: `<div class="waypoint-marker ${markerClass}" style="width: ${size}px; height: ${size}px; font-size: ${fontSize}px; border-width: ${border}px;">${index + 1}</div>`,
    className: 'custom-waypoint-marker',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2]
  })

  const marker = L.marker([lat, lng], {
    icon: waypointIcon,
    draggable: false // Disable for now
  }).addTo(map!)

  // Store marker reference
  waypointMarkers[index] = marker

  // Update all markers to reflect correct start/end positions
  updateWaypointMarkerStyles()
}

function updateWaypointMarkerStyles() {
  if (!map) return

  const zoom = map.getZoom()
  const { size, fontSize, border } = getMarkerSizeForZoom(zoom)

  waypointMarkers.forEach((marker, index) => {
    if (!marker) return

    const isStart = index === 0
    const isEnd = index === waypoints.value.length - 1 && waypoints.value.length > 1
    const markerClass = isStart
      ? 'waypoint-start'
      : isEnd
        ? 'waypoint-end'
        : 'waypoint-intermediate'

    const waypointIcon = L.divIcon({
      html: `<div class="waypoint-marker ${markerClass}" style="width: ${size}px; height: ${size}px; font-size: ${fontSize}px; border-width: ${border}px;">${index + 1}</div>`,
      className: 'custom-waypoint-marker',
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2]
    })

    marker.setIcon(waypointIcon)
  })
}

function removeWaypoint(index: number) {
  waypoints.value.splice(index, 1)

  // Remove marker
  if (waypointMarkers[index]) {
    map!.removeLayer(waypointMarkers[index])
    waypointMarkers.splice(index, 1)
  }

  // Update all remaining markers to reflect new indices
  updateWaypointMarkerStyles()

  // Regenerate route
  if (waypoints.value.length >= 2) {
    generateRoute()
  } else {
    clearRoute()
  }
}

function clearAllWaypoints() {
  waypoints.value = []
  waypointMarkers.forEach((marker) => map!.removeLayer(marker))
  waypointMarkers = []
  clearRoute()
}

// ============================================================================
// ROUTE GENERATION
// ============================================================================

async function generateRoute() {
  if (waypoints.value.length < 2) return

  routeSegments.value = []
  routePoints.value = []

  // Generate segments between consecutive waypoints
  for (let i = 0; i < waypoints.value.length - 1; i++) {
    const startWp = waypoints.value[i]
    const endWp = waypoints.value[i + 1]

    // Check if this segment should be GPX or OSRM
    const segmentInfo = findSegmentBetweenWaypoints(i, i + 1)

    if (segmentInfo) {
      // GPX segment
      await generateGPXSegment(segmentInfo, startWp, endWp, i)
    } else {
      // OSRM segment
      await generateOSRMSegment(startWp, endWp, i)
    }
  }

  // Render the route
  renderRoute()
}

function findSegmentBetweenWaypoints(
  startIndex: number,
  endIndex: number
): { segment: TrackResponse; isReversed: boolean } | null {
  // In guided mode, check if there's a selected segment that matches these waypoints
  if (routeMode.value !== 'startEnd') return null

  const startWp = waypoints.value[startIndex]
  const endWp = waypoints.value[endIndex]

  // Check if both waypoints belong to the same segment
  if (
    startWp.segmentId &&
    endWp.segmentId &&
    startWp.segmentId === endWp.segmentId &&
    startWp.type === 'segment-start' &&
    endWp.type === 'segment-end'
  ) {
    // Find the segment in selectedSegments
    const segment = selectedSegments.value.find((s) => s.id === startWp.segmentId)
    if (segment) {
      return {
        segment: segment,
        isReversed: segment.isReversed || false
      }
    }
  }

  return null
}

async function generateGPXSegment(
  segmentInfo: { segment: TrackResponse; isReversed: boolean },
  _startWp: Waypoint,
  _endWp: Waypoint,
  segmentIndex: number
) {
  const { segment, isReversed } = segmentInfo

  // Add segment metadata
  routeSegments.value[segmentIndex] = {
    type: 'gpx',
    segmentId: segment.id,
    isReversed
  }

  // Load GPX data if not cached
  if (!gpxDataCache.has(segment.id)) {
    try {
      const response = await fetch(`/api/segments/${segment.id}/gpx`)
      const data: { gpx_xml_data: string } = await response.json()
      const segmentWithGPX: TrackWithGPXDataResponse = {
        ...segment,
        gpx_data: null,
        gpx_xml_data: data.gpx_xml_data
      }
      gpxDataCache.set(segment.id, segmentWithGPX)
    } catch (error) {
      console.error('Error loading GPX data:', error)
    }
  }

  const gpxData = gpxDataCache.get(segment.id)
  if (!gpxData?.gpx_xml_data) {
    console.error('No GPX data for segment', segment.id)
    return
  }

  // Parse GPX
  const fileId =
    segment.file_path.split('/').pop()?.replace('.gpx', '') || String(segment.id)
  const parsedGPX = parseGPXData(gpxData.gpx_xml_data, fileId)

  if (!parsedGPX?.points || parsedGPX.points.length === 0) {
    console.error('No points in parsed GPX')
    return
  }

  // Convert to RoutePoints
  let points: RoutePoint[] = parsedGPX.points.map((p) => ({
    lat: p.latitude,
    lng: p.longitude,
    elevation: p.elevation,
    distance: 0 // Will calculate below
  }))

  // Reverse if needed
  if (isReversed) {
    points = points.reverse()
  }

  // Calculate cumulative distance
  let cumulativeDistance =
    segmentIndex > 0
      ? routePoints.value[segmentIndex - 1][
          routePoints.value[segmentIndex - 1].length - 1
        ].distance
      : 0

  for (let i = 0; i < points.length; i++) {
    if (i > 0) {
      cumulativeDistance += calculateDistance(
        points[i - 1].lat,
        points[i - 1].lng,
        points[i].lat,
        points[i].lng
      )
    }
    points[i].distance = cumulativeDistance
  }

  routePoints.value[segmentIndex] = points
}

async function generateOSRMSegment(
  startWp: Waypoint,
  endWp: Waypoint,
  segmentIndex: number
) {
  routeSegments.value[segmentIndex] = { type: 'osrm' }

  try {
    // Call OSRM API
    const url = `https://routing.openstreetmap.de/routed-bike/route/v1/cycling/${startWp.lng},${startWp.lat};${endWp.lng},${endWp.lat}?overview=full&geometries=geojson`

    const response = await fetch(url)
    const data = await response.json()

    if (data.code !== 'Ok' || !data.routes || data.routes.length === 0) {
      console.error('OSRM routing failed')
      return
    }

    const coordinates = data.routes[0].geometry.coordinates // [lng, lat] format

    // Convert to RoutePoints (without elevation yet)
    let cumulativeDistance =
      segmentIndex > 0
        ? routePoints.value[segmentIndex - 1][
            routePoints.value[segmentIndex - 1].length - 1
          ].distance
        : 0

    const points: RoutePoint[] = coordinates.map((coord: number[], idx: number) => {
      if (idx > 0) {
        cumulativeDistance += calculateDistance(
          coordinates[idx - 1][1],
          coordinates[idx - 1][0],
          coord[1],
          coord[0]
        )
      }
      return {
        lat: coord[1],
        lng: coord[0],
        elevation: 0, // Will fetch later
        distance: cumulativeDistance
      }
    })

    routePoints.value[segmentIndex] = points

    // Fetch elevation data
    await fetchElevationForSegment(segmentIndex)

    // Trigger chart update after elevation is fetched
    // The computed properties will automatically update
  } catch (error) {
    console.error('Error generating OSRM segment:', error)
  }
}

// ============================================================================
// ELEVATION FETCHING
// ============================================================================

const ELEVATION_CHUNK_SIZE = 2000 // Max points per API call

async function fetchElevationForSegment(segmentIndex: number) {
  const points = routePoints.value[segmentIndex]
  if (!points || points.length === 0) return

  const segment = routeSegments.value[segmentIndex]
  if (segment.type === 'gpx') {
    // GPX already has elevation
    return
  }

  // Chunk the points
  const chunks: RoutePoint[][] = []
  for (let i = 0; i < points.length; i += ELEVATION_CHUNK_SIZE) {
    chunks.push(points.slice(i, i + ELEVATION_CHUNK_SIZE))
  }

  // Fetch elevation for each chunk
  for (const chunk of chunks) {
    await fetchElevationChunk(chunk)
  }
}

async function fetchElevationChunk(
  points: RoutePoint[],
  retryCount = 0
): Promise<void> {
  const MAX_RETRIES = 3
  const INITIAL_DELAY = 1000 // ms

  try {
    const locations = points.map((p) => ({ latitude: p.lat, longitude: p.lng }))

    const response = await fetch('https://api.open-elevation.com/api/v1/lookup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ locations })
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const data = await response.json()

    if (data.results && Array.isArray(data.results)) {
      data.results.forEach((result: any, idx: number) => {
        if (points[idx]) {
          points[idx].elevation = result.elevation || 0
        }
      })
    }
  } catch (error) {
    console.error(
      `Error fetching elevation (attempt ${retryCount + 1}/${MAX_RETRIES + 1}):`,
      error
    )

    // Exponential backoff retry
    if (retryCount < MAX_RETRIES) {
      const delay = INITIAL_DELAY * Math.pow(2, retryCount)
      console.log(`Retrying in ${delay}ms...`)
      await new Promise((resolve) => setTimeout(resolve, delay))
      return fetchElevationChunk(points, retryCount + 1)
    } else {
      console.error('Max retries reached for elevation fetch')
      // Set elevation to 0 for failed points
      points.forEach((p) => {
        if (p.elevation === undefined || p.elevation === null) {
          p.elevation = 0
        }
      })
    }
  }
}

// ============================================================================
// ROUTE RENDERING
// ============================================================================

function renderRoute() {
  // Clear existing route line
  if (routeLine) {
    map!.removeLayer(routeLine)
  }

  const allPoints = allRoutePoints.value
  if (allPoints.length < 2) return

  // Create polyline
  const latLngs = allPoints.map((p) => L.latLng(p.lat, p.lng))

  routeLine = L.polyline(latLngs, {
    color: 'var(--brand-primary)',
    weight: 4,
    opacity: 0.8
  }).addTo(map!)

  // Fit map to route
  map!.fitBounds(routeLine.getBounds(), { padding: [50, 50] })
}

function clearRoute() {
  if (routeLine) {
    map!.removeLayer(routeLine)
    routeLine = null
  }
  routeSegments.value = []
  routePoints.value = []
}

// ============================================================================
// GUIDED MODE - SEGMENT MANAGEMENT
// ============================================================================

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

    const url = `/api/segments/search?${params}`
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
    const response = await fetch(`/api/segments/${segment.id}/gpx`)
    if (!response.ok) {
      console.warn(
        `Failed to fetch GPX data for segment ${segment.id}: ${response.statusText}`
      )
      return
    }

    const gpxResponse: { gpx_xml_data: string } = await response.json()

    // Create a TrackWithGPXDataResponse object for caching and rendering
    const segmentWithGPX: TrackWithGPXDataResponse = {
      ...segment,
      gpx_data: null,
      gpx_xml_data: gpxResponse.gpx_xml_data
    }

    // Cache the GPX data
    gpxDataCache.set(segment.id, segmentWithGPX)

    // Render the segment on the map
    renderSegmentOnMap(segmentWithGPX)
  } catch (error) {
    console.error(`Error loading GPX data for segment ${segment.id}:`, error)
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
  let trackPoints = gpxData.points.map((point: any) => [
    point.latitude,
    point.longitude
  ])

  // Reverse the points if needed
  if (segment.isReversed) {
    trackPoints = trackPoints.reverse()
  }

  // Check if segment is selected
  const isSelected = selectedSegments.value.some((s) => s.id === segment.id)

  // Create polyline for the segment
  const polyline = L.polyline(trackPoints, {
    color: isSelected ? 'var(--brand-primary)' : '#000000',
    weight: isSelected ? 4 : 3,
    opacity: 0.8
  }).addTo(map)

  // Create popup with segment details
  const popupContent = createSegmentPopup(segment)
  const popup = L.popup({
    maxWidth: 340,
    className: 'segment-hover-popup',
    closeButton: false,
    autoClose: false,
    closeOnClick: false
  }).setContent(popupContent)

  // Store close timeout for this segment
  let closeTimeout: any = null

  // Add hover effects and popup trigger
  polyline.on('mouseover', () => {
    // Clear any pending close timeout
    if (closeTimeout) {
      clearTimeout(closeTimeout)
      closeTimeout = null
    }

    polyline.setStyle({
      weight: isSelected ? 5 : 4,
      opacity: 1
    })
    // Show popup on hover
    popup.setLatLng(polyline.getBounds().getCenter()).openOn(map)
  })

  polyline.on('mouseout', () => {
    polyline.setStyle({
      weight: isSelected ? 4 : 3,
      opacity: 0.8
    })
    // Close popup after delay (allows mouse to move to popup)
    closeTimeout = setTimeout(() => {
      if (map && popup) {
        map.closePopup(popup)
      }
      closeTimeout = null
    }, 300) // Increased delay to allow moving to popup
  })

  // Click to select/deselect
  polyline.on('click', () => {
    selectSegment(segment)
  })

  // Add popup open event to setup card interactions
  popup.on('add', () => {
    const popupElement = popup.getElement()
    if (popupElement) {
      const cardElement = popupElement.querySelector('.segment-popup-card')
      if (cardElement) {
        let justSelected = false

        // Keep popup open when hovering over card
        cardElement.addEventListener('mouseenter', () => {
          if (closeTimeout) {
            clearTimeout(closeTimeout)
            closeTimeout = null
          }
          justSelected = false // Reset flag when re-entering
        })

        // Close popup when leaving card
        cardElement.addEventListener('mouseleave', () => {
          // Use shorter delay if segment was just selected
          const delay = justSelected ? 50 : 200
          closeTimeout = setTimeout(() => {
            if (map && popup) {
              map.closePopup(popup)
            }
            closeTimeout = null
          }, delay)
        })

        // Click on card to select segment
        cardElement.addEventListener('click', (e: Event) => {
          e.stopPropagation()
          selectSegment(segment)
          justSelected = true // Mark that segment was just selected
        })
      }
    }
  })

  // Store the layer reference
  const segmentId = segment.id.toString()
  segmentMapLayers.set(segmentId, {
    polyline: polyline,
    popup: popup,
    startMarker: null,
    endMarker: null,
    closeTimeout: closeTimeout
  })

  // If segment is already selected, add landmarks
  if (isSelected && !routeLine) {
    addSegmentLandmarks(segment, polyline)
  }
}

function createSegmentPopup(segment: TrackResponse): HTMLElement {
  const isSelected = selectedSegments.value.some((s) => s.id === segment.id)

  // Get cached GPX data for stats
  const gpxDataWithXml = gpxDataCache.get(segment.id)
  let gpxData = null

  if (gpxDataWithXml && gpxDataWithXml.gpx_xml_data) {
    const fileId =
      segment.file_path.split('/').pop()?.replace('.gpx', '') || segment.id.toString()
    gpxData = parseGPXData(gpxDataWithXml.gpx_xml_data, fileId)
  }

  // Create a container for the Vue component
  const container = document.createElement('div')

  // Mount the SegmentPopupCard component
  const app = createApp(SegmentPopupCard, {
    segment: segment,
    isSelected: isSelected,
    gpxData: gpxData
  })

  app.mount(container)

  return container
}

function selectSegment(segment: TrackResponse) {
  const existingIndex = selectedSegments.value.findIndex((s) => s.id === segment.id)

  if (existingIndex >= 0) {
    selectedSegments.value.splice(existingIndex, 1)
  } else {
    selectedSegments.value.push(segment)
  }

  // Update popup content and polyline style to reflect new selection status
  const segmentId = segment.id.toString()
  const layerData = segmentMapLayers.get(segmentId)
  if (layerData) {
    const isSelected = selectedSegments.value.some((s) => s.id === segment.id)

    // Update polyline style
    if (layerData.polyline) {
      layerData.polyline.setStyle({
        color: isSelected ? 'var(--brand-primary)' : '#000000',
        weight: isSelected ? 4 : 3
      })
    }

    // Update popup content
    if (layerData.popup) {
      layerData.popup.setContent(createSegmentPopup(segment))
    }

    // Add or remove landmarks based on selection
    // Don't show landmarks if a route is currently active (replaced by waypoint markers)
    if (isSelected && !routeLine) {
      // Add landmarks for selected segment (only if no route is active)
      addSegmentLandmarks(segment, layerData.polyline)
    } else {
      // Remove landmarks for deselected segment or when route is active
      removeSegmentLandmarks(segment.id)
    }
  }
}

function createSegmentLandmark(
  point: [number, number],
  type: 'start' | 'end',
  index: number = -1
) {
  if (!map) return null

  // Get zoom-based sizes
  const zoom = map.getZoom()
  const { size, fontSize, badgeSize, badgeFontSize } =
    getSegmentLandmarkSizeForZoom(zoom)

  // Create different icons for start and end with index
  const icon = L.divIcon({
    className: `segment-landmark segment-landmark-${type}`,
    html: `<div class="landmark-content" style="width: ${size}px; height: ${size}px; font-size: ${fontSize}px;">
      ${index >= 0 ? `<div class="landmark-index" style="width: ${badgeSize}px; height: ${badgeSize}px; font-size: ${badgeFontSize}px; top: -${Math.round(badgeSize / 2)}px; right: -${Math.round(badgeSize / 2)}px;">${index + 1}</div>` : ''}
      <i class="fa-solid ${type === 'start' ? 'fa-play' : 'fa-stop'}"></i>
    </div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2]
  })

  const marker = L.marker([point[0], point[1]], { icon }).addTo(map)
  return marker
}

function addSegmentLandmarks(segment: TrackResponse, polyline: any) {
  if (!map) return

  const segmentId = segment.id.toString()
  const layerData = segmentMapLayers.get(segmentId)

  if (!layerData) return

  // Get the polyline coordinates
  const coordinates = polyline.getLatLngs()
  if (coordinates.length < 2) return

  // Remove existing landmarks if any
  removeSegmentLandmarks(segment.id)

  // Find the index of this segment in the selected segments list
  const segmentIndex = selectedSegments.value.findIndex((s) => s.id === segment.id)

  // Create landmarks at start and end points
  const startPoint = coordinates[0]
  const endPoint = coordinates[coordinates.length - 1]

  // Create new landmarks
  const startMarker = createSegmentLandmark(
    [startPoint.lat, startPoint.lng],
    'start',
    segmentIndex
  )
  const endMarker = createSegmentLandmark(
    [endPoint.lat, endPoint.lng],
    'end',
    segmentIndex
  )

  // Update layer data
  layerData.startMarker = startMarker
  layerData.endMarker = endMarker
}

function removeSegmentLandmarks(segmentId: number) {
  const segmentIdStr = segmentId.toString()
  const layerData = segmentMapLayers.get(segmentIdStr)

  if (layerData) {
    if (layerData.startMarker && map) {
      map.removeLayer(layerData.startMarker)
      layerData.startMarker = null
    }
    if (layerData.endMarker && map) {
      map.removeLayer(layerData.endMarker)
      layerData.endMarker = null
    }
  }
}

function updateSegmentLandmarksIndices() {
  // Update landmarks for all selected segments with their current indices
  selectedSegments.value.forEach((segment) => {
    const segmentIdStr = segment.id.toString()
    const layerData = segmentMapLayers.get(segmentIdStr)

    if (layerData?.polyline && !routeLine) {
      // Re-add landmarks with updated indices
      addSegmentLandmarks(segment, layerData.polyline)
    }
  })
}

function clearAllSegments() {
  // Ensure map is available before attempting to remove layers
  if (!map) {
    return
  }

  // Remove all segment layers from map (polylines, popups, and landmarks)
  segmentMapLayers.forEach((layerData) => {
    try {
      // Clear any pending close timeout
      if (layerData.closeTimeout) {
        clearTimeout(layerData.closeTimeout)
        layerData.closeTimeout = null
      }

      if (layerData.polyline && map.hasLayer(layerData.polyline)) {
        map.removeLayer(layerData.polyline)
      }
      if (layerData.popup && map.hasLayer(layerData.popup)) {
        map.removeLayer(layerData.popup)
      }
      if (layerData.startMarker && map.hasLayer(layerData.startMarker)) {
        map.removeLayer(layerData.startMarker)
      }
      if (layerData.endMarker && map.hasLayer(layerData.endMarker)) {
        map.removeLayer(layerData.endMarker)
      }
    } catch {
      // Silently handle errors during cleanup
    }
  })

  // Clear all data structures
  segmentMapLayers.clear()
  availableSegments.value = []
  // Don't clear selectedSegments or gpxDataCache - keep selections when reloading
  loadingGPXData.clear()
}

// ============================================================================
// MODE SWITCHING
// ============================================================================

function onToggleMode() {
  routeMode.value = routeMode.value === 'standard' ? 'startEnd' : 'standard'

  // Clear everything when switching modes
  clearAllWaypoints()
  clearAllSegments()
  selectedSegments.value = []
  clearStartEndWaypoints()

  // Update cursor for new mode
  updateMapCursor()
}

// ============================================================================
// MAP INITIALIZATION
// ============================================================================

function initializeMap() {
  // Initialize map with OpenCycleMap tiles
  map = L.map('route-map', {
    center: [46.942728, 4.033681], // Mont-Beuvray
    zoom: 14
  })

  // Add OpenCycleMap tiles via backend proxy (secure API key handling)
  L.tileLayer('/api/map-tiles/{z}/{x}/{y}.png', {
    attribution:
      'Maps © <a href="https://www.thunderforest.com/">Thunderforest</a>, Data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18
  }).addTo(map)

  // Click to add waypoints based on mode
  map.on('click', (e: any) => {
    if (routeMode.value === 'standard') {
      addWaypoint(e.latlng.lat, e.latlng.lng)
    } else if (routeMode.value === 'startEnd') {
      // In guided mode, only allow setting start/end waypoints if they're not both set
      if (!startWaypoint.value || !endWaypoint.value) {
        addStartEndWaypoint(e.latlng)
      }
      // If both start and end are set, clicks are ignored (for segment selection)
    }
  })

  // Listen for map movement and zoom to reload segments in guided mode
  map.on('moveend', handleMapBoundsChange)
  map.on('zoomend', handleMapBoundsChange)

  // Listen for zoom changes to update marker sizes
  map.on('zoomend', updateMarkerSizes)

  // Set initial cursor based on current mode
  updateMapCursor()
}

function handleMapBoundsChange() {
  if (
    routeMode.value === 'startEnd' &&
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

function getMarkerSizeForZoom(zoom: number): {
  size: number
  fontSize: number
  border: number
} {
  // More aggressive scaling based on zoom level
  // Zoom 8: very small (8px), Zoom 14: medium (20px), Zoom 18: large (32px)
  // Formula: size increases by 2px per zoom level
  const baseSize = Math.max(8, Math.min(32, (zoom - 6) * 2))
  const baseFontSize = Math.max(6, Math.min(14, baseSize * 0.5))
  const baseBorder = zoom < 12 ? 1 : 2

  return {
    size: Math.round(baseSize),
    fontSize: Math.round(baseFontSize),
    border: baseBorder
  }
}

function getSegmentLandmarkSizeForZoom(zoom: number): {
  size: number
  fontSize: number
  badgeSize: number
  badgeFontSize: number
} {
  // Landmarks scale similarly but slightly smaller
  const baseSize = Math.max(8, Math.min(24, (zoom - 7) * 1.6))
  const badgeSize = Math.max(8, Math.min(16, baseSize * 0.7))

  return {
    size: Math.round(baseSize),
    fontSize: Math.round(baseSize * 0.5),
    badgeSize: Math.round(badgeSize),
    badgeFontSize: Math.round(badgeSize * 0.6)
  }
}

function updateMarkerSizes() {
  if (!map) return

  const zoom = map.getZoom()
  const { size, fontSize, border } = getMarkerSizeForZoom(zoom)

  // Update waypoint markers
  waypointMarkers.forEach((marker, index) => {
    if (!marker) return

    const isStart = index === 0
    const isEnd = index === waypoints.value.length - 1 && waypoints.value.length > 1
    const markerClass = isStart
      ? 'waypoint-start'
      : isEnd
        ? 'waypoint-end'
        : 'waypoint-intermediate'

    const waypointIcon = L.divIcon({
      html: `<div class="waypoint-marker ${markerClass}" style="width: ${size}px; height: ${size}px; font-size: ${fontSize}px; border-width: ${border}px;">${index + 1}</div>`,
      className: 'custom-waypoint-marker',
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2]
    })

    marker.setIcon(waypointIcon)
  })

  // Update start/end markers
  startEndMarkers.forEach((marker: any) => {
    if (!marker) return

    const type = marker.options.type
    const isStart = type === 'start'
    const markerClass = isStart
      ? 'start-end-marker start-marker'
      : 'start-end-marker end-marker'
    const iconClass = isStart ? 'fa-play' : 'fa-stop'

    const iconFontSize = Math.round(10 * (size / 24))

    const markerIcon = L.divIcon({
      html: `<div class="${markerClass}" style="width: ${size}px; height: ${size}px; font-size: ${iconFontSize}px; border-width: ${border}px;"><i class="fa-solid ${iconClass}"></i></div>`,
      className: 'custom-start-end-marker',
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2]
    })

    marker.setIcon(markerIcon)
  })

  // Update segment landmarks
  const landmarkSizes = getSegmentLandmarkSizeForZoom(zoom)
  segmentMapLayers.forEach((layerData, segmentIdStr) => {
    if (layerData.startMarker || layerData.endMarker) {
      // Find the segment index in selected segments
      const segmentId = parseInt(segmentIdStr)
      const segmentIndex = selectedSegments.value.findIndex((s) => s.id === segmentId)

      if (layerData.startMarker) {
        const icon = L.divIcon({
          className: 'segment-landmark segment-landmark-start',
          html: `<div class="landmark-content" style="width: ${landmarkSizes.size}px; height: ${landmarkSizes.size}px; font-size: ${landmarkSizes.fontSize}px;">
            ${segmentIndex >= 0 ? `<div class="landmark-index" style="width: ${landmarkSizes.badgeSize}px; height: ${landmarkSizes.badgeSize}px; font-size: ${landmarkSizes.badgeFontSize}px; top: -${Math.round(landmarkSizes.badgeSize / 2)}px; right: -${Math.round(landmarkSizes.badgeSize / 2)}px;">${segmentIndex + 1}</div>` : ''}
            <i class="fa-solid fa-play"></i>
          </div>`,
          iconSize: [landmarkSizes.size, landmarkSizes.size],
          iconAnchor: [landmarkSizes.size / 2, landmarkSizes.size / 2]
        })
        layerData.startMarker.setIcon(icon)
      }

      if (layerData.endMarker) {
        const icon = L.divIcon({
          className: 'segment-landmark segment-landmark-end',
          html: `<div class="landmark-content" style="width: ${landmarkSizes.size}px; height: ${landmarkSizes.size}px; font-size: ${landmarkSizes.fontSize}px;">
            ${segmentIndex >= 0 ? `<div class="landmark-index" style="width: ${landmarkSizes.badgeSize}px; height: ${landmarkSizes.badgeSize}px; font-size: ${landmarkSizes.badgeFontSize}px; top: -${Math.round(landmarkSizes.badgeSize / 2)}px; right: -${Math.round(landmarkSizes.badgeSize / 2)}px;">${segmentIndex + 1}</div>` : ''}
            <i class="fa-solid fa-stop"></i>
          </div>`,
          iconSize: [landmarkSizes.size, landmarkSizes.size],
          iconAnchor: [landmarkSizes.size / 2, landmarkSizes.size / 2]
        })
        layerData.endMarker.setIcon(icon)
      }
    }
  })
}

// ============================================================================
// START/END WAYPOINT MANAGEMENT (Guided Mode)
// ============================================================================

function addStartEndWaypoint(latlng: any) {
  if (!startWaypoint.value) {
    // Set start waypoint
    startWaypoint.value = { lat: latlng.lat, lng: latlng.lng }
    createStartEndMarker('start', latlng)
  } else if (!endWaypoint.value) {
    // Set end waypoint
    endWaypoint.value = { lat: latlng.lat, lng: latlng.lng }
    createStartEndMarker('end', latlng)
    // Update cursor now that both waypoints are set
    updateMapCursor()
    // Don't generate route automatically - user will click the button
  } else {
    // Both waypoints are set, replace the end waypoint
    endWaypoint.value = { lat: latlng.lat, lng: latlng.lng }

    // Remove existing end marker
    const endMarkerIndex = startEndMarkers.findIndex(
      (marker: any) => marker.options.type === 'end'
    )
    if (endMarkerIndex > -1) {
      const endMarker = startEndMarkers[endMarkerIndex]
      if (map!.hasLayer(endMarker)) {
        map!.removeLayer(endMarker)
      }
      startEndMarkers.splice(endMarkerIndex, 1)
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

  // Get zoom-based sizes
  const zoom = map!.getZoom()
  const { size, border } = getMarkerSizeForZoom(zoom)
  const iconFontSize = Math.round(10 * (size / 24))

  const markerIcon = L.divIcon({
    html: `<div class="${markerClass}" style="width: ${size}px; height: ${size}px; font-size: ${iconFontSize}px; border-width: ${border}px;"><i class="fa-solid ${iconClass}"></i></div>`,
    className: 'custom-start-end-marker',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2]
  })

  const marker = L.marker(latlng, {
    icon: markerIcon,
    interactive: true,
    zIndexOffset: 600,
    type: type
  } as any).addTo(map!)

  startEndMarkers.push(marker)
}

function clearStartEndWaypoints() {
  startWaypoint.value = null
  endWaypoint.value = null

  // Clear start/end markers from map
  startEndMarkers.forEach((marker) => {
    if (marker && map!.hasLayer(marker)) {
      map!.removeLayer(marker)
    }
  })
  startEndMarkers.length = 0

  // Update cursor since waypoints changed
  updateMapCursor()
}

// ============================================================================
// UI HANDLERS
// ============================================================================

function toggleSidebar() {
  showSidebar.value = !showSidebar.value
}

function toggleElevation() {
  showElevation.value = !showElevation.value
}

function dismissInfoBanner() {
  showInfoBanner.value = false
  localStorage.setItem('routePlanner_infoBannerDismissed', 'true')
}

function clearMap() {
  clearAllWaypoints()
  clearAllSegments()
  selectedSegments.value = []
  clearStartEndWaypoints()
}

function undo() {
  // TODO: Implement undo
}

function redo() {
  // TODO: Implement redo
}

function handleDeleteWaypoint() {
  if (contextMenu.value.waypointIndex >= 0) {
    removeWaypoint(contextMenu.value.waypointIndex)
  }
  hideContextMenu()
}

function hideContextMenu() {
  contextMenu.value = {
    visible: false,
    x: 0,
    y: 0,
    waypointIndex: -1
  }
}

function handleRouteSaved(routeId: number) {
  showSaveModal.value = false
  clearMap()
  router.push(`/segment/${routeId}`)
}

function startElevationResize() {
  // TODO: Implement resize
}

function handleChartHover(point: RoutePoint | null) {
  if (!map) return

  if (!point) {
    // Remove cursor marker
    if (chartCursorMarker) {
      map.removeLayer(chartCursorMarker)
      chartCursorMarker = null
    }
    return
  }

  // Create or update cursor marker
  if (!chartCursorMarker) {
    const cursorIcon = L.divIcon({
      html: '<div class="chart-cursor-marker"></div>',
      className: 'custom-chart-cursor',
      iconSize: [16, 16],
      iconAnchor: [8, 8]
    })

    chartCursorMarker = L.marker([point.lat, point.lng], {
      icon: cursorIcon,
      interactive: false,
      zIndexOffset: 1000
    }).addTo(map)
  } else {
    chartCursorMarker.setLatLng([point.lat, point.lng])
  }
}

// Segment management for sidebar
function deselectSegment(segmentId: number) {
  const segment = selectedSegments.value.find((s) => s.id === segmentId)
  if (segment) {
    selectSegment(segment) // Reuse the selectSegment function which toggles
  }
}

function reverseSegment(segmentId: number) {
  const segment = selectedSegments.value.find((s) => s.id === segmentId)
  if (segment) {
    segment.isReversed = !segment.isReversed

    // Update the segment display to reflect the reversal
    const layerData = segmentMapLayers.get(String(segmentId))
    if (layerData?.popup) {
      layerData.popup.setContent(createSegmentPopup(segment))
    }

    // If there's a cached GPX data, re-render the segment on map
    const gpxData = gpxDataCache.get(segmentId)
    if (gpxData) {
      // Update the segment's reversed state in the cache
      gpxData.isReversed = segment.isReversed

      // Remove old polyline and landmarks
      if (layerData?.polyline && map) {
        map.removeLayer(layerData.polyline)
      }
      removeSegmentLandmarks(segmentId)

      // Re-render with new direction
      renderSegmentOnMap(gpxData)
    }

    // If a route is already active, regenerate it with the reversed segment
    if (waypoints.value.length > 0 && routeLine) {
      generateStartEndRoute()
    }
  }
}

function handleDragStart(event: any, index: number) {
  draggedIndex.value = index
  event.dataTransfer.effectAllowed = 'move'
}

function handleDragOver(event: any) {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
}

function handleDrop(event: any, dropIndex: number) {
  event.preventDefault()

  if (draggedIndex.value !== null && draggedIndex.value !== dropIndex) {
    const draggedItem = selectedSegments.value[draggedIndex.value]

    // Remove from old position
    selectedSegments.value.splice(draggedIndex.value, 1)

    // Insert at new position (adjust index if dragging down)
    const insertIndex = draggedIndex.value < dropIndex ? dropIndex - 1 : dropIndex
    selectedSegments.value.splice(insertIndex, 0, draggedItem)

    // Update all segment landmarks with new indices
    updateSegmentLandmarksIndices()

    // If a route is already active, regenerate it with the new segment order
    if (waypoints.value.length > 0 && routeLine) {
      generateStartEndRoute()
    }
  }

  draggedIndex.value = null
  dragOverIndex.value = null
}

function handleDragEnd() {
  draggedIndex.value = null
  dragOverIndex.value = null
}

function handleSegmentItemHover() {
  // TODO: Highlight segment on map
}

function handleSegmentItemLeave() {
  // TODO: Remove highlight
}

async function generateStartEndRoute() {
  if (!startWaypoint.value || !endWaypoint.value) {
    console.warn('Cannot generate route: missing start or end waypoint')
    return
  }

  // Clear existing route
  clearRoute()

  // Build waypoints array from start, selected segments, and end
  waypoints.value = []

  // Add start waypoint
  waypoints.value.push({
    lat: startWaypoint.value.lat,
    lng: startWaypoint.value.lng,
    type: 'user',
    name: 'Start'
  })

  // Add waypoints from selected segments
  for (const segment of selectedSegments.value) {
    // Load GPX data if not cached
    if (!gpxDataCache.has(segment.id)) {
      try {
        const response = await fetch(`/api/segments/${segment.id}/gpx`)
        const data: { gpx_xml_data: string } = await response.json()
        const segmentWithGPX: TrackWithGPXDataResponse = {
          ...segment,
          gpx_data: null,
          gpx_xml_data: data.gpx_xml_data
        }
        gpxDataCache.set(segment.id, segmentWithGPX)
      } catch (error) {
        console.error('Error loading GPX data:', error)
        continue
      }
    }

    const gpxData = gpxDataCache.get(segment.id)
    if (!gpxData?.gpx_xml_data) {
      console.warn(`No GPX data for segment ${segment.id}`)
      continue
    }

    // Parse GPX
    const fileId =
      segment.file_path.split('/').pop()?.replace('.gpx', '') || String(segment.id)
    const parsedGPX = parseGPXData(gpxData.gpx_xml_data, fileId)

    if (!parsedGPX?.points || parsedGPX.points.length === 0) {
      console.warn(`No points in parsed GPX for segment ${segment.id}`)
      continue
    }

    // Get start and end points of segment
    let startPoint = parsedGPX.points[0]
    let endPoint = parsedGPX.points[parsedGPX.points.length - 1]

    // Reverse if needed
    if (segment.isReversed) {
      ;[startPoint, endPoint] = [endPoint, startPoint]
    }

    // Add segment start and end as waypoints
    waypoints.value.push({
      lat: startPoint.latitude,
      lng: startPoint.longitude,
      type: 'segment-start',
      segmentId: segment.id,
      name: `${segment.name} (start)`
    })

    waypoints.value.push({
      lat: endPoint.latitude,
      lng: endPoint.longitude,
      type: 'segment-end',
      segmentId: segment.id,
      name: `${segment.name} (end)`
    })
  }

  // Add end waypoint
  waypoints.value.push({
    lat: endWaypoint.value.lat,
    lng: endWaypoint.value.lng,
    type: 'user',
    name: 'End'
  })

  // Now generate the route using the standard route generation logic
  await generateRoute()

  // After route generation, switch to free mode and show waypoint markers
  if (waypoints.value.length > 0) {
    // Create waypoint markers for all waypoints
    waypoints.value.forEach((wp, index) => {
      createWaypointMarker(index, wp.lat, wp.lng)
    })

    // Clear segment visuals (but keep GPX data cached for the route)
    clearAllSegments()

    // Clear start/end markers
    clearStartEndWaypoints()

    // Switch to standard mode
    routeMode.value = 'standard'

    // Update cursor for standard mode
    updateMapCursor()
  }
}

function toggleFilter() {
  // TODO: Implement filter toggle
}

function onDifficultyMinChangeFromSidebar(value: number) {
  segmentFilters.value.difficultyMin = value
}

function onDifficultyMaxChangeFromSidebar(value: number) {
  segmentFilters.value.difficultyMax = value
}

function clearFilters() {
  segmentFilters.value = {
    difficultyMin: 1,
    difficultyMax: 5,
    surface: [],
    tireDry: [],
    tireWet: []
  }
}

// ============================================================================
// WATCHERS
// ============================================================================

// Timeout for debouncing segment search
let segmentSearchTimeout: any = null

// Watch for start/end waypoints to trigger segment search
watch([startWaypoint, endWaypoint], () => {
  if (routeMode.value === 'startEnd' && startWaypoint.value && endWaypoint.value) {
    // Both waypoints are set, load segments
    loadSegmentsInBounds()
  }
})

// ============================================================================
// LIFECYCLE
// ============================================================================

onMounted(async () => {
  await loadAuthState()
  initializeMap()

  // Check if banner was dismissed
  const dismissed = localStorage.getItem('routePlanner_infoBannerDismissed')
  if (dismissed === 'true') {
    showInfoBanner.value = false
  }
})

onUnmounted(() => {
  if (map) {
    // Remove event listeners
    map.off('moveend', handleMapBoundsChange)
    map.off('zoomend', handleMapBoundsChange)
    map.off('zoomend', updateMarkerSizes)
    map.remove()
  }

  // Clear any pending search timeout
  if (segmentSearchTimeout) {
    clearTimeout(segmentSearchTimeout)
    segmentSearchTimeout = null
  }
})
</script>

<style scoped>
.route-planner {
  position: relative;
  width: 100%;
  height: calc(100vh - var(--navbar-height, 60px));
}

.map-container {
  position: relative;
  width: 100%;
  height: 100%;
}

.map {
  width: 100%;
  height: 100%;
}

.info-banner {
  position: absolute;
  top: 1rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  background: white;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  max-width: 90%;
}

.info-banner-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.info-banner-icon {
  color: var(--brand-primary);
  font-size: 0.85rem;
}

.info-banner-message {
  font-size: 0.75rem;
  color: #333;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.banner-route-icon {
  color: var(--brand-primary);
  font-size: 0.8rem;
  margin: 0 0.1rem;
}

.info-banner-close {
  background: none;
  border: none;
  cursor: pointer;
  color: #666;
  padding: 0.15rem;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.info-banner-close:hover {
  background-color: #f5f5f5;
  color: #333;
}

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

.control-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.control-btn.active {
  background: var(--brand-primary);
  color: white;
}

.control-btn.active:hover:not(:disabled) {
  background: #e55a0d; /* Darker orange */
  color: white;
}

/* Route button (first button) - orange icon when not active */
.control-btn:first-child:not(.active) i {
  color: var(--brand-primary);
}

.waypoint-context-menu {
  position: fixed;
  background: white;
  border: 1px solid #ddd;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 10000;
  min-width: 160px;
  overflow: hidden;
}

.context-menu-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  font-size: 14px;
  color: #333;
}

.context-menu-item:hover {
  background-color: #f5f5f5;
}

.context-menu-item i {
  margin-right: 8px;
  width: 16px;
  text-align: center;
  color: #dc3545;
}

/* Start/End markers for guided mode */
:global(.custom-start-end-marker) {
  background: transparent;
  border: none;
}

:global(.start-end-marker) {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  transition: all 0.2s ease;
  border: 2px solid white;
  font-size: 0.65rem;
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

/* Leaflet popup compact styling */
:global(.segment-hover-popup .leaflet-popup-content-wrapper) {
  padding: 0;
  border-radius: 6px;
}

:global(.segment-hover-popup .leaflet-popup-content) {
  margin: 0;
  padding: 0;
  width: auto !important;
}

/* Segment popup card styles */
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
  width: 340px;
}

:global(.segment-popup-card:hover) {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
  border-color: rgba(255, 107, 53, 0.3);
}

:global(.segment-popup-card.selected) {
  box-shadow: 0 3px 8px rgba(255, 107, 53, 0.3);
  transform: translateY(-1px);
  border-color: #ff6b35;
}

:global(.segment-popup-card.selected:hover) {
  box-shadow: 0 5px 15px rgba(255, 107, 53, 0.4);
  transform: translateY(-3px);
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
  color: #f97316;
  font-weight: 600;
}

:global(.tire-recommendations) {
  display: flex;
  flex-direction: row;
  gap: 6px;
  width: 100%;
  justify-content: center;
}

:global(.tire-recommendation) {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 0.6rem;
}

:global(.tire-recommendation i) {
  font-size: 0.7rem;
  color: #666;
}

:global(.tire-badge) {
  display: inline-block;
  padding: 1px 4px;
  background: #e2e8f0;
  border-radius: 3px;
  font-size: 0.6rem;
  font-weight: 500;
  color: #475569;
}

/* Segment landmark styles */
:global(.segment-landmark) {
  background: transparent !important;
  border: none !important;
}

:global(.segment-landmark .landmark-content) {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  font-size: 0.6rem;
  font-weight: bold;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  position: relative;
}

:global(.segment-landmark-start .landmark-content) {
  background: #10b981;
  color: white;
}

:global(.segment-landmark-end .landmark-content) {
  background: #ef4444;
  color: white;
}

:global(.segment-landmark .landmark-index) {
  position: absolute;
  top: -7px;
  right: -7px;
  background: #374151;
  color: white;
  border-radius: 50%;
  width: 14px;
  height: 14px;
  font-size: 9px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid white;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

/* Custom waypoint markers for free mode */
:global(.custom-waypoint-marker) {
  background: transparent;
  border: none;
}

:global(.waypoint-marker) {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 11px;
  color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  transition: all 0.2s ease;
}

:global(.waypoint-marker:hover) {
  transform: scale(1.1);
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.4);
}

:global(.waypoint-start) {
  background: #f97316; /* Orange */
  border: 2px solid white;
}

:global(.waypoint-end) {
  background: #3b82f6; /* Blue */
  border: 2px solid white;
}

:global(.waypoint-intermediate) {
  background: #6b7280; /* Gray */
  border: 2px solid white;
}

/* Chart cursor marker */
:global(.custom-chart-cursor) {
  background: transparent;
  border: none;
}

:global(.chart-cursor-marker) {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: white;
  border: 3px solid #ea580c;
  box-shadow: 0 0 0 3px rgba(234, 88, 12, 0.3);
  animation: pulse-cursor 1.5s ease-in-out infinite;
}

@keyframes pulse-cursor {
  0%,
  100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.8;
  }
}
</style>
