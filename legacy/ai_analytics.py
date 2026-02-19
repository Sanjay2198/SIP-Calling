"""
AI Analytics for Call Recordings
- Speech-to-text transcription
- Call summarization
- Sentiment analysis
"""
import os
import wave
from datetime import datetime
from threading import Thread
from typing import Any, Dict, List, Optional, cast
import yaml

# Speech recognition
sr: Any
try:
    import speech_recognition as sr  # pyright: ignore[reportMissingImports,reportMissingModuleSource]
    SPEECH_AVAILABLE = True
except ImportError:
    print("  SpeechRecognition not installed. Run: pip install SpeechRecognition")
    SPEECH_AVAILABLE = False

# Transformers for NLP
pipeline: Any
try:
    from transformers import pipeline  # pyright: ignore[reportMissingImports,reportMissingModuleSource]
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("  Transformers not installed. Run: pip install transformers torch")
    TRANSFORMERS_AVAILABLE = False

from models import CallHistory, get_session


class AIAnalytics:
    """AI-powered call analytics"""
    
    def __init__(self, config_path='config.yaml'):
        """Initialize AI models"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.ai_config = self.config.get('ai', {})
        self.enabled = self.ai_config.get('enabled', False)
        
        if not self.enabled:
            print(" AI analytics disabled in config")
            return
        
        # Initialize models
        self.sentiment_analyzer: Any = None
        self.summarizer: Any = None
        
        if TRANSFORMERS_AVAILABLE:
            try:
                print(" Loading AI models...")
                
                if self.ai_config.get('sentiment_analysis', True):
                    self.sentiment_analyzer = pipeline(
                        "sentiment-analysis",
                        model="distilbert-base-uncased-finetuned-sst-2-english"
                    )
                
                if self.ai_config.get('call_summary', True):
                    try:
                        self.summarizer = pipeline(
                            "summarization",
                            model="facebook/bart-large-cnn"
                        )
                    except Exception as summary_error:
                        # Newer transformers builds may not expose the "summarization" alias.
                        print(f"  Summarization task unavailable ({summary_error}); trying text2text-generation")
                        self.summarizer = pipeline(
                            "text2text-generation",
                            model="facebook/bart-large-cnn"
                        )
                
                print(" AI models loaded successfully")
            except Exception as e:
                print(f"  Failed to load AI models: {e}")
    
    def transcribe_audio(self, audio_path: str) -> Optional[str]:
        """
        Transcribe audio file to text using Google Speech Recognition
        
        Args:
            audio_path: Path to WAV file
            
        Returns:
            str: Transcribed text or None
        """
        if not SPEECH_AVAILABLE:
            print(" Speech recognition not available")
            return None
        
        if not self.ai_config.get('transcription', True):
            return None
        
        try:
            recognizer = cast(Any, sr.Recognizer())
            
            # Load audio file
            with sr.AudioFile(audio_path) as source:
                audio_data = recognizer.record(source)
            
            # Recognize speech using Google Speech Recognition
            print(f" Transcribing: {audio_path}")
            text = cast(str, recognizer.recognize_google(audio_data))
            
            print(f" Transcription complete: {len(text)} characters")
            return text
            
        except sr.UnknownValueError:
            print("  Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f" Speech recognition service error: {e}")
            return None
        except Exception as e:
            print(f" Transcription error: {e}")
            return None
    
    def analyze_sentiment(self, text: str) -> Optional[str]:
        """
        Analyze sentiment of text
        
        Args:
            text: Text to analyze
            
        Returns:
            str: Sentiment label (positive/negative/neutral)
        """
        if not self.sentiment_analyzer or not text:
            return None
        
        try:
            # Truncate text if too long (model limit)
            text = text[:512]
            
            results = cast(List[Dict[str, Any]], self.sentiment_analyzer(text))
            if not results:
                return None

            first = results[0]
            label = first.get('label')
            score = first.get('score')
            if not isinstance(label, str) or not isinstance(score, (int, float)):
                return None

            sentiment = label.lower()
            confidence = float(score)
            
            print(f" Sentiment: {sentiment} ({confidence:.2%} confidence)")
            return f"{sentiment} ({confidence:.0%})"
            
        except Exception as e:
            print(f" Sentiment analysis error: {e}")
            return None
    
    def generate_summary(self, text: str) -> Optional[str]:
        """
        Generate summary of text
        
        Args:
            text: Text to summarize
            
        Returns:
            str: Summary text
        """
        if not self.summarizer or not text:
            return None
        
        try:
            # Summarization works best with at least 50 words
            if len(text.split()) < 50:
                return "Call too short for summary"
            
            # Truncate if too long
            text = text[:1024]
            
            summaries = cast(
                List[Dict[str, Any]],
                self.summarizer(
                text,
                max_length=130,
                min_length=30,
                do_sample=False
                ),
            )
            if not summaries:
                return None

            summary_item = summaries[0]
            if not isinstance(summary_item, dict):
                return None
            summary_text = summary_item.get('summary_text')
            if not isinstance(summary_text, str):
                generated_text = summary_item.get('generated_text')
                if isinstance(generated_text, str):
                    summary_text = generated_text
            if not isinstance(summary_text, str):
                return None
            summary = summary_text.strip()
            
            print(f" Summary generated: {len(summary)} characters")
            return summary
            
        except Exception as e:
            print(f" Summary generation error: {e}")
            return None
    
    def process_call_recording(self, call_id: int) -> None:
        """
        Process a call recording with AI analytics
        Background task that updates the database
        
        Args:
            call_id: ID of call in database
        """
        if not self.enabled:
            return
        
        print(f" Processing call {call_id} with AI...")
        
        session = get_session()
        try:
            call = cast(Any, session.query(CallHistory).filter(CallHistory.id == call_id).first())
            recording_path = cast(Optional[str], getattr(call, "recording_path", None)) if call else None
            
            if not call or not recording_path:
                print(f" Call {call_id} has no recording")
                return
            
            if not os.path.exists(recording_path):
                print(f" Recording file not found: {recording_path}")
                return
            
            # Step 1: Transcribe audio
            transcript = self.transcribe_audio(recording_path)
            if transcript:
                call.transcript = transcript
                session.commit()
                
                # Step 2: Analyze sentiment
                sentiment = self.analyze_sentiment(transcript)
                if sentiment:
                    call.sentiment = sentiment
                    session.commit()
                
                # Step 3: Generate summary
                summary = self.generate_summary(transcript)
                if summary:
                    call.summary = summary
                    session.commit()
                
                print(f" Call {call_id} processing complete")
            else:
                print(f"  No transcript available for call {call_id}")
                
        except Exception as e:
            print(f" Error processing call {call_id}: {e}")
        finally:
            session.close()
    
    def process_call_async(self, call_id: int) -> None:
        """Process call in background thread"""
        thread = Thread(target=self.process_call_recording, args=(call_id,))
        thread.daemon = True
        thread.start()


# Global instance
ai_analytics: Optional[AIAnalytics] = None

def get_ai_analytics() -> AIAnalytics:
    """Get or create AI analytics instance"""
    global ai_analytics
    if ai_analytics is None:
        ai_analytics = AIAnalytics()
    return ai_analytics


if __name__ == '__main__':
    # Test AI analytics
    print("=== Testing AI Analytics ===\n")
    
    ai = AIAnalytics()
    
    # Test sentiment
    if ai.sentiment_analyzer:
        test_texts = [
            "This was a great call! Very productive and helpful.",
            "I'm very disappointed with the service quality.",
            "The call was okay, nothing special."
        ]
        
        for text in test_texts:
            print(f"Text: {text}")
            sentiment = ai.analyze_sentiment(text)
            print(f"Sentiment: {sentiment}\n")
    
    # Test summarization
    if ai.summarizer:
        long_text = """
        During our call today, we discussed the implementation of the new SIP softphone
        client project. The client will be built using Python and the PJSUA2 library.
        We agreed to include features like call recording, web-based UI control, and
        AI-powered analytics for call transcription and sentiment analysis. The project
        timeline is approximately 2 weeks for the initial version, with additional time
        for testing and refinement. We also discussed the importance of having a clean,
        modern user interface with glassmorphism design principles.
        """
        
        print(f"Original text ({len(long_text)} chars):\n{long_text}")
        summary = ai.generate_summary(long_text)
        print(f"\nSummary ({len(summary) if summary else 0} chars):\n{summary}")
