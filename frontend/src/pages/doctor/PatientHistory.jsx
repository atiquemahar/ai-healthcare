import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { doctorAPI } from '../../utils/api'

export default function PatientHistory() {
  const { patientId } = useParams()
  const navigate = useNavigate()
  const [history, setHistory] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchPatientHistory()
  }, [patientId])

  const fetchPatientHistory = async () => {
    try {
      const res = await doctorAPI.patientHistory(patientId)
      setHistory(res.data)
      setError('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load patient history')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading patient history...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-6 py-8">
          <button
            onClick={() => navigate('/doctor/dashboard')}
            className="mb-4 text-blue-600 hover:text-blue-700"
          >
            ← Back to Dashboard
          </button>
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4">
            {error}
          </div>
        </div>
      </div>
    )
  }

  const patient = history?.patient
  const encounters = history?.history || []
  const activeMediacations = history?.active_medications || []
  const knownAllergies = history?.known_allergies || []

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <button
            onClick={() => navigate('/doctor/dashboard')}
            className="text-blue-600 hover:text-blue-700 text-sm mb-2"
          >
            ← Back to Dashboard
          </button>
          <h1 className="text-2xl font-bold text-gray-900">Patient History</h1>
          {patient && <p className="text-sm text-gray-600">{patient.full_name}</p>}
        </div>
      </div>

      {/* Content */}
      <div className="max-w-5xl mx-auto px-6 py-8">
        
        {/* Patient Info */}
        {patient && (
          <div className="bg-white rounded-lg shadow p-6 mb-6 border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Patient Information</h2>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-gray-600">Full Name</p>
                <p className="text-lg font-semibold text-gray-900">{patient.full_name}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Email</p>
                <p className="text-lg font-semibold text-gray-900">{patient.email}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Phone</p>
                <p className="text-lg font-semibold text-gray-900">{patient.phone || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Gender</p>
                <p className="text-lg font-semibold text-gray-900">
                  {patient.gender === 'M' ? 'Male' : patient.gender === 'F' ? 'Female' : 'Other'}
                </p>
              </div>
            </div>

            {/* Active Info */}
            <div className="grid grid-cols-2 gap-6 mt-6 pt-6 border-t border-gray-200">
              <div>
                <p className="text-sm font-semibold text-gray-700 mb-2">Current Medications</p>
                <ul className="space-y-1">
                  {activeMediacations.length > 0 ? (
                    activeMediacations.map((med, idx) => (
                      <li key={idx} className="text-sm text-gray-600">
                        • {typeof med === 'string' ? med : med.name}
                      </li>
                    ))
                  ) : (
                    <li className="text-sm text-gray-500">No medications reported</li>
                  )}
                </ul>
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-700 mb-2">Known Allergies</p>
                <ul className="space-y-1">
                  {knownAllergies.length > 0 ? (
                    knownAllergies.map((allergy, idx) => (
                      <li key={idx} className="text-sm text-gray-600">
                        • {typeof allergy === 'string' ? allergy : allergy.allergen}
                      </li>
                    ))
                  ) : (
                    <li className="text-sm text-gray-500">No allergies reported</li>
                  )}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Encounters */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Visit History ({encounters.length})</h2>
          {encounters.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-6 text-center border border-gray-200">
              <p className="text-gray-500">No prior encounters</p>
            </div>
          ) : (
            <div className="space-y-4">
              {encounters.map((encounter) => (
                <div key={encounter.encounter_id} className="bg-white rounded-lg shadow border border-gray-200 p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <p className="text-sm text-gray-600">
                        {encounter.date
                          ? new Date(encounter.date + 'T00:00:00').toLocaleDateString(
                              'en-US',
                              {
                                weekday: 'short',
                                year: 'numeric',
                                month: 'short',
                                day: 'numeric',
                              }
                            )
                          : 'Date not recorded'}
                      </p>
                      <h3 className="text-lg font-semibold text-gray-900">Encounter #{encounter.encounter_id}</h3>
                    </div>
                    <span className="inline-block px-3 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded-full">
                      Completed
                    </span>
                  </div>

                  {encounter.chief_complaint && (
                    <div className="mb-4">
                      <p className="text-sm font-semibold text-gray-700">Chief Complaint</p>
                      <p className="text-sm text-gray-600">{encounter.chief_complaint}</p>
                    </div>
                  )}

                  {encounter.intake_summary && (
                    <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
                      <p className="text-xs font-semibold text-blue-900 mb-1">AI Summary</p>
                      <p className="text-sm text-blue-800">{encounter.intake_summary}</p>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <p className="text-sm font-semibold text-gray-700">Diagnosis</p>
                      <p className="text-sm text-gray-600">
                        {Array.isArray(encounter.diagnosis) && encounter.diagnosis.length > 0
                          ? encounter.diagnosis
                              .map((d) => d.condition_name || d.icd10_code || '')
                              .filter(Boolean)
                              .join(', ')
                          : 'Not recorded'}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-gray-700">Treatment Plan</p>
                      <p className="text-sm text-gray-600">{encounter.treatment_plan || 'Not recorded'}</p>
                    </div>
                  </div>

                  {encounter.examination_notes && (
                    <div className="mb-4">
                      <p className="text-sm font-semibold text-gray-700">Notes</p>
                      <p className="text-sm text-gray-600">{encounter.examination_notes}</p>
                    </div>
                  )}

                  {encounter.prescription && (
                    <div className="p-3 bg-yellow-50 border border-yellow-200 rounded">
                      <p className="text-xs font-semibold text-yellow-900 mb-2">Prescription</p>
                      <ul className="text-sm text-yellow-800 space-y-1">
                        {Array.isArray(encounter.prescription.medications) &&
                        encounter.prescription.medications.length > 0 ? (
                          encounter.prescription.medications.slice(0, 3).map((med, idx) => {
                            if (typeof med === 'string') {
                              return <li key={idx}>• {med}</li>
                            }
                            return (
                              <li key={idx}>
                                • {med.drug_name || med.name}{' '}
                                {med.dosage ? `— ${med.dosage}` : ''}{' '}
                                {med.frequency ? `(${med.frequency})` : ''}
                              </li>
                            )
                          })
                        ) : (
                          <li>No medications listed</li>
                        )}
                        {encounter.prescription.medications?.length > 3 && (
                          <li>• +{encounter.prescription.medications.length - 3} more</li>
                        )}
                      </ul>
                      {encounter.prescription.follow_up && (
                        <p className="text-xs text-yellow-800 mt-2">
                          Follow-up: {new Date(
                            encounter.prescription.follow_up + 'T00:00:00'
                          ).toLocaleDateString()}
                        </p>
                      )}
                      {encounter.prescription.pdf_url && (
                        <a
                          href={encounter.prescription.pdf_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-block text-xs text-blue-700 hover:underline mt-2"
                        >
                          View PDF
                        </a>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
