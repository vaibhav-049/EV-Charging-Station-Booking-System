"""Add latitude and longitude coordinates to existing stations based on city"""
import sqlite3
from pathlib import Path

DB_PATH = Path("database/ev_stations.db")

# Major Indian cities with coordinates (latitude, longitude)
CITY_COORDINATES = {
    # Major metros
    "Mumbai": (19.0760, 72.8777),
    "Delhi": (28.6139, 77.2090),
    "Bangalore": (12.9716, 77.5946),
    "Bengaluru": (12.9716, 77.5946),
    "Hyderabad": (17.3850, 78.4867),
    "Ahmedabad": (23.0225, 72.5714),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
    "Pune": (18.5204, 73.8567),
    "Surat": (21.1702, 72.8311),
    
    # Other major cities
    "Jaipur": (26.9124, 75.7873),
    "Lucknow": (26.8467, 80.9462),
    "Kanpur": (26.4499, 80.3319),
    "Nagpur": (21.1458, 79.0882),
    "Indore": (22.7196, 75.8577),
    "Thane": (19.2183, 72.9781),
    "Bhopal": (23.2599, 77.4126),
    "Visakhapatnam": (17.6868, 83.2185),
    "Pimpri-Chinchwad": (18.6298, 73.7997),
    "Patna": (25.5941, 85.1376),
    
    # Tier 2 cities
    "Vadodara": (22.3072, 73.1812),
    "Ghaziabad": (28.6692, 77.4538),
    "Ludhiana": (30.9010, 75.8573),
    "Agra": (27.1767, 78.0081),
    "Nashik": (19.9975, 73.7898),
    "Faridabad": (28.4089, 77.3178),
    "Meerut": (28.9845, 77.7064),
    "Rajkot": (22.3039, 70.8022),
    "Kalyan-Dombivali": (19.2403, 73.1305),
    "Vasai-Virar": (19.4612, 72.7988),
    
    # State capitals
    "Thiruvananthapuram": (8.5241, 76.9366),
    "Chandigarh": (30.7333, 76.7794),
    "Bhubaneswar": (20.2961, 85.8245),
    "Ranchi": (23.3441, 85.3096),
    "Dehradun": (30.3165, 78.0322),
    "Gandhinagar": (23.2156, 72.6369),
    "Shimla": (31.1048, 77.1734),
    "Raipur": (21.2514, 81.6296),
    "Dispur": (26.1433, 91.7898),
    "Imphal": (24.8170, 93.9368),
    
    # Tech hubs
    "Gurgaon": (28.4595, 77.0266),
    "Gurugram": (28.4595, 77.0266),
    "Noida": (28.5355, 77.3910),
    "Coimbatore": (11.0168, 76.9558),
    "Kochi": (9.9312, 76.2673),
    "Mysore": (12.2958, 76.6394),
    "Mysuru": (12.2958, 76.6394),
    
    # Gujarat cities
    "Bhavnagar": (21.7645, 72.1519),
    "Jamnagar": (22.4707, 70.0577),
    "Junagadh": (21.5222, 70.4579),
    "Anand": (22.5645, 72.9289),
    "Mehsana": (23.5880, 72.3693),
    
    # Maharashtra cities
    "Aurangabad": (19.8762, 75.3433),
    "Kolhapur": (16.7050, 74.2433),
    "Solapur": (17.6599, 75.9064),
    "Amravati": (20.9374, 77.7796),
    "Navi Mumbai": (19.0330, 73.0297),
    
    # South India
    "Madurai": (9.9252, 78.1198),
    "Tiruchirappalli": (10.7905, 78.7047),
    "Salem": (11.6643, 78.1460),
    "Tiruppur": (11.1085, 77.3411),
    "Vijayawada": (16.5062, 80.6480),
    "Guntur": (16.3067, 80.4365),
    "Warangal": (17.9689, 79.5941),
    "Mangalore": (12.9141, 74.8560),
    
    # North India
    "Varanasi": (25.3176, 82.9739),
    "Srinagar": (34.0837, 74.7973),
    "Amritsar": (31.6340, 74.8723),
    "Jalandhar": (31.3260, 75.5762),
    "Allahabad": (25.4358, 81.8463),
    "Prayagraj": (25.4358, 81.8463),
    "Jodhpur": (26.2389, 73.0243),
    "Udaipur": (24.5854, 73.7125),
    "Kota": (25.2138, 75.8648),
}

def add_coordinate_columns():
    """Add latitude and longitude columns if they don't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(ev_charging_stations_reduced)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'latitude' not in columns:
            cursor.execute("ALTER TABLE ev_charging_stations_reduced ADD COLUMN latitude REAL")
            print("✅ Added latitude column")
        
        if 'longitude' not in columns:
            cursor.execute("ALTER TABLE ev_charging_stations_reduced ADD COLUMN longitude REAL")
            print("✅ Added longitude column")
        
        conn.commit()
    except Exception as e:
        print(f"Error adding columns: {e}")
    finally:
        conn.close()

def update_coordinates():
    """Update coordinates for all stations based on their city"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    updated_count = 0
    not_found_cities = set()
    
    try:
        # Get all stations
        cursor.execute("SELECT station_id, city FROM ev_charging_stations_reduced")
        stations = cursor.fetchall()
        
        for station_id, city in stations:
            if not city:
                continue
            
            # Clean city name
            city_clean = city.strip()
            
            # Find coordinates
            coords = None
            for city_key, city_coords in CITY_COORDINATES.items():
                if city_key.lower() in city_clean.lower() or city_clean.lower() in city_key.lower():
                    coords = city_coords
                    break
            
            if coords:
                lat, lng = coords
                # Add small random offset for variety (0-0.05 degrees ~= 0-5km)
                import random
                lat_offset = random.uniform(-0.05, 0.05)
                lng_offset = random.uniform(-0.05, 0.05)
                
                cursor.execute(
                    "UPDATE ev_charging_stations_reduced SET latitude = ?, longitude = ? WHERE station_id = ?",
                    (lat + lat_offset, lng + lng_offset, station_id)
                )
                updated_count += 1
            else:
                not_found_cities.add(city_clean)
        
        conn.commit()
        
        print(f"\n✅ Updated coordinates for {updated_count} stations")
        
        if not_found_cities:
            print(f"\n⚠️ Could not find coordinates for {len(not_found_cities)} cities:")
            for city in sorted(not_found_cities)[:10]:  # Show first 10
                print(f"   - {city}")
            if len(not_found_cities) > 10:
                print(f"   ... and {len(not_found_cities) - 10} more")
    
    except Exception as e:
        print(f"Error updating coordinates: {e}")
        conn.rollback()
    finally:
        conn.close()

def verify_coordinates():
    """Verify how many stations have coordinates"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM ev_charging_stations_reduced")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ev_charging_stations_reduced WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
        with_coords = cursor.fetchone()[0]
        
        print(f"\n📊 Statistics:")
        print(f"   Total stations: {total}")
        print(f"   With coordinates: {with_coords}")
        print(f"   Without coordinates: {total - with_coords}")
        print(f"   Coverage: {(with_coords/total*100):.1f}%")
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("🗺️  Adding coordinates to EV charging stations...\n")
    
    # Step 1: Add columns
    add_coordinate_columns()
    
    # Step 2: Update coordinates
    update_coordinates()
    
    # Step 3: Verify
    verify_coordinates()
    
    print("\n✅ Done! Coordinates have been added to the database.")
    print("   Restart Flask to see the map working!")
