from youtube_transcript_api import YouTubeTranscriptApi
from transformers import Pipeline, pipeline
import re
import requests
import torch
import html
from typing import Optional, List


MODEL_NAME: str = 'facebook/bart-large-cnn'


def get_youtube_title(url: str) -> Optional[str]:
    """Get YouTube video title from an URL"""
    try:
        response = requests.get(url)
        title = re.search(r'<title>(.*?) - YouTube</title>', response.text)
        return html.unescape(title.group(1)) if title else None
    except Exception as e:
        print(f"Error getting video title {e}")
        return None


def get_youtube_video_channel_name(url: str) -> Optional[str]:
    """Get the YouTube channel name from a video URL."""
    try:
        response = requests.get(url)

        channel_name = re.search(r'"channelName":"(.*?)"', response.text)
        if channel_name:
            decoded_name = html.unescape(channel_name.group(1))
            return decoded_name if decoded_name else 'unknown'

        return 'unknown'

    except Exception as e:
        print(f"Error getting channel name: {e}")
        return None


def extract_video_id(youtube_url: str) -> Optional[str]:
    """Extract video ID from YouTube URL"""
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, youtube_url)
    return match.group(1) if match else None


def get_transcript(video_id: str) -> Optional[str]:
    """Get video transcript using YouTube Transcript API"""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = ' '.join([item['text'] for item in transcript_list])
        return transcript
    except Exception as e:
        return str(e)


def get_summarizer(model_name: str = MODEL_NAME) -> Optional[Pipeline]:
    """Initialize the summarization model"""
    try:
        summarizer = pipeline(
            "summarization",
            model=model_name,
            device=0 if torch.cuda.is_available() else "cpu"
        )
        return summarizer
    except Exception as e:
        print(f"Error loading model: {e}")
        return None


def text_chunking(text: str, max_chunk_length: int = 1024, overlap: int = 200) -> List[str]:
    """Create overlapping chunks to preserve context between segments."""
    chunks: List[str] = []
    for i in range(0, len(text), max_chunk_length - overlap):
        chunk = text[i:i + max_chunk_length]
        chunks.append(chunk)
    return chunks


def summarize_text(text: str, max_length: int = 50, model_name: str = MODEL_NAME) -> str:
    """Summarize text using the specified model"""
    summarizer = get_summarizer(model_name)
    if not summarizer:
        return "Error: Could not load summarization model"

    chunks = text_chunking(text=text)

    summaries: List[str] = []
    for chunk in chunks:
        try:
            summary = summarizer(chunk, max_length=max_length, min_length=15, do_sample=False)[
                0]['summary_text']
            summaries.append(summary)
        except Exception as e:
            print(f"Error summarizing chunk: {e}")
            continue

    return ' '.join(summaries)
