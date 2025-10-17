<template>
  <div class="card card-elevation">
    <div class="chart-wrapper">
      <div class="chart-container">
        <canvas ref="chartCanvas" class="chart"></canvas>
        <div
          class="vertical-slider start-slider"
          :style="{ left: startSliderPosition + '%' }"
          @mousedown="startDrag('start', $event)"
          @touchstart="startDrag('start', $event)"
        >
          <div class="slider-handle"></div>
          <div class="slider-line"></div>
          <div class="slider-index">{{ startIndex }}</div>
          <div class="slider-controls">
            <button
              class="slider-btn slider-btn-minus"
              @click="moveSlider('start', -1)"
              :disabled="startIndex <= 0"
              :title="t('tooltip.moveStartBack')"
            >
              -
            </button>
            <button
              class="slider-btn slider-btn-plus"
              @click="moveSlider('start', 1)"
              :disabled="startIndex >= endIndex - 1"
              :title="t('tooltip.moveStartForward')"
            >
              +
            </button>
          </div>
        </div>
        <div
          class="vertical-slider end-slider"
          :style="{ left: endSliderPosition + '%' }"
          @mousedown="startDrag('end', $event)"
          @touchstart="startDrag('end', $event)"
        >
          <div class="slider-handle"></div>
          <div class="slider-line"></div>
          <div class="slider-index">{{ endIndex }}</div>
          <div class="slider-controls" :style="{ top: `-${endSliderOffset}px` }">
            <button
              class="slider-btn slider-btn-minus"
              @click="moveSlider('end', -1)"
              :disabled="endIndex <= startIndex + 1"
              :title="t('tooltip.moveEndBack')"
            >
              -
            </button>
            <button
              class="slider-btn slider-btn-plus"
              @click="moveSlider('end', 1)"
              :disabled="endIndex >= points.length - 1"
              :title="t('tooltip.moveEndForward')"
            >
              +
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="axis-toggle below">
      <button
        type="button"
        class="seg left"
        :class="{ active: xMode === 'distance' }"
        @click="xMode = 'distance'"
      >
        {{ t('chart.distance') }}
      </button>
      <button
        type="button"
        class="seg right"
        :class="{ active: xMode === 'time' }"
        @click="xMode = 'time'"
      >
        {{ t('chart.time') }}
      </button>
    </div>

    <div class="controls" ref="controlsCard">
      <div class="slider-group">
        <div class="slider-header">
          <span class="badge start">{{ t('chart.start') }}</span>
        </div>
        <div class="metrics-grid">
          <div class="metric" :title="t('tooltip.elapsedTime')">
            <span class="icon"><i class="fa-solid fa-clock"></i></span>
            <span class="value">{{ formatElapsed(startIndex) }}</span>
          </div>
          <div class="metric" :title="t('tooltip.distance')">
            <span class="icon"><i class="fa-solid fa-ruler"></i></span>
            <span class="value">{{ formatKm(distanceAt(startIndex)) }}</span>
          </div>
          <div class="metric" :title="t('tooltip.elevation')">
            <span class="icon"><i class="fa-solid fa-mountain"></i></span>
            <span class="value">{{
              formatElevation(pointAt(startIndex)?.elevation)
            }}</span>
          </div>
          <div class="gps-col">
            <span class="label">{{ t('gps.latitude') }}</span
            ><span class="value">{{
              pointAt(startIndex)?.latitude?.toFixed(5) ?? '-'
            }}</span>
          </div>
          <div class="gps-col">
            <span class="label">{{ t('gps.longitude') }}</span
            ><span class="value">{{
              pointAt(startIndex)?.longitude?.toFixed(5) ?? '-'
            }}</span>
          </div>
        </div>
      </div>
      <div class="slider-group">
        <div class="slider-header">
          <span class="badge end">{{ t('chart.end') }}</span>
        </div>
        <div class="metrics-grid">
          <div class="metric" :title="t('tooltip.elapsedTime')">
            <span class="icon"><i class="fa-solid fa-clock"></i></span>
            <span class="value">{{ formatElapsed(endIndex) }}</span>
          </div>
          <div class="metric" :title="t('tooltip.distance')">
            <span class="icon"><i class="fa-solid fa-ruler"></i></span>
            <span class="value">{{ formatKm(distanceAt(endIndex)) }}</span>
          </div>
          <div class="metric" :title="t('tooltip.elevation')">
            <span class="icon"><i class="fa-solid fa-mountain"></i></span>
            <span class="value">{{
              formatElevation(pointAt(endIndex)?.elevation)
            }}</span>
          </div>
          <div class="gps-col">
            <span class="label">{{ t('gps.latitude') }}</span
            ><span class="value">{{
              pointAt(endIndex)?.latitude?.toFixed(5) ?? '-'
            }}</span>
          </div>
          <div class="gps-col">
            <span class="label">{{ t('gps.longitude') }}</span
            ><span class="value">{{
              pointAt(endIndex)?.longitude?.toFixed(5) ?? '-'
            }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted, nextTick, watch, computed } from 'vue'
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

// Types
type TrackPoint = {
  latitude: number
  longitude: number
  elevation: number
  time?: string
}

// Props
const props = defineProps<{
  points: TrackPoint[]
  cumulativeKm: number[]
  cumulativeSec: number[]
  smoothedElevations: number[]
  startIndex: number
  endIndex: number
  xMode: 'distance' | 'time'
}>()

// Emits
const emit = defineEmits<{
  'update:startIndex': [value: number]
  'update:endIndex': [value: number]
  'update:xMode': [value: 'distance' | 'time']
  chartHover: [pointIndex: number]
}>()

// Reactive data
const chartCanvas = ref<HTMLCanvasElement | null>(null)
const controlsCard = ref<HTMLDivElement | null>(null)
let chart: Chart | null = null

// Slider state
const isDragging = ref(false)
const dragType = ref<'start' | 'end' | null>(null)
const startSliderPosition = ref(0)
const endSliderPosition = ref(100)
const endSliderOffset = ref(0)

// Constants
const overlapThreshold = 20
const constantOffset = 25

// Computed properties for v-model
const startIndex = computed({
  get: () => props.startIndex,
  set: (value) => emit('update:startIndex', value)
})

const endIndex = computed({
  get: () => props.endIndex,
  set: (value) => emit('update:endIndex', value)
})

const xMode = computed({
  get: () => props.xMode,
  set: (value) => emit('update:xMode', value)
})

// Helper functions
function getX(i: number): number {
  return xMode.value === 'distance'
    ? (props.cumulativeKm[i] ?? 0)
    : (props.cumulativeSec[i] ?? 0)
}

function distanceAt(i: number): number {
  return props.cumulativeKm[i] ?? 0
}

function pointAt(i: number): TrackPoint | undefined {
  return props.points[i]
}

function formatKm(km?: number): string {
  return km == null ? '-' : `${km.toFixed(2)} ${t('units.km')}`
}

function formatElevation(ele?: number): string {
  return ele == null ? '-' : `${Math.round(ele)} ${t('units.m')}`
}

function formatElapsed(i: number): string {
  const t0 = props.points[0]?.time
    ? new Date(props.points[0].time as string).getTime()
    : undefined
  const ti = props.points[i]?.time
    ? new Date(props.points[i].time as string).getTime()
    : undefined
  if (!t0 || !ti) return '-'
  const ms = Math.max(0, ti - t0)
  const sec = Math.floor(ms / 1000)
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = sec % 60
  const hh = h > 0 ? `${h}:` : ''
  const mm = h > 0 ? String(m).padStart(2, '0') : String(m)
  const ss = String(s).padStart(2, '0')
  return `${hh}${mm}:${ss}`
}

function buildFullXYData(): { x: number; y: number }[] {
  return props.points.map((p, i) => ({
    x: getX(i),
    y: props.smoothedElevations[i] ?? p.elevation
  }))
}

function buildSelectedAreaData(): { x: number; y: number }[] {
  const selectedData = []

  for (let i = startIndex.value; i <= endIndex.value; i++) {
    selectedData.push({
      x: getX(i),
      y: props.smoothedElevations[i] ?? props.points[i]?.elevation ?? 0
    })
  }

  return selectedData
}

function formatXTick(v: number): string {
  if (xMode.value === 'distance') return `${v.toFixed(1)} ${t('units.km')}`
  const sec = Math.max(0, Math.round(v))
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = sec % 60
  const hh = h > 0 ? `${h}:` : ''
  const mm = h > 0 ? String(m).padStart(2, '0') : String(m)
  const ss = String(s).padStart(2, '0')
  return `${hh}${mm}:${ss}`
}

function checkSliderOverlap() {
  if (!chart || !chartCanvas.value) return

  const containerRect = chartCanvas.value.parentElement!.getBoundingClientRect()
  const sliderWidth = 20
  const controlsExtension = 18
  const startPixelCenter =
    (startSliderPosition.value / 100) * containerRect.width + sliderWidth / 2
  const endPixelCenter =
    (endSliderPosition.value / 100) * containerRect.width + sliderWidth / 2

  const startControlRight = startPixelCenter + controlsExtension
  const endControlLeft = endPixelCenter - controlsExtension
  const distance = endControlLeft - startControlRight

  if (distance < overlapThreshold) {
    endSliderOffset.value = constantOffset
  } else {
    endSliderOffset.value = 0
  }
}

function moveSlider(type: 'start' | 'end', direction: -1 | 1) {
  if (type === 'start') {
    const newIndex = startIndex.value + direction
    if (newIndex >= 0 && newIndex < endIndex.value) {
      startIndex.value = newIndex
    }
  } else {
    const newIndex = endIndex.value + direction
    if (newIndex > startIndex.value && newIndex < props.points.length) {
      endIndex.value = newIndex
    }
  }
}

function startDrag(type: 'start' | 'end', event: MouseEvent | TouchEvent) {
  event.preventDefault()
  isDragging.value = true
  dragType.value = type

  const handleMouseMove = (e: MouseEvent | TouchEvent) => {
    if (!isDragging.value || !chartCanvas.value || !chart) return

    const rect = chartCanvas.value.getBoundingClientRect()
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX
    const x = clientX - rect.left

    const dataX = chart.scales.x.getValueForPixel(x)
    if (dataX === undefined) return
    let closestIndex = 0
    let minDistance = Infinity

    for (let i = 0; i < props.points.length; i++) {
      const pointX = getX(i)
      const distance = Math.abs(pointX - dataX)
      if (distance < minDistance) {
        minDistance = distance
        closestIndex = i
      }
    }

    if (type === 'start') {
      if (closestIndex < endIndex.value) {
        startIndex.value = closestIndex
      }
    } else {
      if (closestIndex > startIndex.value) {
        endIndex.value = closestIndex
      }
    }
  }

  const handleMouseUp = () => {
    isDragging.value = false
    dragType.value = null
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
    document.removeEventListener('touchmove', handleMouseMove)
    document.removeEventListener('touchend', handleMouseUp)
  }

  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
  document.addEventListener('touchmove', handleMouseMove)
  document.addEventListener('touchend', handleMouseUp)
}

function initializeChart() {
  if (!chartCanvas.value || props.points.length === 0) return

  // Destroy existing chart
  if (chart) {
    chart.destroy()
    chart = null
  }

  const ctx = chartCanvas.value.getContext('2d')
  if (!ctx) return

  const fullData = buildFullXYData()
  const labels = fullData.map((d) => d.x.toString())

  // Get CSS variable values
  const rootStyles = getComputedStyle(document.documentElement)
  const brandPrimary = rootStyles.getPropertyValue('--brand-primary').trim()
  const brandPrimaryRgb = rootStyles.getPropertyValue('--brand-primary-rgb').trim()
  const textColor = rootStyles.getPropertyValue('--text-primary').trim()
  const gridColor = rootStyles.getPropertyValue('--border-muted').trim()
  const backgroundColor = rootStyles.getPropertyValue('--card-bg').trim()

  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: t('chart.elevation'),
          data: fullData.map((d) => ({ x: d.x, y: d.y })),
          borderColor: brandPrimary || '#ff6600',
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 5,
          backgroundColor: 'transparent',
          fill: false,
          tension: 0.1,
          parsing: false
        },
        {
          label: 'Selected Area',
          data: buildSelectedAreaData(),
          borderColor: 'transparent',
          backgroundColor: `rgba(${brandPrimaryRgb || '255, 102, 0'}, 0.15)`,
          fill: 'origin',
          pointRadius: 0,
          pointHoverRadius: 0,
          parsing: false,
          tension: 0
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
      layout: {
        padding: {
          left: 0,
          right: 0,
          top: 0,
          bottom: 0
        }
      },
      scales: {
        x: {
          type: 'linear',
          display: true,
          title: { display: false },
          min: getX(0),
          max: getX(props.points.length - 1),
          ticks: {
            callback: (v: any) => formatXTick(Number(v)),
            color: textColor || '#374151'
          },
          grid: {
            color: gridColor || '#e5e7eb'
          }
        },
        y: {
          display: true,
          title: {
            display: true,
            text: t('chart.elevation'),
            color: textColor || '#374151'
          },
          min: Math.min(...props.smoothedElevations),
          ticks: {
            color: textColor || '#374151'
          },
          grid: {
            color: gridColor || '#e5e7eb'
          }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: backgroundColor || '#ffffff',
          titleColor: textColor || '#374151',
          bodyColor: textColor || '#374151',
          borderColor: gridColor || '#e5e7eb',
          borderWidth: 1,
          filter: function (tooltipItem) {
            return tooltipItem.datasetIndex === 0
          },
          callbacks: {
            title: function (context) {
              const xValue = context[0].parsed.x
              return xMode.value === 'distance'
                ? `${xValue.toFixed(2)} ${t('units.km')}`
                : formatXTick(xValue)
            },
            label: function (context) {
              const yValue = context.parsed.y
              return `${t('chart.elevation')}: ${Math.round(yValue)} ${t('units.m')}`
            }
          }
        }
      },
      onHover: (event, activeElements) => {
        if (activeElements.length > 0) {
          const pointIndex = activeElements[0].index
          // Emit hover event for parent component to handle
          emit('chartHover', pointIndex)
        }
      }
    }
  })

  updateSliderPositions()
}

function updateSliderPositions() {
  if (!chart || !chartCanvas.value || props.points.length === 0) return

  nextTick(() => {
    if (chart && chartCanvas.value) {
      const startX = getX(startIndex.value)
      const endX = getX(endIndex.value)
      const canvasRect = chart.canvas.getBoundingClientRect()
      const containerRect = chartCanvas.value.parentElement!.getBoundingClientRect()
      const startPixel = chart.scales.x.getPixelForValue(startX)
      const endPixel = chart.scales.x.getPixelForValue(endX)
      const canvasOffsetLeft = canvasRect.left - containerRect.left
      const startPixelInContainer = startPixel + canvasOffsetLeft
      const endPixelInContainer = endPixel + canvasOffsetLeft
      const sliderWidth = 20
      const startPixelCentered = startPixelInContainer - sliderWidth / 2
      const endPixelCentered = endPixelInContainer - sliderWidth / 2

      startSliderPosition.value = (startPixelCentered / containerRect.width) * 100
      endSliderPosition.value = (endPixelCentered / containerRect.width) * 100
      checkSliderOverlap()
    }
  })
}

function updateChart() {
  if (!chart || props.points.length === 0) return

  const fullData = buildFullXYData()
  const labels = fullData.map((d) => d.x.toString())

  chart.data.labels = labels
  chart.data.datasets[0].data = fullData.map((d) => ({ x: d.x, y: d.y }))
  chart.data.datasets[1].data = buildSelectedAreaData()

  // Update scale min/max values
  if (chart.options.scales?.x) {
    chart.options.scales.x.min = getX(0)
    chart.options.scales.x.max = getX(props.points.length - 1)
  }
  if (chart.options.scales?.y) {
    chart.options.scales.y.min = Math.min(...props.smoothedElevations)
  }

  chart.update('none')
  updateSliderPositions()
}

// Watchers
watch(
  [startIndex, endIndex],
  () => {
    updateChart()
  },
  { flush: 'post' }
)

watch(
  xMode,
  () => {
    updateChart()
  },
  { flush: 'post' }
)

watch(
  () => props.points,
  () => {
    if (props.points.length > 0) {
      nextTick(() => {
        initializeChart()
      })
    }
  },
  { deep: true, flush: 'post' }
)

// Lifecycle
onMounted(() => {
  if (props.points.length > 0) {
    nextTick(() => {
      initializeChart()
    })
  }
})

onUnmounted(() => {
  if (chart) {
    chart.destroy()
    chart = null
  }
})
</script>

<style scoped>
.card-elevation {
  padding: 0.75rem;
  overflow: visible;
  margin-top: 1rem;
  margin-bottom: 1rem;
  background: var(--card-bg);
  border: 1px solid var(--border-muted);
  border-radius: 10px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}

.axis-toggle {
  display: inline-flex;
  gap: 0;
  margin: 0.25rem auto 0.25rem;
  border: 1px solid var(--border-muted);
  border-radius: 999px;
  overflow: hidden;
  background: var(--bg-secondary);
  position: relative;
  left: 50%;
  transform: translateX(-50%);
  max-width: 100%;
}

.axis-toggle.below {
  margin-top: 0.5rem;
}

.axis-toggle .seg {
  font-size: 12px;
  padding: 4px 10px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--text-secondary);
}

.axis-toggle .seg.left {
  border-right: 1px solid var(--border-muted);
}

.axis-toggle .seg.active {
  background: var(--bg-primary);
  color: var(--text-primary);
}

.controls {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  width: 100%;
  box-sizing: border-box;
}

/* Responsive controls for narrow devices */
@media (max-width: 819px) {
  .controls {
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
  }
}

.controls .meta-title {
  grid-column: 1 / -1;
  text-align: center;
  margin: 0 0 0.5rem 0;
}

.slider-group {
  background: var(--bg-tertiary);
  padding: 0.75rem;
  border: 1px solid var(--border-muted);
  border-radius: 8px;
  width: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

/* Responsive slider group for mobile */
@media (max-width: 819px) {
  .slider-group {
    padding: 0.5rem;
  }
}

.slider-header {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.5rem;
}

.badge {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 999px;
  font-weight: 600;
}

.badge.start {
  background: var(--brand-500, #ff6600);
  color: #ffffff;
}

.badge.end {
  background: var(--brand-500, #ff6600);
  color: #ffffff;
}

.metric {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--text-secondary);
}

.metric .icon {
  width: 18px;
  text-align: center;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.25rem 0.5rem;
  align-items: center;
  margin-bottom: 0.75rem;
  width: 100%;
  box-sizing: border-box;
}

/* Responsive metrics grid for narrow devices */
@media (max-width: 819px) {
  .metrics-grid {
    grid-template-columns: 1fr;
    gap: 0.25rem;
  }
}

@media (max-width: 480px) {
  .metrics-grid {
    grid-template-columns: 1fr;
    gap: 0.25rem;
  }
}

.gps-col {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--text-secondary);
}

.gps-col .label {
  font-size: 12px;
  color: var(--text-tertiary);
}

.gps-col .value {
  font-variant-numeric: tabular-nums;
}

.chart-wrapper {
  width: 100%;
  overflow: visible;
  margin-bottom: 20px;
}

.chart-container {
  position: relative;
  width: 100%;
  overflow: visible;
}

.chart {
  width: 100%;
  height: 200px;
  max-height: 200px;
  cursor: crosshair;
}

.vertical-slider {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 20px;
  cursor: grab;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.vertical-slider:active {
  cursor: grabbing;
}

.slider-handle {
  position: relative;
  width: 16px;
  height: 16px;
  background: var(--brand-500, #ff6600);
  border: 2px solid #ffffff;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  margin-bottom: 4px;
  z-index: 11;
  display: flex;
  align-items: center;
  justify-content: center;
}

.slider-line {
  width: 3px;
  height: 100%;
  background: var(--brand-500, #ff6600);
  border-radius: 2px;
  opacity: 0.8;
}

.start-slider .slider-handle::after {
  content: 'S';
  color: white;
  font-size: 10px;
  font-weight: bold;
  line-height: 1;
}

.end-slider .slider-handle::after {
  content: 'E';
  color: white;
  font-size: 10px;
  font-weight: bold;
  line-height: 1;
}

.slider-index {
  position: absolute;
  bottom: -22px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--text-primary);
  color: var(--bg-primary);
  font-size: 11px;
  line-height: 1;
  padding: 2px 6px;
  border-radius: 8px;
  white-space: nowrap;
  z-index: 14;
  max-width: 40px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.slider-controls {
  position: absolute;
  top: 0;
  left: -18px;
  right: -18px;
  height: 22px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 13;
  pointer-events: none;
}

.slider-btn {
  width: 12px;
  height: 12px;
  border: none;
  border-radius: 50%;
  background: var(--brand-500, #ff6600);
  color: #ffffff;
  font-size: 8px;
  font-weight: bold;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: all;
  transition: background-color 0.2s;
}

.slider-btn:hover:not(:disabled) {
  background: var(--brand-600, #e55a00);
}

.slider-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.end-slider .slider-handle {
  background: var(--blue-500);
}

.end-slider .slider-line {
  background: var(--blue-500);
}

.end-slider .slider-btn {
  background: var(--blue-500);
}

.end-slider .slider-btn:hover:not(:disabled) {
  background: var(--blue-600);
}

.badge.end {
  background: var(--blue-500);
  color: #ffffff;
}
</style>
