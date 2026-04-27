<script setup>
import { ref, onMounted } from 'vue'

const gamesList = ref([])
const selectedGame = ref(null)

// GET All Games
const fetchAllGames = async () => {
  try {
    const response = await fetch('https://cloud-computing-faceezexhef2aaf3.italynorth-01.azurewebsites.net/api/games')
    gamesList.value = await response.json() // Prove we only extract JSON!
  } catch (error) {
    console.error("Error fetching games:", error)
  }
}

// GET One Game
const fetchOneGame = async (id) => {
  try {
    const response = await fetch(`https://cloud-computing-faceezexhef2aaf3.italynorth-01.azurewebsites.net/api/games/${id}`)
    selectedGame.value = await response.json()
  } catch (error) {
    console.error("Error fetching game details:", error)
  }
}

// GET ALL when the page first loads
onMounted(() => {
  fetchAllGames()
})

const newGameInput = ref({
  title: '',
  description: '',
  tags: ''
})

const showAddForm = ref(false)

// POST
const submitNewGame = async () => {
  const tagsArray = newGameInput.value.tags
    .split(',')
    .map(tag => tag.trim())
    .filter(tag => tag !== '')

  const payload = {
    title: newGameInput.value.title,
    description: newGameInput.value.description,
    tags: tagsArray
  }

  try {
    // sends the request to backend
    const response = await fetch('https://cloud-computing-faceezexhef2aaf3.italynorth-01.azurewebsites.net/api/games', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })

    if (response.ok) {
      newGameInput.value = { title: '', description: '', tags: '' }
      showAddForm.value = false
      fetchAllGames() 
    } else {
      console.error("Failed to add game. Check backend logs.")
    }
  } catch (error) {
    console.error("Error submitting new game:", error)
  }
}

// DELETE
const deleteGame = async (id) => {
  if (!confirm("Are you sure you want to delete this game?")) return;

  try {
    const response = await fetch(`https://cloud-computing-faceezexhef2aaf3.italynorth-01.azurewebsites.net/api/games/${id}`, {
      method: 'DELETE'
    });

    if (response.ok) {
      selectedGame.value = null;
      fetchAllGames();
    } else {
      console.error("Failed to delete the game. Check backend logs.");
    }
  } catch (error) {
    console.error("Error deleting game:", error);
  }
}
</script>

<template>
  <main class="app-container">
    <div v-if="!selectedGame" class="library-view">
      <h1 class="main-title">Game Library</h1>
      
      <div class="add-game-section">
        <button v-if="!showAddForm" @click="showAddForm = true" class="action-btn">
          + Add New Game
        </button>
        
        <div v-else class="form-card">
          <h3>Add a Game to Library</h3>
          
          <input v-model="newGameInput.title" type="text" placeholder="Game Title (needs to be the full title)" class="form-input" />
          
          <textarea v-model="newGameInput.description" placeholder="A short description..." class="form-input textarea"></textarea>
          
          <input v-model="newGameInput.tags" type="text" placeholder="Tags (comma separated, e.g. Action, Sci-Fi)" class="form-input" />
          
          <div class="form-actions">
            <button @click="submitNewGame" class="submit-btn">Save to Library</button>
            <button @click="showAddForm = false" class="cancel-btn">Cancel</button>
          </div>
        </div>
      </div>
      
      <div class="grid-container">
        <div 
          v-for="game in gamesList" 
          :key="game.id" 
          class="game-card"
          @click="fetchOneGame(game.id)"
        >
          <div class="card-content">
            <h2>{{ game.title }}</h2>
            <span class="click-hint">View Details &rarr;</span>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="detail-view">
      <button class="back-btn" @click="selectedGame = null">
        &#8592; Back to Library
      </button>
      
      <div class="detail-card">
        <h2 class="game-title">{{ selectedGame.local_data?.title || selectedGame.title }}</h2> 
        
        <div class="tags-container" v-if="selectedGame.local_data?.tags">
          <span v-for="tag in selectedGame.local_data.tags" :key="tag" class="tag local-tag">
            {{ tag }}
          </span>
        </div>

        <img 
          class="game-cover" 
          :src="selectedGame.media?.cover_url" 
          alt="Game Cover" 
        /> 

        <div class="platforms-container" v-if="selectedGame.platforms">
          <span v-for="platform in selectedGame.platforms" :key="platform" class="tag platform-tag">
            {{ platform }}
          </span>
        </div>

        <p class="description">{{ selectedGame.local_data?.description || selectedGame.description }}</p>

        <div class="stats-grid">
          <div class="metacritic-section" v-if="selectedGame.reviews?.metacritic">
            <h3>Metacritic</h3>
            <div class="score" :class="{'high-score': selectedGame.reviews.metacritic >= 80}">
              {{ selectedGame.reviews.metacritic }}
            </div>
          </div>

          <div class="pricing-section">
            <h3>Best Deal</h3>
            <p class="price"><strong>USD:</strong> ${{ selectedGame.pricing?.usd }}</p>
            <p class="price"><strong>EUR:</strong> €{{ selectedGame.pricing?.eur }} </p>
            <p class="price"><strong>RON:</strong> {{ selectedGame.pricing?.ron }} lei</p>
            
            <a v-if="selectedGame.pricing?.deal_id" 
               :href="`https://www.cheapshark.com/redirect?dealID=${selectedGame.pricing.deal_id}`" 
               target="_blank" 
               class="buy-btn">
               View Deal &rarr;
            </a>
          </div>
        </div>
        <button class="delete-btn" @click="deleteGame(selectedGame.local_data?.id || selectedGame.id)">
          Delete Game
        </button>
      </div>
    </div>
  </main>
</template>

<style scoped>
/* stilul ramane neschimbat fata de versiunea ta */
.app-container { font-family: 'Segoe UI', sans-serif; color: #fff; max-width: 1000px; margin: 0 auto; padding: 20px; }
.main-title { text-align: center; font-size: 2.5rem; margin-bottom: 30px; color: #7a7a7a; }
.grid-container { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }
.game-card { background-color: #383838; border: 1px solid #555; border-radius: 12px; padding: 20px; cursor: pointer; text-align: center; }
.game-card:hover { transform: translateY(-5px); background-color: #2a2a2a; }
.detail-card { background-color: #1e1e1e; border-radius: 12px; padding: 30px; text-align: center; }
.game-cover { width: 100%; border-radius: 8px; margin-bottom: 20px; }
.action-btn { background-color: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; }
.form-card { background-color: #2a2a2a; padding: 20px; border-radius: 10px; display: flex; flex-direction: column; gap: 15px; }
.form-input { background-color: #1e1e1e; border: 1px solid #555; color: white; padding: 10px; border-radius: 5px; }
.delete-btn { background-color: transparent; color: #ff4c4c; border: 1px solid #ff4c4c; padding: 10px; cursor: pointer; width: 100%; margin-top: 20px; }
</style>