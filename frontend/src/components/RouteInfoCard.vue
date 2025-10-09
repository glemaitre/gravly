<template>
  <div class="route-info-card">
    <div class="info-grid">
      <!-- Top Row: Difficulty, Surface, Tires -->
      <div class="info-row">
        <!-- Difficulty -->
        <div
          class="info-item-compact"
          :class="{
            editable: editable && hasSegmentData,
            editing: isEditingDifficulty
          }"
          @click="editable && hasSegmentData && toggleDifficultyEditor()"
        >
          <div class="info-label">
            <i class="fa-solid fa-signal"></i>
            {{ t('segmentDetail.difficulty') }}
            <i
              v-if="editable && hasSegmentData"
              class="fa-solid fa-pencil edit-icon"
            ></i>
          </div>
          <div class="info-value">
            <div
              v-if="hasSegmentData && !isEditingDifficulty"
              class="difficulty-display"
            >
              <span class="difficulty-level">{{ difficultyLevel }}</span>
              <span class="difficulty-word">{{ difficultyWord }}</span>
            </div>
            <div v-else-if="isEditingDifficulty" class="difficulty-editor" @click.stop>
              <div class="difficulty-buttons">
                <button
                  v-for="level in [1, 2, 3, 4, 5]"
                  :key="level"
                  class="difficulty-btn"
                  :class="{ active: editableDifficulty === level }"
                  @click="updateDifficulty(level)"
                >
                  {{ level }}
                </button>
              </div>
              <button class="close-editor-btn" @click.stop="closeDifficultyEditor">
                <i class="fa-solid fa-check"></i>
              </button>
            </div>
            <div v-else class="no-data">{{ t('routePlanner.noSegmentData') }}</div>
          </div>
        </div>

        <!-- Surface Type -->
        <div
          class="info-item-compact"
          :class="{ editable: editable && hasSegmentData, editing: isEditingSurface }"
          @click="editable && hasSegmentData && toggleSurfaceEditor()"
        >
          <div class="info-label">
            <i class="fa-solid fa-road"></i>
            {{ t('segmentDetail.surface') }}
            <i
              v-if="editable && hasSegmentData"
              class="fa-solid fa-pencil edit-icon"
            ></i>
          </div>
          <div class="info-value surface-nav-container">
            <button
              v-if="surfaceTypes.length > 1 && !isEditingSurface"
              class="surface-nav-btn"
              @click.stop="previousSurface"
              :disabled="currentSurfaceIndex === 0"
              title="Previous surface type"
            >
              <i class="fa-solid fa-chevron-left"></i>
            </button>
            <div
              v-if="hasSegmentData && !isEditingSurface"
              class="surface-info-vertical"
            >
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
            <div v-else-if="isEditingSurface" class="surface-editor" @click.stop>
              <div class="surface-options-grid">
                <label
                  v-for="(image, surfaceType) in surfaceImages"
                  :key="surfaceType"
                  class="surface-option-compact"
                  :class="{ selected: isSurfaceTypeSelected(surfaceType as string) }"
                >
                  <input
                    type="checkbox"
                    :value="surfaceType"
                    :checked="isSurfaceTypeSelected(surfaceType as string)"
                    @change="toggleSurfaceType(surfaceType as any)"
                  />
                  <img :src="image" :alt="t(`surface.${surfaceType}`)" />
                  <span class="surface-caption">{{ t(`surface.${surfaceType}`) }}</span>
                </label>
              </div>
              <button class="close-editor-btn" @click.stop="closeSurfaceEditor">
                <i class="fa-solid fa-check"></i>
              </button>
            </div>
            <div v-else class="no-data">{{ t('routePlanner.noSegmentData') }}</div>
            <button
              v-if="surfaceTypes.length > 1 && !isEditingSurface"
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
        <div
          class="info-item-compact"
          :class="{ editable: editable && hasSegmentData, editing: isEditingTires }"
          @click="editable && hasSegmentData && toggleTireEditor()"
        >
          <div class="info-label">
            <i class="fa-solid fa-circle"></i>
            {{ t('segmentDetail.tireRecommendations') }}
            <i
              v-if="editable && hasSegmentData"
              class="fa-solid fa-pencil edit-icon"
            ></i>
          </div>
          <div class="info-value">
            <div
              v-if="hasSegmentData && !isEditingTires"
              class="tire-recommendations-compact"
            >
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
            <div v-else-if="isEditingTires" class="tire-editor" @click.stop>
              <div class="tire-groups-compact">
                <div class="tire-group-compact">
                  <div class="tire-group-header">
                    <i class="fa-solid fa-sun"></i>
                    <span>{{ t('segmentDetail.dry') }}</span>
                  </div>
                  <div class="tire-options">
                    <label
                      v-for="tireType in ['slick', 'semi-slick', 'knobs']"
                      :key="tireType"
                      class="tire-option-compact"
                      :class="{ selected: editableTireDry === tireType }"
                    >
                      <input
                        type="radio"
                        name="tire-dry"
                        :value="tireType"
                        :checked="editableTireDry === tireType"
                        @change="updateTireDry(tireType as any)"
                      />
                      <img
                        :src="getTireImage(tireType)"
                        :alt="formatTireType(tireType)"
                      />
                      <span class="tire-caption">{{ formatTireType(tireType) }}</span>
                    </label>
                  </div>
                </div>
                <div class="tire-group-compact">
                  <div class="tire-group-header">
                    <i class="fa-solid fa-cloud-rain"></i>
                    <span>{{ t('segmentDetail.wet') }}</span>
                  </div>
                  <div class="tire-options">
                    <label
                      v-for="tireType in ['slick', 'semi-slick', 'knobs']"
                      :key="tireType"
                      class="tire-option-compact"
                      :class="{ selected: editableTireWet === tireType }"
                    >
                      <input
                        type="radio"
                        name="tire-wet"
                        :value="tireType"
                        :checked="editableTireWet === tireType"
                        @change="updateTireWet(tireType as any)"
                      />
                      <img
                        :src="getTireImage(tireType)"
                        :alt="formatTireType(tireType)"
                      />
                      <span class="tire-caption">{{ formatTireType(tireType) }}</span>
                    </label>
                  </div>
                </div>
              </div>
              <button class="close-editor-btn" @click.stop="closeTireEditor">
                <i class="fa-solid fa-check"></i>
              </button>
            </div>
            <div v-else class="no-data">{{ t('routePlanner.noSegmentData') }}</div>
          </div>
        </div>
      </div>

      <!-- Bottom Row: Statistics -->
      <div class="info-row">
        <!-- Distance -->
        <div class="info-item-compact">
          <div class="info-label">
            <i class="fa-solid fa-route"></i>
            {{ t('segmentDetail.distance') }}
          </div>
          <div class="info-value">
            <span class="stat-value">{{ formattedDistance }}</span>
          </div>
        </div>

        <!-- Elevation Gain -->
        <div class="info-item-compact">
          <div class="info-label">
            <i class="fa-solid fa-arrow-trend-up"></i>
            {{ t('segmentDetail.elevationGain') }}
          </div>
          <div class="info-value">
            <span class="stat-value">{{ formattedElevationGain }}</span>
          </div>
        </div>

        <!-- Elevation Loss -->
        <div class="info-item-compact">
          <div class="info-label">
            <i class="fa-solid fa-arrow-trend-down"></i>
            {{ t('segmentDetail.elevationLoss') }}
          </div>
          <div class="info-value">
            <span class="stat-value">{{ formattedElevationLoss }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
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
  editable?: boolean
}>()

// Emits
const emit = defineEmits<{
  'update:difficulty': [difficulty: number]
  'update:surfaceTypes': [surfaceTypes: SurfaceType[]]
  'update:tireDry': [tireDry: 'slick' | 'semi-slick' | 'knobs']
  'update:tireWet': [tireWet: 'slick' | 'semi-slick' | 'knobs']
}>()

// Editing state
const isEditingDifficulty = ref(false)
const isEditingSurface = ref(false)
const isEditingTires = ref(false)

// Editable values (local state)
const editableDifficulty = ref(props.stats.difficulty)
const editableSurfaceTypes = ref<SurfaceType[]>([...props.stats.surfaceTypes])
const editableTireDry = ref(props.stats.tireDry)
const editableTireWet = ref(props.stats.tireWet)

// Watch for changes in props and update editable values
watch(
  () => props.stats,
  (newStats) => {
    if (!isEditingDifficulty.value) {
      editableDifficulty.value = newStats.difficulty
    }
    if (!isEditingSurface.value) {
      editableSurfaceTypes.value = [...newStats.surfaceTypes]
    }
    if (!isEditingTires.value) {
      editableTireDry.value = newStats.tireDry
      editableTireWet.value = newStats.tireWet
    }
  },
  { deep: true }
)

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

// Editor toggle functions
function toggleDifficultyEditor(): void {
  if (!props.editable || !props.hasSegmentData) return
  isEditingDifficulty.value = !isEditingDifficulty.value
  if (isEditingDifficulty.value) {
    // Close other editors
    isEditingSurface.value = false
    isEditingTires.value = false
  }
}

function toggleSurfaceEditor(): void {
  if (!props.editable || !props.hasSegmentData) return
  isEditingSurface.value = !isEditingSurface.value
  if (isEditingSurface.value) {
    // Close other editors
    isEditingDifficulty.value = false
    isEditingTires.value = false
  }
}

function toggleTireEditor(): void {
  if (!props.editable || !props.hasSegmentData) return
  isEditingTires.value = !isEditingTires.value
  if (isEditingTires.value) {
    // Close other editors
    isEditingDifficulty.value = false
    isEditingSurface.value = false
  }
}

// Difficulty editor functions
function updateDifficulty(level: number): void {
  editableDifficulty.value = level
  emit('update:difficulty', level)
}

function closeDifficultyEditor(): void {
  isEditingDifficulty.value = false
}

// Surface editor functions
function isSurfaceTypeSelected(surfaceType: string): boolean {
  return editableSurfaceTypes.value.includes(surfaceType as SurfaceType)
}

function toggleSurfaceType(surfaceType: SurfaceType): void {
  const currentTypes = [...editableSurfaceTypes.value]
  const index = currentTypes.indexOf(surfaceType)

  if (index > -1) {
    // Remove if already selected
    currentTypes.splice(index, 1)
  } else {
    // Add if not selected
    currentTypes.push(surfaceType)
  }

  editableSurfaceTypes.value = currentTypes
  emit('update:surfaceTypes', currentTypes)
}

function closeSurfaceEditor(): void {
  isEditingSurface.value = false
}

// Tire editor functions
function updateTireDry(tireType: 'slick' | 'semi-slick' | 'knobs'): void {
  editableTireDry.value = tireType
  emit('update:tireDry', tireType)
}

function updateTireWet(tireType: 'slick' | 'semi-slick' | 'knobs'): void {
  editableTireWet.value = tireType
  emit('update:tireWet', tireType)
}

function closeTireEditor(): void {
  isEditingTires.value = false
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
const surfaceTypes = computed(() =>
  isEditingSurface.value ? editableSurfaceTypes.value : props.stats.surfaceTypes || []
)

const difficultyLevel = computed(() => {
  if (!props.hasSegmentData) return 0
  return Math.round(props.stats.difficulty)
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

/* First row: Difficulty, Surface, Tire */
.info-row:first-child .info-item-compact:nth-child(1) {
  flex: 1;
}

.info-row:first-child .info-item-compact:nth-child(2) {
  flex: 1;
}

.info-row:first-child .info-item-compact:nth-child(3) {
  flex: 2;
}

/* Second row: Distance, Elevation Gain, Elevation Loss */
.info-row:nth-child(2) .info-item-compact {
  flex: 1;
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
  font-size: 0.75rem;
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
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  text-align: center;
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
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  text-align: center;
  line-height: 1.2;
  word-break: break-word;
  overflow-wrap: break-word;
}

.stat-value {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  text-align: center;
}

/* Editable styles */
.info-item-compact.editable {
  cursor: pointer;
  transition: all 0.2s ease;
}

.info-item-compact.editable:hover {
  background: #f9fafb;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.info-item-compact.editing {
  background: #f9fafb;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.edit-icon {
  font-size: 0.7rem;
  opacity: 0.6;
  margin-left: 0.25rem;
}

/* Difficulty Editor */
.difficulty-editor {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  width: 100%;
  padding: 0.5rem;
}

.difficulty-buttons {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
}

.difficulty-btn {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  border: 2px solid #d1d5db;
  background: white;
  color: #6b7280;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.difficulty-btn:hover {
  border-color: var(--brand-500, #ff6600);
  color: var(--brand-500, #ff6600);
}

.difficulty-btn.active {
  background: var(--brand-500, #ff6600);
  border-color: var(--brand-500, #ff6600);
  color: white;
}

/* Surface Editor */
.surface-editor {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 0.75rem;
  width: 100%;
  max-height: 400px;
  overflow-y: auto;
}

.surface-options-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
}

.surface-option-compact {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  border: 2px solid #e5e7eb;
  border-radius: 6px;
  padding: 0.5rem;
  cursor: pointer;
  background: #fff;
  transition: all 0.2s;
}

.surface-option-compact input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.surface-option-compact img {
  width: 100%;
  aspect-ratio: 16/9;
  object-fit: cover;
  border-radius: 4px;
}

.surface-option-compact .surface-caption {
  font-size: 0.7rem;
  color: #374151;
  text-align: center;
  font-weight: 500;
}

.surface-option-compact.selected {
  border-color: var(--brand-500, #ff6600);
  box-shadow: 0 0 0 2px rgba(255, 102, 0, 0.15);
  background: var(--brand-50, #ffe6d5);
}

/* Tire Editor */
.tire-editor {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 0.75rem;
  width: 100%;
}

.tire-groups-compact {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.tire-group-compact {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.tire-group-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: #374151;
}

.tire-group-header i {
  color: var(--brand-500, #ff6600);
}

.tire-options {
  display: flex;
  gap: 0.5rem;
}

.tire-option-compact {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  border: 2px solid #e5e7eb;
  border-radius: 6px;
  padding: 0.5rem;
  cursor: pointer;
  background: #fff;
  transition: all 0.2s;
}

.tire-option-compact input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.tire-option-compact img {
  width: 2rem;
  height: 2rem;
  object-fit: cover;
  border-radius: 4px;
}

.tire-option-compact .tire-caption {
  font-size: 0.7rem;
  color: #374151;
  text-align: center;
  font-weight: 500;
}

.tire-option-compact.selected {
  border-color: var(--brand-500, #ff6600);
  box-shadow: 0 0 0 2px rgba(255, 102, 0, 0.15);
  background: var(--brand-50, #ffe6d5);
}

/* Close editor button */
.close-editor-btn {
  align-self: center;
  padding: 0.5rem 1rem;
  background: var(--brand-500, #ff6600);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.close-editor-btn:hover {
  background: var(--brand-600, #e65c00);
}

/* Responsive layout adjustments */
@media (max-width: 640px) {
  .info-row {
    flex-direction: column;
    gap: 0.75rem;
  }

  .info-row .info-item-compact {
    flex: 1 !important;
  }

  .tire-recommendations-compact {
    flex-direction: column;
    gap: 0.75rem;
  }

  .surface-options-grid {
    grid-template-columns: 1fr;
  }

  .tire-options {
    flex-direction: column;
  }
}
</style>
