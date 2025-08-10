#!/usr/bin/env python3
"""
Enhanced Voice Scam Shield Backend Setup Script
Installs dependencies and downloads required models for enhanced transcription and classification.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
import urllib.request
import zipfile
import tarfile

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def install_system_dependencies():
    """Install system-level audio dependencies"""
    system = platform.system().lower()
    print(f"🔍 Detected system: {system}")
    
    if system == "linux":
        # Ubuntu/Debian
        commands = [
            "sudo apt-get update",
            "sudo apt-get install -y python3-pyaudio portaudio19-dev python3-dev",
            "sudo apt-get install -y flac ffmpeg"
        ]
        for cmd in commands:
            run_command(cmd, f"Installing Linux dependency: {cmd}")
    
    elif system == "darwin":
        # macOS
        commands = [
            "brew install portaudio",
            "brew install flac",
            "brew install ffmpeg"
        ]
        for cmd in commands:
            run_command(cmd, f"Installing macOS dependency: {cmd}")
    
    elif system == "windows":
        print("⚠️ Windows detected. Please ensure you have:")
        print("  - Microsoft C++ Build Tools installed")
        print("  - FFmpeg installed and in PATH")
        print("  - PyAudio may need manual installation: pip install pipwin && pipwin install pyaudio")

def install_python_dependencies():
    """Install Python packages"""
    print("📦 Installing Python dependencies...")
    
    # Upgrade pip first
    run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip")
    
    # Install basic requirements
    run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installing requirements")
    
    # Try to install PyAudio separately (often problematic)
    if not run_command(f"{sys.executable} -m pip install pyaudio", "Installing PyAudio"):
        print("⚠️ PyAudio installation failed. You may need to install it manually.")
        if platform.system().lower() == "windows":
            print("Try: pip install pipwin && pipwin install pyaudio")

def download_vosk_model():
    """Download Vosk speech recognition model"""
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    model_url = "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip"
    model_file = models_dir / "vosk-model-en-us-0.22.zip"
    model_dir = models_dir / "vosk-model-en-us-0.22"
    
    if model_dir.exists():
        print("✅ Vosk model already downloaded")
        return True
    
    try:
        print("🔽 Downloading Vosk English model (large file, ~40MB)...")
        urllib.request.urlretrieve(model_url, model_file)
        print("✅ Vosk model downloaded")
        
        print("📂 Extracting Vosk model...")
        with zipfile.ZipFile(model_file, 'r') as zip_ref:
            zip_ref.extractall(models_dir)
        
        # Clean up zip file
        model_file.unlink()
        print("✅ Vosk model extracted successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to download Vosk model: {e}")
        print("⚠️ You may need to download manually from: https://alphacephei.com/vosk/models/")
        return False

def setup_nltk_data():
    """Download required NLTK data"""
    print("📚 Setting up NLTK data...")
    try:
        import nltk
        
        # Download required datasets quietly
        datasets = ['punkt', 'stopwords', 'vader_lexicon']
        for dataset in datasets:
            try:
                nltk.download(dataset, quiet=True)
                print(f"✅ Downloaded NLTK {dataset}")
            except Exception as e:
                print(f"⚠️ Failed to download NLTK {dataset}: {e}")
        
        return True
    except ImportError:
        print("⚠️ NLTK not installed, skipping NLTK data setup")
        return False

def create_env_template():
    """Create .env template file"""
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file already exists")
        return
    
    env_template = """# Voice Scam Shield Backend Configuration
# Copy this to .env and fill in your values

# OpenAI API Key (optional, for enhanced transcription/classification)
OPENAI_API_KEY=your_openai_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Audio Processing Settings
MAX_AUDIO_SIZE_MB=50
SUPPORTED_FORMATS=wav,mp3,flac,m4a,ogg

# Enhanced Features
ENABLE_REAL_TIME_TRANSCRIPTION=true
ENABLE_ML_CLASSIFICATION=true
TRANSCRIPTION_ENGINE=google  # Options: google, vosk, openai
CLASSIFICATION_ENGINE=enhanced  # Options: enhanced, openai, basic

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/voice_scam_shield.log
"""
    
    env_file.write_text(env_template)
    print("✅ Created .env template file")
    print("⚠️ Please edit .env file with your configuration")

def test_installation():
    """Test that key components work"""
    print("🧪 Testing installation...")
    
    # Test imports
    test_modules = [
        ("fastapi", "FastAPI"),
        ("pydub", "Audio processing"),
        ("numpy", "Numerical computing"),
        ("sklearn", "Machine learning (optional)"),
        ("speechrecognition", "Speech recognition (optional)"),
        ("nltk", "Natural language processing (optional)")
    ]
    
    for module, description in test_modules:
        try:
            __import__(module)
            print(f"✅ {description} - OK")
        except ImportError:
            print(f"⚠️ {description} - Not available (may be optional)")
    
    # Test enhanced modules
    try:
        sys.path.append(str(Path.cwd()))
        from real_time_transcriber import RealTimeTranscriber
        print("✅ Enhanced transcriber - OK")
    except Exception as e:
        print(f"⚠️ Enhanced transcriber - Error: {e}")
    
    try:
        from enhanced_fraud_classifier import EnhancedFraudClassifier
        print("✅ Enhanced classifier - OK")
    except Exception as e:
        print(f"⚠️ Enhanced classifier - Error: {e}")

def main():
    """Main setup function"""
    print("🚀 Voice Scam Shield Enhanced Backend Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    steps = [
        ("Installing system dependencies", install_system_dependencies),
        ("Installing Python dependencies", install_python_dependencies),
        ("Downloading Vosk model", download_vosk_model),
        ("Setting up NLTK data", setup_nltk_data),
        ("Creating environment template", create_env_template),
        ("Testing installation", test_installation)
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}")
        print("-" * 30)
        step_func()
    
    print("\n🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Edit .env file with your configuration")
    print("2. For OpenAI features, add your API key to .env")
    print("3. Start the server with: python main.py or uvicorn main:app --reload")
    print("\nNew endpoints available:")
    print("- POST /upload-audio-enhanced - Enhanced audio analysis")
    print("- POST /analyze-transcript - Analyze text with ML")
    print("- WebSocket /ws/live-transcription - Real-time analysis")
    print("- GET /health - Check system status")

if __name__ == "__main__":
    main()
