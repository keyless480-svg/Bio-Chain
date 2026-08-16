// components/layout/Header.jsx
import { useAuth } from '../../context/AuthContext'
import { LogOut, Leaf, Bell } from 'lucide-react'

const ROLE_LABELS = {
  analyst:   'Analis Kebijakan',
  farmer:    'Petani Jagung',
  collector: 'Petugas KUD',
  driver:    'Sopir Truk',
}

const ROLE_BADGE_CLASS = {
  analyst:   'badge-green',
  farmer:    'badge-brown',
  collector: 'badge-yellow',
  driver:    'badge-blue',
}

export default function Header({ title = 'BioChain-Opt' }) {
  const { user, logout } = useAuth()

  return (
    <header className="header">
      <div className="flex items-center gap-3">
        <Leaf size={24} color="var(--color-primary-700)" />
        <div>
          <h1 style={{
            fontFamily: 'var(--font-display)',
            fontSize: 'var(--text-xl)',
            fontWeight: 800,
            color: 'var(--color-primary-800)',
            lineHeight: 1.1,
          }}>
            {title}
          </h1>
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-gray-500)' }}>
            Rantai Pasok Bioetanol Jawa Timur
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {user && (
          <>
            <span className={`badge ${ROLE_BADGE_CLASS[user.role] || 'badge-green'}`}>
              {ROLE_LABELS[user.role] || user.role}
            </span>
            <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-gray-700)', fontWeight: 600 }}>
              {user.full_name || user.username}
            </span>
            {user.kabupaten && (
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-gray-400)' }}>
                📍 {user.kabupaten}
              </span>
            )}
            <button
              className="btn btn-ghost btn-sm"
              onClick={logout}
              title="Keluar"
            >
              <LogOut size={16} />
              Keluar
            </button>
          </>
        )}
      </div>
    </header>
  )
}
