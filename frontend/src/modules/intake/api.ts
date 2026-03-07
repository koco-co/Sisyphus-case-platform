import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export interface CreateTaskPayload {
  project_id: number
  title: string
  source_type: string
  business_domain?: string
  input_summary?: string
}

export async function createTask(payload: CreateTaskPayload) {
  const response = await api.post('/tasks', payload)
  return response.data
}

export async function uploadTaskDocument(taskId: number, file: File) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post(`/tasks/${taskId}/documents`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}
