"""
models/transactions.py — Transactional ORM models for the 5-Step Circular Flow.
Provides full audit trail for harvests, hub batches, shipments, factory HPP, and circularity.
All monetary values in IDR (Rupiah).
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, Date, JSON
from sqlalchemy.sql import func
from src.database import Base


class Harvest(Base):
    """
    Langkah 1 — Record output petani.
    Mencatat setiap pengiriman panen dari petani.
    """
    __tablename__ = "harvests"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, nullable=False, index=True)
    # Measurement
    gross_weight_kg = Column(Float, nullable=False)
    initial_moisture_pct = Column(Float, nullable=False)  # 35-40%
    net_dry_weight_kg = Column(Float, nullable=True)  # Calculated after drying
    # Location
    geo_lat = Column(Float, nullable=True)
    geo_long = Column(Float, nullable=True)
    # Cost (IDR)
    harvest_cost = Column(Float, default=0.0)
    packing_cost = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    price_per_kg = Column(Float, default=850.0)  # Rp/kg harga beli
    total_payment = Column(Float, default=0.0)   # Rp total dibayar ke petani
    # Metadata
    harvest_date = Column(Date, nullable=False)
    destination_hub_id = Column(Integer, nullable=True)
    status = Column(String(30), default="recorded")  # recorded|delivered|verified
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, nullable=True)  # user_id


class HubBatch(Base):
    """
    Langkah 2 — Agregasi di Pengepul.
    Mencatat batch masuk, proses pengeringan, dan shrinkage.
    """
    __tablename__ = "hub_batches"

    id = Column(Integer, primary_key=True, index=True)
    hub_id = Column(Integer, nullable=False, index=True)
    batch_code = Column(String(50), unique=True, index=True)
    # Input
    total_input_kg = Column(Float, nullable=False)
    input_moisture_pct = Column(Float, nullable=False)
    num_farmers = Column(Integer, default=1)
    # Output (after drying/shrinkage)
    final_weight_kg = Column(Float, nullable=True)
    final_moisture_pct = Column(Float, nullable=True)
    shrinkage_kg = Column(Float, nullable=True)  # Weight lost (water)
    shrinkage_pct = Column(Float, nullable=True)  # % lost
    # ABC Costs (IDR)
    loading_cost = Column(Float, default=0.0)     # Bongkar muat
    drying_cost = Column(Float, default=0.0)      # Energi pengeringan
    storage_cost = Column(Float, default=0.0)     # Sewa gudang
    shrinkage_cost = Column(Float, default=0.0)   # "Biaya hantu" penyusutan
    total_handling_cost = Column(Float, default=0.0)
    # Quality
    quality_grade = Column(String(10), default="A")  # A|B|C
    iot_sensor_id = Column(String(50), nullable=True)  # IoT moisture sensor
    # Status
    status = Column(String(30), default="received")  # received|drying|ready|shipped
    batch_date = Column(Date, nullable=False)
    ready_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, nullable=True)


class Shipment(Base):
    """
    Langkah 3 — Transportasi & Logistik (Green Routing).
    Mencatat pengiriman FTL dari Pengepul ke Pabrik.
    """
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    hub_batch_id = Column(Integer, nullable=False, index=True)
    hub_id = Column(Integer, nullable=False, index=True)
    factory_id = Column(Integer, nullable=False)
    # Truck info
    truck_plate = Column(String(20), nullable=False)
    driver_name = Column(String(100), nullable=True)
    driver_user_id = Column(Integer, nullable=True)
    truck_capacity_ton = Column(Float, default=20.0)
    payload_ton = Column(Float, nullable=False)
    truck_utilization_pct = Column(Float, nullable=True)  # Must be >95%
    # Route
    distance_km = Column(Float, nullable=False)
    estimated_duration_hours = Column(Float, nullable=True)
    # ABC Costs (IDR)
    fuel_cost = Column(Float, default=0.0)        # BBM (jarak × konsumsi × harga solar)
    toll_cost = Column(Float, default=0.0)        # Biaya tol
    driver_cost = Column(Float, default=0.0)      # Upah + uang makan
    maintenance_cost = Column(Float, default=0.0)  # Perawatan truk prorata
    total_transport_cost = Column(Float, default=0.0)
    # ESG / Green
    carbon_emitted_kg = Column(Float, default=0.0)  # kg CO₂
    carbon_tax_cost = Column(Float, default=0.0)    # Pajak karbon internal (IDR)
    emission_factor = Column(Float, default=2.68)   # kg CO₂ / liter solar
    # Status
    status = Column(String(30), default="dispatched")  # dispatched|in_transit|delivered|verified
    departure_time = Column(DateTime(timezone=True), nullable=True)
    arrival_time = Column(DateTime(timezone=True), nullable=True)
    shipment_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, nullable=True)


class FactoryHppLog(Base):
    """
    Langkah 4 — Kalkulasi HPP & Fair Trade di Pabrik.
    Log penerimaan dan penghitungan Harga Pokok Penjualan.
    """
    __tablename__ = "factory_hpp_logs"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, nullable=False, index=True)
    factory_id = Column(Integer, nullable=False)
    # Weighbridge measurement
    net_weight_received_kg = Column(Float, nullable=False)
    weight_difference_kg = Column(Float, nullable=True)  # Selisih dari shipment
    # Cost accumulation (IDR)
    acquisition_cost = Column(Float, default=0.0)     # Total dibayar ke pengepul+petani
    transport_cost = Column(Float, default=0.0)       # Total biaya transport
    processing_cost = Column(Float, default=0.0)      # Biaya pabrikasi (listrik, overhead)
    depreciation_cost = Column(Float, default=0.0)    # Depresiasi mesin
    total_cost = Column(Float, default=0.0)           # HPP total
    # HPP Calculation
    total_hpp_per_kg = Column(Float, default=0.0)     # Rp/kg
    ethanol_produced_liter = Column(Float, nullable=True)
    hpp_per_liter_ethanol = Column(Float, nullable=True)  # Rp/liter etanol
    # Fair Trade
    farmer_share_pct = Column(Float, nullable=True)   # % margin petani dari HPP
    hub_share_pct = Column(Float, nullable=True)      # % margin pengepul
    # Metadata
    received_date = Column(Date, nullable=False)
    quality_sample_result = Column(String(50), nullable=True)  # pass|fail|conditional
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, nullable=True)


class CircularityLog(Base):
    """
    Langkah 5 — Waste to Value (Circular Economy).
    Mencatat reverse logistics: pupuk/kompos dari limbah pabrik kembali ke petani.
    """
    __tablename__ = "circularity_logs"

    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(String(20), nullable=False)  # factory|hub
    source_id = Column(Integer, nullable=False)
    destination_farmer_id = Column(Integer, nullable=False)
    # Product
    product_type = Column(String(50), nullable=False)  # pupuk_silika|karbon_aktif|kompos
    quantity_kg = Column(Float, nullable=False)
    # Cost saving (IDR)
    production_cost = Column(Float, default=0.0)       # Biaya pembuatan pupuk
    market_value = Column(Float, default=0.0)          # Nilai pupuk di pasar
    farmer_saving = Column(Float, default=0.0)         # Penghematan petani
    # Reverse logistics
    truck_plate = Column(String(20), nullable=True)    # Truk kosong (backhaul)
    transport_cost = Column(Float, default=0.0)        # Biaya reverse logistics (rendah/gratis)
    is_backhaul = Column(Boolean, default=True)        # True = truk kembali kosong
    # Metadata
    delivery_date = Column(Date, nullable=False)
    status = Column(String(30), default="produced")    # produced|shipped|received
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, nullable=True)
