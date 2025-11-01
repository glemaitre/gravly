# Gravly - Find your next gravel ride

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Vue.js](https://img.shields.io/badge/Vue.js-3.3+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5.6+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
[![codecov](https://codecov.io/gh/glemaitre/gravly/branch/main/graph/badge.svg)](https://codecov.io/gh/glemaitre/gravly)

A modern web application for discovering, creating, and viewing cycling routes stored as
GPX files. Built with Vue.js frontend, FastAPI backend, and PostgreSQL for data
persistence.

**Gravly** helps cyclists discover their next gravel adventure by providing:
- 🗺️ **Interactive map discovery** with real-time segment streaming
- ✏️ **Advanced GPX editor** with surface classification and difficulty ratings
- 🚴 **Strava integration** for seamless activity import
- ⚙️ **Wahoo Cloud integration** for route upload and management
- 📍 **Route planner** with interactive waypoint management
- 📊 **Elevation profiles** and detailed route analytics
- 🔐 **Secure authorization** system for editor access control

## Screenshots

> 📸 *Screenshots coming soon - showing the interactive map, route editor, and
> segment details*

## Quick Start

```bash
# 1. Install Pixi
curl -fsSL https://pixi.sh/install.sh | bash

# 2. Install dependencies
pixi run frontend-install

# 3. Setup database
pixi run pg-setup

# 4. Configure environment (see Environment Configuration section)
mkdir -p .env
# Create .env/database, .env/storage, .env/strava, .env/auth_users, .env/server files

# 5. Start the application (in separate terminals)
pixi run start-backend   # Terminal 1: http://localhost:8000 (or configured port)
pixi run start-frontend  # Terminal 2: http://localhost:3000 (or configured port)

# 6. (Optional) Seed test data
pixi run python scripts/test_seeding.py
```

## Table of Contents

- [Screenshots](#screenshots)
- [Quick Start](#quick-start)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
- [Environment Configuration](#environment-configuration)
  - [Database Configuration](#database-configuration)
  - [Storage Configuration](#storage-configuration)
  - [Map Configuration](#map-configuration)
  - [Strava Integration](#strava-integration)
  - [Wahoo Integration](#wahoo-integration)
  - [Editor Authorization System](#editor-authorization-system)
- [Database Seeding](#database-seeding)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Development](#development)
- [Architecture & Performance](#architecture--performance)
- [Testing](#testing)
- [Continuous Integration](#continuous-integration)
- [Key Features Implemented](#key-features-implemented)
- [Future Enhancements](#future-enhancements)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)
- [Acknowledgments](#acknowledgments)

## Features

- **Interactive Map Discovery**: Real-time streaming of cycling segments using
  Server-Sent Events (SSE) with Leaflet maps
- **GPX Route Editor**: Upload and edit GPX files with visual segment selection, surface
  type classification, and difficulty rating
- **Segment Detail View**: Comprehensive segment information with interactive maps,
  elevation charts, and detailed metadata
- **Advanced Segment List**: Filterable and sortable segment lists with track type
  filtering (segments vs routes)
- **Real-time Segment Streaming**: Efficient bounds-based search with client-side GPX
  parsing for optimal performance
- **Map State Persistence**: Automatic saving and restoration of map position and zoom
  level
- **Multi-language Support**: Internationalization with English and French locales
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Advanced Route Analysis**: Elevation profiles, distance calculations, and trail
  condition metadata
- **Media Management**: Upload and manage images and videos for cycling segments
- **Flexible Storage**: Support for both local filesystem and AWS S3 storage backends
- **Database Seeding**: Automated generation of realistic test data for development and
  testing
- **Strava Integration**: Import GPX files directly from Strava activities with OAuth
  authentication
- **Wahoo Cloud Integration**: Upload routes to Wahoo Cloud devices with OAuth
  authentication and GPX to FIT conversion
- **Route Planner**: Interactive route planning tool with waypoint management,
  elevation profiles, and route generation

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
   - Frontend: http://localhost:3000 (or configured FRONTEND_PORT)
   - Backend API: http://localhost:8000 (or configured BACKEND_PORT)
   - API Documentation: http://localhost:8000/docs (or your backend URL)

5. **Seed the database with test data** (optional):
   ```bash
   # Generate 1,000 realistic cycling segments across France
   pixi run python scripts/database_seeding.py

   # Or generate just 5 segments for quick testing
   pixi run python scripts/test_seeding.py
   ```

## Environment Configuration

This project uses separate `.env` files for database, storage, server, and API
configuration. The backend automatically loads environment variables from
`.env/storage`, `.env/database`, and `.env/server` files.

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

4. **Create the Strava configuration file** (`.env/strava`):
   ```bash
   # Strava API Configuration
   STRAVA_CLIENT_ID=your_client_id_here
   STRAVA_CLIENT_SECRET=your_client_secret_here
   STRAVA_TOKENS_FILE_PATH=/secure/path/to/strava_tokens.json
   ```

5. **Create the authorization configuration file** (`.env/auth_users`):
   ```bash
   # Editor Authorization - Authorized Strava Users
   AUTHORIZED_STRAVA_USERS=820773,123456,789012
   ```

6. **Create the Wahoo configuration file** (`.env/wahoo`):
   ```bash
   # Wahoo API Configuration
   WAHOO_CLIENT_ID=your_client_id_here
   WAHOO_CLIENT_SECRET=your_client_secret_here
   WAHOO_CALLBACK_URL=http://localhost:3000/wahoo/callback
   WAHOO_SCOPES=user_read routes_write
   ```

7. **Create the Thunderforest map configuration file** (`.env/thunderforest`):
   ```bash
   # Thunderforest Map API Key
   THUNDERFOREST_API_KEY=your_api_key_here
   ```

8. **Create the server configuration file** (`.env/server`):
   ```bash
   # Server Configuration
   BACKEND_PORT=8000
   BACKEND_HOST=0.0.0.0
   FRONTEND_PORT=3000
   FRONTEND_URL=http://localhost:3000
   BACKEND_URL=http://localhost:8000
   ```

9. **Never commit actual `.env` files** - they contain sensitive information and are
   already in `.gitignore`.

### Storage Configuration

The storage backend is controlled by the `STORAGE_TYPE` variable in `.env/storage`:

- `STORAGE_TYPE=local` - Use local filesystem storage
- `STORAGE_TYPE=s3` - Use AWS S3 storage

### Map Configuration

The application uses Thunderforest for map tiles. Configuration is set in
`.env/thunderforest`:

- `THUNDERFOREST_API_KEY` - API key for Thunderforest map tiles (required)

To get an API key:
1. Visit [Thunderforest](https://www.thunderforest.com/)
2. Sign up for an account
3. Create a new API key
4. Add the key to your `.env/thunderforest` file

**Note**: The backend proxies map tile requests to hide the API key from the
frontend for security.

### Server Configuration

The application's server ports and URLs are configured through environment variables in
`.env/server`:

- `BACKEND_PORT` - Backend server port (default: 8000)
- `BACKEND_HOST` - Backend server host (default: 0.0.0.0)
- `FRONTEND_PORT` - Frontend development server port (default: 3000)
- `FRONTEND_URL` - Frontend URL for CORS and OAuth redirects (default:
  http://localhost:3000)
- `BACKEND_URL` - Backend URL for frontend API calls (default: http://localhost:8000)

**Production Deployment**: When deploying to production, update these values:
```bash
# Example production configuration
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0
FRONTEND_PORT=80
FRONTEND_URL=https://yourdomain.com
BACKEND_URL=https://api.yourdomain.com
```

### Database Configuration

The application uses PostgreSQL for persistent storage. Database connection is
configured through environment variables in `.env/database`:

- `DB_HOST` - Database host (required)
- `DB_PORT` - Database port (required)
- `DB_NAME` - Database name (required)
- `DB_USER` - Database username (required)
- `DB_PASSWORD` - Database password (required)

The application automatically constructs the PostgreSQL connection string from these
individual components.

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

## Wahoo Integration

The application includes comprehensive Wahoo Cloud integration for uploading routes to
Wahoo devices. The integration provides OAuth 2.0 authentication, route upload with GPX
to FIT conversion, route management, and seamless integration with the route editor.

### Setup Wahoo Integration

1. **Create a Wahoo Application**:
   - Go to [Wahoo Developer Portal](https://developers.wahooligan.com/)
   - Register your application
   - Get your client ID and client secret

2. **Configure Environment Variables**:
   Add your Wahoo credentials to the `.env/wahoo` file:
   ```bash
   WAHOO_CLIENT_ID=your_client_id_here
   WAHOO_CLIENT_SECRET=your_client_secret_here
   WAHOO_CALLBACK_URL=http://localhost:3000/wahoo/callback
   WAHOO_SCOPES=user_read routes_write
   ```

### How Wahoo Integration Works

1. **Authentication**: Users authenticate with Wahoo using OAuth 2.0
2. **Route Upload**: Routes can be uploaded directly from the segment detail view
3. **GPX to FIT Conversion**: GPX files are automatically converted to FIT
   format for Wahoo devices
4. **Route Management**: Routes are synced between Gravly and Wahoo Cloud
5. **Automatic Updates**: If a route already exists in Wahoo, it's updated
   instead of creating duplicates

### Wahoo Integration Features

- **OAuth 2.0 Authentication**: Secure login with Wahoo Cloud
- **Database-backed Token Storage**: OAuth tokens stored securely in PostgreSQL
- **Automatic Token Refresh**: Seamless token renewal when access tokens expire
- **Route Upload**: Direct upload of routes to Wahoo Cloud from segment detail view
- **GPX to FIT Conversion**: Automatic conversion of GPX files to FIT format
- **Route Synchronization**: Routes are tracked with external IDs for update support
- **Route Deletion**: Delete routes from Wahoo Cloud
- **Activity Retrieval**: Access to Wahoo activities and route data

### Wahoo API Endpoints

- `GET /api/wahoo/auth-url` - Get OAuth authorization URL
- `POST /api/wahoo/exchange-code` - Exchange authorization code for access token
- `POST /api/wahoo/refresh-token` - Refresh expired access token
- `POST /api/wahoo/deauthorize` - Deauthorize and delete tokens
- `GET /api/wahoo/user` - Get authenticated user information
- `GET /api/wahoo/callback` - Handle OAuth callback
- `POST /api/wahoo/routes/{route_id}/upload` - Upload route to Wahoo Cloud
- `DELETE /api/wahoo/routes/{route_id}` - Delete route from Wahoo Cloud

### Security Notes

- OAuth tokens are stored securely in PostgreSQL database
- Client secret is handled securely on the backend only
- All Wahoo API calls are proxied through the backend for security
- Tokens are automatically refreshed before expiration

## Strava Integration

The application includes comprehensive Strava integration with full OAuth 2.0
authentication, activity retrieval, and GPX data import capabilities. The backend
provides a complete Strava API service with secure token management and comprehensive
error handling.

### Setup Strava Integration

1. **Create a Strava Application**:
   - Go to [Strava API Settings](https://www.strava.com/settings/api)
   - Click "Create App" or "Register Your Application"
   - Fill in the application details:
     - **Application Name**: Your cycling website name
     - **Category**: Choose "Web"
     - **Club**: Leave empty or select a club
     - **Website**: Your website URL (e.g., `http://localhost:5173`)
     - **Authorization Callback Domain**: `localhost` (for development) or your
       production domain

2. **Get Your API Credentials**:
   After creating the app, you'll get:
   - **Client ID**: A number (e.g., `12345`)
   - **Client Secret**: A string (e.g., `abcdef1234567890abcdef1234567890abcdef12`)

3. **Configure Environment Variables**:
   Add your Strava credentials to the `.env/strava` file (see Environment Configuration
   section above). **Important**: The `STRAVA_TOKENS_FILE_PATH` must be set to a secure
   location for storing OAuth tokens. This path should be outside your web root and
   accessible only by your application.

### How Strava Integration Works

1. **Authentication**: Users click "Login with Strava" in the navbar to authenticate
   with Strava using OAuth 2.0
2. **Route Protection**: The editor requires Strava authentication - users are
   automatically redirected to login when accessing protected routes
3. **Activity Import**: Once authenticated, users can import Strava activities directly
   from the editor's sidebar menu
4. **Activity List**: Users see a list of their cycling activities with previews
   including distance, time, elevation, and mini-maps
5. **Import**: Users can select any activity to import its GPX data directly into the
   editor
6. **Processing**: The GPX data is processed the same way as local file uploads,
   maintaining full compatibility with existing editor functionality

### Authentication Flow

The Strava integration uses a sophisticated authentication system:

1. **Global Authentication**: Login/logout buttons are always visible in the navbar
2. **Route Protection**: Protected routes (like editor) automatically check
   authentication status
3. **Smart Redirects**: Users are returned to their original page after authentication
4. **Token Storage**: Access and refresh tokens are stored securely on the backend
5. **Proactive Refresh**: Tokens are automatically refreshed 5 minutes before expiration
6. **Error Handling**: If authentication fails, users are automatically redirected back
   to Strava login
7. **Full Page Reload**: After authentication, the page reloads to ensure navbar updates
   correctly
8. **Seamless Experience**: Users rarely need to manually re-authenticate

### Strava Integration Features

- **Global Authentication**: Login/logout buttons in the navbar for easy access
- **OAuth Authentication**: Secure login with Strava using industry-standard OAuth 2.0
- **Route Protection**: Automatic authentication checks for protected routes
- **Smart Redirects**: Users return to their original page after authentication
- **Automatic Token Refresh**: Seamless token renewal when access tokens expire
- **Smart Authentication Handling**: Automatic redirect to login when authentication
  fails
- **Activity Preview**: Visual previews showing distance, time, elevation, and GPS trace
  for each activity
- **GPX Import**: Direct import of Strava activity GPX data with elevation and time
  information
- **Seamless Integration**: Works with all existing editor functionality including
  charts, segment selection, and metadata editing
- **Backend Processing**: GPX data is processed on the backend using the same pipeline
  as local file uploads
- **Editor Authorization**: Restrictive access control for editor features
  based on authorized Strava user IDs

### User Experience Improvements

The Strava integration provides a modern, seamless user experience:

#### **Authentication States**
- **Not Authenticated**: Orange "Login with Strava" button in navbar
- **Authenticated**: User avatar, name, and dropdown menu in navbar
- **Token Expired**: Automatic refresh or redirect to login
- **Logout**: Clean return to home page with login button restored

#### **Smart Navigation**
- **Context Preservation**: Users return to their original page after authentication
- **Route Protection**: Editor automatically redirects unauthenticated users to login
- **Full Page Reload**: Ensures navbar updates correctly after authentication
- **Seamless Flow**: No manual navigation required

#### **Mobile Responsive**
- **Desktop**: Full login button with text and Strava branding
- **Tablet**: Icon-only login button to save space
- **Mobile**: Compact authentication interface

### Troubleshooting Strava Integration

#### Common Issues

1. **"Invalid redirect_uri"**: Check that your callback domain in Strava settings
   matches your development/production domain
2. **"Invalid client_id"**: Verify your `STRAVA_CLIENT_ID` is correct in
   `.env/strava`
3. **"Invalid client_secret"**: Verify your `STRAVA_CLIENT_SECRET` is correct in
   `.env/strava`
4. **CORS errors**: Make sure your callback domain is properly configured in Strava

#### Development vs Production

- **Development**: Use `localhost` as the callback domain in Strava settings
- **Production**: Use your actual domain (e.g., `mycyclingapp.com`) without `http://` or
  `https://`

### Strava API Limits

Strava has rate limits for API calls:
- **Default**: 1,000 requests per 15 minutes
- **Premium**: 1,000 requests per 15 minutes (same as default)

The integration is designed to be efficient and should not hit these limits under normal
usage.

### Strava Service Architecture

The backend includes a comprehensive Strava service (`backend/src/services/strava.py`)
that provides:

#### **Core Features**
- **OAuth 2.0 Flow**: Complete authentication flow with authorization URL generation and
  token exchange
- **Token Management**: Automatic token refresh with secure filesystem storage
- **Activity Retrieval**: Paginated access to user activities with comprehensive metadata
- **GPX Processing**: Direct GPX data retrieval and processing from Strava streams
- **Athlete Information**: Access to authenticated user profile data

#### **Error Handling**
- **HTTPException Propagation**: Proper handling of Strava API errors with correct HTTP
  status codes
- **Authentication Failures**: Comprehensive handling of token expiration and refresh
  scenarios
- **Rate Limiting**: Proper handling of Strava API rate limits
- **Network Errors**: Robust error handling for network failures and API unavailability

#### **Security Features**
- **Secure Configuration**: Environment-based configuration with mandatory token file
  path
- **Token Encryption**: Secure storage of OAuth tokens with proper file permissions
- **Client Secret Protection**: Backend-only handling of sensitive credentials
- **Request Validation**: Proper validation of all API requests and responses

### Security Notes

- Client secret is handled securely on the backend
- OAuth tokens are stored in localStorage (consider using httpOnly cookies for
  production)
- All Strava API calls are proxied through the backend for security
- **Secure Token Storage**: OAuth tokens are stored securely in the location specified
  by `STRAVA_TOKENS_FILE_PATH` environment variable for persistence across sessions
- **Never commit tokens**: The token file is automatically ignored by git and should
  never be committed to version control
- **Token Security**: The token file path must be set to a secure location outside your
  web root and accessible only by your application

## Database Seeding

The project includes comprehensive database seeding scripts to generate realistic test
data for development and testing purposes.

### Seeding Scripts

- **`scripts/database_seeding.py`**: Generates 1,000 realistic 5km cycling segments
  across 13 French regions
- **`scripts/test_seeding.py`**: Generates 5 segments for quick testing
- **`scripts/seed_auth_users.py`**: Seeds authorized users from `.env/auth_users` file

### Features of Generated Data

- **Geographic Distribution**: Segments distributed across 13 French regions with
  realistic GPS coordinates
- **Realistic Routes**: 5km cycling routes with elevation changes and proper GPS point
  distribution
- **Varied Surface Types**: Different surface types (paved roads, trails, etc.) with
  realistic probabilities
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

# Auth users seeding (if authorization enabled)
pixi run python scripts/seed_auth_users.py
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

## Editor Authorization System

The application includes a sophisticated authorization system that controls access to
the route editor based on authorized Strava user IDs. This enables selective access to
premium editing features while maintaining security.

### Overview

The authorization system provides fine-grained control over who can access the GPX route
editor:
- **Strava Authentication**: Users must be authenticated with Strava
- **Authorization Check**: Backend validates authorized user IDs against database
- **Frontend UI Control**: Editor button only visible to authenticated and authorized
  users
- **Environment Configuration**: Authorized users configured via `.env/auth_users` file

### Setup Editor Authorization

1. **Create the authorization configuration file**:
   ```bash
   # Create from example template
   cp .env/auth_users.example .env/auth_users
   ```

2. **Configure authorized users** in `.env/auth_users`:
   ```bash
   # List of Strava user IDs with editor access
   # Format: comma-separated Strava IDs (no spaces)
   AUTHORIZED_STRAVA_USERS=820773,123456,789012
   ```

3. **Seed the database** with authorized users:
   ```bash
   # Run the authorization seeder
   pixi run python scripts/seed_auth_users.py
   ```

### Authorization Features

- **Database-driven Control**: Authorized users stored in PostgreSQL `auth_users` table
- **Automatic Checking**: Frontend automatically validates authorization on Strava
  authentication
- **UI Hiding**: Editor button hidden from unauthorized users (not shown at all)
- **Error Prevention**: Unauthorized users cannot access editor routes
- **Secure Backend**: All authorization checks validated server-side
- **Environment Configuration**: Easy management via `.env/auth_users` file

### Authorization Flow

1. **User Authentication**: User logs in with Strava OAuth
2. **Authorization Request**: Frontend calls
   `/api/auth/check-authorization?strava_id=<ID>`
3. **Database Check**: Backend validates Strava ID against `auth_users` table
4. **Response**: Returns authorization status and user information
5. **UI Update**: Editor button appears/disappears based on authorization
6. **Real-time Updates**: Authorization checked on any authentication state changes

### Backend API Endpoints

#### Check Authorization
```
GET /api/auth/check-authorization?strava_id=820773
```

**Response:**
```json
{
  "authorized": true,
  "user": {
    "strava_id": 820773,
    "firstname": "Test",
    "lastname": "User"
  }
}
```

#### List Authorized Users (Admin)
```
GET /api/auth/users
```

**Response:**
```json
[
  {
    "id": 1,
    "strava_id": 820773,
    "firstname": "Test",
    "lastname": "User",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### Security Features

- **Database Validation**: Server-side authorization checks against PostgreSQL
- **Environment Security**: No sensitive data hardcoded in repository
- **Token Protection**: OAuth tokens managed securely by backend
- **UI Protection**: Frontend UI prevents unauthorized access to editor
- **Route Protection**: Backend validates authorization on editor access
- **Error Handling**: Proper HTTP status codes and error messages
- **Cache Management**: Frontend caching with automatic refresh on auth changes

### Development Configuration

#### Example Configuration
The `.env/auth_users.example` template shows:
```bash
# Default authorization setup with test user
AUTHORIZED_STRAVA_USERS=820773

# For additional users, use comma separation:
# AUTHORIZED_STRAVA_USERS=820773,123456,789012
```

#### Manual Database Management
You can also manually add authorized users directly to the database:
```sql
INSERT INTO auth_users (strava_id, firstname, lastname)
VALUES (123456, 'Test', 'User');
```

### Troubleshooting

#### Common Issues
- **Editor button not showing**: Verify user's Strava ID exists in `auth_users` table
- **Database errors**: Ensure `auth_users` table has been created (run seeder)
- **Environment not loaded**: Check `.env/auth_users` file exists and has valid Strava
  IDs
- **No authorization response**: Check backend authorization endpoints are working
- **Authentication failures**: Ensure Strava OAuth integration is properly configured

#### Verification Commands
```bash
# Check if authorization endpoint is working
curl "http://localhost:8000/api/auth/check-authorization?strava_id=820773"

# Verify authorized users in database
curl "http://localhost:8000/api/auth/users"

# Check if environment is loaded correctly
pixi run python -c "
import os
print('AUTHORIZED_STRAVA_USERS:', os.getenv('AUTHORIZED_STRAVA_USERS', 'Not found'))
"
```

### Authorization vs Authentication

| Feature | Authentication | Authorization |
|---------|---------------|---------------|
| **Purpose** | Verify Strava login | Control feature access |
| **Scope** | Global login state | Specific feature (editor) |
| **Storage** | OAuth tokens (secure) | Authorized users (database) |
| **UI Impact** | Login/logout buttons | Editor button visibility |
| **Validation** | Backend Strava API | Backend authorization DB |
| **Security** | OAuth 2.0 tokens | Database-driven user list |

### Running the Application

#### Start the Backend
```bash
# Using pixi (loads from .env/storage and .env/database)
pixi run start-backend

# Or manually
source ../.env/strava && uvicorn backend.src.main:app --reload --host 0.0.0.0 --port 8000
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
gravly/
├── backend/                 # FastAPI backend
│   ├── src/
│   │   ├── main.py         # Main API server with streaming endpoints
│   │   ├── models/         # SQLAlchemy models and Pydantic schemas
│   │   │   ├── track.py    # Track model and response schemas
│   │   │   ├── image.py    # Track image model and schemas
│   │   │   ├── video.py    # Track video model and schemas
│   │   │   ├── auth_user.py # Authorized user model and schemas
│   │   │   ├── wahoo_token.py # Wahoo OAuth token model and schemas
│   │   │   └── base.py     # Base model configuration
│   │   ├── services/       # Service modules
│   │   │   ├── strava.py   # Strava API integration service with OAuth and GPX processing
│   │   │   └── wahoo/      # Wahoo API integration service
│   │   │       ├── client.py      # Wahoo API client
│   │   │       ├── service.py     # Wahoo service with token management
│   │   │       ├── protocol.py    # API protocol definitions
│   │   │       └── exceptions.py  # Wahoo-specific exceptions
│   │   └── utils/          # Utility modules
│   │       ├── config.py   # Environment configuration
│   │       ├── storage.py  # Storage managers (S3/Local)
│   │       ├── gpx.py      # GPX parsing utilities
│   │       └── postgres.py # Database configuration
│   └── tests/              # Backend tests with comprehensive coverage
├── frontend/               # Vue.js frontend
│   ├── src/
│   │   ├── components/     # Vue components
│   │   │   ├── Explorer.vue # Interactive map with streaming segments
│   │   │   ├── Editor.vue      # GPX route editor with chart visualization
│   │   │   ├── SegmentDetail.vue # Detailed segment view with map and charts
│   │   │   ├── SegmentList.vue   # Filterable segment list component
│   │   │   ├── Navbar.vue        # Navigation component with Strava authentication
│   │   │   ├── RoutePlanner.vue  # Route planning component with waypoint management
│   │   │   ├── RoutePlannerSidebar.vue # Route planner sidebar with filters and controls
│   │   │   ├── StravaCallback.vue # Strava OAuth callback handler
│   │   │   ├── StravaActivityList.vue # Strava activities list component
│   │   │   ├── StravaActivityDetailsModal.vue # Strava activity details modal
│   │   │   └── WahooCallback.vue # Wahoo OAuth callback handler
│   │   ├── composables/    # Vue composables
│   │   │   ├── useMapState.ts    # Map state persistence management
│   │   │   ├── useStravaApi.ts   # Strava API integration and authentication composable
│   │   │   ├── useStravaActivities.ts # Strava activities management composable
│   │   │   ├── useWahooApi.ts    # Wahoo API integration and authentication composable
│   │   │   └── useAuthorization.ts # Editor authorization management
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
│   ├── storage             # Storage configuration
│   ├── strava              # Strava API configuration
│   ├── wahoo               # Wahoo API configuration
│   ├── thunderforest       # Thunderforest map API key
│   ├── auth_users          # Editor authorization configuration
│   ├── server              # Server port and URL configuration
│   └── strava_tokens.json  # Strava OAuth tokens (auto-generated, git-ignored)
├── scripts/                # Database seeding and utility scripts
│   ├── database_seeding.py # Generate 1,000 realistic cycling segments
│   ├── test_seeding.py     # Generate 5 test segments
│   ├── seed_auth_users.py  # Authorized users for editor access
│   └── README_auth_users.md # Authorization documentation
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

### Strava Integration
- `GET /api/strava/auth-url?state={route}` - Get Strava OAuth authorization URL with
  optional state parameter for redirect
- `POST /api/strava/exchange-code` - Exchange Strava authorization code for access token
- `POST /api/strava/refresh-token` - Refresh expired Strava access token
- `GET /api/strava/activities?page={page}&per_page={per_page}` - Get paginated list of
  Strava activities
- `GET /api/strava/activities/{activity_id}/gpx` - Get GPX data for a specific Strava
  activity

### Wahoo Integration
- `GET /api/wahoo/auth-url?state={state}` - Get Wahoo OAuth authorization URL
- `POST /api/wahoo/exchange-code` - Exchange Wahoo authorization code for access token
- `POST /api/wahoo/refresh-token` - Refresh expired Wahoo access token
- `POST /api/wahoo/deauthorize` - Deauthorize and delete tokens
- `GET /api/wahoo/user?wahoo_id={wahoo_id}` - Get authenticated Wahoo user information
- `GET /api/wahoo/callback?code={code}` - Handle Wahoo OAuth callback
- `POST /api/wahoo/routes/{route_id}/upload?wahoo_id={wahoo_id}` - Upload route to Wahoo
  Cloud
- `DELETE /api/wahoo/routes/{route_id}?wahoo_id={wahoo_id}` - Delete route from Wahoo
  Cloud

### Editor Authorization
- `GET /api/auth/check-authorization?strava_id={strava_id}` - Check if Strava user is
  authorized for editor access
- `GET /api/auth/users` - List all authorized users (admin endpoint)

### Track Media Management
- `GET /api/tracks/{track_id}/images` - Get images for a specific track
- `POST /api/tracks/{track_id}/images` - Upload images for a track
- `DELETE /api/tracks/{track_id}/images/{image_id}` - Delete a specific track image
- `GET /api/tracks/{track_id}/videos` - Get videos for a specific track
- `POST /api/tracks/{track_id}/videos` - Upload videos for a track
- `DELETE /api/tracks/{track_id}/videos/{video_id}` - Delete a specific track video

### Map Tiles
- `GET /api/utils/map-tiles/{z}/{x}/{y}.png` - Proxy endpoint for Thunderforest map
  tiles (hides API key from frontend)

**Features**:
- **OAuth 2.0 Authentication**: Complete OAuth flow with secure token management (Strava
  and Wahoo)
- **Automatic Token Refresh**: Seamless token renewal when access tokens expire
- **Activity Retrieval**: Paginated access to user's Strava activities
- **GPX Data Processing**: Direct import and processing of Strava activity GPX files
- **Wahoo Route Upload**: Upload routes to Wahoo Cloud with GPX to FIT conversion
- **Comprehensive Error Handling**: Proper HTTP status codes and error messages
- **Secure Token Storage**: OAuth tokens stored securely in PostgreSQL database

### Segment Discovery (Streaming)
- `GET /api/segments/search` - Stream segments within geographic bounds using
  Server-Sent Events
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

### Common Tasks Reference

#### Development Servers
```bash
# Start backend API server (http://localhost:8000)
pixi run start-backend

# Start frontend dev server (http://localhost:5173)
pixi run start-frontend

# Install frontend dependencies
pixi run frontend-install

# Build frontend for production
pixi run frontend-build
```

#### Database Management
```bash
# First-time setup (init + start + create)
pixi run pg-setup

# Regular operations
pixi run pg-start                 # Start PostgreSQL server
pixi run pg-stop                  # Stop PostgreSQL server
pixi run pg-status                # Check PostgreSQL server status

# Database operations
pixi run pg-create-db             # Create database
pixi run pg-drop-db               # Drop database
pixi run pg-cleanup               # Stop, drop, and erase database
pixi run pg-erase                 # Erase database files
```

#### Code Quality
```bash
# Linting (with auto-fix)
pixi run -e dev lint-backend      # Python (Ruff)
pixi run -e dev lint-frontend     # TypeScript (ESLint)
pixi run -e dev lint-all          # Both backend & frontend

# Formatting
pixi run -e dev format-backend    # Python (Ruff)
pixi run -e dev format-frontend   # TypeScript (Prettier)
pixi run -e dev format-all        # Both backend & frontend

# Type checking
pixi run -e dev type-check-frontend  # TypeScript type checking

# Pre-commit hooks
pixi run -e lint install-pre-commit  # Install git hooks
pixi run -e lint pre-commit          # Run pre-commit checks
pixi run -e lint pre-commit-update   # Update pre-commit hooks
```

#### Testing
```bash
# Run tests with coverage
pixi run -e dev test-backend      # Backend pytest
pixi run -e dev test-frontend     # Frontend Vitest

# Watch mode (for development)
cd frontend && npm run test       # Frontend watch mode
```

#### Database Seeding
```bash
# Quick test seeding (5 segments)
pixi run python scripts/test_seeding.py

# Full seeding (1,000 segments)
pixi run python scripts/database_seeding.py

# Seed authorized users
pixi run python scripts/seed_auth_users.py
```

**Note**: Task definitions use Pixi's `cwd` and `depends-on` fields for clarity. Use the
`-e dev` flag to access development environment features (testing, linting).

## Architecture & Performance

### Architecture Highlights

**Gravly** is built with a modern, scalable architecture:

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Vue.js 3 +    │◄────────┤   FastAPI +      │◄────────┤   PostgreSQL    │
│   TypeScript    │  HTTP   │   Python 3.10+   │  Async  │   Database      │
│   Frontend      │  SSE    │   Backend        │  SQL    │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
        │                           │
        │                           │
        ▼                           ▼
┌─────────────────┐         ┌──────────────────┐
│   Leaflet Maps  │         │  Storage Layer   │
│   Chart.js      │         │  (S3 / Local)    │
└─────────────────┘         └──────────────────┘
                                    │
                                    ▼
                            ┌──────────────────┐
                            │   Strava API     │
                            │   OAuth 2.0      │
                            └──────────────────┘
```

### Performance Optimizations

#### Client-Side Processing
- **GPX Parsing**: Moved from backend to frontend for reduced server load
- **Streaming Architecture**: Server-Sent Events for real-time data delivery
- **Bounds-based Filtering**: Efficient geographic queries with PostgreSQL
- **Client-side Caching**: Layer tracking to prevent redundant map redraws
- **Distance Calculations**: Real-time distance calculations from map center to segments

#### Backend Optimizations
- **Async Database**: PostgreSQL with asyncpg for concurrent operations
- **Streaming Responses**: Real-time segment delivery without blocking
- **Storage Abstraction**: Unified API for S3 and local storage
- **Error Handling**: Comprehensive error recovery and logging

#### Frontend Optimizations
- **Debounced Search**: Prevents excessive API calls during map interactions
- **Incremental Updates**: Only updates map with new segments
- **Zoom Optimization**: Avoids unnecessary searches when zooming in
- **Map State Persistence**: Automatic saving and restoration of map state using
  localStorage
- **Composable Architecture**: Reusable Vue composables for state management
- **TypeScript**: Strict typing for better performance and reliability

### Performance Metrics

- **Test Coverage**: 82.96% frontend, 100% backend core modules
- **Backend Response Time**: < 50ms for segment queries (typical)
- **Frontend Load Time**: < 2s initial page load
- **Streaming Latency**: Real-time SSE with < 100ms delay
- **Database Performance**: Spatial queries optimized with PostgreSQL GIS

## Testing

### Backend Testing
- **Framework**: pytest with comprehensive coverage
- **Coverage**: 100% coverage for core modules including:
  - `backend/src/main.py` - API endpoints and streaming functionality (99% coverage)
  - `backend/src/services/strava.py` - Strava API integration service (100% coverage)
  - `backend/src/utils/config.py` - Environment configuration management (100% coverage)
  - `backend/src/utils/storage.py` - S3 and local storage managers (100% coverage)
  - `backend/src/models/track.py` - Data models and schemas (100% coverage)
  - `backend/src/utils/` - All utility modules (100% coverage)
- **Run**: `pixi run test-backend`
- **Features**:
  - **Comprehensive Strava Testing**: 22 tests covering all Strava API endpoints
  - **Error Handling Coverage**: HTTPException propagation, authentication failures, API
    errors
  - **Mock Integration**: stravalib mock fixture integration for realistic API testing
  - **Async Database Testing**: PostgreSQL testing with async operations
  - **S3 Mocking**: moto-based S3 testing for storage operations
  - **Security Testing**: Token management, OAuth flow validation

### Frontend Testing
- **Framework**: Vitest + Vue Test Utils + Testing Library with jsdom
- **Coverage**: 82.96% overall coverage with:
  - `Explorer.vue`: 58.68% (map interactions, EventSource streaming)
  - `SegmentList.vue`: Comprehensive segment list functionality
  - `SegmentDetail.vue`: Detailed segment view and interactions
  - `Editor.vue`: 73.42% (route editing functionality)
  - `Navbar.vue`: 88.78% (navigation and language switching)
  - `gpxParser.ts`: 92.8% (comprehensive GPX parsing tests)
  - `useMapState.ts`: Map state persistence composable
- **Run**: `pixi run test-frontend`
- **Features**: Component testing, Leaflet mocking, EventSource simulation, composable
  testing

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
summaries and uploading coverage reports to Codecov.

### Codecov Integration

Test coverage is automatically uploaded to
[Codecov](https://codecov.io/gh/glemaitre/gravly) on each push/PR. The coverage badge in
the README shows the current coverage percentage for the entire project.

**Setup for Repository Maintainers:**

1. Sign up at [Codecov](https://codecov.io/) with your GitHub account
2. Add the repository to Codecov
3. Copy the repository upload token from Codecov settings
4. Add the token as a GitHub secret:
   - Go to repository **Settings** > **Secrets and variables** > **Actions**
   - Create a new secret named `CODECOV_TOKEN`
   - Paste the token from Codecov

The workflows will automatically upload coverage reports:
- **Backend**: XML coverage report from pytest (`backend/coverage.xml`)
- **Frontend**: LCOV coverage report from Vitest (`frontend/coverage/lcov.info`)

## Key Features Implemented

### Real-time Segment Discovery
- **Interactive Map**: Leaflet-based map with real-time segment streaming
- **Server-Sent Events**: Efficient streaming of GPX data to frontend
- **Geographic Search**: Bounds-based filtering with PostgreSQL spatial queries
- **Client-side Parsing**: Frontend GPX parsing for optimal performance
- **Map State Persistence**: Automatic saving and restoration of map position and zoom
  level

### Segment Management
- **Segment List**: Filterable and sortable segment lists with track type filtering
- **Segment Detail View**: Comprehensive segment information with interactive maps and
  elevation charts
- **Track Type Filtering**: Separate views for segments and routes
- **Distance Calculations**: Real-time distance calculations from map center

### GPX Route Editor
- **File Upload**: Drag-and-drop GPX file upload with validation
- **Strava Integration**: Import GPX files directly from Strava activities with OAuth
  authentication
- **Wahoo Integration**: Upload routes to Wahoo Cloud devices with automatic GPX to FIT
  conversion
- **Route Protection**: Editor requires Strava authentication for access
- **Visual Editing**: Interactive segment selection with map and elevation chart
- **Surface Classification**: Trail condition metadata (surface type, difficulty, tire
  recommendations)
- **Chart Visualization**: Real-time elevation profile with Chart.js
- **Commentary Support**: Text, video links, and image attachments for segments
- **Media Management**: Upload and manage images and videos for cycling segments

### Route Planner
- **Interactive Waypoint Management**: Add, move, and remove waypoints on the map
- **Multiple Routing Modes**: Standard routing, start/end mode, and free mode
- **Elevation Profiles**: Real-time elevation visualization with gain/loss statistics
- **Route Generation**: Automatic route generation from selected waypoints
- **Segment Integration**: Add segments from the explorer to your route
- **Filterable Segment List**: Filter segments by difficulty, surface type, and tire
  recommendations
- **State Persistence**: Automatically saves route state to localStorage
- **Undo/Redo Support**: History management for route editing
- **Route Saving**: Save planned routes to the database with Strava authentication

### Authentication System
- **Global Authentication**: Navbar-based login/logout with Strava OAuth 2.0
- **Route Protection**: Automatic authentication checks for protected routes
- **Token Management**: Secure backend token storage with automatic refresh
- **Smart Redirects**: Users return to original page after authentication
- **Full Page Reload**: Ensures proper navbar state updates
- **Mobile Responsive**: Adaptive authentication UI for all screen sizes

### Authorization System
- **Editor Access Control**: Restrictive editor access based on authorized Strava user
  IDs
- **Database-driven Control**: PostgreSQL-stored authorized user list
- **Environment Configuration**: Easy management via `.env/auth_users` file
- **Frontend UI Control**: Editor button shown/hidden based on authorization
- **Backend Validation**: Server-side authorization checks for security
- **Seamless Integration**: Works with existing Strava authentication system

### Wahoo Cloud Integration
- **OAuth 2.0 Authentication**: Secure login with Wahoo Cloud
- **Database-backed Token Storage**: OAuth tokens stored securely in PostgreSQL
- **Automatic Token Refresh**: Seamless token renewal when access tokens expire
- **Route Upload**: Direct upload of routes to Wahoo Cloud from segment detail view
- **GPX to FIT Conversion**: Automatic conversion of GPX files to FIT format for Wahoo
  devices
- **Route Synchronization**: Routes tracked with external IDs for update support
- **Route Management**: Delete routes from Wahoo Cloud

### Storage & Database
- **Dual Storage**: Support for both local filesystem and AWS S3
- **PostgreSQL**: Async database with SQLAlchemy ORM
- **Metadata Management**: Comprehensive track metadata storage
- **File Serving**: Efficient GPX file serving with proper MIME types
- **Media Storage**: Support for images and videos with metadata tracking
- **Database Seeding**: Automated generation of realistic test data

### Development Experience
- **TypeScript**: Strict typing throughout frontend
- **Testing**: Comprehensive test coverage (82.96% frontend, 100% backend core)
- **Code Quality**: Automated linting with Ruff (Python) and ESLint (TypeScript)
- **Environment Management**: Pixi-based development environment
- **Component Architecture**: Modular Vue components with clear separation of concerns
- **Composable Pattern**: Reusable state management with Vue composables
- **Database Seeding**: Automated test data generation for development

## Future Enhancements

- Personal segment collections and favorites
- Social features (sharing, comments, ratings)
- Advanced filtering and sorting options (difficulty, surface type, region)
- Offline map support with progressive web app (PWA)
- Real-time route tracking and live activity sharing
- Native mobile app integration
- Advanced analytics and route statistics dashboard
- Route planning with multi-segment itineraries
- Weather integration for route conditions
- Community-contributed route reviews and photos

## Troubleshooting

### Common Issues

#### PostgreSQL Issues

**Problem**: `pg_ctl: command not found`
```bash
# Solution: Ensure Pixi is properly activated
pixi shell
```

**Problem**: Database connection refused
```bash
# Solution: Check if PostgreSQL is running
pixi run pg-status

# If not running, start it
pixi run pg-start
```

**Problem**: Port 5432 already in use
```bash
# Solution: Stop existing PostgreSQL or change port in .env/database
# To stop system PostgreSQL (macOS)
brew services stop postgresql

# Or find process using port 5432
lsof -i :5432
kill <PID>
```

#### Frontend Issues

**Problem**: `npm install` fails or missing dependencies
```bash
# Solution: Clean install
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Problem**: Port 5173 already in use
```bash
# Solution: Kill process or change port
# Change port in vite.config.js or kill existing process
lsof -i :5173
kill <PID>
```

**Problem**: TypeScript errors after update
```bash
# Solution: Clear cache and rebuild
cd frontend
npm run type-check
rm -rf dist
npm run build
```

#### Backend Issues

**Problem**: `ModuleNotFoundError` when running backend
```bash
# Solution: Ensure you're in the pixi environment
pixi shell
# Or run with pixi
pixi run start-backend
```

**Problem**: `.env` files not loaded
```bash
# Solution: Check .env directory structure
ls -la .env/
# Ensure files exist: database, storage, strava, auth_users
# Check file permissions
chmod 644 .env/*
```

**Problem**: Strava integration not working
```bash
# Solution: Verify Strava credentials
cat .env/strava
# Check callback URL matches Strava app settings
# Ensure STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET are correct
```

#### Storage Issues

**Problem**: GPX files not uploading (local storage)
```bash
# Solution: Check directory permissions
mkdir -p scratch/local_storage
chmod -R 755 scratch/local_storage
```

**Problem**: S3 storage errors
```bash
# Solution: Verify AWS credentials
aws s3 ls s3://your-bucket-name
# Check .env/storage has correct AWS credentials
```

### Getting Help

If you encounter issues not covered here:
1. Check the [API documentation](http://localhost:8000/docs) for backend errors
2. Review browser console for frontend errors
3. Check `postgres.log` for database errors
4. Open an issue on GitHub with error details

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository** and create a feature branch
2. **Follow the code style**: 
   - Python: Ruff (configured in `pyproject.toml`)
   - TypeScript: ESLint + Prettier (configured in `frontend/eslint.config.js`)
3. **Write tests** for new features:
   - Backend: pytest in `backend/tests/`
   - Frontend: Vitest in `frontend/src/__tests__/`
4. **Run the test suite** before submitting:
   ```bash
   pixi run -e dev test-backend
   pixi run -e dev test-frontend
   pixi run -e dev lint-all
   pixi run -e dev format-all
   pixi run -e dev type-check-frontend
   ```
5. **Submit a pull request** with a clear description of changes

### Development Workflow

1. Make your changes in a feature branch
2. Ensure all tests pass locally
3. Run linters and formatters
4. Commit with clear, descriptive messages
5. Push and create a pull request

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Support

For issues, questions, or contributions:
- 🐛 **Report bugs**: Open an issue on GitHub
- 💡 **Feature requests**: Open an issue with the "enhancement" label
- 📧 **Contact**: [Your contact information]

## Acknowledgments

- **Leaflet**: Interactive mapping library
- **FastAPI**: Modern Python web framework
- **Vue.js**: Progressive JavaScript framework
- **Strava API**: Activity data integration
- **Pixi**: Cross-platform package management
