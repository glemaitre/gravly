export interface Bounds {
  north: number
  south: number
  east: number
  west: number
}

export interface TrackResponse {
  id: number
  file_path: string
  bound_north: number
  bound_south: number
  bound_east: number
  bound_west: number
  barycenter_latitude: number
  barycenter_longitude: number
  name: string
  track_type: string
  difficulty_level: number
  surface_type: string
  tire_dry: string
  tire_wet: string
  comments: string
}

export interface GPXDataResponse {
  gpx_xml_data: string
}

export interface GPXPoint {
  latitude: number
  longitude: number
  elevation: number
  time: string
}

export interface GPXTotalStats {
  total_points: number
  total_distance: number
  total_elevation_gain: number
  total_elevation_loss: number
}

export interface GPXBounds {
  north: number
  south: number
  east: number
  west: number
  min_elevation: number
  max_elevation: number
}

export interface GPXData {
  file_id: string
  track_name: string
  points: GPXPoint[]
  total_stats: GPXTotalStats
  bounds: GPXBounds
}

export interface TrackWithGPXDataResponse extends TrackResponse {
  gpx_data: GPXData | null
  gpx_xml_data: string | null // Raw GPX XML data for frontend parsing
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
  uploaded?: boolean
  image_url?: string
  image_id?: string
  storage_key?: string
  filename?: string
  original_filename?: string
}

export interface TrackVideoResponse {
  id: number
  track_id: number
  video_id: string
  video_url: string
  video_title: string | null
  platform: string
  created_at: string
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
