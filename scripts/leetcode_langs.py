"""
Fetches LeetCode language stats and writes a % progress-bar table
into README.md between the START/END markers.
"""

import re
import sys
from datetime import datetime, timezone, timedelta

import requests

# ================= CONFIG =================
USERNAME = "MohanK_2026"   # your LeetCode username
BAR_WIDTH = 25             # progress bar length
README_FILE = "README.md"
# ==========================================

GRAPHQL_URL = "https://leetcode.com/graphql"

QUERY = """
query languageStats($username: String!) {
  matchedUser(username: $username) {
    languageProblemCount {
      languageName
      problemsSolved
    }
  }
}
"""


def fetch_language_stats():
    response = requests.post(
        GRAPHQL_URL,
        json={"query": QUERY, "variables": {"username": USERNAME}},
        headers={
            "Content-Type": "application/json",
            "Referer": f"https://leetcode.com/u/{USERNAME}/",
            "User-Agent": "Mozilla/5.0 (GitHub-Actions LeetCode Stats Bot)",
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    matched = data.get("data", {}).get("matchedUser")
    if not matched:
        print(f"❌ User '{USERNAME}' not found on LeetCode.")
        sys.exit(1)

    return matched["languageProblemCount"]


def build_block(langs):
    langs = sorted(langs, key=lambda x: x["problemsSolved"], reverse=True)
    total = sum(l["problemsSolved"] for l in langs)

    if total == 0:
        return "```text\nNo solved problems yet.\n```"

    # IST timestamp for "last updated"
    ist = timezone(timedelta(hours=5, minutes=30))
    updated = datetime.now(ist).strftime("%d %b %Y, %I:%M %p IST")

    lines = []
    for lang in langs:
        name = lang["languageName"]
        solved = lang["problemsSolved"]
        pct = solved / total * 100
        filled = round(pct / 100 * BAR_WIDTH)
        bar = "█" * filled + "░" * (BAR_WIDTH - filled)
        lines.append(f"{name:<12} {bar} {pct:5.1f}%  ({solved} solved)")

    lines.append("")
    lines.append(f"Total Solved : {total}")
    lines.append(f"Last Updated : {updated}")

    return "```text\n" + "\n".join(lines) + "\n```"


def update_readme(block):
    with open(README_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"(<!--START_SECTION:leetcode-langs-->)[\s\S]*?(<!--END_SECTION:leetcode-langs-->)"

    if not re.search(pattern, content):
        print("❌ Markers not found in README.md!")
        print("Add these lines where you want the stats:")
        print("<!--START_SECTION:leetcode-langs-->")
        print("<!--END_SECTION:leetcode-langs-->")
        sys.exit(1)

    new_content = re.sub(
        pattern,
        lambda m: m.group(1) + "\n" + block + "\n" + m.group(2),
        content,
    )

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)


if __name__ == "__main__":
    print(f"🔍 Fetching LeetCode stats for: {USERNAME}")
    stats = fetch_language_stats()
    block = build_block(stats)
    print(block)
    update_readme(block)
    print("✅ README.md updated successfully!")
