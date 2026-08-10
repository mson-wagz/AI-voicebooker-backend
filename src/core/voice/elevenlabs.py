"""
Eleven Labs voice configuration and utilities for Vapi integration
"""
import os
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

class ElevenLabsVoice(BaseModel):
    """Eleven Labs voice configuration model"""
    voice_id: str
    name: str
    description: str
    language: str = "en"
    gender: str = "female"

def get_voice_config(voice_id: Optional[str] = None, settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get complete voice configuration for Vapi"""
    voice_id = voice_id or "rachel"  # Default voice
    
    # Get voice info from ElevenLabsManager
    voice = ElevenLabsManager.AVAILABLE_VOICES.get(voice_id, ElevenLabsManager.AVAILABLE_VOICES["rachel"])
    
    # Get settings
    elevenlabs_settings = settings or ElevenLabsManager.get_default_settings().dict()
    
    return {
        "provider": "11labs",
        "voice_id": voice_id
    }

class ElevenLabsConfig(BaseModel):
    """Eleven Labs voice configuration"""
    model_config = {"protected_namespaces": ()}
    provider: str = "elevenlabs"
    voice_id: str = "rachel"
    model_id: str = "eleven_multilingual_v2"
    stability: float = 0.5
    similarity_boost: float = 0.5
    style: float = 0.0
    use_speaker_boost: bool = True

class ElevenLabsSettings(BaseModel):
    """Eleven Labs settings model"""
    model_config = {"protected_namespaces": ()}
    
    model_id: str = "eleven_multilingual_v2"
    stability: float = 0.5
    similarity_boost: float = 0.5
    style: float = 0.0
    use_speaker_boost: bool = True

class ElevenLabsManager:
    """Eleven Labs configuration manager"""
    
    # Popular Eleven Labs voices for restaurant assistants
    AVAILABLE_VOICES = {
        "rachel": ElevenLabsVoice(
            voice_id="rachel",
            name="Rachel",
            description="Warm, friendly, and professional female voice",
            language="en",
            gender="female"
        ),
        "domi": ElevenLabsVoice(
            voice_id="domi",
            name="Domi",
            description="Energetic and enthusiastic female voice",
            language="en",
            gender="female"
        ),
        "bella": ElevenLabsVoice(
            voice_id="bella",
            name="Bella",
            description="Sophisticated and elegant female voice",
            language="en",
            gender="female"
        ),
        "antoni": ElevenLabsVoice(
            voice_id="antoni",
            name="Antoni",
            description="Professional and confident male voice",
            language="en",
            gender="male"
        ),
        "elliot": ElevenLabsVoice(
            voice_id="elliot",
            name="Elliot",
            description="Friendly and approachable male voice",
            language="en",
            gender="male"
        ),
        "josh": ElevenLabsVoice(
            voice_id="josh",
            name="Josh",
            description="Casual and conversational male voice",
            language="en",
            gender="male"
        )
    }
    
    @classmethod
    def get_default_voice(cls) -> str:
        """Get default voice ID from environment or fallback"""
        return os.getenv("ELEVENLABS_VOICE_ID", "rachel")
    
    @classmethod
    def get_default_settings(cls) -> ElevenLabsSettings:
        """Get default Eleven Labs settings from environment"""
        return ElevenLabsSettings(
            model_id=os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"),
            stability=float(os.getenv("ELEVENLABS_STABILITY", "0.5")),
            similarity_boost=float(os.getenv("ELEVENLABS_SIMILARITY_BOOST", "0.5")),
            style=float(os.getenv("ELEVENLABS_STYLE", "0.0")),
            use_speaker_boost=os.getenv("ELEVENLABS_USE_SPEAKER_BOOST", "true").lower() == "true"
        )
    
    @classmethod
    def list_available_voices(cls) -> List[Dict[str, Any]]:
        """List all available voices with their details"""
        return [
            {
                "voice_id": voice.voice_id,
                "name": voice.name,
                "description": voice.description,
                "language": voice.language,
                "gender": voice.gender
            }
            for voice in cls.AVAILABLE_VOICES.values()
        ]
    
    @classmethod
    def validate_voice_id(cls, voice_id: str) -> bool:
        """Validate if voice ID is supported"""
        return voice_id in cls.AVAILABLE_VOICES
    
    @classmethod
    def get_voice_info(cls, voice_id: str) -> Optional[ElevenLabsVoice]:
        """Get voice information by ID"""
        return cls.AVAILABLE_VOICES.get(voice_id)

def create_restaurant_voice_config(
    restaurant_name: str,
    voice_id: Optional[str] = None,
    custom_settings: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create voice configuration optimized for restaurant reservations
    
    Args:
        restaurant_name: Name of the restaurant
        voice_id: Optional custom voice ID
        custom_settings: Optional custom voice settings
    
    Returns:
        Complete voice configuration for Vapi assistant
    """
    # Get base voice config
    voice_config = get_voice_config(voice_id, custom_settings)
    
    # Restaurant-optimized settings
    restaurant_settings = {
        "model_id": "eleven_multilingual_v2",  # Best for customer service
        "stability": 0.6,  # Slightly more stable for professional tone
        "similarity_boost": 0.7,  # Higher similarity for clarity
        "style": 0.3,  # Moderate style for friendly but professional
        "use_speaker_boost": True
    }
    
    # Merge with custom settings if provided
    if custom_settings:
        restaurant_settings.update(custom_settings)
    
    voice_config["elevenlabs_settings"] = restaurant_settings
    
    return voice_config

def get_voice_recommendation(restaurant_type: str = "general") -> str:
    """
    Get voice recommendation based on restaurant type
    
    Args:
        restaurant_type: Type of restaurant (fine_dining, casual, family, etc.)
    
    Returns:
        Recommended voice ID
    """
    recommendations = {
        "fine_dining": "bella",  # Elegant and sophisticated
        "casual": "rachel",  # Warm and friendly
        "family": "domi",  # Energetic and enthusiastic
        "sports_bar": "elliot",  # Friendly and approachable male voice
        "coffee_shop": "rachel",  # Warm and inviting
        "formal": "antoni",  # Professional and confident
        "general": "rachel"  # Good all-around choice
    }
    
    return recommendations.get(restaurant_type.lower(), "rachel")
