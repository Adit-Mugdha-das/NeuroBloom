# NeuroBloom - Svelte Frontend

Clinical-grade cognitive assessment platform built with SvelteKit.

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ 
- Backend server running on http://127.0.0.1:8000

### Installation

```bash
cd frontend-svelte
npm install
```

### Development

```bash
npm run dev
```

The app will be available at http://localhost:5174

### Build for Production

```bash
npm run build
npm run preview
```

## 📁 Project Structure

```
frontend-svelte/
├── src/
│   ├── lib/
│   │   ├── api.js           # API client for backend communication
│   │   ├── stores.js        # Svelte stores (user authentication)
│   │   └── components/      # Reusable Svelte components
│   │
│   ├── routes/
│   │   ├── +page.svelte              # Landing page
│   │   ├── +layout.svelte            # Root layout
│   │   ├── login/+page.svelte        # Login page
│   │   ├── register/+page.svelte     # Registration page
│   │   ├── dashboard/+page.svelte    # Main dashboard
│   │   │
│   │   └── baseline/tasks/           # Cognitive assessment tasks
│   │       ├── working-memory/+page.svelte    # N-Back test
│   │       ├── attention/+page.svelte         # CPT test
│   │       ├── flexibility/+page.svelte       # Task switching
│   │       ├── planning/                      # Coming soon
│   │       ├── processing-speed/              # Coming soon
│   │       └── visual-scanning/               # Coming soon
│   │
│   ├── app.html         # HTML template
│   └── app.css          # Global styles
│
├── static/              # Static assets
├── svelte.config.js     # SvelteKit configuration
├── vite.config.js       # Vite configuration
└── package.json
```

## 🧠 Implemented Features

### ✅ Completed
- **Authentication System**
  - User registration and login
  - Svelte stores for state management
  - Protected routes

- **Dashboard**
  - User statistics display
  - Module navigation
  - Session history

- **Baseline Assessment Tasks**
  - **Working Memory (N-Back)**: 1-back test with 20 trials
  - **Attention (CPT)**: Continuous performance test with AX paradigm
  - **Cognitive Flexibility**: Task switching with parity/magnitude rules

### 🚧 In Progress
- Planning (Tower of Hanoi)
- Processing Speed (Reaction time tests)
- Visual Scanning (Visual search)

### 📋 Upcoming Features
- Adaptive difficulty engine
- Fatigue detection
- Weekly progress snapshots
- Training plan generator
- MS-specific features (micro-breaks)
- Progress visualization charts

## 🔌 API Integration

The frontend communicates with the FastAPI backend through:

- `POST /auth/register` - User registration
- `POST /auth/login` - User authentication
- `POST /tasks/results` - Submit test results
- `GET /tasks/stats/:userId` - Get user statistics
- `GET /tasks/results/:userId` - Get test history

## 🎨 Styling

- Custom CSS with gradient backgrounds
- Responsive design
- Card-based UI components
- Color-coded cognitive domains

## 📊 Test Metrics

Each cognitive test collects detailed metrics:

### Working Memory (N-Back)
- Correct hits, misses, false alarms
- Reaction time mean & standard deviation
- Accuracy percentage

### Attention (CPT)
- Target detection rate
- False alarm rate
- Vigilance decrement over time
- Sustained attention metrics

### Cognitive Flexibility
- Switch cost (RT increase on rule changes)
- Perseveration errors
- Switch vs. no-switch accuracy

## 🔧 Configuration

### API Endpoint
Edit `src/lib/api.js` to change the backend URL:
```javascript
const API_BASE_URL = 'http://127.0.0.1:8000';
```

### Port
Edit `vite.config.js` to change the dev server port:
```javascript
server: {
  port: 5174
}
```

## 📝 Development Notes

- Uses Svelte 5 with Runes (new reactivity system)
- SvelteKit for routing and SSR capabilities
- Axios for HTTP requests
- LocalStorage for persistent authentication

## 🐛 Troubleshooting

### Backend Connection Issues
- Ensure backend server is running on port 8000
- Check CORS configuration in FastAPI main.py

### Build Errors
- Delete `node_modules` and `.svelte-kit` folders
- Run `npm install` again
- Clear browser cache

## 📖 Next Steps

1. Complete remaining baseline tasks
2. Implement adaptive difficulty algorithm
3. Add progress tracking charts (Chart.js)
4. Build training plan generator
5. Add MS-specific features
6. Implement weekly re-assessment logic
