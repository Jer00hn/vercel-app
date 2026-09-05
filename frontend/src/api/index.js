import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('admin_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 403) {
      localStorage.removeItem('admin_token')
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

export const subscriptionApi = {
  getStatus(username) {
    return api.get('/subscription/status', { params: { username } })
  },
  getAllSubscriptions(params = {}) {
    return api.get('/subscription/admin/list', { params })
  },
  getStats() {
    return api.get('/subscription/admin/stats')
  },
  addSubscription(username, durationDays) {
    return api.post('/subscription/admin/add', null, {
      params: { username, duration_days: durationDays }
    })
  },
  extendSubscription(username, extraDays) {
    return api.put('/subscription/admin/extend', null, {
      params: { username, extra_days: extraDays }
    })
  },
  revokeSubscription(username) {
    return api.delete('/subscription/admin/revoke', {
      params: { username }
    })
  },
  clearAll() {
    return api.delete('/subscription/admin/clear')
  }
}

export default api
