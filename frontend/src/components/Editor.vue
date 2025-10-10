<template>
  <div class="editor">
    <div
      class="sidebar"
      :class="{ compact: isCompactSidebar, collapsed: isSidebarCollapsed }"
    >
      <div v-if="!isSidebarCollapsed" class="sidebar-scroll">
        <div class="card menu-card">
          <div class="menu-section">
            <div v-if="!isCompactSidebar" class="menu-section-title">
              {{ t('menu.import') }}
            </div>
            <ul class="menu-list">
              <li
                class="menu-item"
                @click="triggerFileOpen"
                :title="isCompactSidebar ? t('menu.gpxFile') : t('tooltip.loadGpxFile')"
                role="button"
              >
                <span class="icon" aria-hidden="true"
                  ><i class="fa-solid fa-file-lines"></i
                ></span>
                <span v-if="!isCompactSidebar" class="text">{{
                  t('menu.gpxFile')
                }}</span>
              </li>
              <li
                class="menu-item"
                @click="openStravaImport"
                :title="
                  isCompactSidebar ? t('menu.stravaImport') : t('strava.selectActivity')
                "
                role="button"
              >
                <span class="icon" aria-hidden="true"
                  ><i class="fa-brands fa-strava"></i
                ></span>
                <span v-if="!isCompactSidebar" class="text">{{
                  t('menu.stravaImport')
                }}</span>
              </li>
              <li
                class="menu-item"
                @click="openSegmentImport"
                :title="
                  isCompactSidebar
                    ? t('menu.importSegment')
                    : t('menu.importSegmentTooltip')
                "
                role="button"
              >
                <span class="icon" aria-hidden="true"
                  ><i class="fa-solid fa-database"></i
                ></span>
                <span v-if="!isCompactSidebar" class="text">{{
                  t('menu.importSegment')
                }}</span>
              </li>
            </ul>
            <input
              ref="fileInput"
              type="file"
              accept=".gpx"
              @change="onFileChange"
              hidden
            />
          </div>

          <div class="menu-section">
            <div v-if="!isCompactSidebar" class="menu-section-title">
              {{ t('menu.segments') }}
            </div>
            <ul class="menu-list">
              <li
                class="menu-item action"
                :class="{ disabled: isSaveDisabled }"
                :aria-disabled="isSaveDisabled"
                :title="
                  isCompactSidebar
                    ? t('menu.saveAsNew')
                    : isSaveDisabled
                      ? saveDisabledTitle
                      : t('menu.saveAsNew')
                "
                @click="!isSaveDisabled && onSaveAsNew()"
                data-testid="save-as-new-button"
              >
                <span class="icon" aria-hidden="true"
                  ><i class="fa-solid fa-plus"></i
                ></span>
                <span v-if="!isCompactSidebar" class="text">{{
                  t('menu.saveAsNew')
                }}</span>
              </li>
              <li
                class="menu-item action"
                :class="{ disabled: isUpdateDisabled }"
                :aria-disabled="isUpdateDisabled"
                :title="
                  isCompactSidebar
                    ? t('menu.updateInDb')
                    : isUpdateDisabled
                      ? updateDisabledTitle
                      : t('menu.updateInDb')
                "
                @click="!isUpdateDisabled && onUpdate()"
                data-testid="update-button"
              >
                <span class="icon" aria-hidden="true"
                  ><i class="fa-solid fa-arrows-rotate"></i
                ></span>
                <span v-if="!isCompactSidebar" class="text">{{
                  t('menu.updateInDb')
                }}</span>
              </li>
              <li
                class="menu-item action danger"
                :class="{ disabled: isDeleteDisabled }"
                :aria-disabled="isDeleteDisabled"
                :title="
                  isCompactSidebar
                    ? t('menu.deleteFromDb')
                    : isDeleteDisabled
                      ? deleteDisabledTitle
                      : t('menu.deleteFromDb')
                "
                @click="!isDeleteDisabled && onDeleteFromDb()"
                data-testid="delete-from-db-button"
              >
                <span class="icon" aria-hidden="true"
                  ><i class="fa-solid fa-trash"></i
                ></span>
                <span v-if="!isCompactSidebar" class="text">{{
                  t('menu.deleteFromDb')
                }}</span>
              </li>
            </ul>
          </div>

          <!-- Info Feed Section -->
          <div class="menu-section info-feed-section">
            <div v-if="!isCompactSidebar" class="menu-section-title">
              {{ t('menu.infoFeed') }}
            </div>

            <!-- Upload Progress -->
            <div v-if="isUploading" class="info-feed-item upload-progress-item">
              <div class="info-feed-icon">
                <i class="fa-solid fa-upload"></i>
              </div>
              <div v-if="!isCompactSidebar" class="info-feed-content">
                <div class="upload-progress-bar">
                  <div
                    class="upload-progress-fill"
                    :style="{ width: uploadProgress + '%' }"
                  ></div>
                </div>
                <div class="info-feed-text">
                  {{ t('message.uploading') }} {{ Math.round(uploadProgress) }}%
                </div>
              </div>
              <div v-else class="info-feed-content">
                <div class="info-feed-text">{{ Math.round(uploadProgress) }}%</div>
              </div>
            </div>

            <!-- Upload Success -->
            <div v-if="showUploadSuccess" class="info-feed-item upload-success-item">
              <div class="info-feed-icon">
                <i class="fa-solid fa-check-circle"></i>
              </div>
              <div v-if="!isCompactSidebar" class="info-feed-content">
                <div class="info-feed-text">
                  {{ t('message.uploadSuccess') }}
                </div>
              </div>
            </div>

            <!-- Segment Success -->
            <div v-if="showSegmentSuccess" class="info-feed-item upload-success-item">
              <div class="info-feed-icon">
                <i class="fa-solid fa-check-circle"></i>
              </div>
              <div v-if="!isCompactSidebar" class="info-feed-content">
                <div class="info-feed-text">
                  {{ t('message.segmentCreated') }}
                </div>
              </div>
            </div>

            <!-- Error Messages -->
            <div v-if="showError" class="info-feed-item error-item">
              <div class="info-feed-icon">
                <i class="fa-solid fa-exclamation-circle"></i>
              </div>
              <div v-if="!isCompactSidebar" class="info-feed-content">
                <div class="info-feed-text">
                  {{ currentErrorMessage }}
                </div>
              </div>
            </div>

            <!-- Empty State -->
            <div
              v-if="
                !isUploading && !showUploadSuccess && !showSegmentSuccess && !showError
              "
              class="info-feed-item empty-item"
            >
              <div class="info-feed-icon">
                <i class="fa-solid fa-info-circle"></i>
              </div>
              <div v-if="!isCompactSidebar" class="info-feed-content">
                <div class="info-feed-text">
                  {{ t('message.noActivity') }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Collapse/Expand Button - Only visible on compact sidebar -->
      <div v-if="isCompactSidebar" class="sidebar-toggle">
        <button
          @click="toggleSidebarCollapse"
          class="toggle-btn"
          :class="{ collapsed: isSidebarCollapsed }"
          :title="
            isSidebarCollapsed ? t('menu.expandSidebar') : t('menu.collapseSidebar')
          "
        >
          <i
            :class="
              isSidebarCollapsed
                ? 'fa-solid fa-chevron-right'
                : 'fa-solid fa-chevron-left'
            "
          ></i>
        </button>
      </div>
    </div>

    <div class="content">
      <div class="page">
        <div class="main-col">
          <div v-if="loaded">
            <div class="card card-map">
              <div id="map" class="map"></div>
            </div>
            <ElevationCropper
              :points="points"
              :cumulative-km="cumulativeKm"
              :cumulative-sec="cumulativeSec"
              :smoothed-elevations="smoothedElevations"
              v-model:start-index="startIndex"
              v-model:end-index="endIndex"
              v-model:x-mode="xMode"
              @chart-hover="updateMarkerPositionFromIndex"
            />

            <MetadataForm
              v-model:name="name"
              v-model:track-type="trackType"
              v-model:trail-conditions="trailConditions"
              v-model:commentary="commentary"
              v-model:is-drag-over="isDragOver"
              @submit="onSaveAsNew"
            />
          </div>

          <div v-if="!loaded" class="empty">
            <p>{{ t('message.useFileLoad') }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Regular Messages -->
    <p v-if="message" class="message">{{ message }}</p>

    <!-- Strava Import Modal -->
    <div v-if="showStravaModal" class="modal-overlay" @click="closeStravaModal">
      <div class="modal-content" @click.stop>
        <StravaActivityList @close="closeStravaModal" @import="handleStravaImport" />
      </div>
    </div>

    <!-- Segment Import Modal -->
    <SegmentImportModal
      :is-open="showSegmentImportModal"
      @close="closeSegmentImportModal"
      @import="handleSegmentImport"
    />
  </div>
</template>

<script lang="ts" setup>
import { onMounted, onUnmounted, ref, watch, nextTick, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import L from 'leaflet'
import StravaActivityList from './StravaActivityList.vue'
import SegmentImportModal from './SegmentImportModal.vue'
import ElevationCropper from './ElevationCropper.vue'
import MetadataForm from './MetadataForm.vue'
import { parseGPXData } from '../utils/gpxParser'
import { useStravaApi } from '../composables/useStravaApi'
import type { Commentary, TrailConditions, SurfaceType } from '../types'

type TrackPoint = {
  latitude: number
  longitude: number
  elevation: number
  time?: string
}

const { t } = useI18n()
const { authState } = useStravaApi()

onMounted(() => {})

onUnmounted(() => {})

const loaded = ref(false)
const name = ref('')
const trackType = ref<'segment' | 'route'>('segment')
const trailConditions = ref<TrailConditions>({
  tire_dry: 'slick',
  tire_wet: 'slick',
  surface_type: [],
  difficulty_level: 3
})
const submitting = ref(false)
const message = ref('')

// Commentary data
const commentary = ref<Commentary>({
  text: '',
  video_links: [],
  images: []
})
const isDragOver = ref(false)

// Responsive sidebar state
const isCompactSidebar = ref(false)
const isSidebarCollapsed = ref(false)

// Strava integration
// Strava authentication is now handled by the navbar and route guards
const showStravaModal = ref(false)

// Segment import modal
const showSegmentImportModal = ref(false)

const fileInput = ref<HTMLInputElement | null>(null)
const points = ref<TrackPoint[]>([])
const startIndex = ref(0)
const endIndex = ref(0)
const cumulativeKm = ref<number[]>([])
const cumulativeSec = ref<number[]>([])
const xMode = ref<'distance' | 'time'>('distance')
const uploadedFileId = ref<string | null>(null)
const uploadProgress = ref<number>(0)
const isUploading = ref<boolean>(false)
const showUploadSuccess = ref<boolean>(false)
const showSegmentSuccess = ref<boolean>(false)
const showError = ref<boolean>(false)
const currentErrorMessage = ref<string>('')

// Update mode state
const isUpdateMode = ref<boolean>(false)
const updatingSegmentId = ref<number | null>(null)

const isSaveDisabled = computed(() => submitting.value || !name.value || !loaded.value)
const isUpdateDisabled = computed(
  () => submitting.value || !name.value || !loaded.value || !isUpdateMode.value
)

const saveDisabledTitle = computed(() => {
  if (!loaded.value) return t('tooltip.loadGpxFirst')
  if (!name.value) return t('tooltip.enterSegmentName')
  if (submitting.value) return t('tooltip.submitting')
  return ''
})

const updateDisabledTitle = computed(() => {
  if (!loaded.value) return t('tooltip.loadGpxFirst')
  if (!name.value) return t('tooltip.enterSegmentName')
  if (submitting.value) return t('tooltip.submitting')
  if (!isUpdateMode.value) return t('tooltip.loadFromDatabase')
  return ''
})

const isDeleteDisabled = computed(
  () => submitting.value || !loaded.value || !isUpdateMode.value
)

const deleteDisabledTitle = computed(() => {
  if (!loaded.value) return t('tooltip.loadGpxFirst')
  if (submitting.value) return t('tooltip.submitting')
  if (!isUpdateMode.value) return t('tooltip.loadFromDatabase')
  return ''
})

let map: any = null
let fullLine: any = null
let selectedLine: any = null
let baseLayer: any = null
let mapMarker: any = null

const smoothedElevations = ref<number[]>([])
// const startMin = computed(() => 0)
// const startMax = computed(() => Math.max(1, endIndex.value - 1))
// const endMin = computed(() => Math.min(points.value.length - 1, startIndex.value + 1))
// const endMax = computed(() => points.value.length - 1)
// function toPercent(value: number, min: number, max: number): number {
//   if (max <= min) return 0
//   return ((value - min) / (max - min)) * 100
// }
// const startPercent = computed(() =>
//   toPercent(startIndex.value, startMin.value, startMax.value)
// )
// const endPercent = computed(() => toPercent(endIndex.value, endMin.value, endMax.value))

function triggerFileOpen() {
  fileInput.value?.click()
}

async function onFileChange(ev: Event) {
  const input = ev.target as HTMLInputElement
  const file = input.files && input.files[0]
  if (!file) return

  // Reset update mode when loading new file
  resetUpdateMode()

  isUploading.value = true
  uploadProgress.value = 0
  showError.value = false
  currentErrorMessage.value = ''
  message.value = ''

  try {
    const formData = new FormData()
    formData.append('file', file)

    // Simulate upload progress for better UX
    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += Math.random() * 20
        if (uploadProgress.value > 90) uploadProgress.value = 90
      }
    }, 200)

    const response = await fetch('/api/upload-gpx', {
      method: 'POST',
      body: formData
    })

    clearInterval(progressInterval)
    uploadProgress.value = 100

    if (!response.ok) {
      const error = await response.text()
      throw new Error(error || 'Upload failed')
    }

    const uploadData = await response.json()

    // Use points directly from upload response
    const actualPoints: TrackPoint[] = uploadData.points.map((p: any) => ({
      latitude: p.latitude,
      longitude: p.longitude,
      elevation: p.elevation,
      time: p.time
    }))

    if (actualPoints.length < 2) {
      showError.value = true
      currentErrorMessage.value = t('message.insufficientPoints')
      showUploadSuccess.value = false
      showSegmentSuccess.value = false
      return
    }

    points.value = actualPoints
    cumulativeKm.value = computeCumulativeKm(actualPoints)
    cumulativeSec.value = computeCumulativeSec(actualPoints)
    smoothedElevations.value = computeSmoothedElevations(actualPoints, 5)
    startIndex.value = 0
    endIndex.value = actualPoints.length - 1
    uploadedFileId.value = uploadData.file_id
    loaded.value = true
    message.value = ''

    // Keep progress bar visible for 1 second after completion
    setTimeout(() => {
      isUploading.value = false
      uploadProgress.value = 0
      showUploadSuccess.value = true
      showError.value = false
      currentErrorMessage.value = ''
      showSegmentSuccess.value = false
    }, 1000)

    await nextTick()
    renderMap()
  } catch (err: any) {
    isUploading.value = false
    uploadProgress.value = 0
    showError.value = true
    currentErrorMessage.value = err.message || t('message.uploadError')
    showUploadSuccess.value = false
    showSegmentSuccess.value = false

    // Hide error after 5 seconds
    setTimeout(() => {
      showError.value = false
      currentErrorMessage.value = ''
    }, 5000)
  }
}

function computeCumulativeKm(pts: TrackPoint[]): number[] {
  const out: number[] = [0]
  for (let i = 1; i < pts.length; i++) {
    const d = haversine(
      pts[i - 1].latitude,
      pts[i - 1].longitude,
      pts[i].latitude,
      pts[i].longitude
    )
    out.push(out[i - 1] + d)
  }
  return out
}

function haversine(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLon = ((lon2 - lon1) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) ** 2
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

async function uploadImageToStorage(file: File, imageId: string) {
  try {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch('/api/upload-image', {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      throw new Error('Failed to upload image to storage')
    }

    const result = await response.json()

    // Update the image in commentary with the stored URL
    const imageIndex = commentary.value.images.findIndex((img) => img.id === imageId)
    if (imageIndex !== -1) {
      commentary.value.images[imageIndex].uploaded = true
      commentary.value.images[imageIndex].image_url = result.image_url
      commentary.value.images[imageIndex].image_id = result.image_id
      commentary.value.images[imageIndex].storage_key = result.storage_key
    }

    // Only show upload success log in development, not during tests
    // Check if we're in a test environment by checking for the vi mock object
    const isTestEnv = (() => {
      try {
        return typeof (globalThis as any).vi !== 'undefined'
      } catch {
        return false
      }
    })()
    if (!isTestEnv) {
      console.info(`Successfully uploaded image to storage: ${result.storage_key}`)
    }
  } catch (error) {
    console.error('Failed to upload image to storage:', error)
    // Keep the image with local preview even if upload failed
    showError.value = true
    currentErrorMessage.value = 'Failed to upload image to storage'
  }
}

function renderMap() {
  if (!map) {
    const container = document.getElementById('map')
    if (!container) return
    map = L.map(container)
  }
  const latlngs = points.value.map((p) => [p.latitude, p.longitude]) as [
    number,
    number
  ][]
  const bounds = L.latLngBounds(latlngs)
  map!.invalidateSize()
  map!.fitBounds(bounds, { padding: [20, 20] })
  if (!baseLayer) {
    const apiKey = import.meta.env.THUNDERFOREST_API_KEY || 'demo'
    baseLayer = L.tileLayer(
      `https://{s}.tile.thunderforest.com/cycle/{z}/{x}/{y}.png?apikey=${apiKey}`,
      {
        maxZoom: 19,
        attribution:
          'Maps © <a href="https://www.thunderforest.com/">Thunderforest</a>, Data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      }
    )
    baseLayer.addTo(map!)
  }

  if (fullLine) fullLine.remove()
  fullLine = L.polyline(latlngs, { color: '#888', weight: 4 })
  fullLine.addTo(map!)

  // Add click and mousemove handlers for marker positioning
  fullLine.on('click', (e: any) => {
    updateMarkerPosition(e.latlng)
  })

  fullLine.on('mousemove', (e: any) => {
    updateMarkerPosition(e.latlng)
  })

  // Clean up existing marker before creating new one
  if (mapMarker) {
    mapMarker.remove()
    mapMarker = null
  }

  updateSelectedPolyline()

  // Create initial marker at first point AFTER polylines are added
  if (points.value.length > 0) {
    const firstPoint = points.value[0]

    // Create a custom icon for the marker
    const markerIcon = L.divIcon({
      className: 'custom-marker',
      html: '<div style="background-color: #ff6600; width: 16px; height: 16px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>',
      iconSize: [16, 16],
      iconAnchor: [8, 8]
    })

    mapMarker = L.marker([firstPoint.latitude, firstPoint.longitude], {
      icon: markerIcon,
      zIndexOffset: 1000
    }).addTo(map!)
  }
}

function updateMarkerPosition(latlng: any) {
  if (!points.value.length) return

  // Find closest point
  let closestPoint = points.value[0]
  let minDistance = Infinity

  for (let i = 0; i < points.value.length; i++) {
    const point = points.value[i]
    const distance = haversine(latlng.lat, latlng.lng, point.latitude, point.longitude)
    if (distance < minDistance) {
      minDistance = distance
      closestPoint = point
    }
  }

  // Update marker position
  if (mapMarker) {
    mapMarker.setLatLng([closestPoint.latitude, closestPoint.longitude])
  }
}

function updateMarkerPositionFromIndex(index: number) {
  if (!points.value.length || index < 0 || index >= points.value.length) return

  const point = points.value[index]
  if (mapMarker) {
    mapMarker.setLatLng([point.latitude, point.longitude])
  }
}

function updateSelectedPolyline() {
  if (!map) return
  const segLatLngs = points.value
    .slice(startIndex.value, endIndex.value + 1)
    .map((p) => [p.latitude, p.longitude]) as [number, number][]
  if (selectedLine) selectedLine.remove()
  selectedLine = L.polyline(segLatLngs, {
    color:
      getComputedStyle(document.documentElement)
        .getPropertyValue('--brand-500')
        .trim() || '#ff6600',
    weight: 5
  })
  selectedLine.addTo(map)
}

function computeCumulativeSec(pts: TrackPoint[]): number[] {
  const out: number[] = [0]
  for (let i = 1; i < pts.length; i++) {
    const t0 = pts[i - 1].time
      ? new Date(pts[i - 1].time as string).getTime()
      : undefined
    const t1 = pts[i].time ? new Date(pts[i].time as string).getTime() : undefined
    const d = t0 && t1 ? Math.max(0, (t1 - t0) / 1000) : 1
    out.push(out[i - 1] + d)
  }
  return out
}

function computeSmoothedElevations(pts: TrackPoint[], windowSize = 5): number[] {
  const half = Math.floor(windowSize / 2)
  const out: number[] = new Array(pts.length)
  for (let i = 0; i < pts.length; i++) {
    let sum = 0
    let count = 0
    for (let j = Math.max(0, i - half); j <= Math.min(pts.length - 1, i + half); j++) {
      sum += pts[j].elevation
      count += 1
    }
    out[i] = count ? sum / count : pts[i].elevation
  }
  return out
}

watch([startIndex, endIndex], () => {
  if (startIndex.value >= endIndex.value) {
    endIndex.value = Math.min(points.value.length - 1, startIndex.value + 1)
  }
  updateSelectedPolyline()
  if (map && points.value.length > 1) {
    const segLatLngs = points.value
      .slice(startIndex.value, endIndex.value + 1)
      .map((p) => [p.latitude, p.longitude]) as [number, number][]
    const segBounds = L.latLngBounds(segLatLngs)
    map.fitBounds(segBounds, { padding: [20, 20] })
  }

  // Update marker position to the start point when sliders change
  updateMarkerPositionFromIndex(startIndex.value)
})

watch(loaded, async () => {
  await nextTick()
})

// Function to check if sidebar should be compact
function checkSidebarMode() {
  isCompactSidebar.value = window.innerWidth < 1100
}

// Function to toggle sidebar collapse
function toggleSidebarCollapse() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}

onMounted(() => {
  // Check initial sidebar mode
  checkSidebarMode()

  const onResize = () => {
    if (map) {
      setTimeout(() => map!.invalidateSize(), 0)
    }
    // Check sidebar mode on resize
    checkSidebarMode()
  }
  window.addEventListener('resize', onResize)
  ;(window as any).__editorOnResize = onResize
})

onUnmounted(() => {
  const onResize = (window as any).__editorOnResize
  if (onResize) window.removeEventListener('resize', onResize)

  // Clean up map marker
  if (mapMarker) {
    mapMarker.remove()
    mapMarker = null
  }
})

// function escapeXml(s: string): string {
//   return s.replace(
//     /[<>&"']/g,
//     (c) =>
//       ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&apos;' })[
//         c
//       ] as string
//   )
// }

// Strava integration functions
function openStravaImport() {
  showStravaModal.value = true
}

function closeStravaModal() {
  showStravaModal.value = false
}

// Segment import modal functions
function openSegmentImport() {
  showSegmentImportModal.value = true
}

function closeSegmentImportModal() {
  showSegmentImportModal.value = false
}

async function handleStravaImport(gpxData: any) {
  try {
    console.info(
      `Importing Strava activity: ${gpxData.track_name} with ${gpxData.points?.length || 0} points`
    )

    // Use the same logic as file upload but with GPX data from Strava
    const actualPoints: TrackPoint[] = gpxData.points.map((p: any) => ({
      latitude: p.latitude,
      longitude: p.longitude,
      elevation: p.elevation,
      time: p.time
    }))

    // CRITICAL: Process the data the same way as regular file upload
    points.value = actualPoints
    cumulativeKm.value = computeCumulativeKm(actualPoints)
    cumulativeSec.value = computeCumulativeSec(actualPoints)
    smoothedElevations.value = computeSmoothedElevations(actualPoints, 5)
    startIndex.value = 0
    endIndex.value = actualPoints.length - 1

    console.info(`Data processing complete: ${actualPoints.length} points processed`)

    if (actualPoints.length < 2) {
      console.error(`❌ Insufficient points: ${actualPoints.length}`)
      showError.value = true
      currentErrorMessage.value = t('message.insufficientPoints')
      showUploadSuccess.value = false
      showSegmentSuccess.value = false
      return
    }

    // Set additional data
    loaded.value = true
    name.value = gpxData.track_name || 'Strava Activity'

    // CRITICAL: Set uploadedFileId for Strava imports using the real file ID from backend
    uploadedFileId.value = gpxData.file_id || `strava-activity-${Date.now()}`

    console.info(`Editor state updated: ${points.value.length} points loaded`)

    // Clear any previous errors
    showError.value = false
    currentErrorMessage.value = ''
    message.value = ''
    showUploadSuccess.value = true
    showSegmentSuccess.value = false

    console.info(`Strava import successful`)

    // Close the modal
    closeStravaModal()

    // Update the map and chart
    await nextTick()
    renderMap()
  } catch (error) {
    console.error('Error importing Strava activity:', error)
    showError.value = true
    currentErrorMessage.value = t('strava.importError')
  }
}

async function handleSegmentImport(segment: any) {
  try {
    console.info(`Importing segment: ${segment.name} (ID: ${segment.id})`)

    // Fetch GPX data for the segment
    const response = await fetch(`http://localhost:8000/api/segments/${segment.id}/gpx`)
    if (!response.ok) {
      throw new Error(`Failed to fetch GPX data: ${response.statusText}`)
    }

    const gpxResponse = await response.json()

    // Parse GPX data similar to file upload
    const gpxData = parseGPXData(gpxResponse.gpx_xml_data, segment.id.toString())

    if (!gpxData || !gpxData.points || gpxData.points.length < 2) {
      throw new Error('Invalid GPX data or insufficient points')
    }

    // Use the same logic as file upload but with GPX data from database
    const actualPoints: TrackPoint[] = gpxData.points.map((p: any) => ({
      latitude: p.latitude,
      longitude: p.longitude,
      elevation: p.elevation,
      time: p.time
    }))

    // Process the data the same way as regular file upload
    points.value = actualPoints
    cumulativeKm.value = computeCumulativeKm(actualPoints)
    cumulativeSec.value = computeCumulativeSec(actualPoints)
    smoothedElevations.value = computeSmoothedElevations(actualPoints, 5)
    startIndex.value = 0
    endIndex.value = actualPoints.length - 1

    console.info(`Data processing complete: ${actualPoints.length} points processed`)

    if (actualPoints.length < 2) {
      console.error(`❌ Insufficient points: ${actualPoints.length}`)
      showError.value = true
      currentErrorMessage.value = t('message.insufficientPoints')
      showUploadSuccess.value = false
      showSegmentSuccess.value = false
      return
    }

    // Initialize form with database segment data
    loaded.value = true
    name.value = segment.name

    // Set track type from database
    trackType.value = segment.track_type as 'segment' | 'route'

    // Initialize trail conditions from database
    trailConditions.value = {
      tire_dry: segment.tire_dry as 'slick' | 'semi-slick' | 'knobs',
      tire_wet: segment.tire_wet as 'slick' | 'semi-slick' | 'knobs',
      surface_type: segment.surface_type as SurfaceType[],
      difficulty_level: segment.difficulty_level
    }

    // Initialize commentary from database comments
    commentary.value = {
      text: segment.comments || '',
      video_links: [],
      images: []
    }

    // Create a temporary GPX file for database imports
    // Use the actual file_id returned by the backend
    const actualFileId = await createTemporaryGPXFile(segment.id.toString())
    uploadedFileId.value = actualFileId

    // Set update mode
    isUpdateMode.value = true
    updatingSegmentId.value = segment.id

    console.info(`Editor state updated: ${points.value.length} points loaded`)
    console.info(`Form initialized with segment data:`, {
      name: segment.name,
      trackType: segment.track_type,
      trailConditions: trailConditions.value,
      commentary: commentary.value
    })

    // Clear any previous errors
    showError.value = false
    currentErrorMessage.value = ''
    message.value = ''
    showUploadSuccess.value = true
    showSegmentSuccess.value = false

    console.info(`Segment import successful`)

    // Close the modal
    closeSegmentImportModal()

    // Update the map and chart
    await nextTick()
    renderMap()
  } catch (error) {
    console.error('Error importing segment:', error)
    showError.value = true
    currentErrorMessage.value = t('message.importError') || 'Failed to import segment'
  }
}

async function onSaveAsNew() {
  if (!loaded.value || points.value.length < 2 || !uploadedFileId.value) {
    console.error(
      `Form validation failed: ${!loaded.value ? 'not loaded' : points.value.length < 2 ? 'insufficient points' : 'no uploadedFileId'}`
    )

    showError.value = true
    currentErrorMessage.value = t('message.loadGpxFirst')
    showUploadSuccess.value = false
    showSegmentSuccess.value = false
    return
  }

  // Validate that at least one surface type is selected
  if (trailConditions.value.surface_type.length === 0) {
    console.error('Form validation failed: no surface type selected')
    showError.value = true
    currentErrorMessage.value = t('message.surfaceTypeRequired')
    showUploadSuccess.value = false
    showSegmentSuccess.value = false
    return
  }

  submitting.value = true
  showError.value = false
  currentErrorMessage.value = ''
  message.value = ''
  try {
    const formData = new FormData()
    formData.append('name', name.value)
    formData.append('track_type', trackType.value)
    formData.append('tire_dry', trailConditions.value.tire_dry)
    formData.append('tire_wet', trailConditions.value.tire_wet)
    formData.append('surface_type', JSON.stringify(trailConditions.value.surface_type))
    formData.append(
      'difficulty_level',
      trailConditions.value.difficulty_level.toString()
    )

    // Add the start and end indices for GPX processing
    formData.append('start_index', startIndex.value.toString())
    formData.append('end_index', endIndex.value.toString())

    // Add the uploaded file ID instead of the file itself
    formData.append('file_id', uploadedFileId.value)

    // Add commentary data
    formData.append('commentary_text', commentary.value.text)
    formData.append('video_links', JSON.stringify(commentary.value.video_links))

    // Upload images to storage and collect their metadata
    const imageData = []
    for (const image of commentary.value.images) {
      if (!image.uploaded && image.file) {
        // Upload image to storage
        await uploadImageToStorage(image.file, image.id)

        // Find the updated image in the commentary
        const updatedImage = commentary.value.images.find((img) => img.id === image.id)
        if (updatedImage && updatedImage.uploaded) {
          imageData.push({
            image_id: updatedImage.image_id,
            image_url: updatedImage.image_url,
            storage_key: updatedImage.storage_key || '',
            filename: updatedImage.filename,
            original_filename: updatedImage.original_filename
          })
        }
      } else if (image.uploaded) {
        // Image was already uploaded (shouldn't happen with new flow, but keep for safety)
        imageData.push({
          image_id: image.image_id,
          image_url: image.image_url,
          storage_key: image.storage_key || '',
          filename: image.filename,
          original_filename: image.original_filename
        })
      }
    }
    formData.append('image_data', JSON.stringify(imageData))

    // Add strava_id if user is authenticated
    if (authState.value.isAuthenticated && authState.value.athlete?.id) {
      formData.append('strava_id', authState.value.athlete.id.toString())
    }

    const res = await fetch('/api/segments', { method: 'POST', body: formData })
    if (!res.ok) {
      const detail = await res.text()
      throw new Error(detail || 'Failed to create segment')
    }

    // For new segments, reset form fields to original state
    name.value = ''
    trailConditions.value = {
      tire_dry: 'slick',
      tire_wet: 'slick',
      surface_type: [],
      difficulty_level: 3
    }
    commentary.value = { text: '', video_links: [], images: [] }

    // Reset selection markers to start and end of file (preserve loaded state)
    startIndex.value = 0
    endIndex.value = points.value.length - 1

    // Reset update mode
    resetUpdateMode()

    // Update map and chart with new selection
    await nextTick()
    renderMap()

    // Show success message in info feed
    showSegmentSuccess.value = true
    showError.value = false
    currentErrorMessage.value = ''
    showUploadSuccess.value = false
  } catch (err: any) {
    showError.value = true
    currentErrorMessage.value = err.message || t('message.createError')
    showUploadSuccess.value = false
    showSegmentSuccess.value = false

    // Hide error after 5 seconds
    setTimeout(() => {
      showError.value = false
      currentErrorMessage.value = ''
    }, 5000)
  } finally {
    submitting.value = false
  }
}

async function onUpdate() {
  if (
    !loaded.value ||
    points.value.length < 2 ||
    !uploadedFileId.value ||
    !isUpdateMode.value
  ) {
    console.error(
      `Form validation failed: ${!loaded.value ? 'not loaded' : points.value.length < 2 ? 'insufficient points' : !uploadedFileId.value ? 'no uploadedFileId' : 'not in update mode'}`
    )

    showError.value = true
    currentErrorMessage.value = t('message.loadGpxFirst')
    showUploadSuccess.value = false
    showSegmentSuccess.value = false
    return
  }

  // Validate that at least one surface type is selected
  if (trailConditions.value.surface_type.length === 0) {
    console.error('Form validation failed: no surface type selected')
    showError.value = true
    currentErrorMessage.value = t('message.surfaceTypeRequired')
    showUploadSuccess.value = false
    showSegmentSuccess.value = false
    return
  }

  submitting.value = true
  showError.value = false
  currentErrorMessage.value = ''
  message.value = ''
  try {
    const formData = new FormData()
    formData.append('name', name.value)
    formData.append('track_type', trackType.value)
    formData.append('tire_dry', trailConditions.value.tire_dry)
    formData.append('tire_wet', trailConditions.value.tire_wet)
    formData.append('surface_type', JSON.stringify(trailConditions.value.surface_type))
    formData.append(
      'difficulty_level',
      trailConditions.value.difficulty_level.toString()
    )

    // Add the start and end indices for GPX processing
    formData.append('start_index', startIndex.value.toString())
    formData.append('end_index', endIndex.value.toString())

    // Add the uploaded file ID instead of the file itself
    formData.append('file_id', uploadedFileId.value)

    // Add commentary data
    formData.append('commentary_text', commentary.value.text)
    formData.append('video_links', JSON.stringify(commentary.value.video_links))

    // Upload images to storage and collect their metadata
    const imageData = []
    for (const image of commentary.value.images) {
      if (!image.uploaded && image.file) {
        // Upload image to storage
        await uploadImageToStorage(image.file, image.id)

        // Find the updated image in the commentary
        const updatedImage = commentary.value.images.find((img) => img.id === image.id)
        if (updatedImage && updatedImage.uploaded) {
          imageData.push({
            image_id: updatedImage.image_id,
            image_url: updatedImage.image_url,
            storage_key: updatedImage.storage_key || '',
            filename: updatedImage.filename,
            original_filename: updatedImage.original_filename
          })
        }
      } else if (image.uploaded) {
        // Image was already uploaded (shouldn't happen with new flow, but keep for safety)
        imageData.push({
          image_id: image.image_id,
          image_url: image.image_url,
          storage_key: image.storage_key || '',
          filename: image.filename,
          original_filename: image.original_filename
        })
      }
    }
    formData.append('image_data', JSON.stringify(imageData))

    // Add strava_id if user is authenticated
    if (authState.value.isAuthenticated && authState.value.athlete?.id) {
      formData.append('strava_id', authState.value.athlete.id.toString())
    }

    const res = await fetch(`/api/segments/${updatingSegmentId.value}`, {
      method: 'PUT',
      body: formData
    })
    if (!res.ok) {
      const detail = await res.text()
      throw new Error(detail || 'Failed to update segment')
    }

    // For updates, just show success message without resetting form
    showSegmentSuccess.value = true
    showError.value = false
    currentErrorMessage.value = ''
    showUploadSuccess.value = false

    // Update map and chart with current selection
    await nextTick()
    renderMap()

    // Reset update mode
    resetUpdateMode()
  } catch (err: any) {
    showError.value = true
    currentErrorMessage.value = err.message || t('message.updateError')
    showUploadSuccess.value = false
    showSegmentSuccess.value = false

    // Hide error after 5 seconds
    setTimeout(() => {
      showError.value = false
      currentErrorMessage.value = ''
    }, 5000)
  } finally {
    submitting.value = false
  }
}

async function onDeleteFromDb() {
  if (!loaded.value || !isUpdateMode.value || !updatingSegmentId.value) {
    console.error(
      `Delete validation failed: ${!loaded.value ? 'not loaded' : !isUpdateMode.value ? 'not in update mode' : 'no updatingSegmentId'}`
    )

    showError.value = true
    currentErrorMessage.value = t('message.loadGpxFirst')
    showUploadSuccess.value = false
    showSegmentSuccess.value = false
    return
  }

  // Show confirmation dialog
  const confirmed = confirm(t('message.confirmDelete', { name: name.value }))

  if (!confirmed) {
    return
  }

  submitting.value = true
  showError.value = false
  currentErrorMessage.value = ''
  message.value = ''

  try {
    const response = await fetch(`/api/segments/${updatingSegmentId.value}`, {
      method: 'DELETE'
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(error || 'Failed to delete segment')
    }

    const result = await response.json()
    console.info('Segment deleted successfully:', result)

    // Reset the editor state
    loaded.value = false
    name.value = ''
    points.value = []
    cumulativeKm.value = []
    cumulativeSec.value = []
    startIndex.value = 0
    endIndex.value = 0
    uploadedFileId.value = null
    trailConditions.value = {
      tire_dry: 'slick',
      tire_wet: 'slick',
      surface_type: [],
      difficulty_level: 3
    }
    commentary.value = { text: '', video_links: [], images: [] }

    // Reset update mode
    resetUpdateMode()

    // Clear map and chart
    if (map) {
      map.remove()
      map = null
    }

    // Show success message
    showSegmentSuccess.value = true
    showError.value = false
    currentErrorMessage.value = ''
    showUploadSuccess.value = false

    // Hide success message after 3 seconds
    setTimeout(() => {
      showSegmentSuccess.value = false
    }, 3000)
  } catch (err: any) {
    showError.value = true
    currentErrorMessage.value = err.message || t('message.deleteError')
    showUploadSuccess.value = false
    showSegmentSuccess.value = false

    // Hide error after 5 seconds
    setTimeout(() => {
      showError.value = false
      currentErrorMessage.value = ''
    }, 5000)
  } finally {
    submitting.value = false
  }
}

// Function to reset update mode (called when loading new files)
function resetUpdateMode() {
  isUpdateMode.value = false
  updatingSegmentId.value = null
}

// Function to create a temporary GPX file from current editor state
async function createTemporaryGPXFile(fileId: string): Promise<string> {
  if (!points.value.length) {
    throw new Error('No points available to create GPX file')
  }

  // Create GPX structure
  const gpxContent = `<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Gravly Editor" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <name>${name.value || 'Imported Segment'}</name>
    <trkseg>
${points.value
  .map(
    (point) => `      <trkpt lat="${point.latitude}" lon="${point.longitude}">
        <ele>${point.elevation}</ele>
        ${point.time ? `<time>${point.time}</time>` : ''}
      </trkpt>`
  )
  .join('\n')}
    </trkseg>
  </trk>
</gpx>`

  // Create a temporary file and upload it
  const tempFile = new File([gpxContent], `${fileId}.gpx`, {
    type: 'application/gpx+xml'
  })

  try {
    const formData = new FormData()
    formData.append('file', tempFile)

    const response = await fetch('/api/upload-gpx', {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      const detail = await response.text()
      throw new Error(detail || 'Failed to upload temporary GPX file')
    }

    const result = await response.json()
    console.info(`Temporary GPX file created: ${result.file_id}`)
    // Return the actual file_id from the backend
    return result.file_id
  } catch (error) {
    console.error('Error creating temporary GPX file:', error)
    throw error
  }
}
</script>

<style>
:root {
  --brand-50: #ffe6d5ff;
  --brand-100: #ffccaaff;
  --brand-200: #ffb380ff;
  --brand-300: #ff9955ff;
  --brand-400: #ff7f2aff;
  --brand-500: #ff6600ff;
  --brand-600: #e65c00ff;

  --brand-primary: var(--brand-500);
  --brand-primary-hover: #e65c00;
  --brand-accent: var(--brand-300);
  --blue-50: #eff6ff;
  --blue-100: #dbeafe;
  --blue-200: #bfdbfe;
  --blue-300: #93c5fd;
  --blue-400: #60a5fa;
  --blue-500: #3b82f6;
  --blue-600: #2563eb;
  --blue-700: #1d4ed8;
}
</style>

<style scoped>
.editor {
  display: flex;
  min-height: calc(100vh - 80px);
  background: #f8fafc;
  overflow-x: hidden;
  position: relative;
}
.content {
  flex: 1 1 auto;
  padding: 1rem 1.5rem;
  width: 100%;
  box-sizing: border-box;
  overflow-x: hidden;
  margin-left: var(--sidebar-w, 230px);
  transition: margin-left 0.3s ease;
}
.page {
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
  overflow-x: hidden;
}
.main-col {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  min-width: 0;
  overflow: hidden;
}

.sidebar {
  --sidebar-w: 230px;
  --sidebar-w-compact: 120px;
  width: var(--sidebar-w);
  background: transparent;
  border-right: none;
  padding: 0;
  margin: 0;
  box-sizing: border-box;
  position: fixed;
  top: var(--navbar-height, 64px);
  left: 0;
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--navbar-height, 64px));
  z-index: 100;
  transition:
    left 0.3s ease,
    width 0.3s ease;
}

.sidebar.compact {
  --sidebar-w: var(--sidebar-w-compact);
  width: var(--sidebar-w-compact);
}

.sidebar.collapsed {
  --sidebar-w: 50px;
  width: 50px;
}
.sidebar-scroll {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.75rem;
  max-height: calc(100vh - var(--navbar-height, 56px));
  overflow-y: auto;
  overflow-x: hidden;
  padding: 1rem;
}
.sidebar .card {
  margin: 0;
  width: 100%;
  box-sizing: border-box;
}

.menu-card {
  padding: 0.5rem 0;
  position: sticky;
  top: 0;
  background: #ffffff;
  z-index: 10;
}
.menu-section {
  margin-top: 0.5rem;
}
.menu-section + .menu-section {
  margin-top: 0.25rem;
  padding-top: 0.25rem;
  border-top: 1px solid #f1f5f9;
}
.menu-section-title {
  margin: 0.25rem 0 0.25rem;
  padding: 0 0.75rem;
  font-size: 1rem;
  font-weight: 400;
  color: #6b7280;
  text-align: left;
}
.menu-list {
  list-style: none;
  margin: 0;
  padding: 0.1rem 0.25rem 0.25rem;
}
.menu-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.4rem 0.6rem 0.4rem 0.75rem;
  margin: 0.1rem 0.35rem;
  border-radius: 8px;
  cursor: pointer;
  color: #111827;
  user-select: none;
}
.menu-item .icon {
  width: 20px;
  text-align: center;
  opacity: 0.9;
}
.menu-item .text {
  font-size: 0.8rem;
}
.menu-item:hover {
  background: #f3f4f6;
}
.menu-item:active {
  background: #e5e7eb;
}
.menu-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: transparent;
}
.menu-item.disabled:hover {
  background: transparent;
}
.menu-item.active {
  background: var(--brand-50);
  color: var(--brand-600);
  font-weight: 500;
}
.menu-item.active:hover {
  background: var(--brand-100);
}

.menu-item.danger {
  color: #dc2626;
}

.menu-item.danger:hover {
  background: #fef2f2;
  color: #b91c1c;
}

.menu-item.danger:active {
  background: #fee2e2;
}

.menu-item.danger.disabled {
  color: #9ca3af;
}

.menu-item.danger.disabled:hover {
  background: transparent;
  color: #9ca3af;
}

/* Import Dropdown Styles */
.menu-item.dropdown-trigger {
  position: relative;
}

.dropdown-arrow {
  margin-left: auto;
  font-size: 0.75rem;
  transition: transform 0.2s ease;
  opacity: 0.7;
}

.dropdown-arrow .fa-chevron-down.rotated {
  transform: rotate(180deg);
}

.import-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 1000;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow:
    0 4px 6px -1px rgba(0, 0, 0, 0.1),
    0 2px 4px -1px rgba(0, 0, 0, 0.06);
  margin-top: 4px;
}

.dropdown-menu {
  list-style: none;
  margin: 0;
  padding: 0.25rem 0;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.4rem 0.6rem 0.4rem 0.75rem;
  margin: 0.1rem 0.35rem;
  border-radius: 6px;
  cursor: pointer;
  color: #111827;
  user-select: none;
  transition: all 0.2s ease;
}

.dropdown-item:hover {
  background: #f3f4f6;
}

.dropdown-item:active {
  background: #e5e7eb;
}

.dropdown-item .icon {
  width: 20px;
  text-align: center;
  opacity: 0.9;
}

.dropdown-item .text {
  font-size: 0.8rem;
}

/* Compact sidebar styles */
.sidebar.compact .menu-item {
  justify-content: center;
  padding: 0.5rem;
  margin: 0.1rem 0.25rem;
  min-height: 36px;
  aspect-ratio: 1;
}

.sidebar.compact .menu-item .icon {
  width: 20px;
  text-align: center;
  opacity: 0.9;
}

.sidebar.compact .menu-item .text {
  display: none;
}

.sidebar.compact .menu-section {
  margin-top: 0.25rem;
}

.sidebar.compact .menu-section + .menu-section {
  margin-top: 0.1rem;
  padding-top: 0.1rem;
}

.sidebar.compact .menu-section-title {
  display: none;
}

.sidebar.compact .menu-list {
  padding: 0.1rem 0;
}

.sidebar.compact .info-feed-item {
  justify-content: center;
  padding: 0.5rem;
  margin: 0.1rem 0.25rem;
  min-height: 36px;
  aspect-ratio: 1;
}

.sidebar.compact .info-feed-content {
  display: none;
}

.sidebar.compact .info-feed-icon {
  font-size: 1.2rem;
}

/* Sidebar Toggle Button - Only visible on compact sidebar */
.sidebar-toggle {
  position: absolute;
  bottom: 0.75rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 20;
}

.toggle-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  background: var(--brand-500);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

.toggle-btn:hover {
  background: var(--brand-600);
  transform: scale(1.05);
}

.toggle-btn:active {
  transform: scale(0.95);
}

/* Collapsed sidebar styles */
.sidebar.collapsed .sidebar-scroll {
  display: none;
}

.sidebar.collapsed {
  --sidebar-w: 40px;
  width: 40px;
  z-index: 1000;
}

.sidebar.collapsed .sidebar-toggle {
  position: fixed;
  top: 50%;
  left: 0;
  transform: translateY(-50%);
  z-index: 1001;
}

.sidebar.collapsed .toggle-btn {
  width: 40px;
  height: 40px;
  border-radius: 0 8px 8px 0;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

/* Content adjustment for collapsed sidebar */
.sidebar.collapsed + .content {
  margin-left: 0;
  max-width: 100%;
}

.language-dropdown {
  position: relative;
}

.language-flag {
  font-size: 1.1em;
  line-height: 1;
}

.language-name {
  flex: 1;
  white-space: nowrap;
}

.dropdown-arrow {
  font-size: 0.75em;
  transition: transform 0.2s ease;
  opacity: 0.7;
}

.dropdown-arrow .fa-chevron-down.rotated {
  transform: rotate(180deg);
}

.language-option {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border: none;
  background: transparent;
  cursor: pointer;
  color: #374151;
  font-size: 0.875rem;
  text-align: left;
  transition: all 0.2s ease;
  border-radius: 0;
}

.language-option:first-child {
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
}

.language-option:last-child {
  border-bottom-left-radius: 8px;
  border-bottom-right-radius: 8px;
}

.language-option:hover {
  background: #f9fafb;
  color: #111827;
}

.language-option.active {
  background: var(--brand-50);
  color: var(--brand-600);
  font-weight: 500;
}

.language-option.active:hover {
  background: var(--brand-100);
}

.language-option .language-flag {
  font-size: 1.1em;
}

.language-option .language-name {
  flex: 1;
}

.checkmark {
  font-size: 0.75em;
  color: var(--brand-500);
}

.card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
  padding: 0.75rem;
  width: 100%;
  box-sizing: border-box;
}
.card-map {
  padding: 0;
  overflow: hidden;
}
.card-elevation {
  padding: 0.75rem;
  overflow: visible;
  margin-top: 1rem;
  margin-bottom: 1rem;
}
.map {
  height: 480px;
  width: 100%;
}
.empty {
  padding: 2rem;
  text-align: center;
  color: #666;
}
.message {
  margin-top: 1rem;
}

/* Info Feed Styles - Integrated in Menu */
.info-feed-section {
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid #f1f5f9;
}

.info-feed-item {
  padding: 0.75rem;
  border-radius: 6px;
  margin: 0 0.25rem 0.5rem 0.25rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
}

.info-feed-icon {
  font-size: 1rem;
  flex-shrink: 0;
}

.info-feed-content {
  flex: 1;
  min-width: 0;
}

.info-feed-text {
  font-size: 0.75rem;
  font-weight: 500;
  line-height: 1.2;
}

/* Upload Progress Item */
.upload-progress-item {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.upload-progress-item .info-feed-icon {
  color: #ff6600;
}

.upload-progress-item .info-feed-text {
  color: #475569;
}

.upload-progress-bar {
  width: 100%;
  height: 6px;
  background-color: #e2e8f0;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.upload-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff6600, #ff8533);
  border-radius: 3px;
  transition: width 0.3s ease;
  box-shadow: 0 1px 2px rgba(255, 102, 0, 0.2);
}

/* Success Item */
.success-item {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
}

.success-item .info-feed-icon {
  color: #16a34a;
}

.success-item .info-feed-text {
  color: #15803d;
}

/* Upload Success Item (Blue) */
.upload-success-item {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
}

.upload-success-item .info-feed-icon {
  color: #2563eb;
}

.upload-success-item .info-feed-text {
  color: #1d4ed8;
}

/* Error Item */
.error-item {
  background: #fef2f2;
  border: 1px solid #fecaca;
}

.error-item .info-feed-icon {
  color: #dc2626;
}

.error-item .info-feed-text {
  color: #b91c1c;
}

/* Empty Item */
.empty-item {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.empty-item .info-feed-icon {
  color: #64748b;
}

.empty-item .info-feed-text {
  color: #64748b;
}

/* Responsive content to ensure sidebar visibility */
@media (max-width: 1450px) {
  .content {
    margin-left: 210px;
  }

}

/* Responsive layout for screens under 1000px */
@media (max-width: 999px) {
  .main-col {
    width: 100%;
    max-width: 100%;
  }

  .page {
    max-width: 100%;
    padding: 0 1rem;
  }

  .content {
    margin-left: 0;
    padding: 1rem 0.5rem;
  }

  /* Ensure all cards take full width */
  .card {
    width: 100%;
    max-width: 100%;
  }

  /* Stack all form elements vertically */
  .trail-conditions-card,
  .meta,
  .card-map,
  .card-elevation {
    width: 100%;
    margin-bottom: 1rem;
  }
}

/* Compact sidebar for screens under 1100px */
@media (max-width: 1099px) {
  .sidebar {
    --sidebar-w: 120px;
    width: 120px;
  }

  .content {
    margin-left: 100px;
  }

  .sidebar.collapsed {
    --sidebar-w: 40px;
    width: 40px;
  }

  .sidebar.collapsed + .content {
    margin-left: 0;
    max-width: 100%;
  }
}

/* Hide toggle button on larger screens */
@media (min-width: 1100px) {
  .sidebar-toggle {
    display: none;
  }
}

/* For very large screens, ensure sidebar is positioned relative to content */
@media (min-width: 1700px) {
  .sidebar {
    left: calc(50% - 590px - 230px);
  }

  .content {
    margin-left: 230px;
  }
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: white;
  border-radius: 12px;
  box-shadow:
    0 20px 25px -5px rgba(0, 0, 0, 0.1),
    0 10px 10px -5px rgba(0, 0, 0, 0.04);
  max-width: 90vw;
  max-height: 90vh;
  width: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

@media (min-width: 768px) {
  .modal-content {
    max-width: 800px;
    max-height: 600px;
  }
}
</style>
