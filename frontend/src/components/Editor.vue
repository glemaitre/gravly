<template>
  <header class="topbar">
    <div class="topbar-inner">
      <div class="logo">
        <img :src="logoUrl" alt="Cycling Segments" class="logo-img" />
      </div>
      <nav class="nav">
        <!-- Add actions/links here if needed -->
      </nav>
    </div>
  </header>
  <div class="editor">
    <!-- Sidebar completely independent -->
    <div class="sidebar">
      <div class="sidebar-scroll">
        <div class="card menu-card">
          <div class="menu-section">
            <div class="menu-section-title">Import from ...</div>
            <ul class="menu-list">
              <li class="menu-item" @click="triggerFileOpen" title="Load GPX file" role="button">
                <span class="icon" aria-hidden="true"><i class="fa-solid fa-file-lines"></i></span>
                <span class="text">GPX file</span>
              </li>
            </ul>
            <input ref="fileInput" type="file" accept=".gpx" @change="onFileChange" hidden />
          </div>
          <div class="menu-section">
            <div class="menu-section-title">Segments</div>
            <ul class="menu-list">
              <li
                class="menu-item action"
                :class="{ disabled: isSaveDisabled }"
                :aria-disabled="isSaveDisabled"
                :title="isSaveDisabled ? saveDisabledTitle : 'Save in DB'"
                @click="!isSaveDisabled && onSubmit()"
              >
                <span class="icon" aria-hidden="true"><i class="fa-solid fa-database"></i></span>
                <span class="text">Save in DB</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- Main content area independent from sidebar -->
    <div class="content">
      <div class="page">
        <div class="main-col">
        <div v-if="loaded">
          <div class="card card-map">
            <div id="map" class="map"></div>
          </div>
          <div class="card card-elevation">
            <div class="chart-wrapper">
              <div class="chart-container">
                <canvas ref="chartCanvas" class="chart"></canvas>
                <!-- Draggable vertical sliders -->
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
                      title="Move start marker back one point"
                    >-</button>
                    <button
                      class="slider-btn slider-btn-plus"
                      @click="moveSlider('start', 1)"
                      :disabled="startIndex >= endIndex - 1"
                      title="Move start marker forward one point"
                    >+</button>
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
                      title="Move end marker back one point"
                    >-</button>
                    <button
                      class="slider-btn slider-btn-plus"
                      @click="moveSlider('end', 1)"
                      :disabled="endIndex >= points.length - 1"
                      title="Move end marker forward one point"
                    >+</button>
                  </div>
                </div>
              </div>
            </div>
            <div class="axis-toggle below">
              <button type="button" class="seg left" :class="{ active: xMode === 'distance' }" @click="xMode = 'distance'">Distance (km)</button>
              <button type="button" class="seg right" :class="{ active: xMode === 'time' }" @click="xMode = 'time'">Time (hh:mm:ss)</button>
            </div>

            <!-- Selector controls moved here -->
            <div class="controls" ref="controlsCard">
              <div class="slider-group">
                <div class="slider-header">
                  <span class="badge start">Start</span>
                </div>
                <div class="metrics-grid">
                  <div class="metric" title="Elapsed time from start">
                    <span class="icon"><i class="fa-solid fa-clock"></i></span>
                    <span class="value">{{ formatElapsed(startIndex) }}</span>
                  </div>
                  <div class="metric" title="Distance (km)">
                    <span class="icon"><i class="fa-solid fa-ruler"></i></span>
                    <span class="value">{{ formatKm(distanceAt(startIndex)) }}</span>
                  </div>
                  <div class="metric" title="Elevation (m)">
                    <span class="icon"><i class="fa-solid fa-mountain"></i></span>
                    <span class="value">{{ formatElevation(pointAt(startIndex)?.ele) }}</span>
                  </div>
                  <div class="gps-title" title="GPS location"><span class="icon"><i class="fa-solid fa-location-dot"></i></span><span class="text">GPS</span></div>
                  <div class="gps-col"><span class="label">Lat</span><span class="value">{{ pointAt(startIndex)?.lat?.toFixed(5) ?? '-' }}</span></div>
                  <div class="gps-col"><span class="label">Lon</span><span class="value">{{ pointAt(startIndex)?.lon?.toFixed(5) ?? '-' }}</span></div>
                </div>
              </div>
              <div class="slider-group">
                <div class="slider-header">
                  <span class="badge end">End</span>
                </div>
                <div class="metrics-grid">
                  <div class="metric" title="Elapsed time from start">
                    <span class="icon"><i class="fa-solid fa-clock"></i></span>
                    <span class="value">{{ formatElapsed(endIndex) }}</span>
                  </div>
                  <div class="metric" title="Distance (km)">
                    <span class="icon"><i class="fa-solid fa-ruler"></i></span>
                    <span class="value">{{ formatKm(distanceAt(endIndex)) }}</span>
                  </div>
                  <div class="metric" title="Elevation (m)">
                    <span class="icon"><i class="fa-solid fa-mountain"></i></span>
                    <span class="value">{{ formatElevation(pointAt(endIndex)?.ele) }}</span>
                  </div>
                  <div class="gps-title" title="GPS location"><span class="icon"><i class="fa-solid fa-location-dot"></i></span><span class="text">GPS</span></div>
                  <div class="gps-col"><span class="label">Lat</span><span class="value">{{ pointAt(endIndex)?.lat?.toFixed(5) ?? '-' }}</span></div>
                  <div class="gps-col"><span class="label">Lon</span><span class="value">{{ pointAt(endIndex)?.lon?.toFixed(5) ?? '-' }}</span></div>
                </div>
              </div>
            </div>
          </div>

          <!-- Segment information under selector -->
          <div class="section-indicator">
            <span class="icon" aria-hidden="true"><i class="fa-solid fa-circle-info"></i></span>
            <span class="label">Segment information</span>
          </div>
          <form class="card meta" @submit.prevent="onSubmit">
            <div>
              <label for="name">Segment name <span class="req">*</span></label>
              <input id="name" v-model="name" type="text" required />
            </div>

            <div class="grid">
              <label class="group-main-label">Tire</label>
              <div class="tire-group">
                <div class="tire-group-header">
                  <span class="icon" aria-hidden="true"><i class="fa-solid fa-sun"></i></span>
                  <span class="tire-group-title">Dry</span>
                </div>
                <p class="tire-group-help">Use for clear, dry conditions where grip is high.</p>
                <div class="tire-row" role="radiogroup" aria-label="Tire dry">
                  <label class="tire-option" :class="{ selected: tireDry === 'slick' }">
                    <input type="radio" name="tireDry" value="slick" v-model="tireDry" />
                    <img :src="tireImages.slick" alt="slick" />
                    <span class="tire-caption">slick</span>
                  </label>
                  <label class="tire-option" :class="{ selected: tireDry === 'semi-slick' }">
                    <input type="radio" name="tireDry" value="semi-slick" v-model="tireDry" />
                    <img :src="tireImages.semiSlick" alt="semi-slick" />
                    <span class="tire-caption">semi-slick</span>
                  </label>
                  <label class="tire-option" :class="{ selected: tireDry === 'knobs' }">
                    <input type="radio" name="tireDry" value="knobs" v-model="tireDry" />
                    <img :src="tireImages.knobs" alt="knobs" />
                    <span class="tire-caption">knobs</span>
                  </label>
                </div>
              </div>
              <div class="tire-group">
                <div class="tire-group-header">
                  <span class="icon" aria-hidden="true"><i class="fa-solid fa-cloud-rain"></i></span>
                  <span class="tire-group-title">Wet</span>
                </div>
                <p class="tire-group-help">Use for rain, mud, or low-grip conditions.</p>
                <div class="tire-row" role="radiogroup" aria-label="Tire wet">
                  <label class="tire-option" :class="{ selected: tireWet === 'slick' }">
                    <input type="radio" name="tireWet" value="slick" v-model="tireWet" />
                    <img :src="tireImages.slick" alt="slick" />
                    <span class="tire-caption">slick</span>
                  </label>
                  <label class="tire-option" :class="{ selected: tireWet === 'semi-slick' }">
                    <input type="radio" name="tireWet" value="semi-slick" v-model="tireWet" />
                    <img :src="tireImages.semiSlick" alt="semi-slick" />
                    <span class="tire-caption">semi-slick</span>
                  </label>
                  <label class="tire-option" :class="{ selected: tireWet === 'knobs' }">
                    <input type="radio" name="tireWet" value="knobs" v-model="tireWet" />
                    <img :src="tireImages.knobs" alt="knobs" />
                    <span class="tire-caption">knobs</span>
                  </label>
                </div>
              </div>
            </div>
            <!-- Save button is available in the sidebar -->
          </form>
        </div>

        <div v-if="!loaded" class="empty">
          <p>Use File → Load GPX to begin.</p>
        </div>
        </div>
      </div>
    </div>

    <p v-if="message" class="message">{{ message }}</p>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, onUnmounted, ref, watch, nextTick, computed } from 'vue'
import logoUrl from '../assets/images/logo.svg'
import L from 'leaflet'
import { Chart, LineController, LineElement, PointElement, LinearScale, Title, CategoryScale, Filler, Tooltip } from 'chart.js'
import annotationPlugin from 'chartjs-plugin-annotation'
import tireSlickUrl from '../assets/images/slick.png'
import tireSemiSlickUrl from '../assets/images/semi-slick.png'
import tireKnobsUrl from '../assets/images/ext.png'

Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Title, Filler, Tooltip, annotationPlugin)

type Tire = 'slick' | 'semi-slick' | 'knobs'

const tireImages = { slick: tireSlickUrl, semiSlick: tireSemiSlickUrl, knobs: tireKnobsUrl }

type TrackPoint = { lat: number; lon: number; ele: number; time?: string }

const loaded = ref(false)
const sidebarCollapsed = ref(false)
const name = ref('')
const tireDry = ref<Tire>('slick')
const tireWet = ref<Tire>('slick')
const submitting = ref(false)
const message = ref('')

const fileInput = ref<HTMLInputElement | null>(null)
const points = ref<TrackPoint[]>([])
const startIndex = ref(0)
const endIndex = ref(0)
const cumulativeKm = ref<number[]>([])
const cumulativeSec = ref<number[]>([])
const xMode = ref<'distance' | 'time'>('distance')

const controlsCard = ref<HTMLElement | null>(null)

// Save button state and tooltip
const isSaveDisabled = computed(() => submitting.value || !name.value || !loaded.value)
const saveDisabledTitle = computed(() => {
  if (!loaded.value) return 'Load a GPX first to enable saving'
  if (!name.value) return 'Enter a segment name to enable saving'
  if (submitting.value) return 'Submitting…'
  return ''
})

let map: any = null
let fullLine: any = null
let selectedLine: any = null
let baseLayer: any = null

const chartCanvas = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null
const smoothedElevations = ref<number[]>([])

// Slider functionality
const isDragging = ref(false)
const dragType = ref<'start' | 'end' | null>(null)
const startSliderPosition = ref(0)
const endSliderPosition = ref(100)

// Overlap detection and offsetting
const endSliderOffset = ref(0)
const overlapThreshold = 20 // pixels - minimum distance before offsetting
const constantOffset = 25 // pixels - constant offset amount when overlap detected

// Slider bounds and index badge positions
const startMin = computed(() => 0)
const startMax = computed(() => Math.max(1, endIndex.value - 1))
const endMin = computed(() => Math.min(points.value.length - 1, startIndex.value + 1))
const endMax = computed(() => points.value.length - 1)
function toPercent(value: number, min: number, max: number): number {
  if (max <= min) return 0
  return ((value - min) / (max - min)) * 100
}
const startPercent = computed(() => toPercent(startIndex.value, startMin.value, startMax.value))
const endPercent = computed(() => toPercent(endIndex.value, endMin.value, endMax.value))

// Overlap detection function
function checkSliderOverlap() {
  if (!chart || !chartCanvas.value) return

  const containerRect = chartCanvas.value.parentElement!.getBoundingClientRect()
  const sliderWidth = 20 // px - matches CSS width
  const controlsExtension = 18 // px - how far controls extend from slider center

  // Calculate pixel positions of slider centers
  const startPixelCenter = (startSliderPosition.value / 100) * containerRect.width + (sliderWidth / 2)
  const endPixelCenter = (endSliderPosition.value / 100) * containerRect.width + (sliderWidth / 2)

  // Calculate the bounds of each slider's control area
  const startControlRight = startPixelCenter + controlsExtension
  const endControlLeft = endPixelCenter - controlsExtension

  // Check if controls overlap
  const distance = endControlLeft - startControlRight

  if (distance < overlapThreshold) {
    // Apply constant offset when overlap detected
    endSliderOffset.value = constantOffset
  } else {
    endSliderOffset.value = 0
  }
}

// Update slider positions when indices change
watch([startIndex, endIndex], () => {
  if (points.value.length > 0 && chart && chartCanvas.value) {
    // Get the data values
    const startX = getX(startIndex.value)
    const endX = getX(endIndex.value)

    // Get the canvas and container dimensions
    const canvasRect = chart.canvas.getBoundingClientRect()
    const containerRect = chartCanvas.value.parentElement!.getBoundingClientRect()

    // Convert data values to pixel positions using Chart.js built-in method
    const startPixel = chart.scales.x.getPixelForValue(startX)
    const endPixel = chart.scales.x.getPixelForValue(endX)

    // Calculate the offset of the canvas within the container
    const canvasOffsetLeft = canvasRect.left - containerRect.left

    // Adjust pixel positions to be relative to the container
    const startPixelInContainer = startPixel + canvasOffsetLeft
    const endPixelInContainer = endPixel + canvasOffsetLeft

    // Convert to percentage of container width and center the slider
    const sliderWidth = 20 // px - matches CSS width
    const startPixelCentered = startPixelInContainer - (sliderWidth / 2)
    const endPixelCentered = endPixelInContainer - (sliderWidth / 2)

    startSliderPosition.value = (startPixelCentered / containerRect.width) * 100
    endSliderPosition.value = (endPixelCentered / containerRect.width) * 100

    // Check for overlap after position update
    checkSliderOverlap()
  }
})

function triggerFileOpen() {
  fileInput.value?.click()
}

function onFileChange(ev: Event) {
  const input = ev.target as HTMLInputElement
  const file = input.files && input.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = async () => {
    const text = String(reader.result)
    const parsed = parseGPX(text)
    if (parsed.length < 2) {
      message.value = 'GPX has insufficient points.'
      return
    }
    points.value = parsed
    cumulativeKm.value = computeCumulativeKm(parsed)
    cumulativeSec.value = computeCumulativeSec(parsed)
    smoothedElevations.value = computeSmoothedElevations(parsed, 5)
    startIndex.value = 0
    endIndex.value = parsed.length - 1
    loaded.value = true
    message.value = ''
    await nextTick()
    renderMap()
    renderChart()
  }
  reader.readAsText(file)
}

function computeCumulativeKm(pts: TrackPoint[]): number[] {
  const out: number[] = [0]
  for (let i = 1; i < pts.length; i++) {
    const d = haversine(pts[i-1].lat, pts[i-1].lon, pts[i].lat, pts[i].lon)
    out.push(out[i-1] + d)
  }
  return out
}

function haversine(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLon = (lon2 - lon1) * Math.PI / 180
  const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
  return R * c
}

function distanceAt(i: number): number { return cumulativeKm.value[i] ?? 0 }
function pointAt(i: number): TrackPoint | undefined { return points.value[i] }
function formatKm(km?: number): string { return km == null ? '-' : `${km.toFixed(2)} km` }
function formatElevation(ele?: number): string { return ele == null ? '-' : `${Math.round(ele)} m` }
function formatLatLon(p?: TrackPoint): string { return p ? `${p.lat.toFixed(5)}, ${p.lon.toFixed(5)}` : '-' }
function formatTime(t?: string): string { return t ? new Date(t).toLocaleString() : '-' }
function formatElapsed(i: number): string {
  const t0 = points.value[0]?.time ? new Date(points.value[0].time as string).getTime() : undefined
  const ti = points.value[i]?.time ? new Date(points.value[i].time as string).getTime() : undefined
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

function onStartInput(e: Event) {
  const v = Number((e.target as HTMLInputElement).value)
  startIndex.value = Math.min(v, endIndex.value - 1)
}

function onEndInput(e: Event) {
  const v = Number((e.target as HTMLInputElement).value)
  endIndex.value = Math.max(v, startIndex.value + 1)
}

// Move slider by single index
function moveSlider(type: 'start' | 'end', direction: -1 | 1) {
  if (type === 'start') {
    const newIndex = startIndex.value + direction
    if (newIndex >= 0 && newIndex < endIndex.value) {
      startIndex.value = newIndex
    }
  } else {
    const newIndex = endIndex.value + direction
    if (newIndex > startIndex.value && newIndex < points.value.length) {
      endIndex.value = newIndex
    }
  }
}

// Slider drag functionality
function startDrag(type: 'start' | 'end', event: MouseEvent | TouchEvent) {
  event.preventDefault()
  isDragging.value = true
  dragType.value = type

  const handleMouseMove = (e: MouseEvent | TouchEvent) => {
    if (!isDragging.value || !chartCanvas.value || !chart) return

    const rect = chartCanvas.value.getBoundingClientRect()
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX
    const x = clientX - rect.left

    // Convert pixel position to data x value
    const dataX = chart.scales.x.getValueForPixel(x)
    if (dataX === undefined) return

    // Find closest point index
    let closestIndex = 0
    let minDistance = Infinity

    for (let i = 0; i < points.value.length; i++) {
      const pointX = getX(i)
      const distance = Math.abs(pointX - dataX)
      if (distance < minDistance) {
        minDistance = distance
        closestIndex = i
      }
    }

    if (type === 'start') {
      // S slider cannot go beyond E slider
      const newIndex = Math.min(closestIndex, endIndex.value - 1)
      startIndex.value = Math.max(0, newIndex)
    } else {
      // E slider cannot go before S slider
      const newIndex = Math.max(closestIndex, startIndex.value + 1)
      endIndex.value = Math.min(points.value.length - 1, newIndex)
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

function parseGPX(xmlText: string): TrackPoint[] {
  const doc = new DOMParser().parseFromString(xmlText, 'application/xml')
  const trkpts = Array.from(doc.getElementsByTagName('trkpt'))
  const pts: TrackPoint[] = []
  for (const el of trkpts) {
    const lat = parseFloat(el.getAttribute('lat') || '0')
    const lon = parseFloat(el.getAttribute('lon') || '0')
    const eleEl = el.getElementsByTagName('ele')[0]
    const timeEl = el.getElementsByTagName('time')[0]
    const ele = eleEl ? parseFloat(eleEl.textContent || '0') : 0
    const time = timeEl ? timeEl.textContent || undefined : undefined
    if (!Number.isNaN(lat) && !Number.isNaN(lon)) {
      pts.push({ lat, lon, ele, time })
    }
  }
  return pts
}

function renderMap() {
  if (!map) {
    const container = document.getElementById('map')
    if (!container) return
    map = L.map(container)
  }
  // compute bounds
  const latlngs = points.value.map(p => [p.lat, p.lon]) as [number, number][]
  const bounds = L.latLngBounds(latlngs)
  map!.invalidateSize()
  map!.fitBounds(bounds, { padding: [20, 20] })

  // base layer
  if (!baseLayer) {
    baseLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap'
    })
    baseLayer.addTo(map!)
  }

  // full path
  if (fullLine) fullLine.remove()
  fullLine = L.polyline(latlngs, { color: '#888', weight: 4 })
  fullLine.addTo(map!)

  // selected segment
  updateSelectedPolyline()
}

function updateSelectedPolyline() {
  if (!map) return
  const segLatLngs = points.value.slice(startIndex.value, endIndex.value + 1).map(p => [p.lat, p.lon]) as [number, number][]
  if (selectedLine) selectedLine.remove()
  selectedLine = L.polyline(segLatLngs, { color: getComputedStyle(document.documentElement).getPropertyValue('--brand-500').trim() || '#ff6600', weight: 5 })
  selectedLine.addTo(map)
}

function renderChart() {
  if (!chartCanvas.value) return
  const ctx = chartCanvas.value.getContext('2d')!
  const labels = points.value.map((_, i) => i)
  const data = buildXYData()
  const fullData = buildFullXYData()

  chart?.destroy()
  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Elevation (m)',
          data: fullData.map(d => ({ x: d.x, y: d.y })),
          borderColor: getComputedStyle(document.documentElement).getPropertyValue('--brand-500').trim() || '#ff6600',
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 5,
          backgroundColor: 'transparent',
          fill: false,
          tension: 0.1,
          parsing: false
        },
        // Orange fill between selectors (under elevation line)
        {
          label: 'Selected Area',
          data: buildSelectedAreaData(),
          borderColor: 'transparent',
          backgroundColor: 'rgba(255, 102, 0, 0.15)',
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
          max: getX(points.value.length - 1),
          ticks: { callback: (v: any) => formatXTick(Number(v)) }
        },
        y: {
          display: true,
          title: { display: true, text: 'Elevation (m)' },
          min: Math.min(...smoothedElevations.value)
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          filter: function(tooltipItem) {
            // Only show tooltip for the elevation line (first dataset)
            return tooltipItem.datasetIndex === 0;
          },
          callbacks: {
            title: function(context) {
              const dataIndex = context[0].dataIndex;
              const xValue = context[0].parsed.x;
              return xMode.value === 'distance' ? `${xValue.toFixed(2)} km` : formatXTick(xValue);
            },
            label: function(context) {
              const yValue = context.parsed.y;
              return `Elevation: ${Math.round(yValue)} m`;
            }
          }
        },
      },
      onClick: (event, elements) => {
        if (event && chart && event.x !== null && event.y !== null) {
          const rect = chart.canvas.getBoundingClientRect()
          const x = event.x - rect.left
          const y = event.y - rect.top

          const dataX = chart.scales.x.getValueForPixel(x)
          const dataY = chart.scales.y.getValueForPixel(y)

          if (dataX === undefined || dataY === undefined) return

          // Find closest point index based on x position
          let closestIndex = 0
          let minDistance = Infinity

          for (let i = 0; i < points.value.length; i++) {
            const pointX = getX(i)
            const distance = Math.abs(pointX - dataX)
            if (distance < minDistance) {
              minDistance = distance
              closestIndex = i
            }
          }

          // Determine which selector to update based on x position
          const startX = getX(startIndex.value)
          const endX = getX(endIndex.value)

          if (dataX < startX) {
            // Click before start line - update start
            startIndex.value = Math.min(closestIndex, endIndex.value - 1)
          } else if (dataX > endX) {
            // Click after end line - update end
            endIndex.value = Math.max(closestIndex, startIndex.value + 1)
          } else {
            // Click between lines - determine which is closer
            const distToStart = Math.abs(dataX - startX)
            const distToEnd = Math.abs(dataX - endX)

            if (distToStart < distToEnd) {
              startIndex.value = Math.min(closestIndex, endIndex.value - 1)
            } else {
              endIndex.value = Math.max(closestIndex, startIndex.value + 1)
            }
          }
        }
      }
    }
  })

  // Update slider positions after chart is created
  nextTick(() => {
    if (points.value.length > 0 && chart && chartCanvas.value) {
      // Get the data values
      const startX = getX(startIndex.value)
      const endX = getX(endIndex.value)

      // Get the canvas and container dimensions
      const canvasRect = chart.canvas.getBoundingClientRect()
      const containerRect = chartCanvas.value.parentElement!.getBoundingClientRect()

      // Convert data values to pixel positions using Chart.js built-in method
      const startPixel = chart.scales.x.getPixelForValue(startX)
      const endPixel = chart.scales.x.getPixelForValue(endX)

      // Calculate the offset of the canvas within the container
      const canvasOffsetLeft = canvasRect.left - containerRect.left

      // Adjust pixel positions to be relative to the container
      const startPixelInContainer = startPixel + canvasOffsetLeft
      const endPixelInContainer = endPixel + canvasOffsetLeft

      // Convert to percentage of container width and center the slider
      const sliderWidth = 20 // px - matches CSS width
      const startPixelCentered = startPixelInContainer - (sliderWidth / 2)
      const endPixelCentered = endPixelInContainer - (sliderWidth / 2)

      startSliderPosition.value = (startPixelCentered / containerRect.width) * 100
      endSliderPosition.value = (endPixelCentered / containerRect.width) * 100

      // Check for overlap after initial position setting
      checkSliderOverlap()
    }
  })
}

function getX(i: number): number {
  return xMode.value === 'distance' ? (cumulativeKm.value[i] ?? 0) : (cumulativeSec.value[i] ?? 0)
}

function buildXYData(): { x: number, y: number }[] {
  return points.value.map((p, i) => ({ x: getX(i), y: smoothedElevations.value[i] ?? p.ele }))
}

function buildFullXYData(): { x: number, y: number }[] {
  return points.value.map((p, i) => ({ x: getX(i), y: smoothedElevations.value[i] ?? p.ele }))
}

function buildSelectedAreaData(): { x: number, y: number }[] {
  // Create a dataset that only contains the selected portion of the elevation data
  // This will be used with fill: 'origin' to fill from the baseline to the line
  const selectedData = []

  for (let i = startIndex.value; i <= endIndex.value; i++) {
    selectedData.push({
      x: getX(i),
      y: smoothedElevations.value[i] ?? points.value[i]?.ele ?? 0
    })
  }

  return selectedData
}

function buildBeforeStartAreaData(): { x: number, y: number }[] {
  const minY = Math.min(...smoothedElevations.value)

  // Create area under the elevation line before the start selector
  const beforeData = []

  // First, add points along the elevation line from start to beginning
  for (let i = startIndex.value; i >= 0; i--) {
    beforeData.push({
      x: getX(i),
      y: smoothedElevations.value[i] ?? points.value[i]?.ele ?? 0
    })
  }

  // Then, add points along the bottom (min elevation) from beginning back to start
  for (let i = 0; i <= startIndex.value; i++) {
    beforeData.push({
      x: getX(i),
      y: minY
    })
  }

  return beforeData
}

function buildAfterEndAreaData(): { x: number, y: number }[] {
  const minY = Math.min(...smoothedElevations.value)

  // Create area under the elevation line after the end selector
  const afterData = []

  // First, add points along the elevation line from end to the end
  for (let i = endIndex.value; i < points.value.length; i++) {
    afterData.push({
      x: getX(i),
      y: smoothedElevations.value[i] ?? points.value[i]?.ele ?? 0
    })
  }

  // Then, add points along the bottom (min elevation) from end back to end
  for (let i = points.value.length - 1; i >= endIndex.value; i--) {
    afterData.push({
      x: getX(i),
      y: minY
    })
  }

  return afterData
}

function xAxisTitle(): string { return xMode.value === 'distance' ? 'Distance (km)' : 'Time (hh:mm:ss)' }
function formatXTick(v: number): string {
  if (xMode.value === 'distance') return `${v.toFixed(1)} km`
  const sec = Math.max(0, Math.round(v))
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = sec % 60
  const hh = h > 0 ? `${h}:` : ''
  const mm = h > 0 ? String(m).padStart(2, '0') : String(m)
  const ss = String(s).padStart(2, '0')
  return `${hh}${mm}:${ss}`
}

function computeCumulativeSec(pts: TrackPoint[]): number[] {
  const out: number[] = [0]
  for (let i = 1; i < pts.length; i++) {
    const t0 = pts[i-1].time ? new Date(pts[i-1].time as string).getTime() : undefined
    const t1 = pts[i].time ? new Date(pts[i].time as string).getTime() : undefined
    const d = (t0 && t1) ? Math.max(0, (t1 - t0) / 1000) : 1
    out.push(out[i-1] + d)
  }
  return out
}

function computeSmoothedElevations(pts: TrackPoint[], windowSize = 5): number[] {
  const half = Math.floor(windowSize / 2)
  const out: number[] = new Array(pts.length)
  for (let i = 0; i < pts.length; i++) {
    let sum = 0
    let count = 0
    for (let j = Math.max(0, i - half); j <= Math.min(pts.length - 1, i + half); j++) {
      sum += pts[j].ele
      count += 1
    }
    out[i] = count ? sum / count : pts[i].ele
  }
  return out
}

watch([startIndex, endIndex], () => {
  if (startIndex.value >= endIndex.value) {
    endIndex.value = Math.min(points.value.length - 1, startIndex.value + 1)
  }
  updateSelectedPolyline()
  // Update chart area data
  if (chart) {
    // Update area datasets
    // @ts-ignore
    chart.data.datasets[1].data = buildSelectedAreaData()

    chart.update()
  }
  // Fit map to selected segment
  if (map && points.value.length > 1) {
    const segLatLngs = points.value.slice(startIndex.value, endIndex.value + 1).map(p => [p.lat, p.lon]) as [number, number][]
    const segBounds = L.latLngBounds(segLatLngs)
    map.fitBounds(segBounds, { padding: [20, 20] })
  }
})

watch(xMode, () => {
  if (!chart) return
  const fullData = buildFullXYData()

  // Update all datasets
  // @ts-ignore
  chart.data.datasets[0].data = fullData.map(d => ({ x: d.x, y: d.y }))
  // @ts-ignore
  chart.data.datasets[1].data = buildSelectedAreaData()

  // Update x-axis configuration
  // @ts-ignore
  chart.options.scales.x.ticks.callback = (v) => formatXTick(Number(v))
  // @ts-ignore
  chart.options.scales.x.min = getX(0)
  // @ts-ignore
  chart.options.scales.x.max = getX(points.value.length - 1)

  chart.update()

  // Update slider positions after chart update
  nextTick(() => {
    if (points.value.length > 0 && chart && chartCanvas.value) {
      // Get the data values
      const startX = getX(startIndex.value)
      const endX = getX(endIndex.value)

      // Get the canvas and container dimensions
      const canvasRect = chart.canvas.getBoundingClientRect()
      const containerRect = chartCanvas.value.parentElement!.getBoundingClientRect()

      // Convert data values to pixel positions using Chart.js built-in method
      const startPixel = chart.scales.x.getPixelForValue(startX)
      const endPixel = chart.scales.x.getPixelForValue(endX)

      // Calculate the offset of the canvas within the container
      const canvasOffsetLeft = canvasRect.left - containerRect.left

      // Adjust pixel positions to be relative to the container
      const startPixelInContainer = startPixel + canvasOffsetLeft
      const endPixelInContainer = endPixel + canvasOffsetLeft

      // Convert to percentage of container width and center the slider
      const sliderWidth = 20 // px - matches CSS width
      const startPixelCentered = startPixelInContainer - (sliderWidth / 2)
      const endPixelCentered = endPixelInContainer - (sliderWidth / 2)

      startSliderPosition.value = (startPixelCentered / containerRect.width) * 100
      endSliderPosition.value = (endPixelCentered / containerRect.width) * 100

      // Check for overlap after xMode position update
      checkSliderOverlap()
    }
  })
})

watch(sidebarCollapsed, () => {
  if (map) {
    setTimeout(() => map!.invalidateSize(), 220)
  }
})

watch(loaded, async () => {
  await nextTick()
})

onMounted(() => {
  const onResize = () => {
    if (map) {
      // let layout settle before resizing the map canvas
      setTimeout(() => map!.invalidateSize(), 0)
    }
  }
  window.addEventListener('resize', onResize)
  ;(window as any).__editorOnResize = onResize

})

onUnmounted(() => {
  const onResize = (window as any).__editorOnResize
  if (onResize) window.removeEventListener('resize', onResize)
})

function buildSegmentGPX(): string {
  const segPoints = points.value.slice(startIndex.value, endIndex.value + 1)
  const trkpts = segPoints
    .map(p => `<trkpt lat="${p.lat}" lon="${p.lon}"><ele>${p.ele}</ele>${p.time ? `<time>${p.time}</time>` : ''}</trkpt>`)
    .join('')
  return `<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="editor" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><name>${escapeXml(name.value || 'segment')}</name><trkseg>${trkpts}</trkseg></trk>
</gpx>`
}

function escapeXml(s: string): string {
  return s.replace(/[<>&"']/g, c => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&apos;' }[c] as string))
}

async function onSubmit() {
  if (!loaded.value || points.value.length < 2) {
    message.value = 'Load a GPX first.'
    return
  }
  submitting.value = true
  message.value = ''
  try {
    const xml = buildSegmentGPX()
    const blob = new Blob([xml], { type: 'application/gpx+xml' })
    const formData = new FormData()
    formData.append('name', name.value)
    formData.append('tire_dry', tireDry.value)
    formData.append('tire_wet', tireWet.value)
    formData.append('file', blob, (name.value || 'segment') + '.gpx')

    const res = await fetch('/api/segments', { method: 'POST', body: formData })
    if (!res.ok) {
      const detail = await res.text()
      throw new Error(detail || 'Failed to create segment')
    }

    // Reset for next segment
    name.value = ''
    tireDry.value = 'slick'
    tireWet.value = 'slick'
    loaded.value = false
    points.value = []
    chart?.destroy(); chart = null
    if (fullLine) { fullLine.remove(); fullLine = null }
    if (selectedLine) { selectedLine.remove(); selectedLine = null }
    message.value = 'Segment created successfully.'
  } catch (err: any) {
    message.value = err.message || 'Error while creating segment.'
  } finally {
    submitting.value = false
  }
}
</script>

<style>
/* Local brand variables to support the standalone editor entry */
:root {
  --brand-50: #ffe6d5ff;
  --brand-100: #ffccaaff;
  --brand-200: #ffb380ff;
  --brand-300: #ff9955ff;
  --brand-400: #ff7f2aff;
  --brand-500: #ff6600ff;

  --brand-primary: var(--brand-500);
  --brand-primary-hover: #e65c00;
  --brand-accent: var(--brand-300);

  /* Blue colors for end segment */
  --blue-50: #eff6ff;
  --blue-100: #dbeafe;
  --blue-200: #bfdbfe;
  --blue-300: #93c5fd;
  --blue-400: #60a5fa;
  --blue-500: #3b82f6;
  --blue-600: #2563eb;
  --blue-700: #1d4ed8;
}
</style>

<style scoped>
.editor { display: flex; min-height: 100vh; background: #f8fafc; overflow-x: hidden; position: relative; }
.content { flex: 1 1 auto; padding: 1rem 1.5rem; width: 100%; box-sizing: border-box; overflow-x: hidden; }
.page { max-width: 1000px; margin: 0 auto; width: 100%; box-sizing: border-box; overflow-x: hidden; }
.main-col { display: flex; flex-direction: column; gap: 0.75rem; min-width: 0; overflow: hidden; }
.actions-col { display: flex; flex-direction: column; gap: 0.75rem; position: sticky; top: 12px; align-self: start; height: fit-content; width: var(--sidebar-w); }

.sidebar { --sidebar-w: 200px; width: var(--sidebar-w); background: transparent; border-right: none; padding: 0; margin: 0; box-sizing: border-box; position: fixed; top: var(--topbar-h, 48px); left: calc(50% - 500px - var(--sidebar-w)); display: flex; flex-direction: column; height: calc(100vh - var(--topbar-h, 48px)); z-index: 100; }
.sidebar-scroll { display: flex; flex-direction: column; align-items: flex-start; gap: 0.75rem; max-height: calc(100vh - var(--topbar-h, 48px)); overflow-y: auto; overflow-x: hidden; padding: 1rem; }
.sidebar .card { margin: 0; width: 100%; box-sizing: border-box; }
.sidebar .group-title { margin: 0 0 0.75rem 0; font-size: 1rem; font-weight: 700; color: #111827; text-align: center; text-transform: none; letter-spacing: 0; }
.sidebar .menu-btn { width: 100%; justify-content: center; padding: 0.5rem 0; gap: 0.5rem; }
.sidebar-header { display: none; }
.brand { display: none; }
.sidebar-group { display: flex; flex-direction: column; gap: 0.25rem; }
.group-title { font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.06em; margin: 0.25rem 0; }
.menu-btn { display: flex; align-items: center; gap: 0.75rem; border: none; background: transparent; padding: 0.5rem; border-radius: 8px; cursor: pointer; color: #111827; text-align: left; }
.menu-btn:hover { background: #f3f4f6; }
.menu-btn:disabled { background: #f3f4f6; color: #9ca3af; cursor: not-allowed; }
.menu-btn .icon { width: 24px; text-align: center; }
.menu-btn .label { white-space: nowrap; }

/* Unified sidebar menu */
.menu-card { padding: 0.5rem 0; position: sticky; top: 0; background: #ffffff; z-index: 10; }
.menu-section { margin-top: 0.5rem; }
.menu-section + .menu-section { margin-top: 0.25rem; padding-top: 0.25rem; border-top: 1px solid #f1f5f9; }
.menu-section-title { margin: 0.25rem 0 0.25rem; padding: 0 0.75rem; font-size: 1rem; font-weight: 400; color: #6b7280; text-align: left; }
.menu-list { list-style: none; margin: 0; padding: 0.1rem 0.25rem 0.25rem; }
.menu-item { display: flex; align-items: center; gap: 0.6rem; padding: 0.4rem 0.6rem 0.4rem 0.75rem; margin: 0.1rem 0.35rem; border-radius: 8px; cursor: pointer; color: #111827; user-select: none; }
.menu-item .icon { width: 20px; text-align: center; opacity: 0.9; }
.menu-item .text { font-size: 0.8rem; }
.menu-item:hover { background: #f3f4f6; }
.menu-item:active { background: #e5e7eb; }
.menu-item.disabled { opacity: 0.5; cursor: not-allowed; background: transparent; }
.menu-item.disabled:hover { background: transparent; }

.workspace { display: contents; }
.workspace-left { display: contents; }
.workspace-actions { display: contents; }
.card { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.03); padding: 0.75rem; width: 100%; box-sizing: border-box; }
.card-map { padding: 0; overflow: hidden; }
.card-elevation { padding: 0.75rem; overflow: visible; margin-top: 1rem; margin-bottom: 1rem; }
.map { height: 480px; width: 100%; }
.axis-toggle { display: inline-flex; gap: 0; margin: 0.25rem auto 0.25rem; border: 1px solid #e5e7eb; border-radius: 999px; overflow: hidden; background: #fff; position: relative; left: 50%; transform: translateX(-50%); max-width: 100%; }
.axis-toggle.below { margin-top: 0.5rem; }
.axis-toggle .seg { font-size: 12px; padding: 4px 10px; border: none; background: transparent; cursor: pointer; color: #374151; }
.axis-toggle .seg.left { border-right: 1px solid #e5e7eb; }
.axis-toggle .seg.active { background: #f3f4f6; color: #111827; }
.controls { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; width: 100%; box-sizing: border-box; }
.controls .meta-title { grid-column: 1 / -1; text-align: center; margin: 0 0 0.5rem 0; }
.slider-group { background: #fafafa; padding: 0.75rem; border: 1px solid #eee; border-radius: 8px; width: 100%; box-sizing: border-box; overflow: hidden; }
.slider-header { display: flex; align-items: center; justify-content: center; margin-bottom: 0.5rem; }
.badge { font-size: 12px; padding: 2px 10px; border-radius: 999px; font-weight: 600; }
.badge.start { background: var(--brand-500, #ff6600); color: #ffffff; }
.badge.end { background: var(--brand-500, #ff6600); color: #ffffff; }
.slider-row { display: grid; grid-template-columns: 40px 1fr 40px; gap: 0.5rem; align-items: center; margin-top: 0.25rem; margin-bottom: 0.5rem; }
.btn { border: none; background: #e5e7eb; border-radius: 6px; height: 32px; cursor: pointer; }
.btn:hover { background: #d1d5db; }
.range { width: 100%; }
.range-wrap { position: relative; width: 100%; }
.index-badge { position: absolute; bottom: -18px; transform: translateX(-50%); background: #111827; color: #ffffff; font-size: 11px; line-height: 1; padding: 2px 6px; border-radius: 8px; white-space: nowrap; max-width: 40px; overflow: hidden; text-overflow: ellipsis; }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.25rem 0.5rem; }
.info { display: flex; align-items: center; gap: 0.5rem; color: #374151; user-select: none; cursor: default; }
.info .icon { width: 20px; text-align: center; }
.info .value { font-variant-numeric: tabular-nums; }
.info.gps { grid-column: 1 / -1; }
.metrics-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.25rem 0.5rem; align-items: center; margin-bottom: 0.25rem; }
.metric { display: flex; align-items: center; gap: 0.4rem; color: #374151; }
.metric .icon { width: 18px; text-align: center; }
.metrics-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.25rem 0.5rem; align-items: center; margin-bottom: 0.75rem; width: 100%; box-sizing: border-box; }
.gps-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; margin: 0.25rem 0; align-items: center; }
.gps-title { display: inline-flex; align-items: center; gap: 0.35rem; color: #374151; font-weight: 500; }
.gps-title .icon { width: 18px; text-align: center; }
.gps-col { display: flex; align-items: center; gap: 0.4rem; color: #374151; }
.gps-col .label { font-size: 12px; color: #6b7280; }
.gps-col .value { font-variant-numeric: tabular-nums; }
.workspace-right { display: flex; flex-direction: column; gap: 1rem; }
.chart-wrapper { width: 100%; overflow: visible; margin-bottom: 20px; }
.chart-container { position: relative; width: 100%; overflow: visible; }
.chart { width: 100%; height: 200px; max-height: 200px; cursor: crosshair; }

/* Vertical sliders */
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
  background: #111827;
  color: #ffffff;
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
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
  pointer-events: auto;
}

.slider-btn:hover:not(:disabled) {
  background: var(--brand-primary-hover, #e65c00);
  transform: scale(1.1);
}

.slider-btn:active:not(:disabled) {
  transform: scale(0.95);
}

.slider-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  opacity: 0.5;
}

.slider-btn:disabled:hover {
  transform: none;
}
.meta { background: #ffffff; width: 100%; margin-top: 1rem; margin-bottom: 1rem; display: block; }
.meta-title { text-align: center; margin: 0 0 0.75rem 0; font-size: 1rem; font-weight: 700; color: #111827; }
.meta label { display: block; margin: 0.5rem 0 0.25rem; }
.meta input, .meta select { width: 100%; max-width: 100%; padding: 0.5rem; margin-bottom: 0.5rem; box-sizing: border-box; }
.meta .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem 1rem; align-items: start; width: 100%; box-sizing: border-box; }
.group-main-label { grid-column: 1 / -1; margin-top: 0.25rem; color: #111827; }
.tire-group { background: #fbfcfe; border: 1px solid #e5e7eb; border-radius: 10px; padding: 0.5rem; }
.tire-group-header { display: flex; align-items: center; gap: 0.4rem; color: #374151; margin: 0 0 0.5rem 0; }
.tire-group-help { margin: 0 0 0.5rem 0; font-size: 12px; color: #6b7280; }
.tire-group-header .icon { width: 18px; text-align: center; color: var(--brand-500, #ff6600); }
.tire-group-title { font-size: 0.95rem; }
.tire-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; align-items: start; }
.tire-option { display: flex; flex-direction: column; align-items: center; gap: 0.25rem; border: 1px solid #e5e7eb; border-radius: 8px; padding: 0.5rem; cursor: pointer; background: #fff; }
.tire-option input { position: absolute; opacity: 0; pointer-events: none; }
.tire-option img { width: 100%; aspect-ratio: 1 / 1; object-fit: cover; border-radius: 6px; }
.tire-option .tire-caption { font-size: 12px; color: #374151; }
.tire-option.selected { border-color: var(--brand-500, #ff6600); box-shadow: 0 0 0 2px rgba(255, 102, 0, 0.15); }
.req { color: #dc2626; }
.section-indicator { display: inline-flex; align-items: center; gap: 0.5rem; font-size: 1rem; color: #374151; padding: 0 0.25rem; margin-top: 0.5rem; }
.section-indicator .icon { width: 18px; text-align: center; }
.save-btn { display: none; }
.action-card { position: static; }
.action-title { margin: 0 0 0.75rem 0; font-size: 1rem; font-weight: 700; color: #111827; text-align: center; }
.save-side { display: flex; align-items: center; justify-content: center; gap: 6px; width: 100%; background: var(--brand-primary, var(--brand-500, #ff6600)); color: #ffffff; border: none; border-radius: 10px; padding: 10px 14px; font-size: 14px; font-weight: 500; cursor: pointer; }
.save-side:hover { background: var(--brand-primary-hover, #e65c00); }
.save-side:disabled { background: rgba(255, 102, 0, 0.1); color: #7f8286; cursor: not-allowed; border: 1px solid #e5e7eb; }
.info-dot { display: inline-flex; align-items: center; justify-content: center; width: 18px; height: 18px; border-radius: 999px; background: #f3f4f6; color: #374151; font-size: 12px; user-select: none; }
.empty { padding: 2rem; text-align: center; color: #666; }
.message { margin-top: 1rem; }

@media (max-width: 960px) {
  .workspace { grid-template-columns: 1fr; }
}

/* Sticky top navigation bar */
:root { --topbar-h: 48px; }
.topbar { position: sticky; top: 0; z-index: 9999; background: #ffffff; border-bottom: 1px solid #e5e7eb; height: var(--topbar-h, 48px); }
.topbar-inner { max-width: none; margin: 0; padding: 0 1.5rem; height: var(--topbar-h, 48px); display: flex; align-items: center; justify-content: space-between; box-sizing: border-box; position: relative; }
.topbar .logo { display: inline-flex; align-items: center; position: absolute; left: calc(50% - 500px - var(--sidebar-w, 200px)); width: var(--sidebar-w, 200px); }
.topbar .logo-img { width: 100%; height: auto; display: block; max-height: 32px; object-fit: contain; }
.topbar .nav { display: flex; align-items: center; gap: 0.75rem; }

/* Blue styling for end segment elements */
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

/* Blue styling for wet tire section */
.tire-group:nth-child(3) .tire-group-header .icon {
  color: var(--blue-500);
}

.tire-group:nth-child(3) .tire-option.selected {
  border-color: var(--blue-500);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

</style>
