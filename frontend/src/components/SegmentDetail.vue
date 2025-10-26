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
        <div class="header-actions">
          <!-- Actions dropdown - available for both routes and segments -->
          <div class="dropdown-container">
            <button @click="toggleExportMenu" class="export-button" ref="exportButton">
              <i class="fa-solid fa-ellipsis-vertical"></i>
              <span>{{ t('segmentDetail.actions') }}</span>
              <i class="fa-solid fa-chevron-down dropdown-icon"></i>
            </button>
            <div v-if="showExportMenu" class="dropdown-menu" ref="exportMenu">
              <!-- General Actions Section -->
              <div v-if="hasGeneralActions" class="dropdown-section">
                <div class="dropdown-section-title">
                  <i class="fa-solid fa-list"></i>
                  {{ t('segmentDetail.actionsGeneral') }}
                </div>
                <button @click="shareLink" class="dropdown-item dropdown-item-indented">
                  <i class="fa-solid fa-share-nodes"></i>
                  {{ t('segmentDetail.shareLink') }}
                </button>
                <button
                  v-if="segment?.track_type === 'route'"
                  @click="downloadGPX"
                  class="dropdown-item dropdown-item-indented"
                >
                  <i class="fa-solid fa-download"></i>
                  {{ t('segmentDetail.downloadGPX') }}
                </button>
                <button
                  v-if="segment?.track_type === 'route'"
                  @click="handleUploadToWahoo"
                  class="dropdown-item dropdown-item-indented"
                  :disabled="isUploadingToWahoo || !wahooAuthState.isAuthenticated"
                  :title="
                    !wahooAuthState.isAuthenticated
                      ? t('segmentDetail.wahooNotConnectedTooltip')
                      : ''
                  "
                >
                  <i class="fa-solid fa-cloud-upload-alt"></i>
                  {{
                    isUploadingToWahoo
                      ? t('segmentDetail.uploadingToWahoo')
                      : t('segmentDetail.uploadToWahoo')
                  }}
                </button>
                <button
                  v-if="segment?.track_type === 'route'"
                  @click="showDeleteConfirmation"
                  class="dropdown-item dropdown-item-indented dropdown-item-danger"
                  :disabled="!isOwner"
                  :title="!isOwner ? t('segmentDetail.notRouteOwner') : ''"
                >
                  <i class="fa-solid fa-trash"></i>
                  {{ t('segmentDetail.deleteRoute') }}
                </button>
              </div>
            </div>
          </div>
          <button @click="goBack" class="back-button">
            <i class="fa-solid fa-arrow-left"></i>
            {{ t('segmentDetail.backToTrackFinder') }}
          </button>
        </div>
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
            <ElevationChart
              :gpx-data="gpxData"
              @chart-hover="updateCursorPositionFromChart"
            />
          </div>

          <!-- Segment Information Card -->
          <div class="info-section">
            <SegmentInfoCard :segment="segment" :gpx-data="gpxData" />
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

    <!-- Delete Confirmation Modal -->
    <div
      v-if="showDeleteConfirmModal"
      class="confirm-modal-overlay"
      @click="closeDeleteConfirmModal"
    >
      <div class="confirm-modal" @click.stop>
        <div class="confirm-modal-header">
          <h3>
            {{
              segment?.track_type === 'route'
                ? t('segmentDetail.deleteRoute')
                : t('segmentDetail.deleteSegment')
            }}
          </h3>
          <button class="confirm-modal-close" @click="closeDeleteConfirmModal">
            <i class="fa-solid fa-times"></i>
          </button>
        </div>
        <div class="confirm-modal-body">
          <p>
            {{
              segment?.track_type === 'route'
                ? t('segmentDetail.deleteRouteConfirm')
                : t('segmentDetail.deleteSegmentConfirm')
            }}
          </p>
        </div>
        <div class="confirm-modal-footer">
          <button
            @click="closeDeleteConfirmModal"
            class="btn-cancel"
            :disabled="isDeleting"
          >
            {{ t('common.cancel') }}
          </button>
          <button @click="confirmDelete" class="btn-delete" :disabled="isDeleting">
            <i v-if="isDeleting" class="fa-solid fa-spinner fa-spin"></i>
            {{ isDeleting ? t('common.deleting') : t('common.delete') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Wahoo Authorization Modal -->
    <div
      v-if="showWahooAuthModal"
      class="confirm-modal-overlay"
      @click="closeWahooAuthModal"
    >
      <div class="confirm-modal" @click.stop>
        <div class="confirm-modal-header">
          <h3>
            <i class="fa-solid fa-cloud"></i>
            {{ t('segmentDetail.wahooAuthModalTitle') }}
          </h3>
          <button class="confirm-modal-close" @click="closeWahooAuthModal">
            <i class="fa-solid fa-times"></i>
          </button>
        </div>
        <div class="confirm-modal-body">
          <p>{{ t('segmentDetail.wahooAuthModalMessage') }}</p>
        </div>
        <div class="confirm-modal-footer">
          <button
            @click="closeWahooAuthModal"
            class="btn-cancel"
            :disabled="isLoadingWahooAuth"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            @click="proceedWithWahooAuth"
            class="btn-primary-modal"
            :disabled="isLoadingWahooAuth"
          >
            <i v-if="isLoadingWahooAuth" class="fa-solid fa-spinner fa-spin"></i>
            {{ t('segmentDetail.wahooAuthButton') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Wahoo Upload Progress/Success/Error Modal -->
    <div
      v-if="showWahooUploadResultModal"
      class="confirm-modal-overlay"
      @click="closeWahooUploadResultModal"
    >
      <div class="confirm-modal" @click.stop>
        <div class="confirm-modal-header">
          <h3 class="confirm-modal-title">
            <i class="fa-solid fa-cloud"></i>
            {{ t('segmentDetail.uploadingToWahoo') }}
          </h3>
        </div>
        <div class="confirm-modal-body">
          <div class="wahoo-upload-status">
            <i
              class="fa-solid"
              :class="
                isUploadingToWahoo
                  ? 'fa-spinner fa-spin'
                  : wahooUploadError
                    ? 'fa-times-circle'
                    : 'fa-check-circle'
              "
              :style="{ color: '#f97316' }"
            ></i>
            <p>
              {{
                isUploadingToWahoo
                  ? t('segmentDetail.uploadingToWahooMessage')
                  : wahooUploadError || t('segmentDetail.uploadToWahooSuccess')
              }}
            </p>
          </div>
        </div>
        <div class="confirm-modal-footer">
          <button
            v-if="!isUploadingToWahoo"
            @click="closeWahooUploadResultModal"
            class="btn-primary-modal"
          >
            {{ t('common.ok') }}
          </button>
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
import type { TrackResponse, GPXData, TrackVideoResponse } from '../types'
import SegmentInfoCard from './SegmentInfoCard.vue'
import ElevationChart from './ElevationChart.vue'
import { useStravaApi } from '../composables/useStravaApi'
import { useWahooApi } from '../composables/useWahooApi'

const router = useRouter()
const route = useRoute()

// i18n
const { t } = useI18n()

// Authentication state
const { authState } = useStravaApi()

// Wahoo API
const {
  authState: wahooAuthState,
  getAuthUrl,
  uploadRoute: wahooUploadRoute
} = useWahooApi()

const isUploadingToWahoo = ref(false)

// Reactive data
const segment = ref<TrackResponse | null>(null)
const gpxData = ref<GPXData | null>(null)
const trackImages = ref<any[]>([])
const trackVideos = ref<TrackVideoResponse[]>([])
const selectedImage = ref<any>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const map = ref<any>(null)
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
const showExportMenu = ref(false) // State for export dropdown menu
const exportButton = ref<HTMLElement | null>(null)
const exportMenu = ref<HTMLElement | null>(null)
const showDeleteConfirmModal = ref(false) // State for delete confirmation modal
const isDeleting = ref(false) // State for delete operation

// Wahoo upload state
const showWahooAuthModal = ref(false) // State for Wahoo authorization modal
const showWahooUploadResultModal = ref(false) // State for upload result modal
const wahooUploadError = ref<string | null>(null) // Error message for upload result
const isLoadingWahooAuth = ref(false) // State for Wahoo authorization loading

// Current position tracking for cursor sync
const currentPosition = ref({
  lat: 0,
  lng: 0,
  distance: 0,
  elevation: 0
})

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

// Check if current user owns this route
const isOwner = computed(() => {
  if (!segment.value || !authState.value.isAuthenticated || !authState.value.athlete) {
    return false
  }
  return segment.value.strava_id === authState.value.athlete.id
})

// Check if there are any general actions to display
const hasGeneralActions = computed(() => {
  // Share link is always available
  const hasShare = true
  // Download GPX and delete are only available for routes
  const hasRouteActions = segment.value?.track_type === 'route'
  return hasShare || hasRouteActions
})

// Methods
function goBack() {
  router.push('/')
}

function toggleExportMenu() {
  showExportMenu.value = !showExportMenu.value
}

function closeExportMenu() {
  showExportMenu.value = false
}

function showDeleteConfirmation() {
  showDeleteConfirmModal.value = true
  closeExportMenu()
}

function closeDeleteConfirmModal() {
  showDeleteConfirmModal.value = false
}

async function confirmDelete() {
  if (!segment.value || !authState.value.isAuthenticated || !authState.value.athlete) {
    return
  }

  isDeleting.value = true

  const isRoute = segment.value.track_type === 'route'
  const successMessage = isRoute
    ? t('segmentDetail.deleteRouteSuccess')
    : t('segmentDetail.deleteSegmentSuccess')
  const errorMessage = isRoute
    ? t('segmentDetail.deleteRouteError')
    : t('segmentDetail.deleteSegmentError')

  try {
    const stravaId = authState.value.athlete.id
    const response = await fetch(
      `/api/segments/${segmentId.value}?user_strava_id=${stravaId}`,
      {
        method: 'DELETE'
      }
    )

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(errorText || errorMessage)
    }

    // Show success message (could be improved with a toast notification)
    alert(successMessage)

    // Close modal
    closeDeleteConfirmModal()

    // Redirect to explorer
    router.push('/explorer')
  } catch (err: any) {
    console.error('Error deleting:', err)
    alert(err.message || errorMessage)
  } finally {
    isDeleting.value = false
  }
}

async function shareLink() {
  if (!segment.value) return

  try {
    // Create the full URL for sharing
    const shareUrl = `${window.location.origin}/segment/${segmentId.value}`

    // Try using the Web Share API first (mobile devices and modern browsers)
    if (navigator.share) {
      try {
        await navigator.share({
          title: segment.value.name,
          text: `Check out this ${segment.value.track_type === 'route' ? 'route' : 'segment'}: ${segment.value.name}`,
          url: shareUrl
        })
        closeExportMenu()
        return
      } catch (err: any) {
        // User cancelled or share failed, fall back to clipboard
        if (err.name !== 'AbortError') {
          console.warn('Web Share API failed, falling back to clipboard:', err)
        } else {
          // User cancelled, just close the menu
          closeExportMenu()
          return
        }
      }
    }

    // Fallback: Copy to clipboard
    await navigator.clipboard.writeText(shareUrl)
    alert(t('segmentDetail.linkCopied'))
    closeExportMenu()
  } catch (err) {
    console.error('Error sharing link:', err)
    alert(t('segmentDetail.shareLinkError'))
  }
}

async function handleUploadToWahoo() {
  if (!segment.value) return

  closeExportMenu()

  // Check if authenticated with Wahoo
  if (!wahooAuthState.value.isAuthenticated) {
    // Show auth modal
    showWahooAuthModal.value = true
    return
  }

  // Show progress modal immediately
  wahooUploadError.value = null
  showWahooUploadResultModal.value = true
  isUploadingToWahoo.value = true

  // Upload to Wahoo
  try {
    await wahooUploadRoute(segmentId.value)
    // Upload successful - modal will show success state
  } catch (error: any) {
    console.error('Error uploading to Wahoo:', error)
    wahooUploadError.value = error.message || t('segmentDetail.uploadToWahooError')
    // Modal will show error state
  } finally {
    isUploadingToWahoo.value = false
  }
}

function closeWahooAuthModal() {
  showWahooAuthModal.value = false
}

async function proceedWithWahooAuth() {
  try {
    isLoadingWahooAuth.value = true
    const authUrl = await getAuthUrl()
    // Store current URL to redirect back after auth
    sessionStorage.setItem('wahoo_redirect_after_auth', `/segment/${segmentId.value}`)
    window.location.href = authUrl
  } catch (error) {
    console.error('Error getting Wahoo auth URL:', error)
    wahooUploadError.value = t('segmentDetail.wahooAuthError')
    showWahooAuthModal.value = false
    showWahooUploadResultModal.value = true
  } finally {
    isLoadingWahooAuth.value = false
  }
}

function closeWahooUploadResultModal() {
  showWahooUploadResultModal.value = false
  wahooUploadError.value = null
}

async function downloadGPX() {
  if (!segment.value) return

  try {
    // Fetch GPX XML data from backend
    const response = await fetch(`/api/segments/${segmentId.value}/gpx`)
    if (!response.ok) {
      throw new Error('Failed to fetch GPX data')
    }

    const data = await response.json()
    const gpxXmlData = data.gpx_xml_data

    // Create a Blob from the GPX XML data
    const blob = new Blob([gpxXmlData], { type: 'application/gpx+xml' })

    // Create a sanitized filename from the segment name
    const sanitizedName = segment.value.name.replace(/[^a-z0-9]/gi, '_').toLowerCase()
    const suggestedFileName = `${sanitizedName}.gpx`

    // Try using the File System Access API (modern browsers)
    if ('showSaveFilePicker' in window) {
      try {
        const handle = await (window as any).showSaveFilePicker({
          suggestedName: suggestedFileName,
          types: [
            {
              description: 'GPX Files',
              accept: { 'application/gpx+xml': ['.gpx'] }
            }
          ]
        })

        const writable = await handle.createWritable()
        await writable.write(blob)
        await writable.close()

        closeExportMenu()
        return
      } catch (err: any) {
        // User cancelled or browser doesn't support it
        if (err.name !== 'AbortError') {
          console.warn('File System Access API failed, falling back to download:', err)
        } else {
          // User cancelled, just close the menu
          closeExportMenu()
          return
        }
      }
    }

    // Fallback: Create a download link
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = suggestedFileName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    closeExportMenu()
  } catch (err) {
    console.error('Error downloading GPX file:', err)
    alert('Failed to download GPX file. Please try again.')
  }
}

function handleClickOutside(event: MouseEvent) {
  if (
    showExportMenu.value &&
    exportButton.value &&
    exportMenu.value &&
    !exportButton.value.contains(event.target as Node) &&
    !exportMenu.value.contains(event.target as Node)
  ) {
    closeExportMenu()
  }
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
    const segmentResponse = await fetch(`/api/segments/${segmentId.value}`)
    if (!segmentResponse.ok) {
      throw new Error(`Failed to load segment: ${segmentResponse.statusText}`)
    }
    segment.value = await segmentResponse.json()

    // Load parsed GPX data directly from backend
    const gpxResponse = await fetch(`/api/segments/${segmentId.value}/data`)
    if (!gpxResponse.ok) {
      throw new Error(`Failed to load GPX data: ${gpxResponse.statusText}`)
    }
    gpxData.value = await gpxResponse.json()

    if (!gpxData.value) {
      throw new Error('Failed to load GPX data')
    }

    // Load track images
    const imagesResponse = await fetch(`/api/segments/${segmentId.value}/images`)
    if (imagesResponse.ok) {
      trackImages.value = await imagesResponse.json()
    } else {
      // Images are optional, so don't throw error if they fail to load
      console.warn('Failed to load track images:', imagesResponse.statusText)
      trackImages.value = []
    }

    // Load track videos
    const videosResponse = await fetch(`/api/segments/${segmentId.value}/videos`)
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
      color: 'var(--brand-primary)',
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
          fillColor: 'var(--brand-primary)',
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
  document.addEventListener('click', handleClickOutside)
  window.addEventListener('resize', updateImagesPerView)
  window.addEventListener('resize', updateVideosPerView)
  updateImagesPerView()
  updateVideosPerView()
})

onUnmounted(() => {
  if (map.value) {
    map.value.remove()
  }
  if (mapMarker.value) {
    mapMarker.value.remove()
  }
  document.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('resize', updateImagesPerView)
  window.removeEventListener('resize', updateVideosPerView)
})
</script>

<style scoped>
.segment-detail {
  height: calc(100vh - var(--navbar-height, 60px));
  background: var(--bg-secondary);
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
  color: var(--brand-primary);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.dropdown-container {
  position: relative;
}

.export-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: var(--brand-primary);
  border: 1px solid var(--brand-primary);
  border-radius: 8px;
  color: #ffffff;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s;
  cursor: pointer;
}

.export-button:hover {
  background: var(--brand-primary-hover, #0ea5e9);
  border-color: var(--brand-primary-hover, #0ea5e9);
}

.export-button .dropdown-icon {
  font-size: 0.75rem;
  margin-left: 0.25rem;
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 0.5rem);
  left: 0;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 8px;
  box-shadow: var(--shadow-lg);
  min-width: 200px;
  z-index: 1000;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.dropdown-section {
  display: flex;
  flex-direction: column;
}

.dropdown-section:not(:last-child) {
  border-bottom: 1px solid var(--border-muted);
  padding-bottom: 0.5rem;
  margin-bottom: 0.5rem;
}

.dropdown-section-title {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.5rem 1rem 0.25rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.dropdown-section-title i {
  font-size: 0.875rem;
  color: var(--brand-primary);
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.75rem 1rem;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 0.875rem;
  font-weight: 500;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s;
}

.dropdown-item:hover {
  background: var(--bg-hover);
  color: var(--brand-primary);
}

.dropdown-item i {
  color: var(--text-tertiary);
  font-size: 1rem;
}

.dropdown-item:hover i {
  color: var(--brand-primary);
}

.dropdown-item:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: transparent;
}

.dropdown-item:disabled:hover {
  background: transparent;
  color: var(--text-primary);
}

.dropdown-item:disabled:hover i {
  color: var(--text-tertiary);
}

.dropdown-item-danger {
  color: var(--status-error);
}

.dropdown-item-danger:hover {
  background: rgba(var(--status-error-rgb), 0.1);
  color: var(--status-error);
}

.dropdown-item-danger i {
  color: var(--status-error);
}

.dropdown-item-danger:hover i {
  color: var(--status-error);
}

.dropdown-item-indented {
  padding-left: 2rem;
}

.back-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 8px;
  color: var(--text-primary);
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s;
  cursor: pointer;
}

.back-button:hover {
  background: var(--bg-hover);
  border-color: var(--border-primary);
}

/* Hide text on small screens, show only icon */
@media (max-width: 850px) {
  .export-button span {
    display: none;
  }

  .export-button {
    padding: 0.75rem;
    min-width: auto;
  }

  .export-button .dropdown-icon {
    display: none;
  }

  .dropdown-menu {
    left: auto;
    right: 0;
  }

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
  color: var(--text-primary);
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
  background: var(--card-bg);
  border-radius: 12px;
  box-shadow: var(--shadow-md);
}

.loading-spinner i {
  font-size: 1.5rem;
  color: var(--brand-primary);
}

.error-message i {
  font-size: 1.5rem;
  color: var(--status-error);
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
  grid-template-rows: 400px 300px;
  gap: 1rem;
  flex: 1;
  width: 100%;
  box-sizing: border-box;
  grid-template-areas:
    'map info'
    'elevation elevation';
}

/* Dynamic grid layout when comments are present */
.content-grid.with-comments {
  grid-template-rows: 400px 300px auto;
  grid-template-areas:
    'map info'
    'elevation elevation'
    'comments comments';
}

/* Dynamic grid layout when images are present */
.content-grid.with-images {
  grid-template-rows: 400px 300px auto;
  grid-template-areas:
    'map info'
    'elevation elevation'
    'images images';
}

/* Dynamic grid layout when both comments and images are present */
.content-grid.with-comments.with-images {
  grid-template-rows: 400px 300px auto auto;
  grid-template-areas:
    'map info'
    'elevation elevation'
    'comments comments'
    'images images';
}

/* Dynamic grid layout when videos are present */
.content-grid.with-videos {
  grid-template-rows: 400px 300px auto;
  grid-template-areas:
    'map info'
    'elevation elevation'
    'videos videos';
}

/* Dynamic grid layout when comments and videos are present */
.content-grid.with-comments.with-videos {
  grid-template-rows: 400px 300px auto auto;
  grid-template-areas:
    'map info'
    'elevation elevation'
    'comments comments'
    'videos videos';
}

/* Dynamic grid layout when images and videos are present */
.content-grid.with-images.with-videos {
  grid-template-rows: 400px 300px auto auto;
  grid-template-areas:
    'map info'
    'elevation elevation'
    'images images'
    'videos videos';
}

/* Dynamic grid layout when comments, images and videos are present */
.content-grid.with-comments.with-images.with-videos {
  grid-template-rows: 400px 300px auto auto auto;
  grid-template-areas:
    'map info'
    'elevation elevation'
    'comments comments'
    'images images'
    'videos videos';
}

.map-section {
  grid-area: map;
  min-width: 0;
  overflow: hidden;
}

.chart-section {
  grid-area: elevation;
  min-height: 250px;
  min-width: 0;
  overflow: hidden;
}

.info-section {
  grid-area: info;
  min-width: 0;
  overflow: hidden;
}

.comments-section {
  grid-area: comments;
  min-width: 0;
  overflow: hidden;
}

/* Responsive layout adjustments */
@media (max-width: 768px) {
  .segment-detail {
    overflow-y: auto; /* Enable vertical scrolling on small devices */
  }

  .content-grid {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto;
    grid-template-areas:
      'map'
      'elevation'
      'info';
    gap: 1.5rem; /* Increase gap for better spacing when stacked */
  }

  .content-grid.with-comments {
    grid-template-rows: auto auto auto auto;
    grid-template-areas:
      'map'
      'elevation'
      'info'
      'comments';
  }

  .content-grid.with-images {
    grid-template-rows: auto auto auto auto;
    grid-template-areas:
      'map'
      'elevation'
      'info'
      'images';
  }

  .content-grid.with-comments.with-images {
    grid-template-rows: auto auto auto auto auto;
    grid-template-areas:
      'map'
      'elevation'
      'info'
      'comments'
      'images';
  }

  .content-grid.with-videos {
    grid-template-rows: auto auto auto auto;
    grid-template-areas:
      'map'
      'elevation'
      'info'
      'videos';
  }

  .content-grid.with-comments.with-videos {
    grid-template-rows: auto auto auto auto auto;
    grid-template-areas:
      'map'
      'elevation'
      'info'
      'comments'
      'videos';
  }

  .content-grid.with-images.with-videos {
    grid-template-rows: auto auto auto auto auto;
    grid-template-areas:
      'map'
      'elevation'
      'info'
      'images'
      'videos';
  }

  .content-grid.with-comments.with-images.with-videos {
    grid-template-rows: auto auto auto auto auto auto;
    grid-template-areas:
      'map'
      'elevation'
      'info'
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
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  box-shadow: var(--card-shadow);
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
  width: 100%;
  box-sizing: border-box;
}

.card-header {
  padding: 0.75rem 1.5rem;
  border-bottom: 1px solid var(--border-muted);
  background: var(--bg-secondary);
}

.card-header h3 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.card-header i {
  color: var(--brand-primary);
}

.card-content {
  padding: 1.5rem;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  width: 100%;
  box-sizing: border-box;
}

.map {
  height: 100%;
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  flex: 1;
  min-height: 200px; /* Fallback minimum height */
}

/* Comments Section Styles */
.comments-content {
  padding: 1rem;
  width: 100%;
  box-sizing: border-box;
}

.comment-text {
  font-size: 1rem;
  line-height: 1.6;
  color: var(--text-primary);
  background: var(--bg-secondary);
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid var(--border-muted);
  white-space: pre-wrap; /* Preserve line breaks and format text */
}

/* Images Gallery Styles */
.images-section {
  grid-area: images;
  min-width: 0;
  overflow: hidden;
}

.images-carousel {
  position: relative;
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

.images-gallery {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  flex: 1;
  overflow: hidden;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.carousel-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: var(--card-bg);
  border: 1px solid var(--border-secondary);
  border-radius: 50%;
  width: 2.5rem;
  height: 2.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  z-index: 10;
  box-shadow: var(--shadow-sm);
}

.carousel-btn:hover {
  background: var(--bg-hover);
  border-color: var(--brand-primary);
  box-shadow: var(--shadow-md);
}

.carousel-btn i {
  color: var(--text-primary);
  font-size: 0.875rem;
}

.carousel-btn:hover i {
  color: var(--brand-primary);
}

.carousel-btn-left {
  left: 0.25rem;
}

.carousel-btn-right {
  right: 0.25rem;
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
  min-width: 0;
  overflow: hidden;
}

.videos-carousel {
  position: relative;
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

.videos-gallery {
  display: flex;
  justify-content: space-evenly;
  align-items: center;
  flex: 1;
  overflow: hidden;
  padding: 0 1rem;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.video-item {
  display: flex;
  flex-direction: column;
  border-radius: 8px;
  flex: 1;
  min-width: 0; /* Allow flex items to shrink below their content size */
  max-width: 400px; /* Maximum width to prevent items from becoming too large */
  overflow: hidden;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  transition: box-shadow 0.2s ease;
}

.video-item:hover {
  box-shadow: var(--shadow-md);
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
  background: var(--bg-secondary);
  color: var(--text-tertiary);
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
    max-width: 300px; /* Maximum width for 2 videos on medium screens */
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
  border-top: 1px solid var(--border-muted);
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
  background: var(--card-bg);
  border: 1px solid var(--border-secondary);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.pagination-btn:hover:not(:disabled) {
  background: var(--bg-hover);
  border-color: var(--border-primary);
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--bg-secondary);
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
  background: var(--card-bg);
  border: 1px solid var(--border-secondary);
  border-radius: 4px;
  color: var(--text-primary);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.pagination-page:hover {
  background: var(--bg-hover);
  border-color: var(--border-primary);
}

.pagination-page.active {
  background: var(--brand-primary);
  border-color: var(--brand-primary);
  color: #ffffff;
}

.pagination-page.active:hover {
  background: var(--brand-primary-hover);
  border-color: var(--brand-primary-hover);
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
    max-width: 280px; /* Maximum width for 1 video on small screens */
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

/* Confirmation Modal Styles */
.confirm-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.confirm-modal {
  background: var(--card-bg);
  border-radius: 12px;
  box-shadow: var(--shadow-xl);
  max-width: 500px;
  width: 100%;
  overflow: hidden;
}

.confirm-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid var(--card-border);
  background: var(--bg-secondary);
}

.confirm-modal-header h3,
.confirm-modal-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
}

.confirm-modal-title i {
  color: var(--brand-primary);
}

.confirm-modal-close {
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}

.confirm-modal-close:hover {
  color: var(--text-primary);
}

.confirm-modal-header.error-header {
  border-left: 4px solid var(--status-error);
}

.confirm-modal-header.error-header h3 {
  color: var(--status-error);
}

.btn-primary-modal {
  padding: 0.625rem 1.25rem;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid;
  background: var(--brand-primary);
  color: #ffffff;
  border-color: var(--brand-primary);
}

.btn-primary-modal:hover:not(:disabled) {
  background: var(--brand-primary-hover);
  border-color: var(--brand-primary-hover);
}

.confirm-modal-body {
  padding: 1.5rem;
  background: var(--bg-tertiary);
}

.confirm-modal-body p {
  margin: 0;
  color: var(--text-primary);
  line-height: 1.6;
}

.wahoo-upload-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  text-align: center;
}

.wahoo-upload-status i {
  font-size: 3rem;
}

.wahoo-upload-status p {
  margin: 0;
  color: var(--text-primary);
  line-height: 1.6;
}

.confirm-modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1.5rem;
  border-top: 1px solid var(--card-border);
  background: var(--bg-tertiary);
}

.btn-cancel,
.btn-delete {
  padding: 0.625rem 1.25rem;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-cancel {
  background: var(--card-bg);
  color: var(--text-primary);
  border-color: var(--border-secondary);
}

.btn-cancel:hover:not(:disabled) {
  background: var(--bg-hover);
  border-color: var(--border-primary);
}

.btn-delete {
  background: var(--status-error);
  color: #ffffff;
  border-color: var(--status-error);
}

.btn-delete:hover:not(:disabled) {
  background: var(--button-danger-hover);
  border-color: var(--button-danger-hover);
}

.btn-cancel:disabled,
.btn-delete:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 620px) {
  .confirm-modal {
    margin: 0 0.5rem;
  }

  .confirm-modal-header,
  .confirm-modal-body,
  .confirm-modal-footer {
    padding: 1rem;
  }

  .confirm-modal-footer {
    flex-direction: column;
    gap: 0.5rem;
  }

  .btn-cancel,
  .btn-delete {
    width: 100%;
    justify-content: center;
  }
}
</style>
