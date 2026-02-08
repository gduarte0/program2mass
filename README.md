# Program2Mass

> **Intelligent CSV-driven architectural program massing tool for Rhino**

Transform your architectural program spreadsheets into 3D massing models with smart, architecture-appropriate proportions.

![Version](https://img.shields.io/badge/version-0.3-blue)
![Rhino](https://img.shields.io/badge/Rhino-6%2B-green)
![Python](https://img.shields.io/badge/Python-2.7-yellow)



## Overview

**Program2Mass** is a Python script for Rhinoceros 3D that automatically generates architectural massing studies from CSV-based room programs. Instead of manually creating boxes for each space, simply list your rooms and their areas in a spreadsheet—the script handles the rest.



## Features

### Core Functionality

- **CSV-Driven Workflow** - Edit your program in Excel/Sheets, generate massing in Rhino
- **Smart Proportions** - Living rooms get 4:3 ratios, kitchens get galley proportions, hallways get corridor shapes
- **Automatic Optimization** - Algorithm maximizes shared wall dimensions across rooms
- **Modular Grid** - All dimensions snap to 50cm increments for construction logic
- **Minimum Dimensions** - Enforces 170cm minimum wall length (configurable)

### Room Type Intelligence

Automatically detects and applies appropriate proportions for:

| Room Type | Preferred Ratios | Aspect Range | Example Rooms |
|-----------|-----------------|--------------|---------------|
| Living | 4:3, 5:4, 3:2 | 0.6 - 1.5 | Living Room, Family Room, Sala |
| Bedroom | 3:2, 4:3, 5:4 | 0.5 - 1.5 | Master Bedroom, Bedroom 2, Quarto |
| Kitchen | 5:3, 3:2, 4:3 | 0.5 - 2.0 | Kitchen, Kitchenette, Cozinha |
| Bathroom | 3:2, 2:1, 5:4 | 0.4 - 2.0 | Bathroom, Powder Room, Lavabo |
| Office | 3:2, 4:3, 5:4 | 0.6 - 1.5 | Home Office, Study, Escritorio |
| Circulation | 2:1, 3:1, 5:2 | 0.3 - 3.0 | Hallway, Corridor, Entry |
| Utility | 2:1, 3:2, 1:1 | 0.4 - 2.5 | Storage, Closet, Laundry |

### Output

- **3D Box Geometry** - Extruded to specified floor-to-floor height
- **Text Labels** - Room name and area at the top of each box
- **Organized Layers** - `ProgramMassing` (gray boxes) and `ProgramLabels` (text)
- **Grouped Objects** - Each room's geometry and label grouped for easy manipulation



## Installation

### Prerequisites

- **Rhinoceros 6 or later** (Windows or Mac)
- **Python 2.7+** (included with Rhino)
- No additional libraries required



## How to use?

### 1. Prepare Your CSV

Create a simple 2-column spreadsheet:

```csv
Room Name,Area (m2)
Living Room,35.5
Kitchen,18.0
Master Bedroom,22.0
Bedroom 2,16.5
Bathroom,8.5
Hallway,12.0
```

Save as `.csv` format.

### 2. Run the Script

In Rhino:
```
1. Type: RunPythonScript
2. Select: program2mass_x.x.py
3. Run 
```

### 3. Select Your CSV

- File dialog opens automatically
- Navigate to your CSV file
- Click Open

### 4. Review Detection

Script shows detected room types:
```
Detected room types:
  1. Living Room -> [living]
  2. Kitchen -> [kitchen]
  3. Master Bedroom -> [bedroom]
  4. Bedroom 2 -> [bedroom]
  5. Bathroom -> [bathroom]
  6. Hallway -> [circulation]
```

### 5. Enter Floor Height

```
Enter floor-to-floor height in cm (e.g., 300): 300
```

Common heights:
- Residential: 280-320 cm
- Commercial Office: 350-400 cm
- Retail: 400-500 cm

### 6. Get Your Massing!

The script generates:
- 3D boxes with smart proportions
- Text labels showing name + area
- Everything organized and grouped



## How It Works

### Algorithm Overview

```
1. Read CSV File
   └─> Parse room names and areas

2. Detect Room Types
   └─> Match keywords in names (living, bedroom, kitchen, etc.)

3. Calculate Initial Dimensions
   └─> For each room:
       - Select appropriate proportions based on type
       - Calculate dimensions from area
       - Snap to 50cm grid
       - Enforce minimum 170cm wall length

4. Optimize Connections
   └─> Analyze all rooms:
       - Find most common wall dimensions
       - Adjust rooms to share wall lengths (±5% area tolerance)
       - Maintain room type constraints

5. Generate Geometry
   └─> Create in Rhino:
       - 3D box for each room
       - Text label at top center
       - Group box + label
       - Organize in layers
```

### Dimension Calculation Example

**Room:** Kitchen, 18 m²  
**Type Detected:** `kitchen` (5:3 preferred ratio)

```
1. Try 5:3 ratio:
   - length = √(18 × 10000 × 5/3) = 547cm
   - width = 180000 / 547 = 329cm

2. Snap to 50cm grid:
   - length = 550cm (round 547)
   - width = 350cm (round 329)

3. Check constraints:
   - Both > 170cm minimum ✓
   - Aspect ratio 550/350 = 1.57 (within 0.5-2.0) ✓

4. Calculate actual area:
   - 550 × 350 = 192,500 cm² = 19.25 m²
   - Error: 1.25 m² (6.9% - acceptable)

5. Final dimensions: 5.50m × 3.50m
```

### Optimization Example

**Before Optimization:**
```
Living Room: 7.00 × 5.50m (unique walls)
Kitchen:     5.00 × 3.50m (unique walls)
Bedroom:     4.50 × 4.00m (unique walls)
```

**After Optimization:**
```
Living Room: 7.00 × 5.00m (shares 5.00m with Kitchen)
Kitchen:     5.00 × 3.50m (shares 5.00m with Living, 3.50m with Bathroom)
Bedroom:     4.50 × 5.00m (shares 5.00m with Living & Kitchen)
```

Result: **5.00m wall appears 5 times** → Easy to connect rooms!



## CSV Format

### Required Format

```csv
Room Name,Area (m2)
Living Room,35.5
Kitchen,18.0
```

**Rules:**
- First row is header (required)
- Column 1: Room Name (text)
- Column 2: Area in square meters (number)
- Areas must be positive numbers
- Empty rows are automatically skipped

### Supported Variations

**Different Headers:**
```csv
Room Name,Area (m2)
Space Name,Area (sqm)
Room,Area
```
Works as long as there are 2 columns with row 1 as headers.

**Different Delimiters:**
- Comma (`,`) - recommended
- Semicolon (`;`) - common in European Excel
- Tab-delimited - works

**Encoding:**
- UTF-8 (recommended)
- ASCII
- UTF-8 with BOM



## Room Type Detection

### How Detection Works

The script scans room names for **keywords** to determine the room type:

```python
Room Name: "Master Bedroom"
           ↓
Keywords found: ["bedroom", "master"]
           ↓
Type assigned: bedroom
           ↓
Proportions used: 3:2, 4:3, 5:4
           ↓
Constraints: aspect ratio 0.5-1.5
```

### Keyword Reference

| Room Type | Keywords (case-insensitive) |
|-----------|---------------------------|
| **Living** | living, sala, family room, lounge, sitting |
| **Bedroom** | bedroom, quarto, suite, dormitorio, bed, master |
| **Kitchen** | kitchen, cozinha, cocina, kitchenette |
| **Bathroom** | bathroom, bath, wc, toilet, lavabo, powder, restroom |
| **Office** | office, study, escritorio, home office |
| **Circulation** | hallway, hall, corridor, corredor, circulation, entry, foyer |
| **Utility** | storage, closet, laundry, utility, pantry, despensa, lavanderia |



## Examples

### Example 1: Small Apartment (60 m²)

**Input CSV:**
```csv
Room Name,Area (m2)
Living/Dining,24
Kitchen,8
Bedroom,18
Bathroom,5
Storage,3
Hallway,2
```

**Detection:**
```
Living/Dining -> [living]
Kitchen -> [kitchen]
Bedroom -> [bedroom]
Bathroom -> [bathroom]
Storage -> [utility]
Hallway -> [circulation]
```

**Generated Dimensions:**
```
Living/Dining:  6.00 × 4.00m (4:3 ratio)
Kitchen:        4.00 × 2.00m (galley)
Bedroom:        4.50 × 4.00m (3:2)
Bathroom:       2.50 × 2.00m (narrow)
Storage:        2.00 × 1.70m (min size)
Hallway:        3.00 × 1.00m (corridor)
```

**Wall Sharing:**
- Living & Kitchen share 4.00m wall
- Bedroom & Kitchen share 4.00m wall
- Easy to connect!

### Example 2: Office Suite (200 m²)

**Input CSV:**
```csv
Room Name,Area (m2)
Open Office,100
Conference Room,30
Manager Office,20
Break Room,15
Copy Room,8
Main Corridor,15
Restroom M,6
Restroom F,6
```

**Generated Layout:**
- All offices use consistent 3:2 proportions
- Conference room gets balanced 5:4 ratio
- Restrooms are efficiently narrow (2:1)
- Corridor is properly long and narrow

**Detection:**

All detected correctly regardless of language!



## Changelog

### v0.3 (Current)
- Automatic room type detection from names
- Multi-language support (English, Portuguese, Spanish)
- Simplified labels (name + area only)
- Back to 2-column CSV format
- Improved optimization algorithm

### v0.2
- Intelligent room proportions by type
- Wall alignment optimization
- 50cm grid snapping
- Configurable constraints per room type
- Room type-specific aspect ratios

### v0.1
- Initial release
- Basic CSV import
- 3D box generation
- Text labels
- Layer organization
- Automatic grouping



## License

This script is open-source, feel free to modify.
Don't forget to share improvements.

**Happy Massing!**

---

<p align="center">
  by gduarte
</p>
