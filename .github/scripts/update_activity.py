"""Refresh the Activity section of README.md from the GitHub contribution calendar."""
import json
import os
import re
import sys
import urllib.request

LOGIN = os.environ.get("PROFILE_LOGIN", "jahndev")
TOKEN = os.environ["GITHUB_TOKEN"]
README = "README.md"
START, END = "<!-- activity:start -->", "<!-- activity:end -->"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def fetch_days():
    body = json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {TOKEN}", "User-Agent": "profile-activity"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if data.get("errors"):
        sys.exit(f"GraphQL error: {data['errors']}")
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    return cal["totalContributions"], days


def main():
    total, days = fetch_days()
    if total == 0:
        sys.exit("Calendar returned 0 contributions; leaving README unchanged.")
    last30 = days[-30:]
    count30 = sum(d["contributionCount"] for d in last30)
    active30 = sum(1 for d in last30 if d["contributionCount"] > 0)
    block = "\n".join(
        [
            START,
            f"- **{total:,}** contributions in the last 12 months",
            f"- **{count30:,}** contributions in the last 30 days, on **{active30}** active days",
            "- Most of my current work is in private repositories, so it appears here as counts only.",
            END,
        ]
    )
    with open(README, encoding="utf-8") as f:
        text = f.read()
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(text):
        sys.exit("Activity markers not found in README.md")
    new = pattern.sub(lambda _: block, text)
    if new != text:
        with open(README, "w", encoding="utf-8", newline="\n") as f:
            f.write(new)
    print(block)


if __name__ == "__main__":
    main()
