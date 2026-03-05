import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Axios instance with base config
const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token to every request automatically
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// If token expired (401), clear auth and redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const isLoginPage = window.location.pathname.includes('/login')
      if (!isLoginPage) {
        localStorage.removeItem('token')
        localStorage.removeItem('role')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// ─── Auth ──────────────────────────────────────────────────────────────────
export const authAPI = {
  register: (data) => api.post('/api/auth/register', data),
  login:    (data) => api.post('/api/auth/login', data),
  logout:   ()     => api.post('/api/auth/logout'),
  me:       ()     => api.get('/api/auth/me'),
}

// ─── Patient ───────────────────────────────────────────────────────────────
export const patientAPI = {
  dashboard:           ()     => api.get('/api/patients/me/dashboard'),
  appointments:        ()     => api.get('/api/patients/me/appointments'),
  prescriptions:       ()     => api.get('/api/patients/me/prescriptions'),
  prescription:        (id)   => api.get(`/api/patients/me/prescriptions/${id}`),
}

// ─── Appointments ──────────────────────────────────────────────────────────
export const appointmentAPI = {
  getDoctors:       ()              => api.get('/api/doctors'),
  book:             (data)          => api.post('/api/appointments', data),
  checkStatus:      (id)            => api.get(`/api/appointments/${id}/status`),
  cancel:           (id)            => api.put(`/api/appointments/${id}/cancel`),
  availableSlots:   (doctorId, d)   =>
    api.get(`/api/doctors/${doctorId}/available-slots`, { params: { date: d } }),
}

// ─── Intake / AI Chat ──────────────────────────────────────────────────────
export const intakeAPI = {
  startSession:  (data)   => api.post('/api/intake/sessions', data),
  getContext:    (id)     => api.get(`/api/intake/sessions/${id}/context`),
  sendMessage:   (id, msg) => api.post(`/api/intake/sessions/${id}/messages`, { content: msg }),
  complete:      (id)     => api.post(`/api/intake/sessions/${id}/complete`),
}

// ─── Doctor ────────────────────────────────────────────────────────────────
export const doctorAPI = {
  dashboard:        (date)  => api.get('/api/doctor/dashboard', { params: { target_date: date } }),
  patientHistory:   (id)    => api.get(`/api/doctor/patients/${id}/history`),
  startEncounter:   (apptId) => api.post('/api/doctor/encounters', null, { params: { appointment_id: apptId } }),
  completeEncounter:(id, data) => api.post(`/api/doctor/encounters/${id}/complete`, data),
}

export default api
