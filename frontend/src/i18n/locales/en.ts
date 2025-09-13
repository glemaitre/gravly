export default {
  // Menu items
  menu: {
    import: 'Import from ...',
    segments: 'Segments',
    gpxFile: 'GPX file',
    saveInDb: 'Save in DB'
  },

  // Chart and controls
  chart: {
    distance: 'Distance (km)',
    time: 'Time (hh:mm:ss)',
    elevation: 'Elevation (m)',
    start: 'Start',
    end: 'End',
    gps: 'GPS'
  },

  // GPS labels
  gps: {
    lat: 'Lat',
    lon: 'Lon'
  },

  // Form labels
  form: {
    segmentName: 'Segment name',
    tire: 'Tire',
    segmentInfo: 'Segment information',
    trailConditions: 'Trail conditions',
    surfaceType: 'Surface type',
    difficultyLevel: 'Difficulty level',
    comments: 'Comments',
    commentaryText: 'Description',
    commentaryPlaceholder: 'Add your detailed description of this segment...',
    media: 'Media',
    videoLinks: 'Video links',
    addVideoLink: 'Add video link',
    videoUrlPlaceholder: 'https://youtube.com/watch?v=...',
    videoTitlePlaceholder: 'Video title (optional)',
    removeVideo: 'Remove video',
    images: 'Images',
    uploadImages: 'Upload images',
    uploadHint: 'Drag & drop or click to select images',
    imageAlt: 'Segment image',
    imageCaptionPlaceholder: 'Image caption (optional)',
    removeImage: 'Remove image'
  },

  // Tire conditions
  tire: {
    dry: 'Dry',
    wet: 'Wet',
    dryHelp: 'Use for clear, dry conditions where grip is high.',
    wetHelp: 'Use for rain, mud, or low-grip conditions.',
    slick: 'slick',
    semiSlick: 'semi-slick',
    knobs: 'knobs'
  },

  // Tooltips and help text
  tooltip: {
    loadGpxFirst: 'Load a GPX first to enable saving',
    enterSegmentName: 'Enter a segment name to enable saving',
    submitting: 'Submitting…',
    loadGpxFile: 'Load GPX file',
    moveStartBack: 'Move start marker back one point',
    moveStartForward: 'Move start marker forward one point',
    moveEndBack: 'Move end marker back one point',
    moveEndForward: 'Move end marker forward one point',
    elapsedTime: 'Elapsed time from start',
    distance: 'Distance (km)',
    elevation: 'Elevation (m)',
    gpsLocation: 'GPS location'
  },

  // Messages
  message: {
    loadGpxFirst: 'Load a GPX first.',
    insufficientPoints: 'GPX has insufficient points.',
    useFileLoad: 'Use "Import from ..." → "GPX file" to begin.',
    segmentCreated: 'Segment created successfully.',
    createError: 'Error while creating segment.',
    uploading: 'Uploading GPX file...',
    uploadError: 'Error uploading GPX file.'
  },

  // Language selector
  language: {
    title: 'Language',
    english: 'English',
    french: 'Français'
  },

  // Units and formatting
  units: {
    km: 'km',
    m: 'm'
  },

  // Required field indicator
  required: '*',

  // Surface types
  surface: {
    'broken-paved-road': 'Paved road',
    'dirty-road': 'Dirty road',
    'small-stone-road': 'Small stone road',
    'big-stone-road': 'Big stone road',
    'field-trail': 'Field trail',
    'forest-trail': 'Forest trail',
  },

  // Difficulty levels
  difficulty: {
    easy: 'Easy',
    hard: 'Hard',
    level1: 'Very easy',
    level2: 'Easy',
    level3: 'Moderate',
    level4: 'Hard',
    level5: 'Very hard'
  }
}
