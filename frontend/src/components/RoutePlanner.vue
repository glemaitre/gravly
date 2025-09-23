<template>
  <div class="route-planner">
    <div class="map-container">
      <div id="route-map" class="map"></div>

      <!-- Top right corner controls -->
      <div class="map-controls">
        <div class="control-group">
          <button
            class="control-btn"
            @click="clearMap"
            :title="'Clear Map'"
          >
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
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, onUnmounted, ref, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import L from 'leaflet'
import 'leaflet-routing-machine'
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

// Map and routing state
let map: any = null
let routingControl: any = null
let waypoints: any[] = []
let routeLine: any = null
let routeToleranceBuffer: any = null // Invisible thick line for easier interaction
let waypointMarkers: any[] = []

// Undo/Redo state management
const undoStack: any[][] = []
const redoStack: any[][] = []
const canUndo = ref(false)
const canRedo = ref(false)
const maxHistorySize = 50 // Limit history to prevent memory issues

// Route persistence keys
const ROUTE_STORAGE_KEY = 'routePlanner_currentRoute'
const MAP_STATE_STORAGE_KEY = 'routePlanner_mapState'

// Mouse interaction state
let mouseDownStartPoint: any = null
let mouseDownStartTime: number = 0
let isDragging = false
let dragThreshold = 5 // pixels
let clickTimeThreshold = 300 // milliseconds
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
    attribution: 'Maps © <a href="https://www.thunderforest.com/">Thunderforest</a>, Data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18
  }).addTo(map!)

  // Add zoom change detection with logging
  map.on('zoomstart', () => {
    const currentZoom = map.getZoom()
    console.log('🔍 Zoom change starting - current zoom:', currentZoom)
  })

  map.on('zoomend', () => {
    const newZoom = map.getZoom()
    const newWeight = getZoomResponsiveWeight(newZoom)
    const newBufferWeight = getToleranceBufferWeight(newZoom)

    let oldWeight = 'N/A (no route line)'
    let oldBufferWeight = 'N/A (no buffer)'

    if (routeLine && routeToleranceBuffer) {
      oldWeight = routeLine.options.weight || 'unknown'
      oldBufferWeight = routeToleranceBuffer.options.weight || 'unknown'

      // Update both the visible route line and invisible tolerance buffer
      routeLine.setStyle({ weight: newWeight })
      routeToleranceBuffer.setStyle({ weight: newBufferWeight })

      console.log('🔍 ⚡ ZOOM CHANGED - ROUTE LINE & TOLERANCE UPDATED:')
      console.log('🔍   - Zoom level:', newZoom)
      console.log('🔍   - Visible line: ', oldWeight, 'px →', newWeight, 'px')
      console.log('🔍   - Tolerance buffer:', oldBufferWeight, 'px →', newBufferWeight, 'px')
      console.log('🔍   - Tolerance formula: getToleranceBufferWeight(', newZoom, ') = max(12, min(30 -', newZoom, ', 24)) =', newBufferWeight)
    } else {
      console.log('🔍 ⚡ ZOOM CHANGED:')
      console.log('🔍   - Zoom level:', newZoom)
      console.log('🔍   - Would set visible weight to:', newWeight, 'px')
      console.log('🔍   - Would set tolerance weight to:', newBufferWeight, 'px (no route lines exist yet)')
    }
  })

  // Disable double-click waypoint addition
  map.on('dblclick', (e: any) => {
    console.log('Double-click disabled, preventing waypoint addition')
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
    console.log('🗺️ GLOBAL MAP mousedown - currentDragTarget will be set to "map"')
    mouseDownStartPoint = e.containerPoint
    mouseDownStartTime = Date.now()
    isDragging = false
    currentDragTarget = 'map' // Default to map

    console.log('🖱️ Mouse down at:', e.latlng)

    // Add a tiny delay to allow route line handlers to fire first
    setTimeout(() => {
      console.log('🗺️ Final currentDragTarget after potential route override:', currentDragTarget)
    }, 1)
  })

  // Mouse move event handler
  map.on('mousemove', (e: any) => {
    if (!mouseDownStartPoint) return

    const distance = e.containerPoint.distanceTo(mouseDownStartPoint)
    const timeDiff = Date.now() - mouseDownStartTime

    if (!isDragging && distance > dragThreshold) {
      isDragging = true
      console.log('🖱️ 🚀 Drag started, target:', currentDragTarget)
      console.log('🖱️ 🚀 This will determine which handler gets called:')
      console.log('🖱️ 🚀   - "waypoint" -> handleWaypointDragStart')
      console.log('🖱️ 🚀   - "route" -> handleRouteDragStart')
      console.log('🖱️ 🚀   - "map" -> normal map drag')

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
      console.log('🖱️ 🚀 Updating waypoint during drag, index:', draggedWaypointIndex, 'position:', e.latlng)
      updateWaypointPosition(draggedWaypointIndex, e.latlng)
    }
  })

  // Mouse up event handler
  map.on('mouseup', (e: any) => {
    const timeDiff = Date.now() - mouseDownStartTime

    console.log('🖱️ Mouse up - isDragging:', isDragging, 'target:', currentDragTarget, 'time:', timeDiff)

    if (!isDragging && timeDiff < clickTimeThreshold && currentDragTarget === 'map') {
      // Simple click on map - add waypoint
      console.log('🖱️ Adding waypoint at:', e.latlng)
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
    console.log('🔵 Map dragging re-enabled during state reset')
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
  console.log('🔵 ⭐ STARTING waypoint drag for index:', waypointIndex)

  // Set drag active flag to prevent marker rebuilding
  isWaypointDragActive = true
  console.log('🔵 ⭐ Waypoint drag active flag set to TRUE - no marker rebuilding should happen now!')

  // CRITICAL: Disable map dragging to prevent interference
  if (map && map.dragging) {
    map.dragging.disable()
    console.log('🔵 Map dragging disabled for waypoint drag')
  }

  // Verify marker exists before drag
  if (waypointMarkers[waypointIndex]) {
    console.log('🔵 ✅ Marker exists for index', waypointIndex, '- adding drag styling')
    waypointMarkers[waypointIndex].getElement()?.classList.add('waypoint-dragging')
  } else {
    console.log('🔵 ❌ No marker found for index', waypointIndex, 'at drag start!')
  }

  // Change cursor to indicate dragging
  map.getContainer().style.cursor = 'grabbing'
}

function updateWaypointPosition(waypointIndex: number, newLatLng: any) {
  if (waypointIndex < 0 || waypointIndex >= waypoints.length) {
    console.log('🔵 Invalid waypoint index for update:', waypointIndex)
    return
  }

  console.log('🔵 Updating waypoint', waypointIndex, 'to position:', newLatLng)

  // Update waypoint position
  waypoints[waypointIndex] = L.Routing.waypoint(newLatLng)

  // Throttle marker recreation to improve performance (but still be responsive)
  if (markerUpdateTimeout) {
    clearTimeout(markerUpdateTimeout)
  }

  markerUpdateTimeout = setTimeout(() => {
    console.log('🔵 🔄 Recreating marker during drag to ensure visibility')

    // Remove existing marker if it exists
    if (waypointMarkers[waypointIndex] && map.hasLayer(waypointMarkers[waypointIndex])) {
      map.removeLayer(waypointMarkers[waypointIndex])
      console.log('🔵 Removed existing marker for recreation')
    }

    // Create new marker at the new position
    createWaypointMarkerDuringDrag(waypointIndex, newLatLng)
    console.log('🔵 ✅ Marker recreated and should be visible at waypoint', waypointIndex)
  }, 16) // ~60fps update rate
}

function handleWaypointDragEnd(waypointIndex: number, finalLatLng: any) {
  console.log('🔵 Ending waypoint drag for index:', waypointIndex, 'at:', finalLatLng)

  // Save state after waypoint drag completes (position changed)
  saveState()

  // Clear any pending marker updates
  if (markerUpdateTimeout) {
    clearTimeout(markerUpdateTimeout)
    markerUpdateTimeout = null
  }

  // Reset drag active flag to allow marker rebuilding
  isWaypointDragActive = false
  console.log('🔵 Waypoint drag active flag set to false')

  // CRITICAL: Re-enable map dragging
  if (map && map.dragging) {
    map.dragging.enable()
    console.log('🔵 Map dragging re-enabled after waypoint drag')
  }

  // Recreate the marker with full interactivity restored
  console.log('🔵 🔄 Recreating final marker with full interactivity')
  createWaypointMarker(waypointIndex, finalLatLng)

  // Reset cursor
  map.getContainer().style.cursor = 'crosshair'

  // Force route update now that drag is complete
  console.log('🔵 Forcing route update after drag completion')
  if (routingControl) {
    routingControl.setWaypoints(waypoints)
  }
}

function handleRouteDragStart(e: any) {
  console.log('🔶 Starting route drag at:', e.latlng)

  // Disable map dragging for route drag operations too
  if (map && map.dragging) {
    map.dragging.disable()
    console.log('🔶 Map dragging disabled for route drag')
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

function handleRouteDragEnd(finalLatLng: any) {
  console.log('🔶 Ending route drag at:', finalLatLng)

  // Re-enable map dragging (safety check, should be handled by waypoint drag end)
  if (map && map.dragging && !map.dragging.enabled()) {
    map.dragging.enable()
    console.log('🔶 Map dragging re-enabled after route drag')
  }

  debounceRouteUpdate()
}

function findBestInsertionPoint(clickLatLng: any): number {
  if (waypoints.length < 2) return waypoints.length

  let bestIndex = 1 // Default to insert after first waypoint
  let minDistance = Infinity

  console.log('🔍 Finding best insertion point for click at:', clickLatLng)
  console.log('🔍 Checking', waypoints.length - 1, 'route segments')

  // Find the route segment closest to the click point
  for (let i = 0; i < waypoints.length - 1; i++) {
    const start = waypoints[i].latLng
    const end = waypoints[i + 1].latLng

    // Calculate perpendicular distance to line segment
    const distance = calculateDistanceToLineSegment(clickLatLng, start, end)

    console.log(`🔍 Segment ${i}-${i+1}: distance = ${distance.toFixed(2)}m`)

    if (distance < minDistance) {
      minDistance = distance
      bestIndex = i + 1
      console.log(`🔍 ✅ New best segment: ${i}-${i+1}, inserting at index ${bestIndex}`)
    }
  }

  console.log(`🔍 Final insertion point: index ${bestIndex} (between waypoints ${bestIndex-1} and ${bestIndex})`)
  return bestIndex
}

function calculateDistanceToLineSegment(point: any, lineStart: any, lineEnd: any): number {
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

  let param = dot / lenSq

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
    console.log('🔄 Skipping route update - waypoint drag is active')
    return
  }

  routeUpdateTimeout = setTimeout(() => {
    if (routingControl) {
      console.log('🔄 Updating route with', waypoints.length, 'waypoints')
      routingControl.setWaypoints(waypoints)
    }
  }, 200)
}


function initializeRoutingControl() {
  if (!map) return

  // Configure OSRM routing
  const routingOptions = {
    router: new L.Routing.OSRMv1({
      serviceUrl: 'https://routing.openstreetmap.de/routed-bike/route/v1',
      profile: 'cycling',
      useHints: false
    }),
    waypoints: waypoints,
    routeWhileDragging: false, // Disabled to prevent auto-zoom
    addWaypoints: false, // Disable automatic waypoint addition
    show: false, // Hide the routing control panel
    // Custom marker creation function to disable default markers
    createMarker: function(i: number, waypoint: any, n: number) {
      // Return null to disable default markers - we handle our own
      return null
    },
    // Disable auto-zoom but keep route calculation
    fitSelectedRoutes: false,
    lineOptions: {
      styles: [
        { color: '#ff6600', weight: 6, opacity: 0.8 }
      ]
    }
  }

  routingControl = L.Routing.control(routingOptions).addTo(map!)

  // Listen for route changes
  routingControl.on('routesfound', (e: any) => {
    console.log('Routes found event:', e)
    const routes = e.routes
    if (routes && routes.length > 0) {
      const route = routes[0]
      console.log('Route data:', route)
      console.log('Route keys:', Object.keys(route))

      // Ensure all waypoints have markers - use rebuild to handle any index issues
      rebuildWaypointMarkers()

      // Create interactive route line
      console.log('Creating new interactive route line')
      setTimeout(() => {
        createClickableRouteLine(route)
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
  console.log('Adding waypoint at:', latlng)

  // Save state for undo functionality
  saveState()

  const newWaypoint = L.Routing.waypoint(latlng)
  const waypointIndex = waypoints.length
  waypoints.push(newWaypoint)
  console.log('Total waypoints:', waypoints.length)

  // Save route after adding waypoint
  saveCurrentRoute()

  // Create draggable marker for this waypoint
  createWaypointMarker(waypointIndex, latlng)

  if (routingControl) {
    routingControl.setWaypoints(waypoints)
  }

  // Auto-center on the newly added waypoint
  if (map) {
    map.setView([latlng.lat, latlng.lng], map.getZoom())
  }
}

function createWaypointMarker(index: number, latlng: any) {
  console.log('📍 Creating waypoint marker for index:', index, 'at position:', latlng, 'dragActive:', isWaypointDragActive)

  // Remove existing marker at this index if it exists
  if (waypointMarkers[index]) {
    console.log('📍 Removing existing marker at index', index)
    map.removeLayer(waypointMarkers[index])
  }

  // Create custom waypoint marker
  const isStart = index === 0
  const isEnd = index === waypoints.length - 1 && waypoints.length > 1
  const markerClass = isStart ? 'waypoint-start' : (isEnd ? 'waypoint-end' : 'waypoint-intermediate')

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
    console.log('🔵 ⭐ Waypoint marker clicked, index:', index, 'at:', e.latlng)
    console.log('🔵 ⭐ This means route line click was NOT detected - checking layering issue')
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

  console.log('📍 ✅ Waypoint marker created and stored at index:', index)

  // Update all existing markers to reflect new start/end positions
  updateWaypointMarkerStyles()
}

function createWaypointMarkerDuringDrag(index: number, latlng: any) {
  console.log('📍 🚀 Creating DRAG marker for index:', index, 'at position:', latlng)

  // Create custom waypoint marker with drag styling
  const isStart = index === 0
  const isEnd = index === waypoints.length - 1 && waypoints.length > 1
  const markerClass = isStart ? 'waypoint-start' : (isEnd ? 'waypoint-end' : 'waypoint-intermediate')

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

  console.log('📍 🚀 ✅ DRAG marker created and should be visible at index:', index)
}

function updateWaypointMarkerStyles() {
  waypointMarkers.forEach((marker, index) => {
    if (!marker) return

    const isStart = index === 0
    const isEnd = index === waypoints.length - 1 && waypoints.length > 1
    const markerClass = isStart ? 'waypoint-start' : (isEnd ? 'waypoint-end' : 'waypoint-intermediate')

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
  console.log('🔄 rebuildWaypointMarkers called, isWaypointDragActive:', isWaypointDragActive)

  // CRITICAL: Don't rebuild markers during active waypoint dragging
  if (isWaypointDragActive) {
    console.log('🔄 ⚠️ SKIPPING marker rebuild - waypoint drag is active')
    return
  }

  console.log('🔄 Rebuilding all waypoint markers, total waypoints:', waypoints.length)

  // Clear all existing markers
  waypointMarkers.forEach((marker, index) => {
    if (marker && map.hasLayer(marker)) {
      console.log('🔄 Removing marker', index, 'from map')
      map.removeLayer(marker)
    }
  })
  waypointMarkers = []

  // Recreate markers for all waypoints
  waypoints.forEach((waypoint, index) => {
    if (waypoint && waypoint.latLng) {
      console.log('🔄 Creating marker for waypoint', index)
      createWaypointMarker(index, waypoint.latLng)
    }
  })

  console.log('🔄 ✅ Rebuilt', waypointMarkers.length, 'waypoint markers')
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

  console.log('Creating interactive route line from route:', route)

  // Try to find existing route polyline on the map
  let existingPolyline = null
  map.eachLayer((layer: any) => {
    if (layer instanceof L.Polyline && (layer.options.color === '#3388ff' || layer.options.color === '#ff6600')) {
      // This is likely the routing control's polyline
      existingPolyline = layer
      console.log('Found existing route polyline:', layer)
    }
  })

  let latLngs = []

  if (existingPolyline) {
    // Clone the existing polyline and make it interactive
    latLngs = (existingPolyline as any).getLatLngs()
    console.log('Using existing polyline coordinates:', latLngs.length, 'points')
  } else {
    // Fallback: try to extract coordinates from route data
    let coordinates = null

    // Method 1: Direct coordinates array
    if (route.coordinates && Array.isArray(route.coordinates)) {
      coordinates = route.coordinates
      console.log('Found coordinates directly:', coordinates.length)
    }
    // Method 2: Routes array with coordinates
    else if (route.routes && Array.isArray(route.routes) && route.routes.length > 0) {
      if (route.routes[0].coordinates) {
        coordinates = route.routes[0].coordinates
        console.log('Found coordinates in routes[0]:', coordinates.length)
      }
    }
    // Method 3: Instructions with coordinates
    else if (route.instructions && Array.isArray(route.instructions) && route.instructions.length > 0) {
      if (route.instructions[0].coordinates) {
        coordinates = route.instructions[0].coordinates
        console.log('Found coordinates in instructions[0]:', coordinates.length)
      }
    }
    // Method 4: Check if route has latlngs property
    else if (route.latlngs && Array.isArray(route.latlngs)) {
      coordinates = route.latlngs
      console.log('Found latlngs directly:', coordinates.length)
    }

    if (!coordinates || coordinates.length < 2) {
      console.log('No valid coordinates found for route line. Route structure:', Object.keys(route))
      return
    }

    // Convert coordinates to LatLng array
    try {
      if (coordinates[0] && typeof coordinates[0] === 'object' && 'lat' in coordinates[0]) {
        // Already LatLng objects
        latLngs = coordinates
      } else if (Array.isArray(coordinates[0]) && coordinates[0].length >= 2) {
        // Array of [lat, lng] pairs
        latLngs = coordinates.map((coord: any) => L.latLng(coord[0], coord[1]))
      } else {
        console.log('Unknown coordinate format:', coordinates[0])
        return
      }
    } catch (error) {
      console.log('Error converting coordinates:', error)
      return
    }
  }

  if (latLngs.length < 2) {
    console.log('Not enough coordinates for route line')
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
  console.log('📍 ✨ ROUTE LINE SYSTEM CREATED:')
  console.log('📍   - Visible line weight:', initialWeight, 'px (zoom-responsive)')
  console.log('📍   - Tolerance buffer weight:', toleranceWeight, 'px (invisible, for interaction)')
  console.log('📍   - Current zoom level:', currentZoom)
  console.log('📍   - Color: #ff6b35 (orange)')
  console.log('📍   - Z-index: 1501 (visible) / 1500 (buffer)')
  console.log('📍   - Tolerance formula: max(12, min(30 - ', currentZoom, ', 24)) =', toleranceWeight)

  // Add mouse event handlers to the invisible tolerance buffer (better hit detection)
  routeToleranceBuffer.on('mousedown', (e: any) => {
    console.log('🔶 ✅ TOLERANCE BUFFER mousedown - trying to override currentDragTarget to "route"')
    console.log('🔶 ✅ Buffer weight:', toleranceWeight, 'px, visible line weight:', initialWeight, 'px')
    console.log('🔶 ✅ Previous currentDragTarget was:', currentDragTarget)
    console.log('🔶 ✅ Route clicked at:', e.latlng, '(zoom level:', currentZoom, ')')

    // CRITICAL: Stop propagation immediately to prevent map handler interference
    L.DomEvent.stopPropagation(e)
    L.DomEvent.preventDefault(e)

    // Force override the mouse interaction state for route dragging
    currentDragTarget = 'route'
    mouseDownStartPoint = e.containerPoint
    mouseDownStartTime = Date.now()
    isDragging = false

    console.log('🔶 ⚡ Route click processed via tolerance buffer - currentDragTarget now set to:', currentDragTarget)

    return false // Additional event blocking
  })

  // Add hover effects - tolerance buffer detects hover, visible line changes appearance
  routeToleranceBuffer.on('mouseover', () => {
    if (routeLine && !isDragging) {
      const currentZoom = map.getZoom()
      const baseWeight = getZoomResponsiveWeight(currentZoom)
      const bufferWeight = getToleranceBufferWeight(currentZoom)
      const hoverWeight = baseWeight + 5 // Add 5px for dramatic hover effect
      routeLine.setStyle({ opacity: 1.0, weight: hoverWeight })
      console.log('📍 Route HOVER detected by tolerance buffer (', bufferWeight + 'px) - visible line weight increased to', hoverWeight + 'px (zoom', currentZoom + ')')
      map.getContainer().style.cursor = 'grab'
    }
  })

  routeToleranceBuffer.on('mouseout', () => {
    if (routeLine && !isDragging) {
      const currentZoom = map.getZoom()
      const baseWeight = getZoomResponsiveWeight(currentZoom)
      const bufferWeight = getToleranceBufferWeight(currentZoom)
      routeLine.setStyle({ opacity: 0.7, weight: baseWeight })
      console.log('📍 Route UNHOVER detected by tolerance buffer (', bufferWeight + 'px) - visible line weight restored to', baseWeight + 'px (zoom', currentZoom + ')')
      map.getContainer().style.cursor = 'crosshair'
    }
  })

  console.log('Created interactive route line with', latLngs.length, 'points')
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
    waypoints: waypoints.map(wp => ({
      lat: wp.latLng.lat,
      lng: wp.latLng.lng,
      name: wp.name || ''
    })),
    timestamp: new Date().toISOString()
  }

  try {
    localStorage.setItem(ROUTE_STORAGE_KEY, JSON.stringify(routeData))
    console.log('💾 Route saved to localStorage:', routeData)
  } catch (error) {
    console.error('Failed to save route to localStorage:', error)
  }
}

function loadSavedRoute() {
  try {
    const savedRoute = localStorage.getItem(ROUTE_STORAGE_KEY)
    if (!savedRoute) {
      console.log('💾 No saved route found in localStorage')
      return
    }

    const routeData = JSON.parse(savedRoute)
    if (!routeData.waypoints || routeData.waypoints.length === 0) {
      console.log('💾 Saved route has no waypoints')
      return
    }

    console.log('💾 Loading saved route from localStorage:', routeData)

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

    console.log('💾 ✅ Route restored successfully with', waypoints.length, 'waypoints')

  } catch (error) {
    console.error('Failed to load saved route from localStorage:', error)
  }
}

function centerMapOnRoute() {
  if (!map || waypoints.length === 0) {
    console.log('🗺️ Cannot center map - no map or waypoints')
    return
  }

  try {
    // Create bounds from all waypoints
    const bounds = L.latLngBounds(
      waypoints.map(wp => wp.latLng)
    )

    // Fit map to show all waypoints with some padding
    map.fitBounds(bounds, {
      padding: [20, 20], // Add 20px padding around the route
      maxZoom: 16 // Don't zoom in too much for very short routes
    })

    console.log('🗺️ ✅ Map centered on route with', waypoints.length, 'waypoints')

  } catch (error) {
    console.error('Failed to center map on route:', error)
  }
}

// History management functions
function saveState() {
  // Create deep copy of current waypoints
  const currentState = waypoints.map(wp => ({
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
  const currentState = waypoints.map(wp => ({
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
  const currentState = waypoints.map(wp => ({
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
  waypointMarkers.forEach(marker => {
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

// Enhanced clearRoute to work with history
function clearRoute() {
  waypoints = []

  // Clear saved route from localStorage
  localStorage.removeItem(ROUTE_STORAGE_KEY)

  // Clear waypoint markers
  waypointMarkers.forEach(marker => {
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
  0% { transform: scale(1); }
  50% { transform: scale(1.2); }
  100% { transform: scale(1); }
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
  background: #fef2f2;
  color: #dc2626;
}

.control-btn:first-child:hover:not(:disabled) {
  background: #fee2e2;
  color: #b91c1c;
}

</style>
