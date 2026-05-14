from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Patient(Base):
    __tablename__ = "patients"
    id            = Column(Integer, primary_key=True, index=True)
    patient_uid   = Column(String(50), unique=True, nullable=False)
    name          = Column(String(120), nullable=False)
    age           = Column(Integer)
    blood_group   = Column(String(5))
    phone         = Column(String(15))
    tier0_blob    = Column(Text)
    tier1_blob    = Column(Text)
    tier2_blob    = Column(Text)
    tier3_blob    = Column(Text)
    qr_image_path = Column(String(255))
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    audit_logs    = relationship("AuditLog", back_populates="patient")

class Provider(Base):
    __tablename__ = "providers"
    id            = Column(Integer, primary_key=True, index=True)
    provider_id   = Column(String(50), unique=True, nullable=False)
    name          = Column(String(120), nullable=False)
    role          = Column(String(50), nullable=False)
    tier_level    = Column(Integer, nullable=False, default=1)
    license_hash  = Column(String(255), nullable=False)
    is_active     = Column(Boolean, default=True)
    registered_at = Column(DateTime, default=datetime.utcnow)
    audit_logs    = relationship("AuditLog", back_populates="provider")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id            = Column(Integer, primary_key=True, index=True)
    patient_uid   = Column(String(50), ForeignKey("patients.patient_uid"), nullable=False)
    provider_id   = Column(String(50), ForeignKey("providers.provider_id"), nullable=False)
    action        = Column(String(50), nullable=False)
    tier_accessed = Column(Integer, nullable=False)
    details       = Column(Text)
    chain_hash    = Column(String(64), nullable=False, index=True)
    timestamp     = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_address    = Column(String(45))
    patient       = relationship("Patient", back_populates="audit_logs")
    provider      = relationship("Provider", back_populates="audit_logs")

class DrugInteraction(Base):
    __tablename__ = "drug_interactions"
    id             = Column(Integer, primary_key=True, index=True)
    drug_a         = Column(String(100), nullable=False, index=True)
    drug_b         = Column(String(100), nullable=False, index=True)
    severity       = Column(String(20), nullable=False)
    mechanism      = Column(Text)
    recommendation = Column(Text)
    source         = Column(String(100))

class ConsentSession(Base):
    __tablename__ = "consent_sessions"
    id             = Column(Integer, primary_key=True, index=True)
    session_id     = Column(String(36), unique=True, nullable=False, index=True) # UUID
    patient_uid    = Column(String(50), nullable=False, index=True)
    provider_id    = Column(String(50), nullable=False, index=True)
    otp_hash       = Column(String(255), nullable=False)
    phone_number   = Column(String(15), nullable=False)
    tier_requested = Column(Integer, nullable=False)
    status         = Column(String(20), default="pending") # pending, approved, rejected, expired
    created_at     = Column(DateTime, default=datetime.utcnow)
    expires_at     = Column(DateTime, nullable=False)
    approved_at    = Column(DateTime, nullable=True)