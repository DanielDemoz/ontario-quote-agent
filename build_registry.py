"""
Build and merge market registries.

  python build_registry.py              # writes registry/full_registry.json
  python build_registry.py --merge      # merges live-tested seed routes into full list

The full list tracks ~60 Ontario P&C legal entities from the brief's
Appendix A-style seed dataset. Only routes in registry/seed_registry.json
(or those with quote_url + automation scope) are intended for live browser runs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REGISTRY_DIR = Path(__file__).parent / "registry"
SEED_PATH = REGISTRY_DIR / "seed_registry.json"
FULL_PATH = REGISTRY_DIR / "full_registry.json"

# Appendix A-style seed entities: legal underwriter, group, brand, channel.
# quote_url left blank unless a public online quote path is known.
APPENDIX_A_ENTITIES = [
    # Definity group
    ("definity-sonnet-001", "Sonnet Insurance Company", "Definity", "Sonnet", "direct", "https://secure.sonnet.ca/#/quoting/auto/province?lang=en"),
    ("definity-economical-001", "Economical Mutual Insurance Company", "Definity", "Economical Insurance", "direct", "https://www.economical.com/en/insurance/personal/auto"),
    ("definity-echelon-001", "Echelon Insurance", "Definity", "Echelon", "MGA_program", ""),
    ("definity-fis-001", "Family Insurance Solutions Inc.", "Definity", "Family Insurance Solutions", "MGA_program", ""),
    # Intact group
    ("intact-intact-001", "Intact Insurance Company", "Intact", "Intact Insurance", "direct", "https://www.intact.ca/en/personal-insurance/car-insurance"),
    ("intact-belairdirect-001", "Belair Insurance Company Inc.", "Intact", "belairdirect", "direct", "https://www.belairdirect.com/en/car-insurance.html"),
    ("intact-jevco-001", "Jevco Insurance Company", "Intact", "Jevco", "direct", ""),
    ("intact-novex-001", "Novex Insurance Company", "Intact", "Novex", "direct", ""),
    # Aviva / RBC
    ("aviva-aviva-001", "Aviva General Insurance Company", "Aviva", "Aviva Insurance", "direct", "https://www.aviva.ca/en/insurance/auto/"),
    ("aviva-rbc-001", "Aviva General Insurance Company", "Aviva", "RBC Insurance", "agent", "https://www.rbcinsurance.com/auto-insurance.html"),
    # Co-operators / Wawanesa / Desjardins
    ("coop-cooperators-001", "Co-operators General Insurance Company", "Co-operators", "Co-operators", "direct", "https://www.cooperators.ca/en/car-insurance"),
    ("wawanesa-wawanesa-001", "Wawanesa Mutual Insurance Company", "Wawanesa", "Wawanesa Insurance", "mutual", "https://www.wawanesa.com/canada/auto-insurance/"),
    ("desjardins-desjardins-001", "Desjardins General Insurance Group", "Desjardins", "Desjardins Insurance", "direct", "https://www.desjardins.com/ca/personal-insurance/auto/"),
    ("desjardins-statefarm-001", "Desjardins General Insurance Group", "Desjardins", "State Farm Canada", "agent", ""),
    # TD / CAA / Northbridge
    ("td-td-001", "Security National Insurance Company", "TD", "TD Insurance", "direct", "https://www.tdinsurance.com/products-services/auto-insurance"),
    ("caa-caa-001", "CAA Insurance Company", "CAA", "CAA Insurance", "affinity", "https://www.caa.ca/insurance/car-insurance/"),
    ("northbridge-northbridge-001", "Northbridge General Insurance Corporation", "Northbridge", "Northbridge Insurance", "direct", ""),
    # Travelers / Chubb / Liberty / AIG
    ("travelers-travelers-001", "Travelers Canada", "Travelers", "Travelers Canada", "direct", ""),
    ("chubb-chubb-001", "Chubb Insurance Company of Canada", "Chubb", "Chubb", "direct", ""),
    ("liberty-liberty-001", "Liberty Mutual Insurance Company", "Liberty Mutual", "Liberty Mutual Canada", "direct", ""),
    ("aig-aig-001", "AIG Insurance Company of Canada", "AIG", "AIG Canada", "direct", ""),
    # Panel insurers (LowestRates / broker panels)
    ("coachman-coachman-001", "Coachman Insurance Company", "Coachman", "Coachman Insurance", "direct", ""),
    ("gore-gore-001", "Gore Mutual Insurance Company", "Gore", "Gore Mutual", "mutual", ""),
    ("pafco-pafco-001", "Pafco Insurance Company", "Pafco", "Pafco", "direct", ""),
    ("pembridge-pembridge-001", "Pembridge Insurance Company", "Pembridge", "Pembridge", "direct", ""),
    ("sgi-sgi-001", "SGI Canada Insurance Services Ltd.", "SGI", "SGI Canada", "direct", ""),
    ("zenith-zenith-001", "Zenith Insurance Company", "Zenith", "Zenith", "direct", ""),
    # Aggregators / brokers (distribution, not always rate source)
    ("agg-lowestrates-001", "TBD - returned by panel", "TBD", "LowestRates.ca", "aggregator", "https://www.lowestrates.ca/insurance/auto"),
    ("agg-ratesdotca-001", "TBD - returned by panel", "TBD", "Rates.ca", "aggregator", "https://www.rates.ca/"),
    ("broker-thinkinsure-001", "TBD - returned by broker", "TBD", "ThinkInsure", "broker", "https://www.thinkinsure.ca/car-insurance/"),
    ("broker-mitchell-001", "TBD - returned by broker", "TBD", "Mitchell & Whale", "broker", "https://www.mitchellwhale.com/auto-insurance/"),
    ("broker-onlia-001", "TBD - returned by broker", "TBD", "Onlia Insurance", "broker", "https://www.onlia.ca/auto-insurance"),
    # Mutuals (sample of Ontario mutual market)
    ("mutual-halwell-001", "Halwell Dumfries Mutual Insurance Company", "Halwell Dumfries", "Halwell Mutual", "mutual", ""),
    ("mutual-sandbox-001", "Sandbox Mutual Insurance Company", "Sandbox", "Sandbox Mutual", "mutual", ""),
    ("mutual-mutualone-001", "Mutualone Insurance Company", "Mutualone", "Mutualone", "mutual", ""),
    ("mutual-hay-mutual-001", "Hay Mutual Insurance Company", "Hay Mutual", "Hay Mutual", "mutual", ""),
    ("mutual-ontario-mutual-001", "Ontario Mutual Insurance Association members", "OMA", "Various mutuals", "mutual", ""),
    # MGAs / specialty
    ("mga-premier-001", "Premier Group", "Premier", "Premier Group MGA", "MGA_program", ""),
    ("mga-sherbrooke-001", "Sherbrooke Insurance", "Sherbrooke", "Sherbrooke", "MGA_program", ""),
    ("specialty-facility-001", "Facility Association", "FA", "Facility Association", "residual", ""),
    ("specialty-highrisk-001", "Pafco Insurance Company", "Pafco", "High-risk non-standard PPA", "direct", ""),
    ("specialty-echelon-ns-001", "Echelon Insurance", "Definity", "Echelon Non-standard", "MGA_program", ""),
    # Additional licensed entities (Appendix A completeness)
    ("allstate-allstate-001", "Allstate Insurance Company of Canada", "Allstate", "Allstate Canada", "direct", ""),
    ("cna-cna-001", "Continental Casualty Company", "CNA", "CNA Canada", "direct", ""),
    ("federated-federated-001", "Federated Insurance Company of Canada", "Federated", "Federated Insurance", "direct", ""),
    ("hagerty-hagerty-001", "Hagerty Insurance Agency LLC", "Hagerty", "Hagerty Collector", "direct", ""),
    ("markel-markel-001", "Markel International Insurance Company Limited", "Markel", "Markel", "direct", ""),
    ("old-republic-001", "Old Republic Insurance Company of Canada", "Old Republic", "Old Republic", "direct", ""),
    ("perma-perma-001", "Perma Insurance Company", "Perma", "Perma", "direct", ""),
    ("portage-portage-001", "Portage la Prairie Mutual Insurance Company", "Portage", "Portage Mutual", "mutual", ""),
    ("promutuel-promutuel-001", "Promutuel Insurance", "Promutuel", "Promutuel", "mutual", ""),
    ("safety-safety-001", "Safety Insurance Company", "Safety", "Safety Insurance", "direct", ""),
    ("saintjohn-saintjohn-001", "Saint John Mutual Insurance Company", "Saint John", "Saint John Mutual", "mutual", ""),
    ("scotia-scotia-001", "Scotia General Insurance Company", "Scotiabank", "Scotia Insurance", "agent", ""),
    ("securian-securian-001", "Securian Canada", "Securian", "Securian Canada", "direct", ""),
    ("sompo-sompo-001", "Sompo Insurance Company of Canada", "Sompo", "Sompo Canada", "direct", ""),
    ("sure-sure-001", "Sure Insurance", "Sure", "Sure", "direct", ""),
    ("tokio-tokio-001", "Tokio Marine Canada Ltd.", "Tokio Marine", "Tokio Marine", "direct", ""),
    ("unifund-unifund-001", "Unifund Assurance Company", "Unifund", "Unifund", "direct", ""),
    ("usaa-usaa-001", "USAA Casualty Insurance Company", "USAA", "USAA (eligible members)", "affinity", ""),
    ("wawanesa-wawanesa-mb-001", "Wawanesa Mutual Insurance Company", "Wawanesa", "Wawanesa (MB head office)", "mutual", ""),
    ("westfield-westfield-001", "Westfield Insurance", "Westfield", "Westfield", "direct", ""),
    ("york-york-001", "York Fire & Casualty Insurance Company", "York", "York", "direct", ""),
    ("zurich-zurich-001", "Zurich Insurance Company Ltd", "Zurich", "Zurich Canada", "direct", ""),
    ("lloyds-lloyds-001", "Lloyd's Underwriters", "Lloyd's", "Lloyd's syndicates", "direct", ""),
]


def _slug(rate_source: str) -> str:
    return rate_source.lower().replace(" ", "-").replace("/", "-")[:40]


def entity_to_record(
    registry_id: str,
    legal_underwriter: str,
    insurer_group: str,
    brand: str,
    distribution: str,
    quote_url: str,
    *,
    override: dict | None = None,
) -> dict:
    requires_human = distribution in ("broker", "residual", "MGA_program") and not quote_url
    requires_membership = distribution == "affinity" and "CAA" in brand
    status = "manual_handoff" if distribution == "residual" else "unresolved"
    record = {
        "registry_id": registry_id,
        "legal_underwriter": legal_underwriter,
        "insurer_group": insurer_group,
        "brand_or_program": brand,
        "distribution_type": distribution,
        "product_scope": "standard_PPA",
        "quote_url": quote_url,
        "public_phone_route": "",
        "licensed_intermediary": brand if distribution in ("broker", "aggregator") else "",
        "requires_licence": True,
        "requires_vin": distribution == "direct",
        "requires_membership": requires_membership,
        "requires_human": requires_human,
        "automation_notes": (
            "Appendix A seed entry — not yet live-tested."
            if not override
            else override.get("automation_notes", "")
        ),
        "status": status,
        "evidence_url": "",
        "source_citation": f"Brief Appendix A: {insurer_group} group",
        "distinct_rate_source_id": _slug(f"{insurer_group}-{brand}"),
        "last_verified_at": None,
    }
    if override:
        record.update({k: v for k, v in override.items() if v is not None})
    return record


def build_full_registry() -> list[dict]:
    records = []
    for row in APPENDIX_A_ENTITIES:
        records.append(entity_to_record(*row))
    return records


def merge_seed(full: list[dict], seed: list[dict]) -> list[dict]:
    seed_by_id = {r["registry_id"]: r for r in seed}
    seed_by_source = {r.get("distinct_rate_source_id"): r for r in seed if r.get("distinct_rate_source_id")}

    merged = []
    used_seed_ids = set()
    for rec in full:
        if rec["registry_id"] in seed_by_id:
            merged.append(seed_by_id[rec["registry_id"]])
            used_seed_ids.add(rec["registry_id"])
        elif rec["distinct_rate_source_id"] in seed_by_source:
            merged.append(seed_by_source[rec["distinct_rate_source_id"]])
            used_seed_ids.add(seed_by_source[rec["distinct_rate_source_id"]]["registry_id"])
        else:
            merged.append(rec)

    for sid, srec in seed_by_id.items():
        if sid not in used_seed_ids:
            merged.append(srec)
    return merged


def main():
    parser = argparse.ArgumentParser(description="Build Ontario market registry files")
    parser.add_argument("--merge", action="store_true", help="Merge live seed_registry.json into full list")
    args = parser.parse_args()

    full = build_full_registry()
    if args.merge and SEED_PATH.exists():
        with open(SEED_PATH, encoding="utf-8") as f:
            seed = json.load(f)
        full = merge_seed(full, seed)

    REGISTRY_DIR.mkdir(exist_ok=True)
    with open(FULL_PATH, "w", encoding="utf-8") as f:
        json.dump(full, f, indent=2)
    print(f"Wrote {len(full)} registry entries to {FULL_PATH}")


if __name__ == "__main__":
    main()
