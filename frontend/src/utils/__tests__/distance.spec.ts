import { describe, it, expect } from 'vitest'
import { haversineDistance, formatDistance, getBoundingBoxCenter } from '../distance'

describe('Distance Utilities', () => {
  describe('haversineDistance', () => {
    it('should calculate distance between two points correctly', () => {
      // Test distance between Lyon, France and Paris, France
      const lyonLat = 45.764
      const lyonLng = 4.8357
      const parisLat = 48.8566
      const parisLng = 2.3522

      const distance = haversineDistance(lyonLat, lyonLng, parisLat, parisLng)

      // Expected distance is approximately 391.5 km
      expect(distance).toBeCloseTo(391.5, 1)
    })

    it('should return 0 for identical coordinates', () => {
      const lat = 45.764
      const lng = 4.8357

      const distance = haversineDistance(lat, lng, lat, lng)

      expect(distance).toBe(0)
    })

    it('should calculate short distances correctly', () => {
      // Test a very short distance (approximately 1 km)
      const lat1 = 45.764
      const lng1 = 4.8357
      const lat2 = 45.773 // Approximately 1 km north
      const lng2 = 4.8357

      const distance = haversineDistance(lat1, lng1, lat2, lng2)

      expect(distance).toBeCloseTo(1, 1)
    })

    it('should handle negative coordinates', () => {
      // Test with coordinates that cross the equator or prime meridian
      const lat1 = 0
      const lng1 = 0
      const lat2 = 1
      const lng2 = 1

      const distance = haversineDistance(lat1, lng1, lat2, lng2)

      expect(distance).toBeGreaterThan(0)
      expect(distance).toBeCloseTo(157, 0) // Approximately 157 km
    })
  })

  describe('formatDistance', () => {
    it('should format distances less than 1km in meters', () => {
      expect(formatDistance(0.5)).toBe('500m')
      expect(formatDistance(0.25)).toBe('250m')
      expect(formatDistance(0.001)).toBe('1m')
    })

    it('should format distances less than 10km with one decimal', () => {
      expect(formatDistance(1.5)).toBe('1.5km')
      expect(formatDistance(5.7)).toBe('5.7km')
      expect(formatDistance(9.9)).toBe('9.9km')
    })

    it('should format distances 10km and above as whole numbers', () => {
      expect(formatDistance(10)).toBe('10km')
      expect(formatDistance(15.3)).toBe('15km')
      expect(formatDistance(100.7)).toBe('101km')
    })

    it('should handle zero distance', () => {
      expect(formatDistance(0)).toBe('0m')
    })

    it('should round small distances appropriately', () => {
      expect(formatDistance(0.05)).toBe('50m')
      expect(formatDistance(0.15)).toBe('150m')
    })
  })

  describe('getBoundingBoxCenter', () => {
    it('should calculate center of a bounding box correctly', () => {
      const north = 50
      const south = 40
      const east = 10
      const west = 0

      const center = getBoundingBoxCenter(north, south, east, west)

      expect(center.lat).toBe(45) // (50 + 40) / 2
      expect(center.lng).toBe(5) // (10 + 0) / 2
    })

    it('should handle negative coordinates', () => {
      const north = -10
      const south = -20
      const east = -5
      const west = -15

      const center = getBoundingBoxCenter(north, south, east, west)

      expect(center.lat).toBe(-15) // (-10 + -20) / 2
      expect(center.lng).toBe(-10) // (-5 + -15) / 2
    })

    it('should handle zero coordinates', () => {
      const north = 0
      const south = 0
      const east = 0
      const west = 0

      const center = getBoundingBoxCenter(north, south, east, west)

      expect(center.lat).toBe(0)
      expect(center.lng).toBe(0)
    })

    it('should handle asymmetric bounding boxes', () => {
      const north = 100
      const south = 10
      const east = 50
      const west = 30

      const center = getBoundingBoxCenter(north, south, east, west)

      expect(center.lat).toBe(55) // (100 + 10) / 2
      expect(center.lng).toBe(40) // (50 + 30) / 2
    })
  })
})
