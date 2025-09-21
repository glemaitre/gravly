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
              :class="{ active: isPlanningMode }"
              @click="togglePlanningMode"
              :title="t('routePlanner.togglePlanning')"
            >
              <i class="fa-solid fa-mouse-pointer"></i>
            </button>
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
let map: L.Map | null = null
let routingControl: L.Routing.Control | null = null
let waypoints: L.Routing.Waypoint[] = []
let isPlanningMode = ref(true)
let isDragging = ref(false)

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

  // Initialize routing control
  initializeRoutingControl()

  // Add click handler for adding waypoints
  map.on('click', (e: L.LeafletMouseEvent) => {
    if (isPlanningMode.value && !isDragging.value) {
      addWaypoint(e.latlng)
    }
  })

  // Add mouse events for better UX
  map.on('mousedown', () => {
    isDragging.value = true
  })

  map.on('mouseup', () => {
    setTimeout(() => {
      isDragging.value = false
    }, 100)
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
    routeWhileDragging: true,
    addWaypoints: true,
    createMarker: (i: number, waypoint: L.Routing.Waypoint, n: number) => {
      // Create custom marker with better styling
      const marker = L.marker(waypoint.latLng, {
        draggable: true,
        icon: L.divIcon({
          className: 'custom-waypoint-marker',
          html: `<div class="waypoint-marker waypoint-${i === 0 ? 'start' : i === n - 1 ? 'end' : 'waypoint'}">
                   <span class="waypoint-number">${i + 1}</span>
                 </div>`,
          iconSize: [30, 30],
          iconAnchor: [15, 15]
        })
      })

      // Add drag events
      marker.on('dragstart', () => {
        isDragging.value = true
      })

      marker.on('dragend', () => {
        isDragging.value = false
        // Update waypoint position
        const newLatLng = marker.getLatLng()
        waypoints[i] = L.Routing.waypoint(newLatLng)
        if (routingControl) {
          routingControl.setWaypoints(waypoints)
        }
      })

      // Add click handler to remove waypoint (except start and end)
      marker.on('click', (e) => {
        e.originalEvent.stopPropagation()
        if (i > 0 && i < n - 1) {
          removeWaypoint(i)
        }
      })

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
  routingControl.on('routesfound', (e) => {
    const routes = e.routes
    if (routes && routes.length > 0) {
      const route = routes[0]
      updateRouteInfo(route)
      generateElevationProfile(route)
    }
  })

  // Listen for waypoint changes
  routingControl.on('waypointsspliced', (e) => {
    waypoints = e.waypoints
  })
}

function addWaypoint(latlng: L.LatLng) {
  const newWaypoint = L.Routing.waypoint(latlng)
  waypoints.push(newWaypoint)
  if (routingControl) {
    routingControl.setWaypoints(waypoints)
  }
}

function removeWaypoint(index: number) {
  if (waypoints.length > 2) { // Keep at least start and end
    waypoints.splice(index, 1)
    if (routingControl) {
      routingControl.setWaypoints(waypoints)
    }
  }
}

function clearRoute() {
  waypoints = []
  if (routingControl) {
    routingControl.setWaypoints([])
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

function togglePlanningMode() {
  isPlanningMode.value = !isPlanningMode.value
}

function centerMap() {
  if (map && waypoints.length > 0) {
    const group = new L.featureGroup(waypoints.map(wp => L.marker(wp.latLng)))
    map.fitBounds(group.getBounds().pad(0.1))
  }
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

/* Custom waypoint markers */
:global(.custom-waypoint-marker) {
  background: transparent;
  border: none;
}

:global(.waypoint-marker) {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 12px;
  color: white;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  transition: all 0.2s ease;
}

:global(.waypoint-marker:hover) {
  transform: scale(1.1);
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.4);
}

:global(.waypoint-start) {
  background: #22c55e;
  border: 3px solid white;
}

:global(.waypoint-end) {
  background: #ef4444;
  border: 3px solid white;
}

:global(.waypoint-waypoint) {
  background: #ff6600;
  border: 3px solid white;
}

:global(.waypoint-number) {
  font-size: 11px;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}
</style>
