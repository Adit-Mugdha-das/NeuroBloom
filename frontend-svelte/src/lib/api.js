import axios from 'axios';

export const API_BASE_URL = 'http://127.0.0.1:8000';

const api = axios.create({
	baseURL: API_BASE_URL,
	headers: {
		'Content-Type': 'application/json'
	}
});

export const auth = {
	register: async (email, password) => {
		const response = await api.post('/api/auth/register', { email, password });
		return response.data;
	},
	
	login: async (email, password) => {
		const response = await api.post('/api/auth/login', { email, password });
		return response.data;
	}
};

export const tasks = {
	startMemoryTest: async (difficulty = 'medium') => {
		const response = await api.post('/api/tasks/memory/start', { difficulty });
		return response.data;
	},
	
	submitResult: async (userId, taskType, score, details) => {
		const response = await api.post(`/api/tasks/results?user_id=${userId}`, {
			task_type: taskType,
			score,
			details
		});
		return response.data;
	},
	
	getUserStats: async (userId) => {
		const response = await api.get(`/api/tasks/results/${userId}/stats`);
		return response.data;
	},
	
	getUserResults: async (userId) => {
		const response = await api.get(`/api/tasks/results/${userId}`);
		return response.data;
	},
	
	getBaselineStatus: async (userId) => {
		const response = await api.get(`/api/tasks/results/${userId}/baseline-status`);
		return response.data;
	}
};

export const baseline = {
	calculate: async (userId) => {
		const response = await api.post(`/api/baseline/calculate?user_id=${userId}`);
		return response.data;
	},
	
	get: async (userId) => {
		const response = await api.get(`/api/baseline/${userId}`);
		return response.data;
	}
};

export const training = {
	// Generate personalized training plan from baseline
	generatePlan: async (userId) => {
		const response = await api.post(`/api/training/training-plan/generate/${userId}`);
		return response.data;
	},
	
	// Get active training plan
	getPlan: async (userId) => {
		const response = await api.get(`/api/training/training-plan/${userId}?_t=${Date.now()}`);
		return response.data;
	},
	
	// Get next recommended tasks for training session
	getNextTasks: async (userId) => {
		const response = await api.get(`/api/training/training-plan/${userId}/next-tasks?_t=${Date.now()}`);
		return response.data;
	},
	
	// Submit training session results
	submitSession: async (sessionData) => {
		const response = await api.post('/api/training/training-session/submit', null, {
			params: {
				user_id: sessionData.user_id,
				training_plan_id: sessionData.training_plan_id,
				domain: sessionData.domain,
				task_type: sessionData.task_type,
				task_code: sessionData.task_code || sessionData.task_type,  // NEW: Support task rotation
				task_id: sessionData.task_id,  // NEW: Track specific task instance in session
				score: sessionData.score,
				accuracy: sessionData.accuracy,
				average_reaction_time: sessionData.average_reaction_time,
				consistency: sessionData.consistency,
				errors: sessionData.errors,
				duration: sessionData.session_duration
			}
		});
		return response.data;
	},
	
	// Get training session history
	getHistory: async (userId, limit = 50) => {
		const response = await api.get(`/api/training/training-session/history/${userId}`, {
			params: { limit }
		});
		return response.data;
	},
	
	// Get performance metrics
	getMetrics: async (userId) => {
		const response = await api.get(`/api/training/training-session/metrics/${userId}?_t=${Date.now()}`);
		return response.data;
	},
	
	// Get performance comparison (baseline vs current)
	getPerformanceComparison: async (userId) => {
		const response = await api.get(`/api/training/training-session/performance-comparison/${userId}?_t=${Date.now()}`);
		return response.data;
	},
	
	// Get streak information
	getStreak: async (userId) => {
		const response = await api.get(`/api/training/training-plan/${userId}/streak`);
		return response.data;
	},
	
	// Get user badges
	getBadges: async (userId) => {
		const response = await api.get(`/api/training/badges/${userId}`);
		return response.data;
	},
	
	// Get all available badges (earned + locked)
	getAvailableBadges: async (userId) => {
		const response = await api.get(`/api/training/badges/available/${userId}`);
		return response.data;
	},
	
	// Get recent badges
	getRecentBadges: async (userId, limit = 5) => {
		const response = await api.get(`/api/training/badges/recent/${userId}`, {
			params: { limit }
		});
		return response.data;
	},
	
	// Get performance trends
	getTrends: async (userId, days = 30) => {
		const response = await api.get(`/api/training/trends/${userId}`, {
			params: { days }
		});
		return response.data;
	},
	
	// Get weekly summary
	getWeeklySummary: async (userId) => {
		const response = await api.get(`/api/training/weekly-summary/${userId}`);
		return response.data;
	},
	
	// DEV TOOLS - Quick testing endpoints
	dev: {
		completeSingleSession: async (userId) => {
			const response = await api.post(`/api/training/dev/complete-single-session/${userId}`);
			return response.data;
		},
		
		completeSession: async (userId) => {
			const response = await api.post(`/api/training/dev/complete-session/${userId}`);
			return response.data;
		},
		
		generateSessions: async (userId, numSessions = 2) => {
			const response = await api.post(`/api/training/dev/generate-sessions/${userId}?num_sessions=${numSessions}`);
			return response.data;
		},
		
		setStreak: async (userId, days) => {
			const response = await api.post(`/api/training/dev/set-streak/${userId}?days=${days}`);
			return response.data;
		},
		
		clearSessions: async (userId) => {
			const response = await api.delete(`/api/training/dev/clear-sessions/${userId}`);
			return response.data;
		},
		
		checkBadges: async (userId) => {
			const response = await api.post(`/api/training/dev/check-badges/${userId}`);
			return response.data;
		}
	}
};

// Visual Search Task API
export const generateVisualSearchTrial = async (userId) => {
	const response = await api.get(`/api/training/tasks/visual-search/generate/${userId}`);
	return response.data;
};

export const submitVisualSearchResponse = async (userId, data) => {
	const response = await api.post(`/api/training/tasks/visual-search/submit/${userId}`, data);
	return response.data;
};

// Multiple Object Tracking Task API
export const generateMOTTrial = async (userId) => {
	const response = await api.get(`/api/training/tasks/multiple-object-tracking/generate/${userId}`);
	return response.data;
};

export const submitMOTResponse = async (userId, data) => {
	const response = await api.post(`/api/training/tasks/multiple-object-tracking/submit/${userId}`, data);
	return response.data;
};

export const generateUFOVTrial = async (userId) => {
	const response = await api.get(`/api/training/tasks/useful-field-of-view/generate/${userId}`);
	return response.data;
};

export const submitUFOVResponse = async (userId, data) => {
	const response = await api.post(`/api/training/tasks/useful-field-of-view/submit/${userId}`, data);
	return response.data;
};

export default api;

