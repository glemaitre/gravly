<template>
  <div
    class="segment-card"
    :class="{ selected: isSelected }"
    @click="emit('click', segment)"
    @mouseenter="emit('mouseenter', segment)"
    @mouseleave="emit('mouseleave', segment)"
  >
    <div class="segment-card-header">
      <h4 class="segment-name" :class="{ hovered: isHovered }">
        {{ segment.name }}
      </h4>
      <!-- Add segment button for route planner context -->
      <button
        v-if="context === 'route-planner'"
        type="button"
        class="add-segment-btn"
        @click.stop="emit('add-segment', segment)"
        :title="'Add to selected segments'"
      >
        <i class="fa-solid fa-plus"></i>
      </button>
      <!-- Navigate to detail button for explorer context -->
      <button
        v-else-if="context === 'explorer'"
        type="button"
        class="navigate-btn"
        @click.stop="emit('navigate-to-detail', segment)"
        :title="'View segment details'"
      >
        <i class="fa-solid fa-up-right-from-square"></i>
      </button>
    </div>

    <div class="segment-card-content">
      <div class="segment-metrics">
        <div class="metric">
          <span class="metric-label">Distance</span>
          <span class="metric-value">{{
            formatDistance(stats?.total_distance || 0)
          }}</span>
        </div>
        <div class="metric">
          <span class="metric-label">Elevation Gain</span>
          <span class="metric-value">{{
            formatElevation(stats?.total_elevation_gain || 0)
          }}</span>
        </div>
        <div class="metric">
          <span class="metric-label">Elevation Loss</span>
          <span class="metric-value">{{
            formatElevation(stats?.total_elevation_loss || 0)
          }}</span>
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
              <span class="surface-text">{{ getCurrentSurfaceType() }}</span>
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
              <span class="tire-badge">{{ formatTireType(segment.tire_dry) }}</span>
            </div>
            <div class="tire-recommendation">
              <i class="fa-solid fa-cloud-rain"></i>
              <span class="tire-badge">{{ formatTireType(segment.tire_wet) }}</span>
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
import { ref } from 'vue'
import type { TrackResponse } from '../types'

// Types
interface SegmentStats {
  total_distance: number
  total_elevation_gain: number
  total_elevation_loss: number
}

// Props
const props = defineProps<{
  segment: TrackResponse
  stats?: SegmentStats | null
  isHovered?: boolean
  isSelected?: boolean
  distanceFromCenter?: number
  context?: 'explorer' | 'route-planner' // New prop to control button behavior
}>()

// Emits
const emit = defineEmits<{
  click: [segment: TrackResponse]
  mouseenter: [segment: TrackResponse]
  mouseleave: [segment: TrackResponse]
  'add-segment': [segment: TrackResponse]
  'navigate-to-detail': [segment: TrackResponse]
}>()

// State for surface type navigation
const currentSurfaceIndex = ref(0)

// Surface type navigation functions
function getCurrentSurfaceType(): string {
  if (!props.segment.surface_type || props.segment.surface_type.length === 0) {
    return 'N/A'
  }
  const surfaceType = props.segment.surface_type[currentSurfaceIndex.value]
  return formatSurfaceType(surfaceType)
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
</script>

<style scoped>
.segment-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 6px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: var(--card-shadow);
  position: relative;
}

.segment-card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
  border-color: rgba(var(--brand-primary-rgb), 0.3);
}

.segment-card.selected {
  border-color: var(--brand-primary);
  box-shadow: 0 4px 12px rgba(var(--brand-primary-rgb), 0.3);
  background: rgba(var(--brand-primary-rgb), 0.05);
}

.segment-card-header {
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.segment-name {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
  transition: color 0.2s ease;
  line-height: 1.3;
  flex: 1;
  min-width: 0;
}

.segment-name.hovered {
  color: var(--brand-primary);
}

.segment-card-content {
  margin-bottom: 10px;
}

.segment-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.metric {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.metric-label {
  font-size: 0.6rem;
  color: var(--text-tertiary);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.metric-value {
  font-size: 0.75rem;
  color: var(--text-primary);
  font-weight: 600;
}

.segment-card-footer {
  border-top: 1px solid var(--border-muted);
  padding-top: 8px;
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
  color: #e67e22;
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
  color: var(--text-muted);
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
  color: var(--text-muted);
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
  color: var(--brand-primary);
}

.tire-recommendation .fa-cloud-rain {
  color: #3b82f6;
}

.tire-badge {
  background-color: var(--bg-tertiary);
  padding: 1px 4px;
  border-radius: 2px;
  font-size: 0.6rem;
  color: var(--text-primary);
  font-weight: 500;
}

.add-segment-btn {
  background: var(--bg-secondary);
  border: 1px solid var(--border-secondary);
  border-radius: 4px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.add-segment-btn:hover {
  background: var(--bg-hover);
  border-color: var(--border-primary);
  color: var(--text-secondary);
  transform: scale(1.05);
}

.add-segment-btn i {
  font-size: 0.7rem;
}

.navigate-btn {
  background: var(--bg-secondary);
  border: 1px solid var(--border-secondary);
  border-radius: 4px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.navigate-btn:hover {
  background: var(--bg-hover);
  border-color: var(--border-primary);
  color: var(--text-secondary);
  transform: scale(1.05);
}

.navigate-btn i {
  font-size: 0.7rem;
}
</style>
