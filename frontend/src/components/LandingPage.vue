<template>
  <div class="landing-page">
    <div class="landing-content">
      <!-- Empty content for now -->
      <div class="map-section">
        <div class="map-container">
          <div class="card card-map">
            <div id="landing-map" class="map"></div>
            <div class="loading-indicator" :class="{ show: loading }">
              🔍 Searching segments...
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
import type { TrackWithGPXDataResponse } from '../types'

// Map instance
let map: any = null

// Segments data from API
const segments = ref<TrackWithGPXDataResponse[]>([])
const loading = ref(false)

// Sample cycling route data for demonstration (fallback)
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

  // Search for segments when map view changes
  searchSegmentsInView()

  // Add event listeners for map movement
  map.on('moveend', searchSegmentsInView)
  map.on('zoomend', searchSegmentsInView)
}

// Search for segments within current map bounds
async function searchSegmentsInView() {
  if (!map) return

  loading.value = true

  try {
    const bounds = map.getBounds()
    const params = new URLSearchParams({
      north: bounds.getNorth().toString(),
      south: bounds.getSouth().toString(),
      east: bounds.getEast().toString(),
      west: bounds.getWest().toString(),
      limit: '50'
    })

    const response = await fetch(`/api/segments/search?${params}`)
    if (!response.ok) {
      throw new Error(`Search failed: ${response.status}`)
    }

    const data: TrackWithGPXDataResponse[] = await response.json()
    segments.value = data

    // Clear existing segment layers from map
    map.eachLayer((layer: any) => {
      if (layer instanceof L.Rectangle || layer instanceof L.Polyline) {
        map.removeLayer(layer)
      }
    })

    // Add segments to map
    data.forEach((segment: TrackWithGPXDataResponse) => {
      if (segment.gpx_data && segment.gpx_data.points.length > 0) {
        // Display actual GPS track
        addGPXTrackToMap(segment)
      } else {
        // Fallback to bounding box if no GPX data
        addBoundingBoxToMap(segment)
      }
    })
  } catch (error) {
    console.error('Search failed:', error)
  } finally {
    loading.value = false
  }
}

// Get color based on surface type
function getSurfaceColor(surfaceType: string): string {
  const colors: Record<string, string> = {
    'forest-trail': '#228B22',
    'dirty-road': '#8B4513',
    'broken-paved-road': '#696969',
    'big-stone-road': '#A9A9A9',
    'small-stone-road': '#D3D3D3',
    'field-trail': '#9ACD32'
  }
  return colors[surfaceType] || '#FF6600'
}

// Add GPX track to map
function addGPXTrackToMap(segment: TrackWithGPXDataResponse) {
  if (!segment.gpx_data || !segment.gpx_data.points.length) return

  // Convert GPX points to Leaflet lat/lng format
  const trackPoints = segment.gpx_data.points.map((point) => [
    point.latitude,
    point.longitude
  ])

  // Create polyline for the track
  const polyline = L.polyline(trackPoints, {
    color: getSurfaceColor(segment.surface_type),
    weight: 3,
    opacity: 0.8,
    className: 'gpx-track'
  }).addTo(map)

  // Add popup with detailed segment info
  const popupContent = `
    <div class="segment-popup">
      <h3>${segment.name}</h3>
      <p><strong>Surface:</strong> ${segment.surface_type}</p>
      <p><strong>Difficulty:</strong> ${segment.difficulty_level}/10</p>
      <p><strong>Type:</strong> ${segment.track_type}</p>
      <p><strong>Distance:</strong> ${(segment.gpx_data.total_stats.total_distance / 1000).toFixed(2)} km</p>
      <p><strong>Elevation Gain:</strong> ${segment.gpx_data.total_stats.total_elevation_gain.toFixed(0)} m</p>
      <p><strong>Points:</strong> ${segment.gpx_data.total_stats.total_points}</p>
    </div>
  `
  polyline.bindPopup(popupContent)
}

// Add bounding box to map (fallback when no GPX data)
function addBoundingBoxToMap(segment: TrackWithGPXDataResponse) {
  const segmentBounds = L.latLngBounds(
    [segment.bound_south, segment.bound_west],
    [segment.bound_north, segment.bound_east]
  )

  const rectangle = L.rectangle(segmentBounds, {
    color: getSurfaceColor(segment.surface_type),
    weight: 2,
    fillOpacity: 0.1,
    className: 'segment-rectangle'
  }).addTo(map)

  // Add popup with segment info
  rectangle.bindPopup(`
    <div class="segment-popup">
      <h3>${segment.name}</h3>
      <p><strong>Surface:</strong> ${segment.surface_type}</p>
      <p><strong>Difficulty:</strong> ${segment.difficulty_level}/10</p>
      <p><strong>Type:</strong> ${segment.track_type}</p>
      <p><em>GPX data not available</em></p>
    </div>
  `)
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
