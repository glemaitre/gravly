# Cycling Routes Website

A modern web application for discovering and viewing cycling routes stored as GPX files. Built with Vue.js frontend, FastAPI backend, and Elasticsearch for search functionality.

## Features

- **Interactive Map Search**: Search for cycling routes using an interactive map with OpenStreetMap and cycling-specific layers
- **Route Cards**: Browse routes with mini-map previews and key statistics (distance, elevation gain)
- **Detailed Route Viewer**: View complete routes with synchronized map and
  elevation profile
- **Playback Mode**: Animate through routes with synchronized map and elevation chart
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Frontend**: Vue.js 3, Leaflet, Chart.js
- **Backend**: FastAPI, Python
- **Database**: PostgreSQL (via conda-forge)
- **Search**: Elasticsearch
- **Storage**: Local filesystem (development) or AWS S3 (production)
- **Environment**: Pixi (conda-based environment management)

## Prerequisites

- Pixi (for environment management)
- Elasticsearch (running on localhost:9200)
- PostgreSQL (installed via Pixi - see setup instructions)

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

   # Setup PostgreSQL database
   pixi run pg-setup

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
├── .env/                   # Environment configuration files
│   ├── database            # Database configuration
│   └── storage             # Storage configuration
├── mock_gpx/               # Sample GPX files for testing
├── scripts/                # Setup and utility scripts
│   └── setup_elasticsearch.py
├── postgres_data/          # PostgreSQL data directory (created by pg-setup)
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
# Start development servers
pixi run start-backend            # Backend server
pixi run start-frontend           # Frontend development server

# Database management
pixi run pg-setup                 # Initialize PostgreSQL database (first time)
pixi run pg-start                 # Start PostgreSQL server
pixi run pg-stop                  # Stop PostgreSQL server
pixi run pg-status                # Check PostgreSQL server status

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

## Mock Data

The application includes sample GPX files in the `mock_gpx/` directory for testing.
These are automatically loaded into Elasticsearch when you run the setup script.

For S3-based loading at startup, configure env vars `S3_BUCKET` and optional
`S3_PREFIX`. Elasticsearch persists indexed data; consider loading mock data only if the
index is empty.

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

Workflows activate the Pixi environment and run the Pixi tasks, posting coverage
summaries.

## Future Enhancements

- User authentication and personal ride collections
- Social features (sharing, comments, ratings)
- Advanced filtering and sorting options
- GPX file upload functionality
- Real-time route tracking
- Database integration for persistent storage
