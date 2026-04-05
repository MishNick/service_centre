import random
import logging
from datetime import datetime, timedelta
import json

# Для простоты будем хранить коды в памяти (в Redis позже)
# Структура: {phone: {"code": "1234", "expires": timestamp}}
sms_codes = {}


def generate_sms_code(phone: str) -> str:
    """Генерирует 4-значный код и сохраняет в памяти"""
    code = str(random.randint(1000, 9999))
    expires = (datetime.utcnow() + timedelta(minutes=5)).timestamp()

    sms_codes[phone] = {
        "code": code,
        "expires": expires
    }

    # В реале здесь отправка СМС, пока просто логируем
    logging.info(f"📱 SMS для {phone}: Код {code}")
    print(f"\n🔐 ВАШ КОД ПОДТВЕРЖДЕНИЯ: {code}\n")

    return code


def verify_sms_code(phone: str, code: str) -> bool:
    """Проверяет код"""
    if phone not in sms_codes:
        return False

    data = sms_codes[phone]
    if datetime.utcnow().timestamp() > data["expires"]:
        # Код истек
        del sms_codes[phone]
        return False

    if data["code"] == code:
        # Код верный - удаляем
        del sms_codes[phone]
        return True

    return False