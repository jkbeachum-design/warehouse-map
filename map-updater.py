#!/usr/bin/env python3
"""
Homebox Warehouse Map Link Updater

This script automatically adds warehouse location map links to item descriptions
in the Homebox database based on their parent location.

Format: [WAREHOUSE LOCATION MAP](https://map.jkbeachum.com/?target=LOCATION_CODE)
"""

import sqlite3
import shutil
from datetime import datetime
import sys

# Configuration
DB_PATH = "/home/scout/homelab/homebox/data/homebox.db"
MAP_URL_TEMPLATE = "https://map.jkbeachum.com/?target={location}"
WAREHOUSE_PARENT_ID = "e1dbc360-5ed8-4bf5-905f-da8ed0ea35d2"  # Warehouse location ID

def backup_database():
    """Create a timestamped backup of the database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{DB_PATH}.backup_{timestamp}"
    try:
        shutil.copy2(DB_PATH, backup_path)
        print(f"✓ Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"✗ Failed to create backup: {e}")
        sys.exit(1)

def get_warehouse_items(cursor):
    """Get all items in warehouse locations that need updating"""
    query = """
    SELECT 
        i.id,
        i.name,
        i.description,
        l.name as location_name,
        l.id as location_id
    FROM items i
    JOIN locations l ON i.location_items = l.id
    WHERE l.location_children = ?
        AND i.archived = 0
    ORDER BY l.name, i.name;
    """
    
    cursor.execute(query, (WAREHOUSE_PARENT_ID,))
    return cursor.fetchall()

def create_map_link(location_name):
    """Create the warehouse map link markdown"""
    return f"[WAREHOUSE LOCATION MAP]({MAP_URL_TEMPLATE.format(location=location_name)})"

def needs_update(current_description, location_name):
    """Check if item needs the warehouse map link added/updated"""
    map_link = create_map_link(location_name)
    
    # If description is None or empty, needs update
    if not current_description:
        return True, map_link
    
    # If already has the correct link, skip
    if map_link in current_description:
        return False, None
    
    # If has old/different warehouse map link, needs update
    if "[WAREHOUSE LOCATION MAP]" in current_description:
        # Replace the old link
        import re
        pattern = r'\[WAREHOUSE LOCATION MAP\]\(https://map\.jkbeachum\.com/\?target=[^\)]+\)'
        new_description = re.sub(pattern, map_link, current_description)
        return True, new_description
    
    # Add link to existing description
    new_description = f"{current_description.strip()}\n\n{map_link}" if current_description.strip() else map_link
    return True, new_description

def update_items(dry_run=True):
    """Update items with warehouse map links"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all warehouse items
    items = get_warehouse_items(cursor)
    
    if not items:
        print("No warehouse items found!")
        conn.close()
        return
    
    print(f"\nFound {len(items)} warehouse items")
    print("=" * 80)
    
    updates = []
    skipped = []
    
    for item_id, item_name, description, location_name, location_id in items:
        needs_change, new_description = needs_update(description, location_name)
        
        if needs_change:
            updates.append({
                'id': item_id,
                'name': item_name,
                'location': location_name,
                'old_desc': description or "(empty)",
                'new_desc': new_description
            })
        else:
            skipped.append({'name': item_name, 'location': location_name})
    
    # Show what will be changed
    if updates:
        print(f"\n✓ Items to UPDATE ({len(updates)}):")
        print("-" * 80)
        for item in updates:
            print(f"\nItem: {item['name']}")
            print(f"  Location: {item['location']}")
            print(f"  Old description: {item['old_desc'][:60]}...")
            print(f"  New description: {item['new_desc'][:60]}...")
    
    if skipped:
        print(f"\n✓ Items already up-to-date ({len(skipped)}):")
        print("-" * 80)
        for item in skipped:
            print(f"  - {item['name']} ({item['location']})")
    
    # Perform updates if not dry run
    if not dry_run and updates:
        print("\n" + "=" * 80)
        print("APPLYING UPDATES...")
        print("=" * 80)
        
        update_query = """
        UPDATE items 
        SET description = ?,
            updated_at = datetime('now')
        WHERE id = ?;
        """
        
        for item in updates:
            cursor.execute(update_query, (item['new_desc'], item['id']))
            print(f"✓ Updated: {item['name']}")
        
        conn.commit()
        print(f"\n✓ Successfully updated {len(updates)} items!")
    
    elif not dry_run and not updates:
        print("\n✓ All items are already up-to-date!")
    
    conn.close()
    
    return len(updates), len(skipped)

def main():
    """Main execution"""
    print("=" * 80)
    print("HOMEBOX WAREHOUSE MAP LINK UPDATER")
    print("=" * 80)
    
    # Check if running in dry-run mode
    dry_run = "--apply" not in sys.argv
    
    if dry_run:
        print("\n⚠ DRY RUN MODE - No changes will be made")
        print("Run with --apply to actually update the database")
    else:
        print("\n⚠ LIVE MODE - Changes will be applied to database")
        # Create backup before making changes
        backup_database()
    
    # Perform the updates
    update_count, skip_count = update_items(dry_run=dry_run)
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Items to update: {update_count}")
    print(f"Items already correct: {skip_count}")
    
    if dry_run and update_count > 0:
        print("\nTo apply these changes, run:")
        print(f"  python3 {sys.argv[0]} --apply")

if __name__ == "__main__":
    main()