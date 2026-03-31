import os
import base64
import requests
from datetime import datetime, timezone

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_USERNAME = os.environ["GITHUB_USERNAME"]
GITHUB_REPO = os.environ["GITHUB_REPO"]

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}
API_BASE = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}"
FILE_PATH = "contributions/log.md"


def get_current_file():
    url = f"{API_BASE}/contents/{FILE_PATH}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        sha = data["sha"]
        return content, sha
    return None, None


def make_contribution():
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    date_str = now.strftime("%Y-%m-%d")
    slot = "matin" if now.hour < 12 else "soir"

    current_content, sha = get_current_file()

    if current_content is None:
        new_content = f"# Journal des contributions\n\n| Date | Heure | Créneau |\n|------|-------|--------|\n"
    else:
        new_content = current_content

    new_content += f"| {date_str} | {now.strftime('%H:%M')} UTC | {slot} |\n"

    encoded = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")
    commit_message = f"contribution automatique - {timestamp}"

    payload = {
        "message": commit_message,
        "content": encoded,
    }
    if sha:
        payload["sha"] = sha

    url = f"{API_BASE}/contents/{FILE_PATH}"
    response = requests.put(url, headers=HEADERS, json=payload)

    if response.status_code in (200, 201):
        print(f"[OK] Commit réussi : {commit_message}")
    else:
        print(f"[ERREUR] {response.status_code} - {response.json()}")
        raise Exception("Echec du commit GitHub")


if __name__ == "__main__":
    make_contribution()
