import os
from pathlib import Path
from collections import Counter

import requests

USERNAME = "gray-ji"
TOKEN = os.environ["GITHUB_TOKEN"]

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
}

BASE_DIR = Path(__file__).resolve().parent.parent
PROFILE_DIR = BASE_DIR / "profile"
PROFILE_DIR.mkdir(exist_ok=True)


def github_get(url, params=None):
    response = requests.get(url, headers=HEADERS, params=params)

    if response.status_code == 404:
        return None

    response.raise_for_status()
    return response.json()


def get_repositories():
    repositories = []
    page = 1

    while True:
        data = github_get(
            "https://api.github.com/user/repos",
            {
                "per_page": 100,
                "page": page,
                "affiliation": "owner,collaborator,organization_member",
                "sort": "updated",
            },
        )

        if not data:
            break

        repositories.extend(data)
        page += 1

    # Private repository는 제외
    return [repo for repo in repositories if not repo["private"]]


def count_commits(repository):
    owner = repository["owner"]["login"]
    name = repository["name"]

    total = 0
    page = 1

    while True:
        data = github_get(
            f"https://api.github.com/repos/{owner}/{name}/commits",
            {
                "author": USERNAME,
                "per_page": 100,
                "page": page,
            },
        )

        if not data:
            break

        total += len(data)

        if len(data) < 100:
            break

        page += 1

    return total


def get_languages(repository):
    owner = repository["owner"]["login"]
    name = repository["name"]

    return github_get(
        f"https://api.github.com/repos/{owner}/{name}/languages"
    ) or {}


def create_commit_svg(total_commits):
    svg = f"""<svg width="500" height="180"
viewBox="0 0 500 180"
xmlns="http://www.w3.org/2000/svg">

<rect width="500" height="180" rx="12" fill="#0d1117"/>

<text x="30" y="48"
font-family="Arial, sans-serif"
font-size="22"
font-weight="bold"
fill="#ffffff">
GitHub Commits
</text>

<text x="30" y="115"
font-family="Arial, sans-serif"
font-size="48"
font-weight="bold"
fill="#58a6ff">
{total_commits}
</text>

<text x="30" y="145"
font-family="Arial, sans-serif"
font-size="14"
fill="#8b949e">
Public personal + organization repositories
</text>

</svg>
"""

    (PROFILE_DIR / "commits.svg").write_text(
        svg,
        encoding="utf-8",
    )


def create_languages_svg(language_totals):
    total_bytes = sum(language_totals.values())

    if total_bytes == 0:
        rows = """
        <text x="30" y="70"
        font-family="Arial, sans-serif"
        font-size="18"
        fill="#ffffff">
        No language data
        </text>
        """
    else:
        top_languages = language_totals.most_common(5)

        rows = ""
        y = 45

        for language, value in top_languages:
            percentage = value / total_bytes * 100

            rows += f"""
            <text x="30" y="{y}"
            font-family="Arial, sans-serif"
            font-size="16"
            font-weight="bold"
            fill="#ffffff">
            {language}
            </text>

            <text x="410" y="{y}"
            font-family="Arial, sans-serif"
            font-size="15"
            text-anchor="end"
            fill="#8b949e">
            {percentage:.1f}%
            </text>

            <rect x="30" y="{y + 8}"
            width="410"
            height="7"
            rx="3"
            fill="#30363d"/>

            <rect x="30" y="{y + 8}"
            width="{410 * percentage / 100:.1f}"
            height="7"
            rx="3"
            fill="#58a6ff"/>
            """

            y += 30

    svg = f"""<svg width="500" height="220"
viewBox="0 0 500 220"
xmlns="http://www.w3.org/2000/svg">

<rect width="500" height="220" rx="12" fill="#0d1117"/>

<text x="30" y="25"
font-family="Arial, sans-serif"
font-size="22"
font-weight="bold"
fill="#ffffff">
Top Languages
</text>

{rows}

</svg>
"""

    (PROFILE_DIR / "top-langs.svg").write_text(
        svg,
        encoding="utf-8",
    )


def main():
    repositories = get_repositories()

    total_commits = 0
    language_totals = Counter()

    for repository in repositories:
        full_name = repository["full_name"]

        try:
            commits = count_commits(repository)
            total_commits += commits

            languages = get_languages(repository)

            for language, bytes_count in languages.items():
                language_totals[language] += bytes_count

            print(
                f"{full_name}: "
                f"{commits} commits, "
                f"languages={list(languages.keys())}"
            )

        except Exception as error:
            print(f"Skip {full_name}: {error}")

    print(f"Total commits: {total_commits}")
    print(f"Languages: {language_totals}")

    create_commit_svg(total_commits)
    create_languages_svg(language_totals)


if __name__ == "__main__":
    main()