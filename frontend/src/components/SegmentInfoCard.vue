<template>
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
                <span class="difficulty-level">{{ difficultyLevel }}</span>
                <span class="difficulty-word">{{ difficultyWord }}</span>
                <span v-if="difficultyLevel > 5" class="difficulty-over">{{
                  t('segmentDetail.over5')
                }}</span>
              </div>
            </div>
          </div>

          <!-- Surface Type -->
          <div class="info-item-compact">
            <div class="info-label">
              <i class="fa-solid fa-road"></i>
              {{ t('segmentDetail.surface') }}
            </div>
            <div class="info-value surface-nav-container">
              <button
                v-if="segment.surface_type.length > 1"
                class="surface-nav-btn"
                @click.stop="previousSurface"
                :disabled="currentSurfaceIndex === 0"
                title="Previous surface type"
              >
                <i class="fa-solid fa-chevron-left"></i>
              </button>
              <div class="surface-info-vertical">
                <img
                  :src="surfaceImage"
                  :alt="surfaceTypeLabel"
                  class="surface-image"
                />
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
                    <span class="tire-label">{{ t('segmentDetail.dry') }}</span>
                  </div>
                  <div class="tire-option-vertical">
                    <img :src="tireDryImage" :alt="tireDryLabel" class="tire-image" />
                    <span class="tire-text">{{ tireDryLabel }}</span>
                  </div>
                </div>
                <div class="tire-recommendation-compact">
                  <div class="tire-header">
                    <i class="fa-solid fa-cloud-rain"></i>
                    <span class="tire-label">{{ t('segmentDetail.wet') }}</span>
                  </div>
                  <div class="tire-option-vertical">
                    <img :src="tireWetImage" :alt="tireWetLabel" class="tire-image" />
                    <span class="tire-text">{{ tireWetLabel }}</span>
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
                <span class="stat-value">{{ formattedDistance }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">
                  <i class="fa-solid fa-arrow-trend-up"></i>
                  {{ t('segmentDetail.elevationGain') }}
                </span>
                <span class="stat-value">{{ formattedElevationGain }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">
                  <i class="fa-solid fa-arrow-trend-down"></i>
                  {{ t('segmentDetail.elevationLoss') }}
                </span>
                <span class="stat-value">{{ formattedElevationLoss }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
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

const { t } = useI18n()

// Props
const props = defineProps<{
  segment: TrackResponse
  gpxData: GPXData
}>()

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

// State for surface type navigation
const currentSurfaceIndex = ref(0)

// Surface type navigation functions
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

// Helper functions
function formatDistance(kilometers: number): string {
  return `${kilometers.toFixed(2)} km`
}

function formatElevation(meters: number): string {
  return `${Math.round(meters)}m`
}

function formatSurfaceType(surfaceType: string): string {
  if (!surfaceType) return 'N/A'
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
  if (!surfaceType) return brokenPavedRoadUrl
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

// Computed properties for template
const difficultyLevel = computed(() => props.segment.difficulty_level || 0)
const difficultyWord = computed(() => getDifficultyWord(difficultyLevel.value))

const surfaceTypeLabel = computed(() => {
  if (!props.segment.surface_type || props.segment.surface_type.length === 0) {
    return 'N/A'
  }
  const currentType = props.segment.surface_type[currentSurfaceIndex.value]
  return formatSurfaceType(currentType)
})

const surfaceImage = computed(() => {
  if (!props.segment.surface_type || props.segment.surface_type.length === 0) {
    return brokenPavedRoadUrl
  }
  const currentType = props.segment.surface_type[currentSurfaceIndex.value]
  return getSurfaceImage(currentType)
})

const tireDryLabel = computed(() => formatTireType(props.segment.tire_dry))
const tireDryImage = computed(() => getTireImage(props.segment.tire_dry))

const tireWetLabel = computed(() => formatTireType(props.segment.tire_wet))
const tireWetImage = computed(() => getTireImage(props.segment.tire_wet))

const formattedDistance = computed(() =>
  formatDistance(props.gpxData.total_stats.total_distance)
)
const formattedElevationGain = computed(() =>
  formatElevation(props.gpxData.total_stats.total_elevation_gain)
)
const formattedElevationLoss = computed(() =>
  formatElevation(props.gpxData.total_stats.total_elevation_loss)
)
</script>

<style scoped>
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
  color: var(--brand-primary);
}

.card-content {
  padding: 1.5rem;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  height: 100%;
  justify-content: space-between;
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
  color: var(--brand-primary);
}

.info-value {
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
}

.difficulty-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.difficulty-display i {
  color: var(--brand-primary);
}

.difficulty-level {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--brand-primary);
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

.surface-nav-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
  min-width: 180px;
}

.surface-info-vertical {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  min-width: 120px;
  max-width: 120px;
}

.surface-indicator {
  font-size: 0.7rem;
  color: #999;
  font-weight: 400;
  margin-top: 0.25rem;
}

.surface-nav-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  color: var(--brand-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  border-radius: 4px;
  font-size: 1rem;
}

.surface-nav-btn:hover:not(:disabled) {
  background-color: rgba(var(--brand-primary-rgb), 0.1);
  transform: scale(1.1);
}

.surface-nav-btn:disabled {
  color: #ccc;
  cursor: not-allowed;
  opacity: 0.5;
}

.surface-nav-btn i {
  font-size: 0.9rem;
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
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  color: var(--brand-primary);
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
  color: white;
}

.stat-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #111827;
  text-align: center;
}

/* Responsive layout adjustments */
@media (max-width: 480px) {
  .info-row {
    flex-direction: column;
    gap: 0.75rem;
  }

  .tire-recommendations-compact {
    flex-direction: column;
    gap: 0.75rem;
  }
}
</style>
