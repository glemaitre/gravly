export default {
  // Menu items
  menu: {
    import: 'Importer depuis ...',
    segments: 'Piste',
    gpxFile: 'Fichier GPX',
    stravaImport: 'Strava',
    importSegment: 'Base de données',
    importSegmentTooltip: 'Importer un segment depuis la base de données',
    saveAsNew: 'Sauvegarder comme nouveau',
    updateInDb: 'Mettre à jour en BD',
    infoFeed: "Flux d'informations",
    collapseSidebar: 'Réduire la barre latérale',
    expandSidebar: 'Développer la barre latérale'
  },

  // Chart and controls
  chart: {
    distance: 'Distance (km)',
    time: 'Temps (hh:mm:ss)',
    elevation: 'Altitude (m)',
    start: 'Début',
    end: 'Fin',
    gps: 'GPS'
  },

  // GPS labels
  gps: {
    latitude: 'Lat',
    longitude: 'Lon'
  },

  // Form labels
  form: {
    segmentName: 'Nom du segment',
    routeName: 'Nom de la sortie',
    tire: 'Recommandations de pneu',
    trailConditions: 'Conditions de piste',
    surfaceType: 'Type de surface',
    majorSurfaceType: 'Type de surface principal',
    difficultyLevel: 'Niveau de difficulté',
    comments: 'Commentaires',
    commentaryText: 'Description',
    commentaryPlaceholder: 'Ajoutez votre description détaillée de ce segment...',
    media: 'Médias',
    videoLinks: 'Liens vidéo',
    addVideoLink: 'Ajouter un lien vidéo',
    videoUrlPlaceholder: 'https://youtube.com/watch?v=...',
    removeVideo: 'Supprimer la vidéo',
    images: 'Images',
    uploadImages: 'Télécharger des images',
    uploadHint: 'Glisser-déposer ou cliquer pour sélectionner des images',
    imageAlt: 'Image du segment',
    imageCaptionPlaceholder: "Légende de l'image (optionnel)",
    removeImage: "Supprimer l'image"
  },

  // Track type tabs
  trackType: {
    segment: 'Segment',
    route: 'Route'
  },

  // Tire conditions
  tire: {
    dry: 'Sec',
    wet: 'Humide',
    dryHelp: "Utiliser par temps clair et sec où l'adhérence est élevée.",
    wetHelp: 'Utiliser par temps de pluie, boue ou faible adhérence.',
    slick: 'lisse',
    'semi-slick': 'semi-lisse',
    semiSlick: 'semi-lisse',
    knobs: 'crampons'
  },

  // Tooltips and help text
  tooltip: {
    loadGpxFirst: "Charger un fichier GPX d'abord pour activer la sauvegarde",
    enterSegmentName: 'Entrer un nom de segment pour activer la sauvegarde',
    submitting: 'Envoi en cours…',
    loadFromDatabase:
      'Charger un segment depuis la base de données pour activer la mise à jour',
    loadGpxFile: 'Charger un fichier GPX',
    moveStartBack: "Reculer le marqueur de début d'un point",
    moveStartForward: "Avancer le marqueur de début d'un point",
    moveEndBack: "Reculer le marqueur de fin d'un point",
    moveEndForward: "Avancer le marqueur de fin d'un point",
    elapsedTime: 'Temps écoulé depuis le début',
    distance: 'Distance (km)',
    elevation: 'Altitude (m)',
    gpsLocation: 'Position GPS'
  },

  // Messages
  message: {
    loadGpxFirst: "Charger un fichier GPX d'abord",
    insufficientPoints: 'Le fichier GPX a des points insuffisants',
    useFileLoad: 'Utiliser "Importer depuis ..." → "Fichier GPX" pour commencer',
    segmentCreated: 'Segment créé avec succès',
    createError: 'Erreur lors de la création du segment',
    updateError: 'Erreur lors de la mise à jour du segment',
    uploading: 'Téléchargement du fichier GPX...',
    uploadError: 'Erreur lors du téléchargement du fichier GPX',
    uploadSuccess: 'Fichier GPX téléchargé avec succès',
    noActivity: 'Aucune activité récente'
  },

  // Navbar
  navbar: {
    home: 'Explorer',
    editor: 'Éditeur',
    routePlanner: 'Planificateur',
    login: 'Connexion Strava',
    logout: 'Déconnexion'
  },

  // Language selector
  language: {
    title: 'Langue',
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
    'broken-paved-road': 'Asphalte',
    'dirty-road': 'Piste',
    'small-stone-road': 'Petites pierres',
    'big-stone-road': 'Grosses pierres',
    'field-trail': 'Sentier',
    'forest-trail': 'Forêt'
  },

  // Difficulty levels
  difficulty: {
    easy: 'Facile',
    hard: 'Difficile',
    level1: 'Très facile',
    level2: 'Facile',
    level3: 'Modéré',
    level4: 'Difficile',
    level5: 'Très difficile'
  },

  // Segment detail page
  segmentDetail: {
    backToTrackFinder: 'Retour',
    map: 'Carte',
    information: 'Information',
    elevation: 'Altitude',
    difficulty: 'Difficulté',
    surface: 'Surface',
    tireRecommendations: 'Recommandations de pneu',
    statistics: 'Statistiques',
    distance: 'Dist:',
    elevationGain: 'Gain:',
    elevationLoss: 'Perte:',
    over5: 'plus de 5',
    dry: 'Sec',
    wet: 'Humide',
    comments: 'Commentaires',
    images: 'Images',
    videos: 'Vidéos',
    photosVideos: 'Photos & Vidéos',
    photoGallery: 'Galerie photo',
    youtubeVideos: 'Vidéos YouTube',
    videoPlayback: 'Lecture vidéo',
    openVideo: 'Ouvrir la vidéo'
  },

  // Strava integration
  strava: {
    login: 'Se connecter avec Strava',
    logout: 'Se déconnecter',
    activityDetails: "Détails de l'Activité",
    distance: 'Distance',
    movingTime: 'Temps de Mouvement',
    elevationGain: 'Dénivelé Positif',
    averageSpeed: 'Vitesse Moyenne',
    maxSpeed: 'Vitesse Max',
    avgHeartrate: 'Fréquence Cardiaque Moy',
    activityInfo: "Informations sur l'Activité",
    activityStats: "Statistiques de l'Activité",
    startTime: 'Heure de Début',
    totalTime: 'Temps Total',
    kudos: 'Kudos',
    comments: 'Commentaires',
    gpsStatus: 'Statut GPS',
    gpsDataAvailable: 'Données GPS disponibles',
    routePreview: 'Aperçu du Parcours',
    startPoint: 'Point de Départ',
    endPoint: "Point d'Arrivée",
    noGpsDataWarning:
      "Cette activité n'a pas de données GPS et ne peut pas être importée.",
    routes: 'Vos Itinéraires',
    loadingRoutes: 'Chargement des itinéraires...',
    noRoutes: 'Aucun itinéraire de vélo trouvé',
    importRoute: "Importer l'itinéraire",
    selectRoute: 'Sélectionnez un itinéraire à importer',
    activities: 'Vos Activités Strava',
    loadingActivities: 'Chargement des activités...',
    noActivities: 'Aucune activité de vélo trouvée',
    loadMore: 'Charger plus',
    refresh: 'Actualiser',
    importActivity: "Importer l'activité",
    selectActivity: 'Sélectionnez une activité à importer',
    loginRequired: 'Veuillez vous connecter à Strava pour voir vos activités',
    loginSuccess: 'Connexion à Strava réussie',
    loginError: 'Échec de la connexion à Strava',
    importSuccess: 'Activité importée avec succès',
    importError: "Échec de l'importation de l'activité",
    completingLogin: 'Finalisation de la connexion...',
    redirecting: 'Redirection...',
    noGpsData: "Cette activité n'a pas de données GPS disponibles pour l'importation"
  },

  // Editor specific
  editor: {
    importSegment: 'Importer un Segment',
    searchingSegments: 'Recherche de segments',
    segmentsFound: 'segments trouvés',
    noSegmentsFound: 'Aucun segment trouvé',
    noSegmentsInArea: 'Aucun segment dans cette zone',
    tryDifferentArea:
      'Essayez de déplacer la carte pour rechercher dans une zone différente',
    loadingSegments: 'Chargement des segments...',
    searchCenter: 'Centre de recherche',
    maxResults: 'Résultats max',
    importToEditor: "Importer dans l'Éditeur"
  },

  // Route Planner
  routePlanner: {
    planning: 'Planification de Route',
    clearRoute: 'Effacer la Route',
    saveRoute: 'Sauvegarder la Route',
    loadRoute: 'Charger la Route',
    routeInfo: 'Informations de Route',
    distance: 'Distance',
    duration: 'Durée',
    elevation: 'Altitude',
    noRoute: 'Aucune route planifiée',
    togglePlanning: 'Basculer le Mode Planification',
    centerMap: 'Centrer la Carte',
    elevationProfile: "Profil d'Altitude",
    routeSaved: 'Route sauvegardée avec succès',
    noSavedRoutes: 'Aucune route sauvegardée trouvée',
    // Map Control Buttons
    clearMap: 'Effacer la Carte',
    undo: 'Annuler',
    redo: 'Rétablir',
    // Toggle Labels
    profile: 'Profil',
    totalDistance: 'Distance Totale',
    elevationGain: 'Gain de Dénivelé',
    elevationLoss: 'Perte de Dénivelé',
    // Resize Handle
    resizeHandle:
      "Glisser vers le haut ou le bas pour redimensionner la hauteur de la section d'élévation",
    // Chart Labels
    chartDistance: 'Distance (km)',
    chartElevation: 'Altitude (m)',
    chartElevationLabel: 'Altitude',
    // Error Messages
    elevationDataUnavailable:
      "Données d'élévation indisponibles. Veuillez vérifier votre connexion internet et réessayer.",
    // Units
    km: 'km',
    m: 'm'
  },

  // Pagination
  pagination: {
    previous: 'Précédent',
    next: 'Suivant',
    page: 'Page',
    of: 'de',
    showing: 'Affichage',
    items: 'éléments'
  },

  // Common
  common: {
    close: 'Fermer',
    cancel: 'Annuler',
    confirm: 'Confirmer',
    loading: 'Chargement...',
    continue: 'Continuer'
  }
}
