"""Local offline text-to-speech using Windows System.Speech (no API keys).

This is a *local demo* voice for Q1/Q3 so you can hear the bots speak on this
machine. It is NOT the production voice path — real calls use Vapi's ASR/TTS
(see q1_voice_agent/vapi_assistant.json and q3_native_bots/generated/*.json).

On Windows it shells out to PowerShell's System.Speech synthesizer, which is
built in (no install). On other OSes it degrades to printing the text.
"""
from __future__ import annotations

import platform
import subprocess
import tempfile
import os


def _powershell_speak(text: str, voice_hint: str | None, rate: int) -> bool:
    # Build a small PS script; write to a temp file to avoid quoting issues.
    safe = text.replace("'", "''")
    voice_line = ""
    if voice_hint:
        voice_line = (
            "try { $s.SelectVoice((($s.GetInstalledVoices() | "
            "ForEach-Object { $_.VoiceInfo.Name } | "
            f"Where-Object {{ $_ -like '*{voice_hint}*' }})[0])) }} catch {{}}\n"
        )
    script = (
        "Add-Type -AssemblyName System.Speech\n"
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer\n"
        f"{voice_line}"
        f"$s.Rate = {rate}\n"
        f"$s.Speak('{safe}')\n"
    )
    fd, path = tempfile.mkstemp(suffix=".ps1")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(script)
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", path],
            check=True,
        )
        return True
    except Exception:
        return False
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def speak(text: str, *, voice_hint: str | None = None, rate: int = 0) -> None:
    """Speak text aloud if possible; always print it too.

    voice_hint: substring of an installed voice name (e.g. 'Zira', 'David').
    rate: -10..10 (0 = normal).
    """
    print(f"🔊 {text}")
    if platform.system() == "Windows":
        _powershell_speak(text, voice_hint, rate)
