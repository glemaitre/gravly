<template>
  <div class="route-planner">
    <div class="sidebar">
      <div class="sidebar-content">
        <div class="card menu-card">
          <div class="menu-section">
            <div class="menu-section-title">
              {{ t('routePlanner.planning') }}
    </div>
            <ul class="menu-list">
              <li class="menu-item" @click="clearRoute" :title="t('routePlanner.clearRoute')">
                <span class="icon"><i class="fa-solid fa-trash"></i></span>
                <span class="text">{{ t('routePlanner.clearRoute') }}</span>
              </li>
              <li class="menu-item" @click="saveRoute" :title="t('routePlanner.saveRoute')">
                <span class="icon"><i class="fa-solid fa-save"></i></span>
                <span class="text">{{ t('routePlanner.saveRoute') }}</span>
              </li>
              <li class="menu-item" @click="loadRoute" :title="t('routePlanner.loadRoute')">
                <span class="icon"><i class="fa-solid fa-folder-open"></i></span>
                <span class="text">{{ t('routePlanner.loadRoute') }}</span>
              </li>
            </ul>
    </div>

          <div class="menu-section">
            <div class="menu-section-title">
              {{ t('routePlanner.routeInfo') }}
            </div>
            <div class="route-stats" v-if="routeInfo">
              <div class="stat-item">
                <span class="icon"><i class="fa-solid fa-ruler"></i></span>
                <span class="label">{{ t('routePlanner.distance') }}:</span>
                <span class="value">{{ formatDistance(routeInfo.totalDistance) }}</span>
              </div>
              <div class="stat-item">
                <span class="icon"><i class="fa-solid fa-clock"></i></span>
                <span class="label">{{ t('routePlanner.duration') }}:</span>
                <span class="value">{{ formatDuration(routeInfo.totalDuration) }}</span>
              </div>
            </div>
            <div v-else class="no-route">
          <i class="fa-solid fa-route"></i>
              <span>{{ t('routePlanner.noRoute') }}</span>
        </div>
        </div>

        </div>
      </div>
    </div>

    <div class="content">
      <div class="map-container">
        <div id="route-map" class="map"></div>
        <div class="map-controls">
          <div class="control-group">
            <button
              class="control-btn"
              @click="centerMap"
              :title="t('routePlanner.centerMap')"
            >
              <i class="fa-solid fa-crosshairs"></i>
            </button>
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

// Simplified state management for mouse interactions
let routeUpdateTimeout: any = null

// Route information
const routeInfo = ref<{
  totalDistance: number
  totalDuration: number
} | null>(null)

// Initialize map
onMounted(async () => {
  await nextTick()
  initializeMap()
})

onUnmounted(() => {
  if (map) {
    map.remove()
  }
})

function initializeMap() {
  const mapContainer = document.getElementById('route-map')
  if (!mapContainer) return

  // Initialize map with OpenCycleMap tiles
  map = L.map('route-map', {
    center: [46.5197, 6.6323], // Default to Lausanne area
    zoom: 13
  })

  // Add OpenCycleMap tiles via backend proxy (secure API key handling)
  L.tileLayer('/api/map-tiles/{z}/{x}/{y}.png', {
    attribution: 'Maps © <a href="https://www.thunderforest.com/">Thunderforest</a>, Data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18
  }).addTo(map!)

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

  // Simplified mouse interaction - just mouse up for waypoint creation
  map.on('mouseup', (e: any) => {
    console.log('🖱️ MOUSE UP - Adding waypoint at:', e.latlng)
    addWaypoint(e.latlng)
  })

  // Set default crosshair cursor
  map.getContainer().style.cursor = 'crosshair'

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
    // Disable all click handling
    waypointMode: {
      addWaypoints: false
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
      updateRouteInfo(route)
      // generateElevationProfile(route) // Disabled for now

      // Create clickable route line
      console.log('Creating new clickable route line')
      setTimeout(() => {
        createClickableRouteLine(route)
      }, 100)
    }
  })

  // Listen for waypoint changes
  routingControl.on('waypointsspliced', (e: any) => {
    waypoints = e.waypoints
  })
}

function addWaypoint(latlng: any) {
  console.log('Adding waypoint at:', latlng)
  const newWaypoint = L.Routing.waypoint(latlng)
  waypoints.push(newWaypoint)
  console.log('Total waypoints:', waypoints.length)

  if (routingControl) {
    routingControl.setWaypoints(waypoints)
  }

  // Auto-center on the newly added waypoint
  if (map) {
    map.setView([latlng.lat, latlng.lng], map.getZoom())
  }
}


function clearRoute() {
  waypoints = []
  if (routingControl) {
    routingControl.setWaypoints([])
  }
  // Remove route line
  if (routeLine) {
    map.removeLayer(routeLine)
    routeLine = null
  }
  routeInfo.value = null
}

function saveRoute() {
  if (!routeInfo.value || waypoints.length < 2) return

  const routeData = {
    waypoints: waypoints.map(wp => ({
      lat: wp.latLng.lat,
      lng: wp.latLng.lng,
      name: wp.name || ''
    })),
    routeInfo: routeInfo.value,
    timestamp: new Date().toISOString(),
    name: `Route ${new Date().toLocaleDateString()}`
  }

  // Save to localStorage for now
  const savedRoutes = JSON.parse(localStorage.getItem('savedRoutes') || '[]')
  savedRoutes.push(routeData)
  localStorage.setItem('savedRoutes', JSON.stringify(savedRoutes))

  alert(t('routePlanner.routeSaved'))
}

function loadRoute() {
  const savedRoutes = JSON.parse(localStorage.getItem('savedRoutes') || '[]')
  if (savedRoutes.length === 0) {
    alert(t('routePlanner.noSavedRoutes'))
    return
  }

  // For now, load the most recent route
  const routeData = savedRoutes[savedRoutes.length - 1]
  waypoints = routeData.waypoints.map((wp: any) => L.Routing.waypoint(L.latLng(wp.lat, wp.lng), wp.name))

  if (routingControl) {
    routingControl.setWaypoints(waypoints)
  }

  routeInfo.value = routeData.routeInfo
}

function centerMap() {
  // Center map functionality disabled - user manages zoom manually
  console.log('Center map functionality disabled')
}

// Helper functions for clean mouse interaction logic


// Create a clickable route line
function createClickableRouteLine(route: any) {
  // Remove existing route line
  if (routeLine) {
    map.removeLayer(routeLine)
  }

  console.log('Creating route line from route:', route)

  // Try to find existing route polyline on the map
  let existingPolyline = null
  map.eachLayer((layer: any) => {
    if (layer instanceof L.Polyline && layer.options.color === '#3388ff') {
      // This is likely the routing control's polyline
      existingPolyline = layer
      console.log('Found existing route polyline:', layer)
    }
  })

  if (existingPolyline) {
    // Clone the existing polyline and make it clickable
    const latLngs = (existingPolyline as any).getLatLngs()
    console.log('Using existing polyline coordinates:', latLngs.length, 'points')

    routeLine = L.polyline(latLngs, {
      color: '#ff6b35', // Orange color
      weight: 6,
      opacity: 0.8,
      interactive: true // Make it clickable
    }).addTo(map)

    console.log('Created clickable route line with', latLngs.length, 'points')
    return
  }

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
  let latLngs = []
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

  // Create polyline with click events
    routeLine = L.polyline(latLngs, {
    color: '#ff6b35', // Orange color to match the route
      weight: 6,
      opacity: 0.8,
    interactive: true // Make it clickable
    }).addTo(map)

  console.log('Created clickable route line with', latLngs.length, 'points')
}

function updateRouteInfo(route: any) {
  routeInfo.value = {
    totalDistance: route.summary.totalDistance / 1000, // Convert to km
    totalDuration: route.summary.totalTime / 60 // Convert to minutes
  }
}


// Utility functions
function formatDistance(km: number): string {
  return `${km.toFixed(1)} km`
}

function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60)
  const mins = Math.round(minutes % 60)
  return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`
}

</script>

<style scoped>
.route-planner {
  display: flex;
  height: 100vh;
  background: #f8fafc;
}

.sidebar {
  width: 300px;
  background: white;
  border-right: 1px solid #e5e7eb;
  overflow-y: auto;
}

.sidebar-content {
  padding: 1rem;
}

.menu-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
}

.menu-section {
  margin-bottom: 1.5rem;
}

.menu-section:last-child {
  margin-bottom: 0;
}

.menu-section-title {
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.75rem;
}

.menu-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.menu-item:hover {
  background: #f3f4f6;
}

.menu-item .icon {
  width: 20px;
  text-align: center;
  color: #6b7280;
}

.menu-item .text {
  font-size: 0.875rem;
  color: #374151;
}

.route-stats {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: #f9fafb;
  border-radius: 6px;
}

.stat-item .icon {
  width: 16px;
  color: #6b7280;
}

.stat-item .label {
  font-size: 0.875rem;
  color: #6b7280;
  flex: 1;
}

.stat-item .value {
  font-weight: 600;
  color: #111827;
}

.no-route {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 2rem;
  color: #9ca3af;
  text-align: center;
}

.content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.map-container {
  flex: 1;
  position: relative;
}

.map {
  width: 100%;
  height: 100%;
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
}

.control-btn:hover {
  background: #f3f4f6;
  transform: translateY(-1px);
}

.control-btn.active {
  background: #ff6600;
  color: white;
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
</style>
