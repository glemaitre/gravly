<template>
  <div
    class="segment-card"
    @click="emit('click', segment)"
    @mouseenter="emit('mouseenter', segment)"
    @mouseleave="emit('mouseleave', segment)"
  >
    <div class="segment-card-header">
      <h4 class="segment-name" :class="{ hovered: isHovered }">
        {{ segment.name }}
      </h4>
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

    <!-- Distance from center indicator -->
    <div
      v-if="distanceFromCenter !== undefined"
      class="segment-distance"
      title="Distance from map center"
    >
      {{ formatDistanceFromCenter(distanceFromCenter) }} to📍
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { TrackResponse } from '../types'
import { formatDistance as formatDistanceFromCenter } from '../utils/distance'

// Types
interface SegmentStats {
  total_distance: number
  total_elevation_gain: number
  total_elevation_loss: number
}

// Props
defineProps<{
  segment: TrackResponse
  stats?: SegmentStats | null
  isHovered?: boolean
  distanceFromCenter?: number
}>()

// Emits
const emit = defineEmits<{
  click: [segment: TrackResponse]
  mouseenter: [segment: TrackResponse]
  mouseleave: [segment: TrackResponse]
}>()

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
  background: white;
  border: 1px solid #e1e5e9;
  border-radius: 6px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  position: relative;
}

.segment-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
  border-color: rgba(var(--brand-primary-rgb), 0.3);
}

.segment-card-header {
  margin-bottom: 10px;
}

.segment-name {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: #333;
  transition: color 0.2s ease;
  line-height: 1.3;
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
  color: #666;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.metric-value {
  font-size: 0.75rem;
  color: #333;
  font-weight: 600;
}

.segment-card-footer {
  border-top: 1px solid #f0f0f0;
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
  color: #666;
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
  color: #333;
  font-weight: 500;
}

.info-value i {
  font-size: 0.7rem;
  color: #666;
}

.info-value.difficulty {
  color: #e67e22;
  font-weight: 600;
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
  background-color: #f5f5f5;
  padding: 1px 4px;
  border-radius: 2px;
  font-size: 0.6rem;
  color: #333;
  font-weight: 500;
}

.segment-distance {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(var(--brand-primary-rgb), 0.1);
  color: var(--brand-primary);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 500;
}
</style>
