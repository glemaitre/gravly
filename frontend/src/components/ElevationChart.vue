<template>
  <div class="card chart-card">
    <div class="card-header">
      <h3>
        <i class="fa-solid fa-chart-line"></i>
        {{ t('segmentDetail.elevation') }}
      </h3>
    </div>
    <div class="card-content">
      <div class="chart-container">
        <canvas ref="elevationChartRef" class="elevation-chart"></canvas>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
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
import annotationPlugin from 'chartjs-plugin-annotation'
import type { GPXData } from '../types'

Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Title,
  Filler,
  Tooltip,
  annotationPlugin
)

const { t } = useI18n()

// Props
const props = defineProps<{
  gpxData: GPXData
  // eslint-disable-next-line no-unused-vars
  onChartHover?: (pointIndex: number) => void
}>()

// Emits
const emit = defineEmits<{
  chartHover: [pointIndex: number]
}>()

// Reactive data
const elevationChart = ref<Chart | null>(null)
const elevationChartRef = ref<HTMLCanvasElement | null>(null)

// Helper function to calculate distance between two points
function calculateDistance(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371000 // Earth's radius in meters
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLon = ((lon2 - lon1) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

// Helper function to get CSS variable value
function getCssVariableValue(variable: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(variable).trim()
}

// Initialize the elevation chart
async function initializeElevationChart() {
  if (!props.gpxData || !elevationChartRef.value) {
    return
  }

  // Check if chart is already initialized
  if (elevationChart.value) {
    elevationChart.value.destroy()
    elevationChart.value = null
  }

  // Check if chart canvas exists
  if (!elevationChartRef.value) {
    console.error('Chart canvas not found')
    return
  }

  // Ensure canvas has proper dimensions
  const canvas = elevationChartRef.value
  const container = canvas.parentElement
  if (container) {
    canvas.width = container.clientWidth
    canvas.height = container.clientHeight
  }

  const points = props.gpxData.points
  if (points.length === 0) {
    return
  }

  // Calculate cumulative distances in kilometers
  const cumulativeKm: number[] = [0]
  let cumulativeDistance = 0

  for (let i = 1; i < points.length; i++) {
    const distance = calculateDistance(
      points[i - 1].latitude,
      points[i - 1].longitude,
      points[i].latitude,
      points[i].longitude
    )
    cumulativeDistance += distance
    cumulativeKm.push(cumulativeDistance / 1000) // Convert to kilometers
  }

  // Apply smoothing to elevation data (same as RoutePlanner)
  const elevations = points.map((p) => p.elevation)
  const smoothedElevations: number[] = []

  if (elevations.length < 3) {
    // Not enough points for smoothing, use original data
    smoothedElevations.push(...elevations)
  } else {
    // Apply moving average smoothing with window size of 30
    const windowSize = 30
    for (let i = 0; i < elevations.length; i++) {
      const start = Math.max(0, i - Math.floor(windowSize / 2))
      const end = Math.min(elevations.length, i + Math.ceil(windowSize / 2))
      const window = elevations.slice(start, end)

      const avgElevation = window.reduce((sum, elev) => sum + elev, 0) / window.length
      smoothedElevations.push(avgElevation)
    }
  }

  // Prepare chart data with x,y coordinates using smoothed elevations
  const chartData = points.map((point, i) => ({
    x: cumulativeKm[i],
    y: smoothedElevations[i]
  }))

  // Get theme-aware colors
  const brandPrimary = getCssVariableValue('--brand-primary')
  const brandPrimaryRgb = getCssVariableValue('--brand-primary-rgb')
  const cardBg = getCssVariableValue('--card-bg')
  const bgTertiary = getCssVariableValue('--bg-tertiary')

  // Check if we're in dark theme to determine grid visibility and text colors
  const isDarkTheme = document.documentElement.getAttribute('data-theme') === 'dark'

  // Use appropriate colors for axis labels based on theme
  const axisTitleColor = isDarkTheme ? '#f8fafc' : '#111827' // text-primary equivalent
  const axisTickColor = isDarkTheme ? '#e2e8f0' : '#374151' // text-secondary equivalent

  elevationChart.value = new Chart(elevationChartRef.value, {
    type: 'line',
    data: {
      datasets: [
        {
          label: 'Elevation',
          data: chartData,
          borderColor: brandPrimary || '#ff6600',
          backgroundColor: `rgba(${brandPrimaryRgb || '255, 102, 0'}, 0.15)`,
          fill: true,
          tension: 0.1,
          pointRadius: 0,
          pointHoverRadius: 6,
          pointHoverBackgroundColor: brandPrimary,
          pointHoverBorderColor: cardBg,
          pointHoverBorderWidth: 2,
          parsing: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      interaction: {
        intersect: false,
        mode: 'index'
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: function (context) {
              const xValue = context[0].parsed.x
              return `${xValue.toFixed(2)} km`
            },
            label: function (context) {
              const yValue = context.parsed.y
              return `Elevation: ${Math.round(yValue)} m`
            }
          }
        }
      },
      scales: {
        x: {
          type: 'linear',
          display: true,
          title: {
            display: true,
            text: 'Distance (km)',
            color: axisTitleColor
          },
          ticks: {
            color: axisTickColor,
            callback: function (value: any) {
              return `${Number(value).toFixed(1)} km`
            }
          },
          grid: {
            color: isDarkTheme ? bgTertiary : 'transparent'
          },
          min: 0,
          max: cumulativeKm[cumulativeKm.length - 1]
        },
        y: {
          display: true,
          title: {
            display: true,
            text: 'Elevation (m)',
            color: axisTitleColor
          },
          ticks: {
            color: axisTickColor
          },
          grid: {
            color: isDarkTheme ? bgTertiary : 'transparent'
          },
          min: Math.min(...smoothedElevations)
        }
      },
      onHover: (event, activeElements) => {
        if (activeElements.length > 0) {
          const pointIndex = activeElements[0].index
          emit('chartHover', pointIndex)
          if (props.onChartHover) {
            props.onChartHover(pointIndex)
          }
        }
      }
    }
  })
}

// Watch for changes in gpxData and reinitialize chart
watch(
  () => props.gpxData,
  async () => {
    await nextTick()
    if (props.gpxData && elevationChartRef.value) {
      // Small delay to ensure DOM is ready
      setTimeout(async () => {
        await initializeElevationChart()
      }, 100)
    }
  },
  { deep: true }
)

// Watch for theme changes by monitoring the document's data-theme attribute
watch(
  () => document.documentElement.getAttribute('data-theme'),
  () => {
    if (props.gpxData && elevationChartRef.value) {
      // Small delay to ensure CSS variables are updated, then recreate the chart
      setTimeout(() => {
        initializeElevationChart()
      }, 50)
    }
  }
)

// Lifecycle
onMounted(async () => {
  await nextTick()
  if (props.gpxData && elevationChartRef.value) {
    // Small delay to ensure DOM is ready
    setTimeout(async () => {
      await initializeElevationChart()
    }, 100)
  }
})

onUnmounted(() => {
  if (elevationChart.value) {
    elevationChart.value.destroy()
    elevationChart.value = null
  }
})
</script>

<style scoped>
.card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  box-shadow: var(--card-shadow);
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-header {
  padding: 0.75rem 1.5rem;
  border-bottom: 1px solid var(--border-muted);
  background: var(--bg-secondary);
}

.card-header h3 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.card-header i {
  color: var(--brand-primary);
}

.card-content {
  background: var(--bg-tertiary);
  padding: 1.5rem;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chart-container {
  height: 100%;
  position: relative;
  flex: 1;
}

.elevation-chart {
  width: 100% !important;
  height: 100% !important;
}
</style>
