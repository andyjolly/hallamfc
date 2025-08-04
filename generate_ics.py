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
    time_clean = fixture['kick-off'].replace(':', '')
    
    return f"hallam-fc-{season}-{opponent_clean}-{competition_clean}-{home_away}"


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


def generate_ics_content(data, season):
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
    
    # Home ground address
    home_address = "Sandygate, Sandygate Road, Sheffield, S10 5SE"
    
    for fixture in data:
        # Generate UID
        uid = generate_uid(fixture, season)
        
        # Format start and end times
        start_time = format_datetime(fixture['date'], fixture['kick-off'])
        
        # Calculate end time (2 hours after start)
        start_dt = datetime.datetime.strptime(fixture['date'] + " " + fixture['kick-off'], "%Y-%m-%d %H:%M")
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
            location = fixture['away_ground']['name'] + ", " + fixture['away_ground']['address']
        
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


def main():
    parser = argparse.ArgumentParser(description='Generate ICS file from JSON fixture data')
    parser.add_argument('input', help='Input JSON file with fixture data')
    
    args = parser.parse_args()
    
    # Load fixture data
    try:
        data = load_fixtures(args.input)
    except FileNotFoundError:
        print(f"Error: Could not find file '{args.input}'")
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{args.input}': {e}")
        return 1
    
    # Extract season from filename
    try: 
        season = extract_season_from_filename(args.input)
    except ValueError as e:
        print(e)
    
    # Generate ICS content
    ics_content = generate_ics_content(data, season)
    
    # Determine output file
    output_file = f"{season}.ics"
    
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