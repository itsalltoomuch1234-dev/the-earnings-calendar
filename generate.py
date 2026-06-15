import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta
import time, warnings, json
from zoneinfo import ZoneInfo
warnings.filterwarnings('ignore')

COMPANY_NAMES = {
    "UAA":"Under Armour","AEO":"American Eagle Outfitters",
    "ANF":"Abercrombie & Fitch","VFC":"VF Corporation","GAP":"Gap Inc.",
    "BIRK":"Birkenstock","LEVI":"Levi Strauss & Co.","ONON":"On Holding",
    "LULU":"Lululemon Athletica","DECK":"Deckers Outdoor","NKE":"Nike",
    "DLTR":"Dollar Tree","DG":"Dollar General","ROST":"Ross Stores",
    "TJX":"TJX Companies","GOOS":"Canada Goose","COTY":"Coty Inc.",
    "CPRI":"Capri Holdings","ELF":"e.l.f. Beauty","ULTA":"Ulta Beauty",
    "RL":"Ralph Lauren","TPR":"Tapestry","EL":"Estée Lauder",
    "KSS":"Kohl's","BBWI":"Bath & Body Works","M":"Macy's",
    "ACI":"Albertsons","BBY":"Best Buy","KR":"Kroger","TGT":"Target",
    "LOW":"Lowe's","HD":"Home Depot","COST":"Costco","WMT":"Walmart",
    "NCLH":"Norwegian Cruise Line","RCL":"Royal Caribbean",
    "CCL":"Carnival Corporation","TAP":"Molson Coors",
    "BF-B":"Brown-Forman","STZ":"Constellation Brands",
    "KDP":"Keurig Dr Pepper","PEP":"PepsiCo","KO":"Coca-Cola",
    "BYND":"Beyond Meat","LW":"Lamb Weston","CAG":"Conagra Brands",
    "CPB":"Campbell Soup","SJM":"J.M. Smucker",
    "MKC":"McCormick & Company","HRL":"Hormel Foods",
    "GIS":"General Mills","IFF":"Intl Flavors & Fragrances",
    "KHC":"Kraft Heinz","HSY":"Hershey","MDLZ":"Mondelez International",
    "NWL":"Newell Brands","CLX":"Clorox","CHD":"Church & Dwight",
    "KMB":"Kimberly-Clark","CL":"Colgate-Palmolive",
    "PG":"Procter & Gamble","MO":"Altria Group",
    "PM":"Philip Morris International","MAT":"Mattel","HAS":"Hasbro",
    "DPZ":"Domino's Pizza","DRI":"Darden Restaurants",
    "QSR":"Restaurant Brands Intl","CMG":"Chipotle Mexican Grill",
    "YUM":"Yum! Brands","SBUX":"Starbucks","MCD":"McDonald's",
    "SFD":"Smithfield Foods","TSN":"Tyson Foods","SYY":"Sysco",
    "CART":"Instacart","DASH":"DoorDash",
    "FRT":"Federal Realty","REG":"Regency Centers",
    "KIM":"Kimco Realty","SPG":"Simon Property Group",
    "MAS":"Masco Corporation","BALL":"Ball Corporation",
    "TSCO":"Tractor Supply","AMCR":"Amcor",
    "ROL":"Rollins","CTAS":"Cintas Corporation","IP":"International Paper",
}

SECTORS = {
    "APPAREL & FOOTWEAR":  ["UAA","AEO","ANF","VFC","GAP","BIRK","LEVI","ONON","LULU","DECK","NKE"],
    "OFF-PRICE / DOLLAR":  ["DLTR","DG","ROST","TJX"],
    "LUXURY & BEAUTY":     ["GOOS","COTY","CPRI","ELF","ULTA","RL","TPR","EL"],
    "RETAILERS":           ["KSS","BBWI","M","ACI","BBY","KR","TGT","LOW","HD","COST","WMT"],
    "CRUISES":             ["NCLH","RCL","CCL"],
    "BEVERAGES & ALCOHOL": ["TAP","BF-B","STZ","KDP","PEP","KO"],
    "PACKAGED FOOD":       ["BYND","LW","CAG","CPB","SJM","MKC","HRL","GIS","IFF","KHC","HSY","MDLZ"],
    "CONSUMER GOODS":      ["NWL","CLX","CHD","KMB","CL","PG"],
    "CIGARS":              ["MO","PM"],
    "TOYMAKERS":           ["MAT","HAS"],
    "RESTAURANTS":         ["DPZ","DRI","QSR","CMG","YUM","SBUX","MCD"],
    "MEAT COS":            ["SFD","TSN","SYY"],
    "DELIVERY":            ["CART","DASH"],
    "REAL ESTATE":         ["FRT","REG","KIM","SPG"],
    "RANDOS":              ["MAS","BALL","TSCO","AMCR","ROL","CTAS","IP"],
}

SECTOR_COLORS = {
    "APPAREL & FOOTWEAR":  "#4f8ef7",
    "OFF-PRICE / DOLLAR":  "#9b78d4",
    "LUXURY & BEAUTY":     "#c96b9e",
    "RETAILERS":           "#e07d45",
    "CRUISES":             "#3aada8",
    "BEVERAGES & ALCOHOL": "#5fa85a",
    "PACKAGED FOOD":       "#c9a84c",
    "CONSUMER GOODS":      "#4a9e8a",
    "CIGARS":              "#9e7a55",
    "TOYMAKERS":           "#d45f5f",
    "RESTAURANTS":         "#d47a3a",
    "MEAT COS":            "#9a66c0",
    "DELIVERY":            "#5580d4",
    "REAL ESTATE":         "#6a8fa8",
    "RANDOS":              "#7a8fa0",
}

ALL_TICKERS = [t for v in SECTORS.values() for t in v]

def fetch_nasdaq(start, end):
    out  = {}
    hdrs = {
        "user-agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "accept":          "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "origin":          "https://www.nasdaq.com",
        "referer":         "https://www.nasdaq.com/market-activity/earnings",
        "sec-fetch-dest":  "empty",
        "sec-fetch-mode":  "cors",
        "sec-fetch-site":  "same-site",
    }
    cur = start
    while cur <= end:
        if cur.weekday() >= 5:
            cur += timedelta(days=1)
            continue
        ds = cur.strftime("%Y-%m-%d")
        for attempt in range(3):
            try:
                r = requests.get(
                    f"https://api.nasdaq.com/api/calendar/earnings?date={ds}",
                    headers=hdrs, timeout=15)
                if r.status_code == 429:
                    print(f"  Rate limited {ds} — waiting 15s")
                    time.sleep(15); continue
                if r.status_code != 200:
                    time.sleep(2); continue
                payload = r.json()
                for row in (payload.get("data") or {}).get("rows") or []:
                    sym = row.get("symbol","").upper().strip()
                    if sym in ALL_TICKERS:
                        t = row.get("time","").lower()
                        timing = ("BMO" if "pre" in t else
                                  "AMC" if ("after" in t or "post" in t) else None)
                        out[sym] = {"date": ds, "timing": timing}
                break
            except Exception:
                time.sleep(2)
        cur += timedelta(days=1)
        time.sleep(0.45)
    print(f"NASDAQ: {len(out)} tickers found")
    return out

def fetch_yahoo(ticker):
    try:
        s = yf.Ticker(ticker)
        try:
            cal = s.calendar
            if cal is not None:
                if isinstance(cal, dict):
                    ed = cal.get("Earnings Date")
                    if ed:
                        dates  = ed if isinstance(ed, list) else [ed]
                        future = [d for d in dates if pd.Timestamp(d) > pd.Timestamp.now()]
                        if future:
                            return pd.Timestamp(future[0]).strftime("%Y-%m-%d")
                elif hasattr(cal,"index") and "Earnings Date" in cal.index:
                    dv = cal.loc["Earnings Date"].iloc[0]
                    if pd.notna(dv):
                        return pd.to_datetime(dv).strftime("%Y-%m-%d")
        except Exception:
            pass
        try:
            ed = s.earnings_dates
            if ed is not None and not ed.empty:
                future = ed[ed.index > pd.Timestamp.now()]
                if not future.empty:
                    return future.index[-1].strftime("%Y-%m-%d")
        except Exception:
            pass
    except Exception:
        pass
    return None

def run_fetch():
    today = datetime.now(ZoneInfo("America/New_York"))
    end   = today + timedelta(days=182)
    print(f"EARNINGS CALENDAR REFRESH — {today.strftime('%B %d, %Y %I:%M %p ET')}")

    print("[1/2] NASDAQ API...")
    nasdaq = fetch_nasdaq(today, end)

    print(f"[2/2] Yahoo Finance (all {len(ALL_TICKERS)} tickers for cross-check)...")
    yf_data = {}
    for i, t in enumerate(ALL_TICKERS):
        d = fetch_yahoo(t)
        if d:
            yf_data[t] = d
        time.sleep(0.4)
        if (i+1) % 10 == 0:
            print(f"  {i+1}/{len(ALL_TICKERS)}")

    mismatches = 0
    rows = []
    for sector, tickers in SECTORS.items():
        for t in tickers:
            nd = nasdaq.get(t)
            yd = yf_data.get(t)

            if nd:
                mismatch = bool(yd and yd != nd["date"])
                if mismatch:
                    mismatches += 1
                    print(f"  ⚠ MISMATCH {t}: NASDAQ={nd['date']} Yahoo={yd}")
                rows.append({
                    "Sector":       sector,
                    "Ticker":       t,
                    "Earnings Date": nd["date"],
                    "Timing":       nd["timing"],
                    "Source":       "NASDAQ",
                    "Yahoo Date":   yd if mismatch else None,
                    "Mismatch":     mismatch,
                })
            elif yd:
                rows.append({
                    "Sector":       sector,
                    "Ticker":       t,
                    "Earnings Date": yd,
                    "Timing":       None,
                    "Source":       "Yahoo Finance",
                    "Yahoo Date":   None,
                    "Mismatch":     False,
                })
            else:
                rows.append({
                    "Sector":       sector,
                    "Ticker":       t,
                    "Earnings Date": None,
                    "Timing":       None,
                    "Source":       "—",
                    "Yahoo Date":   None,
                    "Mismatch":     False,
                })

    df = pd.DataFrame(rows)
    print(f"DONE: {df['Earnings Date'].notna().sum()} dates found · "
          f"{df['Earnings Date'].isna().sum()} unannounced · "
          f"{mismatches} mismatches")
    return df, today

def build_html(df, generated_at):
    dated = df[df["Earnings Date"].notna()].copy()
    dated["dt"] = pd.to_datetime(dated["Earnings Date"])

    if dated.empty:
        months = [generated_at.replace(day=1)]
    else:
        mn = dated["dt"].min().replace(day=1)
        mx = dated["dt"].max().replace(day=1)
        months, c = [], mn
        while c <= mx:
            months.append(c)
            c = (c.replace(month=c.month+1) if c.month < 12
                 else c.replace(year=c.year+1, month=1))

    dl = {}
    for _, r in dated.iterrows():
        dl.setdefault(r["dt"].strftime("%Y-%m-%d"), []).append((
            r["Ticker"],
            r["Sector"],
            r["Timing"],
            r["Source"],
            r["Yahoo Date"] if pd.notna(r["Yahoo Date"]) and r["Yahoo Date"] else None,
            bool(r["Mismatch"]),
        ))

    today_str = generated_at.strftime("%Y-%m-%d")
    DAYS = ["MON","TUE","WED","THU","FRI","SAT","SUN"]
    cal  = ""

    for ms in months:
        lbl   = ms.strftime("%B %Y").upper()
        heads = "".join(f'<div class="dname">{d}</div>' for d in DAYS)
        blank = "".join('<div class="dcell empty"></div>' for _ in range(ms.weekday()))
        nm    = (ms.replace(month=ms.month+1) if ms.month < 12
                 else ms.replace(year=ms.year+1, month=1))
        cells = ""

        for day in range(1, (nm - ms).days + 1):
            do   = ms.replace(day=day)
            ds   = do.strftime("%Y-%m-%d")
            cls  = "dcell"
            if do.weekday() >= 5: cls += " wknd"
            if ds == today_str:   cls += " today"
            rpts = dl.get(ds, [])
            if rpts: cls += " has-e"

            chips = ""
            for ticker, sector, timing, source, yahoo_date, mismatch in rpts:
                col  = SECTOR_COLORS.get(sector, "#666")
                safe = sector.replace(" ","_").replace("/","_").replace("&","_")
                cn   = (COMPANY_NAMES.get(ticker, ticker)
                        .replace("'", "\\'").replace('"', "&quot;"))
                st   = sector.replace("'", "\\'")
                yd_safe = (yahoo_date or "").replace("'", "\\'")
                badge = ('<span class="bdg bmo">PRE</span>' if timing == "BMO" else
                         '<span class="bdg amc">AFT</span>' if timing == "AMC" else "")
                warn  = '<span class="bdg warn">⚠</span>' if mismatch else ""
                chips += (
                    f'<div class="chip s-{safe}" style="--cc:{col}" '
                    f'onclick="showCard(\'{ticker}\',\'{cn}\',\'{st}\','
                    f'\'{timing or "TBD"}\',\'{ds}\',\'{col}\',\'{source}\','
                    f'\'{yd_safe}\',{str(mismatch).lower()})">'
                    f'{ticker}{badge}{warn}</div>'
                )

            cells += (f'<div class="{cls}">'
                      f'<span class="dno">{day}</span>'
                      f'<div class="chips">{chips}</div>'
                      f'</div>')

        cal += (f'<div class="mblock">'
                f'<div class="mlabel">{lbl}</div>'
                f'<div class="cgrid">{heads}{blank}{cells}</div>'
                f'</div>')

    unann = df[df["Earnings Date"].isna()]
    uhtml = ""
    if not unann.empty:
        rows_h = ""
        for s, tickers in SECTORS.items():
            miss = unann[unann["Sector"] == s]["Ticker"].tolist()
            if not miss: continue
            col  = SECTOR_COLORS[s]
            safe = s.replace(" ","_").replace("/","_").replace("&","_")
            chips_u = "".join(
                f'<span class="uchip s-{safe}" style="--cc:{col}" '
                f'onclick="showCard(\'{t}\','
                f'\'{COMPANY_NAMES.get(t,t).replace(chr(39), chr(92)+chr(39))}\','
                f'\'{s.replace(chr(39), chr(92)+chr(39))}\','
                f'\'TBD\',\'TBD\',\'{col}\',\'—\',\'\',false)">{t}</span>'
                for t in miss
            )
            rows_h += (f'<tr>'
                       f'<td><span class="sbadge" style="background:{col}">{s}</span></td>'
                       f'<td>{chips_u}</td>'
                       f'</tr>')
        uhtml = (f'<div class="ubox">'
                 f'<div class="ubox-head">'
                 f'<span class="ubox-title">NOT YET ANNOUNCED</span>'
                 f'<span class="ubox-sub">Click any ticker for details</span>'
                 f'</div>'
                 f'<table class="utable">'
                 f'<thead><tr><th>SECTOR</th><th>TICKERS</th></tr></thead>'
                 f'<tbody>{rows_h}</tbody>'
                 f'</table></div>')

    nf = len(dated)
    nu = len(unann)
    nm = int(df["Mismatch"].sum())
    ts = generated_at.strftime("%d %b %Y, %I:%M %p ET")
    sj = json.dumps(SECTORS)
    cj = json.dumps(SECTOR_COLORS)
    nj = json.dumps(COMPANY_NAMES)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="21600">
<title>Earnings Calendar — Consumer &amp; Retail</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg0:#080a12;--bg1:#0d1020;--bg2:#111525;--bg3:#181d30;
  --line:rgba(255,255,255,0.08);--line2:rgba(255,255,255,0.15);
  --t0:#ffffff;--t1:#c8cfe8;--t2:#7a84aa;
  --accent:#4f8ef7;
  --warn:#f7a94f;
  --mono:'JetBrains Mono',monospace;
  --sans:'Inter',-apple-system,sans-serif;
}}
body{{font-family:var(--sans);background:var(--bg0);color:var(--t1);min-height:100vh;-webkit-font-smoothing:antialiased;}}
.topbar{{height:58px;background:var(--bg1);border-bottom:1px solid var(--line2);display:flex;align-items:center;justify-content:space-between;padding:0 28px;position:sticky;top:0;z-index:300;gap:16px;}}
.topbar-left{{display:flex;align-items:center;gap:14px;}}
.page-title{{font-size:15px;font-weight:700;color:var(--t0);letter-spacing:-.2px;white-space:nowrap;}}
.divider{{width:1px;height:22px;background:var(--line2);}}
.topbar-meta{{font-size:11px;color:var(--t1);white-space:nowrap;}}
.topbar-right{{display:flex;align-items:center;gap:20px;flex-shrink:0;}}
.tstat{{display:flex;flex-direction:column;align-items:flex-end;}}
.tstat-num{{font-family:var(--mono);font-size:17px;font-weight:700;color:var(--t0);line-height:1;}}
.tstat-lbl{{font-size:9px;color:var(--t2);text-transform:uppercase;letter-spacing:.7px;margin-top:3px;}}
.timingbar{{background:var(--bg0);border-bottom:1px solid var(--line);padding:7px 28px;display:flex;align-items:center;gap:14px;font-size:11.5px;color:var(--t1);}}
.tpill{{display:inline-flex;align-items:center;gap:4px;font-size:10px;font-weight:700;padding:2px 8px;border-radius:4px;font-family:var(--mono);letter-spacing:.3px;}}
.tpill.pre{{background:rgba(79,142,247,.15);color:#8bbcff;border:1px solid rgba(79,142,247,.3);}}
.tpill.aft{{background:rgba(201,168,76,.15);color:#e0c878;border:1px solid rgba(201,168,76,.3);}}
.tpill.warn{{background:rgba(247,169,79,.15);color:#f7a94f;border:1px solid rgba(247,169,79,.3);}}
.main{{padding:32px 28px;max-width:1600px;margin:0 auto;}}
.mblock{{margin-bottom:52px;}}
.mlabel{{font-family:var(--mono);font-size:13px;font-weight:700;color:var(--t0);margin-bottom:14px;border-bottom:1px solid var(--line);padding-bottom:10px;letter-spacing:.5px;}}
.cgrid{{display:grid;grid-template-columns:repeat(7,1fr);gap:5px;}}
.dname{{text-align:center;font-family:var(--mono);font-size:10px;font-weight:700;color:var(--t1);padding:6px 0;letter-spacing:.8px;}}
.dcell{{background:var(--bg2);border:1px solid var(--line);border-radius:8px;min-height:100px;padding:10px 8px 8px;transition:border-color .12s,background .12s;}}
.dcell.empty{{background:transparent;border-color:transparent;pointer-events:none;}}
.dcell.wknd{{background:#0c0e14;opacity:.4;}}
.dcell.today{{border-color:var(--accent)!important;background:color-mix(in srgb,var(--accent) 7%,var(--bg2));}}
.dcell.today .dno{{color:var(--accent)!important;font-weight:700;}}
.dcell.has-e{{border-color:var(--line2);}}
.dno{{font-family:var(--mono);font-size:11px;font-weight:500;color:var(--t1);margin-bottom:6px;display:block;}}
.chips{{display:flex;flex-wrap:wrap;gap:3px;}}
.chip{{display:inline-flex;align-items:center;gap:3px;background:var(--cc,#444);font-family:var(--mono);font-size:10px;font-weight:700;color:#ffffff;padding:3px 7px;border-radius:5px;cursor:pointer;white-space:nowrap;transition:transform .12s,filter .12s;letter-spacing:.2px;text-shadow:0 1px 2px rgba(0,0,0,.4);}}
.chip:hover{{transform:scale(1.08);filter:brightness(1.18);z-index:10;position:relative;}}
.chip.dim{{opacity:.07;pointer-events:none;}}
.bdg{{font-size:8px;font-weight:900;padding:1px 4px;border-radius:3px;letter-spacing:.4px;line-height:1.4;font-family:var(--mono);}}
.bdg.bmo{{background:rgba(255,255,255,.25);color:#deeeff;}}
.bdg.amc{{background:rgba(0,0,0,.4);color:#ffe090;}}
.bdg.warn{{background:rgba(247,169,79,.3);color:#f7a94f;}}
.ubox{{margin:40px 28px 48px;background:var(--bg2);border:1px solid var(--line);border-radius:12px;overflow:hidden;}}
.ubox-head{{padding:16px 22px;border-bottom:1px solid var(--line);display:flex;align-items:baseline;gap:14px;}}
.ubox-title{{font-family:var(--mono);font-size:13px;font-weight:700;color:var(--t0);letter-spacing:.4px;}}
.ubox-sub{{font-size:11px;color:var(--t1);}}
.utable{{width:100%;border-collapse:collapse;font-size:12px;}}
.utable th{{text-align:left;padding:9px 14px;font-family:var(--mono);font-size:9.5px;font-weight:700;color:var(--t1);border-bottom:1px solid var(--line);text-transform:uppercase;letter-spacing:.6px;}}
.utable td{{padding:9px 14px;border-bottom:1px solid var(--line);vertical-align:middle;}}
.utable tr:last-child td{{border-bottom:none;}}
.sbadge{{font-family:var(--mono);font-size:10px;font-weight:700;color:#fff;padding:3px 9px;border-radius:4px;white-space:nowrap;text-shadow:0 1px 2px rgba(0,0,0,.4);}}
.uchip{{display:inline-flex;align-items:center;background:var(--cc,#444);font-family:var(--mono);font-size:10px;font-weight:700;color:#ffffff;padding:3px 8px;border-radius:5px;margin:2px;cursor:pointer;transition:transform .12s,filter .12s;text-shadow:0 1px 2px rgba(0,0,0,.4);}}
.uchip:hover{{transform:scale(1.07);filter:brightness(1.18);}}
.uchip.dim{{opacity:.07;pointer-events:none;}}
.footer{{border-top:1px solid var(--line);padding:14px 28px;font-family:var(--mono);font-size:10.5px;color:var(--t1);display:flex;justify-content:space-between;align-items:center;}}
.overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.82);backdrop-filter:blur(10px);z-index:999;align-items:center;justify-content:center;}}
.overlay.on{{display:flex;}}
.modal{{background:var(--bg3);border:1px solid var(--line2);border-radius:16px;padding:28px;max-width:400px;width:90%;box-shadow:0 24px 48px rgba(0,0,0,.8);position:relative;animation:popIn .2s cubic-bezier(.34,1.4,.64,1);}}
@keyframes popIn{{from{{transform:scale(.9);opacity:0}}to{{transform:scale(1);opacity:1}}}}
.modal-close{{position:absolute;top:12px;right:14px;background:none;border:none;font-size:22px;color:var(--t1);cursor:pointer;line-height:1;}}
.modal-close:hover{{color:var(--t0);}}
.modal-ticker{{font-family:var(--mono);font-size:30px;font-weight:700;margin-bottom:4px;line-height:1;}}
.modal-name{{font-size:13px;color:var(--t1);margin-bottom:20px;}}
.modal-row{{display:flex;justify-content:space-between;align-items:center;padding:9px 0;border-bottom:1px solid var(--line);font-size:13px;}}
.modal-row:last-child{{border-bottom:none;}}
.modal-key{{color:var(--t2);font-size:11px;text-transform:uppercase;letter-spacing:.6px;font-weight:600;}}
.modal-val{{color:var(--t0);font-family:var(--mono);font-size:12px;font-weight:600;}}
.modal-warn{{background:rgba(247,169,79,.1);border:1px solid rgba(247,169,79,.3);border-radius:8px;padding:10px 12px;margin-bottom:14px;font-size:11px;color:#f7a94f;display:none;}}
.modal-warn.on{{display:block;}}
</style>
</head>
<body>
<header class="topbar">
  <div class="topbar-left">
    <span class="page-title">Earnings Calendar</span>
    <span class="divider"></span>
    <span class="topbar-meta">Consumer &amp; Retail · Updated {ts}</span>
  </div>
  <div class="topbar-right">
    <div class="tstat"><span class="tstat-num" style="color:#4f8ef7">{nf}</span><span class="tstat-lbl">Dates Found</span></div>
    <div class="tstat"><span class="tstat-num" style="color:#9098c0">{nu}</span><span class="tstat-lbl">Unannounced</span></div>
    <div class="tstat"><span class="tstat-num" style="color:#f7a94f">{nm}</span><span class="tstat-lbl">Mismatches</span></div>
  </div>
</header>
<div class="timingbar">
  <span style="color:var(--t0);font-weight:600;font-size:11px;">TIMING KEY</span>
  <span class="tpill pre">PRE</span><span style="font-size:11px;">Before market open</span>
  <span class="tpill aft">AFT</span><span style="font-size:11px;">After market close</span>
  <span class="tpill warn">⚠</span><span style="font-size:11px;">NASDAQ &amp; Yahoo dates differ</span>
  <span style="margin-left:6px;font-size:11px;color:var(--t1);">No badge = time unconfirmed · All times ET</span>
</div>
<main class="main" id="calMain">{cal}</main>
{uhtml}
<footer class="footer">
  <span>Neil J Kanatt · Data: NASDAQ API + Yahoo Finance cross-check</span>
  <span>Auto-refreshes every 6 hours · Generated {ts}</span>
</footer>
<div class="overlay" id="overlay" onclick="closeModal(event)">
  <div class="modal" id="modal">
    <button class="modal-close" onclick="closeModal()">×</button>
    <div class="modal-ticker" id="mTicker"></div>
    <div class="modal-name" id="mName"></div>
    <div class="modal-warn" id="mWarn">⚠ Date conflict — NASDAQ and Yahoo Finance disagree. Verify before acting.</div>
    <div class="modal-row"><span class="modal-key">Sector</span><span class="modal-val" id="mSector"></span></div>
    <div class="modal-row"><span class="modal-key">NASDAQ Date</span><span class="modal-val" id="mDate"></span></div>
    <div class="modal-row" id="mYahooRow" style="display:none">
      <span class="modal-key">Yahoo Date</span>
      <span class="modal-val" id="mYahooDate" style="color:#f7a94f"></span>
    </div>
    <div class="modal-row"><span class="modal-key">Timing</span><span class="modal-val" id="mTiming"></span></div>
    <div class="modal-row"><span class="modal-key">Source</span><span class="modal-val" id="mSource"></span></div>
  </div>
</div>
<script>
const SECTORS       = {sj};
const SECTOR_COLORS = {cj};
const COMPANY_NAMES = {nj};
setTimeout(function() {{ location.reload(); }}, 6 * 60 * 60 * 1000);
function showCard(ticker, name, sector, timing, date, color, source, yahooDate, mismatch) {{
  document.getElementById('mTicker').textContent = ticker;
  document.getElementById('mTicker').style.color = color;
  document.getElementById('mName').textContent   = name;
  document.getElementById('mSector').textContent = sector;
  document.getElementById('mDate').textContent   = date === 'TBD' ? 'Not yet announced' : date;
  document.getElementById('mTiming').textContent =
    timing === 'BMO' ? 'Before Market Open (PRE)' :
    timing === 'AMC' ? 'After Market Close (AFT)' :
    timing === 'TBD' ? 'Not yet confirmed' : 'Unconfirmed';
  document.getElementById('mSource').textContent = source;
  document.getElementById('mWarn').classList.toggle('on', mismatch);
  document.getElementById('mYahooRow').style.display = mismatch ? 'flex' : 'none';
  document.getElementById('mYahooDate').textContent  = yahooDate || '';
}}
function closeModal(e) {{
  if (!e || e.target === document.getElementById('overlay'))
    document.getElementById('overlay').classList.remove('on');
}}
document.addEventListener('keydown', e => {{
  if (e.key === 'Escape') document.getElementById('overlay').classList.remove('on');
}});
</script>
</body>
</html>"""
    return html

# ── RUN ──
df, generated_at = run_fetch()
html = build_html(df, generated_at)
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Done — index.html written")
