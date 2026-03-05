import { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '../utils/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)

  // On app load: check if token exists and fetch user info
  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      authAPI.me()
        .then(res => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('token')
          localStorage.removeItem('role')
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (arg1, arg2) => {
    // Overloaded: either `login(email, password)` which calls the API,
    // or `login(token, role)` where the token was returned by an API call
    if (arg2 === 'patient' || arg2 === 'doctor') {
  const token = arg1
  const role = arg2
  localStorage.setItem('token', token)
  localStorage.setItem('role', role)
  try {
    const meRes = await authAPI.me()
    setUser(meRes.data)
  } catch {
    // me() failed but token is saved — set minimal user so redirect works
    setUser({ role, full_name: role === 'doctor' ? 'Doctor' : 'Patient' })
  }
  return role
}

    // Fallback: email/password
    const email = arg1
    const password = arg2
    const res = await authAPI.login({ email, password })
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('role', res.data.role)
    const meRes = await authAPI.me()
    setUser(meRes.data)
    return res.data.role
  }

  const logout = () => {
    authAPI.logout().catch(() => {})
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
