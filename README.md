# Program2Mass v1.0.0
**CSV-Driven Architectural Massing Tool for Rhino**

Transform your room program spreadsheet into intelligent 3D massing geometry in seconds.

![Version](https://img.shields.io/badge/version-1.0-blue)
![Rhino](https://img.shields.io/badge/Rhino-6%2B-green)
![Python](https://img.shields.io/badge/Python-2.7-yellow)

---

This tool saves you hours of mechanical work.

**Use that time to design better buildings.**

**Don't be lazy.**

---

## Quick Start 

1. **Open Rhino** with the "Large Objects - Centimeters" template
2. **Run** `Program2Mass.exe`
3. **Enter** your floor-to-floor height (e.g., 300 cm)
4. **Select** your CSV file when prompted in Rhino
5. **Done!** Your massing is generated automatically

**That's it.** No manual input in Rhino. No calculations. No tedious box-drawing.

---

## What You Need

- **Rhino 7 or 8** (Windows)
- **CSV file** with your room program

---

## CSV Format

Any spreedsheet software works (Google Sheets, Excel, etc...)
Your CSV should have 2 columns: Room Name and Area (in m²)

```csv
Room Name,Area (m2)
Living Room,35.5
Kitchen,18.0
Master Bedroom,22.0
Bathroom 1,8.5
Bedroom 2,16.0
```

**That's the only input you need.**

Save it as a `.csv` file and you're ready to go.

---

## 🎯 What It Does

Program2Mass takes your room program and:

✓ **Detects room types** automatically (living, bedroom, kitchen, bathroom, etc.)  
✓ **Calculates optimal dimensions** using architectural proportions  
✓ **Finds a modular grid** where all walls are multiples of a common module  
✓ **Generates 3D volumes** in Rhino with proper heights  
✓ **Color-codes by function** (Public/Private/Service)  
✓ **Labels everything** with room names and areas  

---

## Detailed Walkthrough

### Step 1: Prepare Your CSV

Create a spreadsheet with your room program:

| Room Name        | Area (m2) |
|------------------|-----------|
| Living Room      | 35.5      |
| Kitchen          | 18.0      |
| Master Bedroom   | 22.0      |
| Bedroom 2        | 16.0      |
| Bathroom 1       | 8.5       |
| Bathroom 2       | 6.0       |
| Storage          | 4.0       |

**Tips:**
- Use descriptive names ("Master Bedroom" not "Room 1")
- Areas in square meters
- No need to include circulation (hallways, corridors)
- The script detects room types from names automatically

**Save as:** `whatever.csv`

---

### Step 2: Open Rhino

**Important:** Use the correct template!

1. Launch Rhino
2. Select: **Large Objects - Centimeters.3dm**
3. Wait for Rhino to fully load

**Why this template?**  
Program2Mass works in centimeters. Using the correct template ensures everything aligns properly.

---

### Step 3: Run Program2Mass

Double-click `Program2Mass.exe`

You'll see:
```
Program2Mass v0.5
CSV to 3D Massing | By gduarte

Main Menu
---------

1. Run Program2Mass
2. Configure Settings
3. Quit

→
```

**Select:** 1

---

### Step 4: Enter Floor Height

The launcher will ask:

```
Step 1/4: Configuration
  → Floor-to-floor height (cm): 300
  ✓ Height: 300 cm
  ✓ Saved
```

**Common heights:**
- Residential: 280-320 cm
- Office: 350-400 cm
- Retail: 400-500 cm

This height is **saved automatically** and applied to all rooms.

---

### Step 5: Script Execution

The launcher will:

```
Step 2/4: Checking Rhino
  ✓ Rhino is running

Step 3/4: Locating script.py
  ✓ Found

Step 4/4: Executing
  ✓ Command sent to Rhino
```

**In Rhino:** A file picker will appear.

---

### Step 6: Select Your CSV

1. Browse to your CSV file
2. Click **Open**
3. **Done!**

The script now runs completely automatically.

---

### Step 7: Watch It Work

In Rhino's command line, you'll see:

```
Program2Mass 0.5
Modular Grid System: All walls as common multiples

Loaded 7 rooms from CSV

Room type detection:
  1. Living Room (35.5m²) -> [living]
  2. Kitchen (18.0m²) -> [kitchen]
  3. Master Bedroom (22.0m²) -> [bedroom]
  ...

FINDING OPTIMAL MODULAR GRID
======================================================================

Selected module: 150cm

APPLYING MODULAR GRID: 150cm
======================================================================
  Living Room: 7.50x4.50m = 33.75m²
  Kitchen: 6.00x3.00m = 18.00m²
  Master Bedroom: 4.50x4.50m = 20.25m²
  ...

[AUTO] Using pre-configured floor height: 300 cm

Generating geometry...
  [OK] Living Room [public]
  [OK] Kitchen [public]
  [OK] Master Bedroom [private]
  ...

[DONE] Massing generated successfully!
```

---

### Step 8: Review Your Massing

In Rhino, you'll see:

**3D Volumes:**
- Color-coded by function
- Labeled with names and areas
- Arranged linearly with spacing
- Grouped for easy manipulation

**Layers created:**
- `Program_Public` (Light Blue) - Living, Kitchen, Dining
- `Program_Private` (Light Red) - Bedrooms, Bathrooms, Offices
- `Program_Service` (Light Yellow) - Storage, Utility
- `ProgramLabels` (Black) - Text labels

---

### Step 9: Arrange Your Layout

**The volumes are placed in a line intentionally.**

Now comes the design part:

1. **Move rooms** to create your floor plan
2. **All walls align** on the modular grid (e.g., 150cm)
3. **Any room can connect** to any other room
4. **Iterate quickly** - all dimensions are coordinated

This is your **design starting point**, not the final layout.

---

## Understanding the Output

### Modular Grid System

**The Key Innovation:** All wall dimensions are multiples of a common module. Possible by the given formula:

<img width="1006" height="227" alt="{282FF493-BA86-4C41-A65C-71DD04C1564E}" src="https://github.com/user-attachments/assets/c49e4133-ede6-4d9f-bf32-58989a3839d4" />

**Example:**
- Module selected: **150 cm**
- Living Room: 7.50m × 4.50m → **(5× module) × (3× module)**
- Kitchen: 6.00m × 3.00m → **(4× module) × (2× module)**
- Bedroom: 4.50m × 4.50m → **(3× module) × (3× module)**

**Why this matters:**
- ✓ Universal connectivity (any room can connect)
- ✓ Modular construction ready
- ✓ No weird dimensions
- ✓ Professional, buildable proportions

---

### Room Type Detection

The script analyzes room names and assigns types:

| Room Type    | Keywords                                      | Color  |
|--------------|-----------------------------------------------|--------|
| **Living**   | living, sala, lounge, family room, dining    | Blue   |
| **Bedroom**  | bedroom, quarto, suite, master               | Red    |
| **Kitchen**  | kitchen, cozinha, cocina                     | Blue   |
| **Bathroom** | bathroom, bath, wc, lavabo, toilet           | Red    |
| **Office**   | office, study, escritório                    | Red    |
| **Utility**  | storage, closet, laundry, despensa           | Yellow |

**Multi-language support:** Works in English, Portuguese, and Spanish.

**Circulation:** Automatically skipped (hallway, corridor, circulation)

---

## ⚙️ Configuration Options

Run `Program2Mass.exe` and select **2. Configure Settings**

### Available Settings:

**1. Minimum Wall Length**
- Range: 100-300 cm
- Default: 120 cm
- Use: Prevents unrealistically small rooms

**2. Auto-close Terminal**
- Options: Yes / No
- Default: Yes
- Use: Terminal closes automatically after execution

**3. Rhino Template**
- Options:
  - Large Objects - Centimeters (recommended)
  - Small Objects - Centimeters
  - Large Objects - Meters
- Default: Large Objects - Centimeters

All settings are saved to `config.json` and persist between sessions.

---

## Troubleshooting

### "Rhino is not running!"

**Solution:**
1. Open Rhino manually
2. Use template: "Large Objects - Centimeters"
3. Restart Program2Mass

---

### "script.py not found!"

**Solution:**
Ensure `script.py` is in the same folder as `Program2Mass.exe`

---

### Script doesn't execute in Rhino

**Solution:**
If automation fails, manually type in Rhino command line:
```
_-RunPythonScript "path\to\script.py"
```

---

## Technical Notes

### Area Accuracy

Typical variance: ±2-5% per room

**Example:**
- Requested: 22.0 m²
- Generated: 20.25 m² (4.5m × 4.5m)
- Variance: -7.95%

The algorithm prioritizes **buildable dimensions** over exact areas.

---

### Performance

**Typical execution:**
- 10 rooms: ~3 seconds
- 20 rooms: ~5 seconds
- 50 rooms: ~10 seconds

---

## Language Support

**Room names can be in:**
- English
- Portuguese
- Spanish

Mix languages freely in the same CSV.

---

## What This Tool Does NOT Do

**Does not:**
- ✗ Create floor plans (generates volumes only)
- ✗ Add circulation automatically
- ✗ Consider site boundaries
- ✗ Place doors/windows
- ✗ Optimize for sun/views
- ✗ Generate multi-story automatically

**This is a conceptual massing tool**, not a complete design solution.

Use it to **accelerate the boring part** so you can focus on design.

 Floor height was entered properly

---

## Credits

**Program2Mass v1.0.0**  
by gduarte
2026

**License:** 
Open-source, feel free to modify, don't forget to share improvements.

---


