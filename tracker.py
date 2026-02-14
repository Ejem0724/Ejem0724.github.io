import requests
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURATION ---
CLAIM_ID = "576460752315947982"
WIPE_DATE = datetime(2026, 2, 26, 12, 0, 0) # Feb 26, 2026 at Noon
XP_MULTIPLIER = 1.106 

# --- HELPER FUNCTIONS ---

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

def get_claim_members():
    """Fetches the current list of users from the claim ID."""
    print(f"Fetching members for claim {CLAIM_ID}...")
    try:
        url = f"https://bitjita.com/api/claims/{CLAIM_ID}/members"
        response = requests.get(url, timeout=15).json()
        # Extract usernames from the response
        members = [member['userName'] for member in response]
        print(f"Found {len(members)} members.")
        return members
    except Exception as e:
        print(f"Error fetching claim members: {e}")
        # Fallback to your leadership list if the API fails
        return ["Ejem", "Lanidae", "Alastari", "Ana", "Argixel", "Daktyl", "Titris"]

def generate_html(df):
    """Creates the index.html with countdown and averages."""
    # Calculate Countdown
    now = datetime.now()
    delta = WIPE_DATE - now
    countdown_text = f"{delta.days}d {delta.seconds//3600}h {(delta.seconds//60)%60}m" if delta.total_seconds() > 0 else "WIPED"

    # Calculate Averages
    numeric_df = df.select_dtypes(include=['number'])
    averages = numeric_df.mean().round(1).to_dict()
    averages['Name'] = '<strong>GUILD AVERAGE</strong>'
    averages['Timestamp'] = '-'
    
    # Sort and add average row
    df = df.sort_values(by='Carpentry', ascending=False)
    df_with_avg = pd.concat([df, pd.DataFrame([averages])], ignore_index=True)

    html_content = f"""
    <html>
    <head>
        <title>Legion Guild Tracker</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #121212; color: #e0e0e0; padding: 30px; }}
            .container {{ max-width: 1200px; margin: auto; }}
            .header-flex {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #00ffcc; padding-bottom: 10px; margin-bottom: 20px; }}
            .countdown {{ background: #b91c1c; color: white; padding: 10px 20px; border-radius: 5px; font-weight: bold; font-size: 1.2em; }}
            table {{ border-collapse: collapse; width: 100%; background: #1e1e1e; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
            th, td {{ border: 1px solid #333; padding: 12px; text-align: left; }}
            th {{ background: #2d2d2d; color: #00ffcc; text-transform: uppercase; font-size: 0.8em; }}
            tr:nth-child(even) {{ background: #252525; }}
            tr:last-child {{ background: #00ffcc22; color: #00ffcc; font-weight: bold; }}
            .timestamp {{ color: #666; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header-flex">
                <h1>Legion Guild Leaderboard</h1>
                <div class="countdown">WIPE IN: {countdown_text}</div>
            </div>
            <div class="timestamp">Data Refreshed: {now.strftime("%Y-%m-%d %H:%M:%S")}</div>
            {df_with_avg.to_html(index=False, escape=False)}
        </div>
    </body>
    </html>
    """
    with open("index.html", "w") as f:
        f.write(html_content)

# --- EXECUTION ---

def run_guild_sync():
    members = get_claim_members()
    all_stats = []
    
    for name in members:
        try:
            search_res = requests.get(f"https://bitjita.com/api/players?q={name}", timeout=10).json()
            if search_res.get('players'):
                p_id = search_res['players'][0]['entityId']
                p_data = requests.get(f"https://bitjita.com/api/players/{p_id}", timeout=10).json()['player']
                
                stats = {"Name": name, "Timestamp": datetime.now().strftime("%H:%M")}
                for exp in p_data['experience']:
                    s_id = str(exp['skill_id'])
                    if s_id in p_data['skillMap']:
                        s_name = p_data['skillMap'][s_id]['name']
                        stats[s_name] = calculate_level(exp['quantity'])
                all_stats.append(stats)
        except: continue

    if all_stats:
        df = pd.DataFrame(all_stats)
        generate_html(df)
        df.to_csv("legion_live_stats.csv", index=False)

if __name__ == "__main__":
    run_guild_sync()
