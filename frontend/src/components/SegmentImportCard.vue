<template>
  <div
    class="segment-card"
    @click="handleClick"
    @mouseenter="handleHover"
    @mouseleave="handleLeave"
    :class="{ 'is-hovered': isHovered }"
  >
    <div class="segment-card-header">
      <h4 class="segment-name" :title="segment.name">
        {{ segment.name }}
      </h4>
    </div>

    <div class="segment-card-content">
      <div class="segment-stats">
        <div class="stat-item">
          <i class="fa-solid fa-route"></i>
          <div class="stat-content">
            <span class="stat-value">
              {{ isLoadingStats ? '...' : formatDistance(segmentStats.total_distance) }}
            </span>
            <span class="stat-label">Distance</span>
          </div>
        </div>
        <div class="stat-item">
          <i class="fa-solid fa-arrow-trend-up"></i>
          <div class="stat-content">
            <span class="stat-value">
              {{
                isLoadingStats
                  ? '...'
                  : formatElevation(segmentStats.total_elevation_gain)
              }}
            </span>
            <span class="stat-label">Elevation Gain</span>
          </div>
        </div>
        <div class="stat-item">
          <i class="fa-solid fa-arrow-trend-down"></i>
          <div class="stat-content">
            <span class="stat-value">
              {{
                isLoadingStats
                  ? '...'
                  : formatElevation(segmentStats.total_elevation_loss)
              }}
            </span>
            <span class="stat-label">Elevation Loss</span>
          </div>
        </div>
      </div>
    </div>

    <div class="segment-card-footer">
      <div class="segment-info-grid">
        <!-- Surface Type -->
        <div class="info-section">
          <div class="info-label">Surface</div>
          <div class="info-value surface-nav">
            <button
              v-if="segment.surface_type.length > 1"
              class="surface-nav-btn"
              @click.stop="previousSurface"
              :disabled="currentSurfaceIndex === 0"
              title="Previous surface type"
            >
              <i class="fa-solid fa-chevron-left"></i>
            </button>
            <div class="surface-content">
              <span class="surface-text">{{ surfaceTypeLabel }}</span>
              <span v-if="segment.surface_type.length > 1" class="surface-indicator">
                {{ currentSurfaceIndex + 1 }}/{{ segment.surface_type.length }}
              </span>
            </div>
            <button
              v-if="segment.surface_type.length > 1"
              class="surface-nav-btn"
              @click.stop="nextSurface"
              :disabled="currentSurfaceIndex === segment.surface_type.length - 1"
              title="Next surface type"
            >
              <i class="fa-solid fa-chevron-right"></i>
            </button>
          </div>
        </div>

        <!-- Tire Recommendations -->
        <div class="info-section">
          <div class="info-label">Tires</div>
          <div class="tire-recommendations">
            <div class="tire-recommendation">
              <i class="fa-solid fa-sun"></i>
              <span class="tire-badge">{{ tireDryLabel }}</span>
            </div>
            <div class="tire-recommendation">
              <i class="fa-solid fa-cloud-rain"></i>
              <span class="tire-badge">{{ tireWetLabel }}</span>
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
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import type { TrackResponse, GPXDataResponse } from '../types'
import { parseGPXData } from '../utils/gpxParser'

const { t } = useI18n()

// Props
const props = defineProps<{
  segment: TrackResponse
  distance: number
  map?: any // Optional map instance for showing trace
}>()

// Emits
const emit = defineEmits<{
  click: [segment: TrackResponse]
  hover: [segment: TrackResponse]
  leave: []
  showTrace: [segment: TrackResponse, gpxData: any]
  hideTrace: []
}>()

// Local state
const isHovered = ref(false)
const isLoadingStats = ref(false)
const segmentStats = ref({
  total_distance: 0,
  total_elevation_gain: 0,
  total_elevation_loss: 0
})
const currentSurfaceIndex = ref(0)

// Surface type navigation functions
function getCurrentSurfaceType(): string {
  if (!props.segment.surface_type || props.segment.surface_type.length === 0) {
    return 'N/A'
  }
  return props.segment.surface_type[currentSurfaceIndex.value]
}

function previousSurface(): void {
  if (currentSurfaceIndex.value > 0) {
    currentSurfaceIndex.value--
  }
}

function nextSurface(): void {
  if (currentSurfaceIndex.value < props.segment.surface_type.length - 1) {
    currentSurfaceIndex.value++
  }
}

// Computed properties
const surfaceTypeLabel = computed(() => {
  const currentType = getCurrentSurfaceType()
  if (currentType === 'N/A') return currentType
  return t(`surface.${currentType}`)
})

const tireDryLabel = computed(() => {
  return formatTireType(props.segment.tire_dry)
})

const tireWetLabel = computed(() => {
  return formatTireType(props.segment.tire_wet)
})

// Methods
async function fetchSegmentStats() {
  if (isLoadingStats.value) return

  isLoadingStats.value = true

  try {
    const response = await fetch(`/api/segments/${props.segment.id}/gpx`)
    if (!response.ok) {
      console.warn(
        `Failed to fetch GPX data for segment ${props.segment.id}: ${response.statusText}`
      )
      generateFallbackStats()
      return
    }

    const gpxResponse: GPXDataResponse = await response.json()

    // Parse GPX data
    const fileId =
      props.segment.file_path.split('/').pop()?.replace('.gpx', '') ||
      props.segment.id.toString()
    const gpxData = parseGPXData(gpxResponse.gpx_xml_data, fileId)

    if (gpxData && gpxData.total_stats) {
      segmentStats.value = {
        total_distance: gpxData.total_stats.total_distance,
        total_elevation_gain: gpxData.total_stats.total_elevation_gain,
        total_elevation_loss: gpxData.total_stats.total_elevation_loss
      }

      // Emit the GPX data for potential map trace display
      emit('showTrace', props.segment, gpxData)
    } else {
      generateFallbackStats()
    }
  } catch (error) {
    console.warn(`Error fetching GPX data for segment ${props.segment.id}:`, error)
    generateFallbackStats()
  } finally {
    isLoadingStats.value = false
  }
}

function generateFallbackStats() {
  // Generate approximate stats based on bounds and difficulty
  const latDiff = props.segment.bound_north - props.segment.bound_south
  const lonDiff = props.segment.bound_east - props.segment.bound_west
  const avgLat = (props.segment.bound_north + props.segment.bound_south) / 2

  // Rough distance calculation
  const latKm = latDiff * 111.32 // 1 degree latitude ≈ 111.32 km
  const lonKm = lonDiff * 111.32 * Math.cos((avgLat * Math.PI) / 180)
  const distance = Math.sqrt(latKm * latKm + lonKm * lonKm) * 1000 // Convert to meters

  // Generate mock elevation gain and loss based on difficulty
  const baseElevation = props.segment.difficulty_level * 50 // 50m per difficulty level
  const elevationGain = baseElevation + Math.random() * 100 // Add some randomness
  const elevationLoss = elevationGain * (0.8 + Math.random() * 0.4) // Loss is typically 80-120% of gain

  segmentStats.value = {
    total_distance: Math.round(distance),
    total_elevation_gain: Math.round(elevationGain),
    total_elevation_loss: Math.round(elevationLoss)
  }
}

function formatDistance(meters: number): string {
  if (meters < 1000) {
    return `${Math.round(meters)}m`
  }
  return `${(meters / 1000).toFixed(1)}km`
}

function formatElevation(meters: number): string {
  return `${Math.round(meters)}m`
}

function formatTireType(tireType: string): string {
  if (!tireType) return ''
  return tireType.replace(/-/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
}

function handleClick() {
  emit('click', props.segment)
}

function handleHover() {
  isHovered.value = true
  emit('hover', props.segment)
  // Fetch stats if not already loaded
  if (segmentStats.value.total_distance === 0) {
    fetchSegmentStats()
  }
}

function handleLeave() {
  isHovered.value = false
  emit('leave')
  emit('hideTrace')
}

// Fetch stats on mount
onMounted(() => {
  fetchSegmentStats()
})
</script>

<style scoped>
.segment-card {
  border: 1px solid var(--card-border);
  border-radius: 6px;
  padding: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: var(--shadow-sm);
  position: relative;
}

.segment-card:hover,
.segment-card.is-hovered {
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
  border-color: var(--brand-primary);
}

.segment-card-header {
  margin-bottom: 8px;
}

.segment-name {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 6px;
  transition: color 0.2s ease;
  line-height: 1.2;
}

.segment-card:hover .segment-name {
  color: var(--brand-primary);
}

.segment-card-content {
  margin-bottom: 8px;
}

.segment-stats {
  display: flex;
  gap: 8px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  border: 1px solid var(--card-border);
  transition: background-color 0.2s ease;
  flex: 1;
}

.stat-item i {
  width: 20px;
  height: 20px;
  background: var(--brand-primary);
  color: white;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  flex-shrink: 0;
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.stat-label {
  font-size: 0.6rem;
  color: var(--text-tertiary);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.stat-value {
  font-size: 0.75rem;
  color: var(--text-primary);
  font-weight: 600;
}

.segment-card-footer {
  border-top: 1px solid var(--border-muted);
  padding-top: 8px;
  position: relative;
}

.segment-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 8px;
}

.info-section {
  display: flex;
  flex-direction: column;
  gap: 2px;
  align-items: center;
  text-align: center;
}

.info-label {
  color: var(--text-tertiary);
  font-weight: 500;
  font-size: 0.6rem;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  margin-bottom: 1px;
}

.info-value {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  font-size: 0.65rem;
  color: var(--text-primary);
  font-weight: 500;
}

.info-value i {
  font-size: 0.7rem;
  color: var(--text-tertiary);
}

.info-value.difficulty {
  color: var(--brand-accent);
  font-weight: 600;
}

/* Surface navigation styles */
.info-value.surface-nav {
  gap: 2px;
  width: 100%;
  position: relative;
}

.surface-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
  flex: 1;
  flex-direction: column;
}

.surface-text {
  font-size: 0.65rem;
  font-weight: 500;
  text-align: center;
  line-height: 1.2;
  color: var(--text-primary);
}

.surface-indicator {
  font-size: 0.55rem;
  color: var(--text-tertiary);
  font-weight: 400;
}

.surface-nav-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 4px;
  color: var(--brand-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  border-radius: 3px;
  font-size: 0.7rem;
}

.surface-nav-btn:hover:not(:disabled) {
  background-color: rgba(var(--brand-primary-rgb), 0.1);
  transform: scale(1.1);
}

.surface-nav-btn:disabled {
  color: var(--text-tertiary);
  cursor: not-allowed;
  opacity: 0.5;
}

.surface-nav-btn i {
  font-size: 0.6rem;
}

.tire-recommendations {
  display: flex;
  gap: 6px;
}

.tire-recommendation {
  display: flex;
  align-items: center;
  gap: 3px;
}

.tire-recommendation i {
  font-size: 0.7rem;
}

.tire-recommendation .fa-sun {
  color: var(--brand-primary); /* Orange for sun - matches Editor brand-500 */
}

.tire-recommendation .fa-cloud-rain {
  color: #3b82f6; /* Blue for cloud - matches Editor blue-500 */
}

.tire-badge {
  background-color: var(--bg-tertiary);
  padding: 1px 4px;
  border-radius: 2px;
  font-size: 0.6rem;
  color: var(--text-primary);
  font-weight: 500;
}
</style>
