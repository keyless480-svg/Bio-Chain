// pages/driver/DriverPage.jsx — Truck driver route and task management
import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../../context/AuthContext'
import { CheckCircle, Circle, Navigation, MapPin, Package, LogOut, ChevronDown, ChevronUp } from 'lucide-react'
import L from 'leaflet'
import toast from 'react-hot-toast'

// Simulated route tasks assigned to this driver
const INITIAL_TASKS = [
  {
    id: 1,
    status: 'active',   // active | loading | done
    type: 'pickup',
    label: 'Ambil Muatan',
    location: 'KUD Pantura Hub — Tuban',
    address: 'Jl. Raya Tuban-Bojonegoro KM 12, Tuban',
    payload: '5 Ton Tongkol Jagung',
    eta: '25 Menit',
    lat: -6.885, lon: 111.900,
    icon: '🏭',
  },
  {
    id: 2,
    status: 'pending',
    type: 'dropoff',
    label: 'Antar ke Pabrik',
    location: 'Biorefinery Gresik — Kawasan Industri',
    address: 'Jl. Industri Gresik, Gresik',
    payload: '5 Ton → Proses Bioetanol',
    eta: '1 Jam 45 Menit',
    lat: -7.161, lon: 112.656,
    icon: '⚗️',
  },
]

// Jawa Timur center
const MAP_CENTER = [-7.2, 112.2]

export default function DriverPage() {
  const { user, logout } = useAuth()
  const mapRef      = useRef(null)
  const mapInst     = useRef(null)
  const [tasks, setTasks]       = useState(INITIAL_TASKS)
  const [expanded, setExpanded] = useState(1)  // expanded task id

  const activeTask   = tasks.find(t => t.status === 'active')
  const completedAll = tasks.every(t => t.status === 'done')

  // Init Leaflet map
  useEffect(() => {
    if (mapInst.current) return
    if (!mapRef.current) return

    mapInst.current = L.map(mapRef.current, {
      center: MAP_CENTER, zoom: 9, zoomControl: false,
    })

    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      attribution: '© OpenStreetMap © CARTO', maxZoom: 18,
    }).addTo(mapInst.current)

    // Draw truck route polyline
    const routeCoords = INITIAL_TASKS.map(t => [t.lat, t.lon])
    L.polyline(routeCoords, { color: '#2E7D32', weight: 5, opacity: 0.85, dashArray: '10 6' })
      .addTo(mapInst.current)

    // Task markers
    INITIAL_TASKS.forEach((task, i) => {
      const icon = L.divIcon({
        className: '',
        html: `<div style="
          width:36px; height:36px;
          border-radius:50%;
          background:${task.type === 'pickup' ? '#FFC107' : '#5D4037'};
          border:3px solid white;
          box-shadow:0 3px 10px rgba(0,0,0,0.4);
          display:flex; align-items:center; justify-content:center;
          font-size:16px;
        ">${task.icon}</div>`,
        iconSize: [36, 36], iconAnchor: [18, 18],
      })
      L.marker([task.lat, task.lon], { icon })
        .bindTooltip(task.location, { permanent: false })
        .addTo(mapInst.current)
    })

    // Driver truck marker (starts at midpoint)
    const truckIcon = L.divIcon({
      className: '',
      html: `<div style="
        width:44px; height:44px;
        border-radius:50%;
        background:linear-gradient(135deg,#2E7D32,#1B5E20);
        border:4px solid white;
        box-shadow:0 4px 16px rgba(46,125,50,0.5);
        display:flex; align-items:center; justify-content:center;
        font-size:22px;
        animation: pulse 1.5s infinite;
      ">🚛</div>`,
      iconSize: [44, 44], iconAnchor: [22, 22],
    })
    L.marker([-7.05, 111.95], { icon: truckIcon })
      .bindPopup('<b>Posisi Truk Anda</b><br/>Sedang dalam perjalanan')
      .addTo(mapInst.current)

    return () => {
      if (mapInst.current) { mapInst.current.remove(); mapInst.current = null }
    }
  }, [])

  const handleTaskAction = (taskId, action) => {
    setTasks(prev => {
      const updated = [...prev]
      const idx = updated.findIndex(t => t.id === taskId)
      if (idx === -1) return prev

      if (action === 'loading') {
        updated[idx] = { ...updated[idx], status: 'loading' }
        toast('⏳ Sedang memuat barang...', { duration: 1500 })
        setTimeout(() => {
          setTasks(prev2 => {
            const u2 = [...prev2]
            u2[idx] = { ...u2[idx], status: 'done' }
            // Activate next task
            if (idx + 1 < u2.length) u2[idx + 1] = { ...u2[idx + 1], status: 'active' }
            return u2
          })
          setExpanded(updated[idx + 1]?.id || null)
          toast.success('✅ Barang sudah dimuat! Lanjut ke tujuan berikutnya.')
        }, 2000)
      } else if (action === 'dropoff') {
        updated[idx] = { ...updated[idx], status: 'loading' }
        toast('⏳ Mengkonfirmasi pengiriman...', { duration: 1500 })
        setTimeout(() => {
          setTasks(prev2 => {
            const u2 = [...prev2]
            u2[idx] = { ...u2[idx], status: 'done' }
            return u2
          })
          toast.success('🎉 Pengiriman selesai! Terima kasih atas kerja kerasmu.')
        }, 2000)
      }

      return updated
    })
  }

  const statusColors = { active: '#4CAF50', pending: '#BDBDBD', done: '#9E9E9E', loading: '#FFC107' }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--color-gray-100)' }}>
      {/* Header */}
      <header style={{
        background: 'linear-gradient(135deg, var(--color-primary-800), var(--color-primary-900))',
        padding: 'var(--space-3) var(--space-5)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        zIndex: 200, position: 'relative',
        boxShadow: 'var(--shadow-lg)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 24 }}>🚛</span>
          <div>
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, color: 'white', fontSize: 'var(--text-lg)' }}>
              Rute Pengiriman
            </div>
            <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: 'var(--text-xs)' }}>
              {user?.full_name || 'Sopir Truk'} • BioChain Logistik
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {activeTask && (
            <div style={{
              background: 'rgba(76,175,80,0.2)', borderRadius: 8, padding: '4px 10px',
              display: 'flex', alignItems: 'center', gap: 6,
            }}>
              <span className="status-dot running" />
              <span style={{ color: '#A5D6A7', fontSize: 'var(--text-xs)', fontWeight: 700 }}>Dalam Perjalanan</span>
            </div>
          )}
          <button onClick={logout} style={{ background: 'rgba(255,255,255,0.15)', border: 'none', color: 'white', padding: '6px 12px', borderRadius: 8, cursor: 'pointer', fontSize: 'var(--text-sm)', display: 'flex', alignItems: 'center', gap: 4 }}>
            <LogOut size={14} /> Keluar
          </button>
        </div>
      </header>

      {/* Map — fullscreen feel */}
      <div style={{ position: 'relative', height: '45vh', minHeight: 280 }}>
        <div ref={mapRef} style={{ width: '100%', height: '100%' }} />
        {/* Navigation overlay */}
        <div style={{
          position: 'absolute', top: 12, left: 12, right: 12,
          background: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(8px)',
          borderRadius: 'var(--radius-xl)', padding: 'var(--space-3) var(--space-4)',
          boxShadow: 'var(--shadow-xl)',
          display: 'flex', alignItems: 'center', gap: 10,
        }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: '#E8F5E9', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Navigation size={22} color="var(--color-primary-700)" />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 700, fontSize: 'var(--text-sm)', color: 'var(--color-gray-800)' }}>
              {activeTask ? activeTask.location : completedAll ? 'Semua tugas selesai! 🎉' : 'Menunggu tugas...'}
            </div>
            {activeTask && (
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-gray-500)' }}>
                📍 {activeTask.address}
              </div>
            )}
          </div>
          {activeTask && (
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-gray-400)' }}>ETA</div>
              <div style={{ fontWeight: 800, fontSize: 'var(--text-lg)', color: 'var(--color-primary-800)' }}>
                {activeTask.eta}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Task Cards */}
      <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
        <h3 style={{ fontWeight: 700, color: 'var(--color-gray-700)', fontSize: 'var(--text-base)', display: 'flex', alignItems: 'center', gap: 8 }}>
          📋 Daftar Tugas Hari Ini
          <span style={{ fontSize: 'var(--text-xs)', fontWeight: 400, color: 'var(--color-gray-400)' }}>
            {tasks.filter(t => t.status === 'done').length}/{tasks.length} selesai
          </span>
        </h3>

        {tasks.map((task) => (
          <div
            key={task.id}
            className={`task-card ${task.status}`}
            style={{
              borderLeftColor: statusColors[task.status],
              opacity: task.status === 'done' ? 0.65 : 1,
            }}
          >
            {/* Task header */}
            <button
              onClick={() => setExpanded(expanded === task.id ? null : task.id)}
              style={{ width: '100%', background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 12, textAlign: 'left', padding: 0 }}
            >
              {/* Status icon */}
              <div style={{
                width: 36, height: 36, borderRadius: '50%', flexShrink: 0,
                background: task.status === 'done' ? '#E0E0E0' : task.status === 'loading' ? '#FFF9C4' : '#E8F5E9',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 18,
              }}>
                {task.status === 'done' ? '✅' : task.status === 'loading' ? '⏳' : task.icon}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 700, color: task.status === 'done' ? 'var(--color-gray-500)' : 'var(--color-gray-800)', fontSize: 'var(--text-base)' }}>
                  Tugas {task.id}: {task.label}
                </div>
                <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-gray-500)', marginTop: 2 }}>
                  {task.location}
                </div>
              </div>
              {task.status === 'active' && (
                <span className="badge badge-green" style={{ flexShrink: 0 }}>AKTIF</span>
              )}
              {task.status === 'done' && (
                <span className="badge" style={{ background: '#E0E0E0', color: '#757575', flexShrink: 0 }}>Selesai</span>
              )}
              {task.status === 'pending' && (
                <span className="badge badge-blue" style={{ flexShrink: 0 }}>Menunggu</span>
              )}
              {expanded === task.id ? <ChevronUp size={16} color="var(--color-gray-400)" /> : <ChevronDown size={16} color="var(--color-gray-400)" />}
            </button>

            {/* Task detail (expandable) */}
            {expanded === task.id && (
              <div className="fade-in" style={{ marginTop: 'var(--space-4)', paddingTop: 'var(--space-4)', borderTop: '1px solid var(--color-gray-100)' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                    <MapPin size={16} color="var(--color-gray-400)" style={{ flexShrink: 0, marginTop: 2 }} />
                    <div>
                      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-gray-400)' }}>Alamat</div>
                      <div style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--color-gray-700)' }}>{task.address}</div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                    <Package size={16} color="var(--color-gray-400)" style={{ flexShrink: 0, marginTop: 2 }} />
                    <div>
                      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-gray-400)' }}>Muatan</div>
                      <div style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--color-gray-700)' }}>{task.payload}</div>
                    </div>
                  </div>
                </div>

                {task.status === 'active' && (
                  <button
                    className="btn btn-primary btn-full"
                    onClick={() => handleTaskAction(task.id, task.type === 'pickup' ? 'loading' : 'dropoff')}
                    style={{ fontSize: 'var(--text-lg)', fontWeight: 800, padding: 'var(--space-4)', borderRadius: 'var(--radius-xl)' }}
                  >
                    {task.type === 'pickup'
                      ? <><Package size={20} /> Barang Sudah Dimuat</>
                      : <><CheckCircle size={20} /> Selesai Antar ✅</>
                    }
                  </button>
                )}

                {task.status === 'loading' && (
                  <div style={{ textAlign: 'center', padding: 'var(--space-3)', color: 'var(--color-gray-500)' }}>
                    <div className="spinner" style={{ margin: '0 auto 8px' }} />
                    Memproses konfirmasi...
                  </div>
                )}

                {task.status === 'pending' && (
                  <div style={{
                    background: 'var(--color-gray-100)', borderRadius: 'var(--radius-lg)',
                    padding: 'var(--space-3)', textAlign: 'center', color: 'var(--color-gray-500)', fontSize: 'var(--text-sm)',
                  }}>
                    ⏳ Selesaikan tugas sebelumnya terlebih dahulu
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {/* Completion screen */}
        {completedAll && (
          <div className="card fade-in" style={{
            background: 'linear-gradient(135deg, #E8F5E9, #C8E6C9)',
            border: '2px solid #A5D6A7', textAlign: 'center', padding: 'var(--space-8)',
          }}>
            <div style={{ fontSize: 64, marginBottom: 12 }}>🎉</div>
            <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 900, fontSize: 'var(--text-2xl)', color: 'var(--color-primary-800)', marginBottom: 8 }}>
              Semua Tugas Selesai!
            </h2>
            <p style={{ color: 'var(--color-gray-600)' }}>
              Kamu telah berkontribusi pada rantai pasok bioetanol hijau Indonesia 🌿
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
