"""Optional microphone dictation for the Streamlit intake UI."""

from __future__ import annotations


def speech_recognition_available() -> bool:
    try:
        import speech_recognition  # noqa: F401
        return True
    except ImportError:
        return False


def listen_once(timeout: int = 5, phrase_limit: int = 10) -> tuple[str | None, str | None]:
    """
    Capture one spoken phrase from the default microphone.
    Returns (transcript, error_message). Transcript uses Google's web API
    (audio leaves your machine for transcription).
    """
    try:
        import speech_recognition as sr
    except ImportError:
        return None, "Install voice support: pip install SpeechRecognition pyaudio"

    try:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.4)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
        text = recognizer.recognize_google(audio)
        return text.strip(), None
    except sr.WaitTimeoutError:
        return None, "No speech detected. Try again or type your answer."
    except sr.UnknownValueError:
        return None, "Could not understand audio. Please type your answer."
    except Exception as exc:
        return None, f"Voice capture failed: {exc}"
