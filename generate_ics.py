#!/usr/bin/env python3
"""
Smart script to generate ICS calendar files from JSON fixture data.
"""

import json
import datetime
import argparse
import re
from pathlib import Path


def load_fixtures(json_file):
    """Load fixture data from JSON file."""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_grounds():
    """Load grounds data from JSON file."""
    grounds_file = "json/grounds.json"
    try:
        with open(grounds_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Grounds file '{grounds_file}' not found. Using fallback data.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Warning: Invalid JSON in '{grounds_file}': {e}. Using fallback data.")
        return {}


def extract_season_from_filename(filename):
    """Extract season from filename like '2024-2025.json'."""
    match = re.search(r'(\d{4})-(\d{4})', filename)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    
    raise ValueError("Expected file format yyyy-yyyy.json");


def generate_uid(fixture, season):
    """Generate unique ID based on opponent, competition, and home/away."""
    opponent_clean = re.sub(r'[^a-zA-Z0-9]', '', fixture['opponent'].lower())
    competition_clean = re.sub(r'[^a-zA-Z0-9]', '', fixture['competition'].lower())
    home_away = "home" if fixture['is_home'] else "away"
    date_clean = fixture['date'].replace('-', '')
    
    # Get kick-off time for UID generation
    kick_off_time = get_kick_off_time(fixture)
    time_clean = kick_off_time.replace(':', '')
    
    return f"hallam-fc-{season}-{opponent_clean}-{competition_clean}-{home_away}"


def get_default_kick_off(date_str):
    """Get default kick-off time based on day of week."""
    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    weekday = date_obj.weekday()  # Monday=0, Sunday=6

    # Weekend games (Saturday=5, Sunday=6): 3:00 PM
    if weekday >= 5:  # Saturday or Sunday
        return "15:00"
    # Midweek games (Monday-Friday): 7:45 PM
    else:
        return "19:45"


def get_kick_off_time(fixture):
    """Get kick-off time from fixture, using default if not specified."""
    if 'kick_off' in fixture and fixture['kick_off']:
        return fixture['kick_off']
    else:
        return get_default_kick_off(fixture['date'])


def format_datetime(date_str, time_str):
    """Convert date and time strings to ICS datetime format."""
    # Parse date and time
    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    time_obj = datetime.datetime.strptime(time_str, "%H:%M")
    
    # Combine date and time
    combined = date_obj.replace(
        hour=time_obj.hour,
        minute=time_obj.minute,
        second=0,
        microsecond=0
    )
    
    # Format for ICS (UTC time)
    return combined.strftime("%Y%m%dT%H%M%SZ")


def escape_ics_text(text):
    """Escape text for ICS format according to RFC 5545."""
    # Replace backslashes with double backslashes
    text = text.replace('\\', '\\\\')
    # Replace semicolons with escaped semicolons
    text = text.replace(';', '\\;')
    # Replace commas with escaped commas
    text = text.replace(',', '\\,')
    # Replace newlines with \n
    text = text.replace('\n', '\\n')
    return text


def generate_ics_content(data, season, grounds_data):
    """Generate ICS content from fixture data."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:-//Hallam FC//Fixtures Calendar//{season}//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:Hallam FC Fixtures {season}",
        f"X-WR-CALDESC:All Hallam FC football fixtures for the {season} season",
        "X-WR-TIMEZONE:Europe/London",
        ""
    ]
    
    # Get Hallam's home ground data
    hallam_ground = grounds_data.get("Hallam")
    if not hallam_ground:
        raise ValueError("Hallam not found in grounds.json. Please add Hallam to the grounds data.")
    home_address = f"{hallam_ground['name']}, {hallam_ground['address']}"
    
    for fixture in data:
        # Generate UID
        uid = generate_uid(fixture, season)
        
        # Get kick-off time (use default if not specified)
        kick_off_time = get_kick_off_time(fixture)

        # Format start and end times
        start_time = format_datetime(fixture['date'], kick_off_time)
        
        # Calculate end time (2 hours after start)
        start_dt = datetime.datetime.strptime(fixture['date'] + " " + kick_off_time, "%Y-%m-%d %H:%M")
        end_dt = start_dt + datetime.timedelta(hours=2)
        end_time = end_dt.strftime("%Y%m%dT%H%M%SZ")
        
        # Create match summary based on home/away
        if fixture['is_home']:
            summary = f"👕 Hallam FC v {fixture['opponent']}"
        else:
            summary = f"{fixture['opponent']} v 👕 Hallam FC"
        
        # Create description with competition and social media links
        description_text = f"⚽ Watch Hallam FC take on {fixture['opponent']} in the {fixture['competition']}.\n\nCheck the website for tickets, news and updates:\nhttps://hallamfc.co.uk\n\nJoin the discussion on X:\nhttps://x.com/HallamFC1860\n\nCheck for highlights on YouTube:\nhttps://www.youtube.com/@hallamfc1860"
        description = escape_ics_text(description_text)
        
        # Set location based on home/away
        if fixture['is_home']:
            location = home_address
        else:
            # Get opponent's ground data from grounds.json
            opponent_ground = grounds_data.get(fixture['opponent'])
            if opponent_ground:
                location = f"{opponent_ground['name']}, {opponent_ground['address']}"
            else:
                raise ValueError(f"Opponent '{fixture['opponent']}' not found in grounds.json. Please add this club to the grounds data.")
        
        # Use individual fixture metadata
        last_updated = fixture.get('last_updated', datetime.datetime.utcnow().isoformat() + 'Z')
        version = fixture.get('version', 0)
        
        # Generate event
        event_lines = [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{last_updated}",
            f"DTSTART:{start_time}",
            f"DTEND:{end_time}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{description}",
            f"LOCATION:{location}",
            "STATUS:CONFIRMED",
            f"SEQUENCE:{version}",
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
            ""
        ]
        
        lines.extend(event_lines)
    
    lines.append("END:VCALENDAR")
    return "\n".join(lines)


def find_json_file(season_input):
    """Find JSON file based on season input."""
    # Try different possible locations and formats
    possible_paths = [
        f"json/fixtures/{season_input}.json",
        f"json/{season_input}.json",
        f"{season_input}.json",
        f"json/fixtures/{season_input.replace('-', '_')}.json",
        f"json/{season_input.replace('-', '_')}.json",
        f"{season_input.replace('-', '_')}.json"
    ]
    
    for path in possible_paths:
        if Path(path).exists():
            return path
    
    # If not found, list available files
    json_files = list(Path("json").glob("*.json")) if Path("json").exists() else []
    fixtures_files = list(Path("json/fixtures").glob("*.json")) if Path("json/fixtures").exists() else []
    all_files = json_files + fixtures_files
    if all_files:
        print(f"Available JSON files: {[f.name for f in all_files]}")
    else:
        print("No JSON files found in json/ or json/fixtures/ directories")
    
    raise FileNotFoundError(f"Could not find JSON file for season '{season_input}'")


def main():
    parser = argparse.ArgumentParser(description='Generate ICS file from JSON fixture data')
    parser.add_argument('season', help='Season name (e.g., 2024-2025)')
    
    args = parser.parse_args()
    
    # Find the JSON file
    try:
        json_file = find_json_file(args.season)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    
    # Load fixture data
    try:
        data = load_fixtures(json_file)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{json_file}': {e}")
        return 1
    
    # Extract season from filename
    season = extract_season_from_filename(json_file)
    
    # Load grounds data
    grounds_data = load_grounds()
    
    # Generate ICS content
    ics_content = generate_ics_content(data, season, grounds_data)
    
    # Determine output file in ics/ directory
    input_filename = Path(json_file).stem  # Get filename without extension
    output_file = f"ics/{input_filename}.ics"
    
    # Create ics directory if it doesn't exist
    Path("ics").mkdir(exist_ok=True)
    
    # Write ICS file
    try:
        with open(output_file, 'w', encoding='utf-8', newline='\r\n') as f:
            f.write(ics_content)
        print(f"Successfully generated '{output_file}' with {len(data)} fixtures")
    except Exception as e:
        print(f"Error writing to '{output_file}': {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 