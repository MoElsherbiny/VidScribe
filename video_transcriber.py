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
from pydub import AudioSegment
import speech_recognition as sr

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_environment():
    """Set up the Python environment."""
    pass  # No specific setup needed for this version  To install Requirement  pip install -r requirements.txt

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

def transcribe_audio_chunk(recognizer, chunk_path, language="en-US"):
    """Transcribe a single audio chunk with retry logic"""
    max_retries = 3
    retry_delay = 5
    chunk_name = os.path.basename(chunk_path)

    for attempt in range(max_retries):
        try:
            with sr.AudioFile(chunk_path) as source:
                audio = recognizer.record(source)
                result = recognizer.recognize_google(
                    audio,
                    language=language,
                    show_all=False  # Changed to False to get direct transcript
                )
                logging.info(f"Successfully transcribed {chunk_name}")
                return result  # Returns the text directly
        except sr.UnknownValueError:
            logging.warning(f"Chunk {chunk_name}: Speech not recognized")
            return ""
        except Exception as e:
            if attempt < max_retries - 1:
                logging.warning(f"Chunk {chunk_name}: Attempt {attempt + 1} failed ({str(e)}), retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logging.error(f"Chunk {chunk_name}: Failed after {max_retries} attempts: {str(e)}")
                return ""

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
        # Create output directory
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        # Extract audio
        logging.info(f"Extracting audio from video: {video_path}")
        import moviepy.editor as mp
        clip = mp.VideoFileClip(str(video_path))
        audio_path = output_dir / f"{Path(video_path).stem}_audio.wav"
        clip.audio.write_audiofile(str(audio_path), codec='pcm_s16le', ffmpeg_params=['-ac', '2', '-ar', '44100'])
        clip.close()

        # Split audio into chunks
        logging.info("Splitting audio into chunks...")
        chunks = split_audio(str(audio_path))

        # Initialize speech recognizer
        import speech_recognition as sr
        r = sr.Recognizer()

        # Process chunks for English
        logging.info(f"Transcribing {len(chunks)} chunks to English...")
        en_results = []
        for i, chunk_path in enumerate(chunks, 1):
            logging.info(f"Processing English chunk {i}/{len(chunks)}")
            result = transcribe_audio_chunk(r, chunk_path, "en-US")
            en_results.append(result)
            time.sleep(2)  # Increased rate limiting

        # Process chunks for Arabic
        logging.info(f"Transcribing {len(chunks)} chunks to Arabic...")
        ar_results = []
        for i, chunk_path in enumerate(chunks, 1):
            logging.info(f"Processing Arabic chunk {i}/{len(chunks)}")
            result = transcribe_audio_chunk(r, chunk_path, "ar-AR")
            ar_results.append(result)
            time.sleep(2)  # Increased rate limiting

        # Merge results with debug logging
        logging.info("Merging English transcription chunks...")
        result_en = merge_transcriptions(en_results, "en-US")
        logging.debug(f"English merge result: {result_en}")

        logging.info("Merging Arabic transcription chunks...")
        result_ar = merge_transcriptions(ar_results, "ar-AR")
        logging.debug(f"Arabic merge result: {result_ar}")

        # Save transcripts with timestamps
        success = False
        if result_en and result_en['result']:
            en_srt_path = output_dir / f"{Path(video_path).stem}_en.srt"
            with open(en_srt_path, 'w', encoding='utf-8') as f:
                f.write(create_srt_content(result_en['result']))

            # Also save plain text version
            en_txt_path = output_dir / f"{Path(video_path).stem}_en.txt"
            with open(en_txt_path, 'w', encoding='utf-8') as f:
                f.write(' '.join(r['text'] for r in result_en['result']))

            logging.info(f"Saved English transcripts to {en_srt_path} and {en_txt_path}")
            success = True

        if result_ar and result_ar['result']:
            ar_srt_path = output_dir / f"{Path(video_path).stem}_ar.srt"
            with open(ar_srt_path, 'w', encoding='utf-8') as f:
                f.write(create_srt_content(result_ar['result']))

            # Also save plain text version
            ar_txt_path = output_dir / f"{Path(video_path).stem}_ar.txt"
            with open(ar_txt_path, 'w', encoding='utf-8') as f:
                f.write(' '.join(r['text'] for r in result_ar['result']))

            logging.info(f"Saved Arabic transcripts to {ar_srt_path} and {ar_txt_path}")
            success = True

        # Clean up temporary files
        os.remove(audio_path)
        for chunk in chunks:
            try:
                os.remove(chunk)
            except:
                pass

        if success:
            logging.info(f"Transcripts saved to: {output_dir}")
            return True
        else:
            logging.error("No valid transcriptions generated")
            return False

    except Exception as e:
        logging.error(f"Error during transcript extraction: {str(e)}")
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
    default_dir = r"D:\VIDSCRIBE"
    while True:
        dir_path = input(f"Enter directory path (press Enter to use default: {default_dir}): ").strip()
        if not dir_path:
            dir_path = default_dir
        if os.path.isdir(dir_path):
            break
        logging.error("Directory not found. Please try again.")

    logging.info(f"Processing videos in directory: {dir_path}")
    process_directory(dir_path)
