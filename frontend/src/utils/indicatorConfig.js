export const INDICATOR_CONFIG = {
  itr: {
    key: 'itr',
    title: 'ITR Paris',
    subtitle: 'Indice de Tension Résidentielle · 2021',
    legendTitle: 'Tension résidentielle',
    scoreField: 'itr_score',
    labelField: 'itr_label',
    scoreLabel: 'Score ITR',
    statsPath: '/stats',
    geojsonPath: '/geojson',
    ruesPath: '/rues',
  },
  iaml: {
    key: 'iaml',
    title: 'IAML Paris',
    subtitle: "Indice d'Accessibilité Multimodale · 2021",
    legendTitle: 'Accessibilité multimodale',
    scoreField: 'iaml_score',
    labelField: 'iaml_label',
    scoreLabel: 'Score IAML',
    statsPath: '/iaml/stats',
    geojsonPath: '/iaml/geojson',
    ruesPath: '/iaml/rues',
  },
}

export function getIndicatorConfig(indicator = 'itr') {
  return INDICATOR_CONFIG[indicator] || INDICATOR_CONFIG.itr
}
