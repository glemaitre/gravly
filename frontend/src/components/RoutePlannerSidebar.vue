<template>
  <!-- Sidebar Menu -->
  <div class="sidebar-menu" :class="{ 'sidebar-open': showSidebar }">
    <div class="sidebar-content">
      <div class="sidebar-header">
        <h4 class="sidebar-title">{{ t('routePlanner.routingMode') }}</h4>
        <button class="sidebar-close" @click="emit('close')">
          <i class="fa-solid fa-times"></i>
        </button>
      </div>

      <div class="sidebar-options">
        <div class="mode-toggle-container">
          <div class="mode-toggle">
            <span class="toggle-label">
              {{ t('routePlanner.standardMode') }}
              <i
                class="fa-solid fa-info-circle mode-info-icon"
                :title="t('routePlanner.standardModeDescription')"
              ></i>
            </span>
            <label class="toggle-switch">
              <input
                type="checkbox"
                :checked="routeMode === 'startEnd'"
                @change="emit('toggle-mode')"
              />
              <span class="toggle-slider"></span>
            </label>
            <span class="toggle-label">
              {{ t('routePlanner.startEndMode') }}
              <i
                class="fa-solid fa-info-circle mode-info-icon"
                :title="t('routePlanner.startEndModeDescription')"
              ></i>
            </span>
          </div>
        </div>
      </div>

      <!-- Free Mode Instructions -->
      <div v-if="routeMode === 'standard'" class="free-mode-instructions">
        <h4 class="instructions-title">
          {{ t('routePlanner.freeModeTitleInstructions') }}
        </h4>
        <ul class="instructions-list">
          <li>
            <i class="fa-solid fa-map-pin"></i>
            {{ t('routePlanner.clickMapToAddWaypoint') }}
          </li>
          <li>
            <i class="fa-solid fa-hand-pointer"></i>
            {{ t('routePlanner.dragWaypointToMove') }}
          </li>
          <li>
            <i class="fa-solid fa-route"></i>
            {{ t('routePlanner.dragRouteToInsertWaypoint') }}
          </li>
          <li>
            <i class="fa-solid fa-trash-alt"></i>
            {{ t('routePlanner.rightClickWaypointToRemove') }}
          </li>
        </ul>
      </div>

      <!-- Map Navigation Instructions -->
      <div v-if="routeMode === 'standard'" class="map-navigation-instructions">
        <h4 class="instructions-title">
          {{ t('routePlanner.mapNavigationTitle') }}
        </h4>
        <ul class="instructions-list">
          <li>
            <i class="fa-solid fa-hand"></i>
            {{ t('routePlanner.dragMapToPan') }}
          </li>
          <li>
            <i class="fa-solid fa-magnifying-glass-plus"></i>
            {{ t('routePlanner.scrollToZoom') }}
          </li>
        </ul>
      </div>

      <!-- Guided Mode Todo List -->
      <div v-if="routeMode === 'startEnd'" class="guided-todo-list">
        <h4 class="todo-title">
          <i class="fa-solid fa-list-check"></i>
          {{ t('routePlanner.guidedTodoList') }}
        </h4>
        <p class="todo-instructions">
          {{ t('routePlanner.guidedTodoInstructions') }}
        </p>
        <div class="todo-items">
          <div
            class="todo-item"
            :class="{ completed: startWaypoint }"
            :title="
              startWaypoint
                ? `Lat: ${startWaypoint.lat.toFixed(6)}, Lng: ${startWaypoint.lng.toFixed(6)}`
                : ''
            "
          >
            <div class="todo-main-content">
              <div class="todo-checkbox">
                <i v-if="startWaypoint" class="fa-solid fa-check"></i>
                <i v-else class="fa-solid fa-spinner fa-spin waiting-icon"></i>
              </div>
              <div class="todo-content">
                <span class="todo-text">
                  <template v-if="startWaypoint">
                    <strong>Starting</strong> point set
                  </template>
                  <template v-else> Set <strong>starting</strong> point </template>
                </span>
              </div>
            </div>
          </div>
          <div
            class="todo-item"
            :class="{ completed: endWaypoint }"
            :title="
              endWaypoint
                ? `Lat: ${endWaypoint.lat.toFixed(6)}, Lng: ${endWaypoint.lng.toFixed(6)}`
                : ''
            "
          >
            <div class="todo-main-content">
              <div class="todo-checkbox">
                <i v-if="endWaypoint" class="fa-solid fa-check"></i>
                <i v-else class="fa-solid fa-spinner fa-spin waiting-icon"></i>
              </div>
              <div class="todo-content">
                <span class="todo-text">
                  <template v-if="endWaypoint">
                    <strong>Ending</strong> point set
                  </template>
                  <template v-else> Set <strong>ending</strong> point </template>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Segment Filters -->
      <div
        v-if="routeMode === 'startEnd' && startWaypoint && endWaypoint"
        class="segment-filters-section"
      >
        <div class="filters-header">
          <button class="filters-toggle-btn" @click="emit('toggle-filters')">
            <h4 class="filters-title">
              <i class="fa-solid fa-filter"></i>
              {{ t('routePlanner.filters') }}
            </h4>
            <i
              class="fa-solid fa-chevron-down filters-chevron"
              :class="{ expanded: filtersExpanded }"
            ></i>
          </button>
          <button
            v-if="hasActiveFilters"
            class="clear-filters-btn"
            @click="emit('clear-filters')"
          >
            <i class="fa-solid fa-times"></i>
            <span>{{ t('routePlanner.clearFilters') }}</span>
          </button>
        </div>

        <div v-show="filtersExpanded" class="filters-content">
          <!-- Difficulty Filter -->
          <div class="filter-group">
            <h5 class="filter-group-title">
              <i class="fa-solid fa-signal"></i>
              {{ t('routePlanner.difficulty') }}
            </h5>
            <div class="difficulty-range-container">
              <div class="difficulty-sliders">
                <div class="slider-track-background"></div>
                <div
                  class="slider-track-fill"
                  :style="{
                    left: `${((segmentFilters.difficultyMin - 1) / 4) * 100}%`,
                    right: `${((5 - segmentFilters.difficultyMax) / 4) * 100}%`
                  }"
                ></div>
                <input
                  type="range"
                  min="1"
                  max="5"
                  step="1"
                  :value="segmentFilters.difficultyMin"
                  @input="onDifficultyMinChange($event)"
                  class="difficulty-slider difficulty-slider-min"
                />
                <input
                  type="range"
                  min="1"
                  max="5"
                  step="1"
                  :value="segmentFilters.difficultyMax"
                  @input="onDifficultyMaxChange($event)"
                  class="difficulty-slider difficulty-slider-max"
                />
              </div>
              <div class="difficulty-range-ticks">
                <div
                  v-for="tick in [1, 2, 3, 4, 5]"
                  :key="tick"
                  class="tick-mark-wrapper"
                  @mouseenter="showDifficultyTooltip($event)"
                  @mouseleave="hideDifficultyTooltip"
                  @mousemove="updateDifficultyTooltipPosition($event)"
                >
                  <span
                    class="tick-mark"
                    :class="{
                      active:
                        tick >= segmentFilters.difficultyMin &&
                        tick <= segmentFilters.difficultyMax
                    }"
                  >
                    {{ tick }}
                  </span>
                  <div class="difficulty-tooltip">
                    {{ getDifficultyDescription(tick) }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Surface Type Filter -->
          <div class="filter-group">
            <h5 class="filter-group-title">
              <i class="fa-solid fa-road"></i>
              {{ t('routePlanner.surface') }}
            </h5>
            <div class="filter-options">
              <div
                v-for="surfaceType in surfaceTypes"
                :key="surfaceType.value"
                class="filter-btn-wrapper"
              >
                <button
                  class="filter-btn filter-btn-with-image"
                  :class="{
                    active: segmentFilters.surface.includes(surfaceType.value)
                  }"
                  @click="emit('toggle-filter', 'surface', surfaceType.value)"
                >
                  <img
                    :src="getSurfaceImage(surfaceType.value)"
                    :alt="surfaceType.label"
                    class="surface-filter-image"
                  />
                  <span class="mobile-description">{{ surfaceType.label }}</span>
                </button>
                <div class="custom-tooltip">
                  <img
                    :src="getSurfaceImage(surfaceType.value)"
                    :alt="surfaceType.label"
                    class="tooltip-image"
                  />
                  <span class="tooltip-text">{{ surfaceType.label }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Tire Filter -->
          <div class="filter-group">
            <h5 class="filter-group-title">
              <i class="fa-solid fa-circle"></i>
              {{ t('routePlanner.tire') }}
            </h5>

            <!-- Dry Tires -->
            <div class="tire-condition-group">
              <div class="tire-condition-header">
                <i class="fa-solid fa-sun"></i>
                <span>{{ t('routePlanner.dry') }}</span>
              </div>
              <div class="filter-options">
                <div
                  v-for="tireType in tireTypes"
                  :key="`dry-${tireType.value}`"
                  class="filter-btn-wrapper"
                >
                  <button
                    class="filter-btn filter-btn-with-image"
                    :class="{ active: segmentFilters.tireDry.includes(tireType.value) }"
                    @click="emit('toggle-filter', 'tireDry', tireType.value)"
                  >
                    <img
                      :src="getTireImage(tireType.value)"
                      :alt="tireType.label"
                      class="tire-filter-image"
                    />
                    <span class="mobile-description">{{ tireType.label }}</span>
                  </button>
                  <div class="custom-tooltip">
                    <img
                      :src="getTireImage(tireType.value)"
                      :alt="tireType.label"
                      class="tooltip-image tooltip-image-tire"
                    />
                    <span class="tooltip-text">{{ tireType.label }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Wet Tires -->
            <div class="tire-condition-group">
              <div class="tire-condition-header">
                <i class="fa-solid fa-cloud-rain"></i>
                <span>{{ t('routePlanner.wet') }}</span>
              </div>
              <div class="filter-options">
                <div
                  v-for="tireType in tireTypes"
                  :key="`wet-${tireType.value}`"
                  class="filter-btn-wrapper"
                >
                  <button
                    class="filter-btn filter-btn-with-image"
                    :class="{ active: segmentFilters.tireWet.includes(tireType.value) }"
                    @click="emit('toggle-filter', 'tireWet', tireType.value)"
                  >
                    <img
                      :src="getTireImage(tireType.value)"
                      :alt="tireType.label"
                      class="tire-filter-image"
                    />
                    <span class="mobile-description">{{ tireType.label }}</span>
                  </button>
                  <div class="custom-tooltip">
                    <img
                      :src="getTireImage(tireType.value)"
                      :alt="tireType.label"
                      class="tooltip-image tooltip-image-tire"
                    />
                    <span class="tooltip-text">{{ tireType.label }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Selected Segments -->
      <div
        v-if="routeMode === 'startEnd' && startWaypoint && endWaypoint"
        class="selected-segments-section"
      >
        <h4 class="selected-segments-title">
          <i class="fa-solid fa-route"></i>
          {{ t('routePlanner.selectedSegments') }}
        </h4>

        <!-- Empty state message -->
        <div v-if="selectedSegments.length === 0" class="no-segments-message">
          <div class="spinning-wheel"></div>
          <span>{{ t('routePlanner.noSegmentsSelectedMessage') }}</span>
        </div>

        <div class="selected-segments-list">
          <div
            v-for="(segment, index) in selectedSegments"
            :key="`${segment.id}-${segment.isReversed || false}`"
            class="selected-segment-item"
            draggable="true"
            @dragstart="emit('drag-start', $event, index)"
            @dragover="emit('drag-over', $event)"
            @drop="emit('drag-drop', $event, index)"
            @dragend="emit('drag-end')"
            @mouseenter="emit('segment-hover', segment)"
            @mouseleave="emit('segment-leave', segment)"
          >
            <div class="segment-index">{{ index + 1 }}</div>
            <div class="segment-drag-handle">
              <i class="fa-solid fa-grip-vertical"></i>
            </div>
            <div class="segment-name">{{ segment.name }}</div>
            <div class="segment-controls">
              <button
                class="reverse-segment-btn"
                @click="emit('reverse-segment', segment)"
                :title="segment.isReversed ? 'Original direction' : 'Reverse direction'"
              >
                <i class="fa-solid fa-arrow-right-arrow-left"></i>
              </button>
              <button
                class="remove-segment-btn"
                @click="emit('deselect-segment', segment)"
                :title="t('routePlanner.removeSegment')"
              >
                <i class="fa-solid fa-times"></i>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Generate Route Button - Always visible in startEnd mode -->
      <div v-if="routeMode === 'startEnd'" class="generate-route-section">
        <button
          class="generate-route-btn"
          :class="{
            disabled:
              !startWaypoint || !endWaypoint || routeGenerationProgress.isGenerating
          }"
          :disabled="
            !startWaypoint || !endWaypoint || routeGenerationProgress.isGenerating
          "
          @click="emit('generate-route')"
        >
          <i
            class="fa-solid"
            :class="
              routeGenerationProgress.isGenerating ? 'fa-spinner fa-spin' : 'fa-route'
            "
          ></i>
          <span>{{
            routeGenerationProgress.isGenerating
              ? t('routePlanner.generatingRoute')
              : t('routePlanner.generateRoute')
          }}</span>
        </button>

        <!-- Progress Bar -->
        <div
          v-if="routeGenerationProgress.isGenerating"
          class="route-progress-container"
        >
          <div class="progress-bar-wrapper">
            <div
              class="progress-bar-fill"
              :style="{
                width: `${(routeGenerationProgress.current / routeGenerationProgress.total) * 100}%`
              }"
            ></div>
          </div>
          <div class="progress-info">
            <span class="progress-message">{{ routeGenerationProgress.message }}</span>
            <span class="progress-counter"
              >{{ routeGenerationProgress.current }} /
              {{ routeGenerationProgress.total }}</span
            >
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { TrackResponse } from '../types'

// Import tire images
import tireSlickUrl from '../assets/images/slick.png'
import tireSemiSlickUrl from '../assets/images/semi-slick.png'
import tireKnobsUrl from '../assets/images/ext.png'

// Import surface images
import brokenPavedRoadUrl from '../assets/images/broken-paved-road.jpeg'
import dirtyRoadUrl from '../assets/images/dirty-road.jpeg'
import smallStoneRoadUrl from '../assets/images/small-stone-road.jpeg'
import bigStoneRoadUrl from '../assets/images/big-stone-road.jpeg'
import fieldTrailUrl from '../assets/images/field-trail.jpeg'
import forestTrailUrl from '../assets/images/forest-trail.jpeg'

// Types
interface SegmentFilters {
  difficultyMin: number
  difficultyMax: number
  surface: string[]
  tireDry: string[]
  tireWet: string[]
}

// Props
const props = defineProps<{
  showSidebar: boolean
  routeMode: 'standard' | 'startEnd'
  startWaypoint: any
  endWaypoint: any
  selectedSegments: TrackResponse[]
  segmentFilters: SegmentFilters
  filtersExpanded: boolean
  routeDistance: number
  elevationStats: {
    totalGain: number
    totalLoss: number
    maxElevation: number
    minElevation: number
  }
  routeGenerationProgress: {
    isGenerating: boolean
    current: number
    total: number
    message: string
  }
}>()

// Emits
const emit = defineEmits<{
  close: []
  'toggle-mode': []
  'toggle-filters': []
  'toggle-filter': [type: 'surface' | 'tireDry' | 'tireWet', value: string]
  'update:difficulty-min': [value: number]
  'update:difficulty-max': [value: number]
  'clear-filters': []
  'deselect-segment': [segment: TrackResponse]
  'reverse-segment': [segment: TrackResponse]
  'drag-start': [event: DragEvent, index: number]
  'drag-over': [event: DragEvent]
  'drag-drop': [event: DragEvent, index: number]
  'drag-end': []
  'segment-hover': [segment: TrackResponse]
  'segment-leave': [segment: TrackResponse]
  'generate-route': []
  'route-saved': [routeId: number]
}>()

// i18n
const { t } = useI18n()

// Tire images mapping
const tireImages = {
  slick: tireSlickUrl,
  'semi-slick': tireSemiSlickUrl,
  knobs: tireKnobsUrl
}

// Surface images mapping
const surfaceImages = {
  'broken-paved-road': brokenPavedRoadUrl,
  'dirty-road': dirtyRoadUrl,
  'small-stone-road': smallStoneRoadUrl,
  'big-stone-road': bigStoneRoadUrl,
  'field-trail': fieldTrailUrl,
  'forest-trail': forestTrailUrl
}

// Surface and tire types for filters
const surfaceTypes = computed(() => [
  {
    value: 'big-stone-road',
    label: t('routePlanner.surfaceTypes.bigStoneRoad')
  },
  {
    value: 'broken-paved-road',
    label: t('routePlanner.surfaceTypes.brokenPavedRoad')
  },
  { value: 'dirty-road', label: t('routePlanner.surfaceTypes.dirtyRoad') },
  {
    value: 'field-trail',
    label: t('routePlanner.surfaceTypes.fieldTrail')
  },
  {
    value: 'forest-trail',
    label: t('routePlanner.surfaceTypes.forestTrail')
  },
  {
    value: 'small-stone-road',
    label: t('routePlanner.surfaceTypes.smallStoneRoad')
  }
])

const tireTypes = computed(() => [
  { value: 'slick', label: t('routePlanner.tireTypes.slick') },
  { value: 'semi-slick', label: t('routePlanner.tireTypes.semiSlick') },
  { value: 'knobs', label: t('routePlanner.tireTypes.knobs') }
])

// Computed property for checking if there are active filters
const hasActiveFilters = computed(() => {
  return (
    props.segmentFilters.difficultyMin !== 1 ||
    props.segmentFilters.difficultyMax !== 5 ||
    props.segmentFilters.surface.length > 0 ||
    props.segmentFilters.tireDry.length > 0 ||
    props.segmentFilters.tireWet.length > 0
  )
})

// Helper functions
function getTireImage(tireType: string): string {
  return tireImages[tireType as keyof typeof tireImages] || tireSlickUrl
}

function getSurfaceImage(surfaceType: string): string {
  return surfaceImages[surfaceType as keyof typeof surfaceImages] || brokenPavedRoadUrl
}

function onDifficultyMinChange(event: Event) {
  const value = Number((event.target as HTMLInputElement).value)
  emit('update:difficulty-min', value)
}

function onDifficultyMaxChange(event: Event) {
  const value = Number((event.target as HTMLInputElement).value)
  emit('update:difficulty-max', value)
}

// Difficulty tooltip functionality
const difficultyTooltipVisible = ref(false)

function getDifficultyDescription(level: number): string {
  // Map difficulty levels to their descriptions
  switch (level) {
    case 1:
      return t('difficulty.descriptions.level1')
    case 2:
      return t('difficulty.descriptions.level2')
    case 3:
      return t('difficulty.descriptions.level3')
    case 4:
      return t('difficulty.descriptions.level4')
    case 5:
      return t('difficulty.descriptions.level5')
    default:
      return t('difficulty.descriptions.level5') // Default to level 5 for invalid levels
  }
}

function showDifficultyTooltip(event: MouseEvent) {
  difficultyTooltipVisible.value = true
  updateDifficultyTooltipPosition(event)
}

function hideDifficultyTooltip() {
  difficultyTooltipVisible.value = false
}

function updateDifficultyTooltipPosition(event: MouseEvent) {
  if (!difficultyTooltipVisible.value) return

  const target = event.currentTarget as HTMLElement
  const tooltip = target.querySelector('.difficulty-tooltip') as HTMLElement
  if (!tooltip) return

  const rect = target.getBoundingClientRect()
  const sidebarWidth = 300 // Sidebar width
  const tooltipWidth = sidebarWidth * 0.8 // 80% of sidebar width

  // Position tooltip within the sidebar bounds
  let left = rect.left + rect.width / 2 - tooltipWidth / 2

  // Ensure tooltip stays within sidebar bounds
  const sidebarLeft = 0 // Sidebar starts at left edge
  const sidebarRight = sidebarWidth

  if (left < sidebarLeft + 10) {
    left = sidebarLeft + 10
  } else if (left + tooltipWidth > sidebarRight - 10) {
    left = sidebarRight - tooltipWidth - 10
  }

  tooltip.style.left = `${left}px`
  tooltip.style.top = `${rect.top - 120}px` // Fixed offset above the tick mark
}
</script>

<style scoped>
/* Sidebar Menu Styles */
.sidebar-menu {
  position: fixed;
  top: var(--navbar-height);
  left: 0;
  width: 300px;
  height: calc(100vh - var(--navbar-height));
  background: rgba(var(--bg-primary-rgb), 0.98);
  backdrop-filter: blur(10px);
  border-right: 1px solid var(--border-primary);
  box-shadow: var(--shadow-lg);
  z-index: 2000;
  transform: translateX(-100%);
  transition: transform 0.3s ease-in-out;
  overflow-y: auto;
  overflow: visible; /* Allow tooltips to be visible */
}

.sidebar-menu.sidebar-open {
  transform: translateX(0);
}

.sidebar-content {
  padding: 1.5rem;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  min-height: 0;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.sidebar-title {
  margin: 0;
  color: var(--text-primary);
  font-size: 1rem;
  font-weight: 600;
}

.sidebar-close {
  width: 32px;
  height: 32px;
  border: none;
  background: var(--bg-secondary);
  color: var(--text-tertiary);
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.sidebar-close:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.sidebar-options {
  margin-bottom: 1rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--border-muted);
  flex-shrink: 0;
}

.free-mode-instructions {
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  background: var(--bg-secondary);
  border-radius: 6px;
  border: 1px solid var(--border-secondary);
  flex-shrink: 0;
}

.map-navigation-instructions {
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  background: var(--bg-secondary);
  border-radius: 6px;
  border: 1px solid var(--border-secondary);
  flex-shrink: 0;
}

.instructions-title {
  margin: 0 0 0.75rem 0;
  color: var(--text-primary);
  font-size: 0.875rem;
  font-weight: 600;
  text-align: center;
}

.instructions-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.instructions-list li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-secondary);
  font-size: 0.8rem;
  line-height: 1.4;
}

.instructions-list li i {
  font-size: 0.75rem;
  color: var(--brand-primary);
  flex-shrink: 0;
  width: 16px;
  text-align: center;
}

.instruction-text {
  margin: 0;
  color: var(--text-tertiary);
  font-size: 0.875rem;
  text-align: center;
  font-style: italic;
}

.mode-toggle-container {
  margin-bottom: 0;
  padding: 1rem;
  background: var(--card-bg);
  border-radius: 8px;
  border: 1px solid var(--card-border);
  transition: all 0.2s ease;
}

.mode-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.toggle-label {
  font-weight: 500;
  color: var(--text-primary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: color 0.2s ease;
}

.toggle-label:hover {
  color: var(--brand-primary);
}

.mode-info-icon {
  margin-left: 0.25rem;
  font-size: 0.75rem;
  color: var(--text-tertiary);
  cursor: help;
  transition: color 0.2s ease;
}

.mode-info-icon:hover {
  color: var(--brand-primary);
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 24px;
  cursor: pointer;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--border-secondary);
  transition: 0.3s;
  border-radius: 24px;
}

.toggle-slider:hover {
  background-color: var(--border-primary);
  box-shadow: 0 0 0 3px rgba(var(--brand-primary-rgb), 0.1);
}

.toggle-slider:before {
  position: absolute;
  content: '';
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: var(--card-bg);
  transition: 0.3s;
  border-radius: 50%;
  box-shadow: var(--shadow-sm);
}

.toggle-slider:hover:before {
  transform: scale(1.1);
  box-shadow: var(--shadow-md);
}

.toggle-switch input:checked + .toggle-slider {
  background-color: var(--brand-primary);
}

.toggle-switch input:checked + .toggle-slider:hover {
  background-color: var(--brand-primary-hover);
  box-shadow: 0 0 0 3px rgba(var(--brand-primary-rgb), 0.2);
}

.toggle-switch input:checked + .toggle-slider:before {
  transform: translateX(24px);
}

.toggle-switch input:checked + .toggle-slider:hover:before {
  transform: translateX(24px) scale(1.1);
}

.guided-todo-list {
  background: rgba(var(--brand-primary-rgb), 0.05);
  border: 1px solid rgba(var(--brand-primary-rgb), 0.2);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.todo-title {
  margin: 0 0 0.5rem 0;
  color: var(--text-primary);
  font-size: 1rem;
  font-weight: 600;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.todo-instructions {
  margin: 0 0 1rem 0;
  color: var(--text-tertiary);
  font-size: 0.75rem;
  text-align: center;
  font-style: italic;
}

.todo-items {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.todo-item {
  display: flex;
  flex-direction: column;
  padding: 0.5rem 0.75rem;
  background: var(--card-bg);
  border-radius: 6px;
  border: 1px solid var(--card-border);
  transition: all 0.3s ease;
}

.todo-item:hover {
  background: var(--bg-hover);
  border-color: var(--status-info);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.todo-item.completed {
  background: rgba(var(--status-success-rgb), 0.1);
  border-color: var(--status-success);
  cursor: help;
}

.todo-item.completed .todo-text {
  color: var(--status-success);
}

.todo-checkbox {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.todo-item:not(.completed) .todo-checkbox {
  color: var(--text-tertiary);
}

.todo-item.completed .todo-checkbox {
  color: var(--status-success);
  background: rgba(var(--status-success-rgb), 0.2);
}

.todo-checkbox i {
  font-size: 12px;
}

.todo-main-content {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.todo-content {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1;
}

.todo-text {
  color: var(--text-primary);
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.3s ease;
  line-height: 1.4;
}

.todo-text strong {
  font-weight: 700;
  color: inherit;
}

.waiting-icon {
  color: var(--brand-primary);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Generate Route Section */
.generate-route-section {
  padding: 0.2rem;
  flex-shrink: 0;
  margin-top: auto;
}

.generate-route-btn {
  width: 100%;
  padding: 0.75rem 1rem;
  background: var(--brand-primary);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(var(--brand-primary-rgb), 0.2);
}

.generate-route-btn:hover:not(.disabled) {
  background: var(--brand-primary-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(var(--brand-primary-rgb), 0.3);
}

.generate-route-btn.disabled {
  background: #9ca3af;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.generate-route-btn.disabled:hover {
  background: #9ca3af;
  transform: none;
  box-shadow: none;
}

.generate-route-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(var(--brand-primary-rgb), 0.2);
}

.generate-route-btn i {
  font-size: 1rem;
}

/* Route generation progress bar */
.route-progress-container {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 8px;
  border: 1px solid rgba(229, 231, 235, 0.5);
}

.progress-bar-wrapper {
  width: 100%;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--brand-primary) 0%, #ea580c 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
  position: relative;
  overflow: hidden;
}

.progress-bar-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.3) 50%,
    transparent 100%
  );
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
}

.progress-message {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  font-weight: 500;
  flex: 1;
}

.progress-counter {
  font-size: 0.75rem;
  color: var(--brand-primary);
  font-weight: 600;
  white-space: nowrap;
}

/* Segment filters section styles */
.segment-filters-section {
  background: rgba(var(--brand-primary-rgb), 0.05);
  border: 1px solid rgba(var(--brand-primary-rgb), 0.2);
  border-radius: 8px;
  padding: 0.75rem;
  margin-bottom: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  flex-shrink: 0;
}

.filters-header {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 0.75rem;
}

.filters-toggle-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 0.5rem;
  background: transparent;
  border: none;
  cursor: pointer;
  border-radius: 6px;
  transition: background-color 0.2s ease;
}

.filters-toggle-btn:hover {
  background: var(--bg-hover);
}

.filters-title {
  margin: 0;
  color: var(--text-primary);
  font-size: 1rem;
  font-weight: 600;
  text-align: center;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.filters-chevron {
  font-size: 0.875rem;
  color: var(--text-tertiary);
  transition: transform 0.3s ease;
}

.filters-chevron.expanded {
  transform: rotate(180deg);
}

.clear-filters-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(var(--brand-primary-rgb), 0.1);
  border: 1px solid rgba(var(--brand-primary-rgb), 0.3);
  border-radius: 6px;
  color: var(--brand-primary);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.875rem;
  font-weight: 500;
  align-self: center;
}

.clear-filters-btn:hover {
  background: rgba(var(--brand-primary-rgb), 0.15);
  border-color: rgba(var(--brand-primary-rgb), 0.4);
}

.clear-filters-btn i {
  font-size: 0.875rem;
}

.filters-content {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding-top: 0.5rem;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-group-title {
  margin: 0;
  color: var(--text-primary);
  font-size: 0.8rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.filter-group-title i {
  font-size: 0.75rem;
  color: var(--brand-primary);
}

.filter-group-title .fa-cloud-rain {
  color: #3b82f6; /* Blue color for cloud icon */
}

/* Tire condition grouping */
.tire-condition-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 8px;
  box-shadow: var(--card-shadow);
  transition: all 0.2s ease;
}

.tire-condition-group:hover {
  background: var(--bg-hover);
  border-color: var(--border-secondary);
  box-shadow: var(--shadow-md);
}

.tire-condition-group:first-of-type {
  margin-top: 0.5rem;
}

.tire-condition-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-tertiary);
  margin-bottom: 0.25rem;
}

.tire-condition-header i {
  font-size: 0.7rem;
}

.tire-condition-header .fa-sun {
  color: #f59e0b; /* Orange/yellow for sun */
}

.tire-condition-header .fa-cloud-rain {
  color: #3b82f6; /* Blue for rain */
}

.filter-options {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

/* Difficulty range slider styles */
.difficulty-range-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 0.5rem 0;
}

.difficulty-sliders {
  position: relative;
  height: 24px;
  display: flex;
  align-items: center;
  margin: 0 1.1rem;
}

.slider-track-background {
  position: absolute;
  height: 6px;
  background: #e5e7eb;
  border-radius: 3px;
  z-index: 1;
  left: -9px;
  right: -9px;
}

.slider-track-fill {
  position: absolute;
  height: 6px;
  background: var(--brand-primary);
  border-radius: 3px;
  z-index: 2;
}

.difficulty-slider {
  position: absolute;
  width: calc(100% + 18px);
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: transparent;
  outline: none;
  pointer-events: none;
  z-index: 3;
  left: -9px;
}

.difficulty-slider::-webkit-slider-track {
  width: 100%;
  height: 6px;
  background: transparent;
  border-radius: 3px;
}

.difficulty-slider::-moz-range-track {
  width: 100%;
  height: 6px;
  background: transparent;
  border-radius: 3px;
}

.difficulty-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  background: var(--brand-primary);
  border: 2px solid white;
  border-radius: 50%;
  cursor: pointer;
  pointer-events: all;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: transform 0.2s ease;
  position: relative;
  z-index: 4;
  margin-left: -9px; /* Half of thumb width to center it with tick marks */
}

.difficulty-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  background: var(--brand-primary);
  border: 2px solid white;
  border-radius: 50%;
  cursor: pointer;
  pointer-events: all;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: transform 0.2s ease;
  position: relative;
  z-index: 4;
  margin-left: -9px; /* Half of thumb width to center it with tick marks */
}

.difficulty-slider::-webkit-slider-thumb:hover {
  transform: scale(1.15);
}

.difficulty-slider::-moz-range-thumb:hover {
  transform: scale(1.15);
}

.difficulty-range-ticks {
  display: flex;
  justify-content: space-between;
  margin: 0;
}

.tick-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  color: #9ca3af;
  font-weight: 500;
  flex: 1;
  text-align: center;
  padding: 0.25rem;
  margin: 0 0.2rem 0 0.2rem;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.tick-mark.active {
  background: var(--brand-primary);
  color: white;
  font-weight: 600;
}

/* Difficulty Tooltip */
.tick-mark-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  text-align: center;
  cursor: help;
}

.difficulty-tooltip {
  position: fixed !important;
  background: #1f2937;
  color: white;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  line-height: 1.4;
  width: 240px; /* 80% of 300px sidebar width */
  z-index: 99999 !important; /* Maximum z-index to ensure foreground display */
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  white-space: normal;
  word-wrap: break-word;
  text-align: center;
  transform: translateZ(0); /* Force hardware acceleration */
}

.tick-mark-wrapper:hover .difficulty-tooltip {
  opacity: 1;
  visibility: visible;
}

/* Keep tire filters on one row */
.filter-group:has(.tire-filter-image) .filter-options {
  flex-wrap: nowrap;
}

.filter-btn {
  padding: 0.35rem 0.65rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border-secondary);
  border-radius: 4px;
  color: var(--text-secondary);
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: normal;
  text-align: center;
}

.filter-btn:hover {
  background: var(--bg-hover);
  border-color: var(--brand-primary);
  color: var(--brand-primary);
}

.filter-btn.active {
  background: var(--brand-primary);
  border-color: var(--brand-primary);
  color: white;
  font-weight: 600;
}

.filter-btn.active:hover {
  background: var(--brand-primary-hover);
  border-color: var(--brand-primary-hover);
}

/* Filter button wrapper for tooltip positioning */
.filter-btn-wrapper {
  position: relative;
  display: inline-block;
}

/* Tire filter buttons - 3 per row, no wrapping */
.filter-group:has(.tire-filter-image) .filter-btn-wrapper {
  flex: 1;
  max-width: calc(33.333% - 0.34rem);
}

/* Surface filter buttons - 3 per row, can wrap to 2nd row */
.filter-group:has(.surface-filter-image) .filter-btn-wrapper {
  flex: 0 1 calc(33.333% - 0.34rem);
}

.filter-btn-with-image {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.3rem;
  min-width: 0;
  width: 100%;
}

.filter-btn-with-image span {
  text-align: center;
  width: 100%;
}

.tire-filter-image {
  width: 24px;
  height: 24px;
  object-fit: contain;
  flex-shrink: 0;
}

.surface-filter-image {
  width: 32px;
  height: 32px;
  object-fit: cover;
  border-radius: 4px;
  flex-shrink: 0;
}

/* Custom Tooltip Styles */
.custom-tooltip {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%) translateY(-8px);
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 8px;
  padding: 12px;
  box-shadow: var(--shadow-lg);
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transition:
    opacity 0.2s ease,
    visibility 0.2s ease,
    transform 0.2s ease;
  z-index: 1000;
  white-space: nowrap;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  min-width: 120px;
}

.filter-btn-wrapper:hover .custom-tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateX(-50%) translateY(-4px);
}

/* Arrow for tooltip */
.custom-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: var(--card-bg);
}

.custom-tooltip::before {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 7px solid transparent;
  border-top-color: var(--card-border);
  margin-top: 1px;
}

.tooltip-image {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 6px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.tooltip-image-tire {
  object-fit: contain;
  background: var(--bg-secondary);
}

.tooltip-text {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
  text-align: center;
  max-width: 150px;
}

/* Selected segments section styles */
.selected-segments-section {
  background: rgba(var(--brand-primary-rgb), 0.05);
  border: 1px solid rgba(var(--brand-primary-rgb), 0.2);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.selected-segments-title {
  margin: 0 0 1rem 0;
  color: var(--text-primary);
  font-size: 1rem;
  font-weight: 600;
  text-align: center;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.no-segments-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-tertiary);
  font-size: 0.875rem;
  text-align: center;
  margin-bottom: 1rem;
  flex-shrink: 0;
  justify-content: center;
}

.spinning-wheel {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-secondary);
  border-top: 2px solid var(--status-info);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  flex-shrink: 0;
}

.selected-segments-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.selected-segment-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.3rem 0.7rem 0.3rem 0.75rem;
  background: var(--card-bg);
  border-radius: 6px;
  border: 1px solid var(--card-border);
  transition: all 0.2s ease;
}

.selected-segment-item:hover {
  background: var(--bg-hover);
  border-color: var(--brand-primary);
}

.selected-segment-item.dragging {
  opacity: 0.5;
  transform: rotate(2deg);
}

.segment-index {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: var(--brand-primary);
  color: white;
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 600;
  margin-right: 0.5rem;
  flex-shrink: 0;
}

.segment-drag-handle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  margin-right: 0.5rem;
  color: var(--text-muted);
  cursor: grab;
  flex-shrink: 0;
}

.segment-drag-handle:active {
  cursor: grabbing;
}

.segment-drag-handle i {
  font-size: 0.75rem;
}

.selected-segment-item .segment-name {
  flex: 1;
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.875rem;
  line-height: 1.2;
  margin-left: 0.25rem;
}

.segment-controls {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.reverse-segment-btn {
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: #3b82f6;
  border-radius: 4px;
  padding: 0.25rem 0.4rem;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.75rem;
}

.reverse-segment-btn:hover {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.5);
  color: #1d4ed8;
}

.remove-segment-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.remove-segment-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #dc2626;
}

.remove-segment-btn i {
  font-size: 0.75rem;
}

/* Mobile descriptions - hidden on desktop, visible on mobile */
.mobile-description {
  display: none;
  font-size: 0.65rem;
  font-weight: 500;
  color: var(--text-tertiary);
  text-align: center;
  line-height: 1.2;
  margin-top: 0.25rem;
  white-space: normal;
  word-wrap: break-word;
  hyphens: auto;
  min-height: 2.4rem;
}

/* Show mobile descriptions on mobile devices */
@media (max-width: 768px) {
  .mobile-description {
    display: flex;
    justify-content: center;
    align-items: center;
  }

  /* Hide tooltips on mobile since descriptions are visible */
  .custom-tooltip {
    display: none !important;
  }

  /* Adjust filter button layout for mobile */
  .filter-btn-with-image {
    gap: 0.4rem;
    padding: 0.5rem 0.4rem;
    min-height: 4.5rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  /* Ensure consistent button sizes on mobile */
  .filter-btn-wrapper {
    min-height: 4.5rem;
    display: flex;
  }

  /* Surface filters - 2 per row on mobile */
  .filter-group:has(.surface-filter-image) .filter-btn-wrapper {
    flex: 0 1 calc(50% - 0.25rem);
    min-width: calc(50% - 0.25rem);
  }

  /* Tire filters - 3 per row on mobile but with consistent sizing */
  .filter-group:has(.tire-filter-image) .filter-btn-wrapper {
    flex: 0 1 calc(33.333% - 0.34rem);
    min-width: calc(33.333% - 0.34rem);
  }

  /* Ensure filter options container handles wrapping properly */
  .filter-options {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    justify-content: flex-start;
  }
}

/* Responsive adjustments for sidebar */
@media (max-width: 768px) {
  .sidebar-menu {
    width: 280px;
  }

  .sidebar-content {
    padding: 1rem;
  }

  .toggle-label {
    font-size: 0.8rem;
  }

  .mode-toggle-container {
    padding: 0.75rem;
  }
}
</style>
