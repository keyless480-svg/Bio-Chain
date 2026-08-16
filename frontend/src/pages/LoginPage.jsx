// pages/LoginPage.jsx — Role-based login with credential form
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import { Leaf, Lock, User, Eye, EyeOff, Settings } from 'lucide-react'

const ROLES = [
  { key: 'analyst',   icon: '📊', title: 'Analis / Pemerintah', desc: 'ESDM, Kementan, Investor', demo: { u: 'analis_esdm', p: 'biochain2026' } },
  { key: 'farmer',    icon: '🌽', title: 'Petani Jagung',        desc: 'Penjual tongkol jagung',  demo: { u: 'petani_tuban', p: 'jagung123' } },
  { key: 'collector', icon: '🏭', title: 'Pengepul / KUD',       desc: 'Petugas Gudang KUD',      demo: { u: 'pengepul_kud', p: 'kud2026' } },
  { key: 'driver',    icon: '🚛', title: 'Sopir Truk',           desc: 'Petugas Logistik',        demo: { u: 'sopir_truk', p: 'truk2026' } },
]

const ROLE_ROUTES = {
  analyst:   '/analyst',
  farmer:    '/farmer',
  collector: '/collector',
  driver:    '/driver',
}

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [selectedRole, setSelectedRole] = useState(null)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [customApiUrl, setCustomApiUrl] = useState(localStorage.getItem('custom_api_url') || '')

  const handleSaveApiUrl = () => {
    localStorage.setItem('custom_api_url', customApiUrl)
    toast.success('Backend URL tersimpan! Memuat ulang...')
    setTimeout(() => window.location.reload(), 1000)
  }

  const handleRoleSelect = (role) => {
    setSelectedRole(role)
    // Auto-fill demo credentials
    const demo = ROLES.find(r => r.key === role)?.demo
    if (demo) { setUsername(demo.u); setPassword(demo.p) }
  }

  const handleLogin = async (e) => {
    e.preventDefault()
    if (!username || !password) { toast.error('Masukkan username dan password'); return }
    setLoading(true)
    try {
      const user = await login(username, password)
      toast.success(`Selamat datang, ${user.full_name || user.username}!`)
      navigate(ROLE_ROUTES[user.role] || '/analyst')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Login gagal. Periksa kembali kredensial Anda.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      {/* Background decorative circles */}
      <div style={{
        position: 'absolute', width: 400, height: 400,
        background: 'radial-gradient(circle, rgba(255,255,255,0.04) 0%, transparent 70%)',
        bottom: -150, left: -100,
      }} />

      {/* Settings Gear */}
      <button 
        onClick={() => setShowSettings(!showSettings)}
        style={{ position: 'absolute', top: 20, right: 20, background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-gray-400)', zIndex: 10 }}
        title="Pengaturan Koneksi Backend"
      >
        <Settings size={24} />
      </button>

      <div className="login-card">
        {/* Brand */}
        <div style={{ textAlign: 'center', marginBottom: 'var(--space-8)' }}>
          <div style={{
            width: 72, height: 72,
            background: 'linear-gradient(135deg, #66BB6A, #2E7D32)',
            borderRadius: 20,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto var(--space-4)',
            boxShadow: '0 8px 24px rgba(46,125,50,0.3)',
            fontSize: 36,
          }}>🌿</div>
          <h1 style={{
            fontFamily: 'var(--font-display)',
            fontSize: 'var(--text-3xl)',
            fontWeight: 900,
            background: 'linear-gradient(135deg, #2E7D32, #1B5E20)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginBottom: 8,
          }}>BioChain-Opt</h1>
          <p style={{ color: 'var(--color-gray-500)', fontSize: 'var(--text-sm)' }}>
            Sistem Optimasi Rantai Pasok Bioetanol 2G<br/>Jawa Timur
          </p>
        </div>

        {/* Role Selector */}
        <p style={{ fontSize: 'var(--text-sm)', fontWeight: 700, color: 'var(--color-gray-700)', marginBottom: 'var(--space-3)' }}>
          Pilih Peran Anda
        </p>
        <div className="role-grid" style={{ marginBottom: 'var(--space-6)' }}>
          {ROLES.map((role) => (
            <button
              key={role.key}
              className={`role-card ${selectedRole === role.key ? 'selected' : ''}`}
              onClick={() => handleRoleSelect(role.key)}
            >
              <span className="role-icon">{role.icon}</span>
              <span className="role-title">{role.title}</span>
              <span className="role-desc">{role.desc}</span>
            </button>
          ))}
        </div>

        {/* Login Form */}
        <form onSubmit={handleLogin}>
          <div className="input-group" style={{ marginBottom: 'var(--space-4)' }}>
            <label className="input-label">
              <User size={14} style={{ display: 'inline', marginRight: 4 }} />
              Username
            </label>
            <input
              className="input"
              type="text"
              placeholder="Masukkan username"
              value={username}
              onChange={e => setUsername(e.target.value)}
              autoComplete="username"
            />
          </div>

          <div className="input-group" style={{ marginBottom: 'var(--space-6)' }}>
            <label className="input-label">
              <Lock size={14} style={{ display: 'inline', marginRight: 4 }} />
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <input
                className="input"
                type={showPass ? 'text' : 'password'}
                placeholder="Masukkan password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                autoComplete="current-password"
                style={{ paddingRight: 48 }}
              />
              <button
                type="button"
                onClick={() => setShowPass(!showPass)}
                style={{
                  position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-gray-400)',
                }}
              >
                {showPass ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-full btn-lg"
            disabled={loading}
          >
            {loading ? (
              <><div className="spinner" style={{ width: 20, height: 20, borderWidth: 3 }} /> Masuk...</>
            ) : (
              <><Leaf size={20} /> Masuk</>
            )}
          </button>
        </form>

        {/* Demo hint */}
        {selectedRole && (
          <p style={{ marginTop: 'var(--space-4)', fontSize: 'var(--text-xs)', color: 'var(--color-gray-400)', textAlign: 'center' }}>
            💡 Kredensial demo sudah terisi otomatis untuk peran {ROLES.find(r => r.key === selectedRole)?.title}
          </p>
        )}

        <div style={{ marginTop: 'var(--space-8)', borderTop: '1px solid var(--color-gray-200)', paddingTop: 'var(--space-4)', textAlign: 'center' }}>
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-gray-400)' }}>
            Greenovate Challenge 2026 • BioChain-Opt v1.0
          </p>
        </div>

        {showSettings && (
          <div style={{ marginTop: 20, padding: 15, background: '#f8fafc', borderRadius: 8, border: '1px solid #e2e8f0' }}>
            <p style={{ fontSize: '12px', fontWeight: 'bold', marginBottom: 8, color: '#334155' }}>🔧 Kustomisasi URL Backend (Cloudflare/Ngrok)</p>
            <input 
              type="text" 
              value={customApiUrl}
              onChange={(e) => setCustomApiUrl(e.target.value)}
              placeholder="https://xxxxx.trycloudflare.com"
              style={{ width: '100%', padding: '8px', fontSize: '12px', borderRadius: 4, border: '1px solid #cbd5e1', marginBottom: 8 }}
            />
            <button onClick={handleSaveApiUrl} style={{ width: '100%', padding: '8px', background: '#334155', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: '12px' }}>
              Simpan & Muat Ulang
            </button>
            <p style={{ fontSize: '10px', color: '#64748b', marginTop: 8 }}>
              Gunakan fitur ini jika Vercel tidak bisa terhubung. Paste URL dari Cloudflare Tunnel di laptop Anda.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
