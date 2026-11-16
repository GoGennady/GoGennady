"""Draws the GitLab contribution graph for the profile README.

Input: GitLab's public calendar (https://gitlab.com/users/<name>/calendar.json, {"YYYY-MM-DD": count}).
Output: activity-dark.svg and activity-light.svg. No dependencies.

    python3 gitlab_activity.py calendar.json out_dir [YYYY-MM-DD]

Writes nothing when the calendar is empty, so a failed or private fetch keeps the last good graph.
"""
import datetime as dt
import json
import pathlib
import sys

FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
THEMES = {
    "dark": dict(bg="#0d1117", panel1="#161b22", panel2="#0d1117", stroke="#262c36", text="#e6edf3", muted="#8b949e",
                 cells=["#28272d", "#743218", "#a64824", "#d96835", "#eebb63"]),
    "light": dict(bg="#ffffff", panel1="#f6f8fa", panel2="#ffffff", stroke="#d8dee4", text="#1f2328", muted="#59636e",
                  cells=["#ececef", "#eebb63", "#d96835", "#a64824", "#743218"]),
}
TANUKI = ('<path d="m24.507 9.5-.034-.09L21.082.562a.896.896 0 0 0-1.694.091l-2.29 7.01H7.825L5.535.653a.898.898 0 0 0-1.694-.09L.451 9.411.416 9.5a6.297 6.297 0 0 0 2.09 7.278l.012.01.03.022 5.16 3.867 2.56 1.935 1.554 1.176a1.051 1.051 0 0 0 1.268 0l1.555-1.176 2.56-1.935 5.197-3.89.014-.01A6.297 6.297 0 0 0 24.507 9.5Z" fill="#E24329"/>'
          '<path d="m24.507 9.5-.034-.09a11.44 11.44 0 0 0-4.56 2.051l-7.447 5.632 4.742 3.584 5.197-3.89.014-.01A6.297 6.297 0 0 0 24.507 9.5Z" fill="#FC6D26"/>'
          '<path d="m7.707 20.677 2.56 1.935 1.555 1.176a1.051 1.051 0 0 0 1.268 0l1.555-1.176 2.56-1.935-4.743-3.584-4.755 3.584Z" fill="#FCA326"/>'
          '<path d="M5.01 11.461a11.43 11.43 0 0 0-4.56-2.05L.416 9.5a6.297 6.297 0 0 0 2.09 7.278l.012.01.03.022 5.16 3.867 4.745-3.584-7.444-5.632Z" fill="#FC6D26"/>')

W = 880
CELL, GAP, R = 12, 3, 2.5
STEP = CELL + GAP
WEEKS = 53
PAD = 24
GX = W - PAD - (WEEKS * STEP - GAP)
GY = 76
LY = GY + 7 * STEP + 12
H = LY + CELL + 22


def level(n):
    """GitLab's own thresholds: 0, 1-9, 10-19, 20-29, 30+."""
    return 0 if n <= 0 else 1 if n < 10 else 2 if n < 20 else 3 if n < 30 else 4


def build(cal, today, theme):
    t, cs = THEMES[theme], THEMES[theme]["cells"]
    end_sun = today - dt.timedelta(days=(today.weekday() + 1) % 7)  # weeks start on Sunday
    start = end_sun - dt.timedelta(weeks=WEEKS - 1)
    total = sum(v for k, v in cal.items() if start.isoformat() <= k <= today.isoformat())
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
         f'aria-label="GitLab activity: {total:,} contributions in the last year">',
         f'<defs><linearGradient id="p" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t["panel1"]}"/>'
         f'<stop offset="1" stop-color="{t["panel2"]}"/></linearGradient></defs>',
         f'<rect width="{W}" height="{H}" fill="{t["bg"]}"/>',
         f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" fill="url(#p)" stroke="{t["stroke"]}"/>',
         f'<g font-family="{FONT}">',
         f'<svg x="{PAD}" y="22" width="21" height="20" viewBox="0 0 25 24">{TANUKI}</svg>',
         f'<text x="{PAD + 30}" y="37" font-size="15" font-weight="600" fill="{t["text"]}">Building on GitLab</text>',
         f'<text x="{W - PAD}" y="37" font-size="13" fill="{t["muted"]}" text-anchor="end">'
         f'<tspan fill="{t["text"]}" font-weight="600">{total:,}</tspan> contributions in the last year</text>']
    last_x = -99
    for w in range(WEEKS):
        d0 = start + dt.timedelta(weeks=w)
        first = next((d0 + dt.timedelta(days=i) for i in range(7) if (d0 + dt.timedelta(days=i)).day == 1), None)
        if (w == 0 and d0.day <= 7) or first:
            x = GX + w * STEP
            if x - last_x >= 3 * STEP:
                s.append(f'<text x="{x}" y="{GY - 8}" font-size="11" fill="{t["muted"]}">{(first or d0).strftime("%b")}</text>')
                last_x = x
    for i, name in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        s.append(f'<text x="{GX - 8}" y="{GY + i * STEP + 10}" font-size="10" fill="{t["muted"]}" text-anchor="end">{name}</text>')
    for w in range(WEEKS):
        for i in range(7):
            d = start + dt.timedelta(weeks=w, days=i)
            if d > today:
                continue
            n = cal.get(d.isoformat(), 0)
            s.append(f'<rect x="{GX + w * STEP}" y="{GY + i * STEP}" width="{CELL}" height="{CELL}" rx="{R}" '
                     f'fill="{cs[level(n)]}"><title>{n} on {d:%b} {d.day}</title></rect>')
    lx = W - PAD - 5 * STEP + GAP - 32
    s.append(f'<text x="{lx - 6}" y="{LY + 10}" font-size="11" fill="{t["muted"]}" text-anchor="end">Less</text>')
    for k, c in enumerate(cs):
        s.append(f'<rect x="{lx + k * STEP}" y="{LY}" width="{CELL}" height="{CELL}" rx="{R}" fill="{c}"/>')
    s.append(f'<text x="{lx + 5 * STEP + 3}" y="{LY + 10}" font-size="11" fill="{t["muted"]}">More</text>')
    s.append(f'<text x="{PAD}" y="{LY + 10}" font-size="11" fill="{t["muted"]}">Commits, merge requests, issues and comments, updated daily</text>')
    s.append("</g></svg>")
    return "\n".join(s) + "\n", total


if __name__ == "__main__":
    cal = json.loads(pathlib.Path(sys.argv[1]).read_text() or "{}")
    out = pathlib.Path(sys.argv[2])
    today = dt.date.fromisoformat(sys.argv[3]) if len(sys.argv) > 3 else dt.date.today()
    if not isinstance(cal, dict) or not any(cal.values()):
        print("calendar is empty or private, keeping the last graph")
        sys.exit(0)
    out.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        svg, total = build(cal, today, theme)
        (out / f"activity-{theme}.svg").write_text(svg)
    print(f"ok: {total} contributions")
