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
              <div class="stat-item">
                <span class="icon"><i class="fa-solid fa-mountain"></i></span>
                <span class="label">{{ t('routePlanner.elevation') }}:</span>
                <span class="value">{{ formatElevation(routeInfo.totalElevation) }}</span>
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

      <!-- Elevation Profile -->
    <div class="elevation-profile" v-if="elevationProfile.length > 0">
        <div class="profile-header">
          <h3>{{ t('routePlanner.elevationProfile') }}</h3>
        </div>
        <div class="profile-chart">
          <canvas ref="elevationChart" class="elevation-canvas"></canvas>
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
import { Chart, LineController, LineElement, PointElement, LinearScale, CategoryScale, Filler, Tooltip } from 'chart.js'

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

// Register Chart.js components
Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Filler, Tooltip)

const { t } = useI18n()

// Map and routing state
let map: any = null
let routingControl: any = null
let waypoints: any[] = []
let waypointMarkers: any[] = []
let routeLine: any = null

// Simplified state management for mouse interactions
let mouseDownOnWaypoint = false
let isPanning = false
let draggedWaypoint: any = null
let routeUpdateTimeout: any = null

// Route information
const routeInfo = ref<{
  totalDistance: number
  totalDuration: number
  totalElevation: number
} | null>(null)

// Elevation profile
const elevationProfile = ref<{ distance: number; elevation: number }[]>([])
const elevationChart = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null

// Initialize map
onMounted(async () => {
  await nextTick()
  initializeMap()
})

onUnmounted(() => {
  if (map) {
    map.remove()
  }
  if (chart) {
    chart.destroy()
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

  // Add OpenCycleMap tiles
  const apiKey = import.meta.env.THUNDERFOREST_API_KEY || 'demo'
  L.tileLayer(`https://{s}.tile.thunderforest.com/cycle/{z}/{x}/{y}.png?apikey=${apiKey}`, {
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

  // Simplified mouse interaction handlers - only mouse down + up for waypoint creation
  map.on('mousedown', (e: any) => {
    console.log('🖱️ MOUSE DOWN:', e.latlng)

    // Check if clicking on a waypoint
    const clickedWaypoint = findWaypointAtPosition(e.latlng)
    if (clickedWaypoint) {
      console.log('🖱️ Clicked on waypoint - starting drag')
      mouseDownOnWaypoint = true
      draggedWaypoint = clickedWaypoint
      isPanning = false
      return
    }

    // Regular map click - prepare for panning
    console.log('🖱️ Clicked on map - preparing for pan')
      mouseDownOnWaypoint = false
    isPanning = true
  })

  map.on('mousemove', (e: any) => {
    if (mouseDownOnWaypoint && draggedWaypoint) {
      console.log('🖱️ DRAGGING WAYPOINT:', e.latlng)
      // Rule: Move waypoint to new location and trigger recomputation
      draggedWaypoint.setLatLng(e.latlng)
      updateWaypointPosition(draggedWaypoint, e.latlng)
      triggerRouteRecomputation()
    } else if (isPanning) {
      console.log('🖱️ PANNING MAP')
      // Let Leaflet handle panning naturally
    }
  })

  map.on('mouseup', (e: any) => {
    console.log('🖱️ MOUSE UP:', e.latlng)

    if (mouseDownOnWaypoint && draggedWaypoint) {
      console.log('🖱️ Mouse up after dragging waypoint - finalizing')
      // Rule: Finalize waypoint position and trigger recomputation
      draggedWaypoint.setLatLng(e.latlng)
      updateWaypointPosition(draggedWaypoint, e.latlng)
      triggerRouteRecomputation()
      mouseDownOnWaypoint = false
      draggedWaypoint = null
    } else if (isPanning) {
      console.log('🖱️ Mouse up after panning - adding waypoint')
      // Rule: Mouse down + mouse up not on waypoint -> create waypoint
      addWaypoint(e.latlng)
      isPanning = false
    } else {
      console.log('🖱️ Mouse up - adding waypoint')
      // Rule: Mouse down + mouse up -> create waypoint
      addWaypoint(e.latlng)
    }
  })

  // Set default crosshair cursor
  map.getContainer().style.cursor = 'crosshair'

  // Add zoom event listener to update marker sizes
  map.on('zoomend', () => {
    updateMarkerSizes()
  })
}

// Function to update all marker sizes based on current zoom level
function updateMarkerSizes() {
  if (!map) return

  const zoom = map.getZoom()
  // Scale from 12px at zoom 8 to 24px at zoom 18
  const baseSize = 12
  const maxSize = 24
  const minZoom = 8
  const maxZoom = 18
  const scale = Math.max(0, Math.min(1, (zoom - minZoom) / (maxZoom - minZoom)))
  const markerSize = Math.round(baseSize + (maxSize - baseSize) * scale)
  const halfSize = markerSize / 2

  // Update all waypoint markers
  waypointMarkers.forEach((marker, index) => {
    if (!marker) return

    const isStart = index === 0
    const isEnd = index === waypointMarkers.length - 1
    const isIntermediate = !isStart && !isEnd

    let markerHtml = ''
    if (isStart) {
      markerHtml = `<div class="waypoint-marker waypoint-start" style="width: ${markerSize}px; height: ${markerSize}px; font-size: ${Math.max(8, markerSize * 0.5)}px;">
                      <i class="fa-solid fa-play"></i>
                    </div>`
    } else if (isEnd) {
      markerHtml = `<div class="waypoint-marker waypoint-end" style="width: ${markerSize}px; height: ${markerSize}px; font-size: ${Math.max(8, markerSize * 0.5)}px;">
                      <i class="fa-solid fa-stop"></i>
                    </div>`
    } else {
      markerHtml = `<div class="waypoint-marker waypoint-intermediate" style="width: ${markerSize}px; height: ${markerSize}px; font-size: ${Math.max(8, markerSize * 0.5)}px;">
                      <i class="fa-solid fa-circle"></i>
                    </div>`
    }

    // Create new icon with updated size
    const newIcon = L.divIcon({
      className: 'custom-waypoint-marker',
      html: markerHtml,
      iconSize: [markerSize, markerSize],
      iconAnchor: [halfSize, halfSize]
    })

    // Update the marker icon
    marker.setIcon(newIcon)
  })
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
    createMarker: (i: number, waypoint: L.Routing.Waypoint, n: number) => {
      // Create custom marker with better styling
      const isStart = i === 0
      const isEnd = i === n - 1
      const isIntermediate = !isStart && !isEnd

      // Calculate marker size based on zoom level
      const getMarkerSize = () => {
        const zoom = map?.getZoom() || 13
        // Scale from 12px at zoom 8 to 24px at zoom 18
        const baseSize = 12
        const maxSize = 24
        const minZoom = 8
        const maxZoom = 18
        const scale = Math.max(0, Math.min(1, (zoom - minZoom) / (maxZoom - minZoom)))
        return Math.round(baseSize + (maxSize - baseSize) * scale)
      }

      const markerSize = getMarkerSize()
      const halfSize = markerSize / 2

      let markerHtml = ''
      if (isStart) {
        // Orange start marker (more visible)
        markerHtml = `<div class="waypoint-marker waypoint-start" style="width: ${markerSize}px; height: ${markerSize}px; font-size: ${Math.max(8, markerSize * 0.5)}px;">
                        <i class="fa-solid fa-play"></i>
                      </div>`
      } else if (isEnd) {
        // Blue end marker
        markerHtml = `<div class="waypoint-marker waypoint-end" style="width: ${markerSize}px; height: ${markerSize}px; font-size: ${Math.max(8, markerSize * 0.5)}px;">
                        <i class="fa-solid fa-stop"></i>
                      </div>`
    } else {
        // Gray intermediate marker
        markerHtml = `<div class="waypoint-marker waypoint-intermediate" style="width: ${markerSize}px; height: ${markerSize}px; font-size: ${Math.max(8, markerSize * 0.5)}px;">
                        <i class="fa-solid fa-circle"></i>
                      </div>`
      }

      const marker = L.marker(waypoint.latLng, {
        draggable: true,
        icon: L.divIcon({
          className: 'custom-waypoint-marker',
          html: markerHtml,
          iconSize: [markerSize, markerSize],
          iconAnchor: [halfSize, halfSize]
        })
      })

      // Add drag events
      marker.on('dragend', () => {
        // Update waypoint position
        const newLatLng = marker.getLatLng()
        waypoints[i] = L.Routing.waypoint(newLatLng)
        if (routingControl) {
          routingControl.setWaypoints(waypoints)
        }
      })

      // Add click handler to remove waypoint (except start and end)
      marker.on('click', (e: any) => {
        e.originalEvent.stopPropagation()
        if (i > 0 && i < n - 1) {
          removeWaypoint(i)
        }
      })

      // Store marker reference
      waypointMarkers[i] = marker
      return marker
    },
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
      generateElevationProfile(route)

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
    console.log('Updating routing control with waypoints:', waypoints.length)
    routingControl.setWaypoints(waypoints)

    // Force route calculation if we have at least 2 waypoints
    if (waypoints.length >= 2) {
      console.log('Forcing route calculation...')
      // Trigger route calculation manually
      setTimeout(() => {
        try {
          routingControl.route()
        } catch (error) {
          console.log('Error triggering route calculation:', error)
        }
      }, 100)
    }
  } else {
    console.log('No routing control available')
  }
  // Clear marker array - it will be repopulated by the routing control
  waypointMarkers = []

  // Auto-center on the newly added waypoint (keeping current zoom level)
  // Only auto-center for appended waypoints, not inserted ones
  if (map) {
    map.setView([latlng.lat, latlng.lng], map.getZoom())
  }
}

function removeWaypoint(index: number) {
  if (waypoints.length > 2) { // Keep at least start and end
    waypoints.splice(index, 1)
    waypointMarkers.splice(index, 1) // Remove corresponding marker
    if (routingControl) {
      routingControl.setWaypoints(waypoints)
    }
  }
}

function clearRoute() {
  waypoints = []
  waypointMarkers = []
  if (routingControl) {
    routingControl.setWaypoints([])
  }
  // Remove route line
  if (routeLine) {
    map.removeLayer(routeLine)
    routeLine = null
  }
  routeInfo.value = null
  elevationProfile.value = []
  if (chart) {
    chart.destroy()
    chart = null
  }
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
    elevationProfile: elevationProfile.value,
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
  elevationProfile.value = routeData.elevationProfile

  if (elevationProfile.value.length > 0) {
    nextTick(() => {
      renderElevationChart()
    })
  }
}

function centerMap() {
  // Center map functionality disabled - user manages zoom manually
  console.log('Center map functionality disabled')
}

// Helper functions for clean mouse interaction logic
function findWaypointAtPosition(latlng: any): any {
  // Find if there's a waypoint marker at the given position
  for (let i = 0; i < waypointMarkers.length; i++) {
    const marker = waypointMarkers[i]
    if (marker && marker.getLatLng().distanceTo(latlng) < 20) { // 20 meter tolerance
      return marker
    }
  }
  return null
}

function updateWaypointPosition(marker: any, newLatLng: any): void {
  // Update the waypoint in the waypoints array
  const index = waypointMarkers.indexOf(marker)
  if (index !== -1) {
    waypoints[index] = L.Routing.waypoint(newLatLng)
  }
}

function triggerRouteRecomputation(): void {
  // Clear any pending updates
  if (routeUpdateTimeout) {
    clearTimeout(routeUpdateTimeout)
  }

  // Trigger route recomputation with stabilization
  routeUpdateTimeout = setTimeout(() => {
    if (routingControl) {
      routingControl.setWaypoints(waypoints)
    }
  }, 300)
}

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
    totalDuration: route.summary.totalTime / 60, // Convert to minutes
    totalElevation: calculateTotalElevation(route)
  }
}

function calculateTotalElevation(route: any): number {
  // This is a simplified calculation
  // In a real implementation, you'd need elevation data from the route
  return 0 // Placeholder
}

async function generateElevationProfile(route: any) {
  if (!route.coordinates || route.coordinates.length === 0) {
    elevationProfile.value = []
    return
  }

  try {
    // Get elevation data from OpenElevation API
    const coordinates = route.coordinates.map((coord: any) => ({
      latitude: coord[0],
      longitude: coord[1]
    }))

    // Sample coordinates for elevation (every 10th point to avoid too many requests)
    const sampledCoords = coordinates.filter((_: any, index: number) => index % 10 === 0)

    if (sampledCoords.length === 0) {
      elevationProfile.value = []
      return
    }

    const response = await fetch('https://api.open-elevation.com/api/v1/lookup', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        locations: sampledCoords
      })
    })

    if (!response.ok) {
      throw new Error('Failed to fetch elevation data')
    }

    const elevationData = await response.json()

    // Calculate cumulative distance and create elevation profile
    const profile = []
    let cumulativeDistance = 0

    for (let i = 0; i < elevationData.results.length; i++) {
      const result = elevationData.results[i]
      const coord = sampledCoords[i]

      if (i > 0) {
        const prevCoord = sampledCoords[i - 1]
        const distance = calculateDistance(
          prevCoord.latitude,
          prevCoord.longitude,
          coord.latitude,
          coord.longitude
        )
        cumulativeDistance += distance
      }

      profile.push({
        distance: cumulativeDistance,
        elevation: result.elevation || 0
      })
    }

    elevationProfile.value = profile

    if (elevationProfile.value.length > 0) {
      nextTick(() => {
    renderElevationChart()
      })
    }
  } catch (error) {
    console.warn('Failed to fetch elevation data:', error)
    // Fallback to empty profile
    elevationProfile.value = []
  }
}

function calculateDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371 // Earth's radius in km
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLon = (lon2 - lon1) * Math.PI / 180
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon/2) * Math.sin(dLon/2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
  return R * c
}

function renderElevationChart() {
  if (!elevationChart.value || elevationProfile.value.length === 0) return

  const ctx = elevationChart.value.getContext('2d')
  if (!ctx) return

  if (chart) {
    chart.destroy()
  }

  const distances = elevationProfile.value.map(point => point.distance)
  const elevations = elevationProfile.value.map(point => point.elevation)

  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: distances.map(d => `${d.toFixed(1)} km`),
      datasets: [{
        label: t('routePlanner.elevation'),
        data: elevations,
        borderColor: '#ff6600',
        backgroundColor: 'rgba(255, 102, 0, 0.1)',
        fill: true,
        tension: 0.1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          title: {
            display: true,
            text: t('routePlanner.distance')
          }
        },
        y: {
          title: {
            display: true,
            text: t('routePlanner.elevation')
          }
        }
      }
    }
  })
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

function formatElevation(meters: number): string {
  return `${Math.round(meters)} m`
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

.elevation-profile {
  height: 200px;
  background: white;
  border-top: 1px solid #e5e7eb;
  padding: 1rem;
}

.profile-header {
  margin-bottom: 1rem;
}

.profile-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
}

.profile-chart {
  height: 150px;
  position: relative;
}

.elevation-canvas {
  width: 100%;
  height: 100%;
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
