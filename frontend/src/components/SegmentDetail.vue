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
        <div
          class="content-grid"
          :class="{
            'with-comments': segment?.comments,
            'with-images': trackImages && trackImages.length > 0,
            'with-videos': trackVideos && trackVideos.length > 0
          }"
        >
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

          <!-- Images Gallery Section - Only shown when images are available -->
          <div v-if="trackImages && trackImages.length > 0" class="images-section">
            <div class="card images-card">
              <div class="card-header">
                <h3>
                  <i class="fa-solid fa-images"></i>
                  {{ t('segmentDetail.images') }}
                </h3>
              </div>
              <div class="card-content">
                <div class="images-carousel">
                  <button
                    v-if="canScrollImagesLeft"
                    @click="scrollImagesLeft"
                    class="carousel-btn carousel-btn-left"
                  >
                    <i class="fa-solid fa-chevron-left"></i>
                  </button>

                  <div class="images-gallery">
                    <div
                      v-for="image in visibleImages"
                      :key="image.id"
                      class="gallery-item"
                      @click="openImageModal(image)"
                    >
                      <img
                        :src="image.image_url"
                        :alt="image.original_filename || 'Segment image'"
                        class="gallery-image"
                        loading="lazy"
                      />
                      <div class="gallery-overlay">
                        <i class="fa-solid fa-expand"></i>
                      </div>
                    </div>
                  </div>

                  <button
                    v-if="canScrollImagesRight"
                    @click="scrollImagesRight"
                    class="carousel-btn carousel-btn-right"
                  >
                    <i class="fa-solid fa-chevron-right"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Videos Gallery Section - Only shown when videos are available -->
          <div v-if="trackVideos && trackVideos.length > 0" class="videos-section">
            <div class="card videos-card">
              <div class="card-header">
                <h3>
                  <i class="fa-solid fa-video"></i>
                  {{ t('segmentDetail.videos') }}
                </h3>
              </div>
              <div class="card-content">
                <div class="videos-carousel">
                  <!-- Carousel Navigation Buttons -->
                  <button
                    v-if="canScrollVideosLeft"
                    @click="scrollVideosLeft"
                    class="carousel-btn carousel-btn-left"
                    :title="t('pagination.previous')"
                  >
                    <i class="fa-solid fa-chevron-left"></i>
                  </button>

                  <button
                    v-if="canScrollVideosRight"
                    @click="scrollVideosRight"
                    class="carousel-btn carousel-btn-right"
                    :title="t('pagination.next')"
                  >
                    <i class="fa-solid fa-chevron-right"></i>
                  </button>

                  <!-- Videos Gallery -->
                  <div class="videos-gallery">
                    <div
                      v-for="video in visibleVideos"
                      :key="video.id"
                      class="video-item"
                    >
                      <div class="video-embed">
                        <iframe
                          v-if="video.platform === 'youtube'"
                          :src="getYouTubeEmbedUrl(video.video_url)"
                          frameborder="0"
                          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                          allowfullscreen
                          class="video-iframe"
                        ></iframe>
                        <iframe
                          v-else-if="video.platform === 'vimeo'"
                          :src="getVimeoEmbedUrl(video.video_url)"
                          frameborder="0"
                          allow="autoplay; fullscreen; picture-in-picture"
                          allowfullscreen
                          class="video-iframe"
                        ></iframe>
                        <div v-else class="video-placeholder">
                          <i class="fa-solid fa-video"></i>
                          <p>Video</p>
                          <a :href="video.video_url" target="_blank" class="video-link">
                            {{ t('segmentDetail.openVideo') }}
                          </a>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Videos Pagination -->
                <div v-if="totalVideosPages > 1" class="pagination">
                  <div class="pagination-controls">
                    <button
                      @click="previousVideosPage"
                      :disabled="currentVideosPage === 1"
                      class="pagination-btn"
                    >
                      <i class="fa-solid fa-chevron-left"></i>
                      {{ t('pagination.previous') }}
                    </button>

                    <div class="pagination-pages">
                      <button
                        v-for="page in totalVideosPages"
                        :key="page"
                        @click="goToVideosPage(page)"
                        :class="[
                          'pagination-page',
                          { active: page === currentVideosPage }
                        ]"
                      >
                        {{ page }}
                      </button>
                    </div>

                    <button
                      @click="nextVideosPage"
                      :disabled="currentVideosPage === totalVideosPages"
                      class="pagination-btn"
                    >
                      {{ t('pagination.next') }}
                      <i class="fa-solid fa-chevron-right"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Image Modal -->
    <div v-if="selectedImage" class="image-modal" @click="closeImageModal">
      <div class="modal-content" @click.stop>
        <button class="modal-close" @click="closeImageModal">
          <i class="fa-solid fa-times"></i>
        </button>

        <!-- Modal Navigation -->
        <button
          v-if="currentModalImageIndex > 0"
          @click="previousModalImage"
          class="modal-nav-btn modal-nav-left"
        >
          <i class="fa-solid fa-chevron-left"></i>
        </button>

        <button
          v-if="currentModalImageIndex < trackImages.length - 1"
          @click="nextModalImage"
          class="modal-nav-btn modal-nav-right"
        >
          <i class="fa-solid fa-chevron-right"></i>
        </button>

        <div class="modal-image-container">
          <img
            :src="currentModalImage?.image_url"
            :alt="currentModalImage?.original_filename || 'Segment image'"
            class="modal-image"
          />
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
import type { TrackResponse, GPXData, TrackVideoResponse } from '../types'

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
const trackImages = ref<any[]>([])
const trackVideos = ref<TrackVideoResponse[]>([])
const selectedImage = ref<any>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const map = ref<any>(null)
const elevationChart = ref<Chart | null>(null)
const elevationChartRef = ref<HTMLCanvasElement | null>(null)
const mapMarker = ref<any>(null)
const trackPolyline = ref<any>(null)

// Carousel state
const imagesPerView = ref(4) // Number of images visible at once
const videosPerPage = ref(3) // Number of videos per page (dynamic)
const videosPerView = ref(3) // Number of videos visible at once in current page
const currentImagesStart = ref(0) // Starting index for visible images
const currentVideosPage = ref(1)
const currentVideosStart = ref(0) // Starting index for visible videos in current page
const currentModalImageIndex = ref(0) // Index of currently viewed image in modal

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

// Carousel computed properties
const visibleImages = computed(() => {
  const end = Math.min(
    currentImagesStart.value + imagesPerView.value,
    trackImages.value.length
  )
  return trackImages.value.slice(currentImagesStart.value, end)
})

const canScrollImagesLeft = computed(() => currentImagesStart.value > 0)
const canScrollImagesRight = computed(
  () => currentImagesStart.value + imagesPerView.value < trackImages.value.length
)

const totalVideosPages = computed(() =>
  Math.ceil(trackVideos.value.length / videosPerPage.value)
)

const paginatedVideos = computed(() => {
  const start = (currentVideosPage.value - 1) * videosPerPage.value
  const end = start + videosPerPage.value
  return trackVideos.value.slice(start, end)
})

const visibleVideos = computed(() => {
  const end = Math.min(
    currentVideosStart.value + videosPerView.value,
    paginatedVideos.value.length
  )
  return paginatedVideos.value.slice(currentVideosStart.value, end)
})

const canScrollVideosLeft = computed(() => currentVideosStart.value > 0)
const canScrollVideosRight = computed(() => {
  return currentVideosStart.value + videosPerView.value < paginatedVideos.value.length
})

const currentModalImage = computed(
  () => trackImages.value[currentModalImageIndex.value]
)

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

    // Load track images
    const imagesResponse = await fetch(
      `http://localhost:8000/api/segments/${segmentId.value}/images`
    )
    if (imagesResponse.ok) {
      trackImages.value = await imagesResponse.json()
    } else {
      // Images are optional, so don't throw error if they fail to load
      console.warn('Failed to load track images:', imagesResponse.statusText)
      trackImages.value = []
    }

    // Load track videos
    const videosResponse = await fetch(
      `http://localhost:8000/api/segments/${segmentId.value}/videos`
    )
    if (videosResponse.ok) {
      trackVideos.value = await videosResponse.json()
    } else {
      // Videos are optional, so don't throw error if they fail to load
      console.warn('Failed to load track videos:', videosResponse.statusText)
      trackVideos.value = []
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

function openImageModal(image: any) {
  selectedImage.value = image
  currentModalImageIndex.value = trackImages.value.findIndex(
    (img) => img.id === image.id
  )
}

function closeImageModal() {
  selectedImage.value = null
}

// Carousel methods
function scrollImagesLeft() {
  if (canScrollImagesLeft.value) {
    currentImagesStart.value = Math.max(0, currentImagesStart.value - 1)
  }
}

function scrollImagesRight() {
  if (canScrollImagesRight.value) {
    currentImagesStart.value = Math.min(
      trackImages.value.length - imagesPerView.value,
      currentImagesStart.value + 1
    )
  }
}

function goToVideosPage(page: number) {
  if (page >= 1 && page <= totalVideosPages.value) {
    currentVideosPage.value = page
    currentVideosStart.value = 0 // Reset to first video in new page
  }
}

function nextVideosPage() {
  if (currentVideosPage.value < totalVideosPages.value) {
    currentVideosPage.value++
    currentVideosStart.value = 0 // Reset to first video in new page
  }
}

function previousVideosPage() {
  if (currentVideosPage.value > 1) {
    currentVideosPage.value--
    currentVideosStart.value = 0 // Reset to first video in new page
  }
}

function scrollVideosLeft() {
  if (canScrollVideosLeft.value) {
    currentVideosStart.value = Math.max(0, currentVideosStart.value - 1)
  }
}

function scrollVideosRight() {
  if (canScrollVideosRight.value) {
    currentVideosStart.value = Math.min(
      paginatedVideos.value.length - videosPerView.value,
      currentVideosStart.value + 1
    )
  }
}

// Modal navigation methods
function previousModalImage() {
  if (currentModalImageIndex.value > 0) {
    currentModalImageIndex.value--
  }
}

function nextModalImage() {
  if (currentModalImageIndex.value < trackImages.value.length - 1) {
    currentModalImageIndex.value++
  }
}

// Video helper functions
function getYouTubeEmbedUrl(url: string): string {
  // Extract video ID from various YouTube URL formats
  let videoId = null

  // Handle different YouTube URL formats
  if (url.includes('youtube.com/watch?v=')) {
    const match = url.match(/[?&]v=([^&]+)/)
    videoId = match ? match[1] : null
  } else if (url.includes('youtu.be/')) {
    const match = url.match(/youtu\.be\/([^?&]+)/)
    videoId = match ? match[1] : null
  } else if (url.includes('youtube.com/embed/')) {
    const match = url.match(/embed\/([^?&]+)/)
    videoId = match ? match[1] : null
  }

  if (videoId) {
    return `https://www.youtube.com/embed/${videoId}`
  }

  // Fallback for direct embed URLs
  return url
    .replace('watch?v=', 'embed/')
    .replace('youtu.be/', 'www.youtube.com/embed/')
}

function getVimeoEmbedUrl(url: string): string {
  // Extract video ID from Vimeo URL
  const regExp = /vimeo\.com\/(\d+)/
  const match = url.match(regExp)
  const videoId = match ? match[1] : null

  if (videoId) {
    return `https://player.vimeo.com/video/${videoId}`
  }

  return url
}

// Keyboard navigation for modal
function handleKeydown(event: KeyboardEvent) {
  if (selectedImage.value) {
    if (event.key === 'ArrowLeft') {
      event.preventDefault()
      previousModalImage()
    } else if (event.key === 'ArrowRight') {
      event.preventDefault()
      nextModalImage()
    } else if (event.key === 'Escape') {
      event.preventDefault()
      closeImageModal()
    }
  }
}

// Responsive images per view calculation
function updateImagesPerView() {
  const width = window.innerWidth
  if (width <= 480) {
    imagesPerView.value = 2
  } else if (width <= 768) {
    imagesPerView.value = 3
  } else {
    imagesPerView.value = 4
  }

  // Reset to first image if current start is beyond available images
  if (currentImagesStart.value + imagesPerView.value > trackImages.value.length) {
    currentImagesStart.value = Math.max(
      0,
      trackImages.value.length - imagesPerView.value
    )
  }
}

function updateVideosPerView() {
  // Use a more robust width detection that works in test environments
  const width = window.innerWidth || 1024 // Default to desktop width in test environments

  if (width <= 620) {
    videosPerView.value = 1
    videosPerPage.value = 1 // Match videos per page with videos per view for small screens
  } else if (width <= 1020) {
    videosPerView.value = 2
    videosPerPage.value = 2 // Match videos per page with videos per view for medium screens
  } else {
    videosPerView.value = 3
    videosPerPage.value = 3 // Match videos per page with videos per view for large screens
  }

  // Reset carousel position if current start is beyond available videos in current page
  if (currentVideosStart.value + videosPerView.value > paginatedVideos.value.length) {
    currentVideosStart.value = Math.max(
      0,
      paginatedVideos.value.length - videosPerView.value
    )
  }

  // Reset to page 1 if current page is beyond available pages with new page size
  const newTotalPages = Math.ceil(trackVideos.value.length / videosPerPage.value)
  if (currentVideosPage.value > newTotalPages) {
    currentVideosPage.value = 1
    currentVideosStart.value = 0
  }
}

// Lifecycle
onMounted(() => {
  loadSegmentData()
  document.addEventListener('keydown', handleKeydown)
  window.addEventListener('resize', updateImagesPerView)
  window.addEventListener('resize', updateVideosPerView)
  updateImagesPerView()
  updateVideosPerView()
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
  document.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('resize', updateImagesPerView)
  window.removeEventListener('resize', updateVideosPerView)
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
  margin-bottom: 1rem;
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
  grid-template-rows: 50% 50%;
  gap: 1rem;
  flex: 1;
  grid-template-areas:
    'map info'
    'elevation elevation';
}

/* Dynamic grid layout when comments are present */
.content-grid.with-comments {
  grid-template-rows: 33.33% 33.33% 33.33%;
  grid-template-areas:
    'map info'
    'elevation elevation'
    'comments comments';
}

/* Dynamic grid layout when images are present */
.content-grid.with-images {
  grid-template-rows: 33.33% 33.33% 33.33%;
  grid-template-areas:
    'map info'
    'elevation elevation'
    'images images';
}

/* Dynamic grid layout when both comments and images are present */
.content-grid.with-comments.with-images {
  grid-template-rows: 25% 25% 25% 25%;
  grid-template-areas:
    'map info'
    'elevation elevation'
    'comments comments'
    'images images';
}

/* Dynamic grid layout when videos are present */
.content-grid.with-videos {
  grid-template-rows: 33.33% 33.33% 33.33%;
  grid-template-areas:
    'map info'
    'elevation elevation'
    'videos videos';
}

/* Dynamic grid layout when comments and videos are present */
.content-grid.with-comments.with-videos {
  grid-template-rows: 25% 25% 25% 25%;
  grid-template-areas:
    'map info'
    'elevation elevation'
    'comments comments'
    'videos videos';
}

/* Dynamic grid layout when images and videos are present */
.content-grid.with-images.with-videos {
  grid-template-rows: 25% 25% 25% 25%;
  grid-template-areas:
    'map info'
    'elevation elevation'
    'images images'
    'videos videos';
}

/* Dynamic grid layout when comments, images and videos are present */
.content-grid.with-comments.with-images.with-videos {
  grid-template-rows: 20% 20% 20% 20% 20%;
  grid-template-areas:
    'map info'
    'elevation elevation'
    'comments comments'
    'images images'
    'videos videos';
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

/* Responsive layout adjustments */
@media (max-width: 768px) {
  .segment-detail {
    overflow-y: auto; /* Enable vertical scrolling on small devices */
  }

  .content-grid {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(300px, auto) auto auto;
    grid-template-areas:
      'map'
      'info'
      'elevation';
    gap: 1.5rem; /* Increase gap for better spacing when stacked */
  }

  .content-grid.with-comments {
    grid-template-rows: minmax(300px, auto) auto auto auto;
    grid-template-areas:
      'map'
      'info'
      'elevation'
      'comments';
  }

  .content-grid.with-images {
    grid-template-rows: minmax(300px, auto) auto auto auto;
    grid-template-areas:
      'map'
      'info'
      'elevation'
      'images';
  }

  .content-grid.with-comments.with-images {
    grid-template-rows: minmax(300px, auto) auto auto auto auto;
    grid-template-areas:
      'map'
      'info'
      'elevation'
      'comments'
      'images';
  }

  .content-grid.with-videos {
    grid-template-rows: minmax(300px, auto) auto auto auto;
    grid-template-areas:
      'map'
      'info'
      'elevation'
      'videos';
  }

  .content-grid.with-comments.with-videos {
    grid-template-rows: minmax(300px, auto) auto auto auto auto;
    grid-template-areas:
      'map'
      'info'
      'elevation'
      'comments'
      'videos';
  }

  .content-grid.with-images.with-videos {
    grid-template-rows: minmax(300px, auto) auto auto auto auto;
    grid-template-areas:
      'map'
      'info'
      'elevation'
      'images'
      'videos';
  }

  .content-grid.with-comments.with-images.with-videos {
    grid-template-rows: minmax(300px, auto) auto auto auto auto auto;
    grid-template-areas:
      'map'
      'info'
      'elevation'
      'comments'
      'images'
      'videos';
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

/* Images Gallery Styles */
.images-section {
  grid-area: images;
}

.images-carousel {
  position: relative;
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 3.5rem 1rem 3.5rem;
}

.images-gallery {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  flex: 1;
  overflow: hidden;
}

.carousel-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #d1d5db;
  border-radius: 50%;
  width: 2.5rem;
  height: 2.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  z-index: 10;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.carousel-btn:hover {
  background: #ffffff;
  border-color: #ff6600;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.carousel-btn i {
  color: #374151;
  font-size: 0.875rem;
}

.carousel-btn:hover i {
  color: #ff6600;
}

.carousel-btn-left {
  left: 0.5rem;
}

.carousel-btn-right {
  right: 0.5rem;
}

.gallery-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.gallery-item:hover {
  transform: scale(1.02);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.gallery-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.gallery-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.gallery-item:hover .gallery-overlay {
  opacity: 1;
}

.gallery-overlay i {
  color: white;
  font-size: 1.5rem;
}

/* Image Modal Styles */
.image-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 2rem;
}

.modal-content {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.modal-image-container {
  position: relative;
  overflow: hidden;
  max-width: 80vw;
  max-height: 80vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-image {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
  user-select: none;
}

.modal-nav-btn {
  position: fixed;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(0, 0, 0, 0.7);
  border: none;
  border-radius: 50%;
  width: 3rem;
  height: 3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  z-index: 1001;
  color: white;
}

.modal-nav-btn:hover {
  background: rgba(0, 0, 0, 0.9);
  transform: translateY(-50%) scale(1.1);
}

.modal-nav-btn i {
  font-size: 1.25rem;
}

.modal-nav-left {
  left: 2rem;
}

.modal-nav-right {
  right: 2rem;
}

.modal-close {
  position: fixed;
  top: 5rem;
  right: 2rem;
  background: rgba(0, 0, 0, 0.7);
  border: none;
  color: white;
  font-size: 1.25rem;
  cursor: pointer;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  z-index: 1002;
}

.modal-close:hover {
  background: rgba(0, 0, 0, 0.9);
  transform: scale(1.1);
}

.modal-image {
  max-width: 100%;
  max-height: 80vh;
  object-fit: contain;
  border-radius: 8px;
}

.modal-info {
  margin-top: 1rem;
  text-align: center;
}

.image-filename {
  color: white;
  font-size: 0.875rem;
  margin: 0;
  opacity: 0.8;
}

/* Videos Gallery Styles */
.videos-section {
  grid-area: videos;
}

.videos-carousel {
  position: relative;
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
}

.videos-gallery {
  display: flex;
  justify-content: space-evenly;
  align-items: center;
  flex: 1;
  overflow: hidden;
  padding: 0 1rem;
}

.video-item {
  display: flex;
  flex-direction: column;
  border-radius: 8px;
  flex-shrink: 0;
  width: 320px; /* Larger width for 3 videos on large screens */
  overflow: hidden;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  transition: box-shadow 0.2s ease;
}

.video-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.video-embed {
  position: relative;
  width: 100%;
  height: 0;
  padding-bottom: 56.25%; /* 16:9 aspect ratio */
  overflow: hidden;
}

.video-iframe {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: none;
}

.video-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f9fafb;
  color: #6b7280;
  text-align: center;
  padding: 1rem;
}

.video-placeholder i {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.video-placeholder p {
  margin: 0.5rem 0;
  font-weight: 500;
}

.video-link {
  display: inline-block;
  padding: 0.5rem 1rem;
  background: var(--brand-500);
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-size: 0.875rem;
  transition: background-color 0.2s;
}

.video-link:hover {
  background: var(--brand-600);
}

/* Responsive adjustments for images and videos */
@media (max-width: 1020px) {
  .images-carousel {
    padding: 0.75rem;
  }

  .images-gallery {
    grid-template-columns: repeat(3, 1fr);
    gap: 0.75rem;
  }

  .carousel-btn {
    width: 2rem;
    height: 2rem;
  }

  .carousel-btn i {
    font-size: 0.75rem;
  }

  .carousel-btn-left {
    left: 0.25rem;
  }

  .carousel-btn-right {
    right: 0.25rem;
  }

  .videos-carousel {
    padding: 0.75rem;
  }

  .videos-gallery {
    justify-content: space-evenly;
    padding: 0 0.5rem;
  }

  .video-item {
    width: 300px; /* Larger width for 2 videos on medium screens */
  }

  .modal-nav-btn {
    width: 2.5rem;
    height: 2.5rem;
  }

  .modal-nav-btn i {
    font-size: 1rem;
  }

  .modal-image-container {
    max-width: 85vw;
    max-height: 75vh;
  }

  .modal-nav-left {
    left: 1rem;
  }

  .modal-nav-right {
    right: 1rem;
  }

  .image-modal {
    padding: 1rem;
  }

  .modal-close {
    top: 5rem;
    right: 0.75rem;
    width: 2rem;
    height: 2rem;
    font-size: 1rem;
  }
}

/* Pagination Styles */
.pagination {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: center;
  align-items: center;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  justify-content: center;
}

.pagination-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  color: #374151;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.pagination-btn:hover:not(:disabled) {
  background: #f9fafb;
  border-color: #9ca3af;
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #f9fafb;
}

.pagination-btn i {
  font-size: 0.75rem;
}

.pagination-pages {
  display: flex;
  gap: 0.25rem;
}

.pagination-page {
  min-width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  color: #374151;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.pagination-page:hover {
  background: #f9fafb;
  border-color: #9ca3af;
}

.pagination-page.active {
  background: #ff6600;
  border-color: #ff6600;
  color: #ffffff;
}

.pagination-page.active:hover {
  background: #e55a00;
  border-color: #e55a00;
}

/* Responsive pagination */
@media (max-width: 768px) {
  .pagination {
    margin-top: 1rem;
    padding-top: 0.75rem;
    gap: 0.75rem;
  }

  .pagination-btn {
    padding: 0.4rem 0.8rem;
    font-size: 0.8rem;
  }

  .pagination-page {
    min-width: 1.75rem;
    height: 1.75rem;
    font-size: 0.8rem;
  }

  .pagination-controls {
    gap: 0.25rem;
  }

  .pagination-pages {
    gap: 0.125rem;
  }
}

@media (max-width: 620px) {
  .images-gallery {
    grid-template-columns: repeat(2, 1fr);
  }

  .carousel-btn {
    width: 1.75rem;
    height: 1.75rem;
  }

  .carousel-btn i {
    font-size: 0.625rem;
  }

  .videos-carousel {
    padding: 0.5rem;
  }

  .videos-gallery {
    justify-content: center;
    padding: 0 0.25rem;
  }

  .video-item {
    width: 280px; /* Full width for 1 video on small screens */
  }

  .modal-nav-btn {
    width: 2rem;
    height: 2rem;
  }

  .modal-nav-btn i {
    font-size: 0.875rem;
  }

  .modal-close {
    top: 5rem;
    right: 0.5rem;
    width: 1.75rem;
    height: 1.75rem;
    font-size: 0.875rem;
  }

  .modal-image-container {
    max-width: 90vw;
    max-height: 70vh;
  }

  .modal-nav-left {
    left: 0.5rem;
  }

  .modal-nav-right {
    right: 0.5rem;
  }

  .pagination-btn {
    padding: 0.35rem 0.6rem;
    font-size: 0.75rem;
  }

  .pagination-btn span {
    display: none; /* Hide text on very small screens, keep only icons */
  }

  .pagination-btn i {
    margin: 0;
  }

  .pagination-page {
    min-width: 1.5rem;
    height: 1.5rem;
    font-size: 0.75rem;
  }
}
</style>
