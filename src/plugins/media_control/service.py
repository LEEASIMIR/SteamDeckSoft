from __future__ import annotations

import logging

from pycaw.constants import EDataFlow, ERole, DEVICE_STATE
from pycaw.pycaw import AudioUtilities

logger = logging.getLogger(__name__)


class MediaControlService:
    def __init__(self) -> None:
        self._volume_interface = None
        self._mic_volume_interface = None
        self._init_audio()
        self._init_microphone()

    def _init_audio(self) -> None:
        try:
            devices = AudioUtilities.GetSpeakers()
            self._volume_interface = devices.EndpointVolume
            logger.info("Audio endpoint initialized")
        except Exception:
            logger.exception("Failed to initialize audio endpoint")

    def _init_microphone(self) -> None:
        try:
            mic = AudioUtilities.GetMicrophone()
            mic_device = AudioUtilities.CreateDevice(mic)
            self._mic_volume_interface = mic_device.EndpointVolume
            logger.info("Microphone endpoint initialized")
        except Exception:
            logger.debug("Failed to initialize microphone endpoint", exc_info=True)

    def get_volume(self) -> float:
        if self._volume_interface is None:
            return 0.0
        try:
            return self._volume_interface.GetMasterVolumeLevelScalar()
        except Exception:
            return 0.0

    def set_volume(self, level: float) -> None:
        if self._volume_interface is None:
            return
        try:
            level = max(0.0, min(1.0, level))
            self._volume_interface.SetMasterVolumeLevelScalar(level, None)
        except Exception:
            logger.exception("Failed to set volume")

    def volume_up(self, step: float = 0.05) -> None:
        current = self.get_volume()
        self.set_volume(current + step)

    def volume_down(self, step: float = 0.05) -> None:
        current = self.get_volume()
        self.set_volume(current - step)

    def toggle_mute(self) -> None:
        if self._volume_interface is None:
            return
        try:
            muted = self._volume_interface.GetMute()
            self._volume_interface.SetMute(not muted, None)
        except Exception:
            logger.exception("Failed to toggle mute")

    def is_muted(self) -> bool:
        if self._volume_interface is None:
            return False
        try:
            return bool(self._volume_interface.GetMute())
        except Exception:
            return False

    # --- Microphone mute ---

    def toggle_mic_mute(self) -> None:
        if self._mic_volume_interface is None:
            return
        try:
            muted = self._mic_volume_interface.GetMute()
            self._mic_volume_interface.SetMute(not muted, None)
        except Exception:
            logger.exception("Failed to toggle mic mute")

    def is_mic_muted(self) -> bool:
        if self._mic_volume_interface is None:
            return False
        try:
            return bool(self._mic_volume_interface.GetMute())
        except Exception:
            return False

    # --- Audio output device switching ---

    def get_audio_output_devices(self) -> list[tuple[str, str]]:
        """Return list of (device_id, friendly_name) for active render endpoints."""
        try:
            devices = AudioUtilities.GetAllDevices(
                data_flow=EDataFlow.eRender.value,
                device_state=DEVICE_STATE.ACTIVE.value,
            )
            return [(d.id, d.FriendlyName or d.id) for d in devices]
        except Exception:
            logger.debug("Failed to enumerate audio output devices", exc_info=True)
            return []

    def get_default_audio_output_device_id(self) -> str:
        try:
            enumerator = AudioUtilities.GetDeviceEnumerator()
            device = enumerator.GetDefaultAudioEndpoint(
                EDataFlow.eRender.value, ERole.eMultimedia.value,
            )
            return device.GetId()
        except Exception:
            logger.debug("Failed to get default audio output device", exc_info=True)
            return ""

    def cycle_audio_output_device(self) -> str:
        """Switch to the next audio output device. Returns the new device's friendly name."""
        devices = self.get_audio_output_devices()
        if len(devices) < 2:
            return self.get_current_audio_output_name()

        current_id = self.get_default_audio_output_device_id()
        current_idx = next(
            (i for i, (did, _) in enumerate(devices) if did == current_id),
            0,
        )
        next_idx = (current_idx + 1) % len(devices)
        next_id, next_name = devices[next_idx]

        try:
            AudioUtilities.SetDefaultDevice(
                next_id,
                roles=[ERole.eConsole, ERole.eMultimedia, ERole.eCommunications],
            )
        except Exception:
            logger.exception("Failed to switch audio device")
            return self.get_current_audio_output_name()

        # Re-init speaker endpoint to use the new device
        self._init_audio()
        return next_name

    def get_current_audio_output_name(self) -> str:
        try:
            enumerator = AudioUtilities.GetDeviceEnumerator()
            device = enumerator.GetDefaultAudioEndpoint(
                EDataFlow.eRender.value, ERole.eMultimedia.value,
            )
            audio_device = AudioUtilities.CreateDevice(device)
            return audio_device.FriendlyName or ""
        except Exception:
            logger.debug("Failed to get current audio output name", exc_info=True)
            return ""
