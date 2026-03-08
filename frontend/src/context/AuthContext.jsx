import { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '../utils/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)

  // On app load: restore user from localStorage if token exists
  useEffect(() => {
    const token     = localStorage.getItem('token')
    const savedUser = localStorage.getItem('user')

    if (token && savedUser) {
      try {
        setUser(JSON.parse(savedUser))
      } catch {
        localStorage.removeItem('token')
        localStorage.removeItem('role')
        localStorage.removeItem('user')
      }
    }
    setLoading(false)
  }, [])

  const login = async (arg1, arg2) => {
    if (arg2 === 'patient' || arg2 === 'doctor') {
      const token   = typeof arg1 === 'object' ? arg1.access_token : arg1
      const role    = arg2
      const userObj = typeof arg1 === 'object'
        ? arg1.user
        : { role, full_name: role === 'doctor' ? 'Doctor' : 'Patient' }

      localStorage.setItem('token', token)
      localStorage.setItem('role', role)
      localStorage.setItem('user', JSON.stringify(userObj))
      setUser(userObj)
      return role
    }

    // Legacy: login(email, password)
    const res = await authAPI.login({ email: arg1, password: arg2 })
    const { access_token, role, user: userObj } = res.data

    localStorage.setItem('token', access_token)
    localStorage.setItem('role', role)
    localStorage.setItem('user', JSON.stringify(userObj))
    setUser(userObj)
    return role
  }

  const logout = () => {
    authAPI.logout().catch(() => {})
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    localStorage.removeItem('user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
