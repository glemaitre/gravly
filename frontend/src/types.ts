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

export interface Commentary {
  text: string
  video_links: VideoLink[]
  images: CommentaryImage[]
}

export interface VideoLink {
  id: string
  url: string
  title: string
  platform: 'youtube' | 'vimeo' | 'other'
}

export interface CommentaryImage {
  id: string
  file: File
  preview: string
  caption?: string
}

export interface TrailConditions {
  tire_dry: 'slick' | 'semi-slick' | 'knobs'
  tire_wet: 'slick' | 'semi-slick' | 'knobs'
  surface_type:
    | 'big-stone-road'
    | 'broken-paved-road'
    | 'dirty-road'
    | 'field-trail'
    | 'forest-trail'
    | 'small-stone-road'
  difficulty_level: number // 1-5
}
