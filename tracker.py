import requests
import pandas as pd
from datetime import datetime
import os
import sys

# --- CONFIGURATION ---
CLAIM_ID = "576460752315947982"
WIPE_DATE = datetime(2026, 2, 26, 12, 0, 0) 
XP_MULTIPLIER = 1.106 

def get_xp_table(max_level=120):
    xp_table = [0]
    current_total_xp = 0
    for level in range(1, max_level):
        xp_to_next_level = int(640 * (XP_MULTIPLIER ** (level - 1)))
        current_total_xp += xp_to_next_level
        xp_table.append(current_total_xp)
    return xp_table

BITCRAFT_XP_TABLE = get_xp_table()

def calculate_level(xp):
    if xp <= 0: return 1
    for level, threshold in enumerate(BITCRAFT_XP_TABLE):
        if xp < threshold: return level
    return len(BITCRAFT_XP_TABLE)

def generate_html(df):
    now = datetime.now()
    delta = WIPE_DATE - now
    countdown = f"{delta.days}d {delta.seconds//3600}h" if delta.total_seconds() > 0 else "WIPED"

    numeric_cols = df.select_dtypes(include=['number']).columns
    avg_row = {col: round(df[col].mean(), 1) for col in numeric_cols}
    avg_row['Name'] = '<strong>GUILD AVERAGE</strong>'
    avg_row['Timestamp'] = '-'
    
    if 'Carpentry' in df.columns:
        df_sorted = df.sort_values(by='Carpentry', ascending=False)
    else:
        df_sorted = df

    df_final = pd.concat([df_sorted, pd.DataFrame([avg_row])], ignore_index=True)

    html_content = f"""<html>
<head>
<title>Legion Guild Tracker</title>
<style>
body {{ font-family: sans-serif; background: #121212; color: #e0e0e0; padding: 20px; line-height: 1.5; }}
.header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #00ffcc; padding-bottom: 10px; }}
.countdown {{ background: #b91c1c; color: white; padding: 10px 15px; border-radius: 4px; font-weight: bold; }}
.table-container {{ overflow-x: auto; margin-top: 20px; }}
table {{ border-collapse: collapse; width: 100%; background: #1e1e1e; font-size: 0.85em; }}
th, td {{ border: 1px solid #333; padding: 10px; text-align: left; }}
th {{ background: #2d2d2d; color: #00ffcc; text-transform: uppercase; }}
tr:nth-child(even) {{ background: #252525; }}
tr:last-child {{ background: #00ffcc11; color: #00ffcc; font-weight: bold; }}
h1 {{ margin: 0; color: #00ffcc; }}
</style>
</head>
<body>
<div class="header">
<h1>Legion Leaderboard</h1>
<div class="countdown">WIPE IN: {countdown}</div>
</div>
<p>Refreshed: {now.strftime("%Y-%m-%d %H:%M:%S")}</p>
<div class="table-container">
{df_final.to_html(index=False, escape=False)}
</div>
</body>
</html>"""
    
    with open("index.html", "w") as f:
        f.write(html_content)

def run_guild_sync():
    print(f"Connecting to Claim: {CLAIM_ID}")
    
    try:
        claim_url = f"https://bitjita.com/api/claims/{CLAIM_ID}/members"
        resp = requests.get(claim_url, timeout=20)
        resp.raise_for_status()
        members_data = resp.json()
    except Exception as e:
        print(f"FAILED to fetch claim members: {e}")
        sys.exit(1)

    all_stats = []
    
    for item in members_data:
        # DATA SHAPE PROTECTION: Check if item is a dict or just a string
        if isinstance(item, dict):
            name = item.get('userName')
            p_id = item.get('playerEntityId')
        else:
            name = str(item)
            p_id = None
            
        print(f"Processing: {name}...")

        try:
            # If we don't have an ID, we MUST search by name first
            if not p_id:
                search_url = f"https://bitjita.com/api/players?q={name}"
                search_res = requests.get(search_url, timeout=10).json()
                if search_res.get('players'):
                    p_id = search_res['players'][0]['entityId']
                else:
                    print(f"Could not find ID for name: {name}")
                    continue

            # Fetch detailed stats
            p_resp = requests.get(f"https://bitjita.com/api/players/{p_id}", timeout=10)
            p_data = p_resp.json().get('player')
            
            stats = {"Name": name, "Timestamp": datetime.now().strftime("%H:%M")}
            
            for exp in p_data.get('experience', []):
                s_id = str(exp.get('skill_id'))
                if s_id in p_data.get('skillMap', {}):
                    s_name = p_data['skillMap'][s_id]['name']
                    stats[s_name] = calculate_level(exp.get('quantity', 0))
            
            all_stats.append(stats)
            print(f"  > Synced {name}")
            
        except Exception as e:
            print(f"  ! Error with {name}: {e}")

    if all_stats:
        df = pd.DataFrame(all_stats).fillna(1)
        df.to_csv("legion_live_stats.csv", index=False)
        generate_html(df)
        print(f"Sync complete. Total: {len(all_stats)}")
    else:
        print("Error: No data retrieved.")
        sys.exit(1)

if __name__ == "__main__":
    run_guild_sync()
