"""
routers/transactions.py — API for transactional operations in the 5-Step Flow.
Provides CRUD and business logic for Harvests, HubBatches, Shipments, FactoryHPP, Circularity.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from datetime import date, timedelta
import uuid

from src.database import get_db
from src.models.spatial import Farmer, Hub, Factory
from src.models.transactions import Harvest, HubBatch, Shipment, FactoryHppLog, CircularityLog
from src.schemas.transactions import (
    HarvestCreate, HarvestResponse,
    HubBatchCreate, HubBatchResponse,
    ShipmentCreate, ShipmentResponse,
    FactoryHppCreate, FactoryHppResponse,
    CircularityCreate, CircularityResponse
)
from src.services.spatial_service import full_transport_breakdown, check_truck_utilization
from src.services.ledger_service import append_ledger_entry

router = APIRouter()


@router.post("/harvests", response_model=HarvestResponse, status_code=status.HTTP_201_CREATED)
def create_harvest(harvest: HarvestCreate, db: Session = Depends(get_db)):
    """Petani: Catat hasil panen (Langkah 1)."""
    farmer = db.query(Farmer).filter(Farmer.id == harvest.farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
        
    harvest_cost = (harvest.gross_weight_kg / 1000) * farmer.harvest_cost_per_ton
    packing_cost = (harvest.gross_weight_kg / 1000) * farmer.packing_cost_per_ton
    total_cost = harvest_cost + packing_cost
    price_per_kg = 850.0
    total_payment = harvest.gross_weight_kg * price_per_kg
    
    new_harvest = Harvest(
        farmer_id=harvest.farmer_id,
        gross_weight_kg=harvest.gross_weight_kg,
        initial_moisture_pct=harvest.initial_moisture_pct,
        harvest_cost=harvest_cost,
        packing_cost=packing_cost,
        total_cost=total_cost,
        price_per_kg=price_per_kg,
        total_payment=total_payment,
        harvest_date=harvest.harvest_date,
        destination_hub_id=harvest.destination_hub_id,
        notes=harvest.notes,
        geo_lat=farmer.latitude,
        geo_long=farmer.longitude
    )
    db.add(new_harvest)
    db.flush()
    append_ledger_entry(db, "harvest", new_harvest.id, "created", {
        "farmer_id": new_harvest.farmer_id,
        "gross_weight_kg": new_harvest.gross_weight_kg,
        "total_payment": new_harvest.total_payment,
        "harvest_date": str(new_harvest.harvest_date),
    })
    db.commit()
    db.refresh(new_harvest)
    return new_harvest


@router.get("/harvests", response_model=List[HarvestResponse])
def get_harvests(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(Harvest).order_by(Harvest.created_at.desc()).limit(limit).all()


@router.post("/hub-batches", response_model=HubBatchResponse, status_code=status.HTTP_201_CREATED)
def create_hub_batch(batch: HubBatchCreate, db: Session = Depends(get_db)):
    """Pengepul: Terima input dan proses pengeringan (Langkah 2)."""
    hub = db.query(Hub).filter(Hub.id == batch.hub_id).first()
    if not hub:
        raise HTTPException(status_code=404, detail="Hub not found")
        
    shrinkage = hub.shrinkage_rate
    final_weight = batch.total_input_kg * (1 - shrinkage)
    shrinkage_kg = batch.total_input_kg - final_weight
    
    loading = (batch.total_input_kg / 1000) * hub.loading_cost_per_ton
    drying = (batch.total_input_kg / 1000) * hub.drying_energy_cost_per_ton
    storage = hub.warehouse_area_m2 * hub.storage_cost_per_m2_day
    shrinkage_cost = shrinkage_kg * 850.0  # Biaya hantu dari bobot hilang
    
    batch_code = f"BATCH-{batch.batch_date.strftime('%y%m%d')}-H{hub.id:02d}-{uuid.uuid4().hex[:4].upper()}"
    
    new_batch = HubBatch(
        hub_id=batch.hub_id,
        batch_code=batch_code,
        total_input_kg=batch.total_input_kg,
        input_moisture_pct=batch.input_moisture_pct,
        num_farmers=batch.num_farmers,
        final_weight_kg=final_weight,
        final_moisture_pct=hub.target_moisture_pct,
        shrinkage_kg=shrinkage_kg,
        shrinkage_pct=shrinkage * 100,
        loading_cost=loading,
        drying_cost=drying,
        storage_cost=storage,
        shrinkage_cost=shrinkage_cost,
        total_handling_cost=loading + drying + storage + shrinkage_cost,
        quality_grade=batch.quality_grade,
        batch_date=batch.batch_date,
        ready_date=batch.batch_date + timedelta(days=1),
        notes=batch.notes
    )
    db.add(new_batch)
    db.flush()
    append_ledger_entry(db, "hub_batch", new_batch.id, "created", {
        "hub_id": new_batch.hub_id,
        "batch_code": new_batch.batch_code,
        "total_input_kg": new_batch.total_input_kg,
        "final_weight_kg": new_batch.final_weight_kg,
    })
    db.commit()
    db.refresh(new_batch)
    return new_batch


@router.get("/hub-batches", response_model=List[HubBatchResponse])
def get_hub_batches(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(HubBatch).order_by(HubBatch.created_at.desc()).limit(limit).all()


@router.post("/shipments", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
def create_shipment(shipment: ShipmentCreate, db: Session = Depends(get_db)):
    """Driver/Hub: Kirim FTL ke pabrik (Langkah 3)."""
    # Check utilization
    is_ok, util_pct = check_truck_utilization(shipment.payload_ton)
    if not is_ok:
        raise HTTPException(
            status_code=400, 
            detail=f"Truck utilization too low ({util_pct}%). Must be >= 95% for green routing."
        )
        
    transport_costs = full_transport_breakdown(shipment.distance_km)
    
    new_shipment = Shipment(
        hub_batch_id=shipment.hub_batch_id,
        hub_id=shipment.hub_id,
        factory_id=shipment.factory_id,
        truck_plate=shipment.truck_plate,
        payload_ton=shipment.payload_ton,
        truck_utilization_pct=util_pct,
        distance_km=shipment.distance_km,
        estimated_duration_hours=shipment.distance_km / 50.0,
        fuel_cost=transport_costs["fuel_cost"],
        toll_cost=transport_costs["toll_cost"],
        driver_cost=transport_costs["driver_cost"],
        total_transport_cost=transport_costs["total_transport"],
        carbon_emitted_kg=transport_costs["carbon_emitted_kg"],
        carbon_tax_cost=transport_costs["carbon_tax_cost"],
        shipment_date=shipment.shipment_date,
        notes=shipment.notes
    )
    db.add(new_shipment)
    db.flush()
    append_ledger_entry(db, "shipment", new_shipment.id, "created", {
        "hub_id": new_shipment.hub_id,
        "factory_id": new_shipment.factory_id,
        "payload_ton": new_shipment.payload_ton,
        "carbon_tax_cost": new_shipment.carbon_tax_cost,
    })
    db.commit()
    db.refresh(new_shipment)
    return new_shipment


@router.get("/shipments", response_model=List[ShipmentResponse])
def get_shipments(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(Shipment).order_by(Shipment.created_at.desc()).limit(limit).all()


@router.get("/daily-summary")
def get_daily_summary(db: Session = Depends(get_db)):
    """Analis: Dapatkan ringkasan transaksi hari ini (dan total historis)."""
    today = date.today()
    
    harvests_today = db.query(Harvest).filter(Harvest.harvest_date == today).all()
    batches_today = db.query(HubBatch).filter(HubBatch.batch_date == today).all()
    shipments_today = db.query(Shipment).filter(Shipment.shipment_date == today).all()
    
    return {
        "date": today,
        "harvests": {
            "count": len(harvests_today),
            "total_weight_kg": sum(h.gross_weight_kg for h in harvests_today),
            "total_payment": sum(h.total_payment for h in harvests_today)
        },
        "hub_batches": {
            "count": len(batches_today),
            "total_input_kg": sum(b.total_input_kg for b in batches_today),
            "total_shrinkage_kg": sum(b.shrinkage_kg for b in batches_today if b.shrinkage_kg)
        },
        "shipments": {
            "count": len(shipments_today),
            "total_payload_ton": sum(s.payload_ton for s in shipments_today),
            "total_carbon_emitted_kg": sum(s.carbon_emitted_kg for s in shipments_today)
        }
    }
