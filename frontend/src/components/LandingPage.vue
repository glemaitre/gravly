<template>
  <div class="landing-page">
    <div class="landing-content">
      <!-- Empty content for now -->
      <div class="map-section">
        <div class="map-container">
          <div class="card card-map">
            <div id="landing-map" class="map"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, onUnmounted } from 'vue'
import L from 'leaflet'

// Map instance
let map: any = null

// Sample cycling route data for demonstration
const sampleRoute = [
  { lat: 45.764, lng: 4.8357 }, // Lyon, France
  { lat: 45.75, lng: 4.85 },
  { lat: 45.76, lng: 4.86 },
  { lat: 45.77, lng: 4.87 },
  { lat: 45.78, lng: 4.88 },
  { lat: 45.79, lng: 4.89 },
  { lat: 45.8, lng: 4.9 },
  { lat: 45.81, lng: 4.91 },
  { lat: 45.82, lng: 4.92 },
  { lat: 45.83, lng: 4.93 }
]

function initializeMap() {
  if (map) return

  const container = document.getElementById('landing-map')
  if (!container) return

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

  // Add sample cycling route
  L.polyline(sampleRoute, {
    color: '#ff6600',
    weight: 4,
    opacity: 0.8,
    smoothFactor: 1
  }).addTo(map)

  // Add start and end markers
  const startIcon = L.divIcon({
    className: 'custom-div-icon',
    html: '<div class="marker-icon start-marker">🚴</div>',
    iconSize: [30, 30],
    iconAnchor: [15, 15]
  })

  const endIcon = L.divIcon({
    className: 'custom-div-icon',
    html: '<div class="marker-icon end-marker">🏁</div>',
    iconSize: [30, 30],
    iconAnchor: [15, 15]
  })

  L.marker(sampleRoute[0], { icon: startIcon }).addTo(map)
  L.marker(sampleRoute[sampleRoute.length - 1], { icon: endIcon }).addTo(map)

  // Fit map to route bounds
  const bounds = L.latLngBounds(sampleRoute)
  map.fitBounds(bounds, { padding: [20, 20] })

  // Add scale control
  L.control
    .scale({
      position: 'bottomright',
      metric: true,
      imperial: false
    })
    .addTo(map)
}

function cleanupMap() {
  if (map) {
    map.remove()
    map = null
  }
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
  background: #10b981;
  color: white;
}

:global(.end-marker) {
  background: #ef4444;
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
</style>
