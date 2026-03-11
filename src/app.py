# Замените строку:
from kivymd.toast import toast

# На:
try:
    from kivymd.toast import toast
except ImportError:
    # Fallback для Android
    def toast(text):
        print(f"[TOAST] {text}")
