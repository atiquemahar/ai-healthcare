import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { doctorAPI } from '../../utils/api'
import { useAuth } from '../../context/AuthContext'

export default function DoctorDashboard() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().split('T')[0]
  )
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Load appointments for selected date
  useEffect(() => {
    loadDashboard()
  }, [selectedDate])

  const loadDashboard = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await doctorAPI.dashboard(selectedDate)
      setDashboardData(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load appointments')
    } finally {
      setLoading(false)
    }
  }

  const handlePreviousDay = () => {
    const d = new Date(selectedDate)
    d.setDate(d.getDate() - 1)
    setSelectedDate(d.toISOString().split('T')[0])
  }

  const handleNextDay = () => {
    const d = new Date(selectedDate)
    d.setDate(d.getDate() + 1)
    setSelectedDate(d.toISOString().split('T')[0])
  }

  const handleToday = () => {
    setSelectedDate(new Date().toISOString().split('T')[0])
  }

  const handleStartEncounter = (appointmentId) => {
    navigate(`/doctor/encounter/${appointmentId}`)
  }

  const handleViewHistory = (patientId) => {
    navigate(`/doctor/patients/${patientId}/history`)
  }

  const handleLogout = () => {
    logout()
    navigate('/doctor/login')
  }

  const formatDate = (dateStr) => {
    const d = new Date(dateStr + 'T00:00:00')
    return d.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
  }

  const getRiskColor = (riskLevel) => {
    switch (riskLevel) {
      case 'high':
        return 'bg-red-100 border-red-300 text-red-800'
      case 'medium':
        return 'bg-yellow-100 border-yellow-300 text-yellow-800'
      case 'low':
        return 'bg-green-100 border-green-300 text-green-800'
      default:
        return 'bg-gray-100 border-gray-300 text-gray-800'
    }
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'scheduled':
        return <span className="inline-block px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">Scheduled</span>
      case 'in_progress':
        return <span className="inline-block px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800">In Progress</span>
      case 'completed':
        return <span className="inline-block px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Completed</span>
      default:
        return <span className="inline-block px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">{status}</span>
    }
  }

  const getIntakeStatusBadge = (intakeStatus) => {
    switch (intakeStatus) {
      case 'none':
        return <span className="text-xs text-red-600">No intake</span>
      case 'in_progress':
        return <span className="text-xs text-yellow-600">In progress</span>
      case 'completed':
        return <span className="text-xs text-green-600">✓ Completed</span>
      default:
        return <span className="text-xs text-gray-600">{intakeStatus}</span>
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Doctor Dashboard</h1>
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
        {/* Date Selector */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6 border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Select Date</h2>
          <div className="flex items-center gap-3 flex-wrap">
            <button
              onClick={handlePreviousDay}
              className="px-3 py-1.5 bg-gray-100 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
            >
              ← Previous
            </button>

            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />

            <button
              onClick={handleNextDay}
              className="px-3 py-1.5 bg-gray-100 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
            >
              Next →
            </button>

            <button
              onClick={handleToday}
              className="px-3 py-1.5 bg-blue-50 text-blue-600 rounded-lg text-sm font-medium hover:bg-blue-100 transition-colors"
            >
              Today
            </button>
          </div>
          <p className="text-sm text-gray-600 mt-3">
            Viewing: <strong>{formatDate(selectedDate)}</strong>
          </p>
        </div>

        {/* Appointments Summary */}
        {dashboardData && (
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
              <p className="text-gray-600 text-sm font-medium">Total Appointments</p>
              <p className="text-3xl font-bold text-gray-900">{dashboardData.total_today}</p>
            </div>
            <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
              <p className="text-gray-600 text-sm font-medium">Pending</p>
              <p className="text-3xl font-bold text-blue-600">{dashboardData.pending}</p>
            </div>
            <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
              <p className="text-gray-600 text-sm font-medium">Completed</p>
              <p className="text-3xl font-bold text-green-600">{dashboardData.completed}</p>
            </div>
          </div>
        )}

        {/* Appointments List */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {loading && (
          <div className="flex justify-center py-12">
            <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {!loading && dashboardData && dashboardData.appointments.length === 0 && (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center border border-gray-200">
            <p className="text-gray-500 text-lg">No appointments scheduled for this date</p>
          </div>
        )}

        {!loading && dashboardData && dashboardData.appointments.length > 0 && (
          <div className="space-y-3">
            {dashboardData.appointments.map((appt) => (
              <div
                key={appt.appointment_id}
                className="bg-white rounded-lg shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-gray-900">{appt.patient_name}</h3>
                    <p className="text-sm text-gray-600 mt-1">
                      <strong>Time:</strong> {appt.scheduled_time}
                    </p>
                    <p className="text-sm text-gray-600">
                      <strong>Reason:</strong> {appt.reason}
                    </p>
                  </div>
                  <div className="text-right">
                    {getStatusBadge(appt.status)}
                  </div>
                </div>

                {/* Intake Status */}
                <div className={`rounded-lg p-3 mb-3 border ${getRiskColor(appt.risk_level)}`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs font-semibold mb-1">Intake Status:</p>
                      {getIntakeStatusBadge(appt.intake_status)}
                    </div>
                    {appt.risk_level && appt.risk_level !== 'none' && (
                      <p className="text-xs font-semibold">Risk: {appt.risk_level.toUpperCase()}</p>
                    )}
                  </div>
                  {appt.intake_summary && (
                    <p className="text-xs mt-2 leading-relaxed opacity-90">{appt.intake_summary}</p>
                  )}
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  {appt.status !== 'completed' && appt.intake_status === 'completed' && (
                    <button
                      onClick={() => handleStartEncounter(appt.appointment_id)}
                      className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
                    >
                      Start Encounter
                    </button>
                  )}
                  {appt.status === 'completed' && (
                    <button
                      disabled
                      className="flex-1 px-4 py-2 bg-gray-200 text-gray-600 rounded-lg text-sm font-medium cursor-not-allowed"
                    >
                      Completed
                    </button>
                  )}
                  {appt.status !== 'completed' && appt.intake_status !== 'completed' && (
                    <button
                      disabled
                      className="flex-1 px-4 py-2 bg-gray-200 text-gray-600 rounded-lg text-sm font-medium cursor-not-allowed"
                      title="Waiting for patient intake to complete"
                    >
                      Waiting for Intake...
                    </button>
                  )}
                  <button
                    onClick={() => handleViewHistory(appt.patient_id)}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
                  >
                    History
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
