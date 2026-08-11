"""
Interactive consent-aware intake. Run this instead of hand-editing
intake_config.py. Asks each required field in plain language, then
writes a complete intake_config.py from your answers.

Text input is the default and always works. Voice input is optional
(--voice flag) and comes with a real privacy tradeoff explained below
before you opt in.

Run:
    python interactive_intake.py            (text)
    python interactive_intake.py --voice     (voice, falls back to text per-question on failure)
"""

import sys
from dataclasses import fields
from datetime import date, datetime, timezone

from formatting_utils import normalize_postal_code
from intake_writer import write_applicant
from schema import Applicant, NEVER_DEFAULT_FIELDS

VOICE_MODE = "--voice" in sys.argv


def _try_import_voice():
    try:
        import speech_recognition as sr
        return sr
    except ImportError:
        return None


sr = _try_import_voice() if VOICE_MODE else None
if VOICE_MODE and sr is None:
    print("Voice mode requested but 'speech_recognition' isn't installed.")
    print("Install with: pip install SpeechRecognition pyaudio")
    print("Falling back to text input for this run.\n")
elif VOICE_MODE:
    print("=" * 70)
    print("VOICE MODE: your spoken answers will be sent to Google's speech")
    print("recognition service to be transcribed. This is NOT purely local.")
    print("If you're not comfortable with that for sensitive fields (licence")
    print("number, address), just type the answer instead when prompted -")
    print("every question accepts typed input as a fallback.")
    print("=" * 70 + "\n")


def ask(prompt: str, default: str = "", sensitive: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    note = " (spoken answers for this field go to Google - type instead if preferred)" if (VOICE_MODE and sr and sensitive) else ""
    full_prompt = f"{prompt}{suffix}{note}: "

    if VOICE_MODE and sr and not sensitive:
        print(full_prompt, end="", flush=True)
        print("\n  [Press Enter to speak your answer, or just type it]")
        typed = input("  > ")
        if typed.strip():
            return typed.strip() or default
        return _listen(sr) or default

    typed = input(full_prompt)
    return typed.strip() or default


def _listen(sr_module) -> str:
    try:
        r = sr_module.Recognizer()
        with sr_module.Microphone() as source:
            print("  Listening... speak now.")
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=5, phrase_time_limit=8)
        text = r.recognize_google(audio)
        print(f"  Heard: {text}")
        confirm = input("  Correct? (y/n): ").strip().lower()
        if confirm == "y":
            return text
        return input("  Type the correct answer: ").strip()
    except Exception as e:
        print(f"  Voice recognition failed ({e}). Please type instead.")
        return input("  > ").strip()


def ask_yes_no(prompt: str) -> bool:
    while True:
        ans = input(f"{prompt} (yes/no): ").strip().lower()
        if ans in ("yes", "y"):
            return True
        if ans in ("no", "n"):
            return False
        print("Please answer yes or no.")


def set_verified(applicant: Applicant, field_name: str, value) -> None:
    setattr(applicant, field_name, value)
    applicant.mark_verified(field_name)


def main():
    print("\n=== Ontario Auto Insurance Intake ===")
    print("This information stays on your machine only, in a file that is")
    print("never committed to git (intake_config.py is gitignored).\n")

    applicant = Applicant()
    mode_live = ask_yes_no(
        "Do you want to run LIVE quotes with your real information?\n"
        "(Choose no to stay in safe estimate-only/hypothetical mode)"
    )

    print("\n--- Identity ---")
    if mode_live:
        set_verified(applicant, "legal_name", ask("Full legal name, exactly as on your licence"))
        set_verified(applicant, "date_of_birth", ask("Date of birth (YYYY-MM-DD)"))
        set_verified(applicant, "licence_number", ask("Ontario driver's licence number", sensitive=True))
    set_verified(applicant, "licence_class", ask("Licence class", default="G"))
    if mode_live:
        set_verified(applicant, "date_first_licensed", ask("Date first licensed (YYYY-MM-DD)"))
    set_verified(applicant, "gender", ask("Gender (optional)", default=""))
    set_verified(applicant, "marital_status", ask("Marital status (optional)", default=""))
    set_verified(applicant, "licence_status", ask("Licence status", default="valid"))

    print("\n--- Contact ---")
    if mode_live:
        set_verified(applicant, "email", ask("Email"))
        set_verified(applicant, "phone", ask("Phone number", sensitive=True))

    print("\n--- Address ---")
    if mode_live:
        set_verified(applicant, "street", ask("Street address", sensitive=True))
    set_verified(applicant, "city", ask("City", default="Toronto"))
    if mode_live:
        postal = ask("Postal code", sensitive=True)
        set_verified(applicant, "postal_code", normalize_postal_code(postal) if postal else "")
        set_verified(applicant, "residence_start_date", ask("Date you moved to this address (YYYY-MM-DD)"))
    set_verified(applicant, "residence_type", ask("Residence type (house/condo/apartment)", default=""))
    set_verified(applicant, "residence_owned_or_rented", ask("Own or rent", default="owned"))

    print("\n--- Address history ---")
    set_verified(applicant, "previous_address", ask("Previous address (blank if none)", default=""))
    set_verified(applicant, "previous_address_years", ask("Years at previous address", default=""))

    print("\n--- Vehicle ---")
    set_verified(applicant, "model_year", ask("Vehicle year", default="2020"))
    set_verified(applicant, "make", ask("Vehicle make", default="Toyota"))
    set_verified(applicant, "model", ask("Vehicle model", default="Corolla"))
    if mode_live:
        set_verified(applicant, "vin", ask("VIN (leave blank if unknown)", sensitive=True))
    set_verified(applicant, "vehicle_trim", ask("Vehicle trim (optional)", default=""))
    set_verified(applicant, "ownership", ask("Owned or leased", default="owned"))
    set_verified(applicant, "annual_km", ask("Annual kilometres driven", default="12000"))
    set_verified(applicant, "commute_km_one_way", ask("One-way commute distance (km)", default="10"))
    set_verified(applicant, "primary_use", ask("Primary use (pleasure/commute/business)", default="commute"))
    set_verified(applicant, "vehicle_modifications", ask("Vehicle modifications (type 'none' if none)", default="none"))
    set_verified(applicant, "special_use", ask("Special use (type 'none' if none)", default="none"))
    set_verified(applicant, "winter_tires", ask_yes_no("Winter tires installed?"))
    set_verified(applicant, "unrepaired_damage", ask_yes_no("Any unrepaired damage?"))

    print("\n--- Insurance history ---")
    set_verified(applicant, "current_insurer", ask("Current insurer (leave blank if none)"))
    set_verified(applicant, "years_continuously_insured", ask("Years continuously insured", default="0"))
    print("\nThese answers affect your coverage validity - please confirm explicitly rather than skipping.")
    accidents = ask("Accidents/claims in last 6 years (type 'none' if genuinely none)")
    while not accidents.strip():
        accidents = ask("Please answer explicitly - type 'none' if there are none")
    set_verified(applicant, "accidents_last_6y", accidents)
    convictions = ask("Convictions in last 3 years (type 'none' if genuinely none)")
    while not convictions.strip():
        convictions = ask("Please answer explicitly - type 'none' if there are none")
    set_verified(applicant, "convictions_last_3y", convictions)
    set_verified(applicant, "licence_suspension_last_6y", ask("Licence suspensions last 6 years (type 'none' if none)", default="none"))
    set_verified(applicant, "insurer_cancellation_last_3y", ask("Insurer cancellations last 3 years (type 'none' if none)", default="none"))

    if accidents.strip().lower() != "none":
        print("\nLet's get the details for each incident (blank date to finish):")
        accidents_detail = []
        while True:
            incident_date = ask("Incident date (YYYY-MM-DD, blank to finish)")
            if not incident_date.strip():
                break
            at_fault = ask_yes_no("Were you at fault?")
            accidents_detail.append({"date": incident_date, "at_fault": at_fault})
        applicant.accidents_detail = accidents_detail
        applicant.mark_verified("accidents_detail")

    if convictions.strip().lower() != "none":
        print("\nConviction details (blank date to finish):")
        convictions_detail = []
        while True:
            conviction_date = ask("Conviction date (YYYY-MM-DD, blank to finish)")
            if not conviction_date.strip():
                break
            convictions_detail.append({"date": conviction_date})
        applicant.convictions_detail = convictions_detail
        applicant.mark_verified("convictions_detail")

    print("\n--- Employment ---")
    set_verified(applicant, "occupation", ask("Occupation (optional)", default=""))
    set_verified(applicant, "employer", ask("Employer (optional)", default=""))
    set_verified(applicant, "industry", ask("Industry (optional)", default=""))

    print("\n--- Coverage preferences ---")
    set_verified(applicant, "effective_date", ask("Coverage start date (YYYY-MM-DD)", default=date.today().isoformat()))
    set_verified(applicant, "liability_limit", ask("Third-party liability limit", default="2000000"))
    set_verified(applicant, "telematics_opt_in", ask_yes_no("Opt into telematics/usage-based insurance?"))

    if mode_live:
        print("\n--- Consent ---")
        consented = ask_yes_no(
            "I confirm this is my own accurate information, I consent to it "
            "being submitted to insurance quote routes, and I understand no "
            "policy will be purchased or bound automatically. Do you consent?"
        )
        if not consented:
            print("\nConsent not given. Falling back to estimate_only mode.")
            mode_live = False
        else:
            applicant.consent_timestamp = datetime.now(timezone.utc).isoformat()
            applicant.mark_verified("consent_timestamp")

    applicant.mode = "live" if mode_live else "estimate_only"
    applicant.mark_verified("mode")

    tracked = set(applicant.field_confidence.keys())
    for f in fields(Applicant):
        if f.name in tracked or f.name in ("field_confidence", "accidents_detail", "convictions_detail"):
            continue
        applicant.mark_default(f.name)

    unconfirmed = [f for f in NEVER_DEFAULT_FIELDS if applicant.get_confidence(f) != "verified"]
    if unconfirmed:
        print(f"\nNote: not explicitly confirmed, will block routes asking for these: {unconfirmed}")

    path = write_applicant(applicant, source="interactive_intake.py")
    print(f"\nSaved to {path}")
    print(f"Mode: {applicant.mode}")
    if mode_live:
        print("Live mode active. Review intake_config.py before running any route.")
    else:
        print("Estimate-only mode. Safe to run against any route.")


if __name__ == "__main__":
    main()
