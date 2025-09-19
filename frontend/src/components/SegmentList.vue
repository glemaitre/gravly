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
        </button>
        <button
          type="button"
          class="tab-button"
          :class="{ active: selectedTrackType === 'route' }"
          @click="onTrackTypeChange('route')"
        >
          <i class="fa-solid fa-map"></i>
          Routes
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
          <div
            v-for="segment in displayedSegments"
            :key="segment.id"
            class="segment-card"
            @click="onSegmentClick(segment)"
            @mouseenter="onSegmentHover(segment)"
            @mouseleave="onSegmentLeave(segment)"
          >
            <div class="segment-card-header">
              <h4
                class="segment-name"
                :class="{ hovered: hoveredSegmentId === segment.id }"
              >
                {{ segment.name }}
                <span v-if="hoveredSegmentId === segment.id" class="hover-indicator"
                  >📍</span
                >
              </h4>
            </div>

            <div class="segment-card-content">
              <div class="segment-metrics">
                <div class="metric">
                  <span class="metric-label">Distance</span>
                  <span class="metric-value">{{
                    formatDistance(segmentStats.get(segment.id)?.total_distance || 0)
                  }}</span>
                </div>
                <div class="metric">
                  <span class="metric-label">Elevation Gain</span>
                  <span class="metric-value">{{
                    formatElevation(
                      segmentStats.get(segment.id)?.total_elevation_gain || 0
                    )
                  }}</span>
                </div>
                <div class="metric">
                  <span class="metric-label">Elevation Loss</span>
                  <span class="metric-value">{{
                    formatElevation(
                      segmentStats.get(segment.id)?.total_elevation_loss || 0
                    )
                  }}</span>
                </div>
              </div>
            </div>

            <div class="segment-card-footer">
              <div class="segment-info-grid">
                <!-- Surface Type -->
                <div class="info-section">
                  <div class="info-label">Surface</div>
                  <div class="info-value">
                    <i class="fa-solid fa-road"></i>
                    <span>{{ formatSurfaceType(segment.surface_type) }}</span>
                  </div>
                </div>

                <!-- Tire Recommendations -->
                <div class="info-section">
                  <div class="info-label">Tires</div>
                  <div class="tire-recommendations">
                    <div class="tire-recommendation">
                      <i class="fa-solid fa-sun"></i>
                      <span class="tire-badge">{{
                        formatTireType(segment.tire_dry)
                      }}</span>
                    </div>
                    <div class="tire-recommendation">
                      <i class="fa-solid fa-cloud-rain"></i>
                      <span class="tire-badge">{{
                        formatTireType(segment.tire_wet)
                      }}</span>
                    </div>
                  </div>
                </div>

                <!-- Difficulty -->
                <div class="info-section">
                  <div class="info-label">Difficulty</div>
                  <div class="info-value difficulty">
                    <i class="fa-solid fa-signal"></i>
                    <span>{{ segment.difficulty_level }}/5</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

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
import type { TrackResponse, GPXDataResponse, GPXData } from '../types'
import { parseGPXData } from '../utils/gpxParser'

interface SegmentStats {
  total_distance: number
  total_elevation_gain: number
  total_elevation_loss: number
}

interface Props {
  segments: TrackResponse[]
  loading: boolean
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

// Formatting functions
function formatDistance(meters: number): string {
  if (meters < 1000) {
    return `${Math.round(meters)}m`
  }
  return `${(meters / 1000).toFixed(1)}km`
}

function formatElevation(meters: number): string {
  return `${Math.round(meters)}m`
}

function formatSurfaceType(surfaceType: string): string {
  if (!surfaceType) return ''
  return surfaceType.replace(/-/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
}

function formatTireType(tireType: string): string {
  if (!tireType) return ''
  return tireType.replace(/-/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
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
  margin-bottom: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: visible; /* Allow button to overflow outside */
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
  overflow-y: inherit; /* Allow button to overflow outside */
  padding: 0;
  border-radius: 0 0 8px 8px;
  border: 1px solid #e5e7eb;
  border-top: none;
  background: white;
  position: relative;
  min-height: 0; /* Ensure flex child can shrink */
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
  color: #ff6600;
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

.segment-card {
  background: white;
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  position: relative;
}

.segment-card:hover {
  box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3);
  transform: translateY(-2px);
  border-color: #ff6b35;
  background: linear-gradient(135deg, #fff 0%, #fff8f5 100%);
}

.segment-card:hover::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border: 2px solid #ff6b35;
  border-radius: 8px;
  pointer-events: none;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0% {
    opacity: 0.6;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.02);
  }
  100% {
    opacity: 0.6;
    transform: scale(1);
  }
}

.segment-card-header {
  margin-bottom: 12px;
}

.segment-name {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: color 0.2s ease;
}

.segment-name.hovered {
  color: #ff6b35;
}

.hover-indicator {
  font-size: 0.9rem;
  animation: bounce 1s ease-in-out infinite;
}

@keyframes bounce {
  0%,
  20%,
  50%,
  80%,
  100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-3px);
  }
  60% {
    transform: translateY(-2px);
  }
}

.segment-card-content {
  margin-bottom: 12px;
}

.segment-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}

.metric {
  text-align: center;
}

.metric-label {
  display: block;
  font-size: 0.75rem;
  color: #666;
  margin-bottom: 4px;
  text-transform: uppercase;
  font-weight: 500;
}

.metric-value {
  display: block;
  font-size: 1rem;
  font-weight: 600;
  color: #333;
}

.segment-card-footer {
  border-top: 1px solid #f0f0f0;
  padding-top: 12px;
  position: relative;
}

.segment-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
}

.info-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: center;
  text-align: center;
}

.info-label {
  color: #666;
  font-weight: 500;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 2px;
}

.info-value {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 0.75rem;
  color: #333;
  font-weight: 500;
}

.info-value i {
  font-size: 0.8rem;
  color: #666;
}

.info-value.difficulty {
  color: #e67e22;
  font-weight: 600;
}

.tire-recommendations {
  display: flex;
  gap: 8px;
}

.tire-recommendation {
  display: flex;
  align-items: center;
  gap: 4px;
}

.tire-recommendation i {
  font-size: 0.8rem;
}

.tire-recommendation .fa-sun {
  color: #ff6600; /* Orange for sun - matches Editor brand-500 */
}

.tire-recommendation .fa-cloud-rain {
  color: #3b82f6; /* Blue for cloud - matches Editor blue-500 */
}

.tire-badge {
  background-color: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 0.7rem;
  color: #333;
  font-weight: 500;
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
  margin-bottom: 14px; /* Space for button to overlap filter-card */
}

.show-more-button {
  position: absolute;
  bottom: -30px; /* Half outside the cards-container */
  left: 50%;
  transform: translateX(-50%);
  z-index: 10; /* Ensure button is above filter-card */

  /* Pill shape and style */
  background: linear-gradient(135deg, #ff6600, #ff7f2a);
  border: none;
  border-radius: 24px;
  padding: 10px 28px;
  height: 36px;
  min-width: 90px;

  /* Orange shadow */
  box-shadow: 0 2px 8px rgba(255, 102, 0, 0.3);

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
  background: linear-gradient(135deg, #e55a00, #e66a00);
  transform: translateX(-50%) translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 102, 0, 0.4);
}

.show-more-button:active {
  transform: translateX(-50%) translateY(0);
  box-shadow: 0 2px 8px rgba(255, 102, 0, 0.3);
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
    0 0 0 3px rgba(255, 102, 0, 0.4),
    0 2px 8px rgba(255, 102, 0, 0.3);
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
</style>
