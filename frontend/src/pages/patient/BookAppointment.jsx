import { useState, useEffect, useRef } from 'react'
import { appointmentAPI, intakeAPI } from '../../utils/api'
import { useAuth } from '../../context/AuthContext'

// ─── Step indicators ─────────────────────────────────────────────────────────
const STEP = {
  BOOKING_FORM: 'booking_form',
  CONFIRMING:   'confirming',    // polling for appointment
  CONFIRMED:    'confirmed',     // show confirmed card briefly
  CHAT:         'chat',          // intake chat
  DONE:         'done',          // intake complete
}

export default function BookAppointment() {
  const { user } = useAuth()
  const [step, setStep]                   = useState(STEP.BOOKING_FORM)
  const [doctors, setDoctors]             = useState([])
  const [form, setForm]                   = useState({ doctor_id: '', scheduled_date: '', scheduled_time: '', reason: '' })
  const [error, setError]                 = useState('')
  const [appointment, setAppointment]     = useState(null)
  const [session, setSession]             = useState(null)
  const [messages, setMessages]           = useState([])
  const [inputText, setInputText]         = useState('')
  const [aiTyping, setAiTyping]           = useState(false)
  const chatBottomRef = useRef(null)

  // Load doctors on mount
  useEffect(() => {
    appointmentAPI.getDoctors()
      .then(res => setDoctors(res.data))
      .catch(() => setError('Failed to load doctors'))
  }, [])

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, aiTyping])

  // ─── Step 1: Submit booking form ─────────────────────────────────────────

  const handleBookingSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setStep(STEP.CONFIRMING)

    try {
      // Book appointment — returns immediately with appointment in DB
      const res = await appointmentAPI.book({
        doctor_id      : parseInt(form.doctor_id),
        scheduled_date : form.scheduled_date,
        scheduled_time : form.scheduled_time,
        reason         : form.reason,
        appointment_type: 'new_visit',
      })

      const apptId = res.data.id
      setAppointment(res.data)

      // Poll until confirmed (Option B)
      await pollForAppointment(apptId)

    } catch (err) {
      setError(err.response?.data?.detail || 'Booking failed. Please try again.')
      setStep(STEP.BOOKING_FORM)
    }
  }

  // Poll every second until appointment is confirmed in DB
  const pollForAppointment = async (appointmentId) => {
    for (let i = 0; i < 15; i++) {
      await sleep(1000)
      try {
        const res = await appointmentAPI.checkStatus(appointmentId)
        if (res.data.ready) {
          setAppointment(prev => ({ ...prev, ...res.data }))
          setStep(STEP.CONFIRMED)

          // After 2 seconds showing confirmed card, start chat
          setTimeout(() => initChat(appointmentId), 2000)
          return
        }
      } catch {}
    }
    // After 15 seconds, proceed anyway (appointment was created)
    setStep(STEP.CONFIRMED)
    setTimeout(() => initChat(appointmentId), 2000)
  }

  // ─── Start chat session ───────────────────────────────────────────────────

  const initChat = async (appointmentId) => {
    try {
      const sessionRes = await intakeAPI.startSession({ appointment_id: appointmentId })
      const newSession = sessionRes.data
      setSession(newSession)
      setStep(STEP.CHAT)

      // Load context then get opening AI message
      await intakeAPI.getContext(newSession.id)

      // Send an empty "start" message to get Claude's greeting
      setAiTyping(true)
      const msgRes = await intakeAPI.sendMessage(newSession.id, '__start__')
      setMessages([{ role: 'ai', content: msgRes.data.ai_response }])
      setAiTyping(false)

    } catch (err) {
      setError('Failed to start intake. Please try again.')
      setStep(STEP.CONFIRMED)
    }
  }

  // ─── Send patient message ─────────────────────────────────────────────────

  const handleSendMessage = async () => {
    if (!inputText.trim() || aiTyping) return

    const userMsg = inputText.trim()
    setInputText('')
    setMessages(prev => [...prev, { role: 'patient', content: userMsg }])
    setAiTyping(true)

    try {
      const res = await intakeAPI.sendMessage(session.id, userMsg)
      setMessages(prev => [...prev, { role: 'ai', content: res.data.ai_response }])
    } catch {
      setMessages(prev => [...prev, { role: 'ai', content: "I'm having a technical issue. Please try again." }])
    } finally {
      setAiTyping(false)
    }
  }

  // ─── Complete intake ──────────────────────────────────────────────────────

  const handleDone = async () => {
    try {
      await intakeAPI.complete(session.id)
      setStep(STEP.DONE)
    } catch {
      setError('Failed to complete intake. Your chat has been saved.')
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  // ─── Render ───────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-8">

        {/* Progress indicator */}
        <div className="flex items-center gap-2 mb-8">
          {[STEP.BOOKING_FORM, STEP.CONFIRMED, STEP.CHAT, STEP.DONE].map((s, i) => (
            <div key={s} className="flex items-center gap-2">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold
                ${step === s || (step === STEP.CONFIRMING && s === STEP.BOOKING_FORM)
                  ? 'bg-blue-600 text-white'
                  : [STEP.BOOKING_FORM, STEP.CONFIRMED, STEP.CHAT, STEP.DONE].indexOf(step) > i
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-200 text-gray-500'
                }`}>
                {i + 1}
              </div>
              {i < 3 && <div className="w-8 h-px bg-gray-300" />}
            </div>
          ))}
          <span className="ml-2 text-sm text-gray-500">
            {step === STEP.BOOKING_FORM || step === STEP.CONFIRMING ? 'Book Appointment' :
             step === STEP.CONFIRMED ? 'Confirmed!' :
             step === STEP.CHAT ? 'Pre-Visit Check-in' : 'All Done'}
          </span>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-6 text-sm">
            {error}
          </div>
        )}

        {/* ── STEP 1: Booking Form ──────────────────────────────────────── */}
        {step === STEP.BOOKING_FORM && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Book an Appointment</h1>
            <p className="text-gray-500 text-sm mb-6">After booking, you'll complete a short pre-visit check-in right here.</p>

            <form onSubmit={handleBookingSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Select Doctor</label>
                <select
                  required
                  value={form.doctor_id}
                  onChange={e => setForm(f => ({ ...f, doctor_id: e.target.value }))}
                  className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                >
                  <option value="">Choose a doctor...</option>
                  {doctors.map(d => (
                    <option key={d.id} value={d.id}>
                      {d.full_name} — {d.specialization}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                  <input
                    type="date"
                    required
                    min={new Date().toISOString().split('T')[0]}
                    value={form.scheduled_date}
                    onChange={e => setForm(f => ({ ...f, scheduled_date: e.target.value }))}
                    className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Time</label>
                  <select
                    required
                    value={form.scheduled_time}
                    onChange={e => setForm(f => ({ ...f, scheduled_time: e.target.value }))}
                    className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                  >
                    <option value="">Select time...</option>
                    {['09:00','09:30','10:00','10:30','11:00','11:30',
                      '14:00','14:30','15:00','15:30','16:00','16:30'].map(t => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Reason for visit <span className="text-gray-400">(optional)</span>
                </label>
                <input
                  type="text"
                  placeholder="e.g., chest pain, follow-up, routine check"
                  value={form.reason}
                  onChange={e => setForm(f => ({ ...f, reason: e.target.value }))}
                  className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>

              <button
                type="submit"
                className="w-full bg-blue-600 text-white rounded-lg py-3 font-semibold hover:bg-blue-700 transition-colors"
              >
                Confirm Booking
              </button>
            </form>
          </div>
        )}

        {/* ── STEP 2: Confirming (polling) ─────────────────────────────── */}
        {step === STEP.CONFIRMING && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 text-center">
            <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-800">Confirming your appointment...</h2>
            <p className="text-gray-500 text-sm mt-2">This takes just a second</p>
          </div>
        )}

        {/* ── STEP 3: Confirmed card ────────────────────────────────────── */}
        {step === STEP.CONFIRMED && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-3xl">✅</span>
            </div>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">Booking Confirmed!</h2>
            <p className="text-blue-600 font-medium">
              {appointment?.doctor_name} — {appointment?.scheduled_date} at {appointment?.scheduled_time}
            </p>
            <p className="text-gray-500 text-sm mt-3">Starting your pre-visit check-in...</p>
          </div>
        )}

        {/* ── STEP 4: Chat ──────────────────────────────────────────────── */}
        {step === STEP.CHAT && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            {/* Chat header */}
            <div className="bg-blue-600 text-white px-6 py-4">
              <h2 className="font-semibold">Pre-Visit Check-in</h2>
              <p className="text-blue-200 text-sm">
                AI Assistant for {appointment?.doctor_name || 'your doctor'}
              </p>
            </div>

            {/* Messages */}
            <div className="h-96 overflow-y-auto p-6 space-y-4">
              {messages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === 'patient' ? 'justify-end' : 'justify-start'}`}>
                  {msg.role === 'ai' && (
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3 mt-1 flex-shrink-0">
                      <span className="text-sm">🤖</span>
                    </div>
                  )}
                  <div className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl text-sm leading-relaxed
                    ${msg.role === 'patient'
                      ? 'bg-blue-600 text-white rounded-br-none'
                      : 'bg-gray-100 text-gray-800 rounded-bl-none'
                    }`}>
                    {msg.content}
                  </div>
                </div>
              ))}

              {aiTyping && (
                <div className="flex justify-start">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3 flex-shrink-0">
                    <span className="text-sm">🤖</span>
                  </div>
                  <div className="bg-gray-100 px-4 py-3 rounded-2xl rounded-bl-none">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatBottomRef} />
            </div>

            {/* Input area */}
            <div className="border-t border-gray-100 p-4">
              <div className="flex gap-3">
                <input
                  type="text"
                  placeholder="Type your answer..."
                  value={inputText}
                  onChange={e => setInputText(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={aiTyping}
                  className="flex-1 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none disabled:opacity-50"
                />
                <button
                  onClick={handleSendMessage}
                  disabled={aiTyping || !inputText.trim()}
                  className="bg-blue-600 text-white rounded-lg px-4 py-2.5 font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Send
                </button>
              </div>
              <div className="flex justify-between items-center mt-3">
                <p className="text-xs text-gray-400">Press Enter to send</p>
                <button
                  onClick={handleDone}
                  className="text-sm text-gray-500 hover:text-gray-700 underline"
                >
                  I'm done answering →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── STEP 5: Done ──────────────────────────────────────────────── */}
        {step === STEP.DONE && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-3xl">🎉</span>
            </div>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">Check-in Complete!</h2>
            <p className="text-gray-600 text-sm mb-4">
              Your doctor will review your answers before the appointment.
              You don't need to do anything else right now.
            </p>
            <a
              href="/dashboard"
              className="inline-block bg-blue-600 text-white rounded-lg px-6 py-2.5 font-medium hover:bg-blue-700 transition-colors text-sm"
            >
              Back to Dashboard
            </a>
          </div>
        )}

      </div>
    </div>
  )
}

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))
