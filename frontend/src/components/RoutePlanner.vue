<template>
  <div class="route-planner">
    <div class="map-container">
      <div id="route-map" class="map"></div>

      <!-- Top right corner controls -->
      <div class="map-controls">
        <div class="control-group">
          <button class="control-btn" @click="clearMap" :title="'Clear Map'">
            <i class="fa-solid fa-trash"></i>
          </button>
          <button
            class="control-btn"
            @click="undo"
            :disabled="!canUndo"
            :title="'Undo'"
          >
            <i class="fa-solid fa-undo"></i>
          </button>
          <button
            class="control-btn"
            @click="redo"
            :disabled="!canRedo"
            :title="'Redo'"
          >
            <i class="fa-solid fa-redo"></i>
          </button>
        </div>
      </div>

      <!-- Bottom elevation section -->
      <div class="elevation-section" :class="{ 'elevation-expanded': showElevation }">
        <!-- Toggle button with integrated stats -->
        <div class="elevation-toggle" @click="toggleElevation">
          <div class="elevation-toggle-content">
            <div class="toggle-left">
              <i class="fa-solid fa-mountain"></i>
              <span class="elevation-toggle-text">Elevation Profile</span>
              <div class="toggle-stats">
                <div class="toggle-stat" title="Total Distance">
                  <i class="fa-solid fa-route"></i>
                  <span>{{ routeDistance.toFixed(1) }} km</span>
                </div>
                <div class="toggle-stat" title="Elevation Gain">
                  <i class="fa-solid fa-arrow-trend-up"></i>
                  <span>{{ elevationStats.totalGain }}m</span>
                </div>
                <div class="toggle-stat" title="Elevation Loss">
                  <i class="fa-solid fa-arrow-trend-down"></i>
                  <span>{{ elevationStats.totalLoss }}m</span>
                </div>
              </div>
            </div>
            <i class="fa-solid fa-chevron-up"></i>
          </div>
        </div>

        <!-- Elevation content -->
        <div class="elevation-content" v-if="showElevation">
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
import { onMounted, onUnmounted, ref, nextTick } from 'vue'
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

// eslint-disable-next-line no-unused-vars
const { t: _t } = useI18n()

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
}

const elevationSegments = ref<ElevationSegment[]>([])
const elevationCache = new Map<
  string,
  Array<{ lat: number; lng: number; elevation: number; distance: number }>
>()
const actualRouteCoordinates = ref<Array<{ lat: number; lng: number }>>([]) // Store actual OSRM route coordinates

// Route persistence keys
const ROUTE_STORAGE_KEY = 'routePlanner_currentRoute'
const MAP_STATE_STORAGE_KEY = 'routePlanner_mapState' // eslint-disable-line no-unused-vars

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
onMounted(async () => {
  // Add CSS class to prevent scrollbars on the entire page
  document.body.classList.add('route-planner-active')
  document.documentElement.classList.add('route-planner-active')

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

  // Save current route before unmounting
  saveCurrentRoute()

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

  // Set default crosshair cursor
  map.getContainer().style.cursor = 'crosshair'
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
      // Simple click on map - add waypoint
      addWaypoint(e.latlng)
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

  // Reset cursor
  if (map) {
    map.getContainer().style.cursor = 'crosshair'
  }

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
  if (waypoints.length > 0) {
    saveState()
  }

  // Clear everything
  clearRoute()
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
    // Use actual OSRM route coordinates if available, otherwise fall back to segment approach
    if (actualRouteCoordinates.value.length >= 2) {
      await calculateElevationFromActualRoute()
    } else {
      // Update segments based on current waypoints
      await updateElevationSegments()

      // Calculate stats from all processed segments
      await calculateStatsFromSegments()

      // Update chart with all segment data
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
    // You could also show a user-friendly error message here
    console.error(
      'Elevation data unavailable. Please check your internet connection and try again.'
    )
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
  if (isEnd) return '#3b82f6' // Blue
  return '#6b7280' // Gray
}

function calculateNiceElevationScale(elevations: number[]) {
  if (elevations.length === 0) {
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

  const minElev = Math.min(...elevations)
  const maxElev = Math.max(...elevations)

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
          label: 'Elevation',
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
            text: 'Distance (km)'
          },
          min: 0,
          max: chartData[chartData.length - 1]?.x || 1,
          ticks: {
            callback: function (value: any) {
              return `${Number(value).toFixed(1)} km`
            }
          }
        },
        y: {
          display: true,
          title: {
            display: true,
            text: 'Elevation (m)'
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
  const newSegments: ElevationSegment[] = []

  for (let i = 0; i < waypoints.length - 1; i++) {
    const startPoint = waypoints[i].latLng
    const endPoint = waypoints[i + 1].latLng
    const distance = map?.distance(startPoint, endPoint) || 1000

    // Create segment key for caching
    const segmentKey = `${startPoint.lat.toFixed(6)},${startPoint.lng.toFixed(6)}-${endPoint.lat.toFixed(6)},${endPoint.lng.toFixed(6)}`

    // Check if we already have this segment processed
    const existingSegment = elevationSegments.value.find(
      (seg) => seg.startWaypointIndex === i && seg.endWaypointIndex === i + 1
    )

    if (existingSegment && existingSegment.isProcessed) {
      // Segment already processed, keep it
      newSegments.push(existingSegment)
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
      lastUpdated: Date.now()
    }

    // Check cache first
    if (elevationCache.has(segmentKey)) {
      segment.sampledPoints = elevationCache.get(segmentKey)!
      segment.isProcessed = true
    } else {
      // Process new segment
      try {
        segment.sampledPoints = await processSegmentElevation(segment)
        elevationCache.set(segmentKey, segment.sampledPoints)
        segment.isProcessed = true
      } catch (error) {
        console.error(`Failed to process segment ${i}-${i + 1}:`, error)
        throw new Error(
          `Failed to process elevation segment ${i}-${i + 1}: ${error instanceof Error ? error.message : String(error)}`
        )
      }
    }

    newSegments.push(segment)
  }

  elevationSegments.value = newSegments
}

async function processSegmentElevation(
  segment: ElevationSegment
): Promise<Array<{ lat: number; lng: number; elevation: number; distance: number }>> {
  const samplingDistance = 100 // 100m resolution
  const numSamples = Math.max(2, Math.ceil(segment.distance / samplingDistance))
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

async function updateAffectedSegments(changedWaypointIndex: number) {
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

      // Create new segment key
      const segmentKey = `${startPoint.lat.toFixed(6)},${startPoint.lng.toFixed(6)}-${endPoint.lat.toFixed(6)},${endPoint.lng.toFixed(6)}`

      // Clear cache for this segment
      elevationCache.delete(segmentKey)

      // Update segment data
      segment.startLatLng = startPoint
      segment.endLatLng = endPoint
      segment.distance = map?.distance(startPoint, endPoint) || 1000
      segment.isProcessed = false

      // Process the updated segment
      try {
        segment.sampledPoints = await processSegmentElevation(segment)
        elevationCache.set(segmentKey, segment.sampledPoints)
        segment.isProcessed = true
      } catch (error) {
        console.error(`Failed to update segment ${segmentIndex}:`, error)
        throw new Error(
          `Failed to update elevation segment ${segmentIndex}: ${error instanceof Error ? error.message : String(error)}`
        )
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

    // Batch requests to avoid rate limits (max 100 points per request)
    const batchSize = 100
    const batches = []

    for (let i = 0; i < points.length; i += batchSize) {
      batches.push(points.slice(i, i + batchSize))
    }

    for (let batchIndex = 0; batchIndex < batches.length; batchIndex++) {
      const batch = batches[batchIndex]
      const locations = batch.map((p) => `${p.lat},${p.lng}`).join('|')
      const url = `https://api.open-elevation.com/api/v1/lookup?locations=${locations}`

      try {
        const response = await fetch(url)
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        const data = await response.json()

        if (!data.results || !Array.isArray(data.results)) {
          throw new Error('Invalid API response format - missing results array')
        }

        const batchElevations = data.results.map((result: any) => result.elevation)
        elevations.push(...batchElevations)

        // Small delay to avoid rate limiting
        await new Promise((resolve) => setTimeout(resolve, 100))
      } catch (error) {
        console.error(
          `Failed to fetch elevation data for batch ${batchIndex + 1}:`,
          error
        )
        throw new Error(
          `Failed to fetch elevation data for batch ${batchIndex + 1}: ${error instanceof Error ? error.message : String(error)}`
        )
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
    // Only calculate elevation stats if we have route data ready
    if (actualRouteCoordinates.value.length >= 2) {
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

// Calculate elevation using actual OSRM route coordinates
async function calculateElevationFromActualRoute() {
  if (actualRouteCoordinates.value.length < 2) {
    return
  }

  try {
    // Sample points every 100 meters along the actual route
    const sampledPoints = sampleRouteEvery100Meters(actualRouteCoordinates.value)

    // Get elevation data for sampled points
    const elevations = await getElevationData(sampledPoints)

    // Combine elevations with sampled points to create full elevation data
    const elevationData = sampledPoints.map((point, index) => ({
      ...point,
      elevation: elevations[index] || 0
    }))

    // Apply smoothing to elevation data for both stats and chart
    const smoothedElevations = smoothElevationData(elevations, 5)

    // Calculate statistics using smoothed data
    await calculateStatsFromElevations(elevations) // This function now handles smoothing internally

    // Update chart with smoothed elevation values and sampled points
    const smoothedElevationData = elevationData.map((point, index) => ({
      ...point,
      elevation: smoothedElevations[index] || point.elevation
    }))
    await updateElevationChart(smoothedElevations, smoothedElevationData)

    // Update route distance
    const calculatedDistance =
      elevationData.length > 0
        ? elevationData[elevationData.length - 1].distance / 1000
        : 0
    routeDistance.value = calculatedDistance
  } catch (error) {
    console.error('Error calculating elevation from actual route:', error)
    // Show error to user instead of using mock data
    elevationStats.value = {
      totalGain: 0,
      totalLoss: 0,
      maxElevation: 0,
      minElevation: 0
    }
    throw error // Re-throw to let calling code handle the error
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
  if (elevations.length === 0) {
    elevationStats.value = {
      totalGain: 0,
      totalLoss: 0,
      maxElevation: 0,
      minElevation: 0
    }
    return
  }

  // Apply smoothing to reduce noise before calculating statistics
  const smoothedElevations = smoothElevationData(elevations, 5) // 5-point moving average

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

/* Map cursor styling */
.map {
  cursor: crosshair !important;
}

.map:active {
  cursor: grabbing !important;
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
  background: #3b82f6; /* Blue */
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
}

.elevation-expanded {
  transform: translateY(0); /* Show full content when expanded */
  background: rgba(255, 255, 255, 0.95); /* More opaque when expanded */
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
  /* Remove fixed max-height and overflow to let content determine height */
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
  /* Content will determine the height naturally */
  /* Ensure content doesn't cause overflow */
  overflow: visible;
  /* Use flexbox to manage content layout */
  display: flex;
  flex-direction: column;
}

.elevation-chart {
  padding: 0.3rem;
  /* Remove flex: 1 to prevent expansion */
  flex-shrink: 0;
}

.chart-container {
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  height: 20vh; /* Fixed height to prevent expansion */
  position: relative;
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
</style>
