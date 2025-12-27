import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

const api = axios.create({
	baseURL: API_BASE_URL,
	headers: {
		'Content-Type': 'application/json'
	}
});

export const auth = {
	register: async (email, password) => {
		const response = await api.post('/auth/register', { email, password });
		return response.data;
	},
	
	login: async (email, password) => {
		const response = await api.post('/auth/login', { email, password });
		return response.data;
	}
};

export const tasks = {
	startMemoryTest: async (difficulty = 'medium') => {
		const response = await api.post('/tasks/memory/start', { difficulty });
		return response.data;
	},
	
	submitResult: async (userId, taskType, score, details) => {
		const response = await api.post(`/tasks/results?user_id=${userId}`, {
			task_type: taskType,
			score,
			details
		});
		return response.data;
	},
	
	getUserStats: async (userId) => {
		const response = await api.get(`/tasks/results/${userId}/stats`);
		return response.data;
	},
	
	getUserResults: async (userId) => {
		const response = await api.get(`/tasks/results/${userId}`);
		return response.data;
	},
	
	getBaselineStatus: async (userId) => {
		const response = await api.get(`/tasks/results/${userId}/baseline-status`);
		return response.data;
	}
};

export const baseline = {
	calculate: async (userId) => {
		const response = await api.post(`/baseline/calculate?user_id=${userId}`);
		return response.data;
	},
	
	get: async (userId) => {
		const response = await api.get(`/baseline/${userId}`);
		return response.data;
	}
};

export default api;
