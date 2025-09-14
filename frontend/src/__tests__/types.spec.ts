import { describe, it, expect } from 'vitest'
import type {
  Bounds,
  TrackPoint,
  RideCard,
  GPXTrack,
  Commentary,
  VideoLink,
  CommentaryImage,
  TrailConditions
} from '../types'

describe('Types', () => {
  describe('Bounds', () => {
    it('should have correct structure', () => {
      const bounds: Bounds = {
        north: 50.0,
        south: 49.0,
        east: 2.0,
        west: 1.0
      }

      expect(bounds.north).toBe(50.0)
      expect(bounds.south).toBe(49.0)
      expect(bounds.east).toBe(2.0)
      expect(bounds.west).toBe(1.0)
      expect(typeof bounds.north).toBe('number')
      expect(typeof bounds.south).toBe('number')
      expect(typeof bounds.east).toBe('number')
      expect(typeof bounds.west).toBe('number')
    })
  })

  describe('TrackPoint', () => {
    it('should have correct structure', () => {
      const point: TrackPoint = {
        lat: 48.8566,
        lon: 2.3522,
        elevation: 100.5
      }

      expect(point.lat).toBe(48.8566)
      expect(point.lon).toBe(2.3522)
      expect(point.elevation).toBe(100.5)
      expect(typeof point.lat).toBe('number')
      expect(typeof point.lon).toBe('number')
      expect(typeof point.elevation).toBe('number')
    })
  })

  describe('RideCard', () => {
    it('should have correct structure', () => {
      const rideCard: RideCard = {
        id: 'ride-123',
        name: 'Test Ride',
        distance: 25.5,
        elevation_gain: 500,
        bounds: {
          north: 50.0,
          south: 49.0,
          east: 2.0,
          west: 1.0
        },
        points: [
          { lat: 49.5, lon: 1.5, elevation: 100 },
          { lat: 49.6, lon: 1.6, elevation: 120 }
        ]
      }

      expect(rideCard.id).toBe('ride-123')
      expect(rideCard.name).toBe('Test Ride')
      expect(rideCard.distance).toBe(25.5)
      expect(rideCard.elevation_gain).toBe(500)
      expect(rideCard.bounds).toBeDefined()
      expect(rideCard.points).toBeDefined()
      expect(Array.isArray(rideCard.points)).toBe(true)
      expect(rideCard.points).toHaveLength(2)
    })

    it('should work without optional points', () => {
      const rideCard: RideCard = {
        id: 'ride-456',
        name: 'Test Ride Without Points',
        distance: 15.0,
        elevation_gain: 300,
        bounds: {
          north: 50.0,
          south: 49.0,
          east: 2.0,
          west: 1.0
        }
      }

      expect(rideCard.id).toBe('ride-456')
      expect(rideCard.points).toBeUndefined()
    })
  })

  describe('GPXTrack', () => {
    it('should have correct structure', () => {
      const gpxTrack: GPXTrack = {
        id: 'gpx-789',
        name: 'GPX Track',
        total_distance: 30.0,
        total_elevation_gain: 600,
        total_elevation_loss: 200,
        bounds: {
          north: 51.0,
          south: 50.0,
          east: 3.0,
          west: 2.0
        },
        points: [
          { lat: 50.5, lon: 2.5, elevation: 200 },
          { lat: 50.6, lon: 2.6, elevation: 250 }
        ]
      }

      expect(gpxTrack.id).toBe('gpx-789')
      expect(gpxTrack.name).toBe('GPX Track')
      expect(gpxTrack.total_distance).toBe(30.0)
      expect(gpxTrack.total_elevation_gain).toBe(600)
      expect(gpxTrack.total_elevation_loss).toBe(200)
      expect(gpxTrack.bounds).toBeDefined()
      expect(gpxTrack.points).toBeDefined()
      expect(Array.isArray(gpxTrack.points)).toBe(true)
    })
  })

  describe('VideoLink', () => {
    it('should have correct structure', () => {
      const videoLink: VideoLink = {
        id: 'video-1',
        url: 'https://youtube.com/watch?v=123',
        title: 'Test Video',
        platform: 'youtube'
      }

      expect(videoLink.id).toBe('video-1')
      expect(videoLink.url).toBe('https://youtube.com/watch?v=123')
      expect(videoLink.title).toBe('Test Video')
      expect(videoLink.platform).toBe('youtube')
      expect(['youtube', 'vimeo', 'other']).toContain(videoLink.platform)
    })

    it('should accept all valid platforms', () => {
      const platforms: Array<'youtube' | 'vimeo' | 'other'> = ['youtube', 'vimeo', 'other']

      platforms.forEach(platform => {
        const videoLink: VideoLink = {
          id: `video-${platform}`,
          url: `https://${platform}.com/test`,
          title: `Test ${platform} Video`,
          platform
        }
        expect(videoLink.platform).toBe(platform)
      })
    })
  })

  describe('CommentaryImage', () => {
    it('should have correct structure', () => {
      const mockFile = new File([''], 'test.jpg', { type: 'image/jpeg' })
      const commentaryImage: CommentaryImage = {
        id: 'img-1',
        file: mockFile,
        preview: 'data:image/jpeg;base64,test',
        caption: 'Test image caption'
      }

      expect(commentaryImage.id).toBe('img-1')
      expect(commentaryImage.file).toBe(mockFile)
      expect(commentaryImage.preview).toBe('data:image/jpeg;base64,test')
      expect(commentaryImage.caption).toBe('Test image caption')
      expect(commentaryImage.file instanceof File).toBe(true)
    })

    it('should work without optional caption', () => {
      const mockFile = new File([''], 'test.png', { type: 'image/png' })
      const commentaryImage: CommentaryImage = {
        id: 'img-2',
        file: mockFile,
        preview: 'data:image/png;base64,test'
      }

      expect(commentaryImage.caption).toBeUndefined()
    })
  })

  describe('Commentary', () => {
    it('should have correct structure', () => {
      const mockFile = new File([''], 'test.jpg', { type: 'image/jpeg' })
      const commentary: Commentary = {
        text: 'This is a test commentary',
        video_links: [
          {
            id: 'video-1',
            url: 'https://youtube.com/watch?v=123',
            title: 'Test Video',
            platform: 'youtube'
          }
        ],
        images: [
          {
            id: 'img-1',
            file: mockFile,
            preview: 'data:image/jpeg;base64,test',
            caption: 'Test image'
          }
        ]
      }

      expect(commentary.text).toBe('This is a test commentary')
      expect(Array.isArray(commentary.video_links)).toBe(true)
      expect(Array.isArray(commentary.images)).toBe(true)
      expect(commentary.video_links).toHaveLength(1)
      expect(commentary.images).toHaveLength(1)
    })

    it('should work with empty arrays', () => {
      const commentary: Commentary = {
        text: '',
        video_links: [],
        images: []
      }

      expect(commentary.text).toBe('')
      expect(commentary.video_links).toHaveLength(0)
      expect(commentary.images).toHaveLength(0)
    })
  })

  describe('TrailConditions', () => {
    it('should have correct structure', () => {
      const trailConditions: TrailConditions = {
        tire_dry: 'slick',
        tire_wet: 'semi-slick',
        surface_type: 'forest-trail',
        difficulty_level: 4
      }

      expect(trailConditions.tire_dry).toBe('slick')
      expect(trailConditions.tire_wet).toBe('semi-slick')
      expect(trailConditions.surface_type).toBe('forest-trail')
      expect(trailConditions.difficulty_level).toBe(4)
      expect(typeof trailConditions.difficulty_level).toBe('number')
    })

    it('should accept all valid tire types', () => {
      const tireTypes: Array<'slick' | 'semi-slick' | 'knobs'> = ['slick', 'semi-slick', 'knobs']

      tireTypes.forEach(tireType => {
        const trailConditions: TrailConditions = {
          tire_dry: tireType,
          tire_wet: tireType,
          surface_type: 'forest-trail',
          difficulty_level: 3
        }
        expect(trailConditions.tire_dry).toBe(tireType)
        expect(trailConditions.tire_wet).toBe(tireType)
      })
    })

    it('should accept all valid surface types', () => {
      const surfaceTypes: Array<'big-stone-road' | 'broken-paved-road' | 'dirty-road' | 'field-trail' | 'forest-trail' | 'small-stone-road'> = [
        'big-stone-road',
        'broken-paved-road',
        'dirty-road',
        'field-trail',
        'forest-trail',
        'small-stone-road'
      ]

      surfaceTypes.forEach(surfaceType => {
        const trailConditions: TrailConditions = {
          tire_dry: 'slick',
          tire_wet: 'slick',
          surface_type: surfaceType,
          difficulty_level: 3
        }
        expect(trailConditions.surface_type).toBe(surfaceType)
      })
    })

    it('should accept valid difficulty levels', () => {
      const validDifficulties = [1, 2, 3, 4, 5]

      validDifficulties.forEach(difficulty => {
        const trailConditions: TrailConditions = {
          tire_dry: 'slick',
          tire_wet: 'slick',
          surface_type: 'forest-trail',
          difficulty_level: difficulty
        }
        expect(trailConditions.difficulty_level).toBe(difficulty)
      })
    })
  })
})
