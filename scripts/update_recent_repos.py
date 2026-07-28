#!/usr/bin/env python3
import json
import os
import urllib.request
from pathlib import Path

START = "<!-- PROMOTED-REPOS:START -->"
END = "<!-- PROMOTED-REPOS:END -->"
TOPIC = "promoted"


def fetch_repositories(owner: str) -> list[dict]:
    repositories = []
    page = 1
    while True:
        request = urllib.request.Request(
            f"https://api.github.com/users/{owner}/repos?per_page=100&page={page}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
                "User-Agent": "profile-readme-updater",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        with urllib.request.urlopen(request) as response:
            batch = json.load(response)
        repositories.extend(batch)
        if len(batch) < 100:
            return repositories
        page += 1


def render(repositories: list[dict], profile_repository: str) -> str:
    visible = sorted(
        [
            repository
            for repository in repositories
            if TOPIC in repository["topics"]
            and repository["name"] != profile_repository
        ],
        key=lambda repository: repository["name"].lower(),
    )

    if not visible:
        return f"_No hay proyectos públicos con el topic `{TOPIC}`._"

    rows = []
    for repository in visible:
        description = (repository["description"] or "Sin descripción").replace("|", "\\|")
        language = repository["language"] or "—"
        rows.append(
            f"| [{repository['name']}]({repository['html_url']}) | {description} | {language} |"
        )

    return "\n".join(
        [
            "| Proyecto | Descripción | Tecnología |",
            "|---|---|---|",
            *rows,
        ]
    )


def main() -> None:
    owner, profile_repository = os.environ["GITHUB_REPOSITORY"].split("/", 1)
    readme = Path("README.md")
    content = readme.read_text(encoding="utf-8")
    if START not in content or END not in content:
        raise RuntimeError("No se encontraron los marcadores de proyectos destacados en README.md")

    generated = render(fetch_repositories(owner), profile_repository)
    before, remainder = content.split(START, 1)
    _, after = remainder.split(END, 1)
    readme.write_text(
        f"{before}{START}\n{generated}\n{END}{after}",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
