"""
FastAPI Webhook for LINE Bot
Handle incoming LINE messages and respond with chatbot
"""
import hashlib
import hmac
import base64
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
from .settings import LINE_CHANNEL_SECRET
from .chat import chat
from .line_client import reply_text_message
from .templates import list_templates


app = FastAPI(title="B+ ERP Chatbot")


# In-memory session store (simple implementation)
# For production, use Redis or database
user_sessions: Dict[str, list] = {}


def verify_signature(body: bytes, signature: str) -> bool:
    """
    Verify LINE webhook signature

    Args:
        body: Request body bytes
        signature: X-Line-Signature header value

    Returns:
        True if signature is valid
    """
    if not LINE_CHANNEL_SECRET:
        # Skip verification if no secret configured
        return True

    hash_digest = hmac.new(
        LINE_CHANNEL_SECRET.encode('utf-8'),
        body,
        hashlib.sha256
    ).digest()

    expected_signature = base64.b64encode(hash_digest).decode('utf-8')

    print(f"[DEBUG] Received signature: {signature}")
    print(f"[DEBUG] Expected signature: {expected_signature}")
    print(f"[DEBUG] Secret length: {len(LINE_CHANNEL_SECRET)}")

    return hmac.compare_digest(signature, expected_signature)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "bplus-erp-chatbot"}


@app.get("/debug")
async def debug_info():
    """Debug endpoint — connection + template info."""
    try:
        from .db_client import test_connection
        from .settings import DEEPSEEK_MODEL, DEEPSEEK_BASE_URL
        db = test_connection()
        return {
            "db": db,
            "model": DEEPSEEK_MODEL,
            "base_url": DEEPSEEK_BASE_URL,
            "python": __import__("sys").version,
        }
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


@app.get("/templates")
async def get_templates():
    """List available query templates"""
    try:
        templates = list_templates()
        return {"templates": templates, "count": len(templates)}
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


@app.get("/schema/{table_name}")
async def get_schema(table_name: str):
    """Get column info for a specific table (for debugging)."""
    try:
        import psycopg2.extras
        from .db_client import _get_pool
        
        p = _get_pool()
        conn = p.getconn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position
            """, (table_name,))
            cols = [dict(r) for r in cur.fetchall()]
            if not cols:
                return {"error": f"Table '{table_name}' not found"}
            return {"table": table_name, "columns": cols, "count": len(cols)}
        finally:
            cur.close()
            p.putconn(conn)
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


@app.post("/webhook")
async def webhook(
    request: Request,
    x_line_signature: Optional[str] = Header(None)
):
    """
    LINE webhook endpoint

    Handles incoming messages from LINE Official Account
    """
    # Get request body
    body = await request.body()

    # Debug logging
    print(f"Received webhook request")
    print(f"Signature header: {x_line_signature}")
    print(f"Body length: {len(body)}")

    # Verify signature
    if x_line_signature:
        if not verify_signature(body, x_line_signature):
            print(f"Signature verification FAILED")
            print(f"Expected signature based on body")
            raise HTTPException(status_code=400, detail="Invalid signature")
        else:
            print(f"Signature verification PASSED")
    else:
        print(f"No signature header - skipping verification")

    # Parse JSON
    try:
        data = await request.json()
        print(f"Parsed JSON successfully")
    except Exception as e:
        print(f"JSON parse error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

    # Process events
    events = data.get("events", [])
    print(f"Processing {len(events)} events")

    for event in events:
        event_type = event.get("type")
        print(f"[DEBUG] Event type: {event_type}")
        print(f"[DEBUG] Event data: {event}")

        # Handle message events
        if event_type == "message":
            message_type = event.get("message", {}).get("type")

            print(f"[DEBUG] Message type: {message_type}")
            if message_type == "text":
                # Extract message details
                reply_token = event.get("replyToken")
                user_id = event.get("source", {}).get("userId")
                text = event.get("message", {}).get("text", "")

                if not reply_token or not text:
                    continue

                try:
                    # Get user session history (last 5 turns)
                    history = user_sessions.get(user_id, [])
                    print(f"[DEBUG] History length: {len(history)} messages")

                    # Call chatbot with history for multi-turn context
                    print(f"[DEBUG] Calling chat with text: {text}")
                    response_text, updated_history = chat(text, history=history)
                    print(f"[DEBUG] Chatbot response: {response_text[:100]}...")

                    # chat() already returns cleaned history (text-only, proper alternation)
                    user_sessions[user_id] = updated_history[-10:]

                    # Reply to user (auto-splits if > 5000 chars)
                    result = reply_text_message(reply_token, response_text)

                    if not result.get("success"):
                        print(f"Failed to reply: {result.get('error')}")

                except Exception as e:
                    # Send error message to user
                    error_msg = "❌ ขออภัย เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้ง"
                    reply_text_message(reply_token, error_msg)
                    print(f"Error processing message: {str(e)}")

    return JSONResponse(content={"status": "ok"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
