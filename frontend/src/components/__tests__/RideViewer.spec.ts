import { render, screen } from '@testing-library/vue'
import RideViewer from '../RideViewer.vue'

vi.mock('axios', () => {
  // Inline the sample ride inside the mock factory to avoid hoist issues
  const inlineRide = {
    name: 'Sample',
    points: [
      { lat: 45.0, lon: 6.0, elevation: 1000 },
      { lat: 45.001, lon: 6.001, elevation: 1010 },
    ],
    total_distance: 1.0,
    total_elevation_gain: 10,
    total_elevation_loss: 0,
    bounds: { north: 45.001, south: 45.0, east: 6.001, west: 6.0 },
  }
  return { default: { get: vi.fn().mockResolvedValue({ data: inlineRide }) } }
})

vi.mock('leaflet', () => ({
  default: {
    map: () => {
      const mapObj = {
        setView: () => mapObj,
        fitBounds: () => {},
        panTo: () => {},
      }
      return mapObj
    },
    tileLayer: () => ({ addTo: () => {} }),
    layerGroup: () => ({ addTo: () => ({ clearLayers: () => {}, addLayer: () => {} }) }),
    marker: () => ({}),
    polyline: () => ({}),
    latLngBounds: () => ({}),
    divIcon: () => ({}),
  }
}))

vi.mock('chart.js', () => {
  class MockChart {
    constructor(..._args: any[]) {}
    static register(..._args: any[]) {}
  }
  return { Chart: MockChart, registerables: [] }
})

test('renders ride title after load', async () => {
  render(RideViewer, { props: { id: 'ride-1' } })
  // wait for mounted hook and state update
  await Promise.resolve()
  await Promise.resolve()
  expect(screen.getByText('Sample')).toBeInTheDocument()
})
