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
                <span
                  v-for="tick in [1, 2, 3, 4, 5]"
                  :key="tick"
                  class="tick-mark"
                  :class="{
                    active:
                      tick >= segmentFilters.difficultyMin &&
                      tick <= segmentFilters.difficultyMax
                  }"
                >
                  {{ tick }}
                </span>
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
          :class="{ disabled: !startWaypoint || !endWaypoint }"
          :disabled="!startWaypoint || !endWaypoint"
          @click="emit('generate-route')"
        >
          <i class="fa-solid fa-route"></i>
          <span>{{ t('routePlanner.generateRoute') }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
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
</script>

<style scoped>
/* Sidebar Menu Styles */
.sidebar-menu {
  position: fixed;
  top: var(--navbar-height);
  left: 0;
  width: 300px;
  height: calc(100vh - var(--navbar-height));
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-right: 1px solid rgba(229, 231, 235, 0.5);
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
  z-index: 2000;
  transform: translateX(-100%);
  transition: transform 0.3s ease-in-out;
  overflow-y: auto;
}

.sidebar-menu.sidebar-open {
  transform: translateX(0);
}

.sidebar-content {
  padding: 1.5rem;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.sidebar-title {
  margin: 0;
  color: #374151;
  font-size: 1rem;
  font-weight: 600;
}

.sidebar-close {
  width: 32px;
  height: 32px;
  border: none;
  background: #f3f4f6;
  color: #6b7280;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.sidebar-close:hover {
  background: #e5e7eb;
  color: #374151;
}

.sidebar-options {
  margin-bottom: 1rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid rgba(229, 231, 235, 0.5);
  flex-shrink: 0;
}

.free-mode-instructions {
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  background: rgba(248, 250, 252, 0.8);
  border-radius: 6px;
  border: 1px solid rgba(229, 231, 235, 0.3);
  flex-shrink: 0;
}

.map-navigation-instructions {
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  background: rgba(243, 244, 246, 0.8);
  border-radius: 6px;
  border: 1px solid rgba(229, 231, 235, 0.3);
  flex-shrink: 0;
}

.instructions-title {
  margin: 0 0 0.75rem 0;
  color: #374151;
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
  color: #6b7280;
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
  color: #6b7280;
  font-size: 0.875rem;
  text-align: center;
  font-style: italic;
}

.mode-toggle-container {
  margin-bottom: 0;
  padding: 1rem;
  background: rgba(248, 250, 252, 0.8);
  border-radius: 8px;
  border: 1px solid rgba(229, 231, 235, 0.3);
  transition: all 0.2s ease;
}

.mode-toggle-container:hover {
  background: rgba(248, 250, 252, 1);
  border-color: rgba(var(--brand-primary-rgb), 0.3);
}

.mode-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.toggle-label {
  font-weight: 500;
  color: #374151;
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
  color: #6b7280;
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
  background-color: #d1d5db;
  transition: 0.3s;
  border-radius: 24px;
}

.toggle-slider:before {
  position: absolute;
  content: '';
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.toggle-switch input:checked + .toggle-slider {
  background-color: var(--brand-primary);
}

.toggle-switch input:checked + .toggle-slider:before {
  transform: translateX(24px);
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
  color: #374151;
  font-size: 1rem;
  font-weight: 600;
  text-align: center;
}

.todo-instructions {
  margin: 0 0 1rem 0;
  color: #6b7280;
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
  background: rgba(255, 255, 255, 0.7);
  border-radius: 6px;
  border: 1px solid rgba(229, 231, 235, 0.5);
  transition: all 0.3s ease;
}

.todo-item:hover {
  background: rgba(255, 255, 255, 0.9);
  border-color: rgba(59, 130, 246, 0.3);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.todo-item.completed {
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.3);
  cursor: help;
}

.todo-item.completed .todo-text {
  color: #1d4ed8;
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
  color: #6b7280;
}

.todo-item.completed .todo-checkbox {
  color: #1d4ed8;
  background: rgba(59, 130, 246, 0.2);
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
  color: #374151;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.3s ease;
  line-height: 1.4;
}

.todo-text strong {
  font-weight: 700;
  color: #1f2937;
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
  background: rgba(0, 0, 0, 0.02);
}

.filters-title {
  margin: 0;
  color: #374151;
  font-size: 1rem;
  font-weight: 600;
  text-align: center;
  flex: 1;
}

.filters-chevron {
  font-size: 0.875rem;
  color: #6b7280;
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
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-group-title {
  margin: 0;
  color: #374151;
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
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(229, 231, 235, 0.8);
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
}

.tire-condition-group:hover {
  background: rgba(255, 255, 255, 0.7);
  border-color: rgba(209, 213, 219, 0.9);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
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
  color: #6b7280;
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

/* Keep tire filters on one row */
.filter-group:has(.tire-filter-image) .filter-options {
  flex-wrap: nowrap;
}

.filter-btn {
  padding: 0.35rem 0.65rem;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(209, 213, 219, 0.8);
  border-radius: 4px;
  color: #4b5563;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: normal;
  text-align: center;
}

.filter-btn:hover {
  background: rgba(255, 255, 255, 1);
  border-color: rgba(var(--brand-primary-rgb), 0.4);
  color: #c2410c;
}

.filter-btn.active {
  background: var(--brand-primary);
  border-color: #ea580c;
  color: white;
  font-weight: 600;
}

.filter-btn.active:hover {
  background: #ea580c;
  border-color: #c2410c;
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
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
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
  border-top-color: white;
}

.custom-tooltip::before {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 7px solid transparent;
  border-top-color: #e5e7eb;
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
  background: #f9fafb;
}

.tooltip-text {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
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
  min-height: fit-content;
  max-height: calc(100vh - var(--navbar-height) - 200px);
}

.selected-segments-title {
  margin: 0 0 1rem 0;
  color: #374151;
  font-size: 1rem;
  font-weight: 600;
  text-align: center;
  flex-shrink: 0;
}

.no-segments-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #6b7280;
  font-size: 0.875rem;
  text-align: center;
  margin-bottom: 1rem;
  flex-shrink: 0;
  justify-content: center;
}

.spinning-wheel {
  width: 16px;
  height: 16px;
  border: 2px solid #e5e7eb;
  border-top: 2px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  flex-shrink: 0;
}

.selected-segments-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  max-height: calc(100vh - var(--navbar-height) - 280px);
}

.selected-segment-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.3rem 0.7rem 0.3rem 0.75rem;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 6px;
  border: 1px solid rgba(229, 231, 235, 0.5);
  transition: all 0.2s ease;
}

.selected-segment-item:hover {
  background: rgba(255, 255, 255, 1);
  border-color: rgba(var(--brand-primary-rgb), 0.3);
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
  color: #9ca3af;
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
  color: #374151;
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

/* Responsive adjustments for sidebar */
@media (max-width: 768px) {
  .sidebar-menu {
    width: 280px;
  }

  .sidebar-content {
    padding: 1rem;
  }

  .mode-toggle {
    flex-direction: column;
    gap: 0.75rem;
    text-align: center;
  }

  .toggle-label {
    font-size: 0.8rem;
  }

  .mode-toggle-container {
    padding: 0.75rem;
  }
}
</style>
