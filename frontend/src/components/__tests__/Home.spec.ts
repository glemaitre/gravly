import { render, screen } from '@testing-library/vue'
import { nextTick } from 'vue'
import Home from '../Home.vue'

vi.mock('leaflet', () => ({
  default: {
    map: () => ({ setView: () => ({ on: () => {} }) }),
    tileLayer: () => ({ addTo: () => {} }),
    layerGroup: () => ({ addTo: () => ({ clearLayers: () => {}, addLayer: () => {} }) }),
    marker: () => ({ bindPopup: () => ({}) }),
    polyline: () => ({ on: () => ({}) }),
    latLngBounds: () => ({}),
    rectangle: () => ({ addTo: () => {} }),
    divIcon: () => ({}),
  }
}))

vi.mock('axios', () => ({
  default: { get: vi.fn().mockResolvedValue({ data: [] }) },
}))

test('renders hero title and shows no results initially', async () => {
  render(Home)
  expect(screen.getByText(/Discover Amazing Cycling Routes/i)).toBeInTheDocument()
  // axios mocked to return empty array
  // after mounted lifecycle, it will show no results message
  // allow microtasks to flush
  await nextTick()
  await nextTick()
  expect(
    screen.getByText(/No rides found in this area/i)
  ).toBeInTheDocument()
})
