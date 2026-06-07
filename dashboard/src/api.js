import axios from 'axios'

const api = axios.create({ baseURL: '/api/v1' })

export async function createSession(name, spec) {
  const { data } = await api.post('/sessions', { name, spec })
  return data
}

export async function getSessions() {
  const { data } = await api.get('/sessions')
  return data
}

export async function getSession(id) {
  const { data } = await api.get(`/sessions/${id}`)
  return data
}

export async function getBlackboard(id) {
  const { data } = await api.get(`/sessions/${id}/blackboard`)
  return data
}

export async function getFiles(id) {
  const { data } = await api.get(`/sessions/${id}/files`)
  return data
}

export async function getFileContent(id, filePath) {
  const { data } = await api.get(`/sessions/${id}/files/${filePath}`)
  return data
}

export async function saveFileContent(id, filePath, content) {
  const { data } = await api.put(`/sessions/${id}/files/${filePath}`, { content })
  return data
}

export async function getAgents(id) {
  const { data } = await api.get(`/sessions/${id}/agents`)
  return data
}

export async function getLogs(id, params = {}) {
  const { data } = await api.get(`/sessions/${id}/logs`, { params })
  return data
}

export async function getQuality(id) {
  const { data } = await api.get(`/sessions/${id}/quality`)
  return data
}

export async function getEvents(id, lastId = '0-0') {
  const { data } = await api.get(`/sessions/${id}/events`, { params: { last_id: lastId } })
  return data
}

export async function cancelSession(id) {
  const { data } = await api.post(`/sessions/${id}/cancel`)
  return data
}

export async function deleteSession(id) {
  await api.delete(`/sessions/${id}`)
  return true
}

export function getDownloadUrl(id) {
  return `/api/v1/sessions/${id}/download`
}

export { api }
