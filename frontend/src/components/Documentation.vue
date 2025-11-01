<template>
  <div class="documentation-page">
    <div class="documentation-container">
      <h1 class="documentation-title">{{ $t('documentation.title') }}</h1>

      <nav class="documentation-nav">
        <a
          href="#connections"
          @click.prevent="scrollToSection('connections')"
          class="nav-link"
          :class="{ active: activeSection === 'connections' }"
        >
          {{ $t('documentation.connections') }}
        </a>
        <a
          href="#explorer"
          @click.prevent="scrollToSection('explorer')"
          class="nav-link"
          :class="{ active: activeSection === 'explorer' }"
        >
          {{ $t('documentation.explorer') }}
        </a>
        <a
          href="#planner"
          @click.prevent="scrollToSection('planner')"
          class="nav-link"
          :class="{ active: activeSection === 'planner' }"
        >
          {{ $t('documentation.planner') }}
        </a>
        <a
          v-if="isEditorAuthorized"
          href="#editor"
          @click.prevent="scrollToSection('editor')"
          class="nav-link"
          :class="{ active: activeSection === 'editor' }"
        >
          {{ $t('documentation.editor') }}
        </a>
      </nav>

      <div class="documentation-content">
        <!-- Connections Section -->
        <section
          id="connections"
          ref="connectionsSection"
          class="documentation-section"
        >
          <h2 class="section-title">{{ $t('documentation.connections') }}</h2>
          <div class="section-content">
            <p>
              Gravly integrates with Strava and Wahoo to enhance your experience.
              Connect these services to unlock additional features and capabilities.
            </p>

            <h3>Connecting Services</h3>
            <p>
              To connect or manage services, click the <strong>Menu</strong> button
              (three dots) in the top-right corner of the navbar. You'll find the
              "Connected Services" section at the top of the menu.
            </p>

            <!-- Screenshot -->
            <div class="media-content">
              <img
                :src="connectedServicesImage"
                alt="Connected Services Menu showing Strava and Wahoo connection status"
                class="documentation-image documentation-image-connected-services"
              />
            </div>

            <h3>Strava Connection</h3>
            <p>
              Connecting with Strava enables several important features and is required
              for some advanced functionality.
            </p>

            <h4>What Strava Enables</h4>
            <ul>
              <li>
                <strong>Editor Access:</strong> Strava authentication is required to
                access the Editor, where you can create and edit segments
              </li>
              <li>
                <strong>Save Routes:</strong> Save your planned routes to the Gravly
                database for future access
              </li>
              <li>
                <strong>Import Activities:</strong> Import GPX data directly from your
                Strava activities into the Editor
              </li>
              <li>
                <strong>View Saved Routes:</strong> Access routes saved by you and other
                users in the Explorer
              </li>
              <li>
                <strong>Personalization:</strong> Your Strava profile information is
                displayed when connected
              </li>
            </ul>

            <h4>How to Connect Strava</h4>
            <ol>
              <li>Click the <strong>Menu</strong> button in the top-right corner</li>
              <li>In the "Connected Services" section, find the Strava service</li>
              <li>
                Click the <strong>"Connect with Strava"</strong> button (if not already
                connected)
              </li>
              <li>You'll be redirected to Strava to authorize the connection</li>
              <li>
                After authorizing, you'll be redirected back to Gravly and your
                connection will be active
              </li>
            </ol>

            <!-- Video -->
            <div class="media-content">
              <video
                :src="connectStravaVideo"
                controls
                class="documentation-video"
                preload="metadata"
              >
                Your browser does not support the video tag.
              </video>
            </div>

            <h4>Disconnecting Strava</h4>
            <p>
              To disconnect from Strava, click the disconnect button (<i
                class="fas fa-sign-out-alt"
              ></i
              >) next to the Strava service in the menu. Note that disconnecting may
              limit access to features that require authentication.
            </p>

            <h3>Wahoo Connection</h3>
            <p>
              Connecting with Wahoo allows you to upload routes directly to your Wahoo
              devices and synchronize routes with Wahoo Cloud.
            </p>

            <h4>What Wahoo Enables</h4>
            <ul>
              <li>
                <strong>Route Upload:</strong> Upload routes directly to Wahoo Cloud
                from the segment detail page
              </li>
              <li>
                <strong>Automatic Format Conversion:</strong> GPX files are
                automatically converted to FIT format for Wahoo device compatibility
              </li>
              <li>
                <strong>Route Synchronization:</strong> Routes are synchronized between
                Gravly and Wahoo Cloud
              </li>
              <li>
                <strong>Route Management:</strong> Update or delete routes that have
                been uploaded to Wahoo Cloud
              </li>
            </ul>

            <h4>How to Connect Wahoo</h4>
            <ol>
              <li>Click the <strong>Menu</strong> button in the top-right corner</li>
              <li>In the "Connected Services" section, find the Wahoo service</li>
              <li>
                Click the <strong>"Connect to Wahoo"</strong> button (if not already
                connected)
              </li>
              <li>You'll be redirected to Wahoo to authorize the connection</li>
              <li>
                After authorizing, you'll be redirected back to Gravly and your
                connection will be active
              </li>
            </ol>

            <!-- Video -->
            <div class="media-content">
              <video
                :src="connectWahooVideo"
                controls
                class="documentation-video"
                preload="metadata"
              >
                Your browser does not support the video tag.
              </video>
            </div>

            <h4>Using Wahoo Integration</h4>
            <p>
              Once connected to Wahoo, you can upload routes from the segment detail
              page:
            </p>
            <ul>
              <li>Navigate to any route or segment detail page</li>
              <li>In the "Actions" dropdown, select "Wahoo Cloud" section</li>
              <li>
                Click <strong>"Upload"</strong> to send the route to your Wahoo Cloud
                account
              </li>
              <li>
                The route will be automatically converted to FIT format and synced to
                your devices
              </li>
            </ul>

            <!-- Video -->
            <div class="media-content">
              <video
                :src="uploadRouteWahoo"
                controls
                class="documentation-video"
                preload="metadata"
              >
                Your browser does not support the video tag.
              </video>
            </div>

            <h4>Disconnecting Wahoo</h4>
            <p>
              To disconnect from Wahoo, click the disconnect button (<i
                class="fas fa-sign-out-alt"
              ></i
              >) next to the Wahoo service in the menu. This will prevent future uploads
              but won't delete routes already uploaded to Wahoo Cloud.
            </p>

            <h3>Tips</h3>
            <ul>
              <li>
                Strava connection is required for accessing the Editor, so connect it
                first if you plan to create segments
              </li>
              <li>
                Both services can be connected simultaneously - they work independently
                and complement each other
              </li>
              <li>
                Your connection status is always visible in the menu, so you can easily
                see which services are active
              </li>
              <li>
                Routes uploaded to Wahoo are tracked, so you can update or delete them
                later if needed
              </li>
              <li>
                Connections are secure and use OAuth 2.0 authentication - your
                credentials are never stored directly in Gravly
              </li>
            </ul>
          </div>
        </section>

        <!-- Explorer Section -->
        <section id="explorer" ref="explorerSection" class="documentation-section">
          <h2 class="section-title">{{ $t('documentation.explorer') }}</h2>
          <div class="section-content">
            <p>
              The Explorer allows you to browse and discover gravel segments and routes
              in your area. Use the interactive map to explore terrain and find the
              perfect segments for your next ride.
            </p>

            <h3>Getting Started</h3>
            <p>
              When you first open the Explorer, you'll see a map with a fixed center
              marker (📍). The map automatically loads segments within the visible area.
              You can pan and zoom the map to explore different regions.
            </p>

            <!-- Video -->
            <div class="media-content">
              <video
                :src="explorerOverviewVideo"
                controls
                class="documentation-video"
                preload="metadata"
              >
                Your browser does not support the video tag.
              </video>
            </div>

            <h3>Using Filters</h3>
            <p>
              Click the <strong>Filters</strong> button to open the filter sidebar. You
              can filter segments by:
            </p>
            <ul>
              <li>
                <strong>Track Type:</strong> Switch between "Segments" and "Routes"
              </li>
              <li><strong>Difficulty Level:</strong> Filter by difficulty (1-5)</li>
              <li>
                <strong>Surface Type:</strong> Select specific surface types (paved
                roads, stone roads, trails, etc.)
              </li>
              <li>
                <strong>Tire Recommendations:</strong> Filter by tire type needed
                (slick, semi-slick, knobs) for dry or wet conditions
              </li>
              <li>
                <strong>Search by Name:</strong> Type to search for segments by name
              </li>
            </ul>
            <p>
              Active filters are indicated by a badge on the filter button. Clear all
              filters by clicking the "Clear all filters" button.
            </p>

            <!-- Video -->
            <div class="media-content">
              <video
                :src="explorerFiltersVideo"
                controls
                class="documentation-video"
                preload="metadata"
              >
                Your browser does not support the video tag.
              </video>
            </div>

            <h3>Exploring Segments</h3>
            <p>
              The segment list below the map shows all segments sorted by distance from
              the map center. Each segment card displays:
            </p>
            <ul>
              <li>Segment name</li>
              <li>Distance and elevation gain</li>
              <li>Difficulty level</li>
              <li>Surface types</li>
              <li>Tire recommendations for dry and wet conditions</li>
              <li>Distance from map center</li>
            </ul>
            <p>
              <strong>Hovering</strong> over a segment card highlights it on the map
              with a colored rectangle. <strong>Clicking</strong> on a segment card
              selects it and shows it highlighted on the map. Click again to navigate to
              the segment detail page for more information.
            </p>

            <!-- Video -->
            <div class="media-content">
              <video
                :src="segmentDetailsVideo"
                controls
                class="documentation-video"
                preload="metadata"
              >
                Your browser does not support the video tag.
              </video>
            </div>

            <h3>Map Controls</h3>
            <ul>
              <li>
                <strong>Resize Handle:</strong> Drag the handle between the map and
                segment list to adjust the map height
              </li>
              <li>
                <strong>Max Results:</strong> Use the dropdown in the top-left corner of
                the map to limit results (25, 50, 75, or 100)
              </li>
              <li>
                <strong>Map Navigation:</strong> Pan by dragging, zoom with mouse wheel
                or pinch gestures on mobile
              </li>
            </ul>

            <h3>Tips</h3>
            <ul>
              <li>
                Move the map to different areas to discover segments in new locations
              </li>
              <li>
                Use filters to narrow down segments that match your riding preferences
                and conditions
              </li>
              <li>
                Check tire recommendations to ensure you're prepared for the terrain
              </li>
              <li>
                Login with Strava to view saved routes from other users in addition to
                segments
              </li>
            </ul>
          </div>
        </section>

        <!-- Planner Section -->
        <section id="planner" ref="plannerSection" class="documentation-section">
          <h2 class="section-title">{{ $t('documentation.planner') }}</h2>
          <div class="section-content">
            <p>
              The Route Planner helps you create custom gravel routes by combining
              waypoints and segments. Plan your perfect ride with detailed elevation
              profiles and route statistics.
            </p>

            <h3>Routing Modes</h3>
            <p>
              Click the <strong>Route</strong> button (🗺️) in the top-right corner to
              open the sidebar and choose between two routing modes:
            </p>

            <h4>Free Mode</h4>
            <p>
              Create routes by adding multiple waypoints freely. The system
              automatically generates routes between waypoints, allowing you to create
              complex routes with intermediate stops.
            </p>
            <ul>
              <li>Click anywhere on the map to add a waypoint</li>
              <li>Drag waypoints to reposition them</li>
              <li>Drag the route line to insert a new waypoint</li>
              <li>Right-click a waypoint to remove it</li>
            </ul>

            <!-- Video -->
            <div class="media-content">
              <video
                :src="plannerFreeModeVideo"
                controls
                class="documentation-video"
                preload="metadata"
              >
                Your browser does not support the video tag.
              </video>
            </div>

            <h4>Guided Mode</h4>
            <p>
              Create routes between two points (start and end) by selecting gravel
              segments to pass through. Perfect for planning point-to-point rides.
            </p>
            <ul>
              <li>Set your starting point by clicking on the map</li>
              <li>Set your ending point by clicking on the map</li>
              <li>Select segments from the explorer to include in your route</li>
              <li>Click "Generate Route" to create the complete route</li>
            </ul>

            <!-- Video -->
            <div class="media-content">
              <video
                :src="plannerGuidedModeVideo"
                controls
                class="documentation-video"
                preload="metadata"
              >
                Your browser does not support the video tag.
              </video>
            </div>

            <h3>Adding Segments to Your Route</h3>
            <p>In either mode, you can add segments from the explorer to your route:</p>
            <ul>
              <li>
                Segments are displayed on the map when you pan to areas where they exist
              </li>
              <li>Click on a segment on the map to view its popup</li>
              <li>Click "Add to Route" in the segment popup to include it</li>
              <li>
                Use filters in the sidebar to find segments matching your preferences
              </li>
              <li>
                Manage selected segments in the sidebar - remove them or reverse their
                direction
              </li>
            </ul>

            <!-- Video -->
            <div class="media-content">
              <video
                :src="plannerFiltersVideo"
                controls
                class="documentation-video"
                preload="metadata"
              >
                Your browser does not support the video tag.
              </video>
            </div>

            <h3>Elevation Profile</h3>
            <p>
              Below the map, you'll see a real-time elevation profile of your route
              showing:
            </p>
            <ul>
              <li>Elevation changes along the route</li>
              <li>Total distance</li>
              <li>Elevation gain and loss</li>
            </ul>
            <p>
              Drag the resize handle to adjust the height of the elevation profile
              section. The profile updates automatically as you modify your route.
            </p>

            <h3>Map Controls</h3>
            <p>The top-right corner provides several controls:</p>
            <ul>
              <li>
                <strong>Route (🗺️):</strong> Toggle the sidebar to switch routing modes
                and view route information
              </li>
              <li>
                <strong>Save (💾):</strong> Save your route (requires Strava
                authentication)
              </li>
              <li><strong>Clear (🗑️):</strong> Clear the entire map and start over</li>
              <li>
                <strong>Undo (↶):</strong> Undo the last action (waypoint added, moved,
                or removed)
              </li>
              <li><strong>Redo (↷):</strong> Redo an action that was undone</li>
            </ul>

            <!-- Screenshot -->
            <div class="media-content">
              <img
                :src="plannerControlsImage"
                alt="Route Planner map controls"
                class="documentation-image documentation-image-planner-controls"
              />
            </div>

            <h3>Saving Routes</h3>
            <p>
              To save your route, you need to be logged in with Strava. Click the
              <strong>Save</strong> button to open the save modal where you can:
            </p>
            <ul>
              <li>Enter a route name</li>
              <li>Add comments or notes about the route</li>
              <li>View route statistics before saving</li>
            </ul>
            <p>
              Saved routes are stored in your account and can be viewed in the Explorer
              when you're logged in.
            </p>

            <!-- Video -->
            <div class="media-content">
              <video
                :src="plannerSaveRouteVideo"
                controls
                class="documentation-video"
                preload="metadata"
              >
                Your browser does not support the video tag.
              </video>
            </div>

            <h3>Tips</h3>
            <ul>
              <li>
                Use Free Mode for exploring and creating routes with multiple stops
              </li>
              <li>
                Use Guided Mode when you have a specific start and end point in mind
              </li>
              <li>
                Filter segments by difficulty and surface type to match your skill level
                and bike setup
              </li>
              <li>
                Check the elevation profile to understand the route's difficulty before
                you ride
              </li>
              <li>Use undo/redo to experiment with different route configurations</li>
              <li>
                Save your favorite routes so you can access them later in the Explorer
              </li>
            </ul>
          </div>
        </section>

        <!-- Editor Section (only for authorized users) -->
        <section
          v-if="isEditorAuthorized"
          id="editor"
          ref="editorSection"
          class="documentation-section"
        >
          <h2 class="section-title">{{ $t('documentation.editor') }}</h2>
          <div class="section-content">
            <p>
              The Editor allows authorized users to create and edit gravel segments and
              routes. Import GPX files, define segment boundaries, add metadata, and
              contribute to the Gravly database.
            </p>

            <h3>Importing GPX Data</h3>
            <p>You can import GPX data from three sources:</p>

            <h4>1. GPX File Upload</h4>
            <p>Upload a GPX file directly from your computer:</p>
            <ul>
              <li>Click <strong>"GPX file"</strong> in the sidebar</li>
              <li>Select a .gpx file from your computer</li>
              <li>The file will be parsed and displayed on the map</li>
            </ul>

            <!-- Screenshot/GIF Placeholder -->
            <div class="media-placeholder">
              <div class="placeholder-content">
                <i class="fa-solid fa-video"></i>
                <p><strong>Video: Uploading GPX File</strong></p>
                <p>
                  Show the process of clicking "GPX file", selecting a file from the
                  file picker, and then showing the GPX data being loaded and displayed
                  on the map. Show the loading state and the final result.
                </p>
              </div>
            </div>

            <h4>2. Import from Strava</h4>
            <p>
              Import GPX data directly from your Strava activities (requires Strava
              authentication):
            </p>
            <ul>
              <li>Click <strong>"Strava"</strong> in the sidebar</li>
              <li>Browse your recent Strava activities</li>
              <li>Select an activity to import</li>
              <li>The activity's GPS data will be loaded into the editor</li>
            </ul>

            <!-- Screenshot Placeholder -->
            <div class="media-placeholder">
              <div class="placeholder-content">
                <i class="fa-solid fa-image"></i>
                <p><strong>Screenshot: Strava Import Modal</strong></p>
                <p>
                  Show the Strava activity list modal with activities displayed. Show an
                  activity being selected and the import process. Include the activity
                  details visible in the modal.
                </p>
              </div>
            </div>

            <h4>3. Import from Database</h4>
            <p>
              Load an existing segment from the Gravly database to edit or update it:
            </p>
            <ul>
              <li>Click <strong>"Database"</strong> in the sidebar</li>
              <li>Browse segments on the interactive map</li>
              <li>Click on a segment to import it</li>
              <li>The segment data will be loaded for editing</li>
            </ul>

            <!-- Screenshot Placeholder -->
            <div class="media-placeholder">
              <div class="placeholder-content">
                <i class="fa-solid fa-image"></i>
                <p><strong>Screenshot: Database Import</strong></p>
                <p>
                  Show the segment import modal with the map displaying segments. Show
                  clicking on a segment to select it, and then the segment being loaded
                  into the editor.
                </p>
              </div>
            </div>

            <h3>Selecting Segment Boundaries</h3>
            <p>
              After importing GPX data, use the elevation chart to define your segment's
              start and end points:
            </p>
            <ul>
              <li>The full route is displayed as a gray line on the elevation chart</li>
              <li>
                Drag the <strong>start marker</strong> (green) to set where your segment
                begins
              </li>
              <li>
                Drag the <strong>end marker</strong> (red) to set where your segment
                ends
              </li>
              <li>
                The selected segment is highlighted in color on both the chart and map
              </li>
              <li>
                Use the toggle to switch between <strong>Distance</strong> and
                <strong>Time</strong> on the X-axis
              </li>
            </ul>
            <p>
              You can also use the navigation buttons to move markers one point at a
              time for precise selection.
            </p>

            <!-- Screenshot/GIF Placeholder -->
            <div class="media-placeholder">
              <div class="placeholder-content">
                <i class="fa-solid fa-video"></i>
                <p><strong>Video: Selecting Segment Boundaries</strong></p>
                <p>
                  Show the elevation chart with the full route displayed. Demonstrate
                  dragging the start and end markers to select a segment. Show how the
                  selected portion is highlighted on both the chart and map. Show
                  switching between distance and time modes on the X-axis.
                </p>
              </div>
            </div>

            <h3>Adding Metadata</h3>
            <p>
              Fill in the metadata form below the elevation chart to provide information
              about your segment:
            </p>

            <h4>Basic Information</h4>
            <ul>
              <li>
                <strong>Segment Name:</strong> Give your segment a descriptive name
                (required)
              </li>
              <li><strong>Track Type:</strong> Choose "Segment" or "Route"</li>
            </ul>

            <h4>Trail Conditions</h4>
            <ul>
              <li>
                <strong>Difficulty Level:</strong> Rate the difficulty from 1 (very
                easy) to 5 (very hard)
              </li>
              <li>
                <strong>Surface Types:</strong> Select all surface types present (paved
                roads, stone roads, trails, etc.)
              </li>
              <li>
                <strong>Tire Recommendations:</strong>
                <ul>
                  <li>Select tire type for <strong>Dry</strong> conditions</li>
                  <li>Select tire type for <strong>Wet</strong> conditions</li>
                  <li>Options: Slick, Semi-Slick, or Knobs</li>
                </ul>
              </li>
            </ul>

            <!-- Screenshot Placeholder -->
            <div class="media-placeholder">
              <div class="placeholder-content">
                <i class="fa-solid fa-image"></i>
                <p><strong>Screenshot: Metadata Form</strong></p>
                <p>
                  Show the metadata form with all sections visible: segment name, track
                  type, difficulty level slider, surface type checkboxes, and tire
                  recommendations. Show an example with fields filled in.
                </p>
              </div>
            </div>

            <h4>Commentary and Media</h4>
            <p>Enhance your segment with additional information:</p>
            <ul>
              <li>
                <strong>Description:</strong> Add a detailed text description of the
                segment
              </li>
              <li>
                <strong>Video Links:</strong> Add YouTube or other video platform links
                (click "Add video link" to add multiple)
              </li>
              <li>
                <strong>Images:</strong> Upload images by dragging and dropping or
                clicking to select files
              </li>
            </ul>

            <!-- Screenshot/GIF Placeholder -->
            <div class="media-placeholder">
              <div class="placeholder-content">
                <i class="fa-solid fa-video"></i>
                <p><strong>Video: Adding Media</strong></p>
                <p>
                  Show adding a video link, then demonstrate dragging and dropping
                  images into the upload area. Show how images appear as thumbnails and
                  can be removed. Keep it concise.
                </p>
              </div>
            </div>

            <h3>Saving Your Work</h3>
            <p>Use the sidebar actions to save your segment:</p>
            <ul>
              <li>
                <strong>Save as New:</strong> Create a new segment in the database
              </li>
              <li>
                <strong>Update in DB:</strong> Update an existing segment (only
                available when editing a segment from the database)
              </li>
              <li>
                <strong>Delete from DB:</strong> Delete an existing segment (only
                available when editing a segment you own)
              </li>
            </ul>
            <p>
              All actions require a segment name to be entered. The buttons will be
              disabled until you provide a name.
            </p>

            <!-- Screenshot Placeholder -->
            <div class="media-placeholder">
              <div class="placeholder-content">
                <i class="fa-solid fa-image"></i>
                <p><strong>Screenshot: Save Actions</strong></p>
                <p>
                  Show the sidebar with the save actions visible. Show the buttons in
                  their enabled/disabled states. Show a successful save message or
                  notification.
                </p>
              </div>
            </div>

            <h3>Map Controls</h3>
            <ul>
              <li>
                <strong>Auto Zoom/Pan Toggle:</strong> Lock or unlock automatic map
                adjustment when moving segment markers (enabled by default)
              </li>
              <li>
                <strong>Map Navigation:</strong> Pan and zoom to inspect your route in
                detail
              </li>
            </ul>

            <!-- Screenshot Placeholder -->
            <div class="media-placeholder">
              <div class="placeholder-content">
                <i class="fa-solid fa-image"></i>
                <p><strong>Screenshot: Map with Auto Zoom Control</strong></p>
                <p>
                  Show the map with the lock/unlock button visible in the top-right
                  corner of the map. Indicate what this control does.
                </p>
              </div>
            </div>

            <h3>Tips</h3>
            <ul>
              <li>
                Select segment boundaries carefully to capture the most interesting or
                challenging parts of a route
              </li>
              <li>
                Provide accurate difficulty ratings and surface type information to help
                other riders
              </li>
              <li>
                Add detailed descriptions and media to make your segments more valuable
                to the community
              </li>
              <li>
                Use the time mode on the elevation chart if you want to select segments
                based on time intervals rather than distance
              </li>
              <li>
                Review your segment on the map before saving to ensure the boundaries
                are correct
              </li>
            </ul>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useStravaApi } from '../composables/useStravaApi'
import { useAuthorization } from '../composables/useAuthorization'
import connectedServicesImage from '../assets/doc/connected_services.png'
import connectStravaVideo from '../assets/doc/connect_strava.mp4'
import connectWahooVideo from '../assets/doc/connect_wahoo.mp4'
import uploadRouteWahoo from '../assets/doc/upload_route_wahoo.mp4'
import explorerOverviewVideo from '../assets/doc/explorer_overview.mp4'
import explorerFiltersVideo from '../assets/doc/explorer_filters.mp4'
import segmentDetailsVideo from '../assets/doc/segment_details.mp4'
import plannerFreeModeVideo from '../assets/doc/planner_free_mode.mp4'
import plannerGuidedModeVideo from '../assets/doc/planner_guided_mode.mp4'
import plannerFiltersVideo from '../assets/doc/planner_filters.mp4'
import plannerControlsImage from '../assets/doc/planner_controls.png'
import plannerSaveRouteVideo from '../assets/doc/planner_save_route.mp4'

const route = useRoute()

// Strava authentication (needed for editor authorization)
const { isAuthenticated: isAuthenticatedFn } = useStravaApi()

// User authorization
const { isAuthorized } = useAuthorization()

// Computed properties for authentication
const isAuthenticated = computed(() => isAuthenticatedFn())
const isEditorAuthorized = computed(() => isAuthenticated.value && isAuthorized.value)

// Section refs
const connectionsSection = ref<HTMLElement | null>(null)
const explorerSection = ref<HTMLElement | null>(null)
const plannerSection = ref<HTMLElement | null>(null)
const editorSection = ref<HTMLElement | null>(null)

// Active section tracking
const activeSection = ref<string>('connections')

// Scroll to section
function scrollToSection(sectionId: string) {
  activeSection.value = sectionId
  const section = getSectionRef(sectionId)
  if (section.value) {
    section.value.scrollIntoView({ behavior: 'smooth', block: 'start' })
    // Update URL hash without triggering scroll
    window.history.replaceState(null, '', `#${sectionId}`)
  }
}

// Get section ref by ID
function getSectionRef(sectionId: string) {
  switch (sectionId) {
    case 'connections':
      return connectionsSection
    case 'explorer':
      return explorerSection
    case 'planner':
      return plannerSection
    case 'editor':
      return editorSection
    default:
      return connectionsSection
  }
}

// Handle hash on mount and route changes
onMounted(async () => {
  // Wait for next tick to ensure DOM is rendered
  await nextTick()

  // Check if there's a hash in the URL
  const hash = route.hash.replace('#', '') || window.location.hash.replace('#', '')

  if (hash && ['explorer', 'planner', 'connections', 'editor'].includes(hash)) {
    // Only show editor section if user is authorized
    if (hash === 'editor' && !isEditorAuthorized.value) {
      activeSection.value = 'connections'
      await nextTick()
      scrollToSection('connections')
    } else {
      activeSection.value = hash
      await nextTick()
      scrollToSection(hash)
    }
  } else {
    activeSection.value = 'connections'
  }

  // Watch for scroll to update active section
  const handleScroll = () => {
    const sections = [
      { id: 'connections', ref: connectionsSection },
      { id: 'explorer', ref: explorerSection },
      { id: 'planner', ref: plannerSection },
      { id: 'editor', ref: editorSection }
    ].filter((s) => s.id !== 'editor' || isEditorAuthorized.value)

    const scrollPosition = window.scrollY + 100 // offset for navbar

    for (let i = sections.length - 1; i >= 0; i--) {
      const section = sections[i]
      if (section.ref.value) {
        const rect = section.ref.value.getBoundingClientRect()
        const sectionTop = rect.top + window.scrollY

        if (scrollPosition >= sectionTop) {
          activeSection.value = section.id
          break
        }
      }
    }
  }

  window.addEventListener('scroll', handleScroll)
})

// Watch for hash changes
watch(
  () => route.hash,
  (newHash) => {
    const hash = newHash.replace('#', '')
    if (hash && ['explorer', 'planner', 'connections', 'editor'].includes(hash)) {
      if (hash === 'editor' && !isEditorAuthorized.value) {
        return
      }
      scrollToSection(hash)
    }
  }
)
</script>

<style scoped>
.documentation-page {
  min-height: calc(100vh - var(--navbar-height));
  padding: 2rem 1.5rem;
  background: var(--bg-primary);
}

.documentation-container {
  max-width: 900px;
  margin: 0 auto;
}

.documentation-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid var(--border-primary);
}

.documentation-nav {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border-primary);
  flex-wrap: wrap;
}

.nav-link {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  text-decoration: none;
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 0.875rem;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.nav-link:hover {
  background: var(--bg-hover);
  color: var(--brand-primary);
}

.nav-link.active {
  background: var(--brand-50);
  color: var(--brand-primary);
  border-color: var(--brand-300);
}

.documentation-content {
  display: flex;
  flex-direction: column;
  gap: 3rem;
}

.documentation-section {
  scroll-margin-top: calc(var(--navbar-height) + 1rem);
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border-primary);
}

.section-content {
  color: var(--text-secondary);
  line-height: 1.6;
  min-height: 200px;
}

.section-content h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-top: 2rem;
  margin-bottom: 0.75rem;
}

.section-content h4 {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-top: 1.5rem;
  margin-bottom: 0.5rem;
}

.section-content ul,
.section-content ol {
  margin: 0.75rem 0;
  padding-left: 1.5rem;
}

.section-content li {
  margin: 0.5rem 0;
}

.section-content ul ul {
  margin: 0.5rem 0;
  padding-left: 1.25rem;
}

.media-placeholder {
  margin: 2rem 0;
  padding: 2rem;
  background: var(--bg-secondary);
  border: 2px dashed var(--border-primary);
  border-radius: 8px;
  text-align: center;
}

.placeholder-content {
  color: var(--text-tertiary);
}

.placeholder-content i {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: var(--text-muted);
  display: block;
}

.placeholder-content p {
  margin: 0.5rem 0;
}

.placeholder-content p strong {
  color: var(--text-secondary);
  display: block;
  margin-bottom: 0.5rem;
}

.media-content {
  margin: 2rem 0;
  text-align: center;
}

.documentation-image {
  max-width: 100%;
  width: auto;
  height: auto;
  border-radius: 8px;
  border: 1px solid var(--border-primary);
  box-shadow: var(--shadow-md);
  display: block;
  margin: 0 auto;
}

.documentation-image-connected-services {
  width: 250px;
  max-width: 250px;
}

.documentation-image-planner-controls {
  width: 50px;
  max-width: 50px;
}

.documentation-video {
  max-width: 100%;
  width: auto;
  height: auto;
  border-radius: 8px;
  border: 1px solid var(--border-primary);
  box-shadow: var(--shadow-md);
  display: block;
  margin: 0 auto;
}

/* Responsive Design */
@media (max-width: 768px) {
  .documentation-page {
    padding: 1.5rem 1rem;
  }

  .documentation-title {
    font-size: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .documentation-nav {
    gap: 0.5rem;
  }

  .nav-link {
    padding: 0.4rem 0.75rem;
    font-size: 0.8125rem;
  }

  .section-title {
    font-size: 1.25rem;
  }

  .documentation-content {
    gap: 2rem;
  }
}
</style>
