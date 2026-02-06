

# RAAMP - AI-Powered Marketing Platform

## Prerequisites

- Python 3.11 or higher
- Node.js 18+ or Bun
- MongoDB (for database)
- Firebase account (for authentication)

## Installation & Setup

### Backend Setup

1. Navigate to the backend directory:
```bash
cd raamp-backend
```

2. Install dependencies (this will take several minutes):
```bash
pip install -r requirements.txt
```

**Note:** The project already has a `venv` folder. If you want to use it, you may need to allow script execution on Windows:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

3. Configure environment variables:
   - Create a `.env` file in the `raamp-backend` directory
   - Add the following required environment variables:

   **For local development:**
   ```env
   MONGODB_URL=mongodb://localhost:27017
   ```

   **For MongoDB Atlas (cloud):**
   ```env
   MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/dbname?retryWrites=true&w=majority
   ```

   - Also add other required variables: Firebase credentials, API keys, etc.

4. Set up MongoDB:
   
   **Option A - Local MongoDB:**
   - Install MongoDB from https://www.mongodb.com/try/download/community
   - Start MongoDB service:
     ```bash
     # Windows (as Administrator)
     net start MongoDB
     
     # macOS
     brew services start mongodb-community
     
     # Linux
     sudo systemctl start mongod
     ```

   **Option B - MongoDB Atlas (Cloud):**
   - Create a free cluster at https://www.mongodb.com/cloud/atlas
   - Whitelist your IP address in Network Access
   - Get your connection string and add it to `.env`

5. Run the backend server:
```bash
python main.py
```

The backend API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd raamp-frontend
```

2. Install dependencies:
```bash
# Using npm
npm install

# Or using bun
bun install
```

3. Configure environment variables:
   - Create a `.env` file in the `raamp-frontend` directory
   - Add necessary environment variables (API URL, Firebase config, etc.)

4. Run the development server:
```bash
# Using npm
npm run dev

# Or using bun
bun run dev
```

The frontend application will be available at `http://localhost:5173`

## Running the Full Project

1. Open two terminal windows
2. In the first terminal, start the backend:
   ```bash
   cd raamp-backend
   python main.py
   ```

3. In the second terminal, start the frontend:
   ```bash
   cd raamp-frontend
   npm run dev
   ```

4. Open your browser and navigate to `http://localhost:5173`

## Project Structure

```
raamp-fyp-final/
├── raamp-backend/          # Python FastAPI backend
│   ├── main.py            # Backend entry point
│   ├── requirements.txt   # Python dependencies
│   └── ...
└── raamp-frontend/        # React TypeScript frontend
    ├── src/              # Source code
    ├── package.json      # Node dependencies
    └── ...
```
