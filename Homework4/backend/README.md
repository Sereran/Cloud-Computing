## 🚀 Getting Started

### 🛠️ Local Environment Configuration

1.  **Install Dependencies**:
    _Ensure you have the ODBC Driver for SQL Server installed on your machine._
    ```bash
    cd Homework4/backend
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Linux/macOS
    source .venv/bin/activate
    pip install -r requirements.txt
    ```
2.  **Environment Variables**: Create a `.env` file in the `backend/` directory based on `.env.example`:
    ```env
    # Microsoft SQL Server Configuration
    # Connection String Format: DRIVER={SQL_DRIVER};SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};UID={SQL_USER};PWD={SQL_PASSWORD}
    SQL_SERVER=your_server.database.windows.net
    SQL_DATABASE=cloud_homework
    SQL_USER=your_username
    SQL_PASSWORD=your_password
    SQL_DRIVER={ODBC Driver 18 for SQL Server}
    RAWG_KEY=your-api-key
    ```

    *Note: These variables are used to construct the `pyodbc` connection string: `DRIVER={SQL_DRIVER};SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};UID={SQL_USER};PWD={SQL_PASSWORD}`*

## 🏃 Running the Application

### Local Development

Launch the server using Uvicorn:

```bash
fastapi dev src/main.py
```

The API will be available at `http://127.0.0.1:8000`. Access the interactive Swagger documentation at `/docs`.

### Docker

Build and run the container:

```bash
docker build -t game-library-backend .
docker run -p 8080:8080 --env-file .env game-library-backend
```

## 🧪 Testing the API

A comprehensive **Postman Collection** is provided in `postman_collection.json`.

- Import the file into Postman.
- Ensure the `base_url` variable is set correctly (e.g., `http://localhost:8000`).
- Test the GET, POST, and DELETE endpoints to verify Azure SQL persistence.
