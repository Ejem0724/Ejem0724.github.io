import requests
import pandas as pd
from datetime import datetime
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

def run_guild_sync():
    print(f"Starting Sync for Claim ID: {CLAIM_ID}")
    
    # 1. Get Claim Members (Pulling both Name AND ID)
    claim_url = f"https://bitjita.com/api/claims/{CLAIM_ID}/members"
    try:
        response = requests.get(claim_url, timeout=15)
        response.raise_for_status()
        member_data = response.json()
    except Exception as e:
        print(f"CRITICAL ERROR: Claim API unreachable. {e}")
        sys.exit(1)

    all_stats = []
    
    # 2. Loop through members using their Entity ID directly
    for member in member_data:
        name = member.get('userName')
        p_id = member.get('playerEntityId') # This is the magic key!
        
        if not p_id:
            print(f"Skipping {name}: No Entity ID found.")
            continue

        try:
            # Direct hit on the player's data
            player_url = f"https://bitjita.com/api/players/{p_id}"
            p_res = requests.get(player_url, timeout=10).json()
            player = p_res['player']
            
            stats = {"Name": name, "Timestamp": datetime.now().strftime("%H:%M")}
            
            # Map skills
            for exp in player['experience']:
                s_id = str(exp['skill_id'])
                if s_id in player['skillMap']:
                    s_name = player['skillMap'][s_id]['name']
                    stats[s_name] = calculate_level(exp['quantity'])
            
            all_stats.append(stats)
            print(f"Successfully synced: {name} ({p_id})")
            
        except Exception as e:
            print(f"Failed to fetch detailed data for {name}: {e}")

    # 3. Save and Generate HTML
    if all_stats:
        df = pd.DataFrame(all_stats)
        df.to_csv("legion_live_stats.csv", index=False)
        generate_html(df) # (Keeping your existing HTML function)
        print("Update Complete.")
    else:
        print("No player data could be retrieved.")
        sys.exit(1)

# (Make sure to keep your generate_html function here as well!)

def generate_html(df):
    now = datetime.now()
    delta = WIPE_DATE - now
    countdown = f"{delta.days}d {delta.seconds//3600}h" if delta.total_seconds() > 0 else "WIPED"

    # Formatting averages
    numeric_cols = df.select_dtypes(include=['number']).columns
    avg_row = {col: round(df[col].mean(), 1) for col in numeric_cols}
    avg_row['Name'] = '<strong>GUILD AVERAGE</strong>'
    avg_row['Timestamp'] = '-'
    
    df_sorted = df.sort_values(by='Carpentry', ascending=False)
    df_final = pd.concat([df_sorted, pd.DataFrame([avg_row])], ignore_index=True)

    # Note the lack of indentation here—this prevents the 'indented' HTML look in the source
    html_content = f"""<html>
<head>
<title>Legion Guild Tracker</title>
<style>
body {{ font-family: sans-serif; background: #121212; color: #e0e0e0; padding: 20px; line-height: 1.5; }}
.header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #00ffcc; padding-bottom: 10px; }}
.countdown {{ background: #b91c1c; color: white; padding: 10px; border-radius: 4px; font-weight: bold; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 20px; background: #1e1e1e; font-size: 0.9em; }}
th, td {{ border: 1px solid #333; padding: 8px; text-align: left; }}
th {{ background: #2d2d2d; color: #00ffcc; }}
tr:nth-child(even) {{ background: #252525; }}
tr:last-child {{ background: #00ffcc11; color: #00ffcc; font-weight: bold; }}
</style>
</head>
<body>
<div class="header">
<h1>Legion Leaderboard</h1>
<div class="countdown">WIPE IN: {countdown}</div>
</div>
<p>Updated: {now.strftime("%Y-%m-%d %H:%M:%S")}</p>
{df_final.to_html(index=False, escape=False)}
</body>
</html>"""
    
    with open("index.html", "w") as f:
        f.write(html_content)

def run_guild_sync():
    members = get_claim_members()
    all_stats = []
    
    for name in members:
        try:
            search = requests.get(f"https://bitjita.com/api/players?q={name}", timeout=10).json()
            if search.get('players'):
                p_id = search['players'][0]['entityId']
                p_res = requests.get(f"https://bitjita.com/api/players/{p_id}", timeout=10).json()
                player = p_res['player']
                
                stats = {"Name": name, "Timestamp": datetime.now().strftime("%H:%M")}
                for exp in player['experience']:
                    s_id = str(exp['skill_id'])
                    if s_id in player['skillMap']:
                        s_name = player['skillMap'][s_id]['name']
                        stats[s_name] = calculate_level(exp['quantity'])
                all_stats.append(stats)
        except:
            continue

    if all_stats:
        df = pd.DataFrame(all_stats)
        generate_html(df)
        df.to_csv("legion_live_stats.csv", index=False)

if __name__ == "__main__":
    run_guild_sync()
