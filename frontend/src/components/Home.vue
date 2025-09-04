<template>
  <div class="home">
    <div class="hero-section">
      <h1 class="hero-title">Discover Amazing Cycling Routes</h1>
      <p class="hero-subtitle">Explore GPX tracks from cyclists around the world</p>
    </div>

    <div class="search-section">
      <div class="map-container">
        <div id="search-map" class="map"></div>
        <div class="map-controls">
          <button @click="searchRides" class="search-btn" :disabled="loading">
            {{ loading ? 'Searching...' : 'Search in this area' }}
          </button>
        </div>
      </div>
    </div>

    <div class="results-section">
      <div class="container">
        <h2 v-if="rides.length > 0" class="results-title">
          Found {{ rides.length }} ride{{ rides.length !== 1 ? 's' : '' }}
        </h2>

        <div class="rides-grid">
          <div
            v-for="ride in rides"
            :key="ride.id"
            class="ride-card"
            @click="viewRide(ride.id)"
          >
            <div class="ride-card-map">
              <div :id="`mini-map-${ride.id}`" class="mini-map"></div>
            </div>
            <div class="ride-card-content">
              <h3 class="ride-name">{{ ride.name }}</h3>
              <div class="ride-stats">
                <div class="stat">
                  <span class="stat-icon">📏</span>
                  <span class="stat-value">{{ formatDistance(ride.distance) }}</span>
                </div>
                <div class="stat">
                  <span class="stat-icon">⛰️</span>
                  <span class="stat-value">{{ formatElevation(ride.elevation_gain) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="rides.length === 0 && !loading" class="no-results">
          <p>No rides found in this area. Try searching a different region!</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import L from 'leaflet'
import axios from 'axios'

export default {
  name: 'Home',
  data() {
    return {
      map: null,
      rides: [],
      loading: false,
      searchBounds: null,
      rideLayers: null
    }
  },
  mounted() {
    this.initMap()
    this.loadAllRides()
  },
  methods: {
    initMap() {
      // Initialize the search map
      this.map = L.map('search-map').setView([46.5197, 6.6323], 6) // Center on Switzerland

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
      }).addTo(this.map)

      // Add cycle layer (commented out - requires API key)
      // L.tileLayer('https://tile.thunderforest.com/cycle/{z}/{x}/{y}.png?apikey=YOUR_API_KEY', {
      //   attribution: '© Thunderforest, © OpenStreetMap contributors'
      // }).addTo(this.map)

      // Create layer group for ride paths
      this.rideLayers = L.layerGroup().addTo(this.map)

      // Track map bounds changes
      this.map.on('moveend', () => {
        this.searchBounds = this.map.getBounds()
      })
    },

    async loadAllRides() {
      try {
        this.loading = true
        const response = await axios.get('/api/rides')
        this.rides = response.data
        this.$nextTick(() => {
          this.createMiniMaps()
          this.drawRidePathsOnSearchMap()
        })
      } catch (error) {
        console.error('Error loading rides:', error)
      } finally {
        this.loading = false
      }
    },

    async searchRides() {
      if (!this.searchBounds) return

      try {
        this.loading = true
        const bounds = {
          north: this.searchBounds.getNorth(),
          south: this.searchBounds.getSouth(),
          east: this.searchBounds.getEast(),
          west: this.searchBounds.getWest()
        }

        const response = await axios.get('/api/rides', {
          params: { bounds: JSON.stringify(bounds) }
        })
        this.rides = response.data
        this.$nextTick(() => {
          this.createMiniMaps()
          this.drawRidePathsOnSearchMap()
        })
      } catch (error) {
        console.error('Error searching rides:', error)
      } finally {
        this.loading = false
      }
    },

    createMiniMaps() {
      this.rides.forEach(ride => {
        const mapElement = document.getElementById(`mini-map-${ride.id}`)
        if (mapElement && !mapElement.hasChildNodes()) {
          const miniMap = L.map(`mini-map-${ride.id}`, {
            zoomControl: false,
            dragging: false,
            touchZoom: false,
            doubleClickZoom: false,
            scrollWheelZoom: false
          }).setView([(ride.bounds.north + ride.bounds.south) / 2, (ride.bounds.east + ride.bounds.west) / 2], 10)

          L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: ''
          }).addTo(miniMap)

          // Add GPX route path if points are available
          if (ride.points && ride.points.length > 0) {
            const routePoints = ride.points.map(point => [point.lat, point.lon])
            const route = L.polyline(routePoints, {
              color: '#3b82f6',
              weight: 3,
              opacity: 0.8
            }).addTo(miniMap)

            // Add start and end markers
            if (routePoints.length > 0) {
              const startPoint = routePoints[0]
              const endPoint = routePoints[routePoints.length - 1]

              L.marker(startPoint, {
                icon: L.divIcon({
                  className: 'start-marker',
                  html: '🏁',
                  iconSize: [20, 20]
                })
              }).addTo(miniMap)

              L.marker(endPoint, {
                icon: L.divIcon({
                  className: 'end-marker',
                  html: '🏆',
                  iconSize: [20, 20]
                })
              }).addTo(miniMap)
            }

            // Fit map to route bounds
            const bounds = L.latLngBounds(routePoints)
            miniMap.fitBounds(bounds, { padding: [10, 10] })
          } else {
            // Fallback to bounds rectangle if no points
            const bounds = L.latLngBounds(
              [ride.bounds.south, ride.bounds.west],
              [ride.bounds.north, ride.bounds.east]
            )
            L.rectangle(bounds, {
              color: '#3b82f6',
              weight: 2,
              fillOpacity: 0.1
            }).addTo(miniMap)

            miniMap.fitBounds(bounds)
          }
        }
      })
    },

    drawRidePathsOnSearchMap() {
      // Clear existing paths
      if (this.rideLayers) {
        this.rideLayers.clearLayers()
      }

      // Draw all ride paths on the search map
      this.rides.forEach((ride, index) => {
        if (ride.points && ride.points.length > 0) {
          const routePoints = ride.points.map(point => [point.lat, point.lon])

          // Create polyline for the route
          const route = L.polyline(routePoints, {
            color: this.getRouteColor(index),
            weight: 4,
            opacity: 0.7
          })

          // Add click event to view the ride
          route.on('click', () => {
            this.viewRide(ride.id)
          })

          // Add to the layer group
          this.rideLayers.addLayer(route)

          // Add start and end markers
          const startPoint = routePoints[0]
          const endPoint = routePoints[routePoints.length - 1]

          const startMarker = L.marker(startPoint, {
            icon: L.divIcon({
              className: 'start-marker',
              html: '🏁',
              iconSize: [25, 25]
            })
          }).bindPopup(`<strong>${ride.name}</strong><br/>Start`)

          const endMarker = L.marker(endPoint, {
            icon: L.divIcon({
              className: 'end-marker',
              html: '🏆',
              iconSize: [25, 25]
            })
          }).bindPopup(`<strong>${ride.name}</strong><br/>Finish`)

          this.rideLayers.addLayer(startMarker)
          this.rideLayers.addLayer(endMarker)
        }
      })
    },

    getRouteColor(index) {
      const colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#84cc16', '#f97316']
      return colors[index % colors.length]
    },

    viewRide(rideId) {
      this.$router.push(`/ride/${rideId}`)
    },

    formatDistance(distance) {
      if (distance < 1) {
        return `${Math.round(distance * 1000)}m`
      }
      return `${distance.toFixed(1)}km`
    },

    formatElevation(elevation) {
      return `${Math.round(elevation)}m`
    }
  }
}
</script>

<style scoped>
.home {
  min-height: 100vh;
}

.hero-section {
  text-align: center;
  padding: 4rem 2rem;
  color: white;
}

.hero-title {
  font-size: 3rem;
  font-weight: 700;
  margin: 0 0 1rem 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.hero-subtitle {
  font-size: 1.25rem;
  margin: 0;
  opacity: 0.9;
}

.search-section {
  background: white;
  padding: 2rem;
  margin: 0 2rem;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 100;
}

.map-container {
  position: relative;
  height: 400px;
  border-radius: 12px;
  overflow: hidden;
}

.map {
  width: 100%;
  height: 100%;
}

.map-controls {
  position: absolute;
  top: 1rem;
  right: 1rem;
  z-index: 1000;
}

.search-btn {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.search-btn:hover:not(:disabled) {
  background: #2563eb;
  transform: translateY(-1px);
}

.search-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.results-section {
  padding: 3rem 0;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
}

.results-title {
  color: white;
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 2rem 0;
  text-align: center;
}

.rides-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 2rem;
}

.ride-card {
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s;
}

.ride-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 35px rgba(0, 0, 0, 0.15);
}

.ride-card-map {
  height: 200px;
  position: relative;
}

.mini-map {
  width: 100%;
  height: 100%;
}

.ride-card-content {
  padding: 1.5rem;
}

.ride-name {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
  color: #2d3748;
}

.ride-stats {
  display: flex;
  gap: 1.5rem;
}

.stat {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.stat-icon {
  font-size: 1.25rem;
}

.stat-value {
  font-weight: 600;
  color: #4a5568;
}

.no-results {
  text-align: center;
  color: white;
  padding: 3rem;
}

.no-results p {
  font-size: 1.25rem;
  margin: 0;
  opacity: 0.8;
}
</style>
