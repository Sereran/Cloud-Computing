<script setup>
import { ref, onMounted } from 'vue'
import { initializeApp } from 'firebase/app'
import { getStorage, getDownloadURL, ref as storageRef, uploadBytes } from 'firebase/storage'

const GAME_API_URL = process.env.GAME_API_HOST + process.env.GAME_API_BASE_URI

// ----------------------------------------
// ! Authentication logic and dependencies.
// ----------------------------------------
const isAuthenticated = ref(false)
const isCaptchaValid = ref(false)
const authMode = ref('login')

const authInput = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
})

const handleAuth = () => {
  // TODO: Implement actual authentication logic
  if (isCaptchaValid.value) {
    isAuthenticated.value = true
  }
}

const toggleAuthMode = (mode) => {
  authMode.value = mode
  authInput.value = { username: '', email: '', password: '', confirmPassword: '' }
}

// ----------------------------------------
// ! Firebase logic and dependencies.
// ----------------------------------------
const firebaseConfig = {
  apiKey: process.env.FIREBASE_KEY,
  authDomain: process.env.FIREBASE_AUTH_DOMAIN,
  projectId: process.env.FIREBASE_PROJECT_ID,
  storageBucket: process.env.FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.FIREBASE_APP_ID,
  measurementId: process.env.FIREBASE_MEASUREMENT_ID,
}

const app = initializeApp(firebaseConfig)
const storage = getStorage(app)

const isUploading = ref(false)
const selectedFiles = ref([])

const handleFileChange = (event) => {
  const files = Array.from(event.target.files)
  if (files.length > 3) {
    alert('You can only upload up to 3 files.')
    event.target.value = ''
    selectedFiles.value = []
    return
  }
  selectedFiles.value = files
}

const uploadFiles = async () => {
  const urls = []
  for (const file of selectedFiles.value) {
    const filePath = `games/${new Date().getTime()}_${file.name}`
    const fileRef = storageRef(storage, filePath)
    await uploadBytes(fileRef, file)
    const url = await getDownloadURL(fileRef)
    urls.push(url)
  }
  return urls
}

/**
 * Utility function.
 *
 * Extracts the file extension from a URL, ignoring query parameters.
 * @param {string} urlString - The full URL (e.g., 'https://example.com/video.mp4?user=123')
 * @returns {string} The file extension (e.g., 'mp4' or 'png')
 */
function getFileExtension(urlString) {
  try {
    const url = new URL(urlString)
    const pathname = url.pathname
    return pathname.split('.').pop()
  } catch (error) {
    console.error('Invalid URL provided:', error)
    return ''
  }
}

// ----------------------------------------
// ! Backend request making logic and dependencies.
// ----------------------------------------
const gamesList = ref([])
const selectedGame = ref(null)

// GET All Games
const fetchAllGames = async () => {
  try {
    const response = await fetch(GAME_API_URL)
    gamesList.value = await response.json()
  } catch (error) {
    console.error('Error fetching games:', error)
  }
}

// GET One Game
const fetchOneGame = async (id) => {
  try {
    const response = await fetch(`${GAME_API_URL}/${id}`)
    selectedGame.value = await response.json()
  } catch (error) {
    console.error('Error fetching game details:', error)
  }
}

const newGameInput = ref({
  title: '',
  description: '',
  tags: '',
  media_urls: [],
})

const showAddForm = ref(false)

// POST
const submitNewGame = async () => {
  if (selectedFiles.value.length > 3) {
    alert('Maximum 3 files allowed.')
    return
  }

  isUploading.value = true
  try {
    // 1. Upload files to Firebase Storage
    const mediaUrls = await uploadFiles()

    const tagsArray = newGameInput.value.tags
      .split(',')
      .map((tag) => tag.trim())
      .filter((tag) => tag !== '')

    const payload = {
      title: newGameInput.value.title,
      description: newGameInput.value.description,
      tags: tagsArray,
      media_urls: mediaUrls,
    }

    // 2. Send payload to backend
    const response = await fetch(GAME_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })

    if (response.ok) {
      newGameInput.value = { title: '', description: '', tags: '', media_urls: [] }
      selectedFiles.value = []
      showAddForm.value = false
      fetchAllGames()
    } else {
      const errorData = await response.json()
      console.error('Failed to add game:', errorData)
      alert('Failed to add game. Check console for details.')
    }
  } catch (error) {
    console.error('Error submitting new game:', error)
    alert('An error occurred while saving the game.')
  } finally {
    isUploading.value = false
  }
}

// DELETE
const deleteGame = async (id) => {
  if (!confirm('Are you sure you want to delete this game?')) return

  try {
    const response = await fetch(`${GAME_API_URL}/${id}`, {
      method: 'DELETE',
    })

    if (response.ok) {
      selectedGame.value = null
      fetchAllGames()
    } else {
      console.error('Failed to delete the game. Check backend logs.')
    }
  } catch (error) {
    console.error('Error deleting game:', error)
  }
}

// Initialization
onMounted(() => {
  fetchAllGames()
  window.onCaptchaVerified = (token) => {
    isCaptchaValid.value = true
    // TODO: token needs to get sent to the backend
  }

  window.onCaptchaExpired = () => {
    isCaptchaValid.value = false
  }

  // loads reCAPTCHA
  const script = document.createElement('script')
  script.src = 'https://www.google.com/recaptcha/enterprise.js'
  script.async = true
  script.defer = true
  document.head.appendChild(script)
})
</script>

<template>
  <div v-if="!isAuthenticated" class="auth-container">
    <div class="form-card auth-card">
      <h1 class="main-title">{{ authMode === 'login' ? 'Welcome Back' : 'Create Account' }}</h1>
      <p class="subtitle">
        {{
          authMode === 'login'
            ? 'Log in to access your library.'
            : 'Register to start creating your own game library.'
        }}
      </p>

      <div class="auth-tabs">
        <button class="auth-tab-btn" :class="{ active: authMode === 'login' }" @click="toggleAuthMode('login')">
          Log In
        </button>
        <button class="auth-tab-btn" :class="{ active: authMode === 'register' }" @click="toggleAuthMode('register')">
          Register
        </button>
      </div>

      <input v-model="authInput.username" type="text" placeholder="Username" class="form-input" />

      <input v-if="authMode === 'register'" v-model="authInput.email" type="email" placeholder="Email Address"
        class="form-input" />

      <input v-model="authInput.password" type="password" placeholder="Password" class="form-input" />

      <input v-if="authMode === 'register'" v-model="authInput.confirmPassword" type="password"
        placeholder="Confirm Password" class="form-input" />

      <div class="g-recaptcha" data-sitekey="6LfnSJ4sAAAAAJyxODutrsf1Y7g7kNRcrnBDMJoe" data-callback="onCaptchaVerified"
        data-expired-callback="onCaptchaExpired" data-theme="dark"></div>

      <button @click="handleAuth" class="submit-btn auth-btn" :disabled="!isCaptchaValid">
        <span v-if="!isCaptchaValid">Please complete reCAPTCHA</span>
        <span v-else>{{ authMode === 'login' ? 'Access Library' : 'Create Account & Enter' }}</span>
      </button>
    </div>
  </div>

  <main v-else class="app-container">
    <div v-if="!selectedGame" class="library-view">
      <h1 class="main-title">Game Library</h1>

      <div class="add-game-section">
        <button v-if="!showAddForm" @click="showAddForm = true" class="action-btn">
          + Add New Game
        </button>

        <div v-else class="form-card">
          <h3>Add a Game to Library</h3>

          <input v-model="newGameInput.title" type="text" placeholder="Game Title (needs to be the full title)"
            class="form-input" />

          <textarea v-model="newGameInput.description" placeholder="A short description..."
            class="form-input textarea"></textarea>

          <input v-model="newGameInput.tags" type="text" placeholder="Tags (comma separated, e.g. Action, Sci-Fi)"
            class="form-input" />

          <div class="file-upload-section">
            <label class="form-label">Media Upload (Max 3 files, .mp4 or .png)</label>
            <input type="file" multiple accept=".mp4,.png" @change="handleFileChange" class="form-input file-input"
              :disabled="isUploading" />
            <small v-if="selectedFiles.length > 0">{{ selectedFiles.length }} files selected</small>
          </div>

          <div class="form-actions">
            <button @click="submitNewGame" class="submit-btn" :disabled="isUploading || !newGameInput.title">
              {{ isUploading ? 'Uploading...' : 'Save to Library' }}
            </button>
            <button @click="showAddForm = false" class="cancel-btn" :disabled="isUploading">
              Cancel
            </button>
          </div>
        </div>
      </div>

      <div class="grid-container">
        <div v-for="game in gamesList" :key="game.id" class="game-card" @click="fetchOneGame(game.id)">
          <div class="card-content">
            <h2>{{ game.title }}</h2>
            <span class="click-hint">View Details &rarr;</span>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="detail-view">
      <button class="back-btn" @click="selectedGame = null">&#8592; Back to Library</button>

      <div class="detail-card">
        <h2 class="game-title">{{ selectedGame.game_data.title }}</h2>

        <div class="tags-container" v-if="selectedGame.game_data.tags">
          <span v-for="tag in selectedGame.game_data.tags" :key="tag" class="tag local-tag">
            {{ tag }}
          </span>
        </div>

        <div class="media-gameplay-section" v-if="selectedGame.media.urls && selectedGame.media.urls.length > 0">
          <h3 class="section-subtitle">Media Gameplay</h3>
          <div class="media-grid">
            <div v-for="(url, index) in selectedGame.media.urls" :key="index" class="media-item-box">
              <!-- Small span. -->
              <div class="media-info-header">
                <span v-if="getFileExtension(url) == 'mp4'" class="media-type-tag video-tag">Video Gameplay</span>
                <span v-else class="media-type-tag image-tag">Gameplay Capture</span>
              </div>

              <!-- Render custom media provided by the user. -->
              <div class="media-container">
                <img v-if="
                  getFileExtension(url) == 'png' ||
                  getFileExtension(url) == 'jpg' ||
                  getFileExtension(url) == 'jpeg'
                " :src="url" class="media-element" alt="Gameplay image" />

                <video v-else-if="getFileExtension(url) == 'mp4'" controls class="media-element">
                  <source :src="url" type="video/mp4" />
                  Your browser does not support the video tag.
                </video>

                <div v-else class="unsupported-media">
                  <a :href="url" target="_blank" class="download-link">Download Unknown File</a>
                </div>
              </div>
            </div>
          </div>
        </div>

        <img class="game-cover" :src="selectedGame.media.cover_url" v-if="selectedGame.media.cover_url"
          alt="Game Cover" />

        <div class="platforms-container" v-if="selectedGame.platforms">
          <span v-for="platform in selectedGame.platforms" :key="platform" class="tag platform-tag">
            {{ platform }}
          </span>
        </div>

        <p class="description">{{ selectedGame.game_data.description }}</p>

        <div class="stats-grid">
          <div class="metacritic-section" v-if="selectedGame.reviews.metacritic">
            <h3>Metacritic</h3>
            <div class="score" :class="{ 'high-score': selectedGame.reviews.metacritic >= 80 }">
              {{ selectedGame.reviews.metacritic }}
            </div>
          </div>

          <div class="pricing-section">
            <h3>Best Deal</h3>
            <p class="price" v-if="selectedGame.pricing.usd">
              <strong>USD:</strong> ${{ selectedGame.pricing.usd }}
            </p>
            <p class="price" v-if="selectedGame.pricing.eur">
              <strong>EUR:</strong> €{{ selectedGame.pricing.eur }}
            </p>
            <p class="price" v-if="selectedGame.pricing.ron">
              <strong>RON:</strong> {{ selectedGame.pricing.ron }} lei
            </p>

            <a v-if="selectedGame.pricing.deal_id"
              :href="`https://www.cheapshark.com/redirect?dealID=${selectedGame.pricing.deal_id}`" target="_blank"
              class="buy-btn">
              View Deal &rarr;
            </a>
          </div>
        </div>
        <button class="delete-btn" @click="deleteGame(selectedGame.game_data.id)">
          Delete Game
        </button>
      </div>
    </div>
  </main>
</template>

<style scoped>
/*authentication styling*/
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  color: #ffffff;
}

.auth-card {
  align-items: center;
  padding: 40px;
  width: 100%;
  max-width: 400px;
}

.subtitle {
  color: #aaaaaa;
  margin-bottom: 25px;
  text-align: center;
}

.auth-tabs {
  display: flex;
  width: 70%;
  background-color: #1e1e1e;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #444;
  margin-bottom: 20px;
}

.auth-tab-btn {
  flex: 1;
  padding: 12px;
  background: transparent;
  border: none;
  color: #888;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.2s ease;
  font-size: 1rem;
}

.auth-tab-btn:hover {
  background-color: #2a2a2a;
}

.auth-tab-btn.active {
  background-color: #4caf50;
  color: #121212;
}

.auth-btn {
  width: 100%;
  margin-top: 10px;
  padding: 15px;
  font-size: 1.1rem;
}

.auth-btn:disabled {
  background-color: #555;
  color: #888;
  cursor: not-allowed;
}

.g-recaptcha {
  margin: 15px 0;
  display: flex;
  justify-content: center;
}

/*global styling*/
.app-container {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  color: #ffffff;
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.main-title {
  text-align: center;
  font-size: 2.5rem;
  margin-bottom: 30px;
  color: #7a7a7a;
}

/*list of games*/
.grid-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}

.game-card {
  background-color: #383838;
  border: 1px solid #555;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  min-height: 120px;
}

.game-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.5);
  background-color: #2a2a2a;
}

.card-content h2 {
  margin: 0 0 10px 0;
  font-size: 1.3rem;
}

.click-hint {
  font-size: 0.9rem;
  color: #4caf50;
  font-weight: bold;
}

/*detailed view*/
.detail-view {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.back-btn {
  align-self: flex-start;
  background-color: transparent;
  color: #4caf50;
  border: 1px solid #4caf50;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
  margin-bottom: 20px;
  transition: background-color 0.2s;
}

.back-btn:hover {
  background-color: #4caf50;
  color: #121212;
}

.detail-card {
  background-color: #1e1e1e;
  border-radius: 12px;
  padding: 30px;
  max-width: 600px;
  width: 100%;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.4);
  text-align: center;
}

.game-title {
  margin-top: 0;
  font-size: 2rem;
  margin-bottom: 20px;
}

.game-cover {
  width: 100%;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
  margin-bottom: 20px;
}

.pricing-section {
  background-color: #121212;
  padding: 15px;
  border-radius: 8px;
  display: inline-block;
  min-width: 250px;
}

.pricing-section h3 {
  margin-top: 0;
  font-size: 1.1rem;
  color: #aaaaaa;
  margin-bottom: 10px;
}

.price {
  font-size: 1.2rem;
  margin: 5px 0;
}

.tags-container,
.platforms-container {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  margin-bottom: 15px;
}

.tag {
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: bold;
}

.local-tag {
  background-color: #4caf50;
  color: #121212;
}

.platform-tag {
  background-color: #555;
  color: #fff;
  border: 1px solid #777;
}

/*description*/
.description {
  text-align: left;
  line-height: 1.6;
  color: #cccccc;
  margin: 20px 0;
  padding: 15px;
  background-color: #2a2a2a;
  border-radius: 8px;
}

/*stats and pricing*/
.stats-grid {
  display: flex;
  justify-content: space-around;
  gap: 20px;
  margin-top: 20px;
}

.metacritic-section,
.pricing-section {
  background-color: #121212;
  padding: 15px;
  border-radius: 8px;
  flex: 1;
}

.score {
  font-size: 2.5rem;
  font-weight: bold;
  color: #ff9800;
}

.high-score {
  color: #4caf50;
}

.buy-btn {
  display: inline-block;
  margin-top: 10px;
  padding: 8px 15px;
  background-color: #007bff;
  color: white;
  text-decoration: none;
  border-radius: 5px;
  font-weight: bold;
  transition: background-color 0.2s;
}

.buy-btn:hover {
  background-color: #0056b3;
}

.add-game-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 30px;
}

.action-btn {
  background-color: #007bff;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 1.1rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.action-btn:hover {
  background-color: #0056b3;
}

.form-card {
  background-color: #2a2a2a;
  padding: 20px;
  border-radius: 10px;
  border: 1px solid #444;
  width: 100%;
  max-width: 500px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-card h3 {
  margin-top: 0;
  color: #e0e0e0;
  text-align: center;
}

.form-input {
  background-color: #1e1e1e;
  border: 1px solid #555;
  color: white;
  padding: 10px;
  border-radius: 5px;
  font-family: inherit;
  font-size: 1rem;
}

.form-input:focus {
  outline: 1px solid #4caf50;
  border-color: #4caf50;
}

.textarea {
  resize: vertical;
  min-height: 80px;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.submit-btn {
  flex: 1;
  background-color: #4caf50;
  color: #121212;
  border: none;
  padding: 10px;
  border-radius: 5px;
  font-weight: bold;
  cursor: pointer;
}

.submit-btn:hover {
  background-color: #45a049;
}

.cancel-btn {
  flex: 1;
  background-color: transparent;
  color: #ccc;
  border: 1px solid #777;
  padding: 10px;
  border-radius: 5px;
  cursor: pointer;
}

.cancel-btn:hover {
  background-color: #444;
}

.file-upload-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 10px;
}

.form-label {
  font-size: 0.9rem;
  color: #aaa;
  font-weight: bold;
}

.file-input {
  padding: 8px;
  font-size: 0.9rem;
}

.media-gameplay-section {
  margin: 35px 0;
  padding: 25px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  text-align: left;
  box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.1);
}

.section-subtitle {
  font-size: 1.2rem;
  color: #4caf50;
  margin-top: 0;
  margin-bottom: 25px;
  text-transform: uppercase;
  letter-spacing: 2px;
  font-weight: 900;
  text-align: center;
  text-shadow: 0 0 10px rgba(76, 175, 80, 0.3);
}

.media-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 25px;
}

.media-item-box {
  background: #0a0a0a;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
  transition:
    transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275),
    border-color 0.3s ease;
  border: 1px solid #222;
}

.media-item-box:hover {
  transform: translateY(-5px);
  border-color: #4caf50;
}

.media-info-header {
  padding: 10px 15px;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid #222;
  display: flex;
  align-items: center;
}

.media-type-tag {
  font-size: 0.7rem;
  font-weight: 800;
  text-transform: uppercase;
  padding: 4px 10px;
  border-radius: 6px;
  letter-spacing: 0.5px;
}

.video-tag {
  background: rgba(233, 30, 99, 0.2);
  color: #ff4081;
  border: 1px solid rgba(233, 30, 99, 0.3);
}

.audio-tag {
  background: rgba(156, 39, 176, 0.2);
  color: #e040fb;
  border: 1px solid rgba(156, 39, 176, 0.3);
}

.image-tag {
  background: rgba(33, 150, 243, 0.2);
  color: #448aff;
  border: 1px solid rgba(33, 150, 243, 0.3);
}

.media-container {
  width: 100%;
}

.media-element {
  width: 100%;
  display: block;
  border: none;
}

.audio-element {
  padding: 15px;
  height: 64px;
}

.unsupported-media {
  padding: 30px;
  text-align: center;
}

.download-link {
  color: #4caf50;
  text-decoration: none;
  font-weight: bold;
  font-size: 0.9rem;
  transition: color 0.2s;
}

.download-link:hover {
  color: #66bb6a;
  text-decoration: underline;
}

.delete-btn {
  background-color: transparent;
  color: #ff4c4c;
  border: 1px solid #ff4c4c;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
  margin-top: 30px;
  width: 100%;
  transition: all 0.2s;
}

.delete-btn:hover {
  background-color: #ff4c4c;
  color: #121212;
}

.delete-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
