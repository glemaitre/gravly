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
      <!-- Elevation chart -->
      <div class="elevation-chart">
        <div class="chart-container">
          <!-- Elevation error/empty state message (centered) -->
          <div v-if="elevationError" class="elevation-empty-state">
            <i class="fa-solid fa-mountain"></i>
            <span>{{ elevationError }}</span>
          </div>

          <!-- Chart canvas (hidden when there's an error) -->
          <canvas
            v-show="!elevationError"
            ref="elevationChartRef"
            class="elevation-chart-canvas"
          ></canvas>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  Title,
  CategoryScale,
  Filler,
  Tooltip
} from 'chart.js'

// Register Chart.js components
Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  Title,
  CategoryScale,
  Filler,
  Tooltip
)

// Types
interface ElevationStats {
  totalGain: number
  totalLoss: number
  maxElevation: number
  minElevation: number
}

interface RoutePoint {
  lat: number
  lng: number
  elevation: number
  distance: number
}

// Props
const props = defineProps<{
  showElevation: boolean
  elevationStats: ElevationStats
  elevationError: string | null
  routeDistance: number
  routePoints: RoutePoint[]
  sidebarOpen: boolean
  elevationHeight: number
}>()

// Emits
const emit = defineEmits<{
  toggle: []
  'update:elevation-height': [height: number]
  'start-resize': [event: MouseEvent | TouchEvent]
  'chart-hover': [point: RoutePoint | null]
}>()

// i18n
const { t } = useI18n()

// Refs
const elevationChartRef = ref<HTMLCanvasElement | null>(null)
let elevationChart: Chart | null = null

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

// Helper function to get CSS variable value
function getCssVariableValue(variable: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(variable).trim()
}

// Chart management
function createElevationChart() {
  // Don't create chart if there's an error or no data
  if (props.elevationError || !props.routePoints || props.routePoints.length === 0) {
    return
  }

  if (!elevationChartRef.value) return

  const ctx = elevationChartRef.value.getContext('2d')
  if (!ctx) return

  // Destroy existing chart
  if (elevationChart) {
    elevationChart.destroy()
  }

  // Get theme-aware colors
  const brandPrimary = getCssVariableValue('--brand-primary')
  const brandPrimaryRgb = getCssVariableValue('--brand-primary-rgb')
  const cardBg = getCssVariableValue('--card-bg')
  const borderMuted = getCssVariableValue('--border-muted')

  // Check if we're in dark theme to determine grid visibility and text colors
  const isDarkTheme = document.documentElement.getAttribute('data-theme') === 'dark'

  // Use appropriate colors for axis labels based on theme
  const axisTitleColor = isDarkTheme ? '#f8fafc' : '#111827' // text-primary equivalent
  const axisTickColor = isDarkTheme ? '#e2e8f0' : '#374151' // text-secondary equivalent

  // Create new chart
  elevationChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Elevation',
          data: [],
          borderColor: brandPrimary, // Dynamic brand color
          backgroundColor: `rgba(${brandPrimaryRgb}, 0.15)`, // Dynamic fill with original orange
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 6, // Larger hover point
          pointHoverBackgroundColor: brandPrimary,
          pointHoverBorderColor: cardBg,
          pointHoverBorderWidth: 2,
          borderWidth: 2.5
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          enabled: true,
          mode: 'index',
          intersect: false,
          callbacks: {
            label: (context) => {
              const elevation = context.parsed.y
              return `Elevation: ${elevation.toFixed(1)}m`
            },
            title: (context) => {
              const distance = context[0].parsed.x
              return `Distance: ${distance.toFixed(1)}km`
            }
          }
        }
      },
      scales: {
        x: {
          type: 'linear',
          title: {
            display: true,
            text: 'Distance (km)',
            color: axisTitleColor
          },
          ticks: {
            color: axisTickColor,
            callback: (value) => {
              if (typeof value === 'number') {
                return value.toFixed(1)
              }
              return value
            }
          },
          grid: {
            color: isDarkTheme ? borderMuted : 'transparent'
          },
          min: 0,
          max: props.routeDistance // Set max to total route distance in km
        },
        y: {
          title: {
            display: true,
            text: 'Elevation (m)',
            color: axisTitleColor
          },
          ticks: {
            color: axisTickColor
          },
          grid: {
            color: isDarkTheme ? borderMuted : 'transparent'
          }
        }
      },
      interaction: {
        mode: 'nearest',
        axis: 'x',
        intersect: false
      },
      onHover: (event) => {
        handleChartHover(event)
      }
    }
  })

  // Add mouse leave event to clear cursor
  if (elevationChartRef.value) {
    elevationChartRef.value.addEventListener('mouseleave', handleChartMouseLeave)
  }

  updateChartData()
}

function updateChartData() {
  // If there's an error or no points, destroy the chart
  if (props.elevationError || !props.routePoints || props.routePoints.length === 0) {
    if (elevationChart) {
      elevationChart.destroy()
      elevationChart = null
    }
    return
  }

  if (!elevationChart) return

  // Check if canvas is still attached to DOM before updating
  if (!elevationChartRef.value || !elevationChartRef.value.isConnected) {
    return
  }

  const distances = props.routePoints.map((p) => p.distance / 1000) // Convert to km
  const elevations = props.routePoints.map((p) => p.elevation)

  elevationChart.data.labels = distances as any
  elevationChart.data.datasets[0].data = elevations as any

  // Update x-axis max to match route distance
  if (elevationChart.options.scales?.x) {
    elevationChart.options.scales.x.max = props.routeDistance
  }

  elevationChart.update('none') // Update without animation for better performance
}

// Watch for route points changes
watch(
  () => props.routePoints,
  () => {
    if (props.showElevation && elevationChart) {
      updateChartData()
    } else if (
      props.showElevation &&
      !elevationChart &&
      elevationChartRef.value &&
      !props.elevationError
    ) {
      createElevationChart()
    }
  },
  { deep: true }
)

// Watch for elevation error changes
watch(
  () => props.elevationError,
  () => {
    updateChartData() // This will destroy the chart if there's an error
  }
)

// Watch for show elevation changes
watch(
  () => props.showElevation,
  async (newVal) => {
    if (newVal && !props.elevationError) {
      await nextTick()
      createElevationChart()
    }
  }
)

// Watch for height changes to resize chart
watch(
  () => props.elevationHeight,
  () => {
    if (elevationChart && props.showElevation) {
      setTimeout(() => {
        elevationChart?.resize()
      }, 100)
    }
  }
)

// Watch for theme changes by monitoring the document's data-theme attribute
watch(
  () => document.documentElement.getAttribute('data-theme'),
  () => {
    if (props.showElevation) {
      // Small delay to ensure CSS variables are updated, then recreate the chart
      setTimeout(() => {
        createElevationChart()
      }, 50)
    }
  }
)

onMounted(() => {
  if (props.showElevation && !props.elevationError) {
    nextTick(() => {
      createElevationChart()
    })
  }
})

function handleChartHover(event: any) {
  if (!elevationChart || !props.routePoints || props.routePoints.length === 0) return

  // Get the canvas and chart area
  const canvas = elevationChartRef.value
  if (!canvas) return

  const chartArea = elevationChart.chartArea
  if (!chartArea) return

  // Get mouse position relative to canvas
  const rect = canvas.getBoundingClientRect()
  const mouseX = event.native?.offsetX ?? event.x - rect.left

  // Check if mouse is within chart area
  if (mouseX < chartArea.left || mouseX > chartArea.right) {
    emit('chart-hover', null)
    return
  }

  // Calculate the distance based on mouse x position
  const xScale = elevationChart.scales.x
  const distanceKm = xScale.getValueForPixel(mouseX)

  if (distanceKm === undefined || distanceKm === null) {
    emit('chart-hover', null)
    return
  }

  const distanceM = distanceKm * 1000

  // Find the closest point in the route
  const closestPoint = findClosestPointByDistance(distanceM)

  if (closestPoint) {
    emit('chart-hover', closestPoint)
  }
}

function handleChartMouseLeave() {
  emit('chart-hover', null)
}

function findClosestPointByDistance(targetDistance: number): RoutePoint | null {
  if (!props.routePoints || props.routePoints.length === 0) return null

  let closestPoint = props.routePoints[0]
  let minDiff = Math.abs(props.routePoints[0].distance - targetDistance)

  for (const point of props.routePoints) {
    const diff = Math.abs(point.distance - targetDistance)
    if (diff < minDiff) {
      minDiff = diff
      closestPoint = point
    }
  }

  return closestPoint
}

onUnmounted(() => {
  if (elevationChartRef.value) {
    elevationChartRef.value.removeEventListener('mouseleave', handleChartMouseLeave)
  }

  if (elevationChart) {
    elevationChart.destroy()
    elevationChart = null
  }
})

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
  background: rgba(var(--bg-primary-rgb), 0.85);
  backdrop-filter: blur(8px);
  border-top: 1px solid var(--border-primary);
  box-shadow: var(--shadow-lg);
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
  background: rgba(var(--bg-primary-rgb), 0.95); /* More opaque when expanded */
}

.elevation-section.sidebar-open {
  left: 300px; /* Start from the right edge of the sidebar */
}

.elevation-toggle {
  height: 30px;
  background: var(--bg-primary);
  backdrop-filter: blur(4px);
  border-bottom: 1px solid var(--border-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  padding: 0 1rem;
  transition: background-color 0.2s ease;
}

.elevation-toggle:hover {
  background: var(--bg-hover);
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
  color: var(--text-primary);
  font-weight: 500;
}

.toggle-stat i {
  font-size: 0.7rem;
  color: var(--text-tertiary);
  opacity: 0.9;
}

.elevation-toggle-content i:first-child {
  color: var(--brand-primary);
  font-size: 1.25rem;
}

.elevation-toggle-text {
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
  text-align: left;
  margin-left: 0.5rem;
}

.elevation-toggle-content i:last-child {
  color: var(--text-tertiary);
  font-size: 0.875rem;
  transition: transform 0.2s ease;
}

.elevation-expanded .elevation-toggle-content i:last-child {
  transform: rotate(180deg);
}

.elevation-content {
  background: var(--card-bg);
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
  background: var(--card-bg);
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-primary);
  font-size: 10px;
  box-shadow: var(--shadow-sm);
  position: relative;
}

.elevation-resize-handle:hover .elevation-resize-handle-bar {
  background: var(--bg-hover);
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
  border-bottom: 4px solid var(--card-bg);
}

.elevation-resize-handle-bar::after {
  bottom: -4px;
  border-top: 4px solid var(--card-bg);
}

.elevation-resize-handle:hover .elevation-resize-handle-bar::before,
.elevation-resize-handle:hover .elevation-resize-handle-bar::after {
  border-bottom-color: var(--bg-hover);
  border-top-color: var(--bg-hover);
}

.elevation-empty-state {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  color: var(--text-muted);
  font-size: 0.875rem;
  font-weight: 500;
  text-align: center;
  padding: 1.5rem;
}

.elevation-empty-state i {
  font-size: 2.5rem;
  color: var(--text-tertiary);
  opacity: 0.6;
}

.elevation-chart {
  padding: 0.3rem;
  flex: 1; /* Take remaining space in elevation-content */
  display: flex;
  flex-direction: column;
  min-height: 0; /* Allow flex item to shrink */
}

.chart-container {
  background: var(--card-bg);
  border-radius: 8px;
  border: 1px solid var(--card-border);
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
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-muted);
  font-size: 0.875rem;
  color: var(--text-tertiary);
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
  border: 2px solid var(--card-bg);
  box-shadow: var(--shadow-md);
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

/* Mobile styles */
@media (max-width: 768px) {
  .elevation-toggle-content i:first-child {
    font-size: 0.9rem;
  }

  .toggle-stat i {
    font-size: 0.5rem;
  }

  .elevation-toggle-text {
    margin-left: 0;
    font-size: 0.9rem;
  }
}
</style>
