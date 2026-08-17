// context/AuthContext.jsx — Global auth state with Zustand + React Context
import { createContext, useContext, useEffect, useState } from 'react'
import { authApi } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Rehydrate from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem('biochain_user')
    const token = localStorage.getItem('biochain_token')
    if (stored && token) {
      try {
        setUser(JSON.parse(stored))
      } catch {
        localStorage.removeItem('biochain_user')
      }
    }
    setLoading(false)
  }, [])

  const login = async (username, password) => {
    const res = await authApi.login(username, password)
    const { access_token, role, full_name, kabupaten } = res.data
    const userData = { username, role, full_name, kabupaten }
    localStorage.setItem('biochain_token', access_token)
    localStorage.setItem('biochain_user', JSON.stringify(userData))
    setUser(userData)
    return userData
  }

  const logout = () => {
    localStorage.removeItem('biochain_token')
    localStorage.removeItem('biochain_user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}
