from faster_whisper import WhisperModel
import subprocess
import sys
import os

def extract_audio(video_path, temp_audio="temp_audio.wav"):
    """Extracts a lightweight audio file for the AI to process fast"""
    print("Extracting audio track for AI analysis...")
    cmd = [
        'ffmpeg', '-i', video_path, 
        '-vn',  # no video
        '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',  # optimal whisper format
        '-y', temp_audio
    ]
    subprocess.run(cmd, capture_output=True)
    return temp_audio

def get_top_moments(video_path, num_clips=60):
    print(f"Loading AI Model to analyze: {video_path}\n")
    
    # These are the trigger words. Add your own Discord inside jokes here!
    keywords = [
        # English Hype
        "clip that", "clutch", "oh my god", "let's go", "crazy", "insane", "what was that", "no way",
        # Malay Hype / Vlog
        "gila", "mantap", "cantik", "terbaik", "rekod", "rakam ni", "bapak ah", "weyh", "fuh", "pandai"
    ]
    
    temp_audio = extract_audio(video_path)
    
    # Load model (using CPU for max compatibility)
    print("Loading Whisper AI... (this takes a few seconds)")
    # Using 'tiny' model for maximum speed during testing
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    
    print("\nScanning for English and Malay keywords...")
    print("-" * 50)
    
    # Transcribe the audio
    segments, info = model.transcribe(temp_audio, beam_size=5)
    
    moments = []
    
    for segment in segments:
        text = segment.text.lower()
        
        # Check if any keyword was spoken in this sentence
        for word in keywords:
            if word in text:
                print(f"[{segment.start:.1f}s -> {segment.end:.1f}s] Found '{word}': \"{segment.text.strip()}\"")
                moments.append(segment.start)
                break # Move to next sentence to avoid double counting
                
    # Cleanup temp file
    if os.path.exists(temp_audio):
        os.remove(temp_audio)
        
    # Group close moments (if you say 3 keywords in 10 seconds, only cut 1 clip)
    grouped = []
    if moments:
        grouped.append(moments[0])
        for time in moments[1:]:
            if time - grouped[-1] > 30:
                grouped.append(time)
                
    print("\n" + "="*50)
    print(f"Found {len(grouped)} unique hype moments.")
    
    # Return up to your requested number of clips
    return grouped[:num_clips]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python smart_finder.py <video_file>")
        sys.exit(1)
        
    video_path = sys.argv[1]
    get_top_moments(video_path, num_clips=60)
