"""Find people at a company for /job-hunt-studio:outreach from free, keyless public sources.

Sources (standard library only, no accounts or API keys):
  connections  the user's own LinkedIn connections export (Connections.csv), if they added it: people they
               already know there, the warmest route to a referral. It never leaves their computer.
  research     OpenAlex: authors of the company's recent papers, ranked by how close the paper titles are to
               jhs.yaml outreach.topics; last authors are often team leads. Keyless use shares a small daily
               budget per IP address (about $0.10, roughly 100 searches); one run costs about $0.003.
  github       the company's GitHub organizations: public members and the main contributors to its most
               active repositories, with the name, company and location from their public profiles
               (through the gh command when it is logged in, else 60 anonymous calls an hour).
It never touches linkedin.com. It also prints the web searches for the next step (Claude's WebSearch with
LinkedIn as the allowed domain, which returns search-result titles and snippets only), including shared ties
(people at the company who list one of the user's schools or past employers), and the pastes to ask the user for.

Settings (jhs.yaml): outreach.default_location, outreach.topics, outreach.search_roles, outreach.aliases,
outreach.connections_csv and outreach.connections; candidate.schools and candidate.past_employers for ties.
Outputs:
  applications/outreach/raw/people_<company>_<date>.json   candidates per source (gitignored)
  stdout                                                   a markdown summary for the outreach skill

Usage (from the workspace folder, with the workspace Python):
  python find_people.py "Acme" [--location Lyon] [--github acme-ai] [--institution I123] [--since 2025-01-01]
                        [--sources connections,research,github] [--topics "rank,retriev"]
  python find_people.py "Acme, Globex" --sources connections
  python find_people.py --check-connections [--connections PATH]
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import ConfigError, load, utf8_stdout  # noqa: E402

UA = {"User-Agent": "job-hunt-studio find_people (personal job search)"}
OPENALEX = "https://api.openalex.org"
LINKEDIN_DOMAINS = ["linkedin.com"]
BOTS = re.compile(r"\[bot\]$|-bot$|^dependabot|^renovate|^github-actions|^pre-commit-ci", re.I)
SUFFIXES = re.compile(r"\b(inc|incorporated|ltd|limited|llc|corp|corporation|co|company|plc|gmbh|sa|sas|ag|"
                      r"technologies|technology|labs?|ai|group|the)\b")
ROLE_WORDS = re.compile(r"\b(senior|sr|junior|jr|staff|principal|lead|engineer|engineering|scientist|developer|"
                        r"analyst|specialist|researcher|manager|consultant|associate|intern)\b", re.I)
DEFAULT_ROLES = ["engineering manager", "team lead", "recruiter"]

openalex_budget: dict = {}  # last X-RateLimit-Remaining-USD seen


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").casefold()).strip()


def plain_name(company: str) -> str:
    """The company name without notes in parentheses: 'Acme (Lyon office)' -> 'Acme'."""
    return " ".join(re.sub(r"\(.*?\)", " ", company or "").split())


def norm_company(name: str) -> str:
    """'Acme Corporation Inc.' -> 'acme'; 'Globex (France)' -> 'globex'."""
    core = re.sub(r"\s+", " ", SUFFIXES.sub(" ", norm(plain_name(name)))).strip()
    return core or norm(name)


def same_company(a: str, b: str) -> bool:
    a, b = norm_company(a), norm_company(b)
    if not a or not b:
        return False
    if a == b:
        return True
    short, long_ = sorted((a, b), key=len)
    return len(short) >= 4 and re.search(rf"\b{re.escape(short)}\b", long_) is not None


def get_json(url: str, headers: dict | None = None, retries: int = 3):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                if "api.openalex.org" in url:
                    openalex_budget["remaining_usd"] = r.headers.get("X-RateLimit-Remaining-USD")
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < retries - 1:
                time.sleep(int(e.headers.get("Retry-After") or 0) or 2 ** (attempt + 1))
                continue
            raise


# ---------------------------------------------------------------- connections

def read_connections(path: Path) -> list[dict]:
    """LinkedIn's Connections.csv starts with a few note lines before the header."""
    lines = Path(path).read_text(encoding="utf-8-sig", errors="replace").splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith("First Name")), None)
    if start is None:
        raise ValueError(f"{path}: no 'First Name,...' header row (is this LinkedIn's Connections.csv?)")
    return list(csv.DictReader(lines[start:]))


def scan_connections(company: str, rows: list[dict], aliases=()) -> list[dict]:
    out = []
    for r in rows:
        if any(same_company(name, r.get("Company", "")) for name in (company, *aliases)):
            out.append({
                "name": f"{r.get('First Name', '')} {r.get('Last Name', '')}".strip(),
                "title": r.get("Position", ""),
                "company_listed": r.get("Company", ""),
                "connected_on": r.get("Connected On", ""),
                "link": r.get("URL", ""),
                "email": r.get("Email Address", ""),
                "source": "connections",
                "confidence": "High (1st-degree connection; company as of the export date)",
            })
    return out


def connections_status(path: Path, status: str) -> str:
    """One line on the connections export: not added (and whether it was skipped) or its age."""
    if not path.is_file():
        if status == "skipped":
            return "skipped at setup (/job-hunt-studio:outreach setup adds it)"
        if status == "added":
            return f"set up, but {path.name} is missing; ask for a fresh export (/job-hunt-studio:outreach setup)"
        return "not set up (optional): /job-hunt-studio:outreach setup adds the LinkedIn connections export"
    age = (dt.date.today() - dt.date.fromtimestamp(path.stat().st_mtime)).days
    return f"{age} days old" + ("; over 90 days, suggest a fresh export" if age > 90 else "")


def check_connections(path: Path) -> None:
    rows = read_connections(path)
    counts: dict[str, int] = {}
    for r in rows:
        name = (r.get("Company") or "").strip()
        if name:
            counts[name] = counts.get(name, 0) + 1
    top = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:15]
    print(f"OK: {len(rows)} connections, {len(counts)} companies; file {connections_status(path, 'added')}")
    print("Most common companies: " + ("; ".join(f"{c} ({n})" for c, n in top) or "none listed"))


# ---------------------------------------------------------------- research

def resolve_institutions(company: str, override: str | None = None):
    """OpenAlex institution ids for the company: exact name matches, else the best match."""
    if override:
        ids = [i.strip().rsplit("/", 1)[-1] for i in override.split(",") if i.strip()]
        return [{"id": i, "display_name": "(given)", "works_count": None} for i in ids], []
    q = urllib.parse.urlencode({"search": plain_name(company), "per-page": 10,
                                "select": "id,display_name,type,country_code,works_count"})
    found = get_json(f"{OPENALEX}/institutions?{q}").get("results", [])
    for f in found:
        f["id"] = f["id"].rsplit("/", 1)[-1]
    exact = [f for f in found if norm_company(f["display_name"]) == norm_company(company)]
    picked = exact or [f for f in found[:1] if same_company(company, f["display_name"])]
    return picked, [f for f in found if f not in picked][:5]


def topic_hits(title: str, topics: list[str]) -> list[str]:
    t = (title or "").casefold()
    return [k for k in topics if k.casefold() in t]


def scan_research(company: str, topics: list[str], since: str, institution: str | None = None,
                  max_works: int = 400):
    insts, others = resolve_institutions(company, institution)
    meta = {"institutions": insts, "other_matches": others, "since": since}
    ids = {i["id"] for i in insts}
    if ids:
        where = f"authorships.institutions.id:{'|'.join(sorted(ids))}"

        def at_company(a):
            return bool(ids & {(i.get("id") or "").rsplit("/", 1)[-1] for i in a.get("institutions", [])})
    else:
        # Young companies often have no institution record yet; match the affiliation text instead.
        meta["note"] = ("no OpenAlex institution record; matched the affiliation text instead "
                        "(pass --institution I<id> if one of other_matches is right)")
        where = f"raw_affiliation_strings.search:{plain_name(company)}"

        def at_company(a):
            return any(same_company(company, s) or norm_company(company) in norm(s)
                       for s in a.get("raw_affiliation_strings", []))
    works, cursor = [], "*"
    while cursor and len(works) < max_works:
        q = urllib.parse.urlencode({
            "filter": f"{where},from_publication_date:{since}",
            "sort": "publication_date:desc", "per-page": 200, "cursor": cursor,
            "select": "id,title,publication_date,doi,primary_location,authorships"})
        page = get_json(f"{OPENALEX}/works?{q}")
        works += page.get("results", [])
        meta["works_total"] = page.get("meta", {}).get("count")
        cursor = page.get("meta", {}).get("next_cursor")
    meta["works_read"] = len(works)
    return rank_authors(works, at_company, topics), meta


def rank_authors(works: list[dict], at_company, topics: list[str], today: dt.date | None = None) -> list[dict]:
    people: dict[str, dict] = {}
    for w in works:
        hits = topic_hits(w.get("title"), topics)
        link = (w.get("primary_location") or {}).get("landing_page_url") or w.get("doi") or w["id"]
        for a in w.get("authorships", []):
            if not at_company(a) or not (a.get("author") or {}).get("id"):
                continue  # another affiliation, or an unresolved author record
            aid = a["author"]["id"].rsplit("/", 1)[-1]
            # OpenAlex often splits one person into several author records: merge them by name
            key = " ".join(unicodedata.normalize("NFKD", a["author"].get("display_name") or aid).encode(
                "ascii", "ignore").decode().casefold().replace(".", " ").split()) or aid
            p = people.setdefault(key, {
                "name": a["author"].get("display_name", ""), "openalex": f"https://openalex.org/{aid}",
                "openalex_records": set(),
                "orcid": a["author"].get("orcid"), "papers": 0, "on_topic": 0, "last_author": 0,
                "latest": "", "affiliation_strings": set(), "titles": [], "source": "research"})
            p["openalex_records"].add(aid)
            p["papers"] += 1
            p["on_topic"] += bool(hits)
            p["last_author"] += a.get("author_position") == "last"
            p["latest"] = max(p["latest"], w.get("publication_date") or "")
            p["affiliation_strings"].update(s for s in a.get("raw_affiliation_strings", []) if s)
            p["titles"].append({"title": w.get("title"), "date": w.get("publication_date"), "link": link,
                                "topics": hits})
    year_ago = ((today or dt.date.today()) - dt.timedelta(days=365)).isoformat()
    out = []
    for p in people.values():
        p["titles"].sort(key=lambda t: (len(t["topics"]), t["date"] or ""), reverse=True)
        p["titles"] = p["titles"][:3]
        p["affiliation_strings"] = sorted(p["affiliation_strings"])[:3]
        p["openalex_records"] = len(p["openalex_records"])
        p["score"] = 3 * p["on_topic"] + p["papers"] + 2 * p["last_author"] + 2 * (p["latest"] >= year_ago)
        p["confidence"] = ("Medium (paper with this affiliation in the last 12 months)" if p["latest"] >= year_ago
                           else "Low (last paper with this affiliation over a year ago; may have left)")
        out.append(p)
    out.sort(key=lambda p: (p["score"], p["latest"]), reverse=True)
    return out


# ---------------------------------------------------------------- github

def gh_available() -> bool:
    if not shutil.which("gh"):
        return False
    return subprocess.run(["gh", "auth", "status"], capture_output=True).returncode == 0


def github_api(path: str, use_gh: bool):
    if use_gh:
        r = subprocess.run(["gh", "api", path], capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            raise RuntimeError(r.stderr.strip() or f"gh api {path} failed")
        return json.loads(r.stdout or "null")
    return get_json(f"https://api.github.com/{path}", {"Accept": "application/vnd.github+json"})


def find_orgs(company: str, use_gh: bool):
    key = norm_company(company).replace(" ", "")
    q = urllib.parse.quote(f"{plain_name(company)} type:org")
    logins = [i["login"] for i in github_api(f"search/users?q={q}&per_page=10", use_gh).get("items", [])]
    cands = [lg for lg in logins if key and norm(lg).replace(" ", "").startswith(key)]
    orgs = []
    for lg in cands[:4]:
        o = github_api(f"users/{lg}", use_gh)
        if o.get("public_repos") or o.get("followers"):  # some companies keep code private but list members
            orgs.append(o)
    orgs.sort(key=lambda o: (bool(o.get("blog")), o.get("followers", 0)), reverse=True)
    return [o["login"] for o in orgs[:2]], [lg for lg in logins if lg not in cands][:5]


def github_confidence(company: str, orgs: list[str], field: str, member: bool) -> str:
    if same_company(company, field) or any(same_company(o, field) for o in orgs):
        return "Medium (profile names the company)"
    if norm(field):
        return f"Low (profile names {field.strip()}; may have left)"
    if member:
        return "Medium (public org member)"
    return "Low (contributor only; may be outside the company)"


def scan_github(company: str, orgs: list[str], use_gh: bool, n_repos: int = 5, n_profiles: int | None = None):
    n_profiles = n_profiles or (25 if use_gh else 12)
    meta = {"auth": "gh CLI" if use_gh else "anonymous (60 calls an hour)"}
    if not orgs:
        orgs, meta["other_orgs"] = find_orgs(company, use_gh)
        meta["orgs_detected"] = True
    meta["orgs"] = orgs
    if not orgs:
        meta["note"] = "no GitHub organization matched; pass --github <org> if the company has one"
        return [], meta

    people: dict[str, dict] = {}
    for org in orgs:
        for m in github_api(f"orgs/{org}/public_members?per_page=100", use_gh) or []:
            people.setdefault(m["login"], {"login": m["login"], "member_of": set(), "repos": {}})["member_of"].add(org)
        repos = github_api(f"orgs/{org}/repos?sort=pushed&per_page=30", use_gh) or []
        repos = [r for r in repos if not r.get("fork") and not r.get("archived")]
        repos.sort(key=lambda r: r.get("stargazers_count", 0), reverse=True)
        for r in repos[:n_repos]:
            try:
                contributors = github_api(f"repos/{r['full_name']}/contributors?per_page=30", use_gh) or []
            except (RuntimeError, urllib.error.HTTPError):
                continue  # empty or very large repositories can refuse the contributor list
            for c in contributors:
                if c.get("type") != "User" or BOTS.search(c["login"]):
                    continue
                p = people.setdefault(c["login"], {"login": c["login"], "member_of": set(), "repos": {}})
                p["repos"][r["full_name"]] = c.get("contributions", 0)

    ranked = sorted(people.values(), key=lambda p: (bool(p["member_of"]), sum(p["repos"].values())), reverse=True)
    out = []
    for p in ranked[:n_profiles]:
        try:
            u = github_api(f"users/{p['login']}", use_gh)
        except (RuntimeError, urllib.error.HTTPError) as e:
            log(f"  github: profile {p['login']} skipped ({e})")
            continue
        out.append({
            "name": u.get("name") or p["login"], "login": p["login"], "link": u.get("html_url"),
            "company_field": u.get("company"), "location": u.get("location"), "bio": u.get("bio"),
            "blog": u.get("blog"), "public_email": u.get("email"), "member_of": sorted(p["member_of"]),
            "top_repos": sorted(p["repos"].items(), key=lambda kv: kv[1], reverse=True)[:3],
            "source": "github",
            "confidence": github_confidence(company, orgs, u.get("company") or "", bool(p["member_of"])),
        })
    rank = {"Medium (profile names the company)": 0, "Medium (public org member)": 1}
    out.sort(key=lambda p: rank.get(p["confidence"], 2))
    return out, meta


# ---------------------------------------------------------------- next steps

def field_words(cfg) -> str:
    """The field of the first target title, for search queries: 'Machine Learning Engineer' -> 'Machine Learning'."""
    titles = cfg.get("target.titles") or []
    if not titles:
        return ""
    core = " ".join(ROLE_WORDS.sub(" ", re.sub(r"[,/()-]", " ", titles[0])).split())
    return core or titles[0]


def web_queries(company: str, location: str, cfg) -> list[dict]:
    """WebSearch ignores 'site:' in the query; its allowed_domains filter works and returns indexed LinkedIn
    profile titles and snippets without anyone opening linkedin.com."""
    name = plain_name(company)
    loc = f" {location}" if location else ""
    field = field_words(cfg)
    roles = cfg.get("outreach.search_roles") or [*(cfg.get("target.titles") or [])[:2], *DEFAULT_ROLES]
    q = [{"query": f"{name} {r}{loc}", "allowed_domains": LINKEDIN_DOMAINS, "for": "role"} for r in roles]
    q += [{"query": f"{name} {s}{loc}", "allowed_domains": LINKEDIN_DOMAINS, "for": f"tie: alumni of {s}"}
          for s in cfg.get("candidate.schools") or []]
    q += [{"query": f"{name} {e}{loc}", "allowed_domains": LINKEDIN_DOMAINS, "for": f"tie: also worked at {e}"}
          for e in cfg.get("candidate.past_employers") or [] if not same_company(company, e)]
    q += [{"query": f"{name} hiring in my team {field}{loc}".strip(), "allowed_domains": LINKEDIN_DOMAINS,
           "for": "hiring post"},
          {"query": f'{name} "Head of" OR "Director of" OR "VP" {field}'.strip(), "for": "leaders"},
          {"query": f"{name} {field} team lead talk conference podcast speaker".replace("  ", " "), "for": "leaders"},
          {"query": f"{name} engineering blog {field} author".replace("  ", " "), "for": "authors"},
          {"query": name, "allowed_domains": ["theorg.com"], "for": "executives"}]
    return q


def paste_requests(company: str, location: str, cfg) -> list[str]:
    name = plain_name(company)
    loc = f" with location {location}" if location else ""
    field = field_words(cfg) or "your field"
    schools = cfg.get("candidate.schools") or []
    out = [f"LinkedIn search (by hand): People, current company {name}{loc}, keywords \"{field}\" (then "
           "\"manager\"); select all on the results page, copy, paste here."]
    out += [f"{s} alumni (by hand): the school's LinkedIn page > Alumni, \"Where they work\": {name}; select all, "
            "copy, paste." for s in schools[:1]]
    out += ["\"Meet the hiring team\" on the posting you applied to, if it shows one: paste the names and titles.",
            "For a target shown as 2nd degree: the \"mutual connections\" list on their profile, to ask someone you "
            "know for an introduction."]
    return out


# ---------------------------------------------------------------- reporting

def cell(text) -> str:
    return str(text or "").replace("|", "/").replace("\n", " ").strip()


def report(company: str, result: dict) -> str:
    lines = [f"## {company}", ""]
    for src in ("connections", "research", "github"):
        if src not in result["sources"]:
            continue
        s = result["sources"][src]
        lines.append(f"### {src}: {len(s['people'])} found")
        if s.get("error"):
            lines.append(f"Error: {s['error']}")
        if s["meta"].get("note"):
            lines.append(f"Note: {s['meta']['note']}")
        if src == "research" and "works_read" in s["meta"]:
            insts = ", ".join(f"{i['display_name']} ({i['id']})" for i in s["meta"]["institutions"]) \
                or "affiliation text"
            lines.append(f"OpenAlex: {insts}; {s['meta']['works_read']} papers since {s['meta']['since']}"
                         + ("" if result["topics"] else "; no outreach.topics set, so authors are ranked by "
                            "paper count and recency only"))
        if src == "github" and s["meta"].get("orgs"):
            lines.append(f"Orgs: {', '.join(s['meta']['orgs'])}"
                         + (" (detected; check)" if s["meta"].get("orgs_detected") else ""))
        lines.append("")
        top = s["people"][:12]
        if not top:
            continue
        if src == "connections":
            lines += ["| Name | Position | Connected | Link |", "|---|---|---|---|"]
            lines += [f"| {cell(p['name'])} | {cell(p['title'])} | {cell(p['connected_on'])} | {p['link']} |"
                      for p in top]
        elif src == "research":
            lines += ["| Name | Papers (on topic, last author) | Latest | Closest paper | Link |",
                      "|---|---|---|---|---|"]
            lines += [f"| {cell(p['name'])} | {p['papers']} ({p['on_topic']}, {p['last_author']}) | {p['latest']} "
                      f"| {cell(p['titles'][0]['title'])[:90]} | {p['titles'][0]['link']} |" for p in top]
        else:
            lines += ["| Name | Company field | Location | Confidence | Link |", "|---|---|---|---|---|"]
            lines += [f"| {cell(p['name'])} | {cell(p['company_field'])} | {cell(p['location'])} "
                      f"| {cell(p['confidence'])} | {p['link']} |" for p in top]
        lines.append("")
    lines += ["### Next: web searches (WebSearch; pass allowed_domains where given; read titles and snippets only)",
              ""]
    lines += [f"- `{q['query']}`" + (f" allowed_domains={q['allowed_domains']}" if q.get("allowed_domains") else "")
              + f" ({q['for']})" for q in result["web_queries"]] + [""]
    lines += ["### Last resort: ask the user to paste", ""] + [f"- {p}" for p in result["paste_requests"]] + [""]
    return "\n".join(lines)


def slug(text: str) -> str:
    return norm(plain_name(text)).replace(" ", "-") or "company"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("companies", nargs="?", help="company name, or a comma-separated list")
    ap.add_argument("--check-connections", action="store_true",
                    help="check the connections export (row count, top companies, age), then exit")
    ap.add_argument("--location", help="city for the search queries (default: outreach.default_location)")
    ap.add_argument("--sources", default="connections,research,github")
    ap.add_argument("--topics", help="comma-separated title words (default: outreach.topics)")
    ap.add_argument("--since", help="earliest paper date, YYYY-MM-DD (default: two years ago)")
    ap.add_argument("--institution", help="OpenAlex institution id(s), comma-separated (one company only)")
    ap.add_argument("--github", help="GitHub org(s), comma-separated (one company only)")
    ap.add_argument("--connections", help="path to Connections.csv (default: outreach.connections_csv)")
    args = ap.parse_args()
    utf8_stdout()
    try:
        cfg = load()
    except ConfigError as exc:
        print(f"ERROR: {exc}")
        return 1
    conn_path = Path(args.connections) if args.connections else \
        cfg.root / (cfg.get("outreach.connections_csv") or "applications/outreach/private/Connections.csv")
    status = str(cfg.get("outreach.connections") or "unset")
    if args.check_connections:
        if not conn_path.is_file():
            print(f"Not found: {conn_path}")
            return 1
        try:
            check_connections(conn_path)
        except ValueError as exc:
            print(f"ERROR: {exc}")
            return 1
        return 0
    if not args.companies:
        ap.error("give a company (or --check-connections)")
    companies = [c.strip() for c in args.companies.split(",") if c.strip()]
    if len(companies) > 1 and (args.institution or args.github):
        ap.error("--institution and --github need a single company")
    sources = {s.strip() for s in args.sources.split(",")}
    topics = [t.strip() for t in (args.topics.split(",") if args.topics else cfg.get("outreach.topics") or [])
              if str(t).strip()]
    location = args.location if args.location is not None else (cfg.get("outreach.default_location") or "")
    since = args.since or (dt.date.today() - dt.timedelta(days=730)).isoformat()
    today = dt.date.today().isoformat()
    aliases = cfg.get("outreach.aliases") or {}

    conn_rows = None
    if "connections" in sources and conn_path.is_file():
        try:
            conn_rows = read_connections(conn_path)
            log(f"connections: {len(conn_rows)} rows from {conn_path.name}")
        except ValueError as exc:
            log(f"connections: {exc}")
    use_gh = "github" in sources and gh_available()

    raw = cfg.root / "applications" / "outreach" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    reports = []
    for company in companies:
        log(f"== {company}")
        result = {"company": company, "date": today, "location": location, "topics": topics, "sources": {}}
        jobs = {
            "connections": lambda: ((scan_connections(company, conn_rows, aliases.get(company, [])), {})
                                    if conn_rows is not None else None),
            "research": lambda: scan_research(company, topics, since, args.institution),
            "github": lambda: scan_github(company, [o.strip() for o in (args.github or "").split(",") if o.strip()],
                                          use_gh),
        }
        for src in ("connections", "research", "github"):
            if src not in sources:
                continue
            try:
                got = jobs[src]()
                if got is None:
                    continue
                people, meta = got
                result["sources"][src] = {"people": people, "meta": meta}
            except Exception as e:  # one source failing must not lose the others
                result["sources"][src] = {"people": [], "meta": {}, "error": f"{type(e).__name__}: {e}"}
            log(f"  {src}: {len(result['sources'][src]['people'])}")
        result["web_queries"] = web_queries(company, location, cfg)
        result["paste_requests"] = paste_requests(company, location, cfg)
        out = raw / f"people_{slug(company)}_{today}.json"
        out.write_bytes(json.dumps(result, indent=2, ensure_ascii=False, default=sorted).encode("utf-8"))
        reports.append(report(company, result) + f"Saved: `{out.relative_to(cfg.root).as_posix()}`\n")

    if "connections" in sources:
        reports.append(f"Connections export: {connections_status(conn_path, status)}")
    if openalex_budget.get("remaining_usd"):
        reports.append(f"OpenAlex keyless budget left today: ${openalex_budget['remaining_usd']}")
    print("\n".join(reports))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
