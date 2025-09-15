<template>
  <header class="navbar">
    <div class="navbar-container">
      <!-- Brand/Logo Section -->
      <div class="navbar-brand">
        <img :src="logoUrl" alt="Cycling Segments" class="navbar-logo" />
      </div>

      <!-- Navigation Section -->
      <nav class="navbar-nav">
        <div class="language-dropdown" ref="languageDropdown">
          <button
            class="language-dropdown-trigger navbar-trigger"
            @click="toggleLanguageDropdown"
            :class="{ active: languageDropdownOpen }"
          >
            <span class="language-flag">{{
              languageOptions[currentLanguage].flag
            }}</span>
            <span class="language-name">{{
              languageOptions[currentLanguage].name
            }}</span>
            <span class="dropdown-arrow">
              <i
                class="fa-solid fa-chevron-down"
                :class="{ rotated: languageDropdownOpen }"
              ></i>
            </span>
          </button>
          <div
            class="language-dropdown-menu navbar-menu"
            :class="{ open: languageDropdownOpen }"
          >
            <button
              v-for="(option, lang) in languageOptions"
              :key="lang"
              class="language-option"
              :class="{ active: currentLanguage === lang }"
              @click="
                (e) => {
                  e.stopPropagation()
                  changeLanguage(lang as MessageLanguages)
                }
              "
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
    <div
      class="sidebar"
      :class="{ compact: isCompactSidebar, collapsed: isSidebarCollapsed }"
    >
      <div v-if="!isSidebarCollapsed" class="sidebar-scroll">
        <div class="card menu-card">
          <div class="menu-section">
            <div v-if="!isCompactSidebar" class="menu-section-title">
              {{ t('menu.import') }}
            </div>
            <ul class="menu-list">
              <li
                class="menu-item"
                @click="triggerFileOpen"
                :title="isCompactSidebar ? t('menu.gpxFile') : t('tooltip.loadGpxFile')"
                role="button"
              >
                <span class="icon" aria-hidden="true"
                  ><i class="fa-solid fa-file-lines"></i
                ></span>
                <span v-if="!isCompactSidebar" class="text">{{
                  t('menu.gpxFile')
                }}</span>
              </li>
            </ul>
            <input
              ref="fileInput"
              type="file"
              accept=".gpx"
              @change="onFileChange"
              hidden
            />
          </div>

          <div class="menu-section">
            <div v-if="!isCompactSidebar" class="menu-section-title">
              {{ t('menu.segments') }}
            </div>
            <ul class="menu-list">
              <li
                class="menu-item action"
                :class="{ disabled: isSaveDisabled }"
                :aria-disabled="isSaveDisabled"
                :title="
                  isCompactSidebar
                    ? t('menu.saveInDb')
                    : isSaveDisabled
                      ? saveDisabledTitle
                      : t('menu.saveInDb')
                "
                @click="!isSaveDisabled && onSubmit()"
              >
                <span class="icon" aria-hidden="true"
                  ><i class="fa-solid fa-database"></i
                ></span>
                <span v-if="!isCompactSidebar" class="text">{{
                  t('menu.saveInDb')
                }}</span>
              </li>
            </ul>
          </div>

          <!-- Info Feed Section -->
          <div class="menu-section info-feed-section">
            <div v-if="!isCompactSidebar" class="menu-section-title">
              {{ t('menu.infoFeed') }}
            </div>

            <!-- Upload Progress -->
            <div v-if="isUploading" class="info-feed-item upload-progress-item">
              <div class="info-feed-icon">
                <i class="fa-solid fa-upload"></i>
              </div>
              <div v-if="!isCompactSidebar" class="info-feed-content">
                <div class="upload-progress-bar">
                  <div
                    class="upload-progress-fill"
                    :style="{ width: uploadProgress + '%' }"
                  ></div>
                </div>
                <div class="info-feed-text">
                  {{ t('message.uploading') }} {{ Math.round(uploadProgress) }}%
                </div>
              </div>
              <div v-else class="info-feed-content">
                <div class="info-feed-text">{{ Math.round(uploadProgress) }}%</div>
              </div>
            </div>

            <!-- Upload Success -->
            <div v-if="showUploadSuccess" class="info-feed-item upload-success-item">
              <div class="info-feed-icon">
                <i class="fa-solid fa-check-circle"></i>
              </div>
              <div v-if="!isCompactSidebar" class="info-feed-content">
                <div class="info-feed-text">
                  {{ t('message.uploadSuccess') }}
                </div>
              </div>
            </div>

            <!-- Segment Success -->
            <div v-if="showSegmentSuccess" class="info-feed-item upload-success-item">
              <div class="info-feed-icon">
                <i class="fa-solid fa-check-circle"></i>
              </div>
              <div v-if="!isCompactSidebar" class="info-feed-content">
                <div class="info-feed-text">
                  {{ t('message.segmentCreated') }}
                </div>
              </div>
            </div>

            <!-- Error Messages -->
            <div v-if="showError" class="info-feed-item error-item">
              <div class="info-feed-icon">
                <i class="fa-solid fa-exclamation-circle"></i>
              </div>
              <div v-if="!isCompactSidebar" class="info-feed-content">
                <div class="info-feed-text">
                  {{ currentErrorMessage }}
                </div>
              </div>
            </div>

            <!-- Empty State -->
            <div
              v-if="
                !isUploading && !showUploadSuccess && !showSegmentSuccess && !showError
              "
              class="info-feed-item empty-item"
            >
              <div class="info-feed-icon">
                <i class="fa-solid fa-info-circle"></i>
              </div>
              <div v-if="!isCompactSidebar" class="info-feed-content">
                <div class="info-feed-text">
                  {{ t('message.noActivity') }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Collapse/Expand Button - Only visible on compact sidebar -->
      <div v-if="isCompactSidebar" class="sidebar-toggle">
        <button
          @click="toggleSidebarCollapse"
          class="toggle-btn"
          :class="{ collapsed: isSidebarCollapsed }"
          :title="
            isSidebarCollapsed ? t('menu.expandSidebar') : t('menu.collapseSidebar')
          "
        >
          <i
            :class="
              isSidebarCollapsed
                ? 'fa-solid fa-chevron-right'
                : 'fa-solid fa-chevron-left'
            "
          ></i>
        </button>
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
                    <div
                      class="slider-controls"
                      :style="{ top: `-${endSliderOffset}px` }"
                    >
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

            <form class="card meta" @submit.prevent="onSubmit">
              <!-- Track Type Tabs -->
              <div class="track-type-tabs">
                <button
                  type="button"
                  class="tab-button"
                  :class="{ active: trackType === 'segment' }"
                  @click="trackType = 'segment'"
                >
                  <i class="fa-solid fa-route"></i>
                  {{ t('trackType.segment') }}
                </button>
                <button
                  type="button"
                  class="tab-button"
                  :class="{ active: trackType === 'route' }"
                  @click="trackType = 'route'"
                >
                  <i class="fa-solid fa-map"></i>
                  {{ t('trackType.route') }}
                </button>
              </div>

              <div>
                <label for="name"
                  >{{ nameLabel }} <span class="req">{{ t('required') }}</span></label
                >
                <input id="name" v-model="name" type="text" required />
              </div>

              <!-- Trail Conditions Card -->
              <div class="trail-conditions-card">
                <div class="trail-conditions-header">
                  <span class="icon" aria-hidden="true"
                    ><i class="fa-solid fa-mountain"></i
                  ></span>
                  <span class="trail-conditions-title">{{
                    t('form.trailConditions')
                  }}</span>
                </div>

                <!-- Difficulty Level -->
                <div class="trail-subsection">
                  <div class="subsection-header">
                    <span class="icon" aria-hidden="true"
                      ><i class="fa-solid fa-signal"></i
                    ></span>
                    <span class="subsection-title">{{
                      t('form.difficultyLevel')
                    }}</span>
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
                          @click="setDifficultyLevel(i)"
                          :title="t(`difficulty.level${i}`)"
                        >
                          <span class="difficulty-number">{{ i }}</span>
                          <span class="difficulty-text">{{
                            t(`difficulty.level${i}`)
                          }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Surface Type Selection -->
                <div class="trail-subsection">
                  <div class="subsection-header">
                    <span class="icon" aria-hidden="true"
                      ><i class="fa-solid fa-road"></i
                    ></span>
                    <span class="subsection-title">{{ surfaceTypeLabel }}</span>
                  </div>

                  <div class="surface-options">
                    <label
                      v-for="(image, surfaceType) in surfaceImages"
                      :key="surfaceType"
                      class="surface-option"
                      :class="{
                        selected: trailConditions.surface_type === surfaceType
                      }"
                    >
                      <input
                        type="radio"
                        name="surfaceType"
                        :value="surfaceType"
                        v-model="trailConditions.surface_type"
                      />
                      <img :src="image" :alt="t(`surface.${surfaceType}`)" />
                      <span class="surface-caption">{{
                        t(`surface.${surfaceType}`)
                      }}</span>
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
                      <div
                        class="tire-row"
                        role="radiogroup"
                        :aria-label="t('tire.dry')"
                      >
                        <label
                          class="tire-option"
                          :class="{ selected: trailConditions.tire_dry === 'slick' }"
                        >
                          <input
                            type="radio"
                            name="tireDry"
                            value="slick"
                            v-model="trailConditions.tire_dry"
                          />
                          <img :src="tireImages.slick" :alt="t('tire.slick')" />
                          <span class="tire-caption">{{ t('tire.slick') }}</span>
                        </label>
                        <label
                          class="tire-option"
                          :class="{
                            selected: trailConditions.tire_dry === 'semi-slick'
                          }"
                        >
                          <input
                            type="radio"
                            name="tireDry"
                            value="semi-slick"
                            v-model="trailConditions.tire_dry"
                          />
                          <img :src="tireImages.semiSlick" :alt="t('tire.semiSlick')" />
                          <span class="tire-caption">{{ t('tire.semiSlick') }}</span>
                        </label>
                        <label
                          class="tire-option"
                          :class="{ selected: trailConditions.tire_dry === 'knobs' }"
                        >
                          <input
                            type="radio"
                            name="tireDry"
                            value="knobs"
                            v-model="trailConditions.tire_dry"
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
                      <div
                        class="tire-row"
                        role="radiogroup"
                        :aria-label="t('tire.wet')"
                      >
                        <label
                          class="tire-option"
                          :class="{ selected: trailConditions.tire_wet === 'slick' }"
                        >
                          <input
                            type="radio"
                            name="tireWet"
                            value="slick"
                            v-model="trailConditions.tire_wet"
                          />
                          <img :src="tireImages.slick" :alt="t('tire.slick')" />
                          <span class="tire-caption">{{ t('tire.slick') }}</span>
                        </label>
                        <label
                          class="tire-option"
                          :class="{
                            selected: trailConditions.tire_wet === 'semi-slick'
                          }"
                        >
                          <input
                            type="radio"
                            name="tireWet"
                            value="semi-slick"
                            v-model="trailConditions.tire_wet"
                          />
                          <img :src="tireImages.semiSlick" :alt="t('tire.semiSlick')" />
                          <span class="tire-caption">{{ t('tire.semiSlick') }}</span>
                        </label>
                        <label
                          class="tire-option"
                          :class="{ selected: trailConditions.tire_wet === 'knobs' }"
                        >
                          <input
                            type="radio"
                            name="tireWet"
                            value="knobs"
                            v-model="trailConditions.tire_wet"
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
                      v-for="(video, index) in commentary.video_links"
                      :key="video.id"
                      class="video-link-item"
                    >
                      <div class="video-link-content">
                        <div class="video-platform">
                          <i :class="getVideoIcon(video.platform)"></i>
                          <span class="platform-name">{{
                            getPlatformName(video.platform)
                          }}</span>
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
                    <button type="button" @click="addVideoLink" class="add-video-btn">
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
                        <img
                          :src="image.preview"
                          :alt="image.caption || t('form.imageAlt')"
                        />
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
import tireSlickUrl from '../assets/images/slick.png'
import tireSemiSlickUrl from '../assets/images/semi-slick.png'
import tireKnobsUrl from '../assets/images/ext.png'
import bigStoneRoadUrl from '../assets/images/big-stone-road.jpeg'
import brokenPavedRoadUrl from '../assets/images/broken-paved-road.jpeg'
import dirtyRoadUrl from '../assets/images/dirty-road.jpeg'
import fieldTrailUrl from '../assets/images/field-trail.jpeg'
import forestTrailUrl from '../assets/images/forest-trail.jpeg'
import smallStoneRoadUrl from '../assets/images/small-stone-road.jpeg'
import type { Commentary, VideoLink, TrailConditions } from '../types'

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

// type Tire = 'slick' | 'semi-slick' | 'knobs'

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

type TrackPoint = {
  latitude: number
  longitude: number
  elevation: number
  time?: string
}

const { t, locale } = useI18n()
const currentLanguage = ref<MessageLanguages>('en')
watch(
  locale,
  (newLocale) => {
    currentLanguage.value = newLocale as MessageLanguages
  },
  { immediate: true }
)

const languageDropdownOpen = ref(false)
const languageOptions = {
  en: { flag: '🇺🇸', name: 'English' },
  fr: { flag: '🇫🇷', name: 'Français' }
}

const languageDropdown = ref<HTMLElement | null>(null)

function closeLanguageDropdown(event: MouseEvent) {
  if (
    languageDropdown.value &&
    !languageDropdown.value.contains(event.target as Node)
  ) {
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
const trackType = ref<'segment' | 'route'>('segment')
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

// Responsive sidebar state
const isCompactSidebar = ref(false)
const isSidebarCollapsed = ref(false)

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
const showUploadSuccess = ref<boolean>(false)
const showSegmentSuccess = ref<boolean>(false)
const showError = ref<boolean>(false)
const currentErrorMessage = ref<string>('')

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

// Dynamic labels based on track type
const nameLabel = computed(() => {
  return trackType.value === 'segment' ? t('form.segmentName') : t('form.routeName')
})

const surfaceTypeLabel = computed(() => {
  return trackType.value === 'segment'
    ? t('form.surfaceType')
    : t('form.majorSurfaceType')
})

// Difficulty slider progress
const difficultyProgress = computed(() => {
  return ((trailConditions.value.difficulty_level - 1) / 4) * 100
})

// Set difficulty level when clicking on difficulty marks
function setDifficultyLevel(level: number) {
  trailConditions.value.difficulty_level = level
}

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
// const startMin = computed(() => 0)
// const startMax = computed(() => Math.max(1, endIndex.value - 1))
// const endMin = computed(() => Math.min(points.value.length - 1, startIndex.value + 1))
// const endMax = computed(() => points.value.length - 1)
// function toPercent(value: number, min: number, max: number): number {
//   if (max <= min) return 0
//   return ((value - min) / (max - min)) * 100
// }
// const startPercent = computed(() =>
//   toPercent(startIndex.value, startMin.value, startMax.value)
// )
// const endPercent = computed(() => toPercent(endIndex.value, endMin.value, endMax.value))

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
    const startPixelCentered = startPixelInContainer - sliderWidth / 2
    const endPixelCentered = endPixelInContainer - sliderWidth / 2

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
  showError.value = false
  currentErrorMessage.value = ''
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

    // Use points directly from upload response
    const actualPoints: TrackPoint[] = uploadData.points.map((p: any) => ({
      latitude: p.latitude,
      longitude: p.longitude,
      elevation: p.elevation,
      time: p.time
    }))

    if (actualPoints.length < 2) {
      showError.value = true
      currentErrorMessage.value = t('message.insufficientPoints')
      showUploadSuccess.value = false
      showSegmentSuccess.value = false
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

    // Keep progress bar visible for 1 second after completion
    setTimeout(() => {
      isUploading.value = false
      uploadProgress.value = 0
      showUploadSuccess.value = true
      showError.value = false
      currentErrorMessage.value = ''
      showSegmentSuccess.value = false
    }, 1000)

    await nextTick()
    renderMap()
    renderChart()
  } catch (err: any) {
    isUploading.value = false
    uploadProgress.value = 0
    showError.value = true
    currentErrorMessage.value = err.message || t('message.uploadError')
    showUploadSuccess.value = false
    showSegmentSuccess.value = false

    // Hide error after 5 seconds
    setTimeout(() => {
      showError.value = false
      currentErrorMessage.value = ''
    }, 5000)
  }
}

function computeCumulativeKm(pts: TrackPoint[]): number[] {
  const out: number[] = [0]
  for (let i = 1; i < pts.length; i++) {
    const d = haversine(
      pts[i - 1].latitude,
      pts[i - 1].longitude,
      pts[i].latitude,
      pts[i].longitude
    )
    out.push(out[i - 1] + d)
  }
  return out
}

function haversine(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLon = ((lon2 - lon1) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) ** 2
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

function distanceAt(i: number): number {
  return cumulativeKm.value[i] ?? 0
}
function pointAt(i: number): TrackPoint | undefined {
  return points.value[i]
}
function formatKm(km?: number): string {
  return km == null ? '-' : `${km.toFixed(2)} ${t('units.km')}`
}
function formatElevation(ele?: number): string {
  return ele == null ? '-' : `${Math.round(ele)} ${t('units.m')}`
}
function formatElapsed(i: number): string {
  const t0 = points.value[0]?.time
    ? new Date(points.value[0].time as string).getTime()
    : undefined
  const ti = points.value[i]?.time
    ? new Date(points.value[i].time as string).getTime()
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
    const imageFiles = Array.from(files).filter((file) =>
      file.type.startsWith('image/')
    )
    processImageFiles(imageFiles)
  }
}

function processImageFiles(files: File[]) {
  files.forEach((file) => {
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
  const latlngs = points.value.map((p) => [p.latitude, p.longitude]) as [
    number,
    number
  ][]
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
  const segLatLngs = points.value
    .slice(startIndex.value, endIndex.value + 1)
    .map((p) => [p.latitude, p.longitude]) as [number, number][]
  if (selectedLine) selectedLine.remove()
  selectedLine = L.polyline(segLatLngs, {
    color:
      getComputedStyle(document.documentElement)
        .getPropertyValue('--brand-500')
        .trim() || '#ff6600',
    weight: 5
  })
  selectedLine.addTo(map)
}

function renderChart() {
  if (!chartCanvas.value) return
  const ctx = chartCanvas.value.getContext('2d')!
  const labels = points.value.map((_, i) => i)
  // const data = buildXYData()
  const fullData = buildFullXYData()

  chart?.destroy()
  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: t('chart.elevation'),
          data: fullData.map((d) => ({ x: d.x, y: d.y })),
          borderColor:
            getComputedStyle(document.documentElement)
              .getPropertyValue('--brand-500')
              .trim() || '#ff6600',
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
          filter: function (tooltipItem) {
            return tooltipItem.datasetIndex === 0
          },
          callbacks: {
            title: function (context) {
              // const dataIndex = context[0].dataIndex
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
      onClick: (event) => {
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
      const startPixelCentered = startPixelInContainer - sliderWidth / 2
      const endPixelCentered = endPixelInContainer - sliderWidth / 2

      startSliderPosition.value = (startPixelCentered / containerRect.width) * 100
      endSliderPosition.value = (endPixelCentered / containerRect.width) * 100
      checkSliderOverlap()
    }
  })
}

function getX(i: number): number {
  return xMode.value === 'distance'
    ? (cumulativeKm.value[i] ?? 0)
    : (cumulativeSec.value[i] ?? 0)
}

// function buildXYData(): { x: number; y: number }[] {
//   return points.value.map((p, i) => ({
//     x: getX(i),
//     y: smoothedElevations.value[i] ?? p.elevation
//   }))
// }

function buildFullXYData(): { x: number; y: number }[] {
  return points.value.map((p, i) => ({
    x: getX(i),
    y: smoothedElevations.value[i] ?? p.elevation
  }))
}

function buildSelectedAreaData(): { x: number; y: number }[] {
  const selectedData = []

  for (let i = startIndex.value; i <= endIndex.value; i++) {
    selectedData.push({
      x: getX(i),
      y: smoothedElevations.value[i] ?? points.value[i]?.elevation ?? 0
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
    const t0 = pts[i - 1].time
      ? new Date(pts[i - 1].time as string).getTime()
      : undefined
    const t1 = pts[i].time ? new Date(pts[i].time as string).getTime() : undefined
    const d = t0 && t1 ? Math.max(0, (t1 - t0) / 1000) : 1
    out.push(out[i - 1] + d)
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
      sum += pts[j].elevation
      count += 1
    }
    out[i] = count ? sum / count : pts[i].elevation
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
    const segLatLngs = points.value
      .slice(startIndex.value, endIndex.value + 1)
      .map((p) => [p.latitude, p.longitude]) as [number, number][]
    const segBounds = L.latLngBounds(segLatLngs)
    map.fitBounds(segBounds, { padding: [20, 20] })
  }
})

watch(xMode, () => {
  if (!chart) return
  const fullData = buildFullXYData()
  // @ts-ignore
  chart.data.datasets[0].data = fullData.map((d) => ({ x: d.x, y: d.y }))
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
      const startPixelCentered = startPixelInContainer - sliderWidth / 2
      const endPixelCentered = endPixelInContainer - sliderWidth / 2

      startSliderPosition.value = (startPixelCentered / containerRect.width) * 100
      endSliderPosition.value = (endPixelCentered / containerRect.width) * 100
      checkSliderOverlap()
    }
  })
})

watch(loaded, async () => {
  await nextTick()
})

// Function to check if sidebar should be compact
function checkSidebarMode() {
  isCompactSidebar.value = window.innerWidth < 1100
}

// Function to toggle sidebar collapse
function toggleSidebarCollapse() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}

onMounted(() => {
  // Check initial sidebar mode
  checkSidebarMode()

  const onResize = () => {
    if (map) {
      setTimeout(() => map!.invalidateSize(), 0)
    }
    // Check sidebar mode on resize
    checkSidebarMode()
  }
  window.addEventListener('resize', onResize)
  ;(window as any).__editorOnResize = onResize
})

onUnmounted(() => {
  const onResize = (window as any).__editorOnResize
  if (onResize) window.removeEventListener('resize', onResize)
})

// function escapeXml(s: string): string {
//   return s.replace(
//     /[<>&"']/g,
//     (c) =>
//       ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&apos;' })[
//         c
//       ] as string
//   )
// }

async function onSubmit() {
  if (!loaded.value || points.value.length < 2 || !uploadedFileId.value) {
    showError.value = true
    currentErrorMessage.value = t('message.loadGpxFirst')
    showUploadSuccess.value = false
    showSegmentSuccess.value = false
    return
  }
  submitting.value = true
  showError.value = false
  currentErrorMessage.value = ''
  message.value = ''
  try {
    const formData = new FormData()
    formData.append('name', name.value)
    formData.append('track_type', trackType.value)
    formData.append('tire_dry', trailConditions.value.tire_dry)
    formData.append('tire_wet', trailConditions.value.tire_wet)
    formData.append('surface_type', trailConditions.value.surface_type)
    formData.append(
      'difficulty_level',
      trailConditions.value.difficulty_level.toString()
    )

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

    // Reset only form fields to original state
    name.value = ''
    trailConditions.value = {
      tire_dry: 'slick',
      tire_wet: 'slick',
      surface_type: 'forest-trail',
      difficulty_level: 3
    }
    commentary.value = { text: '', video_links: [], images: [] }

    // Reset selection markers to start and end of file (preserve loaded state)
    startIndex.value = 0
    endIndex.value = points.value.length - 1

    // Update map and chart with new selection
    await nextTick()
    renderMap()
    renderChart()

    // Show success message in info feed
    showSegmentSuccess.value = true
    showError.value = false
    currentErrorMessage.value = ''
    showUploadSuccess.value = false
  } catch (err: any) {
    showError.value = true
    currentErrorMessage.value = err.message || t('message.createError')
    showUploadSuccess.value = false
    showSegmentSuccess.value = false

    // Hide error after 5 seconds
    setTimeout(() => {
      showError.value = false
      currentErrorMessage.value = ''
    }, 5000)
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
.editor {
  display: flex;
  min-height: 100vh;
  background: #f8fafc;
  overflow-x: hidden;
  position: relative;
}
.content {
  flex: 1 1 auto;
  padding: 1rem 1.5rem;
  width: 100%;
  box-sizing: border-box;
  overflow-x: hidden;
  margin-left: var(--sidebar-w, 230px);
  transition: margin-left 0.3s ease;
}
.page {
  max-width: 1000px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
  overflow-x: hidden;
}
.main-col {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  min-width: 0;
  overflow: hidden;
}

.sidebar {
  --sidebar-w: 230px;
  --sidebar-w-compact: 120px;
  width: var(--sidebar-w);
  background: transparent;
  border-right: none;
  padding: 0;
  margin: 0;
  box-sizing: border-box;
  position: fixed;
  top: var(--navbar-height, 64px);
  left: calc(50% - 500px - var(--sidebar-w));
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--navbar-height, 64px));
  z-index: 100;
  transition:
    left 0.3s ease,
    width 0.3s ease;
}

.sidebar.compact {
  --sidebar-w: var(--sidebar-w-compact);
  width: var(--sidebar-w-compact);
}

.sidebar.collapsed {
  --sidebar-w: 50px;
  width: 50px;
}
.sidebar-scroll {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.75rem;
  max-height: calc(100vh - var(--navbar-height, 56px));
  overflow-y: auto;
  overflow-x: hidden;
  padding: 1rem;
}
.sidebar .card {
  margin: 0;
  width: 100%;
  box-sizing: border-box;
}

.menu-card {
  padding: 0.5rem 0;
  position: sticky;
  top: 0;
  background: #ffffff;
  z-index: 10;
}
.menu-section {
  margin-top: 0.5rem;
}
.menu-section + .menu-section {
  margin-top: 0.25rem;
  padding-top: 0.25rem;
  border-top: 1px solid #f1f5f9;
}
.menu-section-title {
  margin: 0.25rem 0 0.25rem;
  padding: 0 0.75rem;
  font-size: 1rem;
  font-weight: 400;
  color: #6b7280;
  text-align: left;
}
.menu-list {
  list-style: none;
  margin: 0;
  padding: 0.1rem 0.25rem 0.25rem;
}
.menu-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.4rem 0.6rem 0.4rem 0.75rem;
  margin: 0.1rem 0.35rem;
  border-radius: 8px;
  cursor: pointer;
  color: #111827;
  user-select: none;
}
.menu-item .icon {
  width: 20px;
  text-align: center;
  opacity: 0.9;
}
.menu-item .text {
  font-size: 0.8rem;
}
.menu-item:hover {
  background: #f3f4f6;
}
.menu-item:active {
  background: #e5e7eb;
}
.menu-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: transparent;
}
.menu-item.disabled:hover {
  background: transparent;
}
.menu-item.active {
  background: var(--brand-50);
  color: var(--brand-600);
  font-weight: 500;
}
.menu-item.active:hover {
  background: var(--brand-100);
}

/* Compact sidebar styles */
.sidebar.compact .menu-item {
  justify-content: center;
  padding: 0.5rem;
  margin: 0.1rem 0.25rem;
  min-height: 36px;
  aspect-ratio: 1;
}

.sidebar.compact .menu-item .icon {
  width: 20px;
  text-align: center;
  opacity: 0.9;
}

.sidebar.compact .menu-item .text {
  display: none;
}

.sidebar.compact .menu-section {
  margin-top: 0.25rem;
}

.sidebar.compact .menu-section + .menu-section {
  margin-top: 0.1rem;
  padding-top: 0.1rem;
}

.sidebar.compact .menu-section-title {
  display: none;
}

.sidebar.compact .menu-list {
  padding: 0.1rem 0;
}

.sidebar.compact .info-feed-item {
  justify-content: center;
  padding: 0.5rem;
  margin: 0.1rem 0.25rem;
  min-height: 36px;
  aspect-ratio: 1;
}

.sidebar.compact .info-feed-content {
  display: none;
}

.sidebar.compact .info-feed-icon {
  font-size: 1.2rem;
}

/* Sidebar Toggle Button - Only visible on compact sidebar */
.sidebar-toggle {
  position: absolute;
  bottom: 0.75rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 20;
}

.toggle-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  background: var(--brand-500);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

.toggle-btn:hover {
  background: var(--brand-600);
  transform: scale(1.05);
}

.toggle-btn:active {
  transform: scale(0.95);
}

/* Collapsed sidebar styles */
.sidebar.collapsed .sidebar-scroll {
  display: none;
}

.sidebar.collapsed {
  --sidebar-w: 40px;
  width: 40px;
  z-index: 1000;
}

.sidebar.collapsed .sidebar-toggle {
  position: fixed;
  top: 50%;
  left: 0;
  transform: translateY(-50%);
  z-index: 1001;
}

.sidebar.collapsed .toggle-btn {
  width: 40px;
  height: 40px;
  border-radius: 0 8px 8px 0;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

/* Content adjustment for collapsed sidebar */
.sidebar.collapsed + .content {
  margin-left: 0;
  max-width: 100%;
}

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

.card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
  padding: 0.75rem;
  width: 100%;
  box-sizing: border-box;
}
.card-map {
  padding: 0;
  overflow: hidden;
}
.card-elevation {
  padding: 0.75rem;
  overflow: visible;
  margin-top: 1rem;
  margin-bottom: 1rem;
}
.map {
  height: 480px;
  width: 100%;
}
.axis-toggle {
  display: inline-flex;
  gap: 0;
  margin: 0.25rem auto 0.25rem;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  overflow: hidden;
  background: #fff;
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
  color: #374151;
}
.axis-toggle .seg.left {
  border-right: 1px solid #e5e7eb;
}
.axis-toggle .seg.active {
  background: #f3f4f6;
  color: #111827;
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
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }
}
.controls .meta-title {
  grid-column: 1 / -1;
  text-align: center;
  margin: 0 0 0.5rem 0;
}
.slider-group {
  background: #fafafa;
  padding: 0.75rem;
  border: 1px solid #eee;
  border-radius: 8px;
  width: 100%;
  box-sizing: border-box;
  overflow: hidden;
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
  color: #374151;
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
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
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
  color: #374151;
}
.gps-col .label {
  font-size: 12px;
  color: #6b7280;
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
.meta {
  background: #ffffff;
  width: 100%;
  margin-top: 1rem;
  margin-bottom: 1rem;
  display: block;
}

/* Track Type Tabs */
.track-type-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  padding: 0.5rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.tab-button {
  flex: 1;
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
.meta-title {
  text-align: center;
  margin: 0 0 0.75rem 0;
  font-size: 1rem;
  font-weight: 700;
  color: #111827;
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

.difficulty-mark:hover {
  background: #f3f4f6;
  border-color: #d1d5db;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.difficulty-mark.active {
  background: var(--brand-50);
  border-color: var(--brand-300);
}

.difficulty-mark.active:hover {
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
  }

  .difficulty-mark {
    min-width: 28px;
    padding: 0.25rem 0.125rem;
    margin: 0;
  }

  .difficulty-text {
    display: none;
  }

  .difficulty-number {
    font-size: 0.9rem;
    font-weight: 700;
  }

  .difficulty-mark:hover .difficulty-text {
    display: block;
    position: absolute;
    bottom: -20px;
    left: 50%;
    transform: translateX(-50%);
    background: #1f2937;
    color: white;
    padding: 0.2rem 0.4rem;
    border-radius: 3px;
    font-size: 0.65rem;
    white-space: nowrap;
    z-index: 1000;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }

  .difficulty-mark {
    position: relative;
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
.section-indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
  color: #374151;
  padding: 0 0.25rem;
  margin-top: 0.5rem;
}
.section-indicator .icon {
  width: 18px;
  text-align: center;
}
.empty {
  padding: 2rem;
  text-align: center;
  color: #666;
}
.message {
  margin-top: 1rem;
}

/* Info Feed Styles - Integrated in Menu */
.info-feed-section {
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid #f1f5f9;
}

.info-feed-item {
  padding: 0.75rem;
  border-radius: 6px;
  margin: 0 0.25rem 0.5rem 0.25rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
}

.info-feed-icon {
  font-size: 1rem;
  flex-shrink: 0;
}

.info-feed-content {
  flex: 1;
  min-width: 0;
}

.info-feed-text {
  font-size: 0.75rem;
  font-weight: 500;
  line-height: 1.2;
}

/* Upload Progress Item */
.upload-progress-item {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.upload-progress-item .info-feed-icon {
  color: #ff6600;
}

.upload-progress-item .info-feed-text {
  color: #475569;
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

/* Success Item */
.success-item {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
}

.success-item .info-feed-icon {
  color: #16a34a;
}

.success-item .info-feed-text {
  color: #15803d;
}

/* Upload Success Item (Blue) */
.upload-success-item {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
}

.upload-success-item .info-feed-icon {
  color: #2563eb;
}

.upload-success-item .info-feed-text {
  color: #1d4ed8;
}

/* Error Item */
.error-item {
  background: #fef2f2;
  border: 1px solid #fecaca;
}

.error-item .info-feed-icon {
  color: #dc2626;
}

.error-item .info-feed-text {
  color: #b91c1c;
}

/* Empty Item */
.empty-item {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.empty-item .info-feed-icon {
  color: #64748b;
}

.empty-item .info-feed-text {
  color: #64748b;
}

/* Responsive breakpoints following Bootstrap conventions */
@media (max-width: 1200px) {
  .navbar-container {
    max-width: 100%;
    padding: 0.75rem 1.25rem;
  }
}

@media (max-width: 992px) {
  .navbar-container {
    padding: 0.75rem 1rem;
  }

  .navbar-logo {
    max-width: 180px;
  }
}

@media (max-width: 768px) {
  .navbar-container {
    padding: 0.75rem 0.75rem;
  }

  .navbar-logo {
    max-width: 150px;
    height: 28px;
  }

  .navbar-nav .language-dropdown-trigger.navbar-trigger {
    padding: 0.4rem 0.6rem;
    font-size: 0.85rem;
  }
}

@media (max-width: 576px) {
  .navbar-container {
    padding: 0.75rem 0.75rem;
  }

  .navbar-logo {
    max-width: 120px;
    height: 24px;
  }

  .navbar-nav .language-dropdown-trigger.navbar-trigger {
    padding: 0.3rem 0.5rem;
    font-size: 0.8rem;
  }

  .language-name {
    display: none;
  }
}

@media (max-width: 480px) {
  .navbar-logo {
    max-width: 100px;
    height: 22px;
  }
}

/* Responsive content to ensure sidebar visibility */
@media (max-width: 1450px) {
  .content {
    margin-left: 210px;
    max-width: calc(100% - 210px);
  }

  .sidebar {
    left: 0;
  }
}

/* Compact sidebar for screens under 1100px */
@media (max-width: 1099px) {
  .sidebar {
    --sidebar-w: 120px;
    width: 120px;
  }

  .content {
    margin-left: 100px;
    max-width: calc(100% - 100px);
  }

  .sidebar.collapsed {
    --sidebar-w: 40px;
    width: 40px;
  }

  .sidebar.collapsed + .content {
    margin-left: 0;
    max-width: 100%;
  }
}

/* Hide toggle button on larger screens */
@media (min-width: 1100px) {
  .sidebar-toggle {
    display: none;
  }
}

/* For very large screens, ensure sidebar is positioned relative to content */
@media (min-width: 1451px) {
  .sidebar {
    left: calc(50% - 500px - 230px);
  }

  .content {
    margin-left: 0;
  }
}

/* Bootstrap-style navbar */
:root {
  --navbar-height: 64px;
}

.navbar {
  position: sticky;
  top: 0;
  z-index: 9999;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  box-shadow:
    0 1px 3px 0 rgba(0, 0, 0, 0.1),
    0 1px 2px 0 rgba(0, 0, 0, 0.06);
  min-height: var(--navbar-height);
}

.navbar-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0.75rem 1.5rem;
  min-height: var(--navbar-height);
  box-sizing: border-box;
}

.navbar-brand {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  margin-right: 1rem;
}

.navbar-logo {
  height: 32px;
  width: auto;
  max-width: 200px;
  object-fit: contain;
  display: block;
}

.navbar-nav {
  display: flex;
  align-items: center;
  margin-left: auto;
}

.nav .language-dropdown {
  position: relative;
}

.navbar-nav .language-dropdown-trigger.navbar-trigger {
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

.navbar-nav .language-dropdown-trigger.navbar-trigger:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

.navbar-nav .language-dropdown-trigger.navbar-trigger.active {
  background: var(--brand-50);
  border-color: var(--brand-300);
  color: var(--brand-600);
  box-shadow: 0 0 0 3px rgba(255, 102, 0, 0.1);
}

.navbar-menu {
  position: absolute;
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

.navbar-nav .language-dropdown-menu.navbar-menu {
  top: 100%;
  right: 0;
  left: auto;
}

.navbar-nav .language-dropdown-menu.navbar-menu.open {
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
</style>
