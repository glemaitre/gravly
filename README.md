# Cycling Routes Website

A modern web application for discovering and viewing cycling routes stored as GPX files. Built with Vue.js frontend, FastAPI backend, and Elasticsearch for search functionality.

## Features

- **Interactive Map Search**: Search for cycling routes using an interactive map with OpenStreetMap and cycling-specific layers
- **Route Cards**: Browse routes with mini-map previews and key statistics (distance, elevation gain)
- **Detailed Route Viewer**: View complete routes with synchronized map and elevation profile
- **Playback Mode**: Animate through routes with synchronized map and elevation chart
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Frontend**: Vue.js 3, Leaflet, Chart.js
- **Backend**: FastAPI, Python
- **Search**: Elasticsearch
- **Environment**: Pixi (conda-based environment management)

## Prerequisites

- Pixi (for environment management)
- Elasticsearch (running on localhost:9200)

## Setup Instructions

1. **Install Pixi** (if not already installed):
   ```bash
   curl -fsSL https://pixi.sh/install.sh | bash
   ```

2. **Start Elasticsearch**:
   ```bash
   # Using Docker
   docker run -d --name elasticsearch -p 9200:9200 -e "discovery.type=single-node" elasticsearch:8.11.0
   
   # Or install locally and start the service
   ```

3. **Install dependencies and setup**:
   ```bash
   # Install frontend dependencies
   pixi run frontend-install
   
   # Setup Elasticsearch index and load mock data
   pixi run setup-elasticsearch
   ```

4. **Start the application**:
   ```bash
   # Terminal 1: Start backend
   pixi run start-backend
   
   # Terminal 2: Start frontend
   pixi run start-frontend
   ```

5. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Project Structure

```
website_cycling/
├── backend/                 # FastAPI backend
│   └── main.py             # Main API server
├── frontend/               # Vue.js frontend
│   ├── src/
│   │   ├── components/     # Vue components
│   │   │   ├── Home.vue    # Landing page with search
│   │   │   └── RideViewer.vue # Route detail viewer
│   │   ├── App.vue         # Main app component
│   │   └── main.ts         # App entry point
│   ├── package.json        # Frontend dependencies
│   └── vite.config.js      # Vite configuration
├── mock_gpx/               # Sample GPX files for testing
├── scripts/                # Setup and utility scripts
│   └── setup_elasticsearch.py
├── pixi.toml              # Pixi environment configuration
└── README.md
```

## API Endpoints

- `GET /api/rides` - Search for rides with optional filters
- `GET /api/rides/{ride_id}` - Get detailed information about a specific ride

## Development

The application uses Pixi for environment management, which provides:
- Isolated Python environments for backend
- Node.js environment for frontend
- Easy dependency management
- Consistent development environment

### Common tasks (Pixi)

```bash
# Lint & format
pixi run lint-all
pixi run format-all

# Type-check frontend
pixi run type-check

# Run tests with coverage
pixi run test-backend
pixi run test-frontend
```

Task definitions use Pixi's cwd and depends-on fields for clarity.

## Mock Data

The application includes sample GPX files in the `mock_gpx/` directory for testing. These are automatically loaded into Elasticsearch when you run the setup script.

For S3-based loading at startup, configure env vars `S3_BUCKET` and optional `S3_PREFIX`. Elasticsearch persists indexed data; consider loading mock data only if the index is empty.

## Testing

- Backend: pytest with 100% coverage for `backend/main.py`
  - Run: `pixi run test-backend`
- Frontend: Vitest + Vue Test Utils + Testing Library with jsdom
  - Run: `pixi run test-frontend`

Coverage is printed in the terminal for both back and front.

## Continuous Integration

GitHub Actions run tests on push/PR to `main` using `prefix-dev/setup-pixi`:
- Backend: `.github/workflows/backend-tests.yml`
- Frontend: `.github/workflows/frontend-tests.yml`

Workflows activate the Pixi environment and run the Pixi tasks, posting coverage summaries.

## Future Enhancements

- S3 integration for GPX file storage
- User authentication and personal ride collections
- Social features (sharing, comments, ratings)
- Advanced filtering and sorting options
- GPX file upload functionality
- Real-time route tracking
