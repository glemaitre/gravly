import { describe, it, expect } from 'vitest'
import type {
  Bounds,
  TrackResponse,
  GPXDataResponse,
  GPXPoint,
  GPXTotalStats,
  GPXBounds,
  GPXData,
  TrackWithGPXDataResponse,
  TrackPoint,
  RideCard,
  GPXTrack,
  Commentary,
  VideoLink,
  CommentaryImage,
  TrailConditions
} from '../types'

describe('Type Definitions', () => {
  describe('Bounds interface', () => {
    it('should accept valid bounds data', () => {
      const bounds: Bounds = {
        north: 45.0,
        south: 44.0,
        east: 5.0,
        west: 4.0
      }

      expect(bounds.north).toBe(45.0)
      expect(bounds.south).toBe(44.0)
      expect(bounds.east).toBe(5.0)
      expect(bounds.west).toBe(4.0)
    })
  })

  describe('TrackResponse interface', () => {
    it('should accept valid track response data', () => {
      const track: TrackResponse = {
        id: 1,
        file_path: '/path/to/file.gpx',
        bound_north: 45.0,
        bound_south: 44.0,
        bound_east: 5.0,
        bound_west: 4.0,
        barycenter_latitude: 44.5,
        barycenter_longitude: 4.5,
        name: 'Test Track',
        track_type: 'cycling',
        difficulty_level: 3,
        surface_type: 'forest-trail',
        tire_dry: 'slick',
        tire_wet: 'semi-slick',
        comments: 'Test comments'
      }

      expect(track.id).toBe(1)
      expect(track.name).toBe('Test Track')
      expect(track.difficulty_level).toBe(3)
    })
  })

  describe('GPXDataResponse interface', () => {
    it('should accept valid GPX data response', () => {
      const gpxResponse: GPXDataResponse = {
        gpx_xml_data: '<?xml version="1.0"?><gpx>...</gpx>'
      }

      expect(gpxResponse.gpx_xml_data).toContain('<?xml')
    })
  })

  describe('GPXPoint interface', () => {
    it('should accept valid GPX point data', () => {
      const point: GPXPoint = {
        latitude: 45.764,
        longitude: 4.8357,
        elevation: 200.5,
        time: '2023-01-01T10:00:00Z'
      }

      expect(point.latitude).toBe(45.764)
      expect(point.longitude).toBe(4.8357)
      expect(point.elevation).toBe(200.5)
      expect(point.time).toContain('2023-01-01')
    })
  })

  describe('GPXTotalStats interface', () => {
    it('should accept valid GPX total stats', () => {
      const stats: GPXTotalStats = {
        total_points: 100,
        total_distance: 5000.5,
        total_elevation_gain: 250.0,
        total_elevation_loss: 200.0
      }

      expect(stats.total_points).toBe(100)
      expect(stats.total_distance).toBe(5000.5)
      expect(stats.total_elevation_gain).toBe(250.0)
      expect(stats.total_elevation_loss).toBe(200.0)
    })
  })

  describe('GPXBounds interface', () => {
    it('should accept valid GPX bounds with elevation', () => {
      const bounds: GPXBounds = {
        north: 45.0,
        south: 44.0,
        east: 5.0,
        west: 4.0,
        min_elevation: 100.0,
        max_elevation: 500.0
      }

      expect(bounds.north).toBe(45.0)
      expect(bounds.min_elevation).toBe(100.0)
      expect(bounds.max_elevation).toBe(500.0)
    })
  })

  describe('GPXData interface', () => {
    it('should accept valid GPX data', () => {
      const gpxData: GPXData = {
        file_id: 'test-file-123',
        track_name: 'Test Track',
        points: [
          {
            latitude: 45.764,
            longitude: 4.8357,
            elevation: 200.5,
            time: '2023-01-01T10:00:00Z'
          }
        ],
        total_stats: {
          total_points: 1,
          total_distance: 0,
          total_elevation_gain: 0,
          total_elevation_loss: 0
        },
        bounds: {
          north: 45.764,
          south: 45.764,
          east: 4.8357,
          west: 4.8357,
          min_elevation: 200.5,
          max_elevation: 200.5
        }
      }

      expect(gpxData.file_id).toBe('test-file-123')
      expect(gpxData.track_name).toBe('Test Track')
      expect(gpxData.points).toHaveLength(1)
    })
  })

  describe('TrackWithGPXDataResponse interface', () => {
    it('should accept valid track with GPX data', () => {
      const trackWithGPX: TrackWithGPXDataResponse = {
        id: 1,
        file_path: '/path/to/file.gpx',
        bound_north: 45.0,
        bound_south: 44.0,
        bound_east: 5.0,
        bound_west: 4.0,
        barycenter_latitude: 44.5,
        barycenter_longitude: 4.5,
        name: 'Test Track',
        track_type: 'cycling',
        difficulty_level: 3,
        surface_type: 'forest-trail',
        tire_dry: 'slick',
        tire_wet: 'semi-slick',
        comments: 'Test comments',
        gpx_data: null,
        gpx_xml_data: '<?xml version="1.0"?><gpx>...</gpx>'
      }

      expect(trackWithGPX.id).toBe(1)
      expect(trackWithGPX.gpx_data).toBeNull()
      expect(trackWithGPX.gpx_xml_data).toContain('<?xml')
    })
  })

  describe('TrackPoint interface', () => {
    it('should accept valid track point data', () => {
      const trackPoint: TrackPoint = {
        lat: 45.764,
        lon: 4.8357,
        elevation: 200.5
      }

      expect(trackPoint.lat).toBe(45.764)
      expect(trackPoint.lon).toBe(4.8357)
      expect(trackPoint.elevation).toBe(200.5)
    })
  })

  describe('RideCard interface', () => {
    it('should accept valid ride card data', () => {
      const rideCard: RideCard = {
        id: 'ride-123',
        name: 'Morning Ride',
        distance: 2500.5,
        elevation_gain: 150.0,
        bounds: {
          north: 45.0,
          south: 44.0,
          east: 5.0,
          west: 4.0
        },
        points: [
          {
            lat: 45.764,
            lon: 4.8357,
            elevation: 200.5
          }
        ]
      }

      expect(rideCard.id).toBe('ride-123')
      expect(rideCard.name).toBe('Morning Ride')
      expect(rideCard.distance).toBe(2500.5)
      expect(rideCard.points).toHaveLength(1)
    })
  })

  describe('GPXTrack interface', () => {
    it('should accept valid GPX track data', () => {
      const gpxTrack: GPXTrack = {
        id: 'track-123',
        name: 'Test GPX Track',
        total_distance: 5000.0,
        total_elevation_gain: 300.0,
        total_elevation_loss: 250.0,
        bounds: {
          north: 45.0,
          south: 44.0,
          east: 5.0,
          west: 4.0
        },
        points: [
          {
            lat: 45.764,
            lon: 4.8357,
            elevation: 200.5
          }
        ]
      }

      expect(gpxTrack.id).toBe('track-123')
      expect(gpxTrack.name).toBe('Test GPX Track')
      expect(gpxTrack.total_distance).toBe(5000.0)
    })
  })

  describe('VideoLink interface', () => {
    it('should accept valid video link data', () => {
      const videoLink: VideoLink = {
        id: 'video-123',
        url: 'https://youtube.com/watch?v=123',
        platform: 'youtube'
      }

      expect(videoLink.id).toBe('video-123')
      expect(videoLink.url).toContain('youtube.com')
      expect(videoLink.platform).toBe('youtube')
    })

    it('should accept different platform types', () => {
      const youtubeLink: VideoLink = {
        id: '1',
        url: 'https://youtube.com/watch?v=123',
        platform: 'youtube'
      }

      const vimeoLink: VideoLink = {
        id: '2',
        url: 'https://vimeo.com/123456',
        platform: 'vimeo'
      }

      const otherLink: VideoLink = {
        id: '3',
        url: 'https://example.com/video',
        platform: 'other'
      }

      expect(youtubeLink.platform).toBe('youtube')
      expect(vimeoLink.platform).toBe('vimeo')
      expect(otherLink.platform).toBe('other')
    })
  })

  describe('CommentaryImage interface', () => {
    it('should accept valid commentary image data', () => {
      const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      const commentaryImage: CommentaryImage = {
        id: 'image-123',
        file: mockFile,
        preview: 'data:image/jpeg;base64,...',
        caption: 'Test image caption'
      }

      expect(commentaryImage.id).toBe('image-123')
      expect(commentaryImage.file).toBe(mockFile)
      expect(commentaryImage.preview).toContain('data:image')
      expect(commentaryImage.caption).toBe('Test image caption')
    })

    it('should accept commentary image without caption', () => {
      const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      const commentaryImage: CommentaryImage = {
        id: 'image-123',
        file: mockFile,
        preview: 'data:image/jpeg;base64,...'
      }

      expect(commentaryImage.id).toBe('image-123')
      expect(commentaryImage.caption).toBeUndefined()
    })
  })

  describe('Commentary interface', () => {
    it('should accept valid commentary data', () => {
      const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      const commentary: Commentary = {
        text: 'This is a test commentary',
        video_links: [
          {
            id: 'video-1',
            url: 'https://youtube.com/watch?v=123',
            platform: 'youtube'
          }
        ],
        images: [
          {
            id: 'image-1',
            file: mockFile,
            preview: 'data:image/jpeg;base64,...',
            caption: 'Test image'
          }
        ]
      }

      expect(commentary.text).toBe('This is a test commentary')
      expect(commentary.video_links).toHaveLength(1)
      expect(commentary.images).toHaveLength(1)
    })
  })

  describe('TrailConditions interface', () => {
    it('should accept valid trail conditions', () => {
      const trailConditions: TrailConditions = {
        tire_dry: 'slick',
        tire_wet: 'semi-slick',
        surface_type: 'forest-trail',
        difficulty_level: 3
      }

      expect(trailConditions.tire_dry).toBe('slick')
      expect(trailConditions.tire_wet).toBe('semi-slick')
      expect(trailConditions.surface_type).toBe('forest-trail')
      expect(trailConditions.difficulty_level).toBe(3)
    })

    it('should accept different tire types', () => {
      const slickConditions: TrailConditions = {
        tire_dry: 'slick',
        tire_wet: 'slick',
        surface_type: 'big-stone-road',
        difficulty_level: 1
      }

      const semiSlickConditions: TrailConditions = {
        tire_dry: 'semi-slick',
        tire_wet: 'semi-slick',
        surface_type: 'broken-paved-road',
        difficulty_level: 2
      }

      const knobsConditions: TrailConditions = {
        tire_dry: 'knobs',
        tire_wet: 'knobs',
        surface_type: 'dirty-road',
        difficulty_level: 4
      }

      expect(slickConditions.tire_dry).toBe('slick')
      expect(semiSlickConditions.tire_dry).toBe('semi-slick')
      expect(knobsConditions.tire_dry).toBe('knobs')
    })

    it('should accept different surface types', () => {
      const surfaceTypes = [
        'big-stone-road',
        'broken-paved-road',
        'dirty-road',
        'field-trail',
        'forest-trail',
        'small-stone-road'
      ]

      surfaceTypes.forEach((surfaceType, index) => {
        const trailConditions: TrailConditions = {
          tire_dry: 'slick',
          tire_wet: 'slick',
          surface_type: surfaceType as any,
          difficulty_level: index + 1
        }

        expect(trailConditions.surface_type).toBe(surfaceType)
      })
    })

    it('should accept different difficulty levels', () => {
      for (let level = 1; level <= 5; level++) {
        const trailConditions: TrailConditions = {
          tire_dry: 'slick',
          tire_wet: 'slick',
          surface_type: 'forest-trail',
          difficulty_level: level
        }

        expect(trailConditions.difficulty_level).toBe(level)
      }
    })
  })

  describe('Type compatibility and inheritance', () => {
    it('should allow extending interfaces correctly', () => {
      // Test that TrackWithGPXDataResponse extends TrackResponse
      const baseTrack: TrackResponse = {
        id: 1,
        file_path: '/path/to/file.gpx',
        bound_north: 45.0,
        bound_south: 44.0,
        bound_east: 5.0,
        bound_west: 4.0,
        barycenter_latitude: 44.5,
        barycenter_longitude: 4.5,
        name: 'Test Track',
        track_type: 'cycling',
        difficulty_level: 3,
        surface_type: 'forest-trail',
        tire_dry: 'slick',
        tire_wet: 'semi-slick',
        comments: 'Test comments'
      }

      const extendedTrack: TrackWithGPXDataResponse = {
        ...baseTrack,
        gpx_data: null,
        gpx_xml_data: '<?xml version="1.0"?><gpx>...</gpx>'
      }

      expect(extendedTrack.id).toBe(baseTrack.id)
      expect(extendedTrack.name).toBe(baseTrack.name)
      expect(extendedTrack.gpx_data).toBeNull()
    })
  })
})
