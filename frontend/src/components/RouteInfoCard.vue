<template>
  <div class="route-info-card">
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
            <div v-if="hasSegmentData" class="difficulty-display">
              <span class="difficulty-level">{{ difficultyLevel }}</span>
              <span class="difficulty-word">{{ difficultyWord }}</span>
            </div>
            <div v-else class="no-data">{{ t('routePlanner.noSegmentData') }}</div>
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
              v-if="surfaceTypes.length > 1"
              class="surface-nav-btn"
              @click.stop="previousSurface"
              :disabled="currentSurfaceIndex === 0"
              title="Previous surface type"
            >
              <i class="fa-solid fa-chevron-left"></i>
            </button>
            <div v-if="hasSegmentData" class="surface-info-vertical">
              <img
                :src="currentSurfaceImage"
                :alt="currentSurfaceLabel"
                class="surface-image"
              />
              <span class="surface-text">{{ currentSurfaceLabel }}</span>
              <span v-if="surfaceTypes.length > 1" class="surface-indicator">
                {{ currentSurfaceIndex + 1 }}/{{ surfaceTypes.length }}
              </span>
            </div>
            <div v-else class="no-data">{{ t('routePlanner.noSegmentData') }}</div>
            <button
              v-if="surfaceTypes.length > 1"
              class="surface-nav-btn"
              @click.stop="nextSurface"
              :disabled="currentSurfaceIndex === surfaceTypes.length - 1"
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
            <div v-if="hasSegmentData" class="tire-recommendations-compact">
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
            <div v-else class="no-data">{{ t('routePlanner.noSegmentData') }}</div>
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
</template>

<script lang="ts" setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { SurfaceType } from '../types'

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

interface RouteStats {
  distance: number
  difficulty: number
  elevationGain: number
  elevationLoss: number
  surfaceTypes: SurfaceType[]
  tireDry: 'slick' | 'semi-slick' | 'knobs'
  tireWet: 'slick' | 'semi-slick' | 'knobs'
}

// Props
const props = defineProps<{
  stats: RouteStats
  hasSegmentData: boolean
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
  if (currentSurfaceIndex.value < surfaceTypes.value.length - 1) {
    currentSurfaceIndex.value++
  }
}

// Helper functions
function formatDistance(kilometers: number): string {
  if (kilometers < 1) {
    return `${Math.round(kilometers * 1000)}m`
  }
  return `${kilometers.toFixed(1)} km`
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
  const roundedLevel = Math.round(level)
  const difficultyWords = {
    1: t('difficulty.level1'),
    2: t('difficulty.level2'),
    3: t('difficulty.level3'),
    4: t('difficulty.level4'),
    5: t('difficulty.level5')
  }
  return difficultyWords[roundedLevel as keyof typeof difficultyWords] || 'Unknown'
}

// Computed properties
const surfaceTypes = computed(() => props.stats.surfaceTypes || [])

const difficultyLevel = computed(() => {
  if (!props.hasSegmentData) return 0
  return props.stats.difficulty.toFixed(1)
})

const difficultyWord = computed(() => {
  if (!props.hasSegmentData) return ''
  return getDifficultyWord(props.stats.difficulty)
})

const currentSurfaceLabel = computed(() => {
  if (surfaceTypes.value.length === 0) return 'N/A'
  const currentType = surfaceTypes.value[currentSurfaceIndex.value]
  return formatSurfaceType(currentType)
})

const currentSurfaceImage = computed(() => {
  if (surfaceTypes.value.length === 0) return brokenPavedRoadUrl
  const currentType = surfaceTypes.value[currentSurfaceIndex.value]
  return getSurfaceImage(currentType)
})

const tireDryLabel = computed(() => formatTireType(props.stats.tireDry))
const tireDryImage = computed(() => getTireImage(props.stats.tireDry))

const tireWetLabel = computed(() => formatTireType(props.stats.tireWet))
const tireWetImage = computed(() => getTireImage(props.stats.tireWet))

const formattedDistance = computed(() => formatDistance(props.stats.distance))
const formattedElevationGain = computed(() =>
  formatElevation(props.stats.elevationGain)
)
const formattedElevationLoss = computed(() =>
  formatElevation(props.stats.elevationLoss)
)
</script>

<style scoped>
.route-info-card {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.info-row {
  display: flex;
  gap: 0.5rem;
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
  background: #ffffff;
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
  color: var(--brand-500, #ff6600);
}

.info-value {
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
}

.no-data {
  font-size: 0.75rem;
  color: #9ca3af;
  font-weight: 400;
  text-align: center;
}

.difficulty-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.difficulty-level {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--brand-500, #ff6600);
}

.difficulty-word {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  text-align: center;
}

.surface-nav-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
}

.surface-info-vertical {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  min-width: 100px;
  max-width: 100px;
}

.surface-indicator {
  font-size: 0.7rem;
  color: #999;
  font-weight: 400;
}

.surface-nav-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  color: var(--brand-500, #ff6600);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  border-radius: 4px;
  font-size: 1rem;
}

.surface-nav-btn:hover:not(:disabled) {
  background-color: rgba(255, 102, 0, 0.1);
  transform: scale(1.1);
}

.surface-nav-btn:disabled {
  color: #ccc;
  cursor: not-allowed;
  opacity: 0.5;
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
  font-size: 0.875rem;
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tire-recommendations-compact {
  display: flex;
  gap: 0.5rem;
  width: 100%;
}

.tire-recommendation-compact {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.5rem 0.25rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.tire-header {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  justify-content: center;
  flex-wrap: wrap;
}

.tire-header i {
  font-size: 0.75rem;
  color: var(--brand-500, #ff6600);
  flex-shrink: 0;
}

.tire-header i.fa-cloud-rain {
  color: #3b82f6;
}

.tire-header .tire-label {
  font-weight: 600;
  color: #374151;
  font-size: 0.7rem;
}

.tire-option-vertical {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.375rem;
}

.tire-image {
  width: 1.75rem;
  height: 1.75rem;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid #d1d5db;
  flex-shrink: 0;
}

.tire-text {
  font-weight: 500;
  color: #111827;
  text-align: center;
  font-size: 0.7rem;
  line-height: 1.2;
  word-break: break-word;
  overflow-wrap: break-word;
}

.stats-grid {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-items: center;
  justify-content: center;
  flex: 1;
  padding: 0.75rem 0.5rem;
  background: #ffffff;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  min-height: 70px;
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
@media (max-width: 640px) {
  .info-row {
    flex-direction: column;
    gap: 0.75rem;
  }

  .info-item-compact:nth-child(1),
  .info-item-compact:nth-child(2),
  .info-item-compact:nth-child(3) {
    flex: 1;
  }

  .tire-recommendations-compact {
    flex-direction: column;
    gap: 0.75rem;
  }
}
</style>
