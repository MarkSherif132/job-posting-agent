import os

from dotenv import load_dotenv

load_dotenv()


def get_api_key() -> str:
    api_key = os.getenv("API_KEY", "").strip()

    if not api_key:
        raise ValueError(
            "API_KEY مش موجود. تأكد إنك حاطط API_KEY=... في ملف .env"
        )

    if api_key == "gsk_your_real_key_here":
        raise ValueError(
            "API_KEY لسه القيمة الوهمية. حط مفتاحك الحقيقي في ملف .env"
        )

    return api_key