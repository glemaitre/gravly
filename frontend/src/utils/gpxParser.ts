import type { GPXData, GPXPoint, GPXBounds, GPXTotalStats } from '../types'

/**
 * Parse GPX XML data and extract track information
 * @param gpxXml Raw GPX XML string
 * @param fileId File ID for the track
 * @returns Parsed GPX data or null if parsing fails
 */
export function parseGPXData(gpxXml: string, fileId: string): GPXData | null {
  try {
    const parser = new DOMParser()
    const doc = parser.parseFromString(gpxXml, 'text/xml')

    // Check for parsing errors
    const parserError = doc.querySelector('parsererror')
    if (parserError) {
      console.error('GPX XML parsing error:', parserError.textContent)
      return null
    }

    // Extract track name
    const trackName = doc.querySelector('trk > name')?.textContent || 'Unknown Track'

    // Extract track points
    const trkptElements = doc.querySelectorAll('trkpt')
    
    const points: GPXPoint[] = []

    for (let i = 0; i < trkptElements.length; i++) {
      const trkpt = trkptElements[i]
      const lat = parseFloat(trkpt.getAttribute('lat') || '0')
      const lon = parseFloat(trkpt.getAttribute('lon') || '0')
      const eleElement = trkpt.querySelector('ele')
      const timeElement = trkpt.querySelector('time')
      const ele = eleElement ? parseFloat(eleElement.textContent || '0') : 0
      const time = timeElement ? timeElement.textContent : new Date().toISOString()

      if (!isNaN(lat) && !isNaN(lon)) {
        points.push({
          latitude: lat,
          longitude: lon,
          elevation: ele,
          time: time
        })
      }
    }

    if (points.length === 0) {
      console.warn('No valid track points found in GPX data')
      return null
    }

    // Calculate bounds
    const bounds = calculateBounds(points)

    // Calculate statistics
    const totalStats = calculateStats(points)

    return {
      file_id: fileId,
      track_name: trackName,
      points: points,
      total_stats: totalStats,
      bounds: bounds
    }
  } catch (error) {
    console.error('Error parsing GPX data:', error)
    return null
  }
}

/**
 * Calculate bounds from track points
 */
export function calculateBounds(points: GPXPoint[]): GPXBounds {
  if (points.length === 0) {
    return {
      north: 0,
      south: 0,
      east: 0,
      west: 0,
      min_elevation: 0,
      max_elevation: 0
    }
  }

  let north = points[0].latitude
  let south = points[0].latitude
  let east = points[0].longitude
  let west = points[0].longitude
  let minElevation = points[0].elevation
  let maxElevation = points[0].elevation

  for (const point of points) {
    north = Math.max(north, point.latitude)
    south = Math.min(south, point.latitude)
    east = Math.max(east, point.longitude)
    west = Math.min(west, point.longitude)
    minElevation = Math.min(minElevation, point.elevation)
    maxElevation = Math.max(maxElevation, point.elevation)
  }

  return {
    north,
    south,
    east,
    west,
    min_elevation: minElevation,
    max_elevation: maxElevation
  }
}

/**
 * Calculate track statistics
 */
function calculateStats(points: GPXPoint[]): GPXTotalStats {
  const totalPoints = points.length
  let totalDistance = 0
  let totalElevationGain = 0
  let totalElevationLoss = 0

  for (let i = 1; i < points.length; i++) {
    const prevPoint = points[i - 1]
    const currPoint = points[i]

    // Calculate distance between points (Haversine formula)
    const distance = calculateDistance(
      prevPoint.latitude,
      prevPoint.longitude,
      currPoint.latitude,
      currPoint.longitude
    )
    totalDistance += distance

    // Calculate elevation change
    const elevationChange = currPoint.elevation - prevPoint.elevation
    if (elevationChange > 0) {
      totalElevationGain += elevationChange
    } else {
      totalElevationLoss += Math.abs(elevationChange)
    }
  }

  return {
    total_points: totalPoints,
    total_distance: totalDistance,
    total_elevation_gain: totalElevationGain,
    total_elevation_loss: totalElevationLoss
  }
}

/**
 * Calculate distance between two points using Haversine formula
 * @param lat1 Latitude of first point
 * @param lon1 Longitude of first point
 * @param lat2 Latitude of second point
 * @param lon2 Longitude of second point
 * @returns Distance in meters
 */
function calculateDistance(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371000 // Earth's radius in meters
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLon = ((lon2 - lon1) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}
