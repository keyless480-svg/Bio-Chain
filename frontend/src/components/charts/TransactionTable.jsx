import React, { useState, useEffect } from 'react';
import { transactionApi } from '../../api/client';
import { Table, ArrowDownRight, ArrowUpRight, Truck, Package, Droplets } from 'lucide-react';

export default function TransactionTable() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    transactionApi.getDailySummary()
      .then(res => {
        setSummary(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="card" style={{ textAlign: 'center', padding: '40px' }}><div className="spinner"></div></div>;
  if (!summary) return <div className="card">Gagal memuat data transaksi.</div>;

  return (
    <div className="card">
      <h3 style={{ fontSize: 'var(--text-lg)', fontWeight: 700, marginBottom: 'var(--space-6)', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Table size={20} color="var(--color-primary-600)" />
        Ringkasan Transaksi Harian ({summary.date})
      </h3>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        {/* Harvests */}
        <div style={{ background: 'var(--color-gray-50)', padding: '16px', borderRadius: '8px', border: '1px solid var(--color-gray-200)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: 'var(--color-gray-600)' }}>
            <ArrowDownRight size={16} /> <span style={{ fontWeight: 600, fontSize: 'var(--text-sm)' }}>Panen Masuk (Petani)</span>
          </div>
          <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 800, color: 'var(--color-gray-900)' }}>
            {summary.harvests.count} <span style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--color-gray-500)' }}>trx</span>
          </div>
          <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-gray-600)', marginTop: '4px' }}>
            Total: <strong>{(summary.harvests.total_weight_kg / 1000).toFixed(1)} ton</strong>
          </div>
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-gray-500)', marginTop: '2px' }}>
            Pembayaran: Rp {(summary.harvests.total_payment / 1000000).toFixed(2)} Juta
          </div>
        </div>

        {/* Hub Batches */}
        <div style={{ background: 'var(--color-gray-50)', padding: '16px', borderRadius: '8px', border: '1px solid var(--color-gray-200)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: 'var(--color-gray-600)' }}>
            <Package size={16} /> <span style={{ fontWeight: 600, fontSize: 'var(--text-sm)' }}>Batch Pengepul</span>
          </div>
          <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 800, color: 'var(--color-gray-900)' }}>
            {summary.hub_batches.count} <span style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--color-gray-500)' }}>batch</span>
          </div>
          <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-gray-600)', marginTop: '4px' }}>
            Input: <strong>{(summary.hub_batches.total_input_kg / 1000).toFixed(1)} ton</strong>
          </div>
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-red-600)', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Droplets size={12} /> Shrinkage: {(summary.hub_batches.total_shrinkage_kg / 1000).toFixed(1)} ton
          </div>
        </div>

        {/* Shipments */}
        <div style={{ background: 'var(--color-gray-50)', padding: '16px', borderRadius: '8px', border: '1px solid var(--color-gray-200)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: 'var(--color-gray-600)' }}>
            <Truck size={16} /> <span style={{ fontWeight: 600, fontSize: 'var(--text-sm)' }}>Pengiriman FTL</span>
          </div>
          <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 800, color: 'var(--color-gray-900)' }}>
            {summary.shipments.count} <span style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--color-gray-500)' }}>truk</span>
          </div>
          <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-gray-600)', marginTop: '4px' }}>
            Muatan: <strong>{summary.shipments.total_payload_ton.toFixed(1)} ton</strong>
          </div>
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-gray-500)', marginTop: '2px' }}>
            Emisi: {summary.shipments.total_carbon_emitted_kg.toFixed(1)} kg CO₂
          </div>
        </div>
      </div>
      
      <div style={{ marginTop: '16px', fontSize: 'var(--text-xs)', color: 'var(--color-gray-500)', textAlign: 'center' }}>
        *Data ditarik secara realtime dari database operasional.
      </div>
    </div>
  );
}
