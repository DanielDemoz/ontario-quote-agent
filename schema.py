"""
Ontario All-Quote Agent Challenge — shared schema definitions.
These enums and field lists come directly from the participant brief
(Sections 3, 5, 6, 7). Keep this as the single source of truth so the
intake form, registry, browser agents, and normalizer all agree on
field names.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


# ---------------------------------------------------------------------
# Status enum (Section 7)
# ---------------------------------------------------------------------
class Status(str, Enum):
    QUOTED_COMPARABLE = "quoted_comparable"
    QUOTED_NON_COMPARABLE = "quoted_non_comparable"
    ESTIMATE_ONLY = "estimate_only"
    CALLBACK_REQUIRED = "callback_required"
    MANUAL_HANDOFF = "manual_handoff"
    INELIGIBLE = "ineligible"
    AFFINITY_RESTRICTED = "affinity_restricted"
    SPECIALTY_ONLY = "specialty_only"
    DUPLICATE_RATE_SOURCE = "duplicate_rate_source"
    NOT_CURRENTLY_WRITING = "not_currently_writing"
    BLOCKED = "blocked"
    UNREACHABLE = "unreachable"
    UNRESOLVED = "unresolved"


class DistributionType(str, Enum):
    DIRECT = "direct"
    AGENT = "agent"
    BROKER = "broker"
    AGGREGATOR = "aggregator"
    AFFINITY = "affinity"
    MGA_PROGRAM = "MGA_program"
    MUTUAL = "mutual"
    RESIDUAL = "residual"


class ProductScope(str, Enum):
    STANDARD_PPA = "standard_PPA"
    NONSTANDARD_PPA = "nonstandard_PPA"
    HIGH_NET_WORTH = "high_net_worth"
    COLLECTOR = "collector"
    COMMERCIAL_SPECIALTY = "commercial_specialty"
    UNKNOWN = "unknown"


class Confidence(str, Enum):
    HIGH = "high"      # exact premium, benchmark coverage matched
    MEDIUM = "medium"  # licensed rep's documented quote
    LOW = "low"        # estimate or unresolved coverage diff


NEVER_DEFAULT_FIELDS = {
    "accidents_last_6y", "convictions_last_3y", "current_insurer",
    "years_continuously_insured", "licence_suspension_last_6y",
    "insurer_cancellation_last_3y", "business_use_percentage",
    "special_use", "unrepaired_damage", "vehicle_modifications",
}


# ---------------------------------------------------------------------
# Market registry record (Section 3 + Appendix B)
# ---------------------------------------------------------------------
@dataclass
class MarketRecord:
    registry_id: str
    legal_underwriter: str
    insurer_group: str
    brand_or_program: str
    distribution_type: DistributionType
    product_scope: ProductScope
    quote_url: str = ""
    public_phone_route: str = ""
    licensed_intermediary: str = ""
    requires_licence: bool = False
    requires_vin: bool = False
    requires_membership: bool = False
    requires_human: bool = False
    automation_notes: str = ""
    status: Status = Status.UNRESOLVED
    evidence_url: str = ""
    source_citation: str = ""
    distinct_rate_source_id: str = ""
    last_verified_at: Optional[str] = None

    def touch(self):
        self.last_verified_at = datetime.utcnow().isoformat() + "Z"


# ---------------------------------------------------------------------
# Full canonical intake schema (Section 5)
# ---------------------------------------------------------------------
@dataclass
class Applicant:
    # Consent / mode
    mode: str = "estimate_only"          # "estimate_only" | "live"
    consent_timestamp: Optional[str] = None

    # Identity — leave blank / hypothetical in estimate_only mode
    legal_name: str = ""
    date_of_birth: str = ""
    licence_number: str = ""             # NEVER fill unless mode == "live" and it's the user's own
    licence_province: str = "ON"
    licence_class: str = "G"
    date_first_licensed: str = ""

    # Additional canonical fields per brief Section 5
    gender: str = ""
    marital_status: str = ""
    licence_status: str = "valid"
    licence_expiry: str = ""
    date_first_licensed_g1: str = ""
    date_first_licensed_g2: str = ""
    date_first_licensed_g: str = ""
    driver_training_completed: bool = False

    # Contact
    email: str = ""
    phone: str = ""
    province: str = "Ontario"   # plain province selector, distinct from licence_province

    # Address
    street: str = ""
    city: str = ""
    postal_code: str = ""
    residence_start_date: str = ""

    # Vehicle
    vin: str = ""
    model_year: str = ""
    make: str = ""
    model: str = ""
    ownership: str = "owned"             # owned | leased
    annual_km: str = ""
    commute_km_one_way: str = ""
    primary_use: str = "pleasure"        # pleasure | commute | business
    vehicle_trim: str = ""
    vehicle_fuel_type: str = ""
    purchase_lease_date: str = ""
    registered_owner_same_as_driver: bool = True
    lienholder_name: str = ""
    business_use_percentage: str = "0"
    days_commuting_per_week: str = "5"
    carpool: bool = False
    garaging_address_same_as_home: bool = True
    unrepaired_damage: bool = False
    vehicle_modifications: str = "none"
    winter_tires: bool = False
    anti_theft_device: bool = False
    special_use: str = "none"
    household_vehicle_count: str = "1"

    # History
    current_insurer: str = ""
    years_continuously_insured: str = ""
    accidents_last_6y: str = "none"
    convictions_last_3y: str = "none"
    licence_suspension_last_6y: str = "none"
    insurer_cancellation_last_3y: str = "none"

    # Employment
    occupation: str = ""
    employer: str = ""
    industry: str = ""
    years_with_employer: str = ""

    # Address history
    previous_address: str = ""
    previous_address_years: str = ""
    residence_type: str = ""
    residence_owned_or_rented: str = "owned"
    has_mortgage: bool = False
    has_tenant_insurance: bool = False

    # Vehicle detail
    vehicle_colour: str = ""
    vehicle_current_value: str = ""
    financing_company: str = ""
    leasing_company: str = ""
    financing_length_months: str = ""

    # Business use detail
    is_self_employed: bool = False
    business_type: str = ""
    business_kilometres: str = "0"

    # Student/young driver
    is_student: bool = False
    school_name: str = ""

    # Household
    other_drivers_count: str = "0"

    # Coverage benchmark (Section 6 — suggested demo benchmark)
    effective_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    liability_limit: str = "2000000"
    dcpd_included: bool = True
    collision_deductible: str = "1000"
    comprehensive_deductible: str = "1000"
    opcf_44r: bool = True
    telematics_opt_in: bool = False

    # Telematics consent (separate from the opt-in decision)
    telematics_data_consent: bool = False

    # Discount eligibility flags
    has_multi_policy: bool = False
    is_good_student: bool = False
    is_mature_driver: bool = False
    has_professional_association: bool = False
    has_alumni_discount_eligibility: bool = False
    has_employer_discount_eligibility: bool = False

    field_confidence: Dict[str, str] = field(default_factory=dict)
    accidents_detail: List[dict] = field(default_factory=list)
    convictions_detail: List[dict] = field(default_factory=list)

    def get_confidence(self, field_name: str) -> str:
        return self.field_confidence.get(field_name, "unknown")

    def mark_verified(self, field_name: str):
        self.field_confidence[field_name] = "verified"

    def mark_default(self, field_name: str):
        self.field_confidence[field_name] = "default"

    def is_hypothetical(self) -> bool:
        return self.mode == "estimate_only"


# ---------------------------------------------------------------------
# Result record (Section 7)
# ---------------------------------------------------------------------
@dataclass
class QuoteResult:
    registry_id: str
    distinct_rate_source_id: str
    status: Status
    annual_premium: Optional[float] = None
    monthly_premium: Optional[float] = None
    coverage_notes: str = ""
    matches_benchmark: bool = False
    quote_or_reference_id: str = ""
    effective_date: str = ""
    evidence_timestamp: str = ""
    evidence_artifact_path: str = ""
    source_url: str = ""
    confidence: Confidence = Confidence.LOW
    failure_reason: str = ""
    next_action: str = ""
