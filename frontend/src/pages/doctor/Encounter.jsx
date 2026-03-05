import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { doctorAPI } from '../../utils/api'
import { useAuth } from '../../context/AuthContext'

export default function Encounter() {
  const { appointmentId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [encounter, setEncounter] = useState(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [formData, setFormData] = useState({
    examination_notes: '',
    diagnosis: [],
    treatment_plan: '',
    prescription: {
      medications: [],
      additional_instructions: '',
      follow_up_date: '',
      follow_up_notes: '',
    },
  })

  useEffect(() => {
    initializeEncounter()
  }, [appointmentId])

  const initializeEncounter = async () => {
    setLoading(true)
    try {
      const encRes = await doctorAPI.startEncounter(appointmentId)
      setEncounter({ id: encRes.data.encounter_id })
      setError('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to initialize encounter')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const diagnosisText = document.getElementById('diagnosis-input')?.value || ''
      const diagnosisArray = diagnosisText
        .split(';')
        .map(d => ({ condition_name: d.trim() }))
        .filter(d => d.condition_name)

      const submitData = {
        examination_notes : formData.examination_notes,
        diagnosis         : diagnosisArray.length > 0 ? diagnosisArray : formData.diagnosis,
        treatment_plan    : formData.treatment_plan,
        prescription: {
          medications             : formData.prescription.medications,
          additional_instructions : formData.prescription.additional_instructions,
          follow_up_date          : formData.prescription.follow_up_date || null,
          follow_up_notes         : formData.prescription.follow_up_notes,
        },
      }

      await doctorAPI.completeEncounter(encounter.id, submitData)
      alert('Encounter completed! Prescription sent to patient.')
      navigate('/doctor/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to complete encounter')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Initializing encounter...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">

      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Patient Encounter</h1>
            <p className="text-sm text-gray-600">{user?.full_name}</p>
          </div>
          <button
            onClick={() => navigate('/doctor/dashboard')}
            className="px-4 py-2 text-sm text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            ← Back
          </button>
        </div>
      </div>

      {/* Form */}
      <div className="max-w-4xl mx-auto px-6 py-8">

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-6">
            {error}
          </div>
        )}

        {encounter && (
          <form onSubmit={handleSubmit} className="space-y-6">

            {/* 1 — Examination Notes */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <label className="block text-sm font-semibold text-gray-900 mb-2">
                Examination Notes
              </label>
              <textarea
                value={formData.examination_notes}
                onChange={e => setFormData(prev => ({ ...prev, examination_notes: e.target.value }))}
                placeholder="Enter your examination findings..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                rows={4}
              />
            </div>

            {/* 2 — Diagnosis */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <label className="block text-sm font-semibold text-gray-900 mb-2">
                Diagnosis
                <span className="font-normal text-gray-500 ml-1">(separate multiple with semicolons)</span>
              </label>
              <input
                id="diagnosis-input"
                type="text"
                placeholder="e.g., Hypertension; Type 2 Diabetes"
                defaultValue={formData.diagnosis.map(d => d.condition_name || '').join('; ')}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>

            {/* 3 — Treatment Plan */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <label className="block text-sm font-semibold text-gray-900 mb-2">
                Treatment Plan
              </label>
              <textarea
                value={formData.treatment_plan}
                onChange={e => setFormData(prev => ({ ...prev, treatment_plan: e.target.value }))}
                placeholder="Describe the treatment plan..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                rows={4}
              />
            </div>

            {/* 4 — Medications */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <label className="block text-sm font-semibold text-gray-900 mb-1">
                Medications
              </label>
              <p className="text-xs text-gray-500 mb-3">
                One per line: <span className="font-mono bg-gray-100 px-1 rounded">Medicine Name | Dosage | Frequency | Duration</span>
                <br />
                Example: <span className="font-mono bg-gray-100 px-1 rounded">Paracetamol | 500mg | Twice daily | 7 days</span>
              </p>
              <textarea
                value={
                  formData.prescription.medications
                    .map(m =>
                      typeof m === 'object'
                        ? `${m.drug_name || ''} | ${m.dosage || ''} | ${m.frequency || ''} | ${m.duration || ''}`
                        : m
                    )
                    .join('\n')
                }
                onChange={e => {
                  const meds = e.target.value
                    .split('\n')
                    .map(line => {
                      const parts = line.split('|').map(p => p.trim())
                      return {
                        drug_name   : parts[0] || line.trim(),
                        dosage      : parts[1] || '',
                        frequency   : parts[2] || '',
                        duration    : parts[3] || '',
                        instructions: '',
                      }
                    })
                    .filter(m => m.drug_name)
                  setFormData(prev => ({
                    ...prev,
                    prescription: { ...prev.prescription, medications: meds },
                  }))
                }}
                placeholder={'Paracetamol | 500mg | Twice daily | 7 days\nAmoxicillin | 250mg | Three times daily | 5 days'}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none font-mono text-sm resize-none"
                rows={4}
              />
            </div>

            {/* 5 — Follow-up Date */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <label className="block text-sm font-semibold text-gray-900 mb-2">
                Follow-up Date <span className="font-normal text-gray-500">(optional)</span>
              </label>
              <input
                type="date"
                value={formData.prescription.follow_up_date}
                onChange={e => setFormData(prev => ({
                  ...prev,
                  prescription: { ...prev.prescription, follow_up_date: e.target.value },
                }))}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>

            {/* 6 — Additional Instructions */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <label className="block text-sm font-semibold text-gray-900 mb-2">
                Additional Instructions <span className="font-normal text-gray-500">(optional)</span>
              </label>
              <textarea
                value={formData.prescription.additional_instructions}
                onChange={e => setFormData(prev => ({
                  ...prev,
                  prescription: { ...prev.prescription, additional_instructions: e.target.value },
                }))}
                placeholder="e.g., Take with food, avoid alcohol, rest for 3 days..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                rows={2}
              />
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-base"
            >
              {submitting ? 'Completing Encounter...' : '✓ Complete Encounter & Send Prescription'}
            </button>

          </form>
        )}
      </div>
    </div>
  )
}