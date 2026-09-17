import axios from 'axios'

const request = axios.create({
  baseURL: '/api',
  timeout: 600000,
})

export function generateLessonPlan(data) {
  return request.post('/generate', data)
}

export function parseTextbookFile(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/parse-file', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
