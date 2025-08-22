from subtitle_extractor import extract_subtitles
import pytest
import time


class TestSubtitleExtractor:
    @pytest.mark.parametrize("url,expected_min_length", [
        (
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            2000
        ),
        (
            "https://www.youtube.com/watch?v=jNQXAC9IVRw",
            200
        ),
        (
            "https://www.youtube.com/watch?v=wt9aZHrghK4",
            200
        ),
        (
            "https://youtube.com/shorts/8Mnfp0yjfFI?si=i3w9cyC1-dKQU1Qm",
            1200
        ),
        (
            "https://youtu.be/qF3ua2_Cx0o",
            20000
        ),
        (
            "https://www.youtube.com/watch?v=XuMi_jPBPbM",
            35000
        ),
    ])
    def test_extract_subtitles(self, url, expected_min_length):
        start_time = time.time()
        result = extract_subtitles(url, 'en')
        test_time = time.time() - start_time

        print(f"\nTest: {url}")
        print(f"Length: {len(result)} (min: {expected_min_length})")
        print(f"Time: {test_time:.2f}s")

        assert isinstance(result, str)
        assert len(result) >= expected_min_length


def test_invalid_url():
    result = extract_subtitles("invalid_url", 'en')
    assert result == ""
