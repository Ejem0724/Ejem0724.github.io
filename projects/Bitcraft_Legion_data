import requests
import pandas as pd
import time
import os
from datetime import datetime

# --- CONFIGURATION ---
LEGIONNAIRES = ["Ejem", "Lanidae", "Alastari", "Ana", "Argixel", "Daktyl", "Titris", "Treskies", "bitHawke", "Alcyonaria", "Axterminator", "Feltos", "LordDrazos", "Maple", "Sakura"]
SKILLS = ['Carpentry', 'Construction', 'Cooking', 'Farming', 'Fishing', 'Foraging', 'Forestry', 'Hunting', 'Leatherworking', 'Masonry', 'Merchanting', 'Mining', 'Sailing', 'Scholar', 'Slayer', 'Smithing', 'Tailoring', 'Taming']
XP_MULTIPLIER = 1.106 # Your engineered math

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
    print(f"\n[{datetime.now()}] Starting Sync...")
    all_stats = []
    
    for name in LEGIONNAIRES:
        try:
            # Step 1: Search for Entity ID
            search_url = f"https://bitjita.com/api/players?q={name}"
            search_res = requests.get(search_url, timeout=10).json()
            
            if search_res['players']:
                p_id = search_res['players'][0]['entityId']
                
                # Step 2: Get Detailed Stats
                player_url = f"https://bitjita.com/api/players/{p_id}"
                player_res = requests.get(player_url, timeout=10).json()
                player = player_res['player']
                
                # Step 3: Parse and Convert
                stats = {"Name": name, "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                for exp in player['experience']:
                    skill_id = str(exp['skill_id'])
                    if skill_id in player['skillMap']:
                        s_name = player['skillMap'][skill_id]['name']
                        stats[s_name] = calculate_level(exp['quantity'])
                
                all_stats.append(stats)
                print(f"  > Synced {name}")
        except Exception as e:
            print(f"  ! Failed {name}: {e}")

    # Step 4: Save Result
    if all_stats:
        df = pd.DataFrame(all_stats)
        # Ensure column order is consistent
        cols = ['Name', 'Timestamp'] + [s for s in SKILLS if s in df.columns]
        df = df[cols]
        
        # Append to a master file or overwrite current
        df.to_csv("legion_live_stats.csv", index=False)
        print(f"[{datetime.now()}] Update Complete. CSV Saved.")

# --- THE LOOP ---
if __name__ == "__main__":
    print("Legion Autonomous Tracker Active.")
    while True:
        run_guild_sync()
        print("Sleeping for 1 hour...")
        time.sleep(3600) # 3600 seconds = 1 hour
