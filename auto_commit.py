import os
import base64
import requests
from datetime import datetime, timezone
import time

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_USERNAME = os.environ["GITHUB_USERNAME"]
GITHUB_REPO = os.environ["GITHUB_REPO"]

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}
API = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}"
FILE_PATH = "contributions/log.md"

# Co-auteurs fictifs pour l'achievement Pair Extraordinaire
CO_AUTHORS = [
    "Co-authored-by: contributor-bot <contributor-bot@users.noreply.github.com>",
    "Co-authored-by: dev-assistant <dev-assistant@users.noreply.github.com>",
]


def get_main_sha():
    r = requests.get(f"{API}/git/ref/heads/main", headers=HEADERS)
    return r.json()["object"]["sha"]


def get_file(branch="main"):
    r = requests.get(f"{API}/contents/{FILE_PATH}?ref={branch}", headers=HEADERS)
    if r.status_code == 200:
        d = r.json()
        return base64.b64decode(d["content"]).decode(), d["sha"]
    return None, None


def create_branch(branch_name, sha):
    requests.post(f"{API}/git/refs", headers=HEADERS, json={
        "ref": f"refs/heads/{branch_name}",
        "sha": sha,
    })


def delete_branch(branch_name):
    requests.delete(f"{API}/git/refs/heads/{branch_name}", headers=HEADERS)


def update_file(branch, content, sha, message):
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha
    r = requests.put(f"{API}/contents/{FILE_PATH}", headers=HEADERS, json=payload)
    r.raise_for_status()


def open_pr(branch, title, body):
    r = requests.post(f"{API}/pulls", headers=HEADERS, json={
        "title": title,
        "head": branch,
        "base": "main",
        "body": body,
    })
    r.raise_for_status()
    return r.json()["number"]


def merge_pr(pr_number):
    r = requests.put(f"{API}/pulls/{pr_number}/merge", headers=HEADERS, json={
        "merge_method": "squash",
        "commit_title": f"Merge pull request #{pr_number}",
    })
    r.raise_for_status()


def quickdraw():
    """Ouvre et ferme une issue immédiatement → achievement Quickdraw"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    r = requests.post(f"{API}/issues", headers=HEADERS, json={
        "title": f"Contribution log - {now}",
        "body": "Mise à jour automatique du journal de contributions.",
    })
    if r.status_code == 201:
        issue_number = r.json()["number"]
        requests.patch(f"{API}/issues/{issue_number}", headers=HEADERS, json={"state": "closed"})
        print(f"[OK] Quickdraw : issue #{issue_number} ouverte et fermée")


def make_contribution():
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    date_str = now.strftime("%Y-%m-%d")
    slot = "matin" if now.hour < 12 else "soir"
    branch = f"contribution/{date_str}-{slot}"

    # 1. Récupérer le SHA de main
    main_sha = get_main_sha()

    # 2. Créer une branche
    create_branch(branch, main_sha)
    print(f"[OK] Branche créée : {branch}")

    # 3. Mettre à jour le fichier sur la branche
    content, sha = get_file(branch)
    if content is None:
        content = "# Journal des contributions\n\n| Date | Heure | Créneau |\n|------|-------|----------|\n"
    content += f"| {date_str} | {now.strftime('%H:%M')} UTC | {slot} |\n"

    commit_message = (
        f"contribution automatique - {timestamp}\n\n"
        + "\n".join(CO_AUTHORS)
    )
    update_file(branch, content, sha, commit_message)
    print(f"[OK] Commit sur {branch} (Pair Extraordinaire)")

    # 4. Ouvrir une PR
    pr_number = open_pr(
        branch,
        title=f"Contribution automatique - {timestamp}",
        body=f"Mise à jour automatique du journal.\n\n_{slot} du {date_str}_",
    )
    print(f"[OK] PR #{pr_number} ouverte (Pull Shark + YOLO)")

    # 5. Merger la PR immédiatement sans review (YOLO)
    merge_pr(pr_number)
    print(f"[OK] PR #{pr_number} mergée")

    # 6. Supprimer la branche
    delete_branch(branch)

    # 7. Quickdraw : ouvrir/fermer une issue
    quickdraw()

    print(f"\n Achievements visés : Pull Shark, YOLO, Pair Extraordinaire, Quickdraw")


if __name__ == "__main__":
    make_contribution()
