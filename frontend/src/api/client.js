// api/client.js — Axios instance with JWT interceptors
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 
  (window.location.hostname.includes('vercel.app') ? 'https://biochain-opt-backend.loca.lt' : '')

const client = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 
    'Content-Type': 'application/json',
    'Bypass-Tunnel-Reminder': 'true'
  },
})

// Attach JWT token to every request
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('biochain_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-redirect to login on 401
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('biochain_token')
      localStorage.removeItem('biochain_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export const authApi = {
  login: (username, password) => {
    const form = new URLSearchParams()
    form.append('username', username)
    form.append('password', password)
    return client.post('/api/v1/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
  },
  me: () => client.get('/api/v1/auth/me'),
}

export const nodesApi = {
  getAll: () => client.get('/api/v1/nodes'),
}

export const optimizeApi = {
  start: (params) => client.post('/api/v1/optimize', params),
  getStatus: (taskId) => client.get(`/api/v1/optimize/status/${taskId}`),
  getResult: (taskId) => client.get(`/api/v1/results/${taskId}`),
  listResults: () => client.get('/api/v1/results'),
}

export const transactionApi = {
  // Harvests
  createHarvest: (data) => client.post('/api/v1/transactions/harvests', data),
  getHarvests: () => client.get('/api/v1/transactions/harvests'),
  // Hub Batches
  createHubBatch: (data) => client.post('/api/v1/transactions/hub-batches', data),
  getHubBatches: () => client.get('/api/v1/transactions/hub-batches'),
  // Shipments
  createShipment: (data) => client.post('/api/v1/transactions/shipments', data),
  getShipments: () => client.get('/api/v1/transactions/shipments'),
  // Daily Summary
  getDailySummary: () => client.get('/api/v1/transactions/daily-summary'),
}

export default client
