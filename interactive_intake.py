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
import re
from datetime import date, datetime, timezone
from pathlib import Path

from formatting_utils import normalize_postal_code

INTAKE_PATH = Path(__file__).parent / "intake_config.py"

VOICE_MODE = "--voice" in sys.argv


def _try_import_voice():
    """Voice input uses SpeechRecognition + Google's free Web Speech
    API by default, which means your spoken answer is sent to Google
    to be transcribed - it does NOT stay purely local. If you want
    voice input without that tradeoff, you'd need a local recognition
    engine (e.g. CMU Sphinx via `pip install pocketsphinx`), which is
    far less accurate. This function returns None if the library
    isn't installed, and the script falls back to text automatically."""
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
    """Ask one question. Tries voice first if enabled, always accepts
    typed input as a fallback or primary method."""
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


def main():
    print("\n=== Ontario Auto Insurance Intake ===")
    print("This information stays on your machine only, in a file that is")
    print("never committed to git (intake_config.py is gitignored).\n")

    mode_live = ask_yes_no("Do you want to run LIVE quotes with your real information?\n(Choose no to stay in safe estimate-only/hypothetical mode)")

    print("\n--- Identity ---")
    legal_name = ask("Full legal name, exactly as on your licence") if mode_live else ""
    date_of_birth = ask("Date of birth (YYYY-MM-DD)") if mode_live else ""
    licence_number = ask("Ontario driver's licence number", sensitive=True) if mode_live else ""
    licence_class = ask("Licence class", default="G")
    date_first_licensed = ask("Date first licensed (YYYY-MM-DD)") if mode_live else ""

    print("\n--- Contact ---")
    email = ask("Email") if mode_live else ""
    phone = ask("Phone number", sensitive=True) if mode_live else ""

    print("\n--- Address ---")
    street = ask("Street address", sensitive=True) if mode_live else ""
    city = ask("City", default="Toronto")
    postal_code = ask("Postal code", sensitive=True) if mode_live else ""
    postal_code = normalize_postal_code(postal_code) if postal_code else ""
    residence_start_date = ask("Date you moved to this address (YYYY-MM-DD)") if mode_live else ""

    print("\n--- Vehicle ---")
    model_year = ask("Vehicle year", default="2020")
    make = ask("Vehicle make", default="Toyota")
    model = ask("Vehicle model", default="Corolla")
    vin = ask("VIN (leave blank if unknown)", sensitive=True) if mode_live else ""
    ownership = ask("Owned or leased", default="owned")
    annual_km = ask("Annual kilometres driven", default="12000")
    commute_km = ask("One-way commute distance (km)", default="10")
    primary_use = ask("Primary use (pleasure/commute/business)", default="commute")

    print("\n--- Insurance history ---")
    current_insurer = ask("Current insurer (leave blank if none)")
    years_insured = ask("Years continuously insured", default="0")
    print("\nThese answers affect your coverage validity - please confirm explicitly rather than skipping.")
    accidents = ask("Accidents/claims in last 6 years (type 'none' if genuinely none)")
    while not accidents.strip():
        accidents = ask("Please answer explicitly - type 'none' if there are none")
    convictions = ask("Convictions in last 3 years (type 'none' if genuinely none)")
    while not convictions.strip():
        convictions = ask("Please answer explicitly - type 'none' if there are none")

    print("\n--- Coverage preferences ---")
    effective_date = ask("Coverage start date (YYYY-MM-DD)", default=date.today().isoformat())
    liability = ask("Third-party liability limit", default="2000000")
    telematics = ask_yes_no("Opt into telematics/usage-based insurance?")

    consent_timestamp = ""
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
            consent_timestamp = datetime.now(timezone.utc).isoformat()

    mode_str = "live" if mode_live else "estimate_only"

    content = f'''"""
YOUR profile — generated by interactive_intake.py.
This file is gitignored — do not remove it from .gitignore.
Re-run interactive_intake.py any time to update these answers.
"""

from schema import Applicant


def build_applicant() -> Applicant:
    return Applicant(
        mode={mode_str!r},
        consent_timestamp={consent_timestamp!r},

        legal_name={legal_name!r},
        date_of_birth={date_of_birth!r},
        licence_number={licence_number!r},
        licence_province="ON",
        licence_class={licence_class!r},
        date_first_licensed={date_first_licensed!r},

        email={email!r},
        phone={phone!r},
        province="Ontario",

        street={street!r},
        city={city!r},
        postal_code={postal_code!r},
        residence_start_date={residence_start_date!r},

        vin={vin!r},
        model_year={model_year!r},
        make={make!r},
        model={model!r},
        ownership={ownership!r},
        annual_km={annual_km!r},
        commute_km_one_way={commute_km!r},
        primary_use={primary_use!r},

        current_insurer={current_insurer!r},
        years_continuously_insured={years_insured!r},
        accidents_last_6y={accidents!r},
        convictions_last_3y={convictions!r},
        confirmed_risk_fields={True!r},

        effective_date={effective_date!r},
        liability_limit={liability!r},
        dcpd_included=True,
        collision_deductible="1000",
        comprehensive_deductible="1000",
        opcf_44r=True,
        telematics_opt_in={telematics!r},
    )
'''

    INTAKE_PATH.write_text(content, encoding="utf-8")
    print(f"\nSaved to {INTAKE_PATH}")
    print(f"Mode: {mode_str}")
    if mode_live:
        print("Live mode active. Review intake_config.py before running any route.")
    else:
        print("Estimate-only mode. Safe to run against any route.")


if __name__ == "__main__":
    main()
