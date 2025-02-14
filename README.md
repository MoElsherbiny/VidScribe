# VidScribe

VidScribe is an advanced video transcription tool designed for content creators, educators, and researchers. It automates the process of converting video speech into text, making content more accessible and multilingual.

## 🚀 Features

- **Automated Speech Recognition (ASR)**: Converts speech into text using Google Speech Recognition.
- **Multi-Language Support**: Transcribes audio into both English and Arabic.
- **Subtitle Generation**: Outputs subtitles in `.srt` format with precise timestamps.
- **Batch Processing**: Processes multiple video files from a specified directory.
- **Error Handling & Logging**: Implements retry mechanisms and logs progress.
- **Custom Chunk Duration**: Splits audio into manageable segments for better accuracy.

---

## 🛠 Installation

### Prerequisites

- Ensure you have Python installed (Python 3.8+ recommended).
- Install FFmpeg (required for audio extraction). You can download it from [FFmpeg.org](https://ffmpeg.org/download.html) and ensure it's added to your system PATH.

### Install Dependencies

Run the following command to install the required packages:

```sh
pip install -r requirements.txt
```

Alternatively, manually install dependencies:

```sh
pip install numpy decorator imageio imageio-ffmpeg moviepy SpeechRecognition pydub
```

---

## 📌 Usage

### 1️⃣ Run the Script

Execute the script and provide a directory containing video files:

```sh
python vidscribe.py
```

You will be prompted to enter a directory path containing video files. If no path is provided, it defaults to:

```
D:\VIDSCRIBE
```

### 2️⃣ Processing Video Files

VidScribe automatically:

✅ Extracts audio from video files
✅ Splits audio into 30-second chunks
✅ Transcribes each chunk into English and Arabic
✅ Generates subtitles with timestamps
✅ Saves transcripts in a `transcripts/` folder

### 3️⃣ Output Files

For each video file, the following output files are generated:

- **`video_name_en.srt`** → English subtitles
- **`video_name_ar.srt`** → Arabic subtitles
- **`video_name_en.txt`** → Plain text transcript (English)
- **`video_name_ar.txt`** → Plain text transcript (Arabic)

## 📂 Example Output Structure

```
transcripts/
├── video1_en.srt
├── video1_ar.srt
├── video1_en.txt
├── video1_ar.txt
├── video2_en.srt
├── video2_ar.srt
├── video2_en.txt
├── video2_ar.txt
```

---

## 🤝 Contributing

Contributions are welcome! If you find any issues or have ideas for improvements, feel free to submit a pull request or open an issue.

---

## 📜 License

This project is owned by [Mohamed Elsherbiny]. All rights reserved.

---

💡 **VidScribe: Automate, Transcribe, and Simplify Your Content Creation!**
