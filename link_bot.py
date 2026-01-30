import requests
import json

# --- CONFIGURATION ---
# 1. Your HomeBox URL
# Use "localhost" if running this on the server.
# Use "192.168.X.X" if running this from your Windows PC.
BASE_URL = "http://localhost:3100" 

# 2. PASTE YOUR KEY HERE
API_TOKEN = "TWVUIHHFVBACQQ6OJE33KHEARY"

# 3. The Map URL base
MAP_URL = "https://map.jkbeachum.com/?target="

# 4. SAFETY SWITCH: Set to True to actually save changes.
ENABLE_WRITES = False 
# ---------------------

def main():
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    print(f"Connecting to {BASE_URL}...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/items", headers=headers)
        response.raise_for_status()
        items = response.json()
        if isinstance(items, dict) and 'data' in items:
            items = items['data']
    except Exception as e:
        print(f"Error connecting: {e}")
        return

    print(f"Found {len(items)} items. Scanning...")
    updates_count = 0

    for item in items:
        location = item.get('location')
        loc_name = location.get('name') if isinstance(location, dict) else location
        
        if not loc_name: continue

        full_link = f"[View on Map]({MAP_URL}{loc_name})"
        description = item.get('description') or ""
        
        if full_link in description: continue 

        print(f"[MATCH] '{item.get('name')}' at '{loc_name}' -> Adding link.")
        
        if ENABLE_WRITES:
            # Update description
            item['description'] = description + f"\n\n{full_link}"
            item_id = item.get('id')
            try:
                res = requests.put(f"{BASE_URL}/api/v1/items/{item_id}", headers=headers, json=item)
                if res.status_code != 200: print(f"   -> Failed: {res.status_code}")
            except Exception as e:
                print(f"   -> Error: {e}")
        
        updates_count += 1

    if not ENABLE_WRITES:
        print(f"\n--- DRY RUN COMPLETE: {updates_count} items needs update ---")
        print("Change ENABLE_WRITES = True to save.")
    else:
        print(f"\nDone! Updated {updates_count} items.")

if __name__ == "__main__":
    main()