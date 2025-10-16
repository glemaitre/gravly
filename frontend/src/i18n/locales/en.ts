export default {
  // Menu items
  menu: {
    import: 'Import from ...',
    segments: 'Track',
    gpxFile: 'GPX file',
    stravaImport: 'Strava',
    importSegment: 'Database',
    importSegmentTooltip: 'Import segment from database',
    saveAsNew: 'Save as New',
    updateInDb: 'Update in DB',
    deleteFromDb: 'Delete from DB',
    infoFeed: 'Information feed',
    collapseSidebar: 'Collapse sidebar',
    expandSidebar: 'Expand sidebar',
    title: 'Menu',
    language: 'Language',
    support: 'Support'
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
    route: 'Route',
    segmentTooltip: 'Gravel segments listed by advanced users',
    routeTooltip:
      'Public routes listed by advanced users and your own private routes previously saved',
    routeAuthWarning:
      'Login with Strava to view saved routes from other users and your own routes'
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
    loadFromDatabase: 'Load a segment from database to enable update',
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
    updateError: 'Error while updating segment',
    deleteError: 'Error while deleting segment',
    confirmDelete:
      'Are you sure you want to delete "{name}"? This action cannot be undone.',
    uploading: 'Uploading GPX file...',
    uploadError: 'Error uploading GPX file',
    uploadSuccess: 'GPX file uploaded successfully',
    noActivity: 'No recent activity',
    surfaceTypeRequired: 'Please select at least one surface type'
  },

  // Navbar
  navbar: {
    home: 'Home',
    explorer: 'Explorer',
    editor: 'Editor',
    routePlanner: 'Planner',
    login: 'Login with Strava',
    logout: 'Logout'
  },

  // Landing page
  landing: {
    subtitle:
      'Plan gravel routes with confidence. Know exactly what terrain awaits you before you ride.',
    exploreSegments: 'Explore Segments',
    planRoute: 'Plan a Route',
    whyGravly: 'Why Gravly?',
    problemTitle: "We've All Been There",
    problemDescription:
      "You plan what looks like a perfect gravel route, only to end up pushing your bike through a rocky streambed, navigating a trail that no longer exists, or riding slicks on loose gravel. Planning gravel rides shouldn't be guesswork.",
    feature1Title: 'Real Gravel Intelligence',
    feature1Description:
      'Every segment includes verified, real-world information: surface types (paved, gravel, stones, trails), difficulty levels, tire recommendations for dry and wet conditions, and actual trail conditions. No more surprises.',
    feature2Title: 'Plan With Precision',
    feature2Description:
      'Filter segments by surface type, difficulty, or conditions. Select exactly which segments you want to ride through, and our planner generates the complete route with detailed elevation profiles. You stay in control.',
    feature3Title: 'Save & Share Your Routes',
    feature3Description:
      'Store your planned routes and share them with the gravel community. Export to GPX format for your GPS device or cycling computer. Build a collection of rides you can trust.'
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
    level5: 'Very hard',
    descriptions: {
      level1: 'You could ride this segment with your eyes closed',
      level2:
        'It should be quite fine. Only a couple of irregularities on the path, but easy business.',
      level3:
        "You'll need some bike handling skill due to irregular terrain or uphill and downhill sections.",
      level4:
        "It's no longer straightforward. You'll definitely need to navigate elevation changes and will encounter unexpected ground variations.",
      level5:
        'Be prepared to put a foot down, as the path is difficult due to either slope, terrain, or both.'
    }
  },

  // Segment detail page
  segmentDetail: {
    backToTrackFinder: 'Go back',
    map: 'Map',
    information: 'Information',
    elevation: 'Elevation',
    difficulty: 'Difficulty',
    surface: 'Surface',
    tireRecommendations: 'Tire Rec',
    statistics: 'Statistics',
    distance: 'Distance',
    elevationGain: 'Elevation Gain',
    elevationLoss: 'Elevation Loss',
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
    openVideo: 'Open Video',
    export: 'Export',
    actions: 'Actions',
    downloadGPX: 'Download GPX',
    shareLink: 'Share Link',
    linkCopied: 'Link copied to clipboard',
    shareLinkError: 'Failed to share link',
    deleteRoute: 'Delete Route',
    deleteSegment: 'Delete Segment',
    deleteRouteConfirm:
      'Are you sure you want to delete this route? This action cannot be undone.',
    deleteSegmentConfirm:
      'Are you sure you want to delete this segment? This action cannot be undone.',
    deleteRouteSuccess: 'Route deleted successfully',
    deleteSegmentSuccess: 'Segment deleted successfully',
    deleteRouteError: 'Failed to delete route',
    deleteSegmentError: 'Failed to delete segment',
    notRouteOwner: 'Only the route owner can delete it',
    notSegmentOwner: 'Only the segment owner can delete it',
    routeNotOwned: 'You do not own this route',
    segmentNotOwned: 'You do not own this segment'
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
    // Sidebar and Mode Selection
    routingMode: 'Routing Mode',
    standardMode: 'Free',
    standardModeDesc:
      'Add multiple waypoints to create complex routes with intermediate stops.',
    startEndMode: 'Guided',
    startEndModeDesc: 'Create simple routes between just two points - start and end.',
    standardModeDescription:
      'Create a route by adding successive waypoints and we generate the route for you.',
    startEndModeDescription:
      'Start by picking your start and end locations, select your gravel segments to pass through and we will generate the route for you.',
    chooseNextWaypoint: 'Choose your next waypoint.',
    freeModeTitleInstructions: 'How to create your route:',
    clickMapToAddWaypoint: 'Click on the map to add a waypoint',
    dragWaypointToMove: 'Drag a waypoint to move it',
    dragRouteToInsertWaypoint: 'Drag the route line to insert a waypoint',
    rightClickWaypointToRemove: 'Right-click a waypoint to remove it',
    mapNavigationTitle: 'Map navigation:',
    dragMapToPan: 'Drag the map to pan',
    scrollToZoom: 'Scroll or pinch to zoom',
    guidedTodoList: 'Steps',
    guidedTodoInstructions: 'Set landmarks on the map',
    todoSetStartPoint: 'Set starting point',
    todoSetEndPoint: 'Set ending point',
    clickStartPoint: 'Click on the map to set the starting point',
    clickEndPoint: 'Click on the map to set the ending point',
    // Save Route Button
    saveRoute: 'Save Route',
    saveRouteTitle: 'Save Route',
    routeName: 'Route Name',
    routeNamePlaceholder: 'Enter route name',
    routeStats: 'Route Statistics',
    routeComments: 'Comments',
    routeCommentsPlaceholder: 'Add any additional notes about this route...',
    defaultRouteName: 'My Route',
    noSegmentsSelected: 'No segments selected',
    noRouteDistance: 'No route distance calculated',
    noRouteToSave: 'No route available to save',
    loginToSaveRoute: 'Login with Strava to save routes',
    noSegmentData: 'N/A (waypoint route)',
    routeSavedSuccessfully: 'Route saved successfully!',
    saveRouteError: 'Failed to save route',
    noSurfaceData: 'No surface data',
    // Surface type labels
    bigStoneRoad: 'Big stone road',
    brokenPavedRoad: 'Broken paved road',
    dirtyRoad: 'Dirty road',
    fieldTrail: 'Field trail',
    forestTrail: 'Forest trail',
    smallStoneRoad: 'Small stone road',
    startSet: 'Start point set',
    startNotSet: 'Start point not set',
    endSet: 'End point set',
    endNotSet: 'End point not set',
    generateRoute: 'Generate Route',
    generatingRoute: 'Generating Route...',
    noRouteMessage: 'Start adding waypoints to see the elevation profile.',
    // Segment selection
    selectedSegments: 'Selected Segments',
    noSegmentsSelectedMessage:
      'Start selecting segments on the map to build your route.',
    removeSegment: 'Remove segment',
    // Segment filters
    filters: 'Filters',
    clearFilters: 'Clear all filters',
    searchByName: 'Search by Name',
    searchByNamePlaceholder: 'Enter segment name...',
    noSegmentsMatchingFilters:
      'No segments match your current filters. Try adjusting your filter settings.',
    difficulty: 'Difficulty',
    surface: 'Surface',
    tire: 'Tires',
    tireDry: 'Tires (Dry)',
    tireWet: 'Tires (Wet)',
    dry: 'Dry',
    wet: 'Wet',
    surfaceTypes: {
      bigStoneRoad: 'Big Stone Road',
      brokenPavedRoad: 'Broken Paved Road',
      dirtyRoad: 'Dirty Road',
      fieldTrail: 'Field Trail',
      forestTrail: 'Forest Trail',
      smallStoneRoad: 'Small Stone Road'
    },
    tireTypes: {
      slick: 'Slick',
      semiSlick: 'Semi-Slick',
      knobs: 'Knobs'
    },
    // Waypoint context menu
    deleteWaypoint: 'Delete Waypoint',
    // Info banner
    infoBannerMessage: 'Click on {icon} to choose the routing mode!',
    infoBannerDismiss: 'Got it',
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
    continue: 'Continue',
    save: 'Save',
    saving: 'Saving...',
    delete: 'Delete',
    deleting: 'Deleting...'
  },

  // Footer
  footer: {
    support: 'Support',
    reportIssue: 'Report an Issue',
    githubRepo: 'GitHub Repository',
    documentation: 'Documentation',
    license: 'MIT License',
    version: 'Version 1.0.0'
  }
}
