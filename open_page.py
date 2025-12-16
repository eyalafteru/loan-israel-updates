import webbrowser
import os

file_path = os.path.join(
    r"C:\Users\eyal\loan-israel-updaets\loan-israel-updates",
    "דפים לשינוי",
    "הלוואה חוץ בנקאית.html"
)

webbrowser.open(f"file:///{file_path}")
print(f"Opened: {file_path}")


