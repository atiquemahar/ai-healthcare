import { useEffect, useState } from 'react'
import { patientAPI } from '../../utils/api'

export default function Prescriptions() {
  const [prescriptions, setPrescriptions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchPrescriptions()
  }, [])

  const fetchPrescriptions = async () => {
    try {
      const response = await patientAPI.prescriptions()
      setPrescriptions(response.data || [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load prescriptions')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8 text-gray-800">My Prescriptions</h1>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {prescriptions.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-6 text-center">
            <p className="text-gray-600">No prescriptions yet</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {prescriptions.map((prescription) => (
              <div
                key={prescription.prescription_id}
                className="bg-white rounded-lg shadow p-6"
              >
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-xl font-semibold text-gray-800">
                      Prescription #{prescription.prescription_id}
                    </h3>
                    <p className="text-gray-600 text-sm">
                      {prescription.date}
                    </p>
                    <p className="text-gray-600 text-sm mt-1">
                      Doctor: {prescription.doctor_name}
                    </p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                    prescription.status === 'sent'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-blue-100 text-blue-800'
                  }`}>
                    {prescription.status}
                  </span>
                </div>

                <div className="mb-4">
                  <h4 className="font-semibold text-gray-700 mb-2">Medications</h4>
                  <ul className="space-y-1">
                    {Array.isArray(prescription.medications) && prescription.medications.length > 0 ? (
                      prescription.medications.map((med, idx) => {
                        if (typeof med === 'string') {
                          return (
                            <li key={idx} className="text-gray-600">
                              • {med}
                            </li>
                          )
                        }
                        return (
                          <li key={idx} className="text-gray-600">
                            • {med.drug_name || med.name}{' '}
                            {med.dosage ? `— ${med.dosage}` : ''}{' '}
                            {med.frequency ? `(${med.frequency})` : ''}
                          </li>
                        )
                      })
                    ) : (
                      <li className="text-gray-500">No medications listed</li>
                    )}
                  </ul>
                </div>

                {prescription.follow_up_date && (
                  <div className="text-sm text-gray-600 mb-4">
                    <strong>Follow-up:</strong> {prescription.follow_up_date}
                  </div>
                )}

                {prescription.pdf_url && (
                  <a
                    href={prescription.pdf_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded transition"
                  >
                    Download PDF
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
