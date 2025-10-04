<template>
  <!-- Bottom elevation section -->
  <div
    class="elevation-section"
    :class="{
      'elevation-expanded': showElevation,
      'sidebar-open': sidebarOpen
    }"
  >
    <!-- Resize Handle - Always visible when elevation is expanded -->
    <div
      v-if="showElevation"
      class="elevation-resize-handle"
      @mousedown="startResize"
      @touchstart="startResize"
      :title="t('routePlanner.resizeHandle')"
    >
      <div class="elevation-resize-handle-bar"></div>
    </div>

    <!-- Toggle button with integrated stats -->
    <div class="elevation-toggle" @click="emit('toggle')">
      <div class="elevation-toggle-content">
        <div class="toggle-left">
          <i class="fa-solid fa-mountain"></i>
          <span class="elevation-toggle-text">{{ t('routePlanner.profile') }}</span>
          <div class="toggle-stats">
            <div class="toggle-stat" :title="t('routePlanner.totalDistance')">
              <i class="fa-solid fa-route"></i>
              <span>{{ routeDistance.toFixed(1) }} {{ t('routePlanner.km') }}</span>
            </div>
            <div class="toggle-stat" :title="t('routePlanner.elevationGain')">
              <i class="fa-solid fa-arrow-trend-up"></i>
              <span>{{ elevationStats.totalGain }}{{ t('routePlanner.m') }}</span>
            </div>
            <div class="toggle-stat" :title="t('routePlanner.elevationLoss')">
              <i class="fa-solid fa-arrow-trend-down"></i>
              <span>{{ elevationStats.totalLoss }}{{ t('routePlanner.m') }}</span>
            </div>
          </div>
        </div>
        <i class="fa-solid fa-chevron-up"></i>
      </div>
    </div>

    <!-- Elevation content -->
    <div
      class="elevation-content"
      v-if="showElevation"
      :style="{ height: elevationHeight + 'px' }"
    >
      <!-- Elevation error message -->
      <div v-if="elevationError" class="elevation-error">
        <i class="fa-solid fa-triangle-exclamation"></i>
        <span>{{ elevationError }}</span>
      </div>

      <!-- Elevation chart -->
      <div class="elevation-chart">
        <div class="chart-container">
          <canvas ref="elevationChartRef" class="elevation-chart-canvas"></canvas>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

// Types
interface ElevationStats {
  totalGain: number
  totalLoss: number
  maxElevation: number
  minElevation: number
}

// Props
const props = defineProps<{
  showElevation: boolean
  elevationStats: ElevationStats
  elevationError: string | null
  routeDistance: number
  sidebarOpen: boolean
  elevationHeight: number
}>()

// Emits
const emit = defineEmits<{
  toggle: []
  'update:elevation-height': [height: number]
  'start-resize': [event: MouseEvent | TouchEvent]
}>()

// i18n
const { t } = useI18n()

// Refs
const elevationChartRef = ref<HTMLCanvasElement | null>(null)

// Resize state
const minElevationHeight = 150
const maxElevationHeight = 600
let startY = 0
let startHeight = 0
let isResizing = false

function startResize(event: MouseEvent | TouchEvent) {
  isResizing = true
  startHeight = props.elevationHeight

  if (event instanceof MouseEvent) {
    startY = event.clientY
  } else {
    startY = event.touches[0].clientY
  }

  // Add document listeners
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  document.addEventListener('touchmove', handleResize)
  document.addEventListener('touchend', stopResize)

  // Prevent text selection during resize
  event.preventDefault()

  // Emit start resize event to parent
  emit('start-resize', event)
}

function handleResize(event: MouseEvent | TouchEvent) {
  if (!isResizing) return

  let currentY = 0
  if (event instanceof MouseEvent) {
    currentY = event.clientY
  } else {
    currentY = event.touches[0].clientY
  }

  // Calculate new height (inverted because we're resizing from bottom)
  const deltaY = startY - currentY
  const newHeight = Math.max(
    minElevationHeight,
    Math.min(maxElevationHeight, startHeight + deltaY)
  )

  emit('update:elevation-height', newHeight)
}

function stopResize() {
  if (!isResizing) return

  isResizing = false

  // Remove document listeners
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
  document.removeEventListener('touchmove', handleResize)
  document.removeEventListener('touchend', stopResize)
}

// Expose chart ref for parent component
defineExpose({
  elevationChartRef
})
</script>

<style scoped>
/* Elevation section styles */
.elevation-section {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border-top: 1px solid rgba(229, 231, 235, 0.5);
  box-shadow: 0 -4px 6px -1px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  transition: all 0.3s ease-in-out;
  transform: translateY(
    calc(100% - 30px)
  ); /* Show only toggle by default (30px height) */
  /* Ensure section doesn't exceed viewport height */
  max-height: calc(
    100vh - var(--navbar-height) - 100px
  ); /* Reserve space for map controls */
  overflow: hidden; /* Prevent content overflow */
  display: flex;
  flex-direction: column;
}

.elevation-expanded {
  transform: translateY(0); /* Show full content when expanded */
  background: rgba(255, 255, 255, 0.95); /* More opaque when expanded */
}

.elevation-section.sidebar-open {
  left: 300px; /* Start from the right edge of the sidebar */
}

.elevation-toggle {
  height: 30px;
  background: rgba(248, 250, 252, 0.8);
  backdrop-filter: blur(4px);
  border-bottom: 1px solid rgba(229, 231, 235, 0.5);
  cursor: pointer;
  display: flex;
  align-items: center;
  padding: 0 1rem;
  transition: background-color 0.2s ease;
}

.elevation-toggle:hover {
  background: rgba(241, 245, 249, 0.9);
}

.elevation-toggle-content {
  display: flex;
  align-items: center;
  gap: 1rem;
  width: 100%;
  justify-content: space-between;
}

.toggle-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
}

.toggle-stats {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-left: 0.5rem;
  flex-wrap: wrap;
}

.toggle-stat {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: #374151;
  font-weight: 500;
}

.toggle-stat i {
  font-size: 0.7rem;
  color: #6b7280;
  opacity: 0.9;
}

.elevation-toggle-content i:first-child {
  color: var(--brand-primary);
  font-size: 1.25rem;
}

.elevation-toggle-text {
  font-weight: 600;
  color: #374151;
  flex: 1;
  text-align: left;
  margin-left: 0.5rem;
}

.elevation-toggle-content i:last-child {
  color: #6b7280;
  font-size: 0.875rem;
  transition: transform 0.2s ease;
}

.elevation-expanded .elevation-toggle-content i:last-child {
  transform: rotate(180deg);
}

.elevation-content {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
  overflow: hidden; /* Prevent content overflow */
  display: flex;
  flex-direction: column;
  /* Height is now controlled by the :style binding */
}

/* Elevation Resize Handle */
.elevation-resize-handle {
  height: 8px;
  background: var(--brand-primary);
  cursor: ns-resize;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(var(--brand-primary-rgb), 0.2);
  border-radius: 4px;
  margin: 2px 8px; /* Reduced margin for smaller handle */
}

.elevation-resize-handle:hover {
  background: var(--brand-primary-hover);
  box-shadow: 0 2px 6px rgba(var(--brand-primary-rgb), 0.3);
  transform: scaleY(1.2);
}

.elevation-resize-handle:active {
  background: var(--brand-primary-hover);
  box-shadow: 0 1px 2px rgba(var(--brand-primary-rgb), 0.4);
  transform: scaleY(1.1);
}

.elevation-resize-handle-bar {
  width: 40px;
  height: 4px;
  background: white;
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 10px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  position: relative;
}

.elevation-resize-handle:hover .elevation-resize-handle-bar {
  background: #fff5f0;
  transform: scale(1.05);
}

/* Vertical arrows to indicate resize direction */
.elevation-resize-handle-bar::before,
.elevation-resize-handle-bar::after {
  content: '';
  position: absolute;
  width: 0;
  height: 0;
  border-left: 3px solid transparent;
  border-right: 3px solid transparent;
}

.elevation-resize-handle-bar::before {
  top: -4px;
  border-bottom: 4px solid white;
}

.elevation-resize-handle-bar::after {
  bottom: -4px;
  border-top: 4px solid white;
}

.elevation-resize-handle:hover .elevation-resize-handle-bar::before,
.elevation-resize-handle:hover .elevation-resize-handle-bar::after {
  border-bottom-color: #fff5f0;
  border-top-color: #fff5f0;
}

.elevation-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 0.75rem 1rem;
  margin: 0.5rem;
  border-radius: 0.375rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.elevation-error i {
  font-size: 1rem;
  flex-shrink: 0;
}

.elevation-chart {
  padding: 0.3rem;
  flex: 1; /* Take remaining space in elevation-content */
  display: flex;
  flex-direction: column;
  min-height: 0; /* Allow flex item to shrink */
}

.chart-container {
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  flex: 1; /* Take remaining space in elevation-chart */
  position: relative;
  min-height: 120px; /* Minimum height for chart visibility */
}

.elevation-chart-canvas {
  width: 100%;
  height: 100%; /* Fill the container */
  display: block;
}

.chart-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #f8fafc;
  border-top: 1px solid #e5e7eb;
  font-size: 0.875rem;
  color: #6b7280;
}

.chart-distance {
  font-weight: 600;
  color: var(--brand-primary);
}

.chart-elevation-range {
  font-weight: 500;
}

/* Chart marker styling */
:global(.custom-chart-marker) {
  background: transparent;
  border: none;
}

:global(.chart-marker) {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--brand-primary);
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.7;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
