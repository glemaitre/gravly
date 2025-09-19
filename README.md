# Gravly - Find your next gravel ride

A modern web application for discovering, creating, and viewing cycling routes stored as GPX files. Built with Vue.js frontend, FastAPI backend, and PostgreSQL for data persistence.

## Features

- **Interactive Map Discovery**: Real-time streaming of cycling segments using Server-Sent Events (SSE) with Leaflet maps
- **GPX Route Editor**: Upload and edit GPX files with visual segment selection, surface type classification, and difficulty rating
- **Segment Detail View**: Comprehensive segment information with interactive maps, elevation charts, and detailed metadata
- **Advanced Segment List**: Filterable and sortable segment lists with track type filtering (segments vs routes)
- **Real-time Segment Streaming**: Efficient bounds-based search with client-side GPX parsing for optimal performance
- **Map State Persistence**: Automatic saving and restoration of map position and zoom level
- **Multi-language Support**: Internationalization with English and French locales
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Advanced Route Analysis**: Elevation profiles, distance calculations, and trail condition metadata
- **Flexible Storage**: Support for both local filesystem and AWS S3 storage backends
- **Database Seeding**: Automated generation of realistic test data for development and testing

## Tech Stack

- **Frontend**: Vue.js 3, TypeScript, Leaflet, Chart.js, Vitest
- **Backend**: FastAPI, Python, SQLAlchemy, Pydantic
- **Database**: PostgreSQL (async with asyncpg)
- **Storage**: Local filesystem (development) or AWS S3 (production)
- **Testing**: pytest (backend), Vitest + Vue Test Utils (frontend)
- **Environment**: Pixi (conda-based environment management)
- **Code Quality**: Ruff (Python), ESLint (TypeScript), TypeScript strict mode

## Prerequisites

- Pixi (for environment management)
- PostgreSQL (installed via Pixi - see setup instructions)

## Setup Instructions

1. **Install Pixi** (if not already installed):
   ```bash
   curl -fsSL https://pixi.sh/install.sh | bash
   ```

2. **Install dependencies and setup**:
   ```bash
   # Install frontend dependencies
   pixi run frontend-install

   # Setup PostgreSQL database
   pixi run pg-setup
   ```

3. **Start the application**:
   ```bash
   # Terminal 1: Start backend
   pixi run start-backend

   # Terminal 2: Start frontend
   pixi run start-frontend
   ```

4. **Access the application**:
   - Frontend: http://localhost:5173 (Vite dev server)
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

5. **Seed the database with test data** (optional):
   ```bash
   # Generate 1,000 realistic cycling segments across France
   pixi run python scripts/database_seeding.py
   
   # Or generate just 5 segments for quick testing
   pixi run python scripts/test_seeding.py
   ```

## Environment Configuration

This project uses separate `.env` files for database and storage configuration. The backend automatically loads environment variables from `.env/storage` and `.env/database` files.

### Setup Environment Files

1. **Create the environment files** in the `.env/` directory:
   ```bash
   mkdir -p .env
   ```

2. **Create the database configuration file** (`.env/database`):
   ```bash
   # Database configuration
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=cycling
   DB_USER=postgres
   DB_PASSWORD=your_secure_password_here
   ```

3. **Create the storage configuration file** (`.env/storage`):
   ```bash
   # For local storage (development)
   STORAGE_TYPE=local
   LOCAL_STORAGE_ROOT=../scratch/local_storage
   LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage
   ```
   
   Or for S3 storage:
   ```bash
   # For S3 storage (production/testing)
   STORAGE_TYPE=s3
   AWS_S3_BUCKET=your-bucket-name
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   AWS_REGION=us-east-1
   ```

4. **Never commit actual `.env` files** - they contain sensitive information and are
   already in `.gitignore`.

### Storage Configuration

The storage backend is controlled by the `STORAGE_TYPE` variable in `.env/storage`:

- `STORAGE_TYPE=local` - Use local filesystem storage
- `STORAGE_TYPE=s3` - Use AWS S3 storage

### Database Configuration

The application uses PostgreSQL for persistent storage. Database connection is configured through environment variables in `.env/database`:

- `DB_HOST` - Database host (required)
- `DB_PORT` - Database port (required)
- `DB_NAME` - Database name (required)
- `DB_USER` - Database username (required)
- `DB_PASSWORD` - Database password (required)

The application automatically constructs the PostgreSQL connection string from these individual components.

### PostgreSQL Setup

1. **Initialize and start PostgreSQL** (first time only):
   ```bash
   pixi run pg-setup
   ```

2. **Start PostgreSQL** (for subsequent sessions):
   ```bash
   pixi run pg-start
   ```

3. **Stop PostgreSQL**:
   ```bash
   pixi run pg-stop
   ```

4. **Check PostgreSQL status**:
   ```bash
   pixi run pg-status
   ```

**Note**: The database will be initialized in a `postgres_data` directory in your
project root. This directory should be added to `.gitignore` (which it already is).

### Local Storage Configuration

When using local storage, configure these variables in `.env/storage`:

- `LOCAL_STORAGE_ROOT` - Root directory for storing files
- `LOCAL_STORAGE_BASE_URL` - Base URL for serving files

### AWS S3 Configuration

When using S3 storage, configure these variables in `.env/storage`:

- `AWS_S3_BUCKET` - S3 bucket name
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_REGION` - AWS region (optional, defaults to `us-east-1`)

## Database Seeding

The project includes comprehensive database seeding scripts to generate realistic test data for development and testing purposes.

### Seeding Scripts

- **`scripts/database_seeding.py`**: Generates 1,000 realistic 5km cycling segments across 13 French regions
- **`scripts/test_seeding.py`**: Generates 5 segments for quick testing

### Features of Generated Data

- **Geographic Distribution**: Segments distributed across 13 French regions with realistic GPS coordinates
- **Realistic Routes**: 5km cycling routes with elevation changes and proper GPS point distribution
- **Varied Surface Types**: Different surface types (paved roads, trails, etc.) with realistic probabilities
- **Tire Recommendations**: Appropriate tire types for dry and wet conditions
- **Difficulty Levels**: 1-5 difficulty scale with realistic distribution
- **Batch Processing**: Processes segments in batches for memory efficiency
- **Storage Integration**: Uploads GPX files to configured storage (local or S3)
- **Database Integration**: Stores segment metadata in PostgreSQL

### Usage

```bash
# Full seeding (1,000 segments) - takes several minutes
pixi run python scripts/database_seeding.py

# Quick test seeding (5 segments) - takes seconds
pixi run python scripts/test_seeding.py
```

### Customization

You can modify the parameters in the `main()` function of `database_seeding.py`:

```python
await seed_database(
    num_segments=1000,      # Number of segments to generate
    target_distance_km=5.0, # Distance of each segment in km
    batch_size=50           # Number of segments per batch
)
```

### Running the Application

#### Start the Backend
```bash
# Using pixi (loads from .env/storage and .env/database)
pixi run start-backend

# Or manually
uvicorn backend.src.main:app --reload --host 0.0.0.0 --port 8000
```

#### Start the Frontend
```bash
# Using pixi
pixi run start-frontend

# Or manually
cd frontend && npm run dev
```

### File Access

#### Local Storage
Files are served via the `/storage/{file_path}` endpoint when using local storage.

Example: `http://localhost:8000/storage/gpx-segments/12345.gpx`

#### S3 Storage
Files are accessed via presigned URLs when using S3 storage.

### Development Workflow

1. **Local Development**: Use `STORAGE_TYPE=local` for development without needing AWS
   credentials
2. **Testing**: Tests use moto to mock S3, so they work regardless of storage
   configuration
3. **Production**: Use `STORAGE_TYPE=s3` with proper AWS credentials

### File Structure (Local Storage)

```
scratch/local_storage/
├── gpx-segments/
│   ├── file1.gpx
│   ├── file1.gpx.metadata
│   ├── file2.gpx
│   └── file2.gpx.metadata
└── other-prefix/
    └── ...
```

Each GPX file has a corresponding `.metadata` file containing:
- file-id
- file-type
- content-type
- original-path

## Project Structure

```
website_cycling/
├── backend/                 # FastAPI backend
│   ├── src/
│   │   ├── main.py         # Main API server with streaming endpoints
│   │   ├── models/         # SQLAlchemy models and Pydantic schemas
│   │   │   ├── track.py    # Track model and response schemas
│   │   │   └── base.py     # Base model configuration
│   │   └── utils/          # Utility modules
│   │       ├── config.py   # Environment configuration
│   │       ├── storage.py  # Storage managers (S3/Local)
│   │       ├── gpx.py      # GPX parsing utilities
│   │       └── postgres.py # Database configuration
│   └── tests/              # Backend tests with comprehensive coverage
├── frontend/               # Vue.js frontend
│   ├── src/
│   │   ├── components/     # Vue components
│   │   │   ├── LandingPage.vue # Interactive map with streaming segments
│   │   │   ├── Editor.vue      # GPX route editor with chart visualization
│   │   │   ├── SegmentDetail.vue # Detailed segment view with map and charts
│   │   │   ├── SegmentList.vue   # Filterable segment list component
│   │   │   └── Navbar.vue        # Navigation component
│   │   ├── composables/    # Vue composables
│   │   │   └── useMapState.ts    # Map state persistence management
│   │   ├── utils/          # Frontend utilities
│   │   │   ├── gpxParser.ts      # Client-side GPX parsing
│   │   │   └── distance.ts       # Distance calculation utilities
│   │   ├── types/          # TypeScript type definitions
│   │   ├── i18n/           # Internationalization
│   │   └── assets/         # Images and static assets
│   ├── package.json        # Frontend dependencies
│   └── vite.config.js      # Vite configuration
├── .env/                   # Environment configuration files
│   ├── database            # Database configuration
│   └── storage             # Storage configuration
├── scripts/                # Database seeding and utility scripts
│   ├── database_seeding.py # Generate 1,000 realistic cycling segments
│   ├── test_seeding.py     # Generate 5 test segments
│   └── README.md           # Scripts documentation
├── backend/tests/data/     # Test GPX files
├── postgres_data/          # PostgreSQL data directory (created by pg-setup)
├── scratch/                # Local storage directory
├── pixi.toml              # Pixi environment configuration
└── README.md
```

## API Endpoints

### Core Endpoints
- `GET /` - Root endpoint with API information
- `GET /storage/{file_path}` - Serve GPX files from storage

### GPX Management
- `POST /api/upload-gpx` - Upload and parse GPX files
- `POST /api/segments` - Create new cycling segments from uploaded GPX data

### Segment Discovery (Streaming)
- `GET /api/segments/search` - Stream segments within geographic bounds using Server-Sent Events
- `OPTIONS /api/segments/search` - CORS preflight for streaming endpoint

### Features
- **Real-time Streaming**: Uses Server-Sent Events (SSE) for efficient data delivery
- **Bounds-based Search**: Geographic filtering with PostgreSQL spatial queries
- **Client-side GPX Parsing**: Raw XML data streamed to frontend for optimal performance
- **CORS Support**: Full CORS configuration for cross-origin requests

## Development

The application uses Pixi for environment management, which provides:
- Isolated Python environments for backend
- Node.js environment for frontend
- Easy dependency management
- Consistent development environment

### Common tasks (Pixi)

```bash
# Start development servers
pixi run start-backend            # Backend server
pixi run start-frontend           # Frontend development server

# Database management
pixi run pg-setup                 # Initialize PostgreSQL database (first time)
pixi run pg-start                 # Start PostgreSQL server
pixi run pg-stop                  # Stop PostgreSQL server
pixi run pg-status                # Check PostgreSQL server status
pixi run pg-create-db             # Create database
pixi run pg-drop-db               # Drop database
pixi run pg-cleanup               # Stop, drop, and erase database
pixi run pg-erase                 # Erase database files

# Lint & format
pixi run lint-all
pixi run format-all

# Type-check frontend
pixi run type-check-frontend

# Run tests with coverage
pixi run test-backend
pixi run test-frontend
```

Task definitions use Pixi's cwd and depends-on fields for clarity.

## Performance Optimizations

### Client-Side Processing
- **GPX Parsing**: Moved from backend to frontend for reduced server load
- **Streaming Architecture**: Server-Sent Events for real-time data delivery
- **Bounds-based Filtering**: Efficient geographic queries with PostgreSQL
- **Client-side Caching**: Layer tracking to prevent redundant map redraws
- **Distance Calculations**: Real-time distance calculations from map center to segments

### Backend Optimizations
- **Async Database**: PostgreSQL with asyncpg for concurrent operations
- **Streaming Responses**: Real-time segment delivery without blocking
- **Storage Abstraction**: Unified API for S3 and local storage
- **Error Handling**: Comprehensive error recovery and logging

### Frontend Optimizations
- **Debounced Search**: Prevents excessive API calls during map interactions
- **Incremental Updates**: Only updates map with new segments
- **Zoom Optimization**: Avoids unnecessary searches when zooming in
- **Map State Persistence**: Automatic saving and restoration of map state using localStorage
- **Composable Architecture**: Reusable Vue composables for state management
- **TypeScript**: Strict typing for better performance and reliability

## Testing

### Backend Testing
- **Framework**: pytest with comprehensive coverage
- **Coverage**: 100% coverage for core modules including:
  - `backend/src/main.py` - API endpoints and streaming functionality
  - `backend/src/utils/storage.py` - S3 and local storage managers
  - `backend/src/models/track.py` - Data models and schemas
  - `backend/src/utils/` - Utility modules
- **Run**: `pixi run test-backend`
- **Features**: Async database testing, S3 mocking with moto, comprehensive error handling

### Frontend Testing
- **Framework**: Vitest + Vue Test Utils + Testing Library with jsdom
- **Coverage**: 83.43% overall coverage with:
  - `LandingPage.vue`: 39.79% (map interactions, EventSource streaming)
  - `SegmentList.vue`: Comprehensive segment list functionality
  - `SegmentDetail.vue`: Detailed segment view and interactions
  - `Editor.vue`: 69.14% (route editing functionality)
  - `Navbar.vue`: Navigation and language switching
  - `gpxParser.ts`: 92.8% (comprehensive GPX parsing tests)
  - `useMapState.ts`: Map state persistence composable
- **Run**: `pixi run test-frontend`
- **Features**: Component testing, Leaflet mocking, EventSource simulation, composable testing

### Test Quality
- **Comprehensive Coverage**: Both backend and frontend have extensive test suites
- **Real-world Scenarios**: Tests cover actual GPX data processing and map interactions
- **Error Handling**: Robust testing of edge cases and error conditions
- **Performance Testing**: Coverage of streaming functionality and client-side parsing

## Continuous Integration

GitHub Actions run tests on push/PR to `main` using `prefix-dev/setup-pixi`:
- Backend: `.github/workflows/backend-tests.yml`
- Frontend: `.github/workflows/frontend-tests.yml`

Workflows activate the Pixi environment and run the Pixi tasks, posting coverage
summaries.

## Key Features Implemented

### Real-time Segment Discovery
- **Interactive Map**: Leaflet-based map with real-time segment streaming
- **Server-Sent Events**: Efficient streaming of GPX data to frontend
- **Geographic Search**: Bounds-based filtering with PostgreSQL spatial queries
- **Client-side Parsing**: Frontend GPX parsing for optimal performance
- **Map State Persistence**: Automatic saving and restoration of map position and zoom level

### Segment Management
- **Segment List**: Filterable and sortable segment lists with track type filtering
- **Segment Detail View**: Comprehensive segment information with interactive maps and elevation charts
- **Track Type Filtering**: Separate views for segments and routes
- **Distance Calculations**: Real-time distance calculations from map center

### GPX Route Editor
- **File Upload**: Drag-and-drop GPX file upload with validation
- **Visual Editing**: Interactive segment selection with map and elevation chart
- **Surface Classification**: Trail condition metadata (surface type, difficulty, tire recommendations)
- **Chart Visualization**: Real-time elevation profile with Chart.js
- **Commentary Support**: Text, video links, and image attachments for segments

### Storage & Database
- **Dual Storage**: Support for both local filesystem and AWS S3
- **PostgreSQL**: Async database with SQLAlchemy ORM
- **Metadata Management**: Comprehensive track metadata storage
- **File Serving**: Efficient GPX file serving with proper MIME types
- **Database Seeding**: Automated generation of realistic test data

### Development Experience
- **TypeScript**: Strict typing throughout frontend
- **Testing**: Comprehensive test coverage (83.43% frontend, 100% backend core)
- **Code Quality**: Automated linting with Ruff (Python) and ESLint (TypeScript)
- **Environment Management**: Pixi-based development environment
- **Component Architecture**: Modular Vue components with clear separation of concerns
- **Composable Pattern**: Reusable state management with Vue composables
- **Database Seeding**: Automated test data generation for development

## Future Enhancements

- User authentication and personal segment collections
- Social features (sharing, comments, ratings)
- Advanced filtering and sorting options
- Offline map support
- Real-time route tracking
- Mobile app integration
- Advanced analytics and route statistics
