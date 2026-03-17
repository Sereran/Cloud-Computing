<script setup>
import { ref, onMounted } from 'vue'

const gamesList = ref([])
const selectedGame = ref(null)

// GET All Games
const fetchAllGames = async () => {
  try {
    const response = await fetch('http://127.0.0.1:8001/api/games')
    gamesList.value = await response.json() // Prove we only extract JSON!
  } catch (error) {
    console.error("Error fetching games:", error)
  }
}

// GET One Game
const fetchOneGame = async (id) => {
  try {
    const response = await fetch(`http://127.0.0.1:8001/api/games/${id}`)
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
    const response = await fetch('http://127.0.0.1:8001/api/games', {
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
    const response = await fetch(`http://127.0.0.1:8001/api/games/${id}`, {
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
        <h2 class="game-title">{{ selectedGame.local_data.title }}</h2> 
        
        <div class="tags-container" v-if="selectedGame.local_data.tags">
          <span v-for="tag in selectedGame.local_data.tags" :key="tag" class="tag local-tag">
            {{ tag }}
          </span>
        </div>

        <img 
          class="game-cover" 
          :src="selectedGame.media.cover_url" 
          alt="Game Cover" 
        /> 

        <div class="platforms-container" v-if="selectedGame.platforms">
          <span v-for="platform in selectedGame.platforms" :key="platform" class="tag platform-tag">
            {{ platform }}
          </span>
        </div>

        <p class="description">{{ selectedGame.local_data.description }}</p>

        <div class="stats-grid">
          <div class="metacritic-section" v-if="selectedGame.reviews.metacritic">
            <h3>Metacritic</h3>
            <div class="score" :class="{'high-score': selectedGame.reviews.metacritic >= 80}">
              {{ selectedGame.reviews.metacritic }}
            </div>
          </div>

          <div class="pricing-section">
            <h3>Best Deal</h3>
            <p class="price"><strong>USD:</strong> ${{ selectedGame.pricing.usd }}</p>
            <p class="price"><strong>EUR:</strong> €{{ selectedGame.pricing.eur }} </p>
            <p class="price"><strong>RON:</strong> {{ selectedGame.pricing.ron }} lei</p>
            
            <a v-if="selectedGame.pricing.deal_id" 
               :href="`https://www.cheapshark.com/redirect?dealID=${selectedGame.pricing.deal_id}`" 
               target="_blank" 
               class="buy-btn">
               View Deal &rarr;
            </a>
          </div>
        </div>
        <button class="delete-btn" @click="deleteGame(selectedGame.local_data.id)">
          Delete Game
        </button>
      </div>
    </div>
  </main>
</template>

<style scoped>
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
  transition: transform 0.2s ease, box-shadow 0.2s ease;
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
  box-shadow: 0 10px 20px rgba(0,0,0,0.4);
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
  box-shadow: 0 4px 8px rgba(0,0,0,0.3);
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

.tags-container, .platforms-container {
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
.metacritic-section, .pricing-section {
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
.action-btn:hover { background-color: #0056b3; }

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

.form-card h3 { margin-top: 0; color: #e0e0e0; text-align: center; }

.form-input {
  background-color: #1e1e1e;
  border: 1px solid #555;
  color: white;
  padding: 10px;
  border-radius: 5px;
  font-family: inherit;
  font-size: 1rem;
}
.form-input:focus { outline: 1px solid #4caf50; border-color: #4caf50; }

.textarea { resize: vertical; min-height: 80px; }

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
.submit-btn:hover { background-color: #45a049; }

.cancel-btn {
  flex: 1;
  background-color: transparent;
  color: #ccc;
  border: 1px solid #777;
  padding: 10px;
  border-radius: 5px;
  cursor: pointer;
}
.cancel-btn:hover { background-color: #444; }

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
</style>