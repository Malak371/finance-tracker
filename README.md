# 💰 Personal Finance Tracker

A full-stack web application to help users track and manage their expenses. The app allows adding, editing, and deleting expenses, categorizing them, and visualizing spending patterns.

Built with:

- **Frontend**: React
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL

---

## 🚀 Features

- Add, edit, and delete expenses
- Categorize expenses (e.g., food, transport, entertainment)
- View spending summaries and breakdowns by category
- Dashboard with total spent and category insights
- Persistent storage using PostgreSQL

---

## 🛠️ Tech Stack

- **React** (frontend UI)
- **FastAPI** (backend API)
- **PostgreSQL** (database)
- **Axios** (for API calls)
- **SQLAlchemy** (ORM for database interaction)

---

## 📂 Project Structure

finance-tracker/
│── backend/ # FastAPI backend
│ ├── auth.py # tokens
│ ├── config.py # Database connection
│ ├── main.py # Entry point
│ ├── database.py # Database connection
│ ├── models.py # Database models
│ ├── crud.py # Database operations
│ ├── routes/ # API routes
│ ├── requirements.txt # Backend dependencies
│ └── schemas.py #schemas
│
│── frontend/ # React frontend
│ ├── src/
│ │ ├── components/ # React components
│ │ ├── context/ # auth
│ │ ├── pages/ # App pages
│ │ ├── App.jsx # Main React component
│ │ └── ...
│
│── README.md

---

## ⚙️ Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/finance-tracker.git
cd finance-tracker
```

## Backend Setup (FastAPI + PostgreSQL)

### 1. Navigate to the backend folder:

```bash
cd backend
```

### 2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate   # On Mac/Linux
venv\Scripts\activate      # On Windows
```

### 3. Install dependencies:

```bash
pip install -r requirements.txt
```

### 4. Set up the database in PostgreSQL:

```bash
CREATE DATABASE finance_tracker;
```

### 5. (Optional) Run migrations or initialize tables if using Alembic/SQLAlchemy.

### 6. Start the backend:

```bash
uvicorn main:app --reload
```

### The backend will run at: http://localhost:8000

## Frontend Setup (React)

### 1. Open a new terminal and navigate to the frontend folder:

```bash
cd frontend
```

### 2. Install dependencies:

```bash
npm install
```

### 3. Start the frontend development server:

```bash
npm run dev
```

### The frontend will run at: http://localhost:5173

📊 Usage

Open the React app in your browser.

Add expenses and budgets for different categories via the UI.

View your dashboard for summaries and breakdowns.

🤝 Contributing

Fork the project

Create a feature branch (git checkout -b feature-name)

Commit changes (git commit -m "Add new feature")

Push to branch (git push origin feature-name)

Open a Pull Request
