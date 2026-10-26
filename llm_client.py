import time
import os
from config import get_api_key
import httpx

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MODEL_ID = "openai/gpt-oss-120b"


# to handel tool calling function' problems, we can use a wrapper function to call the tool and handle exceptions
AGENT_MODEL_ID = "openai/gpt-oss-120b"
MAX_RATE_LIMIT_RETRIES = 4
MAX_WAIT_SECONDS = 30
def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

def _retry_wait_seconds(response: httpx.Response) -> float:
    """كام ثانية Groq طلبت نستناها بعد 429 (من هيدر retry-after)."""
    try:
        return float(response.headers["retry-after"])
    except (KeyError, ValueError):
        return 5.0

def chat_completion(
    prompt: str,
    *,
    system: str | None = None,
    max_tokens: int = 1500,
    temperature: float = 0.7,
) -> str:
    """
    بتبعت prompt لـ Groq وترجع رد الموديل كنص.
    لو Groq قالت "استنى شوية" (429)، بتستنى وتعيد المحاولة تلقائيًا.
    """
    api_key = get_api_key()

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body = {
        "model": MODEL_ID,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
        try:
            response = httpx.post(
                f"{GROQ_BASE_URL}/chat/completions",
                headers=_headers(api_key),
                json=body,
                timeout=60.0,
            )
        except httpx.TimeoutException:
            raise RuntimeError("Groq ماردتش في الوقت المحدد (timeout). جرّب تاني.")
        except httpx.RequestError as e:
            raise RuntimeError(f"مشكلة في الاتصال بـ Groq: {e}")

        if response.status_code == 429 and attempt < MAX_RATE_LIMIT_RETRIES:
            wait = _retry_wait_seconds(response)
            if wait <= MAX_WAIT_SECONDS:
                time.sleep(wait + 1)
                continue
        break

    if response.status_code != 200:
        raise RuntimeError(f"Groq رجّعت خطأ {response.status_code}: {response.text}")

    data = response.json()
    choice = data["choices"][0]

    if choice["finish_reason"] == "length":
        print(
            f"⚠️  تحذير: الرد اتقطع لأنه وصل max_tokens={max_tokens}. "
            "النتيجة ناقصة."
        )

    return choice["message"]["content"]