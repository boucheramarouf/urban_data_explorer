export const INDICATOR_CONFIG = {
  itr: {
    key: 'itr',
    title: 'ITR Paris',
    subtitle: 'Indice de Tension Résidentielle · 2021',
    legendTitle: 'Tension résidentielle',
    scoreField: 'itr_score',
    labelField: 'itr_label',
    scoreLabel: 'Score ITR',
    labels: ['Très accessible', 'Accessible', 'Modéré', 'Tendu', 'Très tendu'],
    statsPath: '/stats',
    geojsonPath: '/geojson',
    ruesPath: '/rues',
  },
  svp: {
    key: 'svp',
    title: 'SVP Paris',
    subtitle: 'Score de Verdure et Proximité · 2021',
    legendTitle: 'Score SVP',
    scoreField: 'svp_score',
    labelField: 'svp_label',
    scoreLabel: 'Score SVP',
    labels: ['Très faible', 'Faible', 'Modéré', 'Bon', 'Excellent'],
    statsPath: '/svp/stats',
    geojsonPath: '/svp/geojson',
    ruesPath: '/svp/rues',
  },
  iaml: {
    key: 'iaml',
    title: 'IAML Paris',
    subtitle: "Indice d'Accessibilité Multimodale · 2021",
    legendTitle: 'Accessibilité multimodale',
    scoreField: 'iaml_score',
    labelField: 'iaml_label',
    scoreLabel: 'Score IAML',
    labels: ['Très accessible', 'Accessible', 'Modéré', 'Tendu', 'Très tendu'],
    statsPath: '/iaml/stats',
    geojsonPath: '/iaml/geojson',
    ruesPath: '/iaml/rues',
  },
}

export function getIndicatorConfig(indicator = 'itr') {
  return INDICATOR_CONFIG[indicator] || INDICATOR_CONFIG.itr
}
