"""
LINE Messaging API Client
Plain requests implementation (no LINE SDK dependency)
"""
import requests
from typing import Dict, Any, List, Optional
from .settings import LINE_CHANNEL_ACCESS_TOKEN


LINE_API_BASE = "https://api.line.me/v2/bot"


def _get_headers() -> Dict[str, str]:
    """Get LINE API headers"""
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }


def push_text_message(user_id: str, text: str) -> Dict[str, Any]:
    """
    Push text message to user

    Args:
        user_id: LINE user ID
        text: Message text

    Returns:
        Response dict with success status
    """
    url = f"{LINE_API_BASE}/message/push"
    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": text
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, headers=_get_headers())
        response.raise_for_status()

        return {
            "success": True,
            "status_code": response.status_code
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
        }


LINE_MAX_CHARS = 4900  # LINE limit is 5000, keep buffer


def _split_text(text: str, max_len: int = LINE_MAX_CHARS) -> list:
    """Split text into LINE-compatible chunks (<= 5000 chars each, max 5 messages)."""
    if len(text) <= max_len:
        return [text]
    chunks = []
    while text and len(chunks) < 5:
        if len(text) <= max_len:
            chunks.append(text)
            break
        # Try to split at newline near the limit
        cut = text.rfind('\n', 0, max_len)
        if cut < max_len // 2:
            cut = max_len
        chunks.append(text[:cut])
        text = text[cut:].lstrip('\n')
    if text and len(chunks) == 5:
        # Truncate last chunk with note
        chunks[-1] = chunks[-1][:max_len - 20] + "\n\n... (ข้อความยาวเกิน)"
    return chunks


def reply_text_message(reply_token: str, text: str) -> Dict[str, Any]:
    """
    Reply to message using reply token.
    Automatically splits messages > 5000 chars (LINE limit).

    Args:
        reply_token: Reply token from webhook event
        text: Message text (auto-split if too long)

    Returns:
        Response dict with success status
    """
    url = f"{LINE_API_BASE}/message/reply"
    chunks = _split_text(text)
    messages = [{"type": "text", "text": chunk} for chunk in chunks]

    payload = {
        "replyToken": reply_token,
        "messages": messages  # LINE allows up to 5 messages per reply
    }

    try:
        response = requests.post(url, json=payload, headers=_get_headers())
        response.raise_for_status()

        return {
            "success": True,
            "status_code": response.status_code
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
        }


def push_flex_message(user_id: str, alt_text: str, contents: Dict[str, Any]) -> Dict[str, Any]:
    """
    Push flex message to user

    Args:
        user_id: LINE user ID
        alt_text: Alternative text for notifications
        contents: Flex message contents (bubble or carousel)

    Returns:
        Response dict with success status
    """
    url = f"{LINE_API_BASE}/message/push"
    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "flex",
                "altText": alt_text,
                "contents": contents
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, headers=_get_headers())
        response.raise_for_status()

        return {
            "success": True,
            "status_code": response.status_code
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
        }
