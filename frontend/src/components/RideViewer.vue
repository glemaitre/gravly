<template>
  <div class="ride-viewer">
    <div v-if="loading" class="loading">
      <div class="loading-spinner"></div>
      <p>Loading ride data...</p>
    </div>

    <div v-else-if="ride" class="ride-content">
      <div class="ride-header">
        <button @click="$router.push('/')" class="back-btn">
          <i class="fa-solid fa-arrow-left" aria-hidden="true"></i> Back to Search
        </button>
        <h1 class="ride-title">{{ ride.name }}</h1>
        <div class="ride-summary">
          <div class="summary-item">
            <span class="summary-label">Distance</span>
            <span class="summary-value">{{ formatDistance(ride.total_distance) }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">Elevation Gain</span>
            <span class="summary-value">{{ formatElevation(ride.total_elevation_gain) }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">Elevation Loss</span>
            <span class="summary-value">{{ formatElevation(ride.total_elevation_loss) }}</span>
          </div>
        </div>
      </div>

      <div class="viewer-container">
        <div class="map-section">
          <div id="main-map" class="main-map"></div>
          <div class="map-info">
            <p class="interaction-hint">Hover over the elevation profile to see the location on the map</p>
          </div>
        </div>

        <div class="elevation-section">
          <h3>Elevation Profile</h3>
          <div class="elevation-chart-container">
            <canvas ref="elevationChart" class="elevation-chart"></canvas>
          </div>
          <div class="elevation-info">
            <div class="elevation-stats">
              <div class="elevation-stat">
                <span class="stat-label">Max Elevation</span>
                <span class="stat-value">{{ formatElevation(maxElevation) }}</span>
              </div>
              <div class="elevation-stat">
                <span class="stat-label">Min Elevation</span>
                <span class="stat-value">{{ formatElevation(minElevation) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="error">
      <h2>Ride not found</h2>
      <p>The requested ride could not be found.</p>
      <button @click="$router.push('/')" class="back-btn">Back to Search</button>
    </div>
  </div>
</template>

<script lang="ts">
import L, { Map as LeafletMap, LayerGroup } from 'leaflet'
import axios from 'axios'
import { Chart, registerables } from 'chart.js'
import type { GPXTrack } from '../types'

Chart.register(...registerables)

export default {
  name: 'RideViewer',
  props: {
    id: String
  },
  data() {
    return {
      ride: null as GPXTrack | null,
      loading: true as boolean,
      map: null as LeafletMap | null,
      routeLayer: null as LayerGroup | null,
      markerLayer: null as LayerGroup | null,
      elevationChart: null as Chart | null,
      maxElevation: 0 as number,
      minElevation: 0 as number,
      currentPositionMarker: null as L.Marker | null
    }
  },
  async mounted() {
    await this.loadRide()
    if (this.ride) {
      this.initMap()
      this.initElevationChart()
    }
  },
  methods: {
    async loadRide(): Promise<void> {
      try {
        const response = await axios.get<GPXTrack>(`/api/rides/${this.id}`)
        this.ride = response.data as GPXTrack

        // Calculate elevation stats
        const elevations = this.ride.points.map(p => p.elevation)
        this.maxElevation = Math.max(...elevations)
        this.minElevation = Math.min(...elevations)
      } catch (error) {
        console.error('Error loading ride:', error)
        this.ride = null
      } finally {
        this.loading = false
      }
    },

    initMap(): void {
      if (!this.ride) return

      // Calculate center and bounds
      const lats = this.ride.points.map(p => p.lat)
      const lons = this.ride.points.map(p => p.lon)
      const centerLat = (Math.max(...lats) + Math.min(...lats)) / 2
      const centerLon = (Math.max(...lons) + Math.min(...lons)) / 2

      this.map = L.map('main-map').setView([centerLat, centerLon], 13)

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
      }).addTo(this.map)

      // Add cycle layer (commented out - requires API key)
      // L.tileLayer('https://tile.thunderforest.com/cycle/{z}/{x}/{y}.png?apikey=YOUR_API_KEY', {
      //   attribution: '© Thunderforest, © OpenStreetMap contributors'
      // }).addTo(this.map)

      // Create route layer
      this.routeLayer = L.layerGroup().addTo(this.map)
      this.markerLayer = L.layerGroup().addTo(this.map)

      // Draw the route
      this.drawRoute()

      // Fit map to route bounds
      const bounds = L.latLngBounds(
        [Math.min(...lats), Math.min(...lons)],
        [Math.max(...lats), Math.max(...lons)]
      )
      this.map.fitBounds(bounds, { padding: [20, 20] })
    },

    drawRoute(): void {
      if (!this.ride || !this.routeLayer) return

      // Clear existing route
      this.routeLayer.clearLayers()
      this.markerLayer.clearLayers()

      // Create polyline for the route
      const routePoints = this.ride.points.map(p => [p.lat, p.lon])
      const brand = getComputedStyle(document.documentElement).getPropertyValue('--brand-500').trim() || '#ff6600'
      const route = L.polyline(routePoints, {
        color: brand,
        weight: 4,
        opacity: 0.85
      })

      this.routeLayer.addLayer(route)

      // Add start and end markers
      const startPoint = this.ride.points[0]
      const endPoint = this.ride.points[this.ride.points.length - 1]

      const startMarker = L.marker([startPoint.lat, startPoint.lon], {
        icon: L.divIcon({
          className: 'start-marker',
          html: '<i class="fa-solid fa-flag-checkered"></i>',
          iconSize: [30, 30]
        })
      })

      const endMarker = L.marker([endPoint.lat, endPoint.lon], {
        icon: L.divIcon({
          className: 'end-marker',
          html: '<i class="fa-solid fa-trophy"></i>',
          iconSize: [30, 30]
        })
      })

      this.markerLayer.addLayer(startMarker)
      this.markerLayer.addLayer(endMarker)
    },

    initElevationChart(): void {
      if (!this.ride) return

      const canvas = this.$refs.elevationChart as HTMLCanvasElement
      const ctx = canvas.getContext('2d') as CanvasRenderingContext2D

      // Calculate cumulative distance
      let cumulativeDistance = 0
      const distances = [0]
      const elevations = [this.ride.points[0].elevation]

      for (let i = 1; i < this.ride.points.length; i++) {
        const p1 = this.ride.points[i - 1]
        const p2 = this.ride.points[i]

        // Calculate distance between points
        const distance = this.calculateDistance(p1.lat, p1.lon, p2.lat, p2.lon)
        cumulativeDistance += distance
        distances.push(cumulativeDistance)
        elevations.push(p2.elevation)
      }

      this.elevationChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: distances.map(d => `${d.toFixed(1)}km`),
          datasets: [{
            label: 'Elevation',
            data: elevations,
            borderColor: getComputedStyle(document.documentElement).getPropertyValue('--brand-500').trim() || '#ff6600',
            backgroundColor: 'rgba(255, 102, 0, 0.12)',
            fill: true,
            tension: 0.1,
            pointRadius: 0,
            pointHoverRadius: 5
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: {
            intersect: false,
            mode: 'index'
          },
          onHover: (_event: unknown, elements: any[]) => {
            if (elements.length > 0) {
              const index = elements[0].index
              this.updateMapPosition(index)
            }
          },
          onClick: (_event: unknown, elements: any[]) => {
            if (elements.length > 0) {
              const index = elements[0].index
              this.updateMapPosition(index)
              // Highlight the clicked point
              if (this.elevationChart) {
                this.elevationChart.setActiveElements([{ datasetIndex: 0, index }])
                this.elevationChart.update('none')
              }
            }
          },
          scales: {
            x: {
              title: {
                display: true,
                text: 'Distance (km)'
              }
            },
            y: {
              title: {
                display: true,
                text: 'Elevation (m)'
              }
            }
          },
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              callbacks: {
                title: (context: any) => {
                  const index = context[0].dataIndex as number
                  const point = this.ride.points[index]
                  return `Distance: ${context[0].label} | Elevation: ${point.elevation}m`
                },
                label: (context: any) => {
                  const index = context.dataIndex as number
                  const point = this.ride.points[index]
                  return `Lat: ${point.lat.toFixed(6)}, Lon: ${point.lon.toFixed(6)}`
                }
              }
            }
          }
        }
      })
    },

    updateMapPosition(index: number): void {
      if (!this.ride || !this.map || index >= this.ride.points.length) return

      const point = this.ride.points[index]

      // Remove existing position marker
      if (this.currentPositionMarker) {
        this.markerLayer.removeLayer(this.currentPositionMarker)
      }

      // Add new position marker
      this.currentPositionMarker = L.marker([point.lat, point.lon], {
        icon: L.divIcon({
          className: 'position-marker',
          html: '<i class="fa-solid fa-location-dot"></i>',
          iconSize: [25, 25]
        })
      })

      this.markerLayer.addLayer(this.currentPositionMarker)

      // Smoothly pan to current position
      this.map.panTo([point.lat, point.lon])
    },


    calculateDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
      const R = 6371 // Earth's radius in km
      const dLat = (lat2 - lat1) * Math.PI / 180
      const dLon = (lon2 - lon1) * Math.PI / 180
      const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                Math.sin(dLon/2) * Math.sin(dLon/2)
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
      return R * c
    },

    formatDistance(distance: number): string {
      if (distance < 1) {
        return `${Math.round(distance * 1000)}m`
      }
      return `${distance.toFixed(1)}km`
    },

    formatElevation(elevation: number): string {
      return `${Math.round(elevation)}m`
    }
  }
}
</script>

<style scoped>
.ride-viewer {
  min-height: 100vh;
  background: var(--brand-bg);
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  color: white;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top: 4px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.ride-content {
  padding: 2rem;
}

.ride-header {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.back-btn {
  background: rgba(255, 102, 0, 0.12);
  color: #4a5568;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  margin-bottom: 1rem;
  transition: all 0.2s;
}

.back-btn:hover {
  background: rgba(255, 102, 0, 0.2);
}

.ride-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin: 0 0 1.5rem 0;
  color: #2d3748;
}

.ride-summary {
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
  background: #f7fafc;
  border-radius: 12px;
  min-width: 120px;
}

.summary-label {
  font-size: 0.875rem;
  color: #718096;
  margin-bottom: 0.5rem;
}

.summary-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2d3748;
}

.viewer-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  height: 600px;
}

.map-section {
  background: white;
  border-radius: 16px;
  padding: 1rem;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  position: relative;
}

.main-map {
  width: 100%;
  height: calc(100% - 40px);
  border-radius: 12px;
  overflow: hidden;
}

.map-info {
  position: absolute;
  bottom: 1rem;
  left: 1rem;
  right: 1rem;
  text-align: center;
}

.interaction-hint {
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  margin: 0;
  backdrop-filter: blur(4px);
}

.elevation-section {
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.elevation-section h3 {
  margin: 0 0 1rem 0;
  color: #2d3748;
  font-size: 1.25rem;
}

.elevation-chart-container {
  height: 300px;
  margin-bottom: 1rem;
}

.elevation-chart {
  width: 100%;
  height: 100%;
}

.elevation-info {
  border-top: 1px solid #e2e8f0;
  padding-top: 1rem;
}

.elevation-stats {
  display: flex;
  gap: 2rem;
}

.elevation-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-label {
  font-size: 0.875rem;
  color: #718096;
  margin-bottom: 0.25rem;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #2d3748;
}

.error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  color: white;
  text-align: center;
}

.error h2 {
  font-size: 2rem;
  margin: 0 0 1rem 0;
}

.error p {
  font-size: 1.25rem;
  margin: 0 0 2rem 0;
  opacity: 0.8;
}

@media (max-width: 768px) {
  .viewer-container {
    grid-template-columns: 1fr;
    height: auto;
  }

  .ride-summary {
    justify-content: center;
  }

  .elevation-stats {
    justify-content: center;
  }
}
</style>
