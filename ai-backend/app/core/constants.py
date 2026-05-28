"""
LabMind AI — Shared Constants & Enums
"""

import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    CLINICIAN = "clinician"
    STUDENT = "student"


class Department(str, enum.Enum):
    HEMATOLOGY = "hematology"
    URINALYSIS = "urinalysis"
    PARASITOLOGY = "parasitology"
    BIOCHEMISTRY = "biochemistry"
    MICROBIOLOGY = "microbiology"
    BLOODBANK = "bloodbank"


class CasePriority(str, enum.Enum):
    ROUTINE = "routine"
    URGENT = "urgent"
    STAT = "stat"


class CaseStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AssetType(str, enum.Enum):
    BLOOD_SMEAR = "blood_smear"
    URINE_SEDIMENT = "urine_sediment"
    STOOL_SAMPLE = "stool_sample"
    OTHER = "other"


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class RashaRole(str, enum.Enum):
    USER = "user"
    RASHA = "rasha"


class AnalysisStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportStatus(str, enum.Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    PRELIMINARY = "preliminary"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class ReviewDecision(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUEST_CHANGES = "request_changes"


class AlertType(str, enum.Enum):
    CRITICAL_FINDING = "critical_finding"
    REVIEW_REQUIRED = "review_required"
    REPORT_REJECTED = "report_rejected"
    SYSTEM = "system"


class AlertPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Which roles can approve/reject reports
REVIEWER_ROLES = {UserRole.ADMIN, UserRole.CLINICIAN}


class AuditAction(str, enum.Enum):
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_LOGIN_FAILED = "user.login_failed"
    USER_PROFILE_UPDATED = "user.profile_updated"
    PATIENT_CREATED = "patient.created"
    CASE_CREATED = "case.created"
    CASE_STATUS_CHANGED = "case.status_changed"
    ASSET_UPLOADED = "asset.uploaded"
    ASSET_DELETED = "asset.deleted"
    ANALYSIS_QUEUED = "analysis.queued"
    ANALYSIS_STARTED = "analysis.started"
    ANALYSIS_COMPLETED = "analysis.completed"
    ANALYSIS_FAILED = "analysis.failed"
    REPORT_CREATED = "report.created"
    REPORT_UPDATED = "report.updated"
    REPORT_SUBMITTED = "report.submitted"
    REPORT_REVIEWED = "report.reviewed"
    REPORT_ARCHIVED = "report.archived"
    ALERT_CREATED = "alert.created"
    ALERT_DISMISSED = "alert.dismissed"
    RASHA_SESSION_STARTED = "rasha.session_started"
    RASHA_MESSAGE_SENT = "rasha.message_sent"
