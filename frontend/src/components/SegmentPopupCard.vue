<template>
  <div class="segment-popup-card" :class="{ selected: isSelected }">
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
            <span class="stat-value">{{ statsDisplay.distance }}</span>
            <span class="stat-label">Distance</span>
          </div>
        </div>
        <div class="stat-item">
          <i class="fa-solid fa-arrow-trend-up"></i>
          <div class="stat-content">
            <span class="stat-value">{{ statsDisplay.elevationGain }}</span>
            <span class="stat-label">Elevation Gain</span>
          </div>
        </div>
        <div class="stat-item">
          <i class="fa-solid fa-arrow-trend-down"></i>
          <div class="stat-content">
            <span class="stat-value">{{ statsDisplay.elevationLoss }}</span>
            <span class="stat-label">Elevation Loss</span>
          </div>
        </div>
      </div>
    </div>

    <div class="segment-card-footer">
      <div class="segment-info-grid">
        <div class="info-section">
          <div class="info-label">Surface</div>
          <div class="info-value">
            <i class="fa-solid fa-road"></i>
            <span>{{ formatSurfaceType(segment.surface_type) }}</span>
          </div>
        </div>

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
import { computed } from 'vue'
import type { TrackResponse, GPXData } from '../types'

// Props
const props = defineProps<{
  segment: TrackResponse
  isSelected: boolean
  gpxData?: GPXData | null
}>()

// Computed stats display
const statsDisplay = computed(() => {
  if (props.gpxData && props.gpxData.total_stats) {
    const stats = props.gpxData.total_stats
    return {
      distance: formatDistance(stats.total_distance),
      elevationGain: formatElevation(stats.total_elevation_gain),
      elevationLoss: formatElevation(stats.total_elevation_loss)
    }
  }

  // Loading state
  return {
    distance: '...',
    elevationGain: '...',
    elevationLoss: '...'
  }
})

// Formatting helper functions
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
  return surfaceType.replace(/-/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
}

function formatTireType(tireType: string): string {
  if (!tireType) return ''
  return tireType.replace(/-/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
}
</script>

<style>
.segment-popup-card {
  border: 1px solid #e1e5e9;
  border-radius: 6px;
  padding: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  position: relative;
  font-family: inherit;
  background: white;
  width: 340px;
}

.segment-popup-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
  border-color: rgba(var(--brand-primary-rgb), 0.3);
}

.segment-popup-card.selected {
  box-shadow: 0 3px 8px rgba(255, 107, 53, 0.3);
  transform: translateY(-1px);
  border-color: #ff6b35;
}

.segment-popup-card.selected:hover {
  box-shadow: 0 5px 15px rgba(255, 107, 53, 0.4);
  transform: translateY(-3px);
}

.segment-card-header {
  margin-bottom: 8px;
}

.segment-name {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: color 0.2s ease;
  line-height: 1.2;
}

.segment-popup-card.selected .segment-name {
  color: #ff6b35;
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
  background: #f8fafc;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
  transition: background-color 0.2s ease;
  flex: 1;
}

.stat-item i {
  width: 20px;
  height: 20px;
  background: #f97316;
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
  color: #666;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.stat-value {
  font-size: 0.75rem;
  color: #333;
  font-weight: 600;
}

.segment-card-footer {
  border-top: 1px solid #f0f0f0;
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
</style>
