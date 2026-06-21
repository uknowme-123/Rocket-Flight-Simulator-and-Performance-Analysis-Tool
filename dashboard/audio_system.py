"""Event-driven audio notifications for the Mission Control dashboard."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


ASSETS_DIR = Path(__file__).resolve().parent / "assets"
AUDIO_MIME_TYPE = "audio/wav"


@dataclass(frozen=True)
class AudioCue:
    """Map a mission event to a local sound asset and operator message."""

    file_name: str
    message: str
    level: str = "info"


AUDIO_CUES: dict[str, AudioCue] = {
    "countdown": AudioCue("countdown_beep.mp3", "Countdown tick", "info"),
    "launch": AudioCue("launch_ignition.mp3", "LIFTOFF CONFIRMED", "success"),
    "engine_burn": AudioCue("engine_burn.mp3", "Powered ascent burn active", "info"),
    "apogee": AudioCue("apogee_alert.mp3", "APOGEE REACHED", "success"),
    "descent": AudioCue("descent_alert.mp3", "DESCENT PHASE INITIATED", "info"),
    "landing": AudioCue("landing_success.mp3", "VEHICLE RECOVERED", "success"),
    "warning": AudioCue("warning_alarm.mp3", "Mission constraint warning", "warning"),
    "mission_complete": AudioCue(
        "mission_complete.mp3",
        "MISSION SUCCESSFULLY COMPLETED",
        "success",
    ),
}


def initialize_audio_state() -> None:
    """Initialize Streamlit session state for audio and event dispatch."""

    st.session_state.setdefault("audio_enabled", True)
    st.session_state.setdefault("audio_volume", 70)
    st.session_state.setdefault("mission_alerts_enabled", True)
    st.session_state.setdefault("played_audio_events", set())


def reset_audio_events() -> None:
    """Clear one-shot audio event history for a new mission run."""

    st.session_state.played_audio_events = set()


def render_audio_controls() -> None:
    """Render Mission Control audio settings in the sidebar."""

    st.subheader("Audio and Alerts")
    st.toggle("Enable Audio", key="audio_enabled")
    st.slider("Master Volume (%)", min_value=0, max_value=100, key="audio_volume")
    st.toggle("Mission Alerts", key="mission_alerts_enabled")


def _asset_bytes(cue: AudioCue) -> bytes | None:
    """Return sound asset bytes if the asset exists."""

    path = ASSETS_DIR / cue.file_name
    if not path.exists():
        return None
    return path.read_bytes()


def trigger_audio(
    event_name: str,
    unique_key: str | None = None,
    force: bool = False,
) -> bool:
    """Play an audio cue once for a mission event.

    Returns True when the event was newly dispatched. The event key prevents
    repeated playback during Streamlit reruns and telemetry auto-refresh.
    """

    cue = AUDIO_CUES.get(event_name)
    if cue is None:
        return False

    event_key = unique_key or event_name
    played_events = st.session_state.setdefault("played_audio_events", set())
    if not force and event_key in played_events:
        return False

    played_events.add(event_key)
    st.session_state.played_audio_events = played_events

    if not st.session_state.get("audio_enabled", True):
        return True

    audio_bytes = _asset_bytes(cue)
    if audio_bytes is None:
        return True

    volume = max(0.0, min(float(st.session_state.get("audio_volume", 70)) / 100.0, 1.0))
    encoded_audio = base64.b64encode(audio_bytes).decode("ascii")
    element_id = f"audio_{event_key}".replace("-", "_").replace(" ", "_")

    components.html(
        f"""
        <audio id="{element_id}" preload="auto">
            <source src="data:{AUDIO_MIME_TYPE};base64,{encoded_audio}" type="{AUDIO_MIME_TYPE}">
        </audio>
        <script>
            const audio = document.getElementById("{element_id}");
            if (audio) {{
                audio.volume = {volume:.2f};
                audio.play().catch(() => {{}});
            }}
        </script>
        """,
        height=0,
    )
    return True


def render_alert(event_name: str, message: str | None = None) -> None:
    """Render a Streamlit alert banner for a mission event."""

    if not st.session_state.get("mission_alerts_enabled", True):
        return

    cue = AUDIO_CUES.get(event_name)
    if cue is None:
        return

    alert_message = message or cue.message
    if cue.level == "success":
        st.success(alert_message)
    elif cue.level == "warning":
        st.warning(alert_message)
    else:
        st.info(alert_message)
