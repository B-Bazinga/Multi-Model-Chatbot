import os
from typing import Optional
import asyncio
import logging

from ai_companion.core.exceptions import TextToSpeechError
from ai_companion.settings import settings
from elevenlabs import ElevenLabs, VoiceSettings


class TextToSpeech:
    """A class to handle text-to-speech conversion using ElevenLabs."""

    # Required environment variables
    REQUIRED_ENV_VARS = ["ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID"]

    def __init__(self):
        """Initialize the TextToSpeech class and validate environment variables."""
        self._validate_env_vars()
        self._client: Optional[ElevenLabs] = None
        self.logger = logging.getLogger(__name__)

    def _validate_env_vars(self) -> None:
        """Validate that all required environment variables are set."""
        missing_vars = [var for var in self.REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    @property
    def client(self) -> ElevenLabs:
        """Get or create ElevenLabs client instance using singleton pattern."""
        if self._client is None:
            self._client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        return self._client

    def _synthesize_sync(self, text: str) -> bytes:
        """Synchronous TTS call to ElevenLabs. Handles the generator and returns bytes."""
        try:
            audio_chunks = self.client.text_to_speech.convert(
                voice_id=settings.ELEVENLABS_VOICE_ID,
                text=text,
                model_id=settings.TTS_MODEL_NAME,
                voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.5),
                output_format="mp3_44100_128",
            )
            audio_bytes = b""
            for chunk in audio_chunks:
                audio_bytes += chunk
            if not audio_bytes:
                raise TextToSpeechError("Generated audio is empty")
            return audio_bytes
        except Exception as e:
            self.logger.error(f"Text-to-speech conversion failed (sync): {str(e)}", exc_info=True)
            raise

    async def synthesize(self, text: str) -> bytes:
        """Convert text to speech using ElevenLabs (async wrapper)."""
        if not text.strip():
            raise ValueError("Input text cannot be empty")
        if len(text) > 5000:
            raise ValueError("Input text exceeds maximum length of 5000 characters")
        try:
            loop = asyncio.get_event_loop()
            audio_bytes = await loop.run_in_executor(None, self._synthesize_sync, text)
            return audio_bytes
        except Exception as e:
            self.logger.error(f"Text-to-speech conversion failed: {str(e)}", exc_info=True)
            raise TextToSpeechError(f"Text-to-speech conversion failed: {str(e)}") from e
