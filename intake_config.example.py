"""
Example intake profile — copy to intake_config.py and customize.

  cp intake_config.example.py intake_config.py

Default mode is estimate_only (no real licence/name).
"""

from schema import Applicant


def build_applicant() -> Applicant:
    return Applicant(
        mode="estimate_only",
        consent_timestamp=None,
        legal_name="",
        date_of_birth="",
        licence_number="",
        licence_province="ON",
        licence_class="G",
        province="Ontario",
        email="quote-demo@example.com",
        phone="",
        street="",
        city="Toronto",
        postal_code="M5V 3A8",
        model_year="2019",
        make="Honda",
        model="Civic",
        ownership="owned",
        annual_km="12000",
        primary_use="pleasure",
        current_insurer="",
        years_continuously_insured="5",
        accidents_last_6y="none",
        convictions_last_3y="none",
        liability_limit="2000000",
        dcpd_included=True,
        collision_deductible="1000",
        comprehensive_deductible="1000",
        opcf_44r=True,
    )
