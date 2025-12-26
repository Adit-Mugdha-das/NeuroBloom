# 🧠 NeuroBloom

A web-based cognitive training and monitoring system designed to help individuals track and improve their cognitive health through personalized exercises and progress tracking.

## 📋 Overview

NeuroBloom provides cognitive-training tasks and personalized progress tracking through an interactive digital platform. Especially beneficial for individuals dealing with cognitive challenges, including those affected by neurological conditions such as Multiple Sclerosis.

## ✨ Features

- **User Authentication**: Secure registration and login system
- **Cognitive Training Modules**:
  - 🧩 Memory Recall Test - Test working memory with word sequences
  - 🎯 Attention & Reaction Test - Measure focus and reaction time
  - ⚡ Processing Speed (Coming Soon)
  - 🧠 Executive Function (Coming Soon)
- **Progress Tracking**: Real-time performance visualization with charts
- **Session History**: Track all completed sessions with detailed statistics
- **Personalized Dashboard**: View your cognitive fitness journey
- **Multiple Difficulty Levels**: Adaptive challenges for all skill levels

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLModel** - SQL database interaction
- **PostgreSQL** - Database
- **Bcrypt** - Password hashing
- **Uvicorn** - ASGI server

### Frontend
- **React** - UI library
- **Vite** - Build tool
- **Recharts** - Data visualization
- **Axios** - HTTP client
- **React Router** - Navigation

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Mac/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure database in `app/core/config.py` (update with your PostgreSQL credentials)

5. Run the server:
```bash
uvicorn app.main:app --reload
```

Backend will run on `http://127.0.0.1:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run development server:
```bash
npm run dev
```

Frontend will run on `http://localhost:5173` or `http://localhost:5174`

## 📊 Database Schema

### User Table
- id (Primary Key)
- email
- password_hash

### Test Result Table
- id (Primary Key)
- user_id (Foreign Key)
- task_type (memory, attention, etc.)
- score
- details (JSON)
- created_at

## 🎮 How to Use

1. **Register** a new account
2. **Login** with your credentials
3. Access your **Dashboard**
4. Choose a **cognitive training module**
5. Complete the test
6. View your **results and progress**

## 📈 Roadmap

- [x] User authentication system
- [x] Memory recall test
- [x] Attention & reaction test
- [x] Progress tracking and visualization
- [ ] Processing speed test
- [ ] Executive function test
- [ ] Mobile app
- [ ] AI-based recommendations
- [ ] Clinical reports export
- [ ] Gamification features

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is open source and available under the MIT License.

## 👨‍💻 Author

Adit Mugdha Das

## 🙏 Acknowledgments

Built for individuals seeking to monitor and improve their cognitive health, especially those managing neurological conditions.

---

**NeuroBloom** - Track your cognitive fitness journey 🧠✨
