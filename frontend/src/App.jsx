import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'

// Patient pages
import PatientLogin    from './pages/patient/Login'
import Register        from './pages/patient/Register'
import PatientDashboard from './pages/patient/Dashboard'
import BookAppointment from './pages/patient/BookAppointment'
import Prescriptions   from './pages/patient/Prescriptions'

// Doctor pages
import DoctorLogin     from './pages/doctor/Login'
import DoctorDashboard from './pages/doctor/Dashboard'
import Encounter       from './pages/doctor/Encounter'
import PatientHistory  from './pages/doctor/PatientHistory'

function ProtectedRoute({ children, requiredRole }) {
  const { user, loading } = useAuth()

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  if (!user) return <Navigate to="/login" replace />
  if (requiredRole && user.role !== requiredRole) return <Navigate to="/" replace />
  return children
}

function HomeRedirect() {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  if (user.role === 'doctor') return <Navigate to="/doctor/dashboard" replace />
  return <Navigate to="/dashboard" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<HomeRedirect />} />

          {/* Patient routes */}
          <Route path="/login"    element={<PatientLogin />} />
          <Route path="/register" element={<Register />} />
          <Route path="/dashboard" element={
            <ProtectedRoute requiredRole="patient">
              <PatientDashboard />
            </ProtectedRoute>
          } />
          <Route path="/book" element={
            <ProtectedRoute requiredRole="patient">
              <BookAppointment />
            </ProtectedRoute>
          } />
          <Route path="/prescriptions" element={
            <ProtectedRoute requiredRole="patient">
              <Prescriptions />
            </ProtectedRoute>
          } />

          {/* Doctor routes */}
          <Route path="/doctor/login"     element={<DoctorLogin />} />
          <Route path="/doctor/dashboard" element={
            <ProtectedRoute requiredRole="doctor">
              <DoctorDashboard />
            </ProtectedRoute>
          } />
          <Route path="/doctor/encounter/:appointmentId" element={
            <ProtectedRoute requiredRole="doctor">
              <Encounter />
            </ProtectedRoute>
          } />
          <Route path="/doctor/patients/:patientId/history" element={
            <ProtectedRoute requiredRole="doctor">
              <PatientHistory />
            </ProtectedRoute>
          } />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
