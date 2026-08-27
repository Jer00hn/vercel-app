import axios from 'axios'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
})

// ============ ПУБЛИЧНЫЕ ============
export const checkSubscription = async (username) => {
  const response = await api.get('/subscription/status', {
    params: { username }
  })
  return response.data
}

// ============ АДМИНСКИЕ ============
export const addSubscription = async (username, durationDays, config) => {
  const response = await api.post('/subscription/admin/add', null, {
    ...config,
    params: { username, duration_days: durationDays }
  })
  return response.data
}

export const extendSubscription = async (username, extraDays, config) => {
  const response = await api.put('/subscription/admin/extend', null, {
    ...config,
    params: { username, extra_days: extraDays }
  })
  return response.data
}

export const revokeSubscription = async (username, config) => {
  const response = await api.delete('/subscription/admin/revoke', {
    ...config,
    params: { username }
  })
  return response.data
}

export const listSubscriptions = async (config) => {
  const response = await api.get('/subscription/admin/list', config)
  return response.data
}

export const bulkRevokeSubscriptions = async (usernames, config) => {
  const response = await api.delete('/subscription/admin/bulk-revoke', {
    ...config,
    params: { usernames: usernames.join(',') }
  })
  return response.data
}