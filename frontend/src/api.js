import axios from 'axios';

// Vite env variable or default localhost
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add a request interceptor to include the JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Add a response interceptor to handle 401 Unauthorized
api.interceptors.response.use((response) => response, (error) => {
  if (error.response && error.response.status === 401) {
    // Optional: auto logout if token expired
    // localStorage.removeItem('token');
    // window.location.href = '/login';
  }
  return Promise.reject(error);
});

// Run automation immediately (multipart data)
export const triggerRun = async (formData) => {
  return api.post('/api/run', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
};

// Save config schedule (multipart data)
export const saveConfig = async (formData) => {
  return api.post('/api/config', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
};

// Get saved config (username, schedule etc)
export const getConfig = async () => {
  return api.get('/api/config');
};

// Get last status
export const getLastStatus = async () => {
  return api.get('/api/status/last');
};

// Get history
export const getRunHistory = async (limit = 20) => {
  return api.get(`/api/runs?limit=${limit}`);
};

// Schedule functions
export const getScheduleInfo = async () => {
  return api.get('/api/schedule');
};

export const enableSchedule = async (timeStr) => {
  return api.post('/api/schedule/enable', { time: timeStr });
};

export const disableSchedule = async () => {
  return api.post('/api/schedule/disable');
};

// Auth Functions
export const login = async (email, password) => {
  const formData = new URLSearchParams();
  formData.append('username', email); // OAuth2 expects 'username'
  formData.append('password', password);
  return api.post('/api/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  });
};

export const signup = async (email, password) => {
  return api.post('/api/auth/signup', { email, password });
};

export const getMe = async () => {
  return api.get('/api/auth/me');
};

export default api;
