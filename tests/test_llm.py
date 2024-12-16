import pytest
import re
from unittest.mock import patch, MagicMock
from typing import List, Dict, Any

from summ.llm import (
    get_youtube_title,
    get_youtube_video_channel_name,
    extract_video_id,
    get_transcript,
    get_summarizer,
    text_chunking,
    summarize_text,
    MODEL_NAME
)


def test_get_youtube_title_valid() -> None:
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.text = '<title>Test Video Title - YouTube</title>'
        mock_get.return_value = mock_response

        title = get_youtube_title('https://youtube.com/watch?v=test')
        assert title == 'Test Video Title'


def test_get_youtube_title_error() -> None:
    with patch('requests.get', side_effect=Exception('Network Error')):
        title = get_youtube_title('https://youtube.com/watch?v=test')
        assert title is None


def test_get_youtube_video_channel_name_valid() -> None:
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.text = '"channelName":"Test Channel"'
        mock_get.return_value = mock_response

        channel_name = get_youtube_video_channel_name(
            'https://youtube.com/watch?v=test')
        assert channel_name == 'Test Channel'


def test_get_youtube_video_channel_name_error() -> None:
    with patch('requests.get', side_effect=Exception('Network Error')):
        channel_name = get_youtube_video_channel_name(
            'https://youtube.com/watch?v=test')
        assert channel_name is None


def test_get_youtube_video_channel_name_empty() -> None:
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.text = ''
        mock_get.return_value = mock_response

        channel_name = get_youtube_video_channel_name(
            'https://youtube.com/watch?v=test')
        assert channel_name == 'unknown'


@pytest.mark.parametrize('url,expected_id', [
    ('https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'dQw4w9WgXcQ'),
    ('https://youtu.be/dQw4w9WgXcQ', 'dQw4w9WgXcQ'),
    ('https://www.youtube.com/embed/dQw4w9WgXcQ', 'dQw4w9WgXcQ'),
])
def test_extract_video_id_valid(url: str, expected_id: str) -> None:
    video_id = extract_video_id(url)
    assert video_id == expected_id


def test_extract_video_id_invalid() -> None:
    video_id = extract_video_id('invalid_url')
    assert video_id is None


def test_get_transcript_success(mocker: Any) -> None:
    mock_transcript = [
        {'text': 'Hello'},
        {'text': 'World'},
    ]
    mocker.patch('youtube_transcript_api.YouTubeTranscriptApi.get_transcript',
                 return_value=mock_transcript)

    transcript = get_transcript('test_video_id')
    assert transcript == 'Hello World'


def test_get_transcript_error(mocker: Any) -> None:
    mocker.patch('youtube_transcript_api.YouTubeTranscriptApi.get_transcript',
                 side_effect=Exception('Transcript not available'))

    transcript = get_transcript('test_video_id')
    assert 'Transcript not available' in transcript


def test_get_summarizer_returns_pipeline(mocker: Any) -> None:
    mocker.patch('torch.cuda.is_available', return_value=False)

    mock_pipeline = MagicMock()
    mocker.patch('transformers.pipeline', return_value=mock_pipeline)

    summarizer = get_summarizer()
    assert summarizer is not None


def test_get_summarizer_exception(mocker: Any) -> None:
    mocker.patch('torch.cuda.is_available', return_value=False)

    mocker.patch('transformers.pipeline',
                 side_effect=Exception("Model loading failed"))

    summarizer = get_summarizer(model_name="invalid_model")

    assert summarizer is None


def test_text_chunking() -> None:
    long_text = 'a' * 2000
    chunks = text_chunking(long_text)

    assert len(chunks) > 1
    assert all(len(chunk) <= 1024 for chunk in chunks)
    assert len(set(chunks)) > 1


def test_summarize_text_success(mocker: Any) -> None:
    mock_summarizer = MagicMock()
    mock_summarizer.return_value = [{'summary_text': 'Summary'}]

    mocker.patch('summ.llm.get_summarizer', return_value=mock_summarizer)

    text = 'a' * 2000
    summary = summarize_text(text)

    assert 'Summary' in summary


def test_summarize_text_model_error(mocker: Any) -> None:
    mocker.patch('summ.llm.get_summarizer', return_value=None)

    text = 'Test text'
    summary = summarize_text(text)

    assert summary == "Error: Could not load summarization model"


def test_summarize_text_chunk_exception(mocker: Any) -> None:
    mock_summarizer = MagicMock()
    mocker.patch('summ.llm.get_summarizer', return_value=mock_summarizer)
    mocker.patch('summ.llm.text_chunking',
                 return_value=['test chunk'])

    mock_summarizer.side_effect = Exception("Summarization failed")

    with patch('builtins.print') as mock_print:
        result = summarize_text("Some test text")

        mock_summarizer.assert_called_once_with(
            'test chunk',
            max_length=100,
            min_length=30,
            do_sample=False
        )

        mock_print.assert_called_once_with(
            "Error summarizing chunk: Summarization failed"
        )

        assert result == ""
