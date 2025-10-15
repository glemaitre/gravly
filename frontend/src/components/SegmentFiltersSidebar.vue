<template>
  <div class="filters-sidebar" :class="{ open: showFilters }">
    <div class="filters-sidebar-content">
      <div class="filters-header">
        <h4 class="filters-title">
          <i class="fa-solid fa-filter"></i>
          {{ t('routePlanner.filters') }}
        </h4>
        <button type="button" class="filters-close" @click="emit('close')">
          <i class="fa-solid fa-times"></i>
        </button>
      </div>

      <!-- Name Filter -->
      <div class="filter-group">
        <h5 class="filter-group-title">
          <i class="fa-solid fa-search"></i>
          {{ t('routePlanner.searchByName') }}
        </h5>
        <input
          :value="nameFilter"
          @input="emit('update:nameFilter', ($event.target as HTMLInputElement).value)"
          type="text"
          class="name-filter-input"
          :placeholder="t('routePlanner.searchByNamePlaceholder')"
        />
      </div>

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
                left: `${((filters.difficultyMin - 1) / 4) * 100}%`,
                right: `${((5 - filters.difficultyMax) / 4) * 100}%`
              }"
            ></div>
            <input
              type="range"
              min="1"
              max="5"
              step="1"
              :value="filters.difficultyMin"
              @input="
                emit(
                  'update:difficultyMin',
                  Number(($event.target as HTMLInputElement).value)
                )
              "
              class="difficulty-slider difficulty-slider-min"
            />
            <input
              type="range"
              min="1"
              max="5"
              step="1"
              :value="filters.difficultyMax"
              @input="
                emit(
                  'update:difficultyMax',
                  Number(($event.target as HTMLInputElement).value)
                )
              "
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
                  active: tick >= filters.difficultyMin && tick <= filters.difficultyMax
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
              type="button"
              class="filter-btn filter-btn-with-image"
              :class="{ active: filters.surface.includes(surfaceType.value) }"
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
                type="button"
                class="filter-btn filter-btn-with-image"
                :class="{ active: filters.tireDry.includes(tireType.value) }"
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
                type="button"
                class="filter-btn filter-btn-with-image"
                :class="{ active: filters.tireWet.includes(tireType.value) }"
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

      <!-- Clear Filters Button -->
      <button
        v-if="hasActiveFilters"
        type="button"
        class="clear-filters-btn"
        @click="emit('clear-filters')"
      >
        <i class="fa-solid fa-times"></i>
        <span>{{ t('routePlanner.clearFilters') }}</span>
      </button>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

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

interface SegmentFilters {
  difficultyMin: number
  difficultyMax: number
  surface: string[]
  tireDry: string[]
  tireWet: string[]
}

interface Props {
  showFilters: boolean
  nameFilter: string
  filters: SegmentFilters
  hasActiveFilters: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  close: []
  'update:nameFilter': [value: string]
  'update:difficultyMin': [value: number]
  'update:difficultyMax': [value: number]
  'toggle-filter': [type: 'surface' | 'tireDry' | 'tireWet', value: string]
  'clear-filters': []
}>()

const { t } = useI18n()

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

// Helper functions
function getTireImage(tireType: string): string {
  return tireImages[tireType as keyof typeof tireImages] || tireSlickUrl
}

function getSurfaceImage(surfaceType: string): string {
  return surfaceImages[surfaceType as keyof typeof surfaceImages] || brokenPavedRoadUrl
}
</script>

<style scoped>
/* Filters Sidebar */
.filters-sidebar {
  position: fixed;
  top: var(--navbar-height);
  left: 0;
  width: 300px;
  height: calc(100vh - var(--navbar-height));
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(10px);
  border-right: 1px solid rgba(229, 231, 235, 0.5);
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  transform: translateX(-100%);
  transition: transform 0.3s ease-in-out;
  overflow-y: auto;
  overflow: visible; /* Allow tooltips to be visible */
}

.filters-sidebar.open {
  transform: translateX(0);
}

.filters-sidebar-content {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.filters-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(229, 231, 235, 0.5);
}

.filters-title {
  margin: 0;
  color: #374151;
  font-size: 1.125rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filters-title i {
  color: var(--brand-primary);
}

.filters-close {
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

.filters-close:hover {
  background: #e5e7eb;
  color: #374151;
}

/* Filter Group Styles */
.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.filter-group-title {
  margin: 0;
  color: #374151;
  font-size: 0.875rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-group-title i {
  font-size: 0.75rem;
  color: var(--brand-primary);
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

/* Name Filter Input */
.name-filter-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.875rem;
  color: #374151;
  transition: all 0.2s ease;
}

.name-filter-input:focus {
  outline: none;
  border-color: var(--brand-primary);
  box-shadow: 0 0 0 3px rgba(var(--brand-primary-rgb), 0.1);
}

.name-filter-input::placeholder {
  color: #9ca3af;
}

/* Difficulty Range Slider */
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
  margin-left: -9px;
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
  margin-left: -9px;
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
  padding: 0.25rem;
  margin: 0 0.2rem;
  border-radius: 4px;
  transition: all 0.2s ease;
  width: 100%;
}

.tick-mark.active {
  background: var(--brand-primary);
  color: white;
  font-weight: 600;
}

/* Filter Options */
.filter-options {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.filter-btn-wrapper {
  position: relative;
  display: inline-block;
}

.filter-btn-wrapper:has(.surface-filter-image) {
  flex: 0 1 calc(33.333% - 0.34rem);
}

.filter-btn-wrapper:has(.tire-filter-image) {
  flex: 1;
  max-width: calc(33.333% - 0.34rem);
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

.filter-btn-with-image {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.3rem;
  min-width: 0;
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

/* Tire Condition Groups */
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
  color: #f59e0b;
}

.tire-condition-header .fa-cloud-rain {
  color: #3b82f6;
}

/* Custom Tooltip */
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

/* Clear Filters Button */
.clear-filters-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: rgba(var(--brand-primary-rgb), 0.1);
  border: 1px solid rgba(var(--brand-primary-rgb), 0.3);
  border-radius: 8px;
  color: var(--brand-primary);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.875rem;
  font-weight: 600;
}

.clear-filters-btn:hover {
  background: rgba(var(--brand-primary-rgb), 0.15);
  border-color: rgba(var(--brand-primary-rgb), 0.4);
}

.clear-filters-btn i {
  font-size: 0.875rem;
}

/* Responsive adjustments for sidebar */
@media (max-width: 768px) {
  .filters-sidebar {
    width: 280px;
  }

  .filters-sidebar-content {
    padding: 1rem;
  }
}

@media (max-width: 640px) {
  .filters-sidebar {
    width: 100%;
  }
}
</style>
