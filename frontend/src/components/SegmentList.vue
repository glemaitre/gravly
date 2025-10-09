<template>
  <div class="segment-list">
    <!-- Filter Card -->
    <div class="filter-card">
      <!-- Sticky Track Type Tabs -->
      <div class="track-type-tabs">
        <button
          type="button"
          class="tab-button"
          :class="{ active: selectedTrackType === 'segment' }"
          @click="onTrackTypeChange('segment')"
        >
          <i class="fa-solid fa-route"></i>
          Segments
          <span class="info-tooltip" :title="t('trackType.segmentTooltip')">
            <i class="fa-solid fa-circle-info"></i>
          </span>
        </button>
        <button
          type="button"
          class="tab-button"
          :class="{ active: selectedTrackType === 'route' }"
          @click="onTrackTypeChange('route')"
        >
          <i class="fa-solid fa-map"></i>
          Routes
          <span
            v-if="!isAuthenticated()"
            class="warning-icon"
            :title="t('trackType.routeAuthWarning')"
          >
            <i class="fa-solid fa-triangle-exclamation"></i>
          </span>
          <span v-else class="info-tooltip" :title="t('trackType.routeTooltip')">
            <i class="fa-solid fa-circle-info"></i>
          </span>
        </button>
      </div>

      <!-- Scrollable Cards Container -->
      <div class="cards-container">
        <div
          v-if="segments.length > 0"
          class="segment-cards"
          :class="{
            'segment-cards--no-button': segments.length <= initialDisplayCount
          }"
        >
          <SegmentCard
            v-for="segment in displayedSegments"
            :key="segment.id"
            :segment="segment"
            :stats="segmentStats.get(segment.id)"
            :is-hovered="hoveredSegmentId === segment.id"
            :distance-from-center="getDistanceFromCenter?.(segment)"
            @click="onSegmentClick"
            @mouseenter="onSegmentHover"
            @mouseleave="onSegmentLeave"
          />

          <!-- Show More Button -->
          <div
            v-if="segments.length > initialDisplayCount"
            class="show-more-button-grid-item"
          >
            <button class="show-more-button" @click="toggleShowMore">
              <i
                class="fa-solid"
                :class="showAll ? 'fa-chevron-up' : 'fa-chevron-down'"
              ></i>
              <span v-if="showAll">Show Less</span>
              <span v-else>
                Show More<br />
                ({{ segments.length - initialDisplayCount }} more)
              </span>
            </button>
          </div>
        </div>

        <div v-else-if="!loading" class="no-segments">
          <p>
            No {{ selectedTrackType }}s found in the current view. Try zooming out or
            panning to a different area.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { TrackResponse, GPXDataResponse, GPXData } from '../types'
import { parseGPXData } from '../utils/gpxParser'
import { useStravaApi } from '../composables/useStravaApi'
import SegmentCard from './SegmentCard.vue'

const { t } = useI18n()

// Strava authentication
const { isAuthenticated } = useStravaApi()

interface SegmentStats {
  total_distance: number
  total_elevation_gain: number
  total_elevation_loss: number
}

interface Props {
  segments: TrackResponse[]
  loading: boolean
  // eslint-disable-next-line no-unused-vars
  getDistanceFromCenter?: (segment: TrackResponse) => number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  segmentClick: [segment: TrackResponse]
  segmentHover: [segment: TrackResponse]
  segmentLeave: [segment: TrackResponse]
  trackTypeChange: [trackType: 'segment' | 'route']
}>()

// Refs for segment stats
const segmentStats = ref<Map<number, SegmentStats>>(new Map())

// Cache for GPX data to avoid refetching
const gpxDataCache = new Map<number, GPXData>()
const loadingGPXData = new Set<number>()

// Track type filter
const selectedTrackType = ref<'segment' | 'route'>('segment')

// Currently hovered segment
const hoveredSegmentId = ref<number | null>(null)

// Show more/less functionality
const showAll = ref(false)

// Dynamic initial display count based on screen size
const getInitialDisplayCount = () => {
  const width = window.innerWidth
  if (width >= 1400) return 8 // 2 rows of 4 cards on large screens
  if (width >= 1200) return 6 // 2 rows of 3 cards on medium-large screens
  if (width >= 900) return 6 // 2 rows of 3 cards on medium screens
  if (width >= 768) return 4 // 2 rows of 2 cards on small-medium screens
  return 2 // 2 rows of 1 card on mobile
}

const initialDisplayCount = ref(getInitialDisplayCount())

// Update display count on window resize
const updateDisplayCount = () => {
  initialDisplayCount.value = getInitialDisplayCount()
}

// Computed property for displayed segments
const displayedSegments = computed(() => {
  if (showAll.value) {
    return props.segments
  }
  return props.segments.slice(0, initialDisplayCount.value)
})

// Watch for segment changes and generate mock stats
watch(
  () => props.segments,
  async (newSegments) => {
    await nextTick()
    for (const segment of newSegments) {
      await fetchSegmentStats(segment)
    }
  },
  { immediate: true }
)

// Reset showAll when segments change (new search)
watch(
  () => props.segments,
  () => {
    showAll.value = false
  }
)

async function fetchSegmentStats(segment: TrackResponse) {
  // Check if we already have stats for this segment
  if (segmentStats.value.has(segment.id)) {
    return
  }

  // Check if we're already loading this GPX data
  if (loadingGPXData.has(segment.id)) {
    return
  }

  loadingGPXData.add(segment.id)

  try {
    // Fetch GPX data from backend
    const response = await fetch(`http://localhost:8000/api/segments/${segment.id}/gpx`)
    if (!response.ok) {
      console.warn(
        `Failed to fetch GPX data for segment ${segment.id}: ${response.statusText}`
      )
      // Fallback to mock data if fetch fails
      generateFallbackStats(segment)
      return
    }

    const gpxResponse: GPXDataResponse = await response.json()

    // Parse GPX data
    const fileId =
      segment.file_path.split('/').pop()?.replace('.gpx', '') || segment.id.toString()
    const gpxData = parseGPXData(gpxResponse.gpx_xml_data, fileId)

    if (gpxData && gpxData.total_stats) {
      // Cache the GPX data
      gpxDataCache.set(segment.id, gpxData)

      // Extract stats from GPX data
      const stats: SegmentStats = {
        total_distance: gpxData.total_stats.total_distance,
        total_elevation_gain: gpxData.total_stats.total_elevation_gain,
        total_elevation_loss: gpxData.total_stats.total_elevation_loss
      }
      segmentStats.value.set(segment.id, stats)
    } else {
      // Fallback to mock data if parsing fails
      generateFallbackStats(segment)
    }
  } catch (error) {
    console.warn(`Error fetching GPX data for segment ${segment.id}:`, error)
    // Fallback to mock data if error occurs
    generateFallbackStats(segment)
  } finally {
    loadingGPXData.delete(segment.id)
  }
}

function generateFallbackStats(segment: TrackResponse) {
  // Generate fallback stats based on segment properties (same as before)
  const latDiff = segment.bound_north - segment.bound_south
  const lonDiff = segment.bound_east - segment.bound_west
  const avgLat = (segment.bound_north + segment.bound_south) / 2

  // Rough distance calculation (not precise, but gives a reasonable estimate)
  const latKm = latDiff * 111.32 // 1 degree latitude ≈ 111.32 km
  const lonKm = lonDiff * 111.32 * Math.cos((avgLat * Math.PI) / 180)
  const distance = Math.sqrt(latKm * latKm + lonKm * lonKm) * 1000 // Convert to meters

  // Generate mock elevation gain and loss based on difficulty and track type
  const baseElevation = segment.difficulty_level * 50 // 50m per difficulty level
  const elevationGain = baseElevation + Math.random() * 100 // Add some randomness
  const elevationLoss = elevationGain * (0.8 + Math.random() * 0.4) // Loss is typically 80-120% of gain

  const stats: SegmentStats = {
    total_distance: Math.round(distance),
    total_elevation_gain: Math.round(elevationGain),
    total_elevation_loss: Math.round(elevationLoss)
  }
  segmentStats.value.set(segment.id, stats)
}

function onSegmentClick(segment: TrackResponse) {
  emit('segmentClick', segment)
}

function onSegmentHover(segment: TrackResponse) {
  hoveredSegmentId.value = segment.id
  emit('segmentHover', segment)
}

function onSegmentLeave(segment: TrackResponse) {
  hoveredSegmentId.value = null
  emit('segmentLeave', segment)
}

function onTrackTypeChange(trackType: 'segment' | 'route') {
  selectedTrackType.value = trackType
  emit('trackTypeChange', trackType)
}

function toggleShowMore() {
  showAll.value = !showAll.value
}

// Add window resize listener
onMounted(() => {
  window.addEventListener('resize', updateDisplayCount)
})

onUnmounted(() => {
  // Cleanup GPX data cache and loading sets
  gpxDataCache.clear()
  loadingGPXData.clear()
  segmentStats.value.clear()

  // Remove window resize listener
  window.removeEventListener('resize', updateDisplayCount)
})
</script>

<style scoped>
.segment-list-header {
  margin-bottom: 16px;
}

.segment-list-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.2rem;
  font-weight: 600;
}

/* Segment List Container */
.segment-list {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.filter-card {
  background: white;
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  margin-bottom: 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden; /* Contain everything within the card */
}

/* Track Type Tabs - Sticky */
.track-type-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
  padding: 0.25rem;
  background: #f8fafc;
  border-radius: 8px 8px 0 0;
  border: 1px solid #e5e7eb;
  border-bottom: none;
  position: sticky;
  top: 0;
  z-index: 10;
  flex-shrink: 0;
  min-height: 0;
}

/* Scrollable Cards Container */
.cards-container {
  flex: 1;
  overflow-y: auto; /* Enable scrolling within the container */
  padding: 0;
  border-radius: 0 0 8px 8px;
  border: 1px solid #e5e7eb;
  border-top: none;
  background: white;
  position: relative;
  min-height: 0; /* Ensure flex child can shrink */
  padding-bottom: 50px; /* Space for the show more button */
}

/* Scroll indicator - subtle shadow at bottom when scrollable */
.cards-container::after {
  content: '';
  position: sticky;
  bottom: 0;
  left: 0;
  right: 0;
  height: 20px;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.1));
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.cards-container.scrollable::after {
  opacity: 1;
}

.cards-container::-webkit-scrollbar {
  width: 8px;
}

.cards-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.cards-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.cards-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.tab-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #6b7280;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-button:hover {
  background: #e5e7eb;
  color: #374151;
}

.tab-button.active {
  background: #ffffff;
  color: var(--brand-primary);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #ffb366;
}

.tab-button i {
  font-size: 0.875rem;
}

.segment-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  padding: 16px 16px 0px 16px;
}

.segment-cards--no-button {
  padding: 16px; /* Add bottom padding when button is not present */
}

.segment-comments {
  font-size: 0.875rem;
  color: #666;
  line-height: 1.4;
}

.segment-comments p {
  margin: 0;
}

.no-segments {
  text-align: center;
  padding: 40px 20px;
  color: #666;
  background: white;
}

.no-segments p {
  margin: 0;
  font-size: 1rem;
}

/* Show More Button */
.show-more-button-grid-item {
  grid-column: 1 / -1; /* Span all grid columns */
  display: flex;
  justify-content: center;
  align-items: center;
  background: white;
  position: relative;
  z-index: 10; /* Higher z-index to appear above filter-card */
  margin-top: 16px; /* Add some spacing from the cards above */
  margin-bottom: 0; /* No bottom margin needed */
}

.show-more-button {
  position: sticky;
  bottom: 10px; /* Stick to bottom of scrollable container */
  left: 50%;
  transform: translateX(-50%);
  z-index: 10; /* Ensure button is above filter-card */

  /* Pill shape and style */
  background: linear-gradient(135deg, var(--brand-primary), #ff7f2a);
  border: none;
  border-radius: 24px;
  padding: 10px 28px;
  height: 36px;
  min-width: 90px;

  /* Orange shadow */
  box-shadow: 0 2px 8px rgba(var(--brand-primary-rgb), 0.3);

  /* Button styles */
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  color: white;
  font-weight: 600;
  transition: all 0.3s ease;

  /* Remove default button styles */
  outline: none;
  font-family: inherit;
}

.show-more-button:hover {
  background: var(--brand-primary-hover);
  transform: translateX(-50%) translateY(-2px);
  box-shadow: 0 4px 12px rgba(var(--brand-primary-rgb), 0.4);
}

.show-more-button:active {
  transform: translateX(-50%) translateY(0);
  box-shadow: 0 2px 8px rgba(var(--brand-primary-rgb), 0.3);
}

/* Icon animation */
.show-more-button i {
  display: inline-block;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 12px;
}

.show-more-button:hover i {
  transform: scale(1.1);
}

/* Focus state for accessibility */
.show-more-button:focus-visible {
  box-shadow:
    0 0 0 3px rgba(var(--brand-primary-rgb), 0.4),
    0 2px 8px rgba(var(--brand-primary-rgb), 0.3);
}

/* Large screens - more cards per row */
@media (min-width: 1400px) {
  .segment-cards {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
}

@media (min-width: 1200px) {
  .segment-cards {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  }
}

@media (min-width: 900px) {
  .segment-cards {
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  }

  .show-more-button {
    min-width: 110px;
    font-size: 0.9rem;
    padding: 12px 32px;
    height: 40px;
  }
}

@media (max-width: 768px) {
  .filter-card {
    height: 100%;
  }

  .segment-cards {
    grid-template-columns: 1fr;
  }

  .segment-metrics {
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
  }

  .segment-info-grid {
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .info-section:nth-child(3) {
    grid-column: 1 / -1;
    text-align: center;
  }

  .tire-recommendations {
    justify-content: center;
  }

  .track-type-tabs {
    grid-template-columns: 1fr 1fr;
    gap: 0.25rem;
    padding: 0.2rem;
  }

  .show-more-button {
    min-width: 80px;
    font-size: 0.8rem;
    padding: 8px 24px;
    height: 32px;
  }
}

/* Info tooltip icon styles */
.info-tooltip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: 4px;
  cursor: help;
  opacity: 0.6;
  transition: opacity 0.2s ease;
  position: relative;
}

.info-tooltip:hover {
  opacity: 1;
}

.info-tooltip i {
  font-size: 0.75rem;
}

/* Prevent info icon from triggering tab button hover/active states */
.info-tooltip:hover,
.info-tooltip:active {
  background: transparent;
}

/* Warning icon styles */
.warning-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: 4px;
  cursor: help;
  color: #f59e0b;
  transition: opacity 0.2s ease;
  position: relative;
  animation: pulse 2s ease-in-out infinite;
}

.warning-icon:hover {
  opacity: 0.8;
}

.warning-icon i {
  font-size: 0.75rem;
}

/* Prevent warning icon from triggering tab button hover/active states */
.warning-icon:hover,
.warning-icon:active {
  background: transparent;
}

/* Pulse animation for warning icon */
@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}
</style>
