## 🚀 Getting Started

### 🛠️ Prerequisites
- Node.js (v20 or higher)
- npm or yarn

### 📦 Installation
1.  **Clone the repository and navigate to the frontend directory**:
    ```bash
    cd Homework4/frontend
    ```
2.  **Install dependencies**:
    ```bash
    npm install
    ```

### ⚙️ Configuration
Create a `.env` file in the `frontend/` directory based on `.env.example`:
```env
VITE_GAME_API_HOST="http://127.0.0.1:8000"
VITE_GAME_API_BASE_URI="/api/games"

# Azure Blob Storage Configuration
VITE_AZURE_STORAGE_CONNECTION_STRING="your_connection_string"
VITE_AZURE_STORAGE_CONTAINER_NAME="games"
```

### 🏃 Running the Application
Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`.
