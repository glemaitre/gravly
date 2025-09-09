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
    <div class="content">
    <div class="page" :style="{ '--section-offset': sectionOffset + 'px' } as any">
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
      <section v-if="loaded" class="main-col">
        <div class="section-indicator" ref="firstSectionIndicator">
          <span class="icon" aria-hidden="true"><i class="fa-solid fa-compass"></i></span>
          <span class="label">Segment selector</span>
        </div>
        <div class="card controls" ref="controlsCard">
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
            <div class="slider-row">
              <button type="button" class="btn" @click="startIndex = Math.max(0, startIndex - 1)">−</button>
              <div class="range-wrap">
                <input class="range" type="range" :min="startMin" :max="startMax" :value="startIndex" @input="onStartInput($event)" />
                <div class="index-badge" :style="{ left: startPercent + '%' }" title="Index">{{ startIndex }}</div>
              </div>
              <button type="button" class="btn" @click="startIndex = Math.min(endIndex - 1, startIndex + 1)">+</button>
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
            <div class="slider-row">
              <button type="button" class="btn" @click="endIndex = Math.max(startIndex + 1, endIndex - 1)">−</button>
              <div class="range-wrap">
                <input class="range" type="range" :min="endMin" :max="endMax" :value="endIndex" @input="onEndInput($event)" />
                <div class="index-badge" :style="{ left: endPercent + '%' }" title="Index">{{ endIndex }}</div>
              </div>
              <button type="button" class="btn" @click="endIndex = Math.min(points.length - 1, endIndex + 1)">+</button>
            </div>
          </div>
        </div>
        <div class="card card-map">
          <div id="map" class="map"></div>
        </div>
        <div class="card card-elevation">
          <canvas ref="chartCanvas" class="chart"></canvas>
          <div class="axis-toggle below">
            <button type="button" class="seg left" :class="{ active: xMode === 'distance' }" @click="xMode = 'distance'">Distance (km)</button>
            <button type="button" class="seg right" :class="{ active: xMode === 'time' }" @click="xMode = 'time'">Time (hh:mm:ss)</button>
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
      </section>

    </div>

    <div v-if="!loaded" class="empty">
      <p>Use File → Load GPX to begin.</p>
    </div>

    <p v-if="message" class="message">{{ message }}</p>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, onUnmounted, ref, watch, nextTick, computed } from 'vue'
import logoUrl from '../assets/images/logo.svg'
import L from 'leaflet'
import { Chart, LineController, LineElement, PointElement, LinearScale, Title, CategoryScale, Filler } from 'chart.js'
import tireSlickUrl from '../assets/images/slick.png'
import tireSemiSlickUrl from '../assets/images/semi-slick.png'
import tireKnobsUrl from '../assets/images/ext.png'

Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Title, Filler)

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

// Constant offset so the sidebar aligns with the top of the controls card
const sectionOffset = ref(0)
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
    // Recompute layout-dependent offsets after controls render
    try { (window as any).__editorRecomputeSectionOffset?.() } catch {}
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
  chart?.destroy()
  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Elevation (m)',
          data: data.map(d => ({ x: d.x, y: d.y })),
          borderColor: getComputedStyle(document.documentElement).getPropertyValue('--brand-500').trim() || '#ff6600',
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 5,
          backgroundColor: 'rgba(255, 102, 0, 0.12)',
          fill: 'start',
          tension: 0.1,
          parsing: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      scales: {
        x: { type: 'linear', display: true, title: { display: false }, min: getX(startIndex.value), max: getX(endIndex.value), ticks: { callback: (v: any) => formatXTick(Number(v)) } },
        y: { display: true, title: { display: true, text: 'Elevation (m)' } }
      },
      plugins: { legend: { display: false } }
    }
  })
}

function getX(i: number): number {
  return xMode.value === 'distance' ? (cumulativeKm.value[i] ?? 0) : (cumulativeSec.value[i] ?? 0)
}

function buildXYData(): { x: number, y: number }[] {
  return points.value.map((p, i) => ({ x: getX(i), y: smoothedElevations.value[i] ?? p.ele }))
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
  // Update selected dataset in chart
  if (chart) {
    const data = buildXYData()
    // @ts-ignore
    chart.data.datasets[0].data = data.map(d => ({ x: d.x, y: d.y }))
    // @ts-ignore
    chart.options.scales.x.min = getX(startIndex.value)
    // @ts-ignore
    chart.options.scales.x.max = getX(endIndex.value)
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
  const data = buildXYData()
  // @ts-ignore
  chart.data.datasets[0].data = data.map(d => ({ x: d.x, y: d.y }))
  // @ts-ignore
  chart.options.scales.x.ticks.callback = (v) => formatXTick(Number(v))
  // @ts-ignore
  chart.options.scales.x.min = getX(startIndex.value)
  // @ts-ignore
  chart.options.scales.x.max = getX(endIndex.value)
  chart.update()
})

watch(sidebarCollapsed, () => {
  if (map) {
    setTimeout(() => map!.invalidateSize(), 220)
  }
})

// Ensure the sidebar offset recomputes when the loaded state toggles and layout changes
watch(loaded, async () => {
  await nextTick()
  try { (window as any).__editorRecomputeSectionOffset?.() } catch {}
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

  // Measure the controls card and set a constant sidebar offset matching its initial gap below the topbar
  const recomputeSectionOffset = () => {
    const el = controlsCard.value
    const topbarAndGap = (Number(getComputedStyle(document.documentElement).getPropertyValue('--topbar-h').replace('px','')) || 48) + 12
    if (!el) { sectionOffset.value = 0; return }
    const rect = el.getBoundingClientRect()
    sectionOffset.value = Math.max(0, Math.round(rect.top - topbarAndGap))
  }
  // Initial compute after layout
  setTimeout(recomputeSectionOffset, 0)
  window.addEventListener('resize', recomputeSectionOffset)
  ;(window as any).__editorRecomputeSectionOffset = recomputeSectionOffset
})

onUnmounted(() => {
  const onResize = (window as any).__editorOnResize
  if (onResize) window.removeEventListener('resize', onResize)
  const recompute = (window as any).__editorRecomputeSectionOffset
  if (recompute) {
    window.removeEventListener('resize', recompute)
  }
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
}
</style>

<style scoped>
.editor { display: flex; min-height: 100vh; background: #f8fafc; }
.content { flex: 1 1 auto; padding: 1rem 1.5rem; }
.page { --sidebar-w: 200px; display: grid; grid-template-columns: var(--sidebar-w) 1fr; gap: 1.25rem; align-items: start; max-width: 1200px; margin: 0 auto; }
.main-col { display: flex; flex-direction: column; gap: 0.75rem; }
.actions-col { display: flex; flex-direction: column; gap: 0.75rem; position: sticky; top: 12px; align-self: start; height: fit-content; width: var(--sidebar-w); }

.sidebar { width: var(--sidebar-w); background: transparent; border-right: none; padding: 0; margin: 0; box-sizing: border-box; position: sticky; top: calc(var(--topbar-h, 48px) + 12px + var(--section-offset, 0px)); align-self: start; }
.sidebar-scroll { display: flex; flex-direction: column; gap: 0.75rem; max-height: calc(100vh - var(--topbar-h, 48px) - 24px - var(--section-offset, 0px)); overflow: auto; padding-right: 2px; }
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
.menu-card { padding: 0.5rem 0; }
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
.card-elevation { padding: 0.75rem; }
.map { height: 480px; width: 100%; }
.axis-toggle { display: inline-flex; gap: 0; margin: 0.25rem auto 0.25rem; border: 1px solid #e5e7eb; border-radius: 999px; overflow: hidden; background: #fff; position: relative; left: 50%; transform: translateX(-50%); }
.axis-toggle.below { margin-top: 0.5rem; }
.axis-toggle .seg { font-size: 12px; padding: 4px 10px; border: none; background: transparent; cursor: pointer; color: #374151; }
.axis-toggle .seg.left { border-right: 1px solid #e5e7eb; }
.axis-toggle .seg.active { background: #f3f4f6; color: #111827; }
.controls { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.controls .meta-title { grid-column: 1 / -1; text-align: center; margin: 0 0 0.5rem 0; }
.slider-group { background: #fafafa; padding: 0.75rem; border: 1px solid #eee; border-radius: 8px; }
.slider-header { display: flex; align-items: center; justify-content: center; margin-bottom: 0.5rem; }
.badge { font-size: 12px; padding: 2px 10px; border-radius: 999px; font-weight: 600; }
.badge.start { background: var(--brand-500, #ff6600); color: #ffffff; }
.badge.end { background: var(--brand-500, #ff6600); color: #ffffff; }
.slider-row { display: grid; grid-template-columns: 40px 1fr 40px; gap: 0.5rem; align-items: center; margin-top: 0.25rem; margin-bottom: 0.5rem; }
.btn { border: none; background: #e5e7eb; border-radius: 6px; height: 32px; cursor: pointer; }
.btn:hover { background: #d1d5db; }
.range { width: 100%; }
.range-wrap { position: relative; width: 100%; }
.index-badge { position: absolute; bottom: -18px; transform: translateX(-50%); background: #111827; color: #ffffff; font-size: 11px; line-height: 1; padding: 2px 6px; border-radius: 8px; white-space: nowrap; }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.25rem 0.5rem; }
.info { display: flex; align-items: center; gap: 0.5rem; color: #374151; user-select: none; cursor: default; }
.info .icon { width: 20px; text-align: center; }
.info .value { font-variant-numeric: tabular-nums; }
.info.gps { grid-column: 1 / -1; }
.metrics-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.25rem 0.5rem; align-items: center; margin-bottom: 0.25rem; }
.metric { display: flex; align-items: center; gap: 0.4rem; color: #374151; }
.metric .icon { width: 18px; text-align: center; }
.metrics-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.25rem 0.5rem; align-items: center; margin-bottom: 0.75rem; }
.gps-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; margin: 0.25rem 0; align-items: center; }
.gps-title { display: inline-flex; align-items: center; gap: 0.35rem; color: #374151; font-weight: 500; }
.gps-title .icon { width: 18px; text-align: center; }
.gps-col { display: flex; align-items: center; gap: 0.4rem; color: #374151; }
.gps-col .label { font-size: 12px; color: #6b7280; }
.gps-col .value { font-variant-numeric: tabular-nums; }
.workspace-right { display: flex; flex-direction: column; gap: 1rem; }
.chart { width: 100%; height: 200px; max-height: 200px; }
.meta { background: #ffffff; width: 100%; margin: 0; display: block; }
.meta-title { text-align: center; margin: 0 0 0.75rem 0; font-size: 1rem; font-weight: 700; color: #111827; }
.meta label { display: block; margin: 0.5rem 0 0.25rem; }
.meta input, .meta select { width: 100%; max-width: 100%; padding: 0.5rem; margin-bottom: 0.5rem; box-sizing: border-box; }
.meta .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem 1rem; align-items: start; }
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
.topbar { position: sticky; top: 0; z-index: 1000; background: #ffffff; border-bottom: 1px solid #e5e7eb; height: var(--topbar-h, 48px); }
.topbar-inner { max-width: 1200px; margin: 0 auto; padding: 0 1.5rem; height: var(--topbar-h, 48px); display: flex; align-items: center; justify-content: space-between; box-sizing: border-box; }
.topbar .logo { display: inline-flex; align-items: center; }
.topbar .logo-img { height: 28px; display: block; }
.topbar .nav { display: flex; align-items: center; gap: 0.75rem; }

/* Ensure sticky sidebars account for topbar height */
.sidebar { top: calc(var(--topbar-h, 48px) + 12px + var(--section-offset, 0px)); }
</style>
