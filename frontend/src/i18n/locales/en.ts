export default {
  // Menu items
  menu: {
    import: 'Import from ...',
    segments: 'Track',
    gpxFile: 'GPX file',
    stravaImport: 'Strava',
    importSegment: 'Database',
    importSegmentTooltip: 'Import segment from database',
    saveInDb: 'Save in DB',
    infoFeed: 'Information feed',
    collapseSidebar: 'Collapse sidebar',
    expandSidebar: 'Expand sidebar'
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
    latitude: 'Lat',
    longitude: 'Lon'
  },

  // Form labels
  form: {
    segmentName: 'Segment name',
    routeName: 'Route name',
    tire: 'Tire recommendations',
    trailConditions: 'Trail conditions',
    surfaceType: 'Surface type',
    majorSurfaceType: 'Major surface type',
    difficultyLevel: 'Difficulty level',
    comments: 'Comments',
    commentaryText: 'Description',
    commentaryPlaceholder: 'Add your detailed description of this segment...',
    media: 'Media',
    videoLinks: 'Video links',
    addVideoLink: 'Add video link',
    videoUrlPlaceholder: 'https://youtube.com/watch?v=...',
    removeVideo: 'Remove video',
    images: 'Images',
    uploadImages: 'Upload images',
    uploadHint: 'Drag & drop or click to select images',
    imageAlt: 'Segment image',
    imageCaptionPlaceholder: 'Image caption (optional)',
    removeImage: 'Remove image'
  },

  // Track type tabs
  trackType: {
    segment: 'Segment',
    route: 'Route'
  },

  // Tire conditions
  tire: {
    dry: 'Dry',
    wet: 'Wet',
    dryHelp: 'Use for clear, dry conditions where grip is high.',
    wetHelp: 'Use for rain, mud, or low-grip conditions.',
    slick: 'slick',
    'semi-slick': 'semi-slick',
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
    loadGpxFirst: 'Load a GPX first',
    insufficientPoints: 'GPX has insufficient points',
    useFileLoad: 'Use "Import from ..." → "GPX file" to begin',
    segmentCreated: 'Segment created successfully',
    createError: 'Error while creating segment',
    uploading: 'Uploading GPX file...',
    uploadError: 'Error uploading GPX file',
    uploadSuccess: 'GPX file uploaded successfully',
    noActivity: 'No recent activity'
  },

  // Navbar
  navbar: {
    home: 'Explorer',
    editor: 'Editor',
    routePlanner: 'Planner',
    login: 'Login with Strava',
    logout: 'Logout'
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
    'forest-trail': 'Forest trail'
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
  },

  // Segment detail page
  segmentDetail: {
    backToTrackFinder: 'Go back',
    map: 'Map',
    information: 'Information',
    elevation: 'Elevation',
    difficulty: 'Difficulty',
    surface: 'Surface',
    tireRecommendations: 'Tire recommendations',
    statistics: 'Statistics',
    distance: 'Dist:',
    elevationGain: 'Gain:',
    elevationLoss: 'Loss:',
    over5: 'over 5',
    dry: 'Dry',
    wet: 'Wet',
    comments: 'Comments',
    images: 'Images',
    videos: 'Videos',
    photosVideos: 'Photos & Videos',
    photoGallery: 'Photo Gallery',
    youtubeVideos: 'YouTube Videos',
    videoPlayback: 'Video Playback',
    openVideo: 'Open Video'
  },

  // Strava integration
  strava: {
    login: 'Login with Strava',
    logout: 'Logout',
    activityDetails: 'Activity Details',
    distance: 'Distance',
    movingTime: 'Moving Time',
    elevationGain: 'Elevation Gain',
    averageSpeed: 'Average Speed',
    maxSpeed: 'Max Speed',
    avgHeartrate: 'Avg Heartrate',
    activityInfo: 'Activity Information',
    activityStats: 'Activity Stats',
    startTime: 'Start Time',
    totalTime: 'Total Time',
    kudos: 'Kudos',
    comments: 'Comments',
    gpsStatus: 'GPS Status',
    gpsDataAvailable: 'GPS data available',
    routePreview: 'Route Preview',
    startPoint: 'Start Point',
    endPoint: 'End Point',
    noGpsDataWarning: 'This activity does not have GPS data and cannot be imported.',
    routes: 'Your Routes',
    loadingRoutes: 'Loading routes...',
    noRoutes: 'No cycling routes found',
    importRoute: 'Import Route',
    selectRoute: 'Select a route to import',
    activities: 'Your Strava Activities',
    loadingActivities: 'Loading activities...',
    noActivities: 'No cycling activities found',
    loadMore: 'Load More',
    refresh: 'Refresh',
    importActivity: 'Import Activity',
    selectActivity: 'Select an activity to import',
    loginRequired: 'Please login to Strava to view your activities',
    loginSuccess: 'Successfully logged in to Strava',
    loginError: 'Failed to login to Strava',
    importSuccess: 'Activity imported successfully',
    importError: 'Failed to import activity',
    completingLogin: 'Completing login...',
    redirecting: 'Redirecting...',
    noGpsData: 'This activity does not have GPS data available for import'
  },

  // Editor specific
  editor: {
    importSegment: 'Import Segment',
    searchingSegments: 'Searching segments',
    segmentsFound: 'segments found',
    noSegmentsFound: 'No segments found',
    noSegmentsInArea: 'No segments in this area',
    tryDifferentArea: 'Try moving the map to search in a different area',
    loadingSegments: 'Loading segments...',
    searchCenter: 'Search center',
    maxResults: 'Max results',
    importToEditor: 'Import to Editor'
  },

  // Route Planner
  routePlanner: {
    planning: 'Route Planning',
    clearRoute: 'Clear Route',
    saveRoute: 'Save Route',
    loadRoute: 'Load Route',
    routeInfo: 'Route Information',
    distance: 'Distance',
    duration: 'Duration',
    elevation: 'Elevation',
    noRoute: 'No route planned',
    togglePlanning: 'Toggle Planning Mode',
    centerMap: 'Center Map',
    elevationProfile: 'Elevation Profile',
    routeSaved: 'Route saved successfully',
    noSavedRoutes: 'No saved routes found',
    // Map Control Buttons
    clearMap: 'Clear Map',
    undo: 'Undo',
    redo: 'Redo',
    // Toggle Labels
    profile: 'Profile',
    totalDistance: 'Total Distance',
    elevationGain: 'Elevation Gain',
    elevationLoss: 'Elevation Loss',
    // Resize Handle
    resizeHandle: 'Drag up or down to resize elevation section height',
    // Chart Labels
    chartDistance: 'Distance (km)',
    chartElevation: 'Elevation (m)',
    chartElevationLabel: 'Elevation',
    // Error Messages
    elevationDataUnavailable:
      'Elevation data unavailable. Please check your internet connection and try again.',
    // Units
    km: 'km',
    m: 'm'
  },

  // Pagination
  pagination: {
    previous: 'Previous',
    next: 'Next',
    page: 'Page',
    of: 'of',
    showing: 'Showing',
    items: 'items'
  },

  // Common
  common: {
    close: 'Close',
    cancel: 'Cancel',
    confirm: 'Confirm',
    loading: 'Loading...',
    continue: 'Continue'
  }
}
