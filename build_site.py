"""Build a static SEO-optimized web directory from latest_jobs.json."""

import json
import os
import statistics
from pathlib import Path
from datetime import datetime

DATA_FILE = Path("data/latest_jobs.json")
DIST_DIR = Path("dist")
RAPIDAPI_URL = "https://rapidapi.com/PradeepKumarKesharwani/api/salaryscout"
GITHUB_URL = "https://github.com/nxtcraft/salaryscout"


def load_jobs():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def median_salary(jobs):
    salaries = [j["salary"]["min"] for j in jobs if j.get("salary", {}).get("min")]
    return int(statistics.median(salaries)) if salaries else 0


def format_salary(job):
    s = job.get("salary", {})
    mn, mx = s.get("min"), s.get("max")
    if mn and mx:
        return f"${mn:,} – ${mx:,} / yr"
    if mn:
        return f"${mn:,}+ / yr"
    return "Salary not disclosed"


def salary_class(job):
    mn = job.get("salary", {}).get("min")
    if not mn:
        return "no-salary"
    if mn >= 150000:
        return "salary-high"
    if mn >= 100000:
        return "salary-mid"
    return "salary-low"


def top_tags(jobs, n=20):
    counts = {}
    for job in jobs:
        for t in job.get("tags", []):
            counts[t] = counts.get(t, 0) + 1
    return [t for t, _ in sorted(counts.items(), key=lambda x: -x[1])[:n]]


def job_schema(job):
    s = job.get("salary", {})
    schema = {
        "@type": "JobPosting",
        "title": job["role"],
        "hiringOrganization": {"@type": "Organization", "name": job["company"]},
        "jobLocation": {"@type": "Place", "name": job.get("location", "Remote")},
        "employmentType": "FULL_TIME",
        "workHours": "Remote",
        "url": job.get("apply_url", ""),
        "datePosted": job.get("source_date", "")[:10],
    }
    if s.get("min") and s.get("max"):
        schema["baseSalary"] = {
            "@type": "MonetaryAmount",
            "currency": "USD",
            "value": {
                "@type": "QuantitativeValue",
                "minValue": s["min"],
                "maxValue": s["max"],
                "unitText": "YEAR",
            },
        }
    return schema


def build_index(jobs):
    med = median_salary(jobs)
    salary_jobs = [j for j in jobs if j.get("salary", {}).get("min")]
    tags = top_tags(jobs)
    updated = datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")

    item_list_schema = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Remote Tech Jobs with Salary Data",
        "description": "Real-time remote tech job listings with normalized salary data",
        "url": "https://nxtcraft.github.io/salaryscout",
        "numberOfItems": len(jobs),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "item": job_schema(j)}
            for i, j in enumerate(jobs[:50])
        ],
    }

    cards_html = ""
    for job in jobs:
        tag_chips = "".join(
            f'<button class="chip" onclick="filterTag(\'{t}\')">{t}</button>'
            for t in job.get("tags", [])[:6]
        )
        sal_label = format_salary(job)
        sal_cls = salary_class(job)
        sal_min = job.get("salary", {}).get("min") or 0
        tag_str = " ".join(job.get("tags", []))
        cards_html += f"""
<article class="card" data-tags="{tag_str}" data-salary="{sal_min}">
  <div class="card-top">
    <div>
      <h2 class="role">{job["role"]}</h2>
      <span class="company">{job["company"]}</span>
      <span class="location">📍 {job.get("location","Remote")}</span>
    </div>
    <span class="salary-badge {sal_cls}">{sal_label}</span>
  </div>
  <div class="tags">{tag_chips}</div>
  <a class="apply-btn" href="{job.get('apply_url','#')}" target="_blank" rel="noopener">Apply Direct →</a>
</article>"""

    tag_filter_options = "".join(
        f'<button class="tag-btn" onclick="filterTag(\'{t}\')">{t}</button>'
        for t in tags
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<meta name="description" content="Browse {len(jobs)} live remote tech jobs with real salary data. Filter by skill (Python, React, AWS) and minimum salary. Updated every 12 hours."/>
<meta name="keywords" content="remote tech jobs, remote salary data, python remote jobs, react remote salary, aws remote jobs, remote developer salary"/>
<meta property="og:title" content="SalaryScout — Real-Time Remote Tech Compensation &amp; Jobs"/>
<meta property="og:description" content="Live remote salary intelligence for {len(jobs)} tech roles. Filter by skill and salary."/>
<meta property="og:type" content="website"/>
<meta property="og:url" content="https://nxtcraft.github.io/salaryscout"/>
<title>SalaryScout — Real-Time Remote Tech Compensation &amp; Jobs</title>
<script type="application/ld+json">{json.dumps(item_list_schema, indent=2)}</script>
<style>
:root{{
  --bg:#0f1117;--bg2:#161b27;--card:#1a2236;--border:#1e293b;
  --fg:#f1f5f9;--fg2:#94a3b8;--fg3:#475569;
  --accent:#6366f1;--accent2:#38bdf8;--green:#10b981;
  --yellow:#f59e0b;--red:#ef4444;
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--fg);line-height:1.6;min-height:100vh}}
a{{color:var(--accent2);text-decoration:none}}
a:hover{{text-decoration:underline}}

/* Header */
header{{background:linear-gradient(135deg,#1a1060 0%,#0f1117 70%);padding:48px 24px 40px;text-align:center;border-bottom:1px solid var(--border)}}
.live-dot{{display:inline-block;width:8px;height:8px;background:var(--green);border-radius:50%;margin-right:6px;animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
.live-label{{font-size:12px;color:var(--green);font-weight:600;letter-spacing:.5px;margin-bottom:16px}}
h1{{font-size:clamp(1.8rem,4vw,3rem);font-weight:700;background:linear-gradient(135deg,#a5b4fc,#38bdf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:10px}}
.tagline{{color:var(--fg2);font-size:1rem;max-width:520px;margin:0 auto 28px}}

/* CTA Banner */
.cta-banner{{background:linear-gradient(135deg,rgba(99,102,241,.15),rgba(56,189,248,.1));border:1px solid rgba(99,102,241,.3);border-radius:10px;padding:14px 20px;max-width:680px;margin:0 auto;font-size:14px;color:var(--fg2)}}
.cta-banner a{{color:#a5b4fc;font-weight:600}}

/* Stats */
.stats{{display:flex;justify-content:center;gap:0;background:var(--bg2);border-bottom:1px solid var(--border)}}
.stat{{text-align:center;padding:20px 32px;border-right:1px solid var(--border);flex:1;max-width:200px}}
.stat:last-child{{border-right:none}}
.stat-n{{font-size:1.6rem;font-weight:700;color:var(--accent2)}}
.stat-l{{font-size:11px;color:var(--fg3);margin-top:2px;text-transform:uppercase;letter-spacing:.4px}}

/* Controls */
.controls{{max-width:1100px;margin:32px auto;padding:0 20px;display:flex;flex-direction:column;gap:16px}}
.search-row{{display:flex;gap:12px;flex-wrap:wrap}}
#search{{flex:1;min-width:200px;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px 14px;color:var(--fg);font-size:14px;outline:none}}
#search:focus{{border-color:var(--accent2)}}
#salary-select{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px 14px;color:var(--fg);font-size:14px;outline:none;cursor:pointer}}
.tag-filters{{display:flex;flex-wrap:wrap;gap:8px}}
.tag-btn{{background:var(--bg2);border:1px solid var(--border);color:var(--fg2);padding:5px 12px;border-radius:20px;font-size:12px;cursor:pointer;transition:all .15s}}
.tag-btn:hover,.tag-btn.active{{background:var(--accent);color:#fff;border-color:var(--accent)}}
.result-count{{font-size:13px;color:var(--fg3)}}

/* Grid */
.grid{{max-width:1100px;margin:0 auto;padding:0 20px 60px;display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px;display:flex;flex-direction:column;gap:14px;transition:border-color .15s}}
.card:hover{{border-color:var(--accent2)}}
.card.hidden{{display:none}}
.card-top{{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}}
.role{{font-size:15px;font-weight:600;color:var(--fg);margin-bottom:4px}}
.company{{font-size:13px;color:var(--fg2);margin-right:10px}}
.location{{font-size:12px;color:var(--fg3)}}
.salary-badge{{flex-shrink:0;font-size:12px;font-weight:600;padding:5px 10px;border-radius:6px;white-space:nowrap}}
.salary-high{{background:rgba(16,185,129,.15);color:#10b981;border:1px solid rgba(16,185,129,.25)}}
.salary-mid{{background:rgba(99,102,241,.15);color:#a5b4fc;border:1px solid rgba(99,102,241,.25)}}
.salary-low{{background:rgba(245,158,11,.12);color:#f59e0b;border:1px solid rgba(245,158,11,.2)}}
.no-salary{{background:var(--bg2);color:var(--fg3);border:1px solid var(--border)}}
.tags{{display:flex;flex-wrap:wrap;gap:6px}}
.chip{{background:var(--bg2);border:1px solid var(--border);color:var(--fg3);padding:3px 8px;border-radius:4px;font-size:11px;cursor:pointer;transition:all .12s}}
.chip:hover{{background:var(--accent2);color:#fff;border-color:var(--accent2)}}
.apply-btn{{display:inline-block;background:var(--accent);color:#fff;padding:9px 18px;border-radius:7px;font-size:13px;font-weight:600;text-align:center;transition:opacity .15s;align-self:flex-start}}
.apply-btn:hover{{opacity:.85;text-decoration:none}}
.no-results{{display:none;text-align:center;padding:60px 20px;color:var(--fg3)}}
.no-results.show{{display:block}}

footer{{text-align:center;padding:32px 20px;border-top:1px solid var(--border);color:var(--fg3);font-size:12px}}
footer a{{color:var(--accent2)}}

@media(max-width:600px){{
  .stats{{flex-wrap:wrap}}
  .stat{{min-width:50%;border-right:none;border-bottom:1px solid var(--border)}}
  .card-top{{flex-direction:column}}
  .salary-badge{{align-self:flex-start}}
}}
</style>
</head>
<body>
<header>
  <div class="live-label"><span class="live-dot"></span>LIVE — Updated {updated}</div>
  <h1>SalaryScout</h1>
  <p class="tagline">Live remote salary intelligence extracted directly from hiring markets.</p>
  <div class="cta-banner">
    🚀 Building a recruitment tool or data platform?
    <a href="{RAPIDAPI_URL}" target="_blank" rel="noopener">Access our programmatic API on RapidAPI</a>
    — filter by skill, salary, and integrate in minutes.
  </div>
</header>

<div class="stats">
  <div class="stat"><div class="stat-n">{len(jobs)}</div><div class="stat-l">Live Roles</div></div>
  <div class="stat"><div class="stat-n">{len(salary_jobs)}</div><div class="stat-l">With Salary</div></div>
  <div class="stat"><div class="stat-n">${med:,}</div><div class="stat-l">Median Min Salary</div></div>
  <div class="stat"><div class="stat-n">12h</div><div class="stat-l">Refresh Rate</div></div>
</div>

<div class="controls">
  <div class="search-row">
    <input id="search" type="search" placeholder="Search roles, companies, skills..." oninput="applyFilters()"/>
    <select id="salary-select" onchange="applyFilters()">
      <option value="0">All Salaries</option>
      <option value="80000">$80k+</option>
      <option value="100000">$100k+</option>
      <option value="120000">$120k+</option>
      <option value="150000">$150k+</option>
      <option value="180000">$180k+</option>
    </select>
  </div>
  <div class="tag-filters" id="tag-filters">
    <span style="font-size:12px;color:var(--fg3);align-self:center;margin-right:4px">Filter:</span>
    {tag_filter_options}
    <button class="tag-btn active" onclick="clearFilters()" id="clear-btn" style="display:none">✕ Clear</button>
  </div>
  <div class="result-count" id="result-count">{len(jobs)} roles shown</div>
</div>

<div class="grid" id="grid">
{cards_html}
</div>
<div class="no-results" id="no-results">No roles match your filters. <a href="#" onclick="clearFilters();return false">Clear filters</a></div>

<footer>
  <p>Data sourced from <a href="https://remoteok.com" target="_blank">RemoteOK</a> · Auto-refreshed every 12 hours ·
  <a href="{RAPIDAPI_URL}" target="_blank">API Access</a> ·
  <a href="{GITHUB_URL}" target="_blank">GitHub</a></p>
</footer>

<script>
let activeTag = null;

function applyFilters() {{
  const q = document.getElementById('search').value.toLowerCase();
  const minSal = parseInt(document.getElementById('salary-select').value) || 0;
  const cards = document.querySelectorAll('.card');
  let visible = 0;
  cards.forEach(card => {{
    const tags = card.dataset.tags || '';
    const text = card.innerText.toLowerCase();
    const sal = parseInt(card.dataset.salary) || 0;
    const matchQ = !q || text.includes(q);
    const matchSal = sal >= minSal;
    const matchTag = !activeTag || tags.split(' ').includes(activeTag);
    const show = matchQ && matchSal && matchTag;
    card.classList.toggle('hidden', !show);
    if (show) visible++;
  }});
  document.getElementById('result-count').textContent = visible + ' roles shown';
  document.getElementById('no-results').classList.toggle('show', visible === 0);
  document.getElementById('clear-btn').style.display = (q || minSal || activeTag) ? 'inline-block' : 'none';
}}

function filterTag(tag) {{
  activeTag = (activeTag === tag) ? null : tag;
  document.querySelectorAll('.tag-btn').forEach(b => b.classList.toggle('active', b.textContent === tag && activeTag));
  applyFilters();
}}

function clearFilters() {{
  activeTag = null;
  document.getElementById('search').value = '';
  document.getElementById('salary-select').value = '0';
  document.querySelectorAll('.tag-btn').forEach(b => b.classList.remove('active'));
  applyFilters();
}}
</script>
</body>
</html>"""
    return html


def main():
    print("Loading jobs...")
    jobs = load_jobs()
    print(f"Loaded {len(jobs)} jobs.")

    DIST_DIR.mkdir(exist_ok=True)

    print("Building index.html...")
    index_html = build_index(jobs)
    (DIST_DIR / "index.html").write_text(index_html, encoding="utf-8")

    # robots.txt and sitemap
    (DIST_DIR / "robots.txt").write_text(
        "User-agent: *\nAllow: /\nSitemap: https://nxtcraft.github.io/salaryscout/sitemap.xml\n"
    )
    (DIST_DIR / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        "  <url><loc>https://nxtcraft.github.io/salaryscout/</loc>"
        f"<lastmod>{datetime.utcnow().strftime('%Y-%m-%d')}</lastmod>"
        "<changefreq>daily</changefreq><priority>1.0</priority></url>\n"
        "</urlset>\n"
    )

    print(f"Done. Files in {DIST_DIR}/:")
    for f in sorted(DIST_DIR.iterdir()):
        print(f"  {f.name} ({f.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
