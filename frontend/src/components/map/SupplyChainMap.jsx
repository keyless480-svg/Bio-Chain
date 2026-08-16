// components/map/SupplyChainMap.jsx — Interactive Leaflet map for supply chain nodes & routes
import { useEffect, useRef } from 'react'
import L from 'leaflet'

// Fix Leaflet default icon path (Vite/Webpack known issue)
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl:       'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl:     'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

// Custom colored circle markers
const createCircleMarker = (color, radius = 10) => L.divIcon({
  className: '',
  html: `<div style="
    width:${radius*2}px; height:${radius*2}px;
    border-radius:50%;
    background:${color};
    border:3px solid white;
    box-shadow:0 2px 8px rgba(0,0,0,0.4);
  "></div>`,
  iconSize:   [radius*2, radius*2],
  iconAnchor: [radius, radius],
})

const NODE_COLORS = {
  farm:        '#4CAF50',    // Hijau — farm
  hub:         '#FFC107',    // Kuning — KUD hub
  biorefinery: '#5D4037',    // Coklat — biorefinery
}

// Jawa Timur center
const JATIM_CENTER = [-7.5, 112.8]

export default function SupplyChainMap({ nodes, routes, openHubs = [] }) {
  const mapRef    = useRef(null)
  const mapInst   = useRef(null)
  const layersRef = useRef([])

  // Initialize map once
  useEffect(() => {
    if (mapInst.current) return
    mapInst.current = L.map(mapRef.current, {
      center: JATIM_CENTER,
      zoom: 8,
      zoomControl: true,
      attributionControl: true,
    })

    // Tile layer — CartoDB Light (clean, minimal)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      attribution: '© OpenStreetMap © CARTO',
      maxZoom: 18,
    }).addTo(mapInst.current)

    // Jawa Timur boundary (approximate bounding box as rectangle)
    L.rectangle([[-8.8, 110.0], [-6.8, 115.5]], {
      color: '#2E7D32', weight: 2, fill: false, dashArray: '6 4', opacity: 0.5,
    }).addTo(mapInst.current)

    return () => {
      if (mapInst.current) {
        mapInst.current.remove()
        mapInst.current = null
      }
    }
  }, [])

  // Draw nodes and routes whenever data changes
  useEffect(() => {
    if (!mapInst.current) return
    const map = mapInst.current

    // Clear old layers
    layersRef.current.forEach(l => map.removeLayer(l))
    layersRef.current = []

    const addLayer = (l) => { l.addTo(map); layersRef.current.push(l) }

    if (!nodes) return

    // Draw route polylines first (under markers)
    if (routes?.length) {
      // Build node ID → coordinates lookup
      const nodeCoords = {}
      nodes.farms?.forEach(f => { nodeCoords[`farm_${f.id}`] = [f.latitude, f.longitude] })
      nodes.hubs?.forEach(h => { nodeCoords[`hub_${h.id}`] = [h.latitude, h.longitude] })
      nodes.biorefineries?.forEach(b => { nodeCoords[`biorefinery_${b.id}`] = [b.latitude, b.longitude] })

      routes.forEach(route => {
        const fromKey = `${route.from_type}_${route.from_id}`
        const toKey   = `${route.to_type}_${route.to_id}`
        const from = nodeCoords[fromKey]
        const to   = nodeCoords[toKey]
        if (!from || !to) return

        const color = route.from_type === 'farm' ? '#81C784' : '#5D4037'
        const weight = Math.max(2, Math.min(8, route.flow_ton_day / 20))

        const line = L.polyline([from, to], {
          color, weight, opacity: 0.75, dashArray: route.from_type === 'farm' ? '8 4' : null,
        })
        line.bindTooltip(
          `<b>${route.from_type === 'farm' ? 'Farm→Hub' : 'Hub→Biorefinery'}</b><br/>
           Aliran: ${route.flow_ton_day.toFixed(1)} ton/hari<br/>
           Jarak: ${route.distance_km.toFixed(0)} km<br/>
           Biaya: $${route.cost_usd_day.toFixed(2)}/hari`,
          { sticky: true }
        )
        addLayer(line)
      })
    }

    // Draw Farm markers
    nodes.farms?.forEach(farm => {
      const m = L.marker([farm.latitude, farm.longitude], {
        icon: createCircleMarker(NODE_COLORS.farm, 9),
      })
      m.bindPopup(`
        <div style="font-family:Inter,sans-serif;min-width:180px">
          <div style="font-weight:700;color:#2E7D32;margin-bottom:4px">🌽 ${farm.name}</div>
          <div style="font-size:12px;color:#555">
            📍 ${farm.kabupaten}<br/>
            Pasokan: <b>${farm.daily_supply_ton.toFixed(1)} ton/hari</b><br/>
            Luas: ${farm.corn_area_ha?.toLocaleString() || '-'} ha
          </div>
        </div>
      `)
      addLayer(m)
    })

    // Draw Hub markers (highlight open hubs from optimization)
    nodes.hubs?.forEach(hub => {
      const isOpen = openHubs.includes(hub.id)
      const color  = isOpen ? '#FFC107' : '#BDBDBD'
      const size   = isOpen ? 13 : 9
      const m = L.marker([hub.latitude, hub.longitude], {
        icon: createCircleMarker(color, size),
        zIndexOffset: isOpen ? 500 : 0,
      })
      m.bindPopup(`
        <div style="font-family:Inter,sans-serif;min-width:180px">
          <div style="font-weight:700;color:#F57F17;margin-bottom:4px">🏭 ${hub.name}</div>
          <div style="font-size:12px;color:#555">
            📍 ${hub.kabupaten}<br/>
            Kapasitas: <b>${hub.max_capacity_ton_day} ton/hari</b><br/>
            Beban: ${hub.current_load_ton.toFixed(1)} ton<br/>
            Status: <b style="color:${isOpen ? '#2E7D32' : '#999'}">${isOpen ? '✅ Aktif (Optimal)' : '⭕ Tidak dipilih'}</b>
          </div>
        </div>
      `)
      addLayer(m)
    })

    // Draw Biorefinery markers
    nodes.biorefineries?.forEach(bio => {
      const m = L.marker([bio.latitude, bio.longitude], {
        icon: createCircleMarker(NODE_COLORS.biorefinery, 15),
        zIndexOffset: 1000,
      })
      m.bindPopup(`
        <div style="font-family:Inter,sans-serif;min-width:200px">
          <div style="font-weight:700;color:#5D4037;margin-bottom:4px">⚗️ ${bio.name}</div>
          <div style="font-size:12px;color:#555">
            📍 ${bio.kabupaten}<br/>
            Kapasitas: <b>${bio.max_capacity_ton_day} ton/hari</b><br/>
            Yield Etanol: ${bio.ethanol_yield_liter_per_ton} L/ton
          </div>
        </div>
      `)
      addLayer(m)
    })

    // Legend
    const legend = L.control({ position: 'bottomright' })
    legend.onAdd = () => {
      const div = L.DomUtil.create('div')
      div.style.cssText = 'background:white;padding:12px 16px;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,0.15);font-family:Inter,sans-serif;font-size:13px;'
      div.innerHTML = `
        <b style="color:#2E7D32;display:block;margin-bottom:8px">Legenda</b>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px">
          <div style="width:14px;height:14px;border-radius:50%;background:#4CAF50;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,0.3)"></div>
          Lahan Jagung (Farm)
        </div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px">
          <div style="width:14px;height:14px;border-radius:50%;background:#FFC107;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,0.3)"></div>
          Gudang KUD (Hub)
        </div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px">
          <div style="width:14px;height:14px;border-radius:50%;background:#5D4037;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,0.3)"></div>
          Pabrik Bioetanol
        </div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px">
          <div style="width:30px;height:3px;background:#81C784;border-radius:2px;"></div>
          Rute Farm→Hub
        </div>
        <div style="display:flex;align-items:center;gap:8px">
          <div style="width:30px;height:3px;background:#5D4037;border-radius:2px;"></div>
          Rute Hub→Pabrik
        </div>
      `
      return div
    }
    legend.addTo(map)
    layersRef.current.push(legend)

  }, [nodes, routes, openHubs])

  return (
    <div style={{ width: '100%', height: '100%', minHeight: 450 }}>
      <div ref={mapRef} style={{ width: '100%', height: '100%', borderRadius: 'var(--radius-xl)' }} />
    </div>
  )
}
