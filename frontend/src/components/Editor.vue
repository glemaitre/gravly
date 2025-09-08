<template>
  <div class="editor">
    <div class="content">
    <div class="page">
      <div class="sidebar">
        <div class="sidebar-group card">
          <h3 class="group-title">Load</h3>
          <button class="menu-btn" @click="triggerFileOpen" title="Load GPX">
            <span class="icon" aria-hidden="true">📄</span>
            <span class="label">GPX</span>
          </button>
          <input ref="fileInput" type="file" accept=".gpx" @change="onFileChange" hidden />
        </div>
      </div>
      <section v-if="loaded" class="main-col">
        <div class="card card-elevation">
          <div class="axis-toggle">
            <button type="button" class="seg left" :class="{ active: xMode === 'distance' }" @click="xMode = 'distance'">Distance</button>
            <button type="button" class="seg right" :class="{ active: xMode === 'time' }" @click="xMode = 'time'">Time</button>
          </div>
          <canvas ref="chartCanvas" class="chart"></canvas>
        </div>
        <div class="card card-map">
          <div id="map" class="map"></div>
        </div>
        <div class="card controls">
          <h3 class="meta-title">Segment selector</h3>
          <div class="slider-group">
            <div class="slider-header">
              <span class="badge start">Start of segment</span>
            </div>
            <div class="slider-row">
              <button type="button" class="btn" @click="startIndex = Math.max(0, startIndex - 1)">−</button>
              <input class="range" type="range" :min="0" :max="Math.max(1, endIndex - 1)" :value="startIndex" @input="onStartInput($event)" />
              <button type="button" class="btn" @click="startIndex = Math.min(endIndex - 1, startIndex + 1)">+</button>
            </div>
            <div class="info-grid">
              <div class="info" title="Index">
                <span class="icon">#️⃣</span>
                <span class="value">{{ startIndex }}</span>
              </div>
              <div class="info" title="Elapsed time from start">
                <span class="icon">⏱️</span>
                <span class="value">{{ formatElapsed(startIndex) }}</span>
              </div>
              <div class="info" title="GPS location">
                <span class="icon">📍</span>
                <span class="value">{{ formatLatLon(pointAt(startIndex)) }}</span>
              </div>
              <div class="info" title="Distance (km)">
                <span class="icon">📏</span>
                <span class="value">{{ formatKm(distanceAt(startIndex)) }}</span>
              </div>
              <div class="info" title="Elevation (m)">
                <span class="icon">⛰️</span>
                <span class="value">{{ formatElevation(pointAt(startIndex)?.ele) }}</span>
              </div>
            </div>
          </div>
          <div class="slider-group">
            <div class="slider-header">
              <span class="badge end">End of segment</span>
            </div>
            <div class="slider-row">
              <button type="button" class="btn" @click="endIndex = Math.max(startIndex + 1, endIndex - 1)">−</button>
              <input class="range" type="range" :min="Math.min(points.length - 1, startIndex + 1)" :max="points.length - 1" :value="endIndex" @input="onEndInput($event)" />
              <button type="button" class="btn" @click="endIndex = Math.min(points.length - 1, endIndex + 1)">+</button>
            </div>
            <div class="info-grid">
              <div class="info" title="Index">
                <span class="icon">#️⃣</span>
                <span class="value">{{ endIndex }}</span>
              </div>
              <div class="info" title="Elapsed time from start">
                <span class="icon">⏱️</span>
                <span class="value">{{ formatElapsed(endIndex) }}</span>
              </div>
              <div class="info" title="GPS location">
                <span class="icon">📍</span>
                <span class="value">{{ formatLatLon(pointAt(endIndex)) }}</span>
              </div>
              <div class="info" title="Distance (km)">
                <span class="icon">📏</span>
                <span class="value">{{ formatKm(distanceAt(endIndex)) }}</span>
              </div>
              <div class="info" title="Elevation (m)">
                <span class="icon">⛰️</span>
                <span class="value">{{ formatElevation(pointAt(endIndex)?.ele) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Segment information under selector -->
        <form class="card meta" @submit.prevent="onSubmit">
          <h3 class="meta-title">Segment information</h3>
          <div>
            <label for="name">Segment name <span class="req">*</span></label>
            <input id="name" v-model="name" type="text" required />
          </div>

          <div class="grid">
            <div>
              <label for="tireDry">Tire (dry)</label>
              <select id="tireDry" v-model="tireDry" required>
                <option value="slick">slick</option>
                <option value="semi-slick">semi-slick</option>
                <option value="knobs">knobs</option>
              </select>
            </div>
            <div>
              <label for="tireWet">Tire (wet)</label>
              <select id="tireWet" v-model="tireWet" required>
                <option value="slick">slick</option>
                <option value="semi-slick">semi-slick</option>
                <option value="knobs">knobs</option>
              </select>
            </div>
          </div>
          <!-- Save moved to right sidebar button -->
        </form>
      </section>
      <aside v-if="loaded" class="actions-col">
        <div class="card action-card">
          <h3 class="action-title">Actions</h3>
          <button class="save-side" :disabled="submitting || !name || !loaded" @click="onSubmit">
            <span>Save segment</span>
            <span v-if="!name" class="info-dot" title="Enter a segment name to enable saving">i</span>
          </button>
        </div>
      </aside>
    </div>

    <div v-if="!loaded" class="empty">
      <p>Use File → Load GPX to begin.</p>
    </div>

    <p v-if="message" class="message">{{ message }}</p>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, onUnmounted, ref, watch, nextTick } from 'vue'
import L, { Map as LeafletMap, Polyline } from 'leaflet'
import { Chart, LineController, LineElement, PointElement, LinearScale, Title, CategoryScale } from 'chart.js'

Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Title)

type Tire = 'slick' | 'semi-slick' | 'knobs'

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

let map: LeafletMap | null = null
let fullLine: Polyline | null = null
let selectedLine: Polyline | null = null
let baseLayer: L.TileLayer | null = null

const chartCanvas = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null
const smoothedElevations = ref<number[]>([])

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
  selectedLine = L.polyline(segLatLngs, { color: '#1e90ff', weight: 5 })
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
          borderColor: '#1e90ff',
          borderWidth: 2,
          pointRadius: 0,
          fill: false,
          parsing: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      scales: {
        x: { type: 'linear', display: true, title: { display: true, text: xAxisTitle() }, min: getX(startIndex.value), max: getX(endIndex.value), ticks: { callback: (v: any) => formatXTick(Number(v)) } },
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
    chart.options.scales.x.title.text = xAxisTitle()
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
  chart.options.scales.x.title.text = xAxisTitle()
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

<style scoped>
.editor { display: flex; min-height: 100vh; background: #f8fafc; }
.content { flex: 1 1 auto; padding: 1rem 1.5rem; }
.page { --sidebar-w: 200px; display: grid; grid-template-columns: var(--sidebar-w) 1fr var(--sidebar-w); gap: 1.25rem; align-items: start; max-width: 1200px; margin: 0 auto; }
.main-col { display: flex; flex-direction: column; gap: 0.75rem; }
.actions-col { display: flex; flex-direction: column; gap: 0.75rem; position: sticky; top: 12px; align-self: start; height: fit-content; width: var(--sidebar-w); }

.sidebar { width: var(--sidebar-w); background: transparent; border-right: none; padding: 0; margin: 0; box-sizing: border-box; display: flex; flex-direction: column; gap: 0.75rem; position: sticky; top: 12px; align-self: start; height: fit-content; }
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

.workspace { display: contents; }
.workspace-left { display: contents; }
.workspace-actions { display: contents; }
.card { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.03); padding: 0.75rem; width: 100%; box-sizing: border-box; }
.card-map { padding: 0; overflow: hidden; }
.card-elevation { padding: 0.75rem; }
.map { height: 480px; width: 100%; }
.axis-toggle { display: inline-flex; gap: 0; margin: 0.25rem auto 0.25rem; border: 1px solid #e5e7eb; border-radius: 999px; overflow: hidden; background: #fff; position: relative; left: 50%; transform: translateX(-50%); }
.axis-toggle .seg { font-size: 12px; padding: 4px 10px; border: none; background: transparent; cursor: pointer; color: #374151; }
.axis-toggle .seg.left { border-right: 1px solid #e5e7eb; }
.axis-toggle .seg.active { background: #f3f4f6; color: #111827; }
.controls { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.controls .meta-title { grid-column: 1 / -1; text-align: center; margin: 0 0 0.5rem 0; }
.slider-group { background: #fafafa; padding: 0.75rem; border: 1px solid #eee; border-radius: 8px; }
.slider-header { display: flex; align-items: center; justify-content: center; margin-bottom: 0.5rem; }
.badge { font-size: 12px; padding: 2px 10px; border-radius: 999px; font-weight: 600; }
.badge.start { background: #1e90ff; color: #ffffff; }
.badge.end { background: #f59e0b; color: #ffffff; }
.slider-row { display: grid; grid-template-columns: 40px 1fr 40px; gap: 0.5rem; align-items: center; margin-bottom: 0.5rem; }
.btn { border: none; background: #e5e7eb; border-radius: 6px; height: 32px; cursor: pointer; }
.btn:hover { background: #d1d5db; }
.range { width: 100%; }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.25rem 0.5rem; }
.info { display: flex; align-items: center; gap: 0.5rem; color: #374151; user-select: none; cursor: default; }
.info .icon { width: 20px; text-align: center; }
.info .value { font-variant-numeric: tabular-nums; }
.workspace-right { display: flex; flex-direction: column; gap: 1rem; }
.chart { width: 100%; height: 200px; max-height: 200px; }
.meta { background: #ffffff; width: 100%; margin: 0; display: block; }
.meta-title { text-align: center; margin: 0 0 0.75rem 0; font-size: 1rem; font-weight: 700; color: #111827; }
.meta label { display: block; margin: 0.5rem 0 0.25rem; }
.meta input, .meta select { width: 100%; max-width: 100%; padding: 0.5rem; margin-bottom: 0.5rem; box-sizing: border-box; }
.req { color: #dc2626; }
.save-btn { display: none; }
.action-card { position: static; }
.action-title { margin: 0 0 0.75rem 0; font-size: 1rem; font-weight: 700; color: #111827; text-align: center; }
.save-side { display: flex; align-items: center; justify-content: center; gap: 6px; width: 100%; background: #1e90ff; color: #ffffff; border: none; border-radius: 10px; padding: 10px 14px; font-size: 14px; font-weight: 500; cursor: pointer; }
.save-side:hover { background: #1b82e6; }
.save-side:disabled { background: rgba(30, 144, 255, 0.1); color: #7f8286; cursor: not-allowed; border: 1px solid #e5e7eb; }
.info-dot { display: inline-flex; align-items: center; justify-content: center; width: 18px; height: 18px; border-radius: 999px; background: #f3f4f6; color: #374151; font-size: 12px; user-select: none; }
.empty { padding: 2rem; text-align: center; color: #666; }
.message { margin-top: 1rem; }

@media (max-width: 960px) {
  .workspace { grid-template-columns: 1fr; }
}
</style>
