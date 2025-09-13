<template>
  <header class="topbar">
    <div class="topbar-inner">
      <div class="nav-left">
        <div class="logo">
          <img :src="logoUrl" alt="Cycling Segments" class="logo-img" />
        </div>
      </div>
      <nav class="nav">
        <div class="language-dropdown" ref="languageDropdown">
          <button
            class="language-dropdown-trigger navbar-trigger"
            @click="toggleLanguageDropdown"
            :class="{ active: languageDropdownOpen }"
          >
            <span class="language-flag">{{ languageOptions[currentLanguage].flag }}</span>
            <span class="language-name">{{ languageOptions[currentLanguage].name }}</span>
            <span class="dropdown-arrow">
              <i class="fa-solid fa-chevron-down" :class="{ rotated: languageDropdownOpen }"></i>
            </span>
          </button>
          <div class="language-dropdown-menu navbar-menu" :class="{ open: languageDropdownOpen }">
            <button
              v-for="(option, lang) in languageOptions"
              :key="lang"
              class="language-option"
              :class="{ active: currentLanguage === lang }"
              @click="(e) => { e.stopPropagation(); changeLanguage(lang as MessageLanguages) }"
            >
              <span class="language-flag">{{ option.flag }}</span>
              <span class="language-name">{{ option.name }}</span>
              <span v-if="currentLanguage === lang" class="checkmark">
                <i class="fa-solid fa-check"></i>
              </span>
            </button>
          </div>
        </div>
      </nav>
    </div>
  </header>
  <div class="editor">
    <div class="sidebar">
      <div class="sidebar-scroll">
        <div class="card menu-card">
          <div class="menu-section">
            <div class="menu-section-title">{{ t('menu.import') }}</div>
            <ul class="menu-list">
              <li class="menu-item" @click="triggerFileOpen" :title="t('tooltip.loadGpxFile')" role="button">
                <span class="icon" aria-hidden="true"><i class="fa-solid fa-file-lines"></i></span>
                <span class="text">{{ t('menu.gpxFile') }}</span>
              </li>
            </ul>
            <input ref="fileInput" type="file" accept=".gpx" @change="onFileChange" hidden />
          </div>

          <!-- Upload Progress Bar in Menu -->
          <div v-if="isUploading" class="menu-section upload-progress-section">
            <div class="upload-progress-container">
              <div class="upload-progress-bar">
                <div
                  class="upload-progress-fill"
                  :style="{ width: uploadProgress + '%' }"
                ></div>
              </div>
              <div class="upload-progress-text">
                {{ t('message.uploading') }} {{ Math.round(uploadProgress) }}%
              </div>
            </div>
          </div>

          <div class="menu-section">
            <div class="menu-section-title">{{ t('menu.segments') }}</div>
            <ul class="menu-list">
              <li
                class="menu-item action"
                :class="{ disabled: isSaveDisabled }"
                :aria-disabled="isSaveDisabled"
                :title="isSaveDisabled ? saveDisabledTitle : t('menu.saveInDb')"
                @click="!isSaveDisabled && onSubmit()"
              >
                <span class="icon" aria-hidden="true"><i class="fa-solid fa-database"></i></span>
                <span class="text">{{ t('menu.saveInDb') }}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

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
                    >-</button>
                    <button
                      class="slider-btn slider-btn-plus"
                      @click="moveSlider('start', 1)"
                      :disabled="startIndex >= endIndex - 1"
                      :title="t('tooltip.moveStartForward')"
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
                      :title="t('tooltip.moveEndBack')"
                    >-</button>
                    <button
                      class="slider-btn slider-btn-plus"
                      @click="moveSlider('end', 1)"
                      :disabled="endIndex >= points.length - 1"
                      :title="t('tooltip.moveEndForward')"
                    >+</button>
                  </div>
                </div>
              </div>
            </div>
            <div class="axis-toggle below">
              <button type="button" class="seg left" :class="{ active: xMode === 'distance' }" @click="xMode = 'distance'">{{ t('chart.distance') }}</button>
              <button type="button" class="seg right" :class="{ active: xMode === 'time' }" @click="xMode = 'time'">{{ t('chart.time') }}</button>
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
                    <span class="value">{{ formatElevation(pointAt(startIndex)?.ele) }}</span>
                  </div>
                  <div class="gps-title" :title="t('tooltip.gpsLocation')"><span class="icon"><i class="fa-solid fa-location-dot"></i></span><span class="text">{{ t('chart.gps') }}</span></div>
                  <div class="gps-col"><span class="label">{{ t('gps.lat') }}</span><span class="value">{{ pointAt(startIndex)?.lat?.toFixed(5) ?? '-' }}</span></div>
                  <div class="gps-col"><span class="label">{{ t('gps.lon') }}</span><span class="value">{{ pointAt(startIndex)?.lon?.toFixed(5) ?? '-' }}</span></div>
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
                    <span class="value">{{ formatElevation(pointAt(endIndex)?.ele) }}</span>
                  </div>
                  <div class="gps-title" :title="t('tooltip.gpsLocation')"><span class="icon"><i class="fa-solid fa-location-dot"></i></span><span class="text">{{ t('chart.gps') }}</span></div>
                  <div class="gps-col"><span class="label">{{ t('gps.lat') }}</span><span class="value">{{ pointAt(endIndex)?.lat?.toFixed(5) ?? '-' }}</span></div>
                  <div class="gps-col"><span class="label">{{ t('gps.lon') }}</span><span class="value">{{ pointAt(endIndex)?.lon?.toFixed(5) ?? '-' }}</span></div>
                </div>
              </div>
            </div>
          </div>

          <div class="section-indicator">
            <span class="icon" aria-hidden="true"><i class="fa-solid fa-circle-info"></i></span>
            <span class="label">{{ t('form.segmentInfo') }}</span>
          </div>
          <form class="card meta" @submit.prevent="onSubmit">
            <div>
              <label for="name">{{ t('form.segmentName') }} <span class="req">{{ t('required') }}</span></label>
              <input id="name" v-model="name" type="text" required />
            </div>

            <!-- Trail Conditions Card -->
            <div class="trail-conditions-card">
              <div class="trail-conditions-header">
                <span class="icon" aria-hidden="true"><i class="fa-solid fa-mountain"></i></span>
                <span class="trail-conditions-title">{{ t('form.trailConditions') }}</span>
              </div>

              <!-- Difficulty Level -->
              <div class="trail-subsection">
                <div class="subsection-header">
                  <span class="icon" aria-hidden="true"><i class="fa-solid fa-signal"></i></span>
                  <span class="subsection-title">{{ t('form.difficultyLevel') }}</span>
                </div>

                <div class="difficulty-container">
                  <div class="difficulty-slider-container">
                    <input
                      type="range"
                      min="1"
                      max="5"
                      v-model="trailConditions.difficulty_level"
                      class="difficulty-slider"
                      :style="{ '--slider-progress': difficultyProgress + '%' }"
                      :aria-label="t('form.difficultyLevel')"
                    />
                    <div class="difficulty-marks">
                      <div
                        v-for="i in 5"
                        :key="i"
                        class="difficulty-mark"
                        :class="{ active: trailConditions.difficulty_level >= i }"
                      >
                        <span class="difficulty-number">{{ i }}</span>
                        <span class="difficulty-text">{{ t(`difficulty.level${i}`) }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Surface Type Selection -->
              <div class="trail-subsection">
                <div class="subsection-header">
                  <span class="icon" aria-hidden="true"><i class="fa-solid fa-road"></i></span>
                  <span class="subsection-title">{{ t('form.surfaceType') }}</span>
                </div>

                <div class="surface-options">
                  <label
                    v-for="(image, surfaceType) in surfaceImages"
                    :key="surfaceType"
                    class="surface-option"
                    :class="{ selected: trailConditions.surface_type === surfaceType }"
                  >
                    <input
                      type="radio"
                      name="surfaceType"
                      :value="surfaceType"
                      v-model="trailConditions.surface_type"
                    />
                    <img :src="image" :alt="t(`surface.${surfaceType}`)" />
                    <span class="surface-caption">{{ t(`surface.${surfaceType}`) }}</span>
                  </label>
                </div>
              </div>

              <!-- Tire Selection -->
              <div class="trail-subsection">
                <div class="subsection-header">
                  <span class="icon" aria-hidden="true"><i class="fa-solid fa-circle-dot"></i></span>
                  <span class="subsection-title">{{ t('form.tire') }}</span>
                </div>

                <div class="tire-groups">
                  <div class="tire-group">
                    <div class="tire-group-header">
                      <span class="icon" aria-hidden="true"><i class="fa-solid fa-sun"></i></span>
                      <span class="tire-group-title">{{ t('tire.dry') }}</span>
                    </div>
                    <p class="tire-group-help">{{ t('tire.dryHelp') }}</p>
                    <div class="tire-row" role="radiogroup" :aria-label="t('tire.dry')">
                      <label class="tire-option" :class="{ selected: trailConditions.tire_dry === 'slick' }">
                        <input type="radio" name="tireDry" value="slick" v-model="trailConditions.tire_dry" />
                        <img :src="tireImages.slick" :alt="t('tire.slick')" />
                        <span class="tire-caption">{{ t('tire.slick') }}</span>
                      </label>
                      <label class="tire-option" :class="{ selected: trailConditions.tire_dry === 'semi-slick' }">
                        <input type="radio" name="tireDry" value="semi-slick" v-model="trailConditions.tire_dry" />
                        <img :src="tireImages.semiSlick" :alt="t('tire.semiSlick')" />
                        <span class="tire-caption">{{ t('tire.semiSlick') }}</span>
                      </label>
                      <label class="tire-option" :class="{ selected: trailConditions.tire_dry === 'knobs' }">
                        <input type="radio" name="tireDry" value="knobs" v-model="trailConditions.tire_dry" />
                        <img :src="tireImages.knobs" :alt="t('tire.knobs')" />
                        <span class="tire-caption">{{ t('tire.knobs') }}</span>
                      </label>
                    </div>
                  </div>
                  <div class="tire-group">
                    <div class="tire-group-header">
                      <span class="icon" aria-hidden="true"><i class="fa-solid fa-cloud-rain"></i></span>
                      <span class="tire-group-title">{{ t('tire.wet') }}</span>
                    </div>
                    <p class="tire-group-help">{{ t('tire.wetHelp') }}</p>
                    <div class="tire-row" role="radiogroup" :aria-label="t('tire.wet')">
                      <label class="tire-option" :class="{ selected: trailConditions.tire_wet === 'slick' }">
                        <input type="radio" name="tireWet" value="slick" v-model="trailConditions.tire_wet" />
                        <img :src="tireImages.slick" :alt="t('tire.slick')" />
                        <span class="tire-caption">{{ t('tire.slick') }}</span>
                      </label>
                      <label class="tire-option" :class="{ selected: trailConditions.tire_wet === 'semi-slick' }">
                        <input type="radio" name="tireWet" value="semi-slick" v-model="trailConditions.tire_wet" />
                        <img :src="tireImages.semiSlick" :alt="t('tire.semiSlick')" />
                        <span class="tire-caption">{{ t('tire.semiSlick') }}</span>
                      </label>
                      <label class="tire-option" :class="{ selected: trailConditions.tire_wet === 'knobs' }">
                        <input type="radio" name="tireWet" value="knobs" v-model="trailConditions.tire_wet" />
                        <img :src="tireImages.knobs" :alt="t('tire.knobs')" />
                        <span class="tire-caption">{{ t('tire.knobs') }}</span>
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Media Section -->
            <div class="media-section">
              <div class="media-header">
                <span class="icon" aria-hidden="true"><i class="fa-solid fa-photo-film"></i></span>
                <span class="media-title">{{ t('form.media') }}</span>
              </div>

              <!-- Video Links Section -->
              <div class="media-field">
                <label>{{ t('form.videoLinks') }}</label>
                <div class="video-links-container">
                  <div
                    v-for="(video, index) in commentary.video_links"
                    :key="video.id"
                    class="video-link-item"
                  >
                    <div class="video-link-content">
                      <div class="video-platform">
                        <i :class="getVideoIcon(video.platform)"></i>
                        <span class="platform-name">{{ getPlatformName(video.platform) }}</span>
                      </div>
                      <input
                        v-model="video.url"
                        type="url"
                        :placeholder="t('form.videoUrlPlaceholder')"
                        class="video-url-input"
                        @input="validateVideoUrl(video)"
                      />
                      <input
                        v-model="video.title"
                        type="text"
                        :placeholder="t('form.videoTitlePlaceholder')"
                        class="video-title-input"
                      />
                    </div>
                    <button
                      type="button"
                      @click="removeVideoLink(index)"
                      class="remove-video-btn"
                      :title="t('form.removeVideo')"
                    >
                      <i class="fa-solid fa-trash"></i>
                    </button>
                  </div>
                  <button
                    type="button"
                    @click="addVideoLink"
                    class="add-video-btn"
                  >
                    <i class="fa-solid fa-plus"></i>
                    <span>{{ t('form.addVideoLink') }}</span>
                  </button>
                </div>
              </div>

              <!-- Image Upload Section -->
              <div class="media-field">
                <label>{{ t('form.images') }}</label>
                <div class="image-upload-container">
                  <div
                    v-for="(image, index) in commentary.images"
                    :key="image.id"
                    class="image-item"
                  >
                    <div class="image-preview">
                      <img :src="image.preview" :alt="image.caption || t('form.imageAlt')" />
                      <div class="image-overlay">
                        <button
                          type="button"
                          @click="removeImage(index)"
                          class="remove-image-btn"
                          :title="t('form.removeImage')"
                        >
                          <i class="fa-solid fa-trash"></i>
                        </button>
                      </div>
                    </div>
                    <input
                      v-model="image.caption"
                      type="text"
                      :placeholder="t('form.imageCaptionPlaceholder')"
                      class="image-caption-input"
                    />
                  </div>
                  <div
                    class="image-upload-area"
                    :class="{ 'drag-over': isDragOver }"
                    @click="triggerImageUpload"
                    @dragover.prevent="handleDragOver"
                    @dragleave.prevent="handleDragLeave"
                    @drop.prevent="handleImageDrop"
                  >
                    <div class="upload-content">
                      <i class="fa-solid fa-cloud-upload-alt upload-icon"></i>
                      <span class="upload-text">{{ t('form.uploadImages') }}</span>
                      <span class="upload-hint">{{ t('form.uploadHint') }}</span>
                    </div>
                  </div>
                </div>
                <input
                  ref="imageInput"
                  type="file"
                  accept="image/*"
                  multiple
                  @change="handleImageSelect"
                  hidden
                />
              </div>
            </div>

            <!-- Comments Section -->
            <div class="commentary-section">
              <div class="commentary-header">
                <span class="icon" aria-hidden="true"><i class="fa-solid fa-comment-dots"></i></span>
                <span class="commentary-title">{{ t('form.comments') }}</span>
              </div>

              <!-- Free Text Commentary -->
              <div class="commentary-field">
                <label for="commentary-text">{{ t('form.commentaryText') }}</label>
                <textarea
                  id="commentary-text"
                  v-model="commentary.text"
                  :placeholder="t('form.commentaryPlaceholder')"
                  rows="4"
                  class="commentary-textarea"
                ></textarea>
              </div>
            </div>
          </form>
        </div>

        <div v-if="!loaded" class="empty">
          <p>{{ t('message.useFileLoad') }}</p>
        </div>
        </div>
      </div>
    </div>

    <!-- Regular Messages -->
    <p v-if="message" class="message">{{ message }}</p>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, onUnmounted, ref, watch, nextTick, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { setLanguage, type MessageLanguages } from '../i18n'
import logoUrl from '../assets/images/logo.svg'
import L from 'leaflet'
import { Chart, LineController, LineElement, PointElement, LinearScale, Title, CategoryScale, Filler, Tooltip } from 'chart.js'
import annotationPlugin from 'chartjs-plugin-annotation'
import tireSlickUrl from '../assets/images/slick.png'
import tireSemiSlickUrl from '../assets/images/semi-slick.png'
import tireKnobsUrl from '../assets/images/ext.png'
import bigStoneRoadUrl from '../assets/images/big-stone-road.jpeg'
import brokenPavedRoadUrl from '../assets/images/broken-paved-road.jpeg'
import dirtyRoadUrl from '../assets/images/dirty-road.jpeg'
import fieldTrailUrl from '../assets/images/field-trail.jpeg'
import forestTrailUrl from '../assets/images/forest-trail.jpeg'
import smallStoneRoadUrl from '../assets/images/small-stone-road.jpeg'
import type { Commentary, VideoLink, CommentaryImage, TrailConditions } from '../types'

Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Title, Filler, Tooltip, annotationPlugin)

type Tire = 'slick' | 'semi-slick' | 'knobs'

const tireImages = { slick: tireSlickUrl, semiSlick: tireSemiSlickUrl, knobs: tireKnobsUrl }

const surfaceImages = {
  'broken-paved-road': brokenPavedRoadUrl,
  'dirty-road': dirtyRoadUrl,
  'small-stone-road': smallStoneRoadUrl,
  'big-stone-road': bigStoneRoadUrl,
  'field-trail': fieldTrailUrl,
  'forest-trail': forestTrailUrl
}

type TrackPoint = { lat: number; lon: number; ele: number; time?: string }

const { t, locale } = useI18n()
const currentLanguage = ref<MessageLanguages>('en')
watch(locale, (newLocale) => {
  currentLanguage.value = newLocale as MessageLanguages
}, { immediate: true })

const languageDropdownOpen = ref(false)
const languageOptions = {
  en: { flag: '🇺🇸', name: 'English' },
  fr: { flag: '🇫🇷', name: 'Français' }
}

const languageDropdown = ref<HTMLElement | null>(null)

function closeLanguageDropdown(event: MouseEvent) {
  if (languageDropdown.value && !languageDropdown.value.contains(event.target as Node)) {
    languageDropdownOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', closeLanguageDropdown)
})

onUnmounted(() => {
  document.removeEventListener('click', closeLanguageDropdown)
})

const loaded = ref(false)
const name = ref('')
const trailConditions = ref<TrailConditions>({
  tire_dry: 'slick',
  tire_wet: 'slick',
  surface_type: 'forest-trail',
  difficulty_level: 3
})
const submitting = ref(false)
const message = ref('')

// Commentary data
const commentary = ref<Commentary>({
  text: '',
  video_links: [],
  images: []
})
const isDragOver = ref(false)

const fileInput = ref<HTMLInputElement | null>(null)
const imageInput = ref<HTMLInputElement | null>(null)
const points = ref<TrackPoint[]>([])
const startIndex = ref(0)
const endIndex = ref(0)
const cumulativeKm = ref<number[]>([])
const cumulativeSec = ref<number[]>([])
const xMode = ref<'distance' | 'time'>('distance')
const uploadedFileId = ref<string | null>(null)
const uploadProgress = ref<number>(0)
const isUploading = ref<boolean>(false)

const controlsCard = ref<HTMLElement | null>(null)

function changeLanguage(lang: MessageLanguages) {
  currentLanguage.value = lang
  setLanguage(lang)
  languageDropdownOpen.value = false
}
function toggleLanguageDropdown(event: Event) {
  event.stopPropagation()
  languageDropdownOpen.value = !languageDropdownOpen.value
}

const isSaveDisabled = computed(() => submitting.value || !name.value || !loaded.value)
const saveDisabledTitle = computed(() => {
  if (!loaded.value) return t('tooltip.loadGpxFirst')
  if (!name.value) return t('tooltip.enterSegmentName')
  if (submitting.value) return t('tooltip.submitting')
  return ''
})

// Difficulty slider progress
const difficultyProgress = computed(() => {
  return ((trailConditions.value.difficulty_level - 1) / 4) * 100
})

let map: any = null
let fullLine: any = null
let selectedLine: any = null
let baseLayer: any = null

const chartCanvas = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null
const smoothedElevations = ref<number[]>([])

const isDragging = ref(false)
const dragType = ref<'start' | 'end' | null>(null)
const startSliderPosition = ref(0)
const endSliderPosition = ref(100)

const endSliderOffset = ref(0)
const overlapThreshold = 20
const constantOffset = 25
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

function checkSliderOverlap() {
  if (!chart || !chartCanvas.value) return

  const containerRect = chartCanvas.value.parentElement!.getBoundingClientRect()
  const sliderWidth = 20
  const controlsExtension = 18
  const startPixelCenter = (startSliderPosition.value / 100) * containerRect.width + (sliderWidth / 2)
  const endPixelCenter = (endSliderPosition.value / 100) * containerRect.width + (sliderWidth / 2)

  const startControlRight = startPixelCenter + controlsExtension
  const endControlLeft = endPixelCenter - controlsExtension
  const distance = endControlLeft - startControlRight

  if (distance < overlapThreshold) {
    endSliderOffset.value = constantOffset
  } else {
    endSliderOffset.value = 0
  }
}

watch([startIndex, endIndex], () => {
  if (points.value.length > 0 && chart && chartCanvas.value) {
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
    const startPixelCentered = startPixelInContainer - (sliderWidth / 2)
    const endPixelCentered = endPixelInContainer - (sliderWidth / 2)

    startSliderPosition.value = (startPixelCentered / containerRect.width) * 100
    endSliderPosition.value = (endPixelCentered / containerRect.width) * 100
    checkSliderOverlap()
  }
})

function triggerFileOpen() {
  fileInput.value?.click()
}

async function onFileChange(ev: Event) {
  const input = ev.target as HTMLInputElement
  const file = input.files && input.files[0]
  if (!file) return

  isUploading.value = true
  uploadProgress.value = 0
  message.value = ''

  try {
    const formData = new FormData()
    formData.append('file', file)

    // Simulate upload progress for better UX
    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += Math.random() * 20
        if (uploadProgress.value > 90) uploadProgress.value = 90
      }
    }, 200)

    const response = await fetch('/api/upload-gpx', {
      method: 'POST',
      body: formData
    })

    clearInterval(progressInterval)
    uploadProgress.value = 100

    if (!response.ok) {
      const error = await response.text()
      throw new Error(error || 'Upload failed')
    }

    const uploadData = await response.json()

    // Fetch the actual track points from the backend
    const pointsResponse = await fetch(`/api/gpx-points/${uploadData.file_id}`)
    if (!pointsResponse.ok) {
      throw new Error('Failed to fetch track points')
    }

    const pointsData = await pointsResponse.json()
    const actualPoints: TrackPoint[] = pointsData.points.map((p: any) => ({
      lat: p.lat,
      lon: p.lon,
      ele: p.elevation,
      time: p.time
    }))

    if (actualPoints.length < 2) {
      message.value = t('message.insufficientPoints')
      return
    }

    points.value = actualPoints
    cumulativeKm.value = computeCumulativeKm(actualPoints)
    cumulativeSec.value = computeCumulativeSec(actualPoints)
    smoothedElevations.value = computeSmoothedElevations(actualPoints, 5)
    startIndex.value = 0
    endIndex.value = actualPoints.length - 1
    uploadedFileId.value = uploadData.file_id
    loaded.value = true
    message.value = ''

    // Reset upload state after a short delay to show completion
    setTimeout(() => {
      isUploading.value = false
      uploadProgress.value = 0
    }, 1000)

    await nextTick()
    renderMap()
    renderChart()
  } catch (err: any) {
    isUploading.value = false
    uploadProgress.value = 0
    message.value = err.message || t('message.uploadError')
  }
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
function formatKm(km?: number): string { return km == null ? '-' : `${km.toFixed(2)} ${t('units.km')}` }
function formatElevation(ele?: number): string { return ele == null ? '-' : `${Math.round(ele)} ${t('units.m')}` }
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

// Commentary methods
function generateId(): string {
  return Math.random().toString(36).substr(2, 9)
}

function addVideoLink() {
  commentary.value.video_links.push({
    id: generateId(),
    url: '',
    title: '',
    platform: 'youtube'
  })
}

function removeVideoLink(index: number) {
  commentary.value.video_links.splice(index, 1)
}

function validateVideoUrl(video: VideoLink) {
  const url = video.url.toLowerCase()
  if (url.includes('youtube.com') || url.includes('youtu.be')) {
    video.platform = 'youtube'
  } else if (url.includes('vimeo.com')) {
    video.platform = 'vimeo'
  } else if (url) {
    video.platform = 'other'
  }
}

function getVideoIcon(platform: string): string {
  switch (platform) {
    case 'youtube': return 'fa-brands fa-youtube'
    case 'vimeo': return 'fa-brands fa-vimeo'
    default: return 'fa-solid fa-video'
  }
}

function getPlatformName(platform: string): string {
  switch (platform) {
    case 'youtube': return 'YouTube'
    case 'vimeo': return 'Vimeo'
    default: return 'Other'
  }
}

function triggerImageUpload() {
  imageInput.value?.click()
}

function handleImageSelect(event: Event) {
  const input = event.target as HTMLInputElement
  const files = input.files
  if (files) {
    processImageFiles(Array.from(files))
  }
}

function handleDragOver(event: DragEvent) {
  event.preventDefault()
  isDragOver.value = true
}

function handleDragLeave(event: DragEvent) {
  event.preventDefault()
  isDragOver.value = false
}

function handleImageDrop(event: DragEvent) {
  event.preventDefault()
  isDragOver.value = false

  const files = event.dataTransfer?.files
  if (files) {
    const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'))
    processImageFiles(imageFiles)
  }
}

function processImageFiles(files: File[]) {
  files.forEach(file => {
    if (file.type.startsWith('image/')) {
      const reader = new FileReader()
      reader.onload = (e) => {
        const preview = e.target?.result as string
        commentary.value.images.push({
          id: generateId(),
          file,
          preview,
          caption: ''
        })
      }
      reader.readAsDataURL(file)
    }
  })
}

function removeImage(index: number) {
  commentary.value.images.splice(index, 1)
}


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

    for (let i = 0; i < points.value.length; i++) {
      const pointX = getX(i)
      const distance = Math.abs(pointX - dataX)
      if (distance < minDistance) {
        minDistance = distance
        closestIndex = i
      }
    }

    if (type === 'start') {
      const newIndex = Math.min(closestIndex, endIndex.value - 1)
      startIndex.value = Math.max(0, newIndex)
    } else {
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


function renderMap() {
  if (!map) {
    const container = document.getElementById('map')
    if (!container) return
    map = L.map(container)
  }
  const latlngs = points.value.map(p => [p.lat, p.lon]) as [number, number][]
  const bounds = L.latLngBounds(latlngs)
  map!.invalidateSize()
  map!.fitBounds(bounds, { padding: [20, 20] })
  if (!baseLayer) {
    baseLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap'
    })
    baseLayer.addTo(map!)
  }

  if (fullLine) fullLine.remove()
  fullLine = L.polyline(latlngs, { color: '#888', weight: 4 })
  fullLine.addTo(map!)
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
          label: t('chart.elevation'),
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
          title: { display: true, text: t('chart.elevation') },
          min: Math.min(...smoothedElevations.value)
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          filter: function(tooltipItem) {
            return tooltipItem.datasetIndex === 0;
          },
          callbacks: {
            title: function(context) {
              const dataIndex = context[0].dataIndex;
              const xValue = context[0].parsed.x;
              return xMode.value === 'distance' ? `${xValue.toFixed(2)} ${t('units.km')}` : formatXTick(xValue);
            },
            label: function(context) {
              const yValue = context.parsed.y;
              return `${t('chart.elevation')}: ${Math.round(yValue)} ${t('units.m')}`;
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
          const startX = getX(startIndex.value)
          const endX = getX(endIndex.value)

          if (dataX < startX) {
            startIndex.value = Math.min(closestIndex, endIndex.value - 1)
          } else if (dataX > endX) {
            endIndex.value = Math.max(closestIndex, startIndex.value + 1)
          } else {
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

  nextTick(() => {
    if (points.value.length > 0 && chart && chartCanvas.value) {
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
      const startPixelCentered = startPixelInContainer - (sliderWidth / 2)
      const endPixelCentered = endPixelInContainer - (sliderWidth / 2)

      startSliderPosition.value = (startPixelCentered / containerRect.width) * 100
      endSliderPosition.value = (endPixelCentered / containerRect.width) * 100
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
  const selectedData = []

  for (let i = startIndex.value; i <= endIndex.value; i++) {
    selectedData.push({
      x: getX(i),
      y: smoothedElevations.value[i] ?? points.value[i]?.ele ?? 0
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
  if (chart) {
    // @ts-ignore
    chart.data.datasets[1].data = buildSelectedAreaData()
    chart.update()
  }
  if (map && points.value.length > 1) {
    const segLatLngs = points.value.slice(startIndex.value, endIndex.value + 1).map(p => [p.lat, p.lon]) as [number, number][]
    const segBounds = L.latLngBounds(segLatLngs)
    map.fitBounds(segBounds, { padding: [20, 20] })
  }
})

watch(xMode, () => {
  if (!chart) return
  const fullData = buildFullXYData()
  // @ts-ignore
  chart.data.datasets[0].data = fullData.map(d => ({ x: d.x, y: d.y }))
  // @ts-ignore
  chart.data.datasets[1].data = buildSelectedAreaData()
  // @ts-ignore
  chart.options.scales.x.ticks.callback = (v) => formatXTick(Number(v))
  // @ts-ignore
  chart.options.scales.x.min = getX(0)
  // @ts-ignore
  chart.options.scales.x.max = getX(points.value.length - 1)

  chart.update()

  nextTick(() => {
    if (points.value.length > 0 && chart && chartCanvas.value) {
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
      const startPixelCentered = startPixelInContainer - (sliderWidth / 2)
      const endPixelCentered = endPixelInContainer - (sliderWidth / 2)

      startSliderPosition.value = (startPixelCentered / containerRect.width) * 100
      endSliderPosition.value = (endPixelCentered / containerRect.width) * 100
      checkSliderOverlap()
    }
  })
})


watch(loaded, async () => {
  await nextTick()
})

onMounted(() => {
  const onResize = () => {
    if (map) {
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


function escapeXml(s: string): string {
  return s.replace(/[<>&"']/g, c => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&apos;' }[c] as string))
}

async function onSubmit() {
  if (!loaded.value || points.value.length < 2 || !uploadedFileId.value) {
    message.value = t('message.loadGpxFirst')
    return
  }
  submitting.value = true
  message.value = ''
  try {
    const formData = new FormData()
    formData.append('name', name.value)
    formData.append('tire_dry', trailConditions.value.tire_dry)
    formData.append('tire_wet', trailConditions.value.tire_wet)
    formData.append('surface_type', trailConditions.value.surface_type)
    formData.append('difficulty_level', trailConditions.value.difficulty_level.toString())

    // Add the start and end indices for GPX processing
    formData.append('start_index', startIndex.value.toString())
    formData.append('end_index', endIndex.value.toString())

    // Add the uploaded file ID instead of the file itself
    formData.append('file_id', uploadedFileId.value)

    // Add commentary data
    formData.append('commentary_text', commentary.value.text)
    formData.append('video_links', JSON.stringify(commentary.value.video_links))

    // Add images
    commentary.value.images.forEach((image, index) => {
      formData.append(`image_${index}`, image.file)
      formData.append(`image_${index}_caption`, image.caption || '')
    })

    const res = await fetch('/api/segments', { method: 'POST', body: formData })
    if (!res.ok) {
      const detail = await res.text()
      throw new Error(detail || 'Failed to create segment')
    }

    name.value = ''
    trailConditions.value = { tire_dry: 'slick', tire_wet: 'slick', surface_type: 'forest-trail', difficulty_level: 3 }
    loaded.value = false
    points.value = []
    uploadedFileId.value = null
    commentary.value = { text: '', video_links: [], images: [] }
    chart?.destroy(); chart = null
    if (fullLine) { fullLine.remove(); fullLine = null }
    if (selectedLine) { selectedLine.remove(); selectedLine = null }
    message.value = t('message.segmentCreated')
  } catch (err: any) {
    message.value = err.message || t('message.createError')
  } finally {
    submitting.value = false
  }
}
</script>

<style>
:root {
  --brand-50: #ffe6d5ff;
  --brand-100: #ffccaaff;
  --brand-200: #ffb380ff;
  --brand-300: #ff9955ff;
  --brand-400: #ff7f2aff;
  --brand-500: #ff6600ff;
  --brand-600: #e65c00ff;

  --brand-primary: var(--brand-500);
  --brand-primary-hover: #e65c00;
  --brand-accent: var(--brand-300);
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

.sidebar { --sidebar-w: 230px; width: var(--sidebar-w); background: transparent; border-right: none; padding: 0; margin: 0; box-sizing: border-box; position: fixed; top: var(--topbar-h, 48px); left: calc(50% - 500px - var(--sidebar-w)); display: flex; flex-direction: column; height: calc(100vh - var(--topbar-h, 48px)); z-index: 100; }
.sidebar-scroll { display: flex; flex-direction: column; align-items: flex-start; gap: 0.75rem; max-height: calc(100vh - var(--topbar-h, 48px)); overflow-y: auto; overflow-x: hidden; padding: 1rem; }
.sidebar .card { margin: 0; width: 100%; box-sizing: border-box; }

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
.menu-item.active { background: var(--brand-50); color: var(--brand-600); font-weight: 500; }
.menu-item.active:hover { background: var(--brand-100); }

.language-dropdown {
  position: relative;
}

.language-flag {
  font-size: 1.1em;
  line-height: 1;
}

.language-name {
  flex: 1;
  white-space: nowrap;
}

.dropdown-arrow {
  font-size: 0.75em;
  transition: transform 0.2s ease;
  opacity: 0.7;
}

.dropdown-arrow .fa-chevron-down.rotated {
  transform: rotate(180deg);
}

.language-option {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border: none;
  background: transparent;
  cursor: pointer;
  color: #374151;
  font-size: 0.875rem;
  text-align: left;
  transition: all 0.2s ease;
  border-radius: 0;
}

.language-option:first-child {
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
}

.language-option:last-child {
  border-bottom-left-radius: 8px;
  border-bottom-right-radius: 8px;
}

.language-option:hover {
  background: #f9fafb;
  color: #111827;
}

.language-option.active {
  background: var(--brand-50);
  color: var(--brand-600);
  font-weight: 500;
}

.language-option.active:hover {
  background: var(--brand-100);
}

.language-option .language-flag {
  font-size: 1.1em;
}

.language-option .language-name {
  flex: 1;
}

.checkmark {
  font-size: 0.75em;
  color: var(--brand-500);
}

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
.metric { display: flex; align-items: center; gap: 0.4rem; color: #374151; }
.metric .icon { width: 18px; text-align: center; }
.metrics-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.25rem 0.5rem; align-items: center; margin-bottom: 0.75rem; width: 100%; box-sizing: border-box; }
.gps-title { display: inline-flex; align-items: center; gap: 0.35rem; color: #374151; font-weight: 500; }
.gps-title .icon { width: 18px; text-align: center; }
.gps-col { display: flex; align-items: center; gap: 0.4rem; color: #374151; }
.gps-col .label { font-size: 12px; color: #6b7280; }
.gps-col .value { font-variant-numeric: tabular-nums; }
.chart-wrapper { width: 100%; overflow: visible; margin-bottom: 20px; }
.chart-container { position: relative; width: 100%; overflow: visible; }
.chart { width: 100%; height: 200px; max-height: 200px; cursor: crosshair; }

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
/* Trail Conditions Card Styles */
.trail-conditions-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 1rem;
  margin-top: 1rem;
  width: 100%;
  box-sizing: border-box;
}

.trail-conditions-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #f1f5f9;
}

.trail-conditions-header .icon {
  width: 18px;
  text-align: center;
  color: var(--brand-500);
}

.trail-conditions-title {
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
}

.trail-subsection {
  margin-bottom: 2rem;
}

.trail-subsection:last-child {
  margin-bottom: 0;
}

.subsection-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #f1f5f9;
}

.subsection-header .icon {
  width: 16px;
  text-align: center;
  color: var(--brand-500);
}

.subsection-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #374151;
}

.tire-groups {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem 1rem;
  align-items: start;
  width: 100%;
  box-sizing: border-box;
}

.tire-group { background: #fbfcfe; border: 1px solid #e5e7eb; border-radius: 10px; padding: 0.5rem; }

/* Surface Type Styles */
.surface-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
}

.surface-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 0.75rem;
  cursor: pointer;
  background: #fff;
  transition: all 0.2s;
}

.surface-option input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.surface-option img {
  width: 100%;
  aspect-ratio: 16/9;
  object-fit: cover;
  border-radius: 6px;
}

.surface-caption {
  font-size: 0.8rem;
  color: #374151;
  text-align: center;
  font-weight: 500;
}

.surface-option.selected {
  border-color: var(--brand-500);
  box-shadow: 0 0 0 2px rgba(255, 102, 0, 0.15);
  background: var(--brand-50);
}

/* Difficulty Level Styles */
.difficulty-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.difficulty-slider-container {
  position: relative;
  padding: 0.5rem 0;
}

.difficulty-slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e5e7eb;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  position: relative;
}

.difficulty-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--brand-500);
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  position: relative;
  z-index: 2;
}

.difficulty-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--brand-500);
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  position: relative;
  z-index: 2;
}

.difficulty-slider::-webkit-slider-track {
  background: linear-gradient(to right, var(--brand-500) 0%, var(--brand-500) var(--slider-progress, 0%), #e5e7eb var(--slider-progress, 0%), #e5e7eb 100%);
}

.difficulty-slider::-moz-range-track {
  background: linear-gradient(to right, var(--brand-500) 0%, var(--brand-500) var(--slider-progress, 0%), #e5e7eb var(--slider-progress, 0%), #e5e7eb 100%);
}

.difficulty-marks {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
}

.difficulty-mark {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 0.5rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: all 0.2s;
  min-width: 60px;
}

.difficulty-mark.active {
  background: var(--brand-50);
  border-color: var(--brand-300);
}

.difficulty-number {
  font-size: 1rem;
  font-weight: 700;
  color: #374151;
  line-height: 1;
}

.difficulty-text {
  font-size: 0.7rem;
  color: #6b7280;
  font-weight: 500;
  line-height: 1;
  text-align: center;
}

.difficulty-mark.active .difficulty-number {
  color: var(--brand-600);
}

.difficulty-mark.active .difficulty-text {
  color: var(--brand-600);
}
.tire-group-header { display: flex; align-items: center; gap: 0.4rem; color: #374151; margin: 0 0 0.5rem 0; }
.tire-group-help { margin: 0 0 0.5rem 0; font-size: 12px; color: #6b7280; }
.tire-group-header .icon { width: 18px; text-align: center; color: var(--brand-500, #ff6600); }
.tire-group-title { font-size: 0.95rem; }
.tire-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; align-items: start; }
.tire-option { display: flex; flex-direction: column; align-items: center; gap: 0.25rem; border: 1px solid #e5e7eb; border-radius: 8px; padding: 0.5rem; cursor: pointer; background: #fff; }
.tire-option input { position: absolute; opacity: 0; pointer-events: none; }
.tire-option img { width: 100%; aspect-ratio: 1 / 1; object-fit: cover; border-radius: 6px; }
.tire-option .tire-caption { font-size: 12px; color: #374151; }
.tire-option.selected { border-color: var(--brand-500, #ff6600); box-shadow: 0 0 0 2px rgba(255, 102, 0, 0.15); background: var(--brand-50); }
.req { color: #dc2626; }
.section-indicator { display: inline-flex; align-items: center; gap: 0.5rem; font-size: 1rem; color: #374151; padding: 0 0.25rem; margin-top: 0.5rem; }
.section-indicator .icon { width: 18px; text-align: center; }
.empty { padding: 2rem; text-align: center; color: #666; }
.message { margin-top: 1rem; }

/* Upload Progress Bar Styles - Integrated in Menu */
.upload-progress-section {
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid #f1f5f9;
}

.upload-progress-container {
  padding: 0.75rem;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  margin: 0 0.25rem;
}

.upload-progress-bar {
  width: 100%;
  height: 6px;
  background-color: #e2e8f0;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.upload-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff6600, #ff8533);
  border-radius: 3px;
  transition: width 0.3s ease;
  box-shadow: 0 1px 2px rgba(255, 102, 0, 0.2);
}

.upload-progress-text {
  text-align: center;
  font-size: 0.75rem;
  color: #475569;
  font-weight: 500;
  line-height: 1.2;
}

@media (max-width: 1200px) {
  .topbar-inner {
    max-width: 100%;
    padding: 0 1rem;
  }
}

@media (max-width: 960px) {
  .nav-left {
    left: calc(50% - 500px - 172px + 1rem);
    gap: 1rem;
  }

  .topbar .logo {
    width: 172px;
  }

  .nav .language-dropdown-trigger.navbar-trigger {
    padding: 0.4rem 0.6rem;
    font-size: 0.8rem;
  }
}

@media (max-width: 768px) {
  .nav-left {
    left: calc(50% - 500px - 138px + 1rem);
  }

  .topbar .logo {
    width: 138px;
  }
}

@media (max-width: 480px) {
  .topbar-inner {
    padding: 0 0.75rem;
  }

  .nav-left {
    left: calc(50% - 500px - 115px + 0.75rem);
  }

  .topbar .logo {
    width: 115px;
  }

  .nav .language-dropdown-trigger.navbar-trigger {
    padding: 0.3rem 0.5rem;
    font-size: 0.75rem;
  }

  .language-name {
    display: none; /* Hide language name on very small screens */
  }
}

:root { --topbar-h: 48px; }
.topbar {
  position: sticky;
  top: 0;
  z-index: 9999;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  height: var(--topbar-h, 48px);
  width: 100%;
}

.topbar-inner {
  max-width: none;
  margin: 0;
  padding: 0 1.5rem;
  height: var(--topbar-h, 48px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-sizing: border-box;
  gap: 2rem;
  position: relative;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  position: absolute;
  left: calc(50% - 500px - 230px + 1.5rem);
}

.topbar .logo {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  width: 230px;
}

.topbar .logo-img {
  height: 32px;
  width: auto;
  display: block;
  object-fit: contain;
}

.topbar .nav {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex: 1;
}


.nav .language-dropdown {
  position: relative;
}

.nav .language-dropdown-trigger.navbar-trigger {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #ffffff;
  cursor: pointer;
  color: #374151;
  font-size: 0.875rem;
  text-align: left;
  transition: all 0.2s ease;
  white-space: nowrap;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.nav .language-dropdown-trigger.navbar-trigger:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

.nav .language-dropdown-trigger.navbar-trigger.active {
  background: var(--brand-50);
  border-color: var(--brand-300);
  color: var(--brand-600);
  box-shadow: 0 0 0 3px rgba(255, 102, 0, 0.1);
}

.nav .language-dropdown-menu.navbar-menu {
  position: absolute;
  top: 100%;
  right: 0;
  left: auto;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-8px);
  transition: all 0.2s ease;
  margin-top: 6px;
  min-width: 160px;
  overflow: hidden;
}

.nav .language-dropdown-menu.navbar-menu.open {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
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

.tire-group:nth-child(2) .tire-group-header .icon {
  color: var(--blue-500);
}

.tire-group:nth-child(2) .tire-option.selected {
  border-color: var(--blue-500);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
  background: var(--blue-50);
}

/* Commentary Section Styles */
.commentary-section {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 1rem;
  margin-top: 1rem;
  width: 100%;
  box-sizing: border-box;
}

.commentary-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #f1f5f9;
}

.commentary-header .icon {
  width: 18px;
  text-align: center;
  color: var(--brand-500);
}

.commentary-title {
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
}

.commentary-field {
  margin-bottom: 1.5rem;
}

.commentary-field:last-child {
  margin-bottom: 0;
}

.commentary-field label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #374151;
}

.commentary-textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-family: inherit;
  font-size: 0.875rem;
  line-height: 1.5;
  resize: vertical;
  min-height: 100px;
  box-sizing: border-box;
}

.commentary-textarea:focus {
  outline: none;
  border-color: var(--brand-500);
  box-shadow: 0 0 0 3px rgba(255, 102, 0, 0.1);
}

/* Media Section Styles */
.media-section {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 1rem;
  margin-top: 1rem;
  width: 100%;
  box-sizing: border-box;
}

.media-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #f1f5f9;
}

.media-header .icon {
  width: 18px;
  text-align: center;
  color: var(--brand-500);
}

.media-title {
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
}

.media-field {
  margin-bottom: 1.5rem;
}

.media-field:last-child {
  margin-bottom: 0;
}

.media-field label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #374151;
}

/* Video Links Styles */
.video-links-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.video-link-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.video-link-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.video-platform {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.video-platform i {
  width: 16px;
  text-align: center;
}

.platform-name {
  font-weight: 500;
}

.video-url-input,
.video-title-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 0.875rem;
  box-sizing: border-box;
}

.video-url-input:focus,
.video-title-input:focus {
  outline: none;
  border-color: var(--brand-500);
  box-shadow: 0 0 0 2px rgba(255, 102, 0, 0.1);
}

.remove-video-btn {
  padding: 0.5rem;
  border: none;
  background: #ef4444;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
  flex-shrink: 0;
}

.remove-video-btn:hover {
  background: #dc2626;
}

.add-video-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  border: 2px dashed #d1d5db;
  background: transparent;
  color: #6b7280;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;
}

.add-video-btn:hover {
  border-color: var(--brand-500);
  color: var(--brand-500);
  background: var(--brand-50);
}

/* Image Upload Styles */
.image-upload-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.image-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.image-preview {
  position: relative;
  aspect-ratio: 16/9;
  border-radius: 8px;
  overflow: hidden;
  background: #f3f4f6;
}

.image-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.image-preview:hover .image-overlay {
  opacity: 1;
}

.remove-image-btn {
  padding: 0.5rem;
  border: none;
  background: #ef4444;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.remove-image-btn:hover {
  background: #dc2626;
}

.image-caption-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 0.875rem;
  box-sizing: border-box;
}

.image-caption-input:focus {
  outline: none;
  border-color: var(--brand-500);
  box-shadow: 0 0 0 2px rgba(255, 102, 0, 0.1);
}

.image-upload-area {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  background: #fafafa;
  cursor: pointer;
  transition: all 0.2s;
  grid-column: 1 / -1;
}

.image-upload-area:hover,
.image-upload-area.drag-over {
  border-color: var(--brand-500);
  background: var(--brand-50);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  text-align: center;
}

.upload-icon {
  font-size: 2rem;
  color: #9ca3af;
}

.upload-text {
  font-weight: 500;
  color: #374151;
}

.upload-hint {
  font-size: 0.875rem;
  color: #6b7280;
}

</style>
