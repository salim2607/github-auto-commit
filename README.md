# github-auto-commit

> Just for fun — a simple experiment to explore GitHub automation.

Ce projet automatise des actions GitHub quotidiennes (commits, pull requests, réactions, discussions) via **GitHub Actions** et l'**API GitHub**.

C'est un essai pour comprendre ce qu'on peut faire automatiquement sur GitHub. Peut-être que des automatisations plus complexes seront ajoutées plus tard.

## Ce que ça fait (2x par jour)

- Crée une branche, fait un commit et ouvre une PR → merge automatique
- Co-signe les commits avec des co-auteurs
- Réagit avec des emojis sur les issues et PRs
- Ouvre et ferme une issue
- Crée une discussion Q&A et marque une réponse comme acceptée

## Stack

- Python + `requests`
- GitHub Actions (cron `0 9 * * *` et `0 20 * * *`)
- GitHub REST API + GraphQL API

---

*Just for fun. More complex automations maybe coming later.*
