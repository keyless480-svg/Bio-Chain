// App.jsx — Root router with role-based protected routes
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from './context/AuthContext'
import LoginPage        from './pages/LoginPage'
import AnalystDashboard from './pages/analyst/AnalystDashboard'
import FarmerPage       from './pages/farmer/FarmerPage'
import CollectorPage    from './pages/collector/CollectorPage'
import DriverPage       from './pages/driver/DriverPage'

const ROLE_HOME = {
  admin:     '/analyst',
  analyst:   '/analyst',
  farmer:    '/farmer',
  collector: '/collector',
  driver:    '/driver',
}

/** Redirects unauthenticated users to /login */
function ProtectedRoute({ children, allowedRoles }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <div style={{ textAlign: 'center' }}>
          <div className="spinner" style={{ margin: '0 auto 16px', width: 48, height: 48, borderWidth: 5 }} />
          <p style={{ color: 'var(--color-gray-500)' }}>Memuat BioChain-Opt...</p>
        </div>
      </div>
    )
  }

  if (!user) return <Navigate to="/login" replace />

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    // Redirect to user's correct home page
    return <Navigate to={ROLE_HOME[user.role] || '/login'} replace />
  }

  return children
}

/** Redirects authenticated users away from /login to their home */
function PublicRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (user) return <Navigate to={ROLE_HOME[user.role] || '/analyst'} replace />
  return children
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />

      {/* Protected — Analyst (Government/Corporate/Admin) */}
      <Route path="/analyst" element={
        <ProtectedRoute allowedRoles={['analyst', 'admin']}>
          <AnalystDashboard />
        </ProtectedRoute>
      } />

      {/* Protected — Farmer */}
      <Route path="/farmer" element={
        <ProtectedRoute allowedRoles={['farmer']}>
          <FarmerPage />
        </ProtectedRoute>
      } />

      {/* Protected — Collector (KUD) */}
      <Route path="/collector" element={
        <ProtectedRoute allowedRoles={['collector']}>
          <CollectorPage />
        </ProtectedRoute>
      } />

      {/* Protected — Driver */}
      <Route path="/driver" element={
        <ProtectedRoute allowedRoles={['driver']}>
          <DriverPage />
        </ProtectedRoute>
      } />

      {/* Root → redirect based on auth state */}
      <Route path="/" element={<RootRedirect />} />

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function RootRedirect() {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  return <Navigate to={ROLE_HOME[user.role] || '/login'} replace />
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
        <Toaster
          position="top-center"
          toastOptions={{
            style: {
              fontFamily: 'Inter, sans-serif',
              fontSize: '14px',
              borderRadius: '12px',
              boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
            },
            success: { iconTheme: { primary: '#2E7D32', secondary: '#fff' } },
            error:   { iconTheme: { primary: '#C62828', secondary: '#fff' } },
          }}
        />
      </BrowserRouter>
    </AuthProvider>
  )
}
