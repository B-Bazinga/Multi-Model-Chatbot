# Custom exceptions to handle errors better 
class SpeechToTextError(Exception):
    """Exception raised when speech to text conversion fails"""
    pass

class TextToSpeechError(Exception):
    """Exception raised when text to speech conversion fails"""
    pass

class LLMError(Exception):
    """Exception raised when LLM fails to generate a response"""
    pass

class TextToImageError(Exception):
    """Exception raised when text to image generation fails"""
    pass

class ImageToTextError(Exception):
    """Exception raised when image to text conversion fails"""
    pass

