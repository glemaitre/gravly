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
    deleteFromDb: 'Supprimer de la BD',
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
    route: 'Route',
    segmentTooltip: 'Segments gravel listés par des utilisateurs avancés',
    routeTooltip:
      'Routes publiques listées par des utilisateurs avancés et vos propres routes privées précédemment sauvegardées',
    routeAuthWarning:
      "Connectez-vous avec Strava pour voir les routes sauvegardées d'autres utilisateurs et vos propres routes"
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
    deleteError: 'Erreur lors de la suppression du segment',
    confirmDelete:
      'Êtes-vous sûr de vouloir supprimer "{name}" ? Cette action ne peut pas être annulée.',
    uploading: 'Téléchargement du fichier GPX...',
    uploadError: 'Erreur lors du téléchargement du fichier GPX',
    uploadSuccess: 'Fichier GPX téléchargé avec succès',
    noActivity: 'Aucune activité récente',
    surfaceTypeRequired: 'Veuillez sélectionner au moins un type de surface'
  },

  // Navbar
  navbar: {
    home: 'Accueil',
    explorer: 'Explorer',
    editor: 'Éditeur',
    routePlanner: 'Planificateur',
    login: 'Connexion Strava',
    logout: 'Déconnexion'
  },

  // Landing page
  landing: {
    subtitle:
      'Planifiez vos parcours gravel en toute confiance. Sachez exactement quel terrain vous attend avant de rouler.',
    exploreSegments: 'Explorer les Segments',
    planRoute: 'Planifier un Parcours',
    whyGravly: 'Pourquoi Gravly ?',
    problemTitle: 'On Connaît Tous Cette Situation',
    problemDescription:
      "Vous planifiez ce qui semble être le parcours gravel parfait, pour finalement vous retrouver à pousser votre vélo dans un lit de rivière rocailleux, naviguer sur un sentier qui n'existe plus, ou rouler en slicks sur du gravier meuble. Planifier des sorties gravel ne devrait pas être une loterie.",
    feature1Title: 'Informations Terrain Réelles',
    feature1Description:
      'Chaque segment inclut des informations vérifiées et réelles : types de surface (asphalte, gravier, pierres, sentiers), niveaux de difficulté, recommandations de pneus pour conditions sèches et humides, et conditions réelles du terrain. Plus de mauvaises surprises.',
    feature2Title: 'Planification Précise',
    feature2Description:
      "Filtrez les segments par type de surface, difficulté ou conditions. Sélectionnez exactement les segments que vous souhaitez emprunter, et notre planificateur génère le parcours complet avec des profils d'altitude détaillés. Vous gardez le contrôle.",
    feature3Title: 'Sauvegardez et Partagez',
    feature3Description:
      'Enregistrez vos parcours planifiés et partagez-les avec la communauté gravel. Exportez au format GPX pour votre GPS ou compteur vélo. Constituez une collection de sorties fiables.'
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
    level5: 'Très difficile',
    descriptions: {
      level1: 'Vous pourriez rouler sur ce segment les yeux fermés',
      level2:
        'Ça devrait être tout à fait correct. Seulement quelques irrégularités sur le chemin, mais facile à gérer.',
      level3:
        'Vous aurez besoin de quelques compétences en pilotage de vélo en raison du terrain irrégulier ou des sections en montée et descente.',
      level4:
        "Ce n'est plus évident. Vous devrez définitivement naviguer les changements d'élévation et rencontrerez des variations de terrain inattendues.",
      level5:
        'Soyez prêt à poser le pied, car le chemin est difficile en raison de la pente, du terrain, ou des deux.'
    }
  },

  // Segment detail page
  segmentDetail: {
    backToTrackFinder: 'Retour',
    map: 'Carte',
    information: 'Information',
    elevation: 'Altitude',
    difficulty: 'Difficulté',
    surface: 'Surface',
    tireRecommendations: 'Rec. Pneu',
    statistics: 'Statistiques',
    distance: 'Distance',
    elevationGain: 'Dénivelé +',
    elevationLoss: 'Dénivelé -',
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
    openVideo: 'Ouvrir la vidéo',
    export: 'Exporter',
    actions: 'Actions',
    downloadGPX: 'Télécharger GPX',
    shareLink: 'Partager le lien',
    linkCopied: 'Lien copié dans le presse-papiers',
    shareLinkError: 'Échec du partage du lien',
    deleteRoute: 'Supprimer la sortie',
    deleteSegment: 'Supprimer le segment',
    deleteRouteConfirm:
      'Êtes-vous sûr de vouloir supprimer cette sortie ? Cette action est irréversible.',
    deleteSegmentConfirm:
      'Êtes-vous sûr de vouloir supprimer ce segment ? Cette action est irréversible.',
    deleteRouteSuccess: 'Sortie supprimée avec succès',
    deleteSegmentSuccess: 'Segment supprimé avec succès',
    deleteRouteError: 'Échec de la suppression de la sortie',
    deleteSegmentError: 'Échec de la suppression du segment',
    notRouteOwner: 'Seul le propriétaire de la sortie peut la supprimer',
    notSegmentOwner: 'Seul le propriétaire du segment peut le supprimer',
    routeNotOwned: 'Vous ne possédez pas cette sortie',
    segmentNotOwned: 'Vous ne possédez pas ce segment'
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
    // Sidebar and Mode Selection
    routingMode: 'Mode de Routage',
    standardMode: 'Libre',
    standardModeDesc:
      'Ajoutez plusieurs points de passage pour créer des itinéraires complexes avec des arrêts intermédiaires.',
    startEndMode: 'Guidé',
    startEndModeDesc:
      'Créez des itinéraires simples entre seulement deux points - départ et arrivée.',
    standardModeDescription:
      'Créez un parcours en ajoutant des points de passage successifs et nous générons le parcours pour vous.',
    startEndModeDescription:
      "Commencez par choisir vos points de départ et d'arrivée, sélectionnez vos segments de gravel à traverser et nous générerons le parcours pour vous.",
    chooseNextWaypoint: 'Choisissez votre prochain point de passage.',
    freeModeTitleInstructions: 'Comment créer votre parcours :',
    clickMapToAddWaypoint: 'Cliquez sur la carte pour ajouter un point de passage',
    dragWaypointToMove: 'Faites glisser un point de passage pour le déplacer',
    dragRouteToInsertWaypoint:
      'Faites glisser la ligne de parcours pour insérer un point de passage',
    rightClickWaypointToRemove:
      'Cliquez-droit sur un point de passage pour le supprimer',
    mapNavigationTitle: 'Navigation de la carte :',
    dragMapToPan: 'Faites glisser la carte pour vous déplacer',
    scrollToZoom: 'Faites défiler ou pincez pour zoomer',
    guidedTodoList: 'Étapes',
    guidedTodoInstructions: 'Définir les points de repère sur la carte',
    todoSetStartPoint: 'Définir le point de départ',
    todoSetEndPoint: "Définir le point d'arrivée",
    clickStartPoint: 'Cliquez sur la carte pour définir le point de départ',
    clickEndPoint: "Cliquez sur la carte pour définir le point d'arrivée",
    // Save Route Button
    saveRoute: 'Sauvegarder la sortie',
    saveRouteTitle: 'Sauvegarder la sortie',
    routeName: 'Nom de la sortie',
    routeNamePlaceholder: 'Entrez le nom de la sortie',
    routeStats: 'Statistiques de la sortie',
    routeComments: 'Commentaires',
    routeCommentsPlaceholder: 'Ajoutez des notes supplémentaires sur cette sortie...',
    defaultRouteName: 'Ma sortie',
    noSegmentsSelected: 'Aucun segment sélectionné',
    noRouteDistance: 'Aucune distance calculée',
    noRouteToSave: 'Aucune sortie disponible à sauvegarder',
    loginToSaveRoute: 'Connectez-vous avec Strava pour sauvegarder des sorties',
    noSegmentData: 'N/A (parcours manuel)',
    routeSavedSuccessfully: 'Sortie sauvegardée avec succès !',
    saveRouteError: 'Échec de la sauvegarde de la sortie',
    noSurfaceData: 'Aucune donnée de surface',
    // Surface type labels
    bigStoneRoad: 'Route en gros cailloux',
    brokenPavedRoad: 'Route pavée cassée',
    dirtyRoad: 'Route sale',
    fieldTrail: 'Sentier de champ',
    forestTrail: 'Sentier forestier',
    smallStoneRoad: 'Route en petits cailloux',
    startSet: 'Point de départ défini',
    startNotSet: 'Point de départ non défini',
    endSet: "Point d'arrivée défini",
    endNotSet: "Point d'arrivée non défini",
    generateRoute: 'Générer le parcours',
    generatingRoute: 'Génération du parcours...',
    noRouteMessage: "Ajoutez des points de passage pour voir le profil d'élévation.",
    // Segment selection
    selectedSegments: 'Segments sélectionnés',
    noSegmentsSelectedMessage:
      'Commencez par sélectionner des segments sur la carte pour construire votre parcours.',
    removeSegment: 'Supprimer le segment',
    // Segment filters
    filters: 'Filtres',
    clearFilters: 'Effacer tous les filtres',
    searchByName: 'Rechercher par Nom',
    searchByNamePlaceholder: 'Entrez le nom du segment...',
    noSegmentsMatchingFilters:
      "Aucun segment ne correspond à vos filtres actuels. Essayez d'ajuster vos paramètres de filtre.",
    difficulty: 'Difficulté',
    surface: 'Surface',
    tire: 'Pneus',
    tireDry: 'Pneus (Sec)',
    tireWet: 'Pneus (Mouillé)',
    dry: 'Sec',
    wet: 'Mouillé',
    surfaceTypes: {
      bigStoneRoad: 'Route Grosse Pierre',
      brokenPavedRoad: 'Route Pavée Cassée',
      dirtyRoad: 'Chemin de Terre',
      fieldTrail: 'Sentier de Champ',
      forestTrail: 'Sentier Forestier',
      smallStoneRoad: 'Route Petite Pierre'
    },
    tireTypes: {
      slick: 'Slick',
      semiSlick: 'Semi-Slick',
      knobs: 'Crampons'
    },
    // Waypoint context menu
    deleteWaypoint: 'Supprimer le point de passage',
    // Info banner
    infoBannerMessage: 'Cliquez sur {icon} pour choisir le mode de routage !',
    infoBannerDismiss: 'Compris',
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
    continue: 'Continuer',
    save: 'Sauvegarder',
    saving: 'Sauvegarde...',
    delete: 'Supprimer',
    deleting: 'Suppression...'
  },

  // Footer
  footer: {
    support: 'Support',
    reportIssue: 'Signaler un Problème',
    githubRepo: 'Dépôt GitHub',
    documentation: 'Documentation',
    license: 'Licence MIT',
    version: 'Version 1.0.0'
  }
}
