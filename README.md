# Hallam FC Fixtures Calendar

This repository contains tools to generate ICS (iCalendar) files with Hallam FC football fixtures.
The calendar can be imported into most calendar applications and will automatically update when fixtures are modified.

## What is an ICS file?

An ICS (iCalendar) file is a standard format for sharing calendar events. It can be imported into most calendar applications including:

- Google Calendar
- Apple Calendar
- Microsoft Outlook
- Mozilla Thunderbird
- Most mobile calendar apps

## Workflow

This repository uses a JSON-based approach for better maintainability:

1. **Edit JSON files** - Add or modify fixtures in readable JSON format
2. **Run the generator script** - Use `python3 generate_ics.py <season>` to create the ICS file
3. **Import the ICS file** - Add the generated ICS file to your calendar application

## Directory Structure

```
hallamfc/
├── json/           # JSON fixture files
│   └── 2024-2025.json
├── ics/            # Generated ICS files
│   └── 2024-2025.ics
├── generate_ics.py # Script to generate ICS files
└── README.md
```

## JSON File Format

Each season has its own JSON file (e.g., `2024-2025.json`) containing an array of fixtures:

```json
[
  {
    "date": "2025-08-04",
    "kick-off": "14:00",
    "competition": "League",
    "opponent": "Sheffield FC",
    "is_home": true,
    "last_updated": "2025-08-04T21:35:00Z",
    "version": 1
  },
  {
    "date": "2025-08-11",
    "kick-off": "15:00",
    "competition": "League",
    "opponent": "Worksop Town",
    "is_home": false,
    "away_ground": {
      "name": "Windsor Foodservice Stadium",
      "address": "Windsor Foodservice Stadium, Worksop"
    },
    "last_updated": "2025-08-04T21:35:00Z",
    "version": 1
  }
]
```

### Fixture Fields

- **date**: Match date in YYYY-MM-DD format
- **kick-off**: Kick-off time in HH:MM format (24-hour)
- **competition**: Competition type (e.g., "League", "Cup")
- **opponent**: The opposing team name
- **is_home**: Boolean indicating if this is a home fixture for Hallam FC
- **last_updated**: ISO timestamp of when this fixture was last modified
- **version**: Version number for this specific fixture (increments when updated)
- **away_ground**: Object with name and address (only for away fixtures)

## Generating ICS Files

### Prerequisites

- Python 3.6 or higher

### Usage

```bash
# Generate ICS file from JSON data
python3 generate_ics.py 2024-2025

# The script will automatically:
# - Find the JSON file (json/2024-2025.json)
# - Extract season from filename (2024-2025.json → 2024/25)
# - Generate output file in ics/ directory (ics/2024-2025.ics)
# - Create unique UIDs for each fixture
# - Format descriptions with social media links
```

### Example

```bash
# Generate the fixtures calendar
python3 generate_ics.py 2024-2025
# Output: Successfully generated 'ics/2024-2025.ics' with 3 fixtures

# If file not found, shows available options
python3 generate_ics.py 2025-2026
# Output: Available JSON files: ['2024-2025.json']
# Error: Could not find JSON file for season '2025-2026'
```

## Calendar Features

The generated ICS file includes:

### **Event Information**

- **Title**: "👕 Hallam FC v Opponent" (home) or "Opponent v 👕 Hallam FC" (away)
- **Description**: Match details with social media links
- **Location**: Sandygate for home games, away ground for away games
- **Duration**: 2 hours per fixture
- **Status**: Shows as "free" (TRANSPARENT) instead of "busy"
- **Unique UIDs**: Generated from opponent, competition, home/away, and season
- **Individual Updates**: Each fixture tracks its own last_updated and version

### **Social Media Integration**

Each fixture description includes:

- Website: https://hallamfc.co.uk/
- Twitter/X: https://x.com/HallamFC1860/
- YouTube: https://www.youtube.com/@hallamfc1860/
