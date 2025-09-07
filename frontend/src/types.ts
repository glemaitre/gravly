export interface Bounds {
  north: number
  south: number
  east: number
  west: number
}

export interface TrackPoint {
  lat: number
  lon: number
  elevation: number
}

export interface RideCard {
  id: string
  name: string
  distance: number
  elevation_gain: number
  bounds: Bounds
  points?: TrackPoint[]
}

export interface GPXTrack {
  id: string
  name: string
  total_distance: number
  total_elevation_gain: number
  total_elevation_loss: number
  bounds: Bounds
  points: TrackPoint[]
}
