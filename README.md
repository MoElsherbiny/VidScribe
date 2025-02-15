# VidScribe Installation & Usage Guide

VidScribe is an advanced video transcription tool designed for content creators, educators, and researchers. It automates the process of converting video speech into text, making content more accessible and multilingual.

---

## 🚀 Features

- **Automated Speech Recognition (ASR)**: Converts speech into text using Google Speech Recognition.
- **Multi-Language Support**: Transcribes audio into both English and Arabic.
- **Subtitle Generation**: Outputs subtitles in `.srt` format with precise timestamps.
- **Batch Processing**: Processes multiple video files from a specified directory.
- **Error Handling & Logging**: Implements retry mechanisms and logs progress.
- **Custom Chunk Duration**: Splits audio into manageable segments for better accuracy.

---

## 💻 Understanding Virtual Machines (VMs)

A **Virtual Machine (VM)** is a software-based emulation of a physical computer that runs an operating system independently of the host machine.

### ✅ Benefits of Using a Virtual Machine:

- **Isolation**: Runs applications in a sandboxed environment, preventing conflicts with system files.
- **Portability**: Can be easily moved between different machines or cloud environments.
- **Multiple OS Support**: Allows running Windows, Linux, or macOS on a single device.
- **Development & Testing**: Ideal for testing software in different environments without modifying the host OS.
- **Security**: Provides a secure space to execute potentially harmful programs.

Using a VM for VidScribe ensures a consistent and reproducible environment, avoiding dependency conflicts that may arise on different operating systems.

---

## 🛠 Installation

### 1️⃣ Prerequisites

Before installing VidScribe, ensure you have the following:

- **Python 3.8+** installed. Download from [Python.org](https://www.python.org/downloads/).
- **FFmpeg** installed and added to your system PATH. Download it from [FFmpeg.org](https://ffmpeg.org/download.html).

To verify your installation, run:

```sh
python --version
ffmpeg -version
```

### 2️⃣ Clone the Repository

```sh
git clone https://github.com/MoElsherbiny/VidScribe.git
cd VidScribe
```

### 3️⃣ Set Up a Virtual Environment (Recommended)

A virtual environment isolates Python dependencies for this project, preventing conflicts with system-wide packages.

```sh
python -m venv venv
source venv/bin/activate  # For macOS/Linux
source venv/Scripts/activate    # For Windows
```

### 4️⃣ Install Dependencies

```sh
pip install -r requirements.txt
```

Alternatively, manually install the dependencies:

```sh
pip install numpy decorator imageio imageio-ffmpeg moviepy SpeechRecognition pydub
```

---

## 📌 Usage

### 1️⃣ Run the Script

To start VidScribe, execute the following command:

```sh
python vidscribe.py
```

You will be prompted to enter a directory containing video files. If no path is provided, it defaults to:

```
D:\VIDSCRIBE
```

### 2️⃣ Processing Video Files

VidScribe will automatically:

✅ Extract audio from video files\
✅ Split audio into 30-second chunks\
✅ Transcribe each chunk into English and Arabic\
✅ Generate subtitles with timestamps\
✅ Save transcripts in the `transcripts/` folder

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

## 📝 Code Explanation

VidScribe consists of several key components:

### 1️⃣ **Audio Extraction (FFmpeg)**

The script extracts audio from video files using FFmpeg:

```python
subprocess.run(["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", audio_path])
```

### 2️⃣ **Audio Splitting**

Since speech recognition works better with smaller segments, the script divides audio into 30-second chunks:

```python
chunk = audio[start_time:end_time]
chunk.export(chunk_path, format="wav")
```

### 3️⃣ **Speech Recognition**

Google Speech Recognition API is used to transcribe the chunks:

```python
text = recognizer.recognize_google(audio, language="en")
```

For Arabic transcription:

```python
text_ar = recognizer.recognize_google(audio, language="ar")
```

### 4️⃣ **Subtitle Generation**

Each transcribed text is converted into an SRT subtitle format:

```python
subtitle_file.write(f"{index}\n{start} --> {end}\n{text}\n\n")
```

---

## ❗ Troubleshooting

### 1️⃣ FFmpeg Not Found

Ensure FFmpeg is installed and added to your system PATH:

- **Windows**: Add the FFmpeg `bin` folder to `Environment Variables > System PATH`.
- **Mac/Linux**: Install via Homebrew: `brew install ffmpeg`.

### 2️⃣ Permission Errors

If you encounter permission errors, try running the script with administrative privileges:

```sh
sudo python vidscribe.py  # Mac/Linux
python vidscribe.py       # Windows (Run as Administrator)
```

### 3️⃣ Missing Dependencies

Reinstall dependencies:

```sh
pip install --upgrade -r requirements.txt
```

---

## 🤝 Contributing

We welcome contributions of all kinds! To contribute to VidScribe, follow these steps:

### 1️⃣ Fork the Repository

Click the **Fork** button at the top of the [GitHub repository](https://github.com/MoElsherbiny/VidScribe) to create your copy.

### 2️⃣ Clone Your Fork

```sh
git clone https://github.com/MoElsherbiny/VidScribe
cd VidScribe
```

### 3️⃣ Create a New Branch

```sh
git checkout -b feature-or-bugfix-name
```

### 4️⃣ Make Your Changes & Commit

Modify the necessary files, then commit your changes:

```sh
git add .
git commit -m "Describe your changes here"
```

### 5️⃣ Push Your Branch & Create a Pull Request

```sh
git push origin feature-or-bugfix-name
```

Go to GitHub and create a pull request from your branch to the `main` branch of the original repository.

🚀 Thank you for contributing! Your efforts help make VidScribe better for everyone.

---

## 📜 License

This project is owned by **Mohamed Elsherbiny**. All rights reserved.

---

💡 **VidScribe: Automate, Transcribe, and Simplify Your Content Creation!**
