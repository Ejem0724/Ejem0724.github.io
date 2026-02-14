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

    # Separate actual players from the average for sorting
    player_df = df[df['Name'] != '<strong>GUILD AVERAGE</strong>'].copy()
    avg_df = df[df['Name'] == '<strong>GUILD AVERAGE</strong>'].copy()

    # Sort players by Carpentry
    if 'Carpentry' in player_df.columns:
        player_df = player_df.sort_values(by='Carpentry', ascending=False)

    # Re-combine
    df_final = pd.concat([player_df, avg_df], ignore_index=True)

    html_content = f"""<html>
<head>
<title>Legion Guild Tracker</title>
<style>
body {{ font-family: sans-serif; background: #121212; color: #e0e0e0; padding: 20px; }}
.header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #00ffcc; padding-bottom: 10px; }}
.countdown {{ background: #b91c1c; color: white; padding: 10px 15px; border-radius: 4px; font-weight: bold; }}
.table-container {{ overflow-x: auto; margin-top: 20px; }}
table {{ border-collapse: collapse; width: 100%; background: #1e1e1e; font-size: 0.85em; }}
th, td {{ border: 1px solid #333; padding: 10px; text-align: left; white-space: nowrap; }}
th {{ background: #2d2d2d; color: #00ffcc; text-transform: uppercase; }}
tr:nth-child(even) {{ background: #252525; }}
tr:hover {{ background: #333; }}
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
        print(f"DEBUG: Raw API Data sample: {str(members_data)[:200]}") # Help us see the 'count' issue
    except Exception as e:
        print(f"FAILED to fetch claim members: {e}")
        sys.exit(1)

    all_stats = []
    
    for item in members_data:
        # DATA SHAPE PROTECTION
        if isinstance(item, dict):
            name = item.get('userName')
            p_id = item.get('playerEntityId')
        else:
            name = str(item)
            p_id = None
            
        if name.lower() == 'count': continue # Filter out the weird 'count' entry if it exists

        try:
            if not p_id:
                search_url = f"https://bitjita.com/api/players?q={name}"
                search_res = requests.get(search_url, timeout=10).json()
                if search_res.get('players'):
                    p_id = search_res['players'][0]['entityId']
                else:
                    continue

            p_resp = requests.get(f"https://bitjita.com/api/players/{p_id}", timeout=10)
            p_data = p_resp.json().get('player')
            
            stats = {"Name": name, "Timestamp": datetime.now().strftime("%H:%M")}
            
            for exp in p_data.get('experience', []):
                s_id = str(exp.get('skill_id'))
                if s_id in p_data.get('skillMap', {}):
                    s_name = p_data['skillMap'][s_id]['name']
                    stats[s_name] = calculate_level(exp.get('quantity', 0))
            
            all_stats.append(stats)
            print(f"Synced: {name}")
            
        except Exception as e:
            print(f"Error with {name}: {e}")

    if all_stats:
        df = pd.DataFrame(all_stats).fillna(1)
        
        # Calculate Averages BEFORE adding the average row to the list
        numeric_cols = df.select_dtypes(include=['number']).columns
        avg_row = {col: round(df[col].mean(), 1) for col in numeric_cols}
        avg_row['Name'] = '<strong>GUILD AVERAGE</strong>'
        avg_row['Timestamp'] = '-'
        
        # Add the average row to the dataframe
        df = pd.concat([df, pd.DataFrame([avg_row])], ignore_index=True)
        
        df.to_csv("legion_live_stats.csv", index=False)
        generate_html(df)
        print(f"Sync complete. Total Players: {len(all_stats)}")
    else:
        print("No players found in claim data.")
        sys.exit(1)

if __name__ == "__main__":
    run_guild_sync()
