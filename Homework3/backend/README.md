# Cloud-Computing Game Library Backend (HW3)

A robust FastAPI backend service that manages a local game library integrated with external game APIs (RAWG, CheapShark) and real-time currency exchange rates. The service utilizes a cloud-hosted MySQL instance for persistent storage and follows modern architectural patterns including connection pooling and modular routing.

## 🚀 Getting Started

### ☁️ GCP MySQL Setup

To ensure the application connects to our cloud environment:

1.  **GCP Console**: Log in to your Google Cloud Project.
2.  **SQL Instances**: Create a new MySQL user with restricted privileges.
3.  **Security**: Add your current IP address to the **Public IP Allowlist** within the SQL instance settings to permit external connections.
4.  **Credentials**: Securely store your database host, username, and password.

### 🛠️ Local Environment Configuration

1.  **Install Dependencies**:
    ```bash
    cd Homework3/backend
    python -m venv .venv
    source .venv/Scripts/activate
    pip install -r requirements.txt
    ```
2.  **Environment Variables**: Create a `.env` file in the `backend/` directory based on `.env.example`:
    ```env
    DB_HOST=your-gcp-mysql-ip
    DB_USER=your-user
    DB_PASSWORD=your-password
    DB_NAME=cloud_homework
    RAWG_KEY=your-api-key
    ```

## 🏃 Running the Application

Launch the server using Uvicorn:

```bash
fastapi dev src/main.py
```

The API will be available at `http://127.0.0.1:8000`. You can access the interactive Swagger documentation at `/docs`.

## 🧪 Testing the API

We have provided a comprehensive **Postman Collection** in the `backend/` directory.

- Import `game_api_collection.json` into Postman.
- Ensure the `base_url` variable is set correctly.
- Test the GET, POST, and DELETE endpoints to verify cloud database persistence.
