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
HEADERS_GRAPHQL = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json",
}
API = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}"
FILE_PATH = "contributions/log.md"

CO_AUTHORS = [
    "Co-authored-by: contributor-bot <contributor-bot@users.noreply.github.com>",
    "Co-authored-by: dev-assistant <dev-assistant@users.noreply.github.com>",
]

EMOJIS = ["+1", "heart", "rocket", "hooray", "laugh", "eyes"]


# ── helpers ──────────────────────────────────────────────────────────────────

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
        "ref": f"refs/heads/{branch_name}", "sha": sha,
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
    requests.put(f"{API}/contents/{FILE_PATH}", headers=HEADERS, json=payload).raise_for_status()


def open_pr(branch, title, body):
    r = requests.post(f"{API}/pulls", headers=HEADERS, json={
        "title": title, "head": branch, "base": "main", "body": body,
    })
    if not r.ok:
        print(f"[ERREUR PR] {r.status_code} - {r.text}")
        r.raise_for_status()
    return r.json()["number"]


def merge_pr(pr_number):
    requests.put(f"{API}/pulls/{pr_number}/merge", headers=HEADERS, json={
        "merge_method": "squash",
        "commit_title": f"Merge pull request #{pr_number}",
    }).raise_for_status()


def add_reaction(subject_type, subject_number, emoji):
    """Heart On Your Sleeve : réagir à une issue ou PR"""
    url = f"{API}/{subject_type}/{subject_number}/reactions"
    r = requests.post(url, headers=HEADERS, json={"content": emoji})
    return r.status_code in (200, 201)


# ── achievements ─────────────────────────────────────────────────────────────

def quickdraw(slot_index):
    """Quickdraw : ouvre et ferme une issue immédiatement"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    r = requests.post(f"{API}/issues", headers=HEADERS, json={
        "title": f"Journal - {now}",
        "body": "Mise à jour automatique du journal de contributions.",
    })
    if r.status_code != 201:
        return None
    issue_number = r.json()["number"]

    # Heart On Your Sleeve : réagir à l'issue avant de la fermer
    emoji = EMOJIS[slot_index % len(EMOJIS)]
    if add_reaction("issues", issue_number, emoji):
        print(f"[OK] Heart On Your Sleeve : réaction :{emoji}: sur issue #{issue_number}")

    requests.patch(f"{API}/issues/{issue_number}", headers=HEADERS, json={"state": "closed"})
    print(f"[OK] Quickdraw : issue #{issue_number} ouverte et fermée")
    return issue_number


def galaxy_brain():
    """
    Galaxy Brain : crée une discussion, poste une réponse, la marque comme acceptée.
    Nécessite que les Discussions soient activées sur le repo.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Récupérer l'ID du repo et la catégorie de discussion via GraphQL
    repo_query = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        id
        discussionCategories(first: 5) {
          nodes { id name }
        }
      }
    }
    """
    r = requests.post("https://api.github.com/graphql", headers=HEADERS_GRAPHQL, json={
        "query": repo_query,
        "variables": {"owner": GITHUB_USERNAME, "name": GITHUB_REPO},
    })
    if r.status_code != 200:
        print("[SKIP] Galaxy Brain : erreur GraphQL")
        return

    data = r.json().get("data", {}).get("repository", {})
    repo_id = data.get("id")
    categories = data.get("discussionCategories", {}).get("nodes", [])
    if not repo_id or not categories:
        print("[SKIP] Galaxy Brain : discussions non activées sur ce repo")
        return

    # Prendre la catégorie Q&A si dispo, sinon la première
    category = next((c for c in categories if "Q&A" in c["name"] or "General" in c["name"]), categories[0])
    category_id = category["id"]

    # Créer la discussion
    create_discussion = """
    mutation($repoId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
      createDiscussion(input: {repositoryId: $repoId, categoryId: $categoryId, title: $title, body: $body}) {
        discussion { id number }
      }
    }
    """
    r = requests.post("https://api.github.com/graphql", headers=HEADERS_GRAPHQL, json={
        "query": create_discussion,
        "variables": {
            "repoId": repo_id, "categoryId": category_id,
            "title": f"Journal automatique - {now}",
            "body": "Comment automatiser ses contributions GitHub efficacement ?",
        },
    })
    discussion = r.json().get("data", {}).get("createDiscussion", {}).get("discussion", {})
    discussion_id = discussion.get("id")
    if not discussion_id:
        print("[SKIP] Galaxy Brain : impossible de créer la discussion")
        return
    print(f"[OK] Discussion #{discussion.get('number')} créée")

    # Poster une réponse
    add_comment = """
    mutation($discussionId: ID!, $body: String!) {
      addDiscussionComment(input: {discussionId: $discussionId, body: $body}) {
        comment { id }
      }
    }
    """
    r = requests.post("https://api.github.com/graphql", headers=HEADERS_GRAPHQL, json={
        "query": add_comment,
        "variables": {
            "discussionId": discussion_id,
            "body": "En utilisant l'API GitHub et GitHub Actions pour automatiser les commits, PRs et réactions quotidiennement.",
        },
    })
    comment_id = r.json().get("data", {}).get("addDiscussionComment", {}).get("comment", {}).get("id")
    if not comment_id:
        print("[SKIP] Galaxy Brain : impossible de poster la réponse")
        return

    # Marquer la réponse comme acceptée
    mark_answer = """
    mutation($commentId: ID!) {
      markDiscussionCommentAsAnswer(input: {id: $commentId}) {
        discussion { id }
      }
    }
    """
    r = requests.post("https://api.github.com/graphql", headers=HEADERS_GRAPHQL, json={
        "query": mark_answer,
        "variables": {"commentId": comment_id},
    })
    if r.json().get("data", {}).get("markDiscussionCommentAsAnswer"):
        print("[OK] Galaxy Brain : réponse marquée comme acceptée")
    else:
        print("[SKIP] Galaxy Brain : impossible de marquer (catégorie non Q&A ?)")


# ── main ─────────────────────────────────────────────────────────────────────

def make_contribution():
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    date_str = now.strftime("%Y-%m-%d")
    slot = "matin" if now.hour < 12 else "soir"
    slot_index = 0 if slot == "matin" else 1
    branch = f"contribution/{date_str}-{slot}"

    # 1. Créer une branche
    main_sha = get_main_sha()
    create_branch(branch, main_sha)
    print(f"[OK] Branche créée : {branch}")

    # 2. Commit avec co-auteurs (Pair Extraordinaire)
    content, sha = get_file(branch)
    if content is None:
        content = "# Journal des contributions\n\n| Date | Heure | Créneau |\n|------|-------|----------|\n"
    content += f"| {date_str} | {now.strftime('%H:%M')} UTC | {slot} |\n"

    commit_message = f"contribution automatique - {timestamp}\n\n" + "\n".join(CO_AUTHORS)
    update_file(branch, content, sha, commit_message)
    print("[OK] Commit avec co-auteurs (Pair Extraordinaire)")

    # 3. Ouvrir une PR
    pr_number = open_pr(
        branch,
        title=f"Contribution automatique - {timestamp}",
        body=f"Mise à jour automatique du journal.\n\n_{slot} du {date_str}_",
    )
    print(f"[OK] PR #{pr_number} ouverte")

    # 4. Réagir à la PR (Heart On Your Sleeve)
    emoji = EMOJIS[slot_index % len(EMOJIS)]
    if add_reaction("issues", pr_number, emoji):  # PRs sont des issues pour l'API
        print(f"[OK] Heart On Your Sleeve : réaction :{emoji}: sur PR #{pr_number}")

    # 5. Merger sans review (Pull Shark + YOLO)
    merge_pr(pr_number)
    print(f"[OK] PR #{pr_number} mergée (Pull Shark + YOLO)")

    # 6. Supprimer la branche
    delete_branch(branch)

    # 7. Quickdraw + Heart On Your Sleeve sur issue
    quickdraw(slot_index + 1)

    # 8. Galaxy Brain (discussions)
    galaxy_brain()

    print(f"\n[DONE] Achievements visés ce run :")
    print("  - Pull Shark       : PR mergée")
    print("  - YOLO             : merge sans review")
    print("  - Pair Extraordinaire : co-authored commit")
    print("  - Quickdraw        : issue ouverte/fermée")
    print("  - Heart On Your Sleeve : réactions emoji")
    print("  - Galaxy Brain     : discussion Q&A acceptée")


if __name__ == "__main__":
    make_contribution()
