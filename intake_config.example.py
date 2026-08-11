"""
EXAMPLE intake profile with fake data, showing the structure. This
file IS committed to git — never put real information here.
"""

from schema import Applicant


def build_applicant() -> Applicant:
    a = Applicant(
        mode="estimate_only",
        consent_timestamp="",
        legal_name="Jordan Example",
        date_of_birth="1990-01-01",
        licence_number="",
        licence_province="ON",
        licence_class="G",
        date_first_licensed="2008-01-01",
        email="jordan.example@example.com",
        phone="",
        province="Ontario",
        street="123 Example Street",
        city="Toronto",
        postal_code="M4B 2E5",
        residence_start_date="2020-01-01",
        vin="",
        model_year="2020",
        make="Toyota",
        model="Corolla",
        ownership="owned",
        annual_km="12000",
        commute_km_one_way="10",
        primary_use="commute",
        current_insurer="Example Insurance Co",
        years_continuously_insured="5",
        accidents_last_6y="none",
        convictions_last_3y="none",
        liability_limit="2000000",
        dcpd_included=True,
        collision_deductible="1000",
        comprehensive_deductible="1000",
        opcf_44r=True,
        telematics_opt_in=False,
    )
    a.field_confidence = {
        "legal_name": "verified",
        "accidents_last_6y": "verified",
        "convictions_last_3y": "verified",
        "liability_limit": "default",
    }
    return a
