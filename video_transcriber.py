import os
import sys
import venv
from pathlib import Path
import subprocess
import time
import logging
import site
import glob
from datetime import timedelta
import math
import moviepy.editor as mp
from pydub import AudioSegment
import speech_recognition as sr
from pydub.silence import detect_nonsilent
import langdetect
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_environment():
    """Set up the Python environment."""
    pass  # No specific setup needed for this version

def run_pip_command(cmd, desc):
    logging.info(f"{desc}...")
    try:
        if cmd[0] != sys.executable:
            cmd = [sys.executable, "-m", "pip"] + cmd[2:]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"Error: {result.stderr}")
            return False
        logging.info(result.stdout)
        return True
    except Exception as e:
        logging.error(f"Error during {desc}: {str(e)}")
        return False

def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format"""
    td = timedelta(seconds=seconds)
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    seconds = td.seconds % 60
    milliseconds = td.microseconds // 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def create_srt_content(segments):
    """Create SRT formatted content from segments"""
    srt_content = ""
    for i, segment in enumerate(segments, 1):
        start_time = format_timestamp(segment.get('start', 0))
        end_time = format_timestamp(segment.get('end', 0))
        text = segment.get('text', '')
        srt_content += f"{i}\n{start_time} --> {end_time}\n{text}\n\n"
    return srt_content

def verify_installation():
    setup_environment()

    if not run_pip_command(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
        "Upgrading pip"
    ):
        logging.warning("Pip upgrade failed, continuing with existing version")

    if not run_pip_command(
        [sys.executable, "-m", "pip", "install", "setuptools", "wheel"],
        "Installing setuptools and wheel"
    ):
        logging.error("Failed to install setuptools and wheel. Exiting.")
        return False

    packages = [
        ("numpy", "2.2.3"),
        ("decorator", "5.1.1"),
        ("imageio", "2.31.1"),
        ("imageio-ffmpeg", "0.4.8"),
        ("moviepy", "1.0.3"),
        ("SpeechRecognition", "3.10.0")
    ]

    for package, version in packages:
        cmd = [sys.executable, "-m", "pip", "install", f"{package}=={version}"]
        if not run_pip_command(cmd, f"Installing {package}"):
            logging.error(f"Failed to install {package}. Please install it manually.")
            return False

    try:
        import numpy
        import decorator
        import imageio
        import imageio_ffmpeg
        import moviepy.editor
        import speech_recognition as sr
        logging.info("All required packages imported successfully")
        return True
    except ImportError as e:
        logging.error(f"Error importing modules: {e}")
        return False

def split_audio(audio_path, chunk_duration=30):
    """Split audio file into smaller chunks"""
    audio = AudioSegment.from_wav(audio_path)
    chunks = []
    total_duration = len(audio) / 1000  # Duration in seconds

    logging.info(f"Total audio duration: {total_duration:.2f} seconds")
    logging.info(f"Splitting into {chunk_duration}-second chunks...")

    # Calculate number of chunks
    chunk_length_ms = chunk_duration * 1000  # Convert to milliseconds
    total_chunks = math.ceil(len(audio) / chunk_length_ms)

    for i in range(0, len(audio), chunk_length_ms):
        chunk = audio[i:i + chunk_length_ms]
        chunk_path = f"{audio_path}.chunk{len(chunks)}.wav"
        chunk.export(chunk_path, format="wav")
        chunks.append(chunk_path)
        logging.info(f"Created chunk {len(chunks)}/{total_chunks}")

    return chunks

def detect_sentences(audio_segment, min_silence_len=500, silence_thresh=-40):
    """Detect sentence boundaries using silence detection"""
    # Get non-silent chunks
    nonsilent_chunks = detect_nonsilent(
        audio_segment,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh
    )

    # Convert chunks to time ranges
    sentences = []
    for start, end in nonsilent_chunks:
        # Convert milliseconds to seconds
        sentences.append({
            'start': start / 1000.0,
            'end': end / 1000.0,
            'duration': (end - start) / 1000.0
        })

    return sentences

def transcribe_audio_chunk(recognizer, audio_segment, language=None):
    """Transcribe an audio segment with automatic language detection"""
    try:
        # Convert audio segment to raw data
        audio_data = audio_segment.raw_data
        # Create AudioData object
        audio = sr.AudioData(
            audio_data,
            audio_segment.frame_rate,
            audio_segment.sample_width
        )

        # Get transcription
        text = recognizer.recognize_google(audio, language=language)

        # Detect language if not specified
        if not language:
            try:
                language = langdetect.detect(text)
            except:
                language = 'en'

        return text.strip(), language
    except Exception as e:
        logging.error(f"Transcription error: {str(e)}")
        return "", language

def merge_transcriptions(chunk_results, language):
    """Merge transcription chunks into a single result"""
    merged_segments = []
    chunk_duration = 30  # seconds per chunk

    for chunk_idx, text in enumerate(chunk_results):
        if text and isinstance(text, str):
            segment = {
                'text': text.strip(),
                'start': chunk_idx * chunk_duration,
                'end': (chunk_idx + 1) * chunk_duration
            }
            merged_segments.append(segment)
            logging.debug(f"Added segment: {segment}")

    if not merged_segments:
        logging.warning(f"No valid segments found for {language}")
        return None

    logging.info(f"Successfully merged {len(merged_segments)} segments for {language}")
    return {'result': merged_segments}

def extract_transcript(video_path, output_dir):
    try:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        # Load video
        logging.info(f"Processing video: {video_path}")
        video = mp.VideoFileClip(str(video_path))

        # Extract audio to temporary WAV file
        logging.info("Extracting audio...")
        temp_audio_path = output_dir / f"temp_{Path(video_path).stem}.wav"
        video.audio.write_audiofile(
            str(temp_audio_path),
            fps=44100,
            nbytes=2,
            codec='pcm_s16le',
            ffmpeg_params=["-ac", "1"]  # Force mono audio
        )
        video.close()

        # Load the audio file with pydub
        audio_segment = AudioSegment.from_wav(str(temp_audio_path))

        # Initialize recognizer
        r = sr.Recognizer()
        r.energy_threshold = 300
        r.dynamic_energy_threshold = True

        # First detect language using a small sample
        detected_language = 'en-US'  # Default to English
        try:
            sample_duration = min(10000, len(audio_segment))  # Use first 10 seconds or full audio
            sample = audio_segment[:sample_duration]
            sample_path = output_dir / "temp_sample.wav"
            sample.export(str(sample_path), format="wav")

            with sr.AudioFile(str(sample_path)) as source:
                audio = r.record(source)
                sample_text = r.recognize_google(audio)
                detected_language = langdetect.detect(sample_text)
                if detected_language.startswith('en'):
                    detected_language = 'en-US'
                elif detected_language.startswith('ar'):
                    detected_language = 'ar-AR'
                logging.info(f"Detected language: {detected_language}")

            sample_path.unlink(missing_ok=True)
        except Exception as e:
            logging.warning(f"Language detection failed: {str(e)}. Using default: en-US")

        # Process audio in chunks
        chunk_duration = 10000  # 10 seconds
        transcription = []

        for i, start in enumerate(range(0, len(audio_segment), chunk_duration)):
            end = start + chunk_duration
            chunk = audio_segment[start:end]

            # Export chunk
            chunk_path = output_dir / f"temp_chunk_{i}.wav"
            chunk.export(str(chunk_path), format="wav")

            try:
                with sr.AudioFile(str(chunk_path)) as source:
                    audio = r.record(source)
                    text = r.recognize_google(audio, language=detected_language)
                    if text:
                        transcription.append({
                            'index': len(transcription) + 1,
                            'start': start / 1000.0,  # Convert to seconds
                            'end': end / 1000.0,
                            'text': text.strip()
                        })
                        logging.info(f"Transcribed chunk {i+1}: {text[:50]}...")
            except Exception as e:
                logging.warning(f"Failed to transcribe chunk {i+1}: {str(e)}")
            finally:
                chunk_path.unlink(missing_ok=True)

            time.sleep(0.5)  # Rate limiting

        # Clean up
        temp_audio_path.unlink(missing_ok=True)

        # Save transcription
        if transcription:
            srt_path = output_dir / f"{Path(video_path).stem}.srt"
            with open(srt_path, 'w', encoding='utf-8') as f:
                for segment in transcription:
                    f.write(f"{segment['index']}\n")
                    f.write(f"{format_timestamp(segment['start'])} --> {format_timestamp(segment['end'])}\n")
                    f.write(f"{segment['text']}\n\n")

            logging.info(f"Saved transcript to {srt_path}")
            return True

        logging.warning("No transcription segments were generated")
        return False

    except Exception as e:
        logging.error(f"Error during transcript extraction: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return False

def process_directory(directory_path):
    """Process all video files in the given directory"""
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv')
    output_dir = Path(directory_path) / "transcripts"

    # Get all video files in directory
    video_files = []
    for ext in video_extensions:
        video_files.extend(glob.glob(str(Path(directory_path) / f"*{ext}")))

    if not video_files:
        logging.error(f"No video files found in {directory_path}")
        return False

    # Process each video file
    for video_file in video_files:
        logging.info(f"Processing video: {video_file}")
        if not extract_transcript(video_file, output_dir):
            logging.error(f"Failed to process {video_file}")
        else:
            logging.info(f"Successfully processed {video_file}")

if __name__ == "__main__":
    if not verify_installation():
        logging.error("Installation verification failed. Exiting script.")
        sys.exit(1)

    # Get directory path
    default_dir = r"D:\transcript\Text-from-Video"
    while True:
        dir_path = input(f"Enter directory path (press Enter to use default: {default_dir}): ").strip()
        if not dir_path:
            dir_path = default_dir
        if os.path.isdir(dir_path):
            break
        logging.error("Directory not found. Please try again.")

    logging.info(f"Processing videos in directory: {dir_path}")
    process_directory(dir_path)
