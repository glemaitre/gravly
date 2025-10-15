<template>
  <form class="card meta" @submit.prevent="$emit('submit')">
    <!-- Track Type Tabs -->
    <div class="track-type-tabs">
      <button
        type="button"
        class="tab-button"
        :class="{ active: modelTrackType === 'segment' }"
        @click="updateTrackType('segment')"
      >
        <i class="fa-solid fa-route"></i>
        {{ t('trackType.segment') }}
      </button>
      <button
        type="button"
        class="tab-button"
        :class="{ active: modelTrackType === 'route' }"
        @click="updateTrackType('route')"
      >
        <i class="fa-solid fa-map"></i>
        {{ t('trackType.route') }}
      </button>
    </div>

    <div>
      <label for="name"
        >{{ nameLabel }} <span class="req">{{ t('required') }}</span></label
      >
      <input id="name" :value="modelName" @input="updateName" type="text" required />
    </div>

    <!-- Trail Conditions Card -->
    <div class="trail-conditions-card">
      <div class="trail-conditions-header">
        <span class="icon" aria-hidden="true"
          ><i class="fa-solid fa-mountain"></i
        ></span>
        <span class="trail-conditions-title">{{ t('form.trailConditions') }}</span>
      </div>

      <!-- Difficulty Level -->
      <div class="trail-subsection">
        <div class="subsection-header">
          <span class="icon" aria-hidden="true"
            ><i class="fa-solid fa-signal"></i
          ></span>
          <span class="subsection-title">{{ t('form.difficultyLevel') }}</span>
        </div>

        <div class="difficulty-container">
          <div class="difficulty-slider-container">
            <input
              type="range"
              min="1"
              max="5"
              :value="modelTrailConditions.difficulty_level"
              @input="updateDifficultyLevel"
              class="difficulty-slider"
              :style="{ '--slider-progress': difficultyProgress + '%' }"
              :aria-label="t('form.difficultyLevel')"
            />
            <div class="difficulty-marks">
              <div
                v-for="i in 5"
                :key="i"
                class="difficulty-mark-wrapper"
                @mouseenter="showDifficultyTooltip($event)"
                @mouseleave="hideDifficultyTooltip"
                @mousemove="updateDifficultyTooltipPosition($event)"
                @click="setDifficultyLevel(i)"
              >
                <div
                  class="difficulty-mark"
                  :class="{ active: modelTrailConditions.difficulty_level >= i }"
                >
                  <span class="difficulty-number">{{ i }}</span>
                  <span class="difficulty-text">{{ t(`difficulty.level${i}`) }}</span>
                </div>
                <div class="difficulty-tooltip">
                  {{ getDifficultyDescription(i) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Surface Type Selection -->
      <div class="trail-subsection">
        <div class="subsection-header">
          <span class="icon" aria-hidden="true"><i class="fa-solid fa-road"></i></span>
          <span class="subsection-title"
            >{{ surfaceTypeLabel }} <span class="req">{{ t('required') }}</span></span
          >
        </div>

        <div class="surface-options">
          <label
            v-for="(image, surfaceType) in surfaceImages"
            :key="surfaceType"
            class="surface-option"
            :class="{ selected: isSurfaceTypeSelected(surfaceType as string) }"
          >
            <input
              type="checkbox"
              name="surfaceType"
              :value="surfaceType"
              :checked="isSurfaceTypeSelected(surfaceType as string)"
              @change="toggleSurfaceType(surfaceType as any)"
            />
            <img :src="image" :alt="t(`surface.${surfaceType}`)" />
            <span class="surface-caption">{{ t(`surface.${surfaceType}`) }}</span>
          </label>
        </div>
      </div>

      <!-- Tire Selection -->
      <div class="trail-subsection">
        <div class="subsection-header">
          <span class="icon" aria-hidden="true"
            ><i class="fa-solid fa-circle-dot"></i
          ></span>
          <span class="subsection-title">{{ t('form.tire') }}</span>
        </div>

        <div class="tire-groups">
          <div class="tire-group">
            <div class="tire-group-header">
              <span class="icon" aria-hidden="true"
                ><i class="fa-solid fa-sun"></i
              ></span>
              <span class="tire-group-title">{{ t('tire.dry') }}</span>
            </div>
            <p class="tire-group-help">{{ t('tire.dryHelp') }}</p>
            <div class="tire-row" role="radiogroup" :aria-label="t('tire.dry')">
              <label
                class="tire-option"
                :class="{ selected: modelTrailConditions.tire_dry === 'slick' }"
              >
                <input
                  type="radio"
                  name="tireDry"
                  value="slick"
                  :checked="modelTrailConditions.tire_dry === 'slick'"
                  @change="updateTireDry('slick')"
                />
                <img :src="tireImages.slick" :alt="t('tire.slick')" />
                <span class="tire-caption">{{ t('tire.slick') }}</span>
              </label>
              <label
                class="tire-option"
                :class="{ selected: modelTrailConditions.tire_dry === 'semi-slick' }"
              >
                <input
                  type="radio"
                  name="tireDry"
                  value="semi-slick"
                  :checked="modelTrailConditions.tire_dry === 'semi-slick'"
                  @change="updateTireDry('semi-slick')"
                />
                <img :src="tireImages.semiSlick" :alt="t('tire.semiSlick')" />
                <span class="tire-caption">{{ t('tire.semiSlick') }}</span>
              </label>
              <label
                class="tire-option"
                :class="{ selected: modelTrailConditions.tire_dry === 'knobs' }"
              >
                <input
                  type="radio"
                  name="tireDry"
                  value="knobs"
                  :checked="modelTrailConditions.tire_dry === 'knobs'"
                  @change="updateTireDry('knobs')"
                />
                <img :src="tireImages.knobs" :alt="t('tire.knobs')" />
                <span class="tire-caption">{{ t('tire.knobs') }}</span>
              </label>
            </div>
          </div>
          <div class="tire-group">
            <div class="tire-group-header">
              <span class="icon" aria-hidden="true"
                ><i class="fa-solid fa-cloud-rain"></i
              ></span>
              <span class="tire-group-title">{{ t('tire.wet') }}</span>
            </div>
            <p class="tire-group-help">{{ t('tire.wetHelp') }}</p>
            <div class="tire-row" role="radiogroup" :aria-label="t('tire.wet')">
              <label
                class="tire-option"
                :class="{ selected: modelTrailConditions.tire_wet === 'slick' }"
              >
                <input
                  type="radio"
                  name="tireWet"
                  value="slick"
                  :checked="modelTrailConditions.tire_wet === 'slick'"
                  @change="updateTireWet('slick')"
                />
                <img :src="tireImages.slick" :alt="t('tire.slick')" />
                <span class="tire-caption">{{ t('tire.slick') }}</span>
              </label>
              <label
                class="tire-option"
                :class="{ selected: modelTrailConditions.tire_wet === 'semi-slick' }"
              >
                <input
                  type="radio"
                  name="tireWet"
                  value="semi-slick"
                  :checked="modelTrailConditions.tire_wet === 'semi-slick'"
                  @change="updateTireWet('semi-slick')"
                />
                <img :src="tireImages.semiSlick" :alt="t('tire.semiSlick')" />
                <span class="tire-caption">{{ t('tire.semiSlick') }}</span>
              </label>
              <label
                class="tire-option"
                :class="{ selected: modelTrailConditions.tire_wet === 'knobs' }"
              >
                <input
                  type="radio"
                  name="tireWet"
                  value="knobs"
                  :checked="modelTrailConditions.tire_wet === 'knobs'"
                  @change="updateTireWet('knobs')"
                />
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
        <span class="icon" aria-hidden="true"
          ><i class="fa-solid fa-photo-film"></i
        ></span>
        <span class="media-title">{{ t('form.media') }}</span>
      </div>

      <!-- Video Links Section -->
      <div class="media-field">
        <label>{{ t('form.videoLinks') }}</label>
        <div class="video-links-container">
          <div
            v-for="(video, index) in modelCommentary.video_links"
            :key="video.id"
            class="video-link-item"
          >
            <div class="video-link-content">
              <div class="video-platform">
                <i :class="getVideoIcon(video.platform)"></i>
                <span class="platform-name">{{ getPlatformName(video.platform) }}</span>
              </div>
              <input
                :value="video.url"
                @input="updateVideoUrl(index, $event)"
                type="url"
                :placeholder="t('form.videoUrlPlaceholder')"
                class="video-url-input"
              />
            </div>
            <button
              type="button"
              @click="handleRemoveVideoLink(index)"
              class="remove-video-btn"
              :title="t('form.removeVideo')"
            >
              <i class="fa-solid fa-trash"></i>
            </button>
          </div>
          <button type="button" @click="handleAddVideoLink" class="add-video-btn">
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
            v-for="(image, index) in modelCommentary.images"
            :key="image.id"
            class="image-item"
          >
            <div class="image-preview">
              <img :src="image.preview" :alt="image.caption || t('form.imageAlt')" />
              <div class="image-overlay">
                <button
                  type="button"
                  @click="handleRemoveImage(index)"
                  class="remove-image-btn"
                  :title="t('form.removeImage')"
                >
                  <i class="fa-solid fa-trash"></i>
                </button>
              </div>
            </div>
            <input
              :value="image.caption"
              @input="updateImageCaption(index, $event)"
              type="text"
              :placeholder="t('form.imageCaptionPlaceholder')"
              class="image-caption-input"
            />
          </div>
          <div
            class="image-upload-area"
            :class="{ 'drag-over': modelIsDragOver }"
            @click="handleTriggerImageUpload"
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
        <span class="icon" aria-hidden="true"
          ><i class="fa-solid fa-comment-dots"></i
        ></span>
        <span class="commentary-title">{{ t('form.comments') }}</span>
      </div>

      <!-- Free Text Commentary -->
      <div class="commentary-field">
        <label for="commentary-text">{{ t('form.commentaryText') }}</label>
        <textarea
          id="commentary-text"
          :value="modelCommentary.text"
          @input="updateCommentaryText"
          :placeholder="t('form.commentaryPlaceholder')"
          rows="4"
          class="commentary-textarea"
        ></textarea>
      </div>
    </div>
  </form>
</template>

<script lang="ts" setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Commentary, TrailConditions, SurfaceType } from '../types'
import tireSlickUrl from '../assets/images/slick.png'
import tireSemiSlickUrl from '../assets/images/semi-slick.png'
import tireKnobsUrl from '../assets/images/ext.png'
import bigStoneRoadUrl from '../assets/images/big-stone-road.jpeg'
import brokenPavedRoadUrl from '../assets/images/broken-paved-road.jpeg'
import dirtyRoadUrl from '../assets/images/dirty-road.jpeg'
import fieldTrailUrl from '../assets/images/field-trail.jpeg'
import forestTrailUrl from '../assets/images/forest-trail.jpeg'
import smallStoneRoadUrl from '../assets/images/small-stone-road.jpeg'

const tireImages = {
  slick: tireSlickUrl,
  semiSlick: tireSemiSlickUrl,
  knobs: tireKnobsUrl
}

const surfaceImages = {
  'broken-paved-road': brokenPavedRoadUrl,
  'dirty-road': dirtyRoadUrl,
  'small-stone-road': smallStoneRoadUrl,
  'big-stone-road': bigStoneRoadUrl,
  'field-trail': fieldTrailUrl,
  'forest-trail': forestTrailUrl
}

const { t } = useI18n()

interface Props {
  name: string
  trackType: 'segment' | 'route'
  trailConditions: TrailConditions
  commentary: Commentary
  isDragOver: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:name': [value: string]
  'update:trackType': [value: 'segment' | 'route']
  'update:trailConditions': [value: TrailConditions]
  'update:commentary': [value: Commentary]
  'update:isDragOver': [value: boolean]
  submit: []
}>()

const imageInput = ref<HTMLInputElement | null>(null)

// Create local computed properties for two-way binding
const modelName = computed({
  get: () => props.name,
  set: (value: string) => emit('update:name', value)
})

const modelTrackType = computed({
  get: () => props.trackType,
  set: (value: 'segment' | 'route') => emit('update:trackType', value)
})

const modelTrailConditions = computed({
  get: () => props.trailConditions,
  set: (value: TrailConditions) => emit('update:trailConditions', value)
})

const modelCommentary = computed({
  get: () => props.commentary,
  set: (value: Commentary) => emit('update:commentary', value)
})

const modelIsDragOver = computed({
  get: () => props.isDragOver,
  set: (value: boolean) => emit('update:isDragOver', value)
})

// Dynamic labels based on track type
const nameLabel = computed(() => {
  return modelTrackType.value === 'segment'
    ? t('form.segmentName')
    : t('form.routeName')
})

const surfaceTypeLabel = computed(() => {
  return modelTrackType.value === 'segment'
    ? t('form.surfaceType')
    : t('form.majorSurfaceType')
})

// Difficulty slider progress
const difficultyProgress = computed(() => {
  return ((modelTrailConditions.value.difficulty_level - 1) / 4) * 100
})

// Update methods
function updateName(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:name', target.value)
}

function updateTrackType(value: 'segment' | 'route') {
  emit('update:trackType', value)
}

function updateDifficultyLevel(event: Event) {
  const target = event.target as HTMLInputElement
  const newConditions = {
    ...modelTrailConditions.value,
    difficulty_level: parseInt(target.value)
  }
  emit('update:trailConditions', newConditions)
}

function setDifficultyLevel(level: number) {
  const newConditions = { ...modelTrailConditions.value, difficulty_level: level }
  emit('update:trailConditions', newConditions)
}

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
  const tooltipRect = tooltip.getBoundingClientRect()
  const viewportWidth = window.innerWidth

  // Position tooltip above the difficulty mark
  let left = rect.left + rect.width / 2 - tooltipRect.width / 2
  let top = rect.top - tooltipRect.height - 8

  // Ensure tooltip stays within viewport bounds
  if (left < 10) {
    left = 10
  } else if (left + tooltipRect.width > viewportWidth - 10) {
    left = viewportWidth - tooltipRect.width - 10
  }

  // If tooltip would go above viewport, position it below
  if (top < 10) {
    top = rect.bottom + 8
  }

  tooltip.style.left = `${left}px`
  tooltip.style.top = `${top}px`
}

function isSurfaceTypeSelected(surfaceType: string): boolean {
  return modelTrailConditions.value.surface_type.includes(surfaceType as SurfaceType)
}

function toggleSurfaceType(surfaceType: SurfaceType) {
  const currentTypes = [...modelTrailConditions.value.surface_type]
  const index = currentTypes.indexOf(surfaceType)

  if (index > -1) {
    // Remove if already selected
    currentTypes.splice(index, 1)
  } else {
    // Add if not selected
    currentTypes.push(surfaceType)
  }

  const newConditions = { ...modelTrailConditions.value, surface_type: currentTypes }
  emit('update:trailConditions', newConditions)
}

function updateTireDry(tire: 'slick' | 'semi-slick' | 'knobs') {
  const newConditions = { ...modelTrailConditions.value, tire_dry: tire }
  emit('update:trailConditions', newConditions)
}

function updateTireWet(tire: 'slick' | 'semi-slick' | 'knobs') {
  const newConditions = { ...modelTrailConditions.value, tire_wet: tire }
  emit('update:trailConditions', newConditions)
}

function updateCommentaryText(event: Event) {
  const target = event.target as HTMLTextAreaElement
  const newCommentary = { ...modelCommentary.value, text: target.value }
  emit('update:commentary', newCommentary)
}

// Video link methods
function generateId(): string {
  return Math.random().toString(36).substr(2, 9)
}

function handleAddVideoLink() {
  const newVideoLinks = [
    ...modelCommentary.value.video_links,
    {
      id: generateId(),
      url: '',
      platform: 'youtube' as const
    }
  ]
  emit('update:commentary', { ...modelCommentary.value, video_links: newVideoLinks })
}

function handleRemoveVideoLink(index: number) {
  const newVideoLinks = [...modelCommentary.value.video_links]
  newVideoLinks.splice(index, 1)
  emit('update:commentary', { ...modelCommentary.value, video_links: newVideoLinks })
}

function updateVideoUrl(index: number, event: Event) {
  const target = event.target as HTMLInputElement
  const newVideoLinks = [...modelCommentary.value.video_links]
  newVideoLinks[index] = { ...newVideoLinks[index], url: target.value }

  // Validate video URL
  const video = newVideoLinks[index]
  const url = video.url.toLowerCase()
  if (url.includes('youtube.com') || url.includes('youtu.be')) {
    video.platform = 'youtube'
  } else if (url.includes('vimeo.com')) {
    video.platform = 'vimeo'
  } else if (url) {
    video.platform = 'other'
  }

  emit('update:commentary', { ...modelCommentary.value, video_links: newVideoLinks })
}

function getVideoIcon(platform: string): string {
  switch (platform) {
    case 'youtube':
      return 'fa-brands fa-youtube'
    case 'vimeo':
      return 'fa-brands fa-vimeo'
    default:
      return 'fa-solid fa-video'
  }
}

function getPlatformName(platform: string): string {
  switch (platform) {
    case 'youtube':
      return 'YouTube'
    case 'vimeo':
      return 'Vimeo'
    default:
      return 'Other'
  }
}

// Image methods
function handleTriggerImageUpload() {
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
  emit('update:isDragOver', true)
}

function handleDragLeave(event: DragEvent) {
  event.preventDefault()
  emit('update:isDragOver', false)
}

function handleImageDrop(event: DragEvent) {
  event.preventDefault()
  emit('update:isDragOver', false)

  const files = event.dataTransfer?.files
  if (files) {
    const imageFiles = Array.from(files).filter((file) =>
      file.type.startsWith('image/')
    )
    processImageFiles(imageFiles)
  }
}

function processImageFiles(files: File[]) {
  const newImages = [...modelCommentary.value.images]

  files.forEach((file) => {
    if (file.type.startsWith('image/')) {
      // Create preview from file immediately
      const reader = new FileReader()
      reader.onload = (e) => {
        const preview = e.target?.result as string
        const imageId = generateId()

        // Add to commentary with temporary preview - upload will happen on save
        const newImage = {
          id: imageId,
          file,
          preview,
          caption: '',
          uploaded: false,
          image_url: '',
          image_id: '',
          storage_key: '',
          filename: file.name,
          original_filename: file.name
        }
        newImages.push(newImage)

        emit('update:commentary', { ...modelCommentary.value, images: newImages })
      }
      reader.readAsDataURL(file)
    }
  })
}

function handleRemoveImage(index: number) {
  const newImages = [...modelCommentary.value.images]
  newImages.splice(index, 1)
  emit('update:commentary', { ...modelCommentary.value, images: newImages })
}

function updateImageCaption(index: number, event: Event) {
  const target = event.target as HTMLInputElement
  const newImages = [...modelCommentary.value.images]
  newImages[index] = { ...newImages[index], caption: target.value }
  emit('update:commentary', { ...modelCommentary.value, images: newImages })
}
</script>

<style scoped>
.meta {
  background: #ffffff;
  width: 100%;
  margin-top: 1rem;
  margin-bottom: 1rem;
  display: block;
}

/* Track Type Tabs */
.track-type-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  padding: 0.5rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

/* Responsive track-type-tabs for small devices */
@media (max-width: 450px) {
  .track-type-tabs {
    grid-template-columns: 1fr;
    gap: 0.25rem;
  }
}

.tab-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #6b7280;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  width: 100%;
  box-sizing: border-box;
}

.tab-button:hover {
  background: #e5e7eb;
  color: #374151;
}

.tab-button.active {
  background: #ffffff;
  color: var(--brand-600);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--brand-200);
}

.tab-button i {
  font-size: 1rem;
}

.meta label {
  display: block;
  margin: 0.5rem 0 0.25rem;
}

.meta input,
.meta select {
  width: 100%;
  max-width: 100%;
  padding: 0.5rem;
  margin-bottom: 0.5rem;
  box-sizing: border-box;
}

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

/* Responsive tire groups for narrow devices */
@media (max-width: 819px) {
  .tire-groups {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }
}

.tire-group {
  background: #fbfcfe;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 0.5rem;
}

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
  background: linear-gradient(
    to right,
    var(--brand-500) 0%,
    var(--brand-500) var(--slider-progress, 0%),
    #e5e7eb var(--slider-progress, 0%),
    #e5e7eb 100%
  );
}

.difficulty-slider::-moz-range-track {
  background: linear-gradient(
    to right,
    var(--brand-500) 0%,
    var(--brand-500) var(--slider-progress, 0%),
    #e5e7eb var(--slider-progress, 0%),
    #e5e7eb 100%
  );
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
  cursor: pointer;
  user-select: none;
}

.difficulty-mark-wrapper:hover .difficulty-mark {
  background: #f3f4f6;
  border-color: #d1d5db;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.difficulty-mark.active {
  background: var(--brand-50);
  border-color: var(--brand-300);
}

.difficulty-mark-wrapper:hover .difficulty-mark.active {
  background: var(--brand-100);
  border-color: var(--brand-400);
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

/* Mobile difficulty marks - show only numbers */
@media (max-width: 649px) {
  .difficulty-marks {
    gap: 0.25rem;
    width: 100%;
    max-width: 100%;
    justify-content: space-between;
    align-items: center;
  }

  .difficulty-mark {
    min-width: 0;
    padding: 0.25rem 0.125rem;
    margin: 0;
    flex: 1;
    max-width: calc(20% - 0.1rem);
  }

  .difficulty-text {
    display: none;
  }

  .difficulty-number {
    font-size: 0.9rem;
    font-weight: 700;
  }

  .difficulty-mark-wrapper {
    position: relative;
  }
}

/* Difficulty Tooltip Styles */
.difficulty-mark-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 0.5rem;
  border: 2px solid transparent;
  border-radius: 8px;
  background: transparent;
  min-width: 60px;
  cursor: pointer;
  user-select: none;
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
  width: 280px;
  z-index: 99999 !important;
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  white-space: normal;
  word-wrap: break-word;
  text-align: center;
  transform: translateZ(0);
}

.difficulty-mark-wrapper:hover .difficulty-tooltip {
  opacity: 1;
  visibility: visible;
}

/* Mobile tooltip adjustments */
@media (max-width: 649px) {
  .difficulty-mark-wrapper {
    min-width: 0;
    padding: 0.25rem 0.125rem;
    margin: 0;
    flex: 1;
    max-width: calc(20% - 0.1rem);
  }

  .difficulty-tooltip {
    width: 240px;
    font-size: 0.8rem;
    padding: 0.6rem 0.8rem;
  }
}

.tire-group-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: #374151;
  margin: 0 0 0.5rem 0;
}

.tire-group-help {
  margin: 0 0 0.5rem 0;
  font-size: 12px;
  color: #6b7280;
}

.tire-group-header .icon {
  width: 18px;
  text-align: center;
  color: var(--brand-500, #ff6600);
}

.tire-group-title {
  font-size: 0.95rem;
}

.tire-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
  align-items: start;
}

.tire-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 0.5rem;
  cursor: pointer;
  background: #fff;
}

.tire-option input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.tire-option img {
  width: 100%;
  aspect-ratio: 1 / 1;
  object-fit: cover;
  border-radius: 6px;
}

.tire-option .tire-caption {
  font-size: 12px;
  color: #374151;
}

.tire-option.selected {
  border-color: var(--brand-500, #ff6600);
  box-shadow: 0 0 0 2px rgba(255, 102, 0, 0.15);
  background: var(--brand-50);
}

.req {
  color: #dc2626;
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

.video-url-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 0.875rem;
  box-sizing: border-box;
}

.video-url-input:focus {
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
  width: 100%;
  box-sizing: border-box;
}

/* Responsive image upload container */
@media (max-width: 649px) {
  .image-upload-container {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }
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
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  overflow: hidden;
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
  padding: 0.5rem;
  max-width: 100%;
  box-sizing: border-box;
}

.upload-icon {
  font-size: 2rem;
  color: #9ca3af;
}

.upload-text {
  font-weight: 500;
  color: #374151;
  word-wrap: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
}

.upload-hint {
  font-size: 0.875rem;
  color: #6b7280;
  word-wrap: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
}

.card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
  padding: 0.75rem;
  width: 100%;
  box-sizing: border-box;
}
</style>
