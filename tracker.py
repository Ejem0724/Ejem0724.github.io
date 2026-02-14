def run_guild_sync():
    print(f"Connecting to Claim: {CLAIM_ID}")
    
    try:
        claim_url = f"https://bitjita.com/api/claims/{CLAIM_ID}/members"
        resp = requests.get(claim_url, timeout=20)
        resp.raise_for_status()
        raw_data = resp.json()
        
        # --- THE FIX IS HERE ---
        # If the API returns a dict with a 'members' key, use that. 
        # Otherwise, assume it's already a list.
        if isinstance(raw_data, dict) and 'members' in raw_data:
            members_data = raw_data['members']
        else:
            members_data = raw_data
        # -----------------------
        
        print(f"Syncing {len(members_data)} members found in claim...")
    except Exception as e:
        print(f"FAILED to fetch claim members: {e}")
        sys.exit(1)

    all_stats = []
    
    for item in members_data:
        # Standardize data extraction
        if isinstance(item, dict):
            name = item.get('userName')
            p_id = item.get('playerEntityId')
        else:
            name = str(item)
            p_id = None
            
        if not name or name.lower() == 'count': continue

        try:
            # If we don't have an ID, search for it
            if not p_id:
                search_res = requests.get(f"https://bitjita.com/api/players?q={name}", timeout=10).json()
                if search_res.get('players'):
                    p_id = search_res['players'][0]['entityId']
                else:
                    continue

            # Get the levels
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
        
        # Calculate Averages
        numeric_cols = df.select_dtypes(include=['number']).columns
        avg_row = {col: round(df[col].mean(), 1) for col in numeric_cols}
        avg_row['Name'] = '<strong>GUILD AVERAGE</strong>'
        avg_row['Timestamp'] = '-'
        
        # Combine and Save
        df = pd.concat([df, pd.DataFrame([avg_row])], ignore_index=True)
        df.to_csv("legion_live_stats.csv", index=False)
        generate_html(df)
    else:
        print("No players found.")
        sys.exit(1)
