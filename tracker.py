import requests
import pandas as pd
import os
from datetime import datetime

# Define these explicitly so the script doesn't hunt for them
LEGIONNAIRES = ["Ejem", "Lanidae", "Alastari", "Ana", "Argixel", "Daktyl", "Titris", "Treskies", "bitHawke", "Alcyonaria", "Axterminator", "Feltos", "LordDrazos", "Maple", "Sakura"]
XP_MULTIPLIER = 1.106 

def generate_html(df):
    # Sort by Carpentry just as a default, or whichever skill you prefer
    df = df.sort_values(by='Carpentry', ascending=False)
    
    html_content = f"""
    <html>
    <head>
        <title>Legion Guild Tracker</title>
        <style>
            body {{ font-family: sans-serif; background: #1a1a1a; color: #eee; padding: 20px; }}
            table {{ border-collapse: collapse; width: 100%; background: #2a2a2a; }}
            th, td {{ border: 1px solid #444; padding: 12px; text-align: left; }}
            th {{ background: #333; color: #00ffcc; cursor: pointer; }}
            tr:nth-child(even) {{ background: #252525; }}
            tr:hover {{ background: #3a3a3a; }}
            .timestamp {{ color: #888; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <h1>Legion Guild Leaderboard</h1>
        <div class="timestamp">Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
        {df.to_html(index=False, classes='guild-table')}
    </body>
    </html>
    """
    with open("index.html", "w") as f:
        f.write(html_content)
    print("HTML Dashboard generated.")
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
    print(f"Starting Data Pull for {len(LEGIONNAIRES)} players...")
    all_stats = []
    
    for name in LEGIONNAIRES:
        try:
            # Use a timeout so the script doesn't hang forever
            search_res = requests.get(f"https://bitjita.com/api/players?q={name}", timeout=15).json()
            
            if search_res.get('players'):
                p_id = search_res['players'][0]['entityId']
                player_res = requests.get(f"https://bitjita.com/api/players/{p_id}", timeout=15).json()
                player = player_res['player']
                
                stats = {"Name": name, "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                for exp in player['experience']:
                    # Accessing the skillMap safely
                    skill_id = str(exp['skill_id'])
                    if skill_id in player['skillMap']:
                        s_name = player['skillMap'][skill_id]['name']
                        stats[s_name] = calculate_level(exp['quantity'])
                all_stats.append(stats)
                print(f"Successfully synced: {name}")
        except Exception as e:
            print(f"Error syncing {name}: {e}")

    if all_stats:
        df = pd.DataFrame(all_stats)
        df.to_csv("legion_live_stats.csv", index=False)
        print("Success: File 'legion_live_stats.csv' created.")
    else:
        print("Error: No data was collected!")
        exit(1) # This tells GitHub the run failed because no data was found

if __name__ == "__main__":
    run_guild_sync()
