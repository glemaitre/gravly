<template>
  <div class="segment-detail">
    <!-- Header with back button and segment name -->
    <div class="detail-header">
      <div class="header-wrapper">
        <div class="header-left">
          <i
            class="fa-solid"
            :class="getTrackTypeIcon(segment?.track_type || 'segment')"
          ></i>
          <h1 class="segment-title">{{ segment?.name || 'Loading...' }}</h1>
        </div>
        <button @click="goBack" class="back-button">
          <i class="fa-solid fa-arrow-left"></i>
          {{ t('segmentDetail.backToTrackFinder') }}
        </button>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner">
        <i class="fa-solid fa-spinner fa-spin"></i>
        <span>Loading segment details...</span>
      </div>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="error-container">
      <div class="error-message">
        <i class="fa-solid fa-exclamation-triangle"></i>
        <span>{{ error }}</span>
      </div>
    </div>

    <!-- Main content -->
    <div v-else-if="segment && gpxData" class="detail-content">
      <div class="content-wrapper">
        <div class="content-grid" :class="{ 'with-comments': segment?.comments }">
          <!-- Map Section -->
          <div class="map-section">
            <div class="card map-card">
              <div class="card-header">
                <h3>
                  <i class="fa-solid fa-map"></i>
                  {{ t('segmentDetail.map') }}
                </h3>
              </div>
              <div class="card-content">
                <div id="detail-map" class="map"></div>
              </div>
            </div>
          </div>

          <!-- Elevation Chart Section -->
          <div class="chart-section">
            <div class="card chart-card">
              <div class="card-header">
                <h3>
                  <i class="fa-solid fa-chart-line"></i>
                  {{ t('segmentDetail.elevation') }}
                </h3>
              </div>
              <div class="card-content">
                <div class="chart-container">
                  <canvas ref="elevationChartRef" class="elevation-chart"></canvas>
                </div>
              </div>
            </div>
          </div>

          <!-- Segment Information Card -->
          <div class="info-section">
            <div class="card info-card">
              <div class="card-header">
                <h3>
                  <i class="fa-solid fa-info-circle"></i>
                  {{ t('segmentDetail.information') }}
                </h3>
              </div>
              <div class="card-content">
                <div class="info-grid">
                  <!-- Top Row: Difficulty, Surface, Tires -->
                  <div class="info-row">
                    <!-- Difficulty -->
                    <div class="info-item-compact">
                      <div class="info-label">
                        <i class="fa-solid fa-signal"></i>
                        {{ t('segmentDetail.difficulty') }}
                      </div>
                      <div class="info-value">
                        <div class="difficulty-display">
                          <span class="difficulty-level">{{
                            segment.difficulty_level || 0
                          }}</span>
                          <span class="difficulty-word">{{
                            getDifficultyWord(segment.difficulty_level || 0)
                          }}</span>
                          <span
                            v-if="(segment.difficulty_level || 0) > 5"
                            class="difficulty-over"
                            >{{ t('segmentDetail.over5') }}</span
                          >
                        </div>
                      </div>
                    </div>

                    <!-- Surface Type -->
                    <div class="info-item-compact">
                      <div class="info-label">
                        <i class="fa-solid fa-road"></i>
                        {{ t('segmentDetail.surface') }}
                      </div>
                      <div class="info-value">
                        <div class="surface-info-vertical">
                          <img
                            :src="getSurfaceImage(segment.surface_type)"
                            :alt="formatSurfaceType(segment.surface_type)"
                            class="surface-image"
                          />
                          <span class="surface-text">{{
                            formatSurfaceType(segment.surface_type)
                          }}</span>
                        </div>
                      </div>
                    </div>

                    <!-- Tire Recommendations -->
                    <div class="info-item-compact">
                      <div class="info-label">
                        <i class="fa-solid fa-circle"></i>
                        {{ t('segmentDetail.tireRecommendations') }}
                      </div>
                      <div class="info-value">
                        <div class="tire-recommendations-compact">
                          <div class="tire-recommendation-compact">
                            <div class="tire-header">
                              <i class="fa-solid fa-sun"></i>
                              <span class="tire-label">{{
                                t('segmentDetail.dry')
                              }}</span>
                            </div>
                            <div class="tire-option-vertical">
                              <img
                                :src="getTireImage(segment.tire_dry)"
                                :alt="formatTireType(segment.tire_dry)"
                                class="tire-image"
                              />
                              <span class="tire-text">{{
                                formatTireType(segment.tire_dry)
                              }}</span>
                            </div>
                          </div>
                          <div class="tire-recommendation-compact">
                            <div class="tire-header">
                              <i class="fa-solid fa-cloud-rain"></i>
                              <span class="tire-label">{{
                                t('segmentDetail.wet')
                              }}</span>
                            </div>
                            <div class="tire-option-vertical">
                              <img
                                :src="getTireImage(segment.tire_wet)"
                                :alt="formatTireType(segment.tire_wet)"
                                class="tire-image"
                              />
                              <span class="tire-text">{{
                                formatTireType(segment.tire_wet)
                              }}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Statistics -->
                  <div class="info-item">
                    <div class="info-value">
                      <div class="stats-grid">
                        <div class="stat-item">
                          <span class="stat-label">
                            <i class="fa-solid fa-route"></i>
                            {{ t('segmentDetail.distance') }}
                          </span>
                          <span class="stat-value">{{
                            formatDistance(gpxData.total_stats.total_distance)
                          }}</span>
                        </div>
                        <div class="stat-item">
                          <span class="stat-label">
                            <i class="fa-solid fa-arrow-trend-up"></i>
                            {{ t('segmentDetail.elevationGain') }}
                          </span>
                          <span class="stat-value">{{
                            formatElevation(gpxData.total_stats.total_elevation_gain)
                          }}</span>
                        </div>
                        <div class="stat-item">
                          <span class="stat-label">
                            <i class="fa-solid fa-arrow-trend-down"></i>
                            {{ t('segmentDetail.elevationLoss') }}
                          </span>
                          <span class="stat-value">{{
                            formatElevation(gpxData.total_stats.total_elevation_loss)
                          }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Comments Section - Only shown when comments are available -->
          <div v-if="segment?.comments" class="comments-section">
            <div class="card comments-card">
              <div class="card-header">
                <h3>
                  <i class="fa-solid fa-comments"></i>
                  {{ t('segmentDetail.comments') }}
                </h3>
              </div>
              <div class="card-content">
                <div class="comments-content">
                  <div class="comment-text">{{ segment.comments }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Media Section -->
          <div class="media-section">
            <div class="card media-card">
              <div class="card-header">
                <h3>
                  <i class="fa-solid fa-photo-film"></i>
                  Media
                </h3>
              </div>
              <div class="card-content">
                <div class="media-placeholder">
                  <div class="placeholder-content">
                    <i class="fa-solid fa-image"></i>
                    <h4>{{ t('segmentDetail.photosVideos') }}</h4>
                    <p>
                      This section will contain photos and YouTube videos related to
                      this segment.
                    </p>
                    <div class="placeholder-features">
                      <div class="feature-item">
                        <i class="fa-solid fa-camera"></i>
                        <span>{{ t('segmentDetail.photoGallery') }}</span>
                      </div>
                      <div class="feature-item">
                        <i class="fa-brands fa-youtube"></i>
                        <span>{{ t('segmentDetail.youtubeVideos') }}</span>
                      </div>
                      <div class="feature-item">
                        <i class="fa-solid fa-play"></i>
                        <span>{{ t('segmentDetail.videoPlayback') }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, onUnmounted, ref, nextTick, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import L from 'leaflet'
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
import annotationPlugin from 'chartjs-plugin-annotation'
import type { TrackResponse, GPXData } from '../types'

// Import images
import tireSlickUrl from '../assets/images/slick.png'
import tireSemiSlickUrl from '../assets/images/semi-slick.png'
import tireKnobsUrl from '../assets/images/ext.png'
import bigStoneRoadUrl from '../assets/images/big-stone-road.jpeg'
import brokenPavedRoadUrl from '../assets/images/broken-paved-road.jpeg'
import dirtyRoadUrl from '../assets/images/dirty-road.jpeg'
import fieldTrailUrl from '../assets/images/field-trail.jpeg'
import forestTrailUrl from '../assets/images/forest-trail.jpeg'
import smallStoneRoadUrl from '../assets/images/small-stone-road.jpeg'

Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Title,
  Filler,
  Tooltip,
  annotationPlugin
)

const router = useRouter()
const route = useRoute()

// i18n
const { t } = useI18n()

// Reactive data
const segment = ref<TrackResponse | null>(null)
const gpxData = ref<GPXData | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const map = ref<any>(null)
const elevationChart = ref<Chart | null>(null)
const elevationChartRef = ref<HTMLCanvasElement | null>(null)
const mapMarker = ref<any>(null)
const trackPolyline = ref<any>(null)

// Current position tracking for cursor sync
const currentPosition = ref({
  lat: 0,
  lng: 0,
  distance: 0,
  elevation: 0
})

// Image mappings
const tireImages = {
  slick: tireSlickUrl,
  'semi-slick': tireSemiSlickUrl,
  knobs: tireKnobsUrl
}

const surfaceImages = {
  'broken-paved-road': brokenPavedRoadUrl,
  'dirty-road': dirtyRoadUrl,
  'small-stone-road': smallStoneRoadUrl,
  'big-stone-road': bigStoneRoadUrl,
  'field-trail': fieldTrailUrl,
  'forest-trail': forestTrailUrl
}

// Computed properties
const segmentId = computed(() => route.params.id as string)

// Methods
function goBack() {
  router.push('/')
}

async function loadSegmentData() {
  if (!segmentId.value) {
    error.value = 'No segment ID provided'
    loading.value = false
    return
  }

  try {
    loading.value = true
    error.value = null

    // Load segment basic info
    const segmentResponse = await fetch(
      `http://localhost:8000/api/segments/${segmentId.value}`
    )
    if (!segmentResponse.ok) {
      throw new Error(`Failed to load segment: ${segmentResponse.statusText}`)
    }
    segment.value = await segmentResponse.json()

    // Load parsed GPX data directly from backend
    const gpxResponse = await fetch(
      `http://localhost:8000/api/segments/${segmentId.value}/data`
    )
    if (!gpxResponse.ok) {
      throw new Error(`Failed to load GPX data: ${gpxResponse.statusText}`)
    }
    gpxData.value = await gpxResponse.json()

    if (!gpxData.value) {
      throw new Error('Failed to load GPX data')
    }

    // Initialize map and chart after data is loaded
    await nextTick()
    if (segment.value && gpxData.value) {
      // Wait for DOM to be fully rendered with a small delay
      setTimeout(async () => {
        await initializeMap()
        await initializeElevationChart()
      }, 100)
    }
  } catch (err) {
    console.error('Error loading segment data:', err)
    error.value = err instanceof Error ? err.message : 'Unknown error occurred'
  } finally {
    loading.value = false
  }
}

async function initializeMap() {
  if (!segment.value || !gpxData.value) return

  // Check if map is already initialized
  if (map.value) {
    map.value.remove()
    map.value = null
  }

  // Check if map container exists
  const mapContainer = document.getElementById('detail-map')
  if (!mapContainer) {
    console.error('Map container not found')
    return
  }

  // Initialize map
  map.value = L.map('detail-map').setView(
    [segment.value.barycenter_latitude, segment.value.barycenter_longitude],
    13
  )

  // Add tile layer
  const apiKey = import.meta.env.THUNDERFOREST_API_KEY || 'demo'
  L.tileLayer(
    `https://{s}.tile.thunderforest.com/cycle/{z}/{x}/{y}.png?apikey=${apiKey}`,
    {
      attribution:
        'Maps © <a href="https://www.thunderforest.com/">Thunderforest</a>, Data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }
  ).addTo(map.value)

  // Add GPX track
  if (gpxData.value.points && gpxData.value.points.length > 0) {
    const trackPoints = gpxData.value.points.map((point) => [
      point.latitude,
      point.longitude
    ])
    trackPolyline.value = L.polyline(trackPoints, {
      color: '#ff6600',
      weight: 4,
      opacity: 0.8
    }).addTo(map.value)

    // Fit map to track bounds (safe call)
    if (map.value && map.value.fitBounds && trackPolyline.value) {
      map.value.fitBounds(trackPolyline.value.getBounds(), { padding: [20, 20] })
    }

    // Add click handler for cursor sync
    if (trackPolyline.value) {
      trackPolyline.value.on('click', (e: any) => {
        updateCursorPosition(e.latlng)
      })

      // Add mouse move handler for cursor sync
      trackPolyline.value.on('mousemove', (e: any) => {
        updateCursorPosition(e.latlng)
      })
    }

    // Create marker
    if (gpxData.value.points.length > 0) {
      const firstPoint = gpxData.value.points[0]
      if (map.value) {
        mapMarker.value = L.circleMarker([firstPoint.latitude, firstPoint.longitude], {
          radius: 8,
          fillColor: '#ff6600',
          color: '#ffffff',
          weight: 3,
          opacity: 1,
          fillOpacity: 0.8
        }).addTo(map.value)
      }
    }
  }

  // Set initial position
  if (gpxData.value.points.length > 0) {
    const firstPoint = gpxData.value.points[0]
    currentPosition.value = {
      lat: firstPoint.latitude,
      lng: firstPoint.longitude,
      distance: 0,
      elevation: firstPoint.elevation
    }
  }
}

async function initializeElevationChart() {
  // Only show debug logs in production/development, not during tests
  // Check if we're in a test environment by checking for the vi mock object
  const isTestEnv = (() => {
    try {
      return typeof (globalThis as any).vi !== 'undefined'
    } catch {
      return false
    }
  })()

  if (!isTestEnv) {
    console.log('Initializing elevation chart...')
    console.log('gpxData.value:', gpxData.value)
    console.log('elevationChartRef.value:', elevationChartRef.value)
  }

  if (!gpxData.value || !elevationChartRef.value) {
    if (!isTestEnv) {
      console.log('Missing required data for chart initialization')
    }
    return
  }

  // Check if chart is already initialized
  if (elevationChart.value) {
    if (!isTestEnv) {
      console.log('Destroying existing chart')
    }
    elevationChart.value.destroy()
    elevationChart.value = null
  }

  // Check if chart canvas exists
  if (!elevationChartRef.value) {
    console.error('Chart canvas not found')
    return
  }

  // Ensure canvas has proper dimensions
  const canvas = elevationChartRef.value
  const container = canvas.parentElement
  if (container) {
    canvas.width = container.clientWidth
    canvas.height = container.clientHeight
    if (!isTestEnv) {
      console.log('Canvas dimensions set:', canvas.width, 'x', canvas.height)
    }
  }

  const points = gpxData.value.points
  if (points.length === 0) {
    if (!isTestEnv) {
      console.log('No points data available for chart')
    }
    return
  }

  if (!isTestEnv) {
    console.log('Points data:', points.length, 'points')
    console.log('First few points:', points.slice(0, 3))
  }

  // Calculate cumulative distances in kilometers
  const cumulativeKm: number[] = [0]
  let cumulativeDistance = 0

  for (let i = 1; i < points.length; i++) {
    const distance = calculateDistance(
      points[i - 1].latitude,
      points[i - 1].longitude,
      points[i].latitude,
      points[i].longitude
    )
    cumulativeDistance += distance
    cumulativeKm.push(cumulativeDistance / 1000) // Convert to kilometers
  }

  // Prepare chart data with x,y coordinates
  const chartData = points.map((point, i) => ({
    x: cumulativeKm[i],
    y: point.elevation
  }))

  if (!isTestEnv) {
    console.log('Chart data sample:', chartData.slice(0, 5))
    console.log(
      'Elevation range:',
      Math.min(...points.map((p) => p.elevation)),
      'to',
      Math.max(...points.map((p) => p.elevation))
    )
    console.log('Distance range:', 0, 'to', cumulativeKm[cumulativeKm.length - 1])
    // Create chart
    console.log('Creating chart with data points:', chartData.length)
  }
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
          max: cumulativeKm[cumulativeKm.length - 1],
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
          min: Math.min(...points.map((p) => p.elevation))
        }
      },
      onHover: (event, activeElements) => {
        if (activeElements.length > 0) {
          const pointIndex = activeElements[0].index
          updateCursorPositionFromChart(pointIndex)
        }
      }
    }
  })

  if (!isTestEnv) {
    console.log('Chart created successfully:', elevationChart.value)
  }
}

function updateCursorPosition(latlng: any) {
  if (!gpxData.value) return

  // Find closest point
  let closestPoint = gpxData.value.points[0]
  let minDistance = Infinity
  let closestIndex = 0

  for (let i = 0; i < gpxData.value.points.length; i++) {
    const point = gpxData.value.points[i]
    const distance = calculateDistance(
      latlng.lat,
      latlng.lng,
      point.latitude,
      point.longitude
    )
    if (distance < minDistance) {
      minDistance = distance
      closestPoint = point
      closestIndex = i
    }
  }

  // Calculate cumulative distance to this point
  let cumulativeDistance = 0
  for (let i = 1; i <= closestIndex; i++) {
    const prevPoint = gpxData.value.points[i - 1]
    const currPoint = gpxData.value.points[i]
    cumulativeDistance += calculateDistance(
      prevPoint.latitude,
      prevPoint.longitude,
      currPoint.latitude,
      currPoint.longitude
    )
  }
  // Convert to kilometers
  cumulativeDistance = cumulativeDistance / 1000

  // Update current position
  currentPosition.value = {
    lat: closestPoint.latitude,
    lng: closestPoint.longitude,
    distance: cumulativeDistance,
    elevation: closestPoint.elevation
  }

  // Update marker position with animation
  if (mapMarker.value) {
    mapMarker.value.setLatLng([closestPoint.latitude, closestPoint.longitude])
  }
}

function updateCursorPositionFromChart(pointIndex: number) {
  if (!gpxData.value || pointIndex < 0 || pointIndex >= gpxData.value.points.length)
    return

  const point = gpxData.value.points[pointIndex]

  // Calculate cumulative distance to this point
  let cumulativeDistance = 0
  for (let i = 1; i <= pointIndex; i++) {
    const prevPoint = gpxData.value.points[i - 1]
    const currPoint = gpxData.value.points[i]
    cumulativeDistance += calculateDistance(
      prevPoint.latitude,
      prevPoint.longitude,
      currPoint.latitude,
      currPoint.longitude
    )
  }
  // Convert to kilometers
  cumulativeDistance = cumulativeDistance / 1000

  // Update current position
  currentPosition.value = {
    lat: point.latitude,
    lng: point.longitude,
    distance: cumulativeDistance,
    elevation: point.elevation
  }

  // Update marker position with animation
  if (mapMarker.value) {
    mapMarker.value.setLatLng([point.latitude, point.longitude])
  }
}

// Utility functions
function calculateDistance(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371000 // Earth's radius in meters
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLon = ((lon2 - lon1) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

function formatDistance(kilometers: number): string {
  return `${kilometers.toFixed(2)} km`
}

function formatElevation(meters: number): string {
  return `${Math.round(meters)}m`
}

function formatSurfaceType(surfaceType: string): string {
  if (!surfaceType) return ''
  return (
    t(`surface.${surfaceType}`) ||
    surfaceType.replace(/-/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
  )
}

function formatTireType(tireType: string): string {
  if (!tireType) return ''

  // Map kebab-case to camelCase for translation keys
  const tireTypeMap: { [key: string]: string } = {
    'semi-slick': 'semiSlick'
  }

  const translationKey = tireTypeMap[tireType] || tireType
  return (
    t(`tire.${translationKey}`) ||
    tireType.replace(/-/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
  )
}

function getTireImage(tireType: string): string {
  return tireImages[tireType as keyof typeof tireImages] || tireSlickUrl
}

function getSurfaceImage(surfaceType: string): string {
  return surfaceImages[surfaceType as keyof typeof surfaceImages] || brokenPavedRoadUrl
}

function getDifficultyWord(level: number): string {
  const difficultyWords = {
    1: t('difficulty.level1'),
    2: t('difficulty.level2'),
    3: t('difficulty.level3'),
    4: t('difficulty.level4'),
    5: t('difficulty.level5')
  }
  return difficultyWords[level as keyof typeof difficultyWords] || 'Unknown'
}

function getTrackTypeIcon(trackType: string): string {
  switch (trackType) {
    case 'segment':
      return 'fa-route'
    case 'route':
      return 'fa-map'
    default:
      return 'fa-route'
  }
}

// Lifecycle
onMounted(() => {
  loadSegmentData()
})

onUnmounted(() => {
  if (map.value) {
    map.value.remove()
  }
  if (elevationChart.value) {
    elevationChart.value.destroy()
  }
  if (mapMarker.value) {
    mapMarker.value.remove()
  }
})
</script>

<style scoped>
.segment-detail {
  height: calc(100vh - var(--navbar-height, 60px));
  background: #f8fafc;
  padding: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* Desktop: no overflow, content fits in viewport */
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem 2rem;
  height: var(--navbar-height, 60px);
  flex-shrink: 0;
}

.header-wrapper {
  max-width: 1200px;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.header-left i {
  font-size: 1.5rem;
  color: #ff6600;
}

.back-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  color: #374151;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s;
  cursor: pointer;
}

.back-button:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

/* Hide text on small screens, show only icon */
@media (max-width: 850px) {
  .back-button {
    padding: 0.75rem;
    min-width: auto;
    gap: 0; /* Remove gap between icon and text */
  }

  .back-button i {
    margin: 0;
  }

  /* Hide the text content but keep the icon */
  .back-button {
    font-size: 0; /* Hide all text */
  }

  .back-button i {
    font-size: 1rem; /* Restore icon size */
  }
}

.segment-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: #111827;
}

.loading-container,
.error-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.loading-spinner,
.error-message {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.loading-spinner i {
  font-size: 1.5rem;
  color: #ff6600;
}

.error-message i {
  font-size: 1.5rem;
  color: #ef4444;
}

.detail-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 1rem;
  box-sizing: border-box;
  overflow-y: auto;
}

.content-wrapper {
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 33% 33% 34%;
  gap: 1rem;
  flex: 1;
  grid-template-areas:
    'map info'
    'elevation elevation'
    'media media';
}

/* Dynamic grid layout when comments are present */
.content-grid.with-comments {
  grid-template-rows: 25% 25% 25% 25%;
  grid-template-areas:
    'map info'
    'elevation elevation'
    'comments comments'
    'media media';
}

.map-section {
  grid-area: map;
}

.chart-section {
  grid-area: elevation;
}

.info-section {
  grid-area: info;
}

.comments-section {
  grid-area: comments;
}

.media-section {
  grid-area: media;
}

/* Responsive layout adjustments */
@media (max-width: 768px) {
  .segment-detail {
    overflow-y: auto; /* Enable vertical scrolling on small devices */
  }

  .content-grid {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(300px, auto) auto auto auto;
    grid-template-areas:
      'map'
      'info'
      'elevation'
      'media';
    gap: 1.5rem; /* Increase gap for better spacing when stacked */
  }

  .content-grid.with-comments {
    grid-template-rows: minmax(300px, auto) auto auto auto auto;
    grid-template-areas:
      'map'
      'info'
      'elevation'
      'comments'
      'media';
  }

  .content-wrapper {
    padding: 0 0.5rem;
  }

  .detail-content {
    padding: 0.5rem;
    overflow-y: visible; /* Allow content to overflow and scroll */
  }

  .detail-header {
    padding: 1rem;
  }

  .header-wrapper {
    padding: 0 0.5rem;
  }

  .map-section {
    min-height: 300px;
  }

  .map-section .map {
    min-height: 300px;
    aspect-ratio: 1;
  }
}

@media (max-width: 480px) {
  .segment-detail {
    overflow-y: auto; /* Ensure scrolling on very small devices too */
  }

  .content-grid {
    gap: 1rem; /* Slightly smaller gap on very small screens */
  }

  .content-wrapper {
    padding: 0 0.25rem;
  }

  .detail-content {
    padding: 0.25rem;
    overflow-y: visible;
  }

  .detail-header {
    padding: 0.75rem;
  }

  .header-wrapper {
    padding: 0 0.25rem;
  }

  .map-section {
    min-height: 250px;
  }

  .map-section .map {
    min-height: 250px;
    aspect-ratio: 1;
  }

  .info-row {
    flex-direction: column;
    gap: 0.75rem;
  }

  .tire-recommendations-compact {
    flex-direction: column;
    gap: 0.75rem;
  }
}

.map-section .card-content {
  padding: 0;
}

.map-section .card-content .map {
  border-radius: 12px;
  flex: 1;
}

.card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-header {
  padding: 0.75rem 1.5rem;
  border-bottom: 1px solid #f1f5f9;
  background: #fafbfc;
}

.card-header h3 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
}

.card-header i {
  color: #ff6600;
}

.card-content {
  padding: 1.5rem;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.map {
  height: 100%;
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  flex: 1;
  min-height: 200px; /* Fallback minimum height */
}

.map-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1; /* Take remaining space in info-grid */
}

.info-row {
  display: flex;
  gap: 0.5rem;
  flex: 0 0 auto; /* Don't grow or shrink, maintain natural size */
}

.info-item-compact:nth-child(1) {
  flex: 1;
}

.info-item-compact:nth-child(2) {
  flex: 1;
}

.info-item-compact:nth-child(3) {
  flex: 2;
}

.info-item-compact {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.5rem;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.info-item-compact .info-value {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
}

.info-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.info-label i {
  color: #ff6600;
}

.info-value {
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
}

.chart-container {
  height: 100%;
  position: relative;
  flex: 1;
}

.elevation-chart {
  width: 100% !important;
  height: 100% !important;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  height: 100%;
  justify-content: space-between;
}

.difficulty-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.difficulty-display i {
  color: #ff6600;
}

.difficulty-level {
  font-size: 1.5rem;
  font-weight: 700;
  color: #ff6600;
}

.difficulty-word {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  text-align: center;
}

.difficulty-over {
  font-size: 0.75rem;
  font-weight: 400;
  color: #6b7280;
  text-align: center;
}

.surface-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.surface-info-vertical {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.surface-image {
  width: 3rem;
  height: 3rem;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.surface-text {
  font-weight: 500;
  color: #111827;
  text-align: center;
}

.tire-recommendations {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.tire-recommendation {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.tire-recommendation i {
  font-size: 1.25rem;
  color: #ff6600;
  width: 1.5rem;
  text-align: center;
}

.tire-label {
  font-weight: 500;
  color: #374151;
  min-width: 120px;
}

.tire-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.tire-option-vertical {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.tire-image {
  width: 2rem;
  height: 2rem;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid #d1d5db;
}

.tire-text {
  font-weight: 500;
  color: #111827;
  text-align: center;
}

.tire-recommendations-compact {
  display: flex;
  gap: 1rem;
  width: 100%;
}

.tire-recommendation-compact {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  width: 100%;
}

.tire-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.tire-header i {
  font-size: 1rem;
  color: #ff6600;
  width: 1rem;
  text-align: center;
}

.tire-header i.fa-cloud-rain {
  color: #3b82f6;
}

.tire-header .tire-label {
  font-weight: 600;
  color: #374151;
  font-size: 0.875rem;
  min-width: auto;
}

.stats-grid {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  flex: 1;
  align-items: stretch;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  align-items: center;
  justify-content: center;
  flex: 1;
  padding: 0.5rem;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  min-height: 60px;
}

.stat-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: #6b7280;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
}

.stat-label i {
  font-size: 0.625rem;
  color: #ff6600;
}

.stat-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #111827;
  text-align: center;
}

.media-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  background: #f8fafc;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
}

.placeholder-content {
  text-align: center;
  color: #6b7280;
}

.placeholder-content i {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: #d1d5db;
}

.placeholder-content h4 {
  margin: 0 0 0.5rem 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #374151;
}

.placeholder-content p {
  margin: 0 0 1.5rem 0;
  font-size: 0.875rem;
}

.placeholder-features {
  display: flex;
  justify-content: center;
  gap: 2rem;
  flex-wrap: wrap;
}

.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.feature-item i {
  font-size: 1.5rem;
  color: #d1d5db;
}

/* Comments Section Styles */
.comments-content {
  padding: 1rem;
}

.comment-text {
  font-size: 1rem;
  line-height: 1.6;
  color: #374151;
  background: #f8fafc;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  white-space: pre-wrap; /* Preserve line breaks and format text */
}
</style>
