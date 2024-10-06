import pytest
from unittest.mock import patch, MagicMock
from ..modules.utils import scrap_url, scrap_url_clean
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()


@pytest.mark.parametrize(
    "url",
    [
        "https://aider.chat/",
        "https://platform.openai.com/docs/guides/structured-outputs",
    ],
)
def test_scrap_url(url):
    if not os.getenv("FIRECRAWL_API_KEY"):
        pytest.skip("FIRECRAWL_API_KEY environment variable not set")

    result = scrap_url(url)

    print(result)

    assert isinstance(result, dict)
    assert "metadata" in result
    assert result["metadata"]["statusCode"] == 200


@pytest.mark.parametrize(
    "url",
    [
        "https://aider.chat/",
        "https://platform.openai.com/docs/guides/structured-outputs",
    ],
)
def test_scrap_url_clean(url):
    if not os.getenv("FIRECRAWL_API_KEY"):
        pytest.skip("FIRECRAWL_API_KEY environment variable not set")

    result = scrap_url_clean(url)

    print(result)

    assert isinstance(result, str)
    assert len(result) > 0
    assert "Error:" not in result
