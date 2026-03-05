import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { patientAPI, appointmentAPI } from '../../utils/api'
import { useAuth } from '../../context/AuthContext'

export default function PatientDashboard() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [dashboard, setDashboard] = useState(null)
  const [appointments, setAppointments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [cancellingId, setCancellingId] = useState(null)

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    try {
      const [dashRes, apptsRes] = await Promise.all([
        patientAPI.dashboard(),
        patientAPI.appointments(),
      ])
      setDashboard(dashRes.data)
      setAppointments(apptsRes.data || [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }

  const handleCancelAppointment = async (appointmentId) => {
    if (!window.confirm('Are you sure you want to cancel this appointment?')) {
      return
    }

    setCancellingId(appointmentId)
    try {
      await appointmentAPI.cancel(appointmentId)
      setAppointments((prev) =>
        prev.map((appt) =>
          appt.appointment_id === appointmentId ? { ...appt, status: 'cancelled' } : appt
        )
      )
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to cancel appointment')
    } finally {
      setCancellingId(null)
    }
  }

  const handleBookAppointment = () => {
    navigate('/book')
  }

  const handleStartCheckIn = () => {
    if (!dashboard?.pending_intake) return
    navigate('/book', {
      state: { appointmentId: dashboard.pending_intake.appointment_id },
    })
  }

  const handleViewPrescriptions = () => {
    navigate('/prescriptions')
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const formatDateTime = (date, time) => {
    const d = new Date(date + 'T00:00:00')
    const dateStr = d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
    return `${dateStr} at ${time}`
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'scheduled':
        return 'bg-blue-100 border-blue-300 text-blue-800'
      case 'in_progress':
        return 'bg-purple-100 border-purple-300 text-purple-800'
      case 'completed':
        return 'bg-green-100 border-green-300 text-green-800'
      case 'cancelled':
        return 'bg-red-100 border-red-300 text-red-800'
      default:
        return 'bg-gray-100 border-gray-300 text-gray-800'
    }
  }

  const getStatus = (status) => {
    switch (status) {
      case 'scheduled':
        return 'Scheduled'
      case 'in_progress':
        return 'In Progress'
      case 'completed':
        return 'Completed'
      case 'cancelled':
        return 'Cancelled'
      default:
        return status
    }
  }

  const upcomingAppointments = appointments.filter((a) => a.status === 'scheduled')
  const pastAppointments = appointments.filter((a) => a.status !== 'scheduled')

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">My Dashboard</h1>
            <p className="text-sm text-gray-600">Welcome, {user?.full_name}</p>
          </div>
          <button
            onClick={handleLogout}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-5xl mx-auto px-6 py-8">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <>
            {/* Pending Intake (from backend dashboard) */}
            {dashboard?.pending_intake && (
              <div className="mb-8">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold text-blue-800 uppercase tracking-wide">
                      Pre-visit check-in needed
                    </p>
                    <p className="text-sm text-blue-900 mt-1">
                      You have an upcoming appointment with{' '}
                      <span className="font-semibold">
                        {dashboard.pending_intake.doctor_name}
                      </span>{' '}
                      on{' '}
                      {formatDateTime(
                        dashboard.pending_intake.scheduled_date,
                        dashboard.pending_intake.scheduled_time
                      )}
                      . Please complete your AI check-in before you arrive.
                    </p>
                  </div>
                  <button
                    onClick={handleStartCheckIn}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
                  >
                    Start check-in
                  </button>
                </div>
              </div>
            )}

            {/* Quick Actions */}
            <div className="grid grid-cols-2 gap-4 mb-8">
              <button
                onClick={handleBookAppointment}
                className="px-6 py-4 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors shadow-sm"
              >
                + Book New Appointment
              </button>
              <button
                onClick={handleViewPrescriptions}
                className="px-6 py-4 bg-white border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition-colors shadow-sm"
              >
                View Prescriptions
              </button>
            </div>

            {/* Upcoming Appointments */}
            <div className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Upcoming Appointments</h2>
              {upcomingAppointments.length === 0 ? (
                <div className="bg-white rounded-lg shadow-sm p-8 text-center border border-gray-200">
                  <p className="text-gray-500">No upcoming appointments</p>
                  <button
                    onClick={handleBookAppointment}
                    className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors inline-block"
                  >
                    Book an Appointment
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {upcomingAppointments.map((appt) => (
                    <div
                      key={appt.appointment_id}
                      className="bg-white rounded-lg shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-semibold text-gray-900">{appt.doctor_name}</h3>
                          <p className="text-sm text-gray-600 mt-1">
                            📅 {formatDateTime(appt.scheduled_date, appt.scheduled_time)}
                          </p>
                          {appt.reason && (
                            <p className="text-sm text-gray-600">
                              <strong>Reason:</strong> {appt.reason}
                            </p>
                          )}
                        </div>
                        <div className="text-right">
                          <span
                            className={`inline-block px-3 py-1 text-xs font-semibold rounded-full border ${getStatusColor(
                              appt.status
                            )}`}
                          >
                            {getStatus(appt.status)}
                          </span>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="mt-3 pt-3 border-t border-gray-200 flex gap-2">
                        <button
                          onClick={() => handleCancelAppointment(appt.appointment_id)}
                          disabled={cancellingId === appt.id}
                          className="px-4 py-2 bg-red-50 text-red-600 rounded-lg text-sm font-medium hover:bg-red-100 transition-colors disabled:opacity-50"
                        >
                          {cancellingId === appt.id ? 'Cancelling...' : 'Cancel'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Past Appointments */}
            {pastAppointments.length > 0 && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Past Appointments</h2>
                <div className="space-y-3">
                  {pastAppointments.map((appt) => (
                    <div
                      key={appt.id}
                      className="bg-gray-50 rounded-lg shadow-sm border border-gray-200 p-5 opacity-75"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-semibold text-gray-700">Dr. {appt.doctor_name}</h3>
                          <p className="text-sm text-gray-600 mt-1">
                            📅 {formatDateTime(appt.scheduled_date, appt.scheduled_time)}
                          </p>
                        </div>
                        <span
                          className={`inline-block px-3 py-1 text-xs font-semibold rounded-full border ${getStatusColor(
                            appt.status
                          )}`}
                        >
                          {getStatus(appt.status)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
