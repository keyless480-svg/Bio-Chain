import React from 'react';
import { Truck, Factory, Warehouse, Sprout, Recycle, ArrowRight } from 'lucide-react';

export default function CircularFlow() {
  const steps = [
    { 
      id: 1, 
      name: 'Hulu: 10 Petani', 
      icon: Sprout, 
      desc: 'Panen, pemisahan kasar, penjemuran pasif.',
      cost: 'Rp/ton panen & karung goni'
    },
    { 
      id: 2, 
      name: 'Konsolidasi: 5 Pengepul', 
      icon: Warehouse, 
      desc: 'Cross-docking, pengeringan, QC.',
      cost: 'Bongkar muat, energi, gudang'
    },
    { 
      id: 3, 
      name: 'Logistik FTL', 
      icon: Truck, 
      desc: 'Utilisasi >95%, green routing.',
      cost: 'BBM, tol, supir, pajak emisi'
    },
    { 
      id: 4, 
      name: 'Hilir: Pabrik Sentral', 
      icon: Factory, 
      desc: 'Ekstraksi bioetanol & fair trade.',
      cost: 'Proses pabrikasi, HPP/kg'
    },
    { 
      id: 5, 
      name: 'Sirkularitas', 
      icon: Recycle, 
      desc: 'Pupuk dikirim balik via backhaul.',
      cost: 'Subsidi silang (cost saving)'
    }
  ];

  return (
    <div className="card">
      <h3 style={{ fontSize: 'var(--text-lg)', fontWeight: 700, marginBottom: 'var(--space-6)', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Recycle size={20} color="var(--color-primary-600)" />
        Arsitektur 5-Step Circular Flow
      </h3>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {steps.map((step, index) => {
          const Icon = step.icon;
          return (
            <div key={step.id} style={{ display: 'flex', alignItems: 'flex-start', gap: '16px' }}>
              <div style={{
                width: 48, height: 48, borderRadius: '50%',
                background: index === 4 ? 'var(--color-accent-100)' : 'var(--color-primary-50)',
                color: index === 4 ? 'var(--color-accent-600)' : 'var(--color-primary-700)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0,
                border: index === 4 ? '2px solid var(--color-accent-200)' : '2px solid var(--color-primary-200)'
              }}>
                <Icon size={24} />
              </div>
              <div style={{ flex: 1, paddingBottom: index < steps.length - 1 ? '16px' : '0', borderBottom: index < steps.length - 1 ? '1px dashed var(--color-gray-200)' : 'none' }}>
                <h4 style={{ fontSize: 'var(--text-base)', fontWeight: 700, color: 'var(--color-gray-800)', marginBottom: '4px' }}>
                  Langkah {step.id}: {step.name}
                </h4>
                <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-gray-600)', marginBottom: '4px' }}>
                  {step.desc}
                </p>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: 'var(--text-xs)', color: 'var(--color-gray-500)', fontWeight: 600 }}>
                  <span style={{ padding: '2px 6px', background: 'var(--color-gray-100)', borderRadius: '4px' }}>
                    ABC Cost: {step.cost}
                  </span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  );
}
