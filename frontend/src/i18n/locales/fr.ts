export default {
  // Menu items
  menu: {
    import: 'Importer depuis ...',
    segments: 'Segments',
    gpxFile: 'Fichier GPX',
    saveInDb: 'Sauvegarder en BD'
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
    lat: 'Lat',
    lon: 'Lon'
  },

  // Form labels
  form: {
    segmentName: 'Nom du segment',
    tire: 'Pneu',
    segmentInfo: 'Informations du segment',
    trailConditions: 'Conditions de piste',
    surfaceType: 'Type de surface',
    difficultyLevel: 'Niveau de difficulté',
    comments: 'Commentaires',
    commentaryText: 'Description',
    commentaryPlaceholder: 'Ajoutez votre description détaillée de ce segment...',
    media: 'Médias',
    videoLinks: 'Liens vidéo',
    addVideoLink: 'Ajouter un lien vidéo',
    videoUrlPlaceholder: 'https://youtube.com/watch?v=...',
    videoTitlePlaceholder: 'Titre de la vidéo (optionnel)',
    removeVideo: 'Supprimer la vidéo',
    images: 'Images',
    uploadImages: 'Télécharger des images',
    uploadHint: 'Glisser-déposer ou cliquer pour sélectionner des images',
    imageAlt: 'Image du segment',
    imageCaptionPlaceholder: 'Légende de l\'image (optionnel)',
    removeImage: 'Supprimer l\'image'
  },

  // Tire conditions
  tire: {
    dry: 'Sec',
    wet: 'Humide',
    dryHelp: 'Utiliser par temps clair et sec où l\'adhérence est élevée.',
    wetHelp: 'Utiliser par temps de pluie, boue ou faible adhérence.',
    slick: 'lisse',
    semiSlick: 'semi-lisse',
    knobs: 'crampons'
  },

  // Tooltips and help text
  tooltip: {
    loadGpxFirst: 'Charger un fichier GPX d\'abord pour activer la sauvegarde',
    enterSegmentName: 'Entrer un nom de segment pour activer la sauvegarde',
    submitting: 'Envoi en cours…',
    loadGpxFile: 'Charger un fichier GPX',
    moveStartBack: 'Reculer le marqueur de début d\'un point',
    moveStartForward: 'Avancer le marqueur de début d\'un point',
    moveEndBack: 'Reculer le marqueur de fin d\'un point',
    moveEndForward: 'Avancer le marqueur de fin d\'un point',
    elapsedTime: 'Temps écoulé depuis le début',
    distance: 'Distance (km)',
    elevation: 'Altitude (m)',
    gpsLocation: 'Position GPS'
  },

  // Messages
  message: {
    loadGpxFirst: 'Charger un fichier GPX d\'abord.',
    insufficientPoints: 'Le fichier GPX a des points insuffisants.',
    useFileLoad: 'Utiliser "Importer depuis ..." → "Fichier GPX" pour commencer.',
    segmentCreated: 'Segment créé avec succès.',
    createError: 'Erreur lors de la création du segment.',
    uploading: 'Téléchargement du fichier GPX...',
    uploadError: 'Erreur lors du téléchargement du fichier GPX.'
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
  }
}
