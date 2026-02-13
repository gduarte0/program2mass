# -*- coding: utf-8 -*-
"""
Program2Mass v0.5 - Modular Grid System
All walls snap to common multiples for universal connectivity
By gduarte
"""

import os
import sys
import csv
import math
import json
import rhinoscriptsyntax as rs

ver = "0.5"

# ============================================================================
# RUNTIME CONFIGURATION
# ============================================================================

def load_runtime_config():
    """Load runtime configuration from launcher"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'runtime.json')
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

# Load config early
RUNTIME_CONFIG = load_runtime_config()
AUTO_MODE = RUNTIME_CONFIG.get('auto_mode', False) if RUNTIME_CONFIG else False

# ============================================================================
# ROOM TYPE DETECTION
# ============================================================================

ROOM_TYPE_KEYWORDS = {
    'living': ['living', 'sala', 'family room', 'lounge', 'sitting', 'dining'],
    'bedroom': ['bedroom', 'quarto', 'suite', 'dormitorio', 'bed', 'master'],
    'kitchen': ['kitchen', 'cozinha', 'cocina', 'kitchenette'],
    'bathroom': ['bathroom', 'bath', 'wc', 'toilet', 'lavabo', 'powder', 'restroom'],
    'office': ['office', 'study', 'escritorio', 'home office'],
    'circulation': ['hallway', 'hall', 'corridor', 'corredor', 'circulation', 'entry', 'foyer'],
    'utility': ['storage', 'closet', 'laundry', 'utility', 'pantry', 'despensa', 'lavanderia']
}

# Fixed proportion ratios per room type (width:depth)
ROOM_TYPE_RATIOS = {
    'living': [(4, 3), (5, 4), (3, 2)],
    'bedroom': [(3, 2), (4, 3), (5, 4)],
    'kitchen': [(5, 3), (3, 2), (4, 3)],
    'bathroom': [(3, 2), (2, 1), (5, 4)],
    'office': [(3, 2), (4, 3), (5, 4)],
    'circulation': [(2, 1), (3, 1), (5, 2)],
    'utility': [(2, 1), (3, 2), (1, 1)],
    'default': [(3, 2), (4, 3), (5, 4), (1, 1)]
}

ROOM_TYPE_CONSTRAINTS = {
    'living': (0.6, 1.5),
    'bedroom': (0.5, 1.5),
    'kitchen': (0.5, 2.0),
    'bathroom': (0.4, 2.0),
    'office': (0.6, 1.5),
    'circulation': (0.3, 3.0),
    'utility': (0.4, 2.5),
    'default': (0.5, 1.5)
}

MIN_WALL_LENGTH = 120  # cm
MAX_WALL_LENGTH = 1000  # cm - reasonable maximum

# Room category colors (pastel RGB)
ROOM_COLORS = {
    'public': (150, 180, 255),
    'private': (255, 150, 150),
    'service': (255, 255, 150)
}

ROOM_CATEGORIES = {
    'living': 'public',
    'kitchen': 'public',
    'office': 'private',
    'bedroom': 'private',
    'bathroom': 'private',
    'utility': 'service',
    'circulation': 'service',
    'default': 'public'
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def detect_room_type(room_name):
    """Detect room type from name using keywords"""
    room_name_lower = room_name.lower()
    for room_type, keywords in ROOM_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in room_name_lower:
                return room_type
    return 'default'

def get_room_type_ratios(room_type):
    """Get preferred proportions for room type"""
    return ROOM_TYPE_RATIOS.get(room_type, ROOM_TYPE_RATIOS['default'])

def get_aspect_constraints(room_type):
    """Get aspect ratio constraints for room type"""
    return ROOM_TYPE_CONSTRAINTS.get(room_type, ROOM_TYPE_CONSTRAINTS['default'])

# ============================================================================
# MODULAR GRID SYSTEM - CORE ALGORITHM
# ============================================================================

def round_to_module(value, module):
    """Round value to nearest module"""
    if module <= 0:
        return value
    result = round(value / module) * module
    return max(result, module)  # At least one module unit

def calculate_room_dimensions_on_grid(area_m2, room_type, module_cm):
    """
    Calculate room dimensions using preferred ratios,
    snapped to modular grid
    
    Args:
        area_m2: Room area in square meters
        room_type: Room type string
        module_cm: Module size in centimeters
    
    Returns:
        (length_cm, width_cm) or None if impossible
    """
    area_cm2 = area_m2 * 10000
    preferred_ratios = get_room_type_ratios(room_type)
    min_aspect, max_aspect = get_aspect_constraints(room_type)
    
    best_dims = None
    best_error = float('inf')
    
    for ratio in preferred_ratios:
        length_ratio, width_ratio = ratio
        
        # Calculate ideal dimensions from ratio
        length = math.sqrt(area_cm2 * length_ratio / width_ratio)
        width = area_cm2 / length
        
        # Snap to modular grid
        length_snapped = round_to_module(length, module_cm)
        width_snapped = round_to_module(width, module_cm)
        
        # Ensure minimum dimensions
        length_snapped = max(length_snapped, MIN_WALL_LENGTH)
        width_snapped = max(width_snapped, MIN_WALL_LENGTH)
        
        # Safety check: ensure non-zero dimensions
        if length_snapped <= 0 or width_snapped <= 0:
            continue
        
        # Ensure they're multiples of module
        if length_snapped % module_cm != 0:
            length_snapped = round_to_module(length_snapped, module_cm)
        if width_snapped % module_cm != 0:
            width_snapped = round_to_module(width_snapped, module_cm)
        
        # Double-check after adjustment
        if length_snapped <= 0 or width_snapped <= 0:
            continue
        
        # Calculate actual area and error
        actual_area_cm2 = length_snapped * width_snapped
        area_error = abs(actual_area_cm2 - area_cm2)
        
        # Check aspect ratio constraints
        aspect = float(length_snapped) / float(width_snapped)
        if aspect < min_aspect or aspect > max_aspect:
            continue
        
        # Score: prefer smaller area error and earlier ratios
        ratio_preference = preferred_ratios.index(ratio)
        score = area_error + (ratio_preference * 10000)
        
        if score < best_error:
            best_error = score
            best_dims = (length_snapped, width_snapped)
    
    return best_dims

def find_optimal_module(rooms_data):
    """
    Find the optimal common module that:
    1. Works for all rooms
    2. Minimizes area errors
    3. Creates reasonable room proportions
    
    Tests all possible modules from MIN_WALL_LENGTH up
    """
    
    if not rooms_data or len(rooms_data) == 0:
        print("ERROR: No rooms to process!")
        return 150  # Default fallback
    
    print("\n" + "="*70)
    print("FINDING OPTIMAL MODULAR GRID")
    print("="*70)
    
    # Test modules: 120, 130, 140, 150, 160, 170, 180, 190, 200, 225, 250, 300, etc.
    test_modules = []
    
    # Fine increments from MIN_WALL_LENGTH to 200cm
    for m in range(MIN_WALL_LENGTH, 201, 10):
        test_modules.append(m)
    
    # Coarser increments from 200cm to 300cm
    for m in range(225, 301, 25):
        test_modules.append(m)
    
    # Even coarser for larger modules
    for m in range(350, 501, 50):
        test_modules.append(m)
    
    best_module = None
    best_total_error = float('inf')
    best_success_rate = 0
    
    results = []
    
    for module in test_modules:
        total_error = 0
        successful_rooms = 0
        failed_rooms = []
        
        for room in rooms_data:
            dims = calculate_room_dimensions_on_grid(
                room['area_m2'], 
                room['room_type'], 
                module
            )
            
            if dims:
                actual_area = (dims[0] * dims[1]) / 10000.0
                error = abs(actual_area - room['area_m2'])
                total_error += error
                successful_rooms += 1
            else:
                failed_rooms.append(room['name'])
        
        success_rate = successful_rooms / float(len(rooms_data))
        
        # Only consider modules that work for all rooms
        if success_rate == 1.0:
            avg_error = total_error / len(rooms_data)
            
            results.append({
                'module': module,
                'avg_error': avg_error,
                'total_error': total_error,
                'success_rate': success_rate
            })
            
            # Prefer modules with lower error
            if total_error < best_total_error:
                best_total_error = total_error
                best_module = module
                best_success_rate = success_rate
    
    # Show top 5 candidates
    if results:
        results.sort(key=lambda x: x['avg_error'])
        print("\nTop 5 module candidates:")
        for i, r in enumerate(results[:5], 1):
            print("  {0}. Module: {1}cm, Avg error: {2:.2f}m2, Total: {3:.2f}m2".format(
                i, int(r['module']), r['avg_error'], r['total_error']))
        
        print("\nSelected module: {0}cm".format(int(best_module)))
        print("Success rate: {0:.0f}%".format(best_success_rate * 100))
        print("Average area error: {0:.2f}m2".format(best_total_error / len(rooms_data)))
    else:
        print("\nWARNING: No module found that works for all rooms!")
        print("Using fallback: 150cm")
        best_module = 150
    
    return best_module

def apply_modular_dimensions(rooms_data, module_cm):
    """
    Apply modular grid to all rooms
    """
    print("\n" + "="*70)
    print("APPLYING MODULAR GRID: {0}cm".format(int(module_cm)))
    print("="*70)
    
    dimensioned_rooms = []
    
    for room in rooms_data:
        dims = calculate_room_dimensions_on_grid(
            room['area_m2'],
            room['room_type'],
            module_cm
        )
        
        if dims:
            length_cm, width_cm = dims
            actual_area = (length_cm * width_cm) / 10000.0
            
            dimensioned_room = room.copy()
            dimensioned_room['dimensions'] = (length_cm, width_cm)
            dimensioned_room['area_actual'] = actual_area
            dimensioned_room['module'] = module_cm
            
            dimensioned_rooms.append(dimensioned_room)
            
            print("  {0}: {1:.2f}x{2:.2f}m = {3:.2f}m2 (requested: {4:.2f}m2)".format(
                room['name'][:25],
                length_cm/100.0, width_cm/100.0,
                actual_area, room['area_m2']
            ))
        else:
            print("  ERROR: Could not dimension {0}".format(room['name']))
    
    return dimensioned_rooms

def analyze_modular_grid(rooms, module_cm):
    """
    Analyze how well the modular grid works
    """
    print("\n" + "="*70)
    print("MODULAR GRID ANALYSIS")
    print("="*70)
    
    # Collect all unique wall dimensions
    all_dimensions = []
    for room in rooms:
        all_dimensions.extend(room['dimensions'])
    
    unique_dims = sorted(set(all_dimensions))
    
    # Count occurrences
    dim_counts = {}
    for dim in all_dimensions:
        dim_counts[dim] = dim_counts.get(dim, 0) + 1
    
    # Calculate module statistics
    print("\nModule: {0}cm ({1}m)".format(int(module_cm), module_cm/100.0))
    print("Unique wall dimensions: {0}".format(len(unique_dims)))
    print("\nWall dimension distribution:")
    
    sorted_dims = sorted(dim_counts.items(), key=lambda x: x[1], reverse=True)
    for dim, count in sorted_dims:
        rooms_using = [r['name'][:20] for r in rooms if dim in r['dimensions']]
        multiples = int(dim / module_cm)
        print("  {0:.2f}m ({1}x module): {2} walls - {3}".format(
            dim/100.0, multiples, count, ", ".join(rooms_using[:3])
        ))
    
    # Universal connectivity
    total_walls = len(all_dimensions)
    print("\nTotal wall surfaces: {0}".format(total_walls))
    print("All walls are multiples of {0}cm".format(int(module_cm)))
    print("Universal connectivity: 100% (any room can connect to any room)")
    
    # Area accuracy
    total_requested = sum(r['area_m2'] for r in rooms)
    total_actual = sum(r['area_actual'] for r in rooms)
    variance = ((total_actual - total_requested) / total_requested) * 100
    
    print("\nArea accuracy:")
    print("  Requested: {0:.2f}m2".format(total_requested))
    print("  Actual: {0:.2f}m2".format(total_actual))
    print("  Variance: {0:+.2f}%".format(variance))

# ============================================================================
# MAIN PROGRAM
# ============================================================================

os.system("cls" if os.name == "nt" else "clear")

print("\n\nProgram2Mass {0}".format(ver))
print("By gduarte\n")
print("Modular Grid System: All walls as common multiples\n")

if not AUTO_MODE:
    print('Press "Enter" to run...')
    raw_input()

os.system("cls" if os.name == "nt" else "clear")

# File selection
print("Select a CSV file with your room program...")
csv_file = rs.OpenFileName("Select CSV File", "CSV Files (*.csv)|*.csv||")

if not csv_file:
    print("No file selected. Exiting...")
    sys.exit()

os.system("cls" if os.name == "nt" else "clear")

# Read CSV
rooms_data = []

try:
    with open(csv_file, 'r') as file:
        csv_reader = csv.reader(file)
        header = next(csv_reader, None)
        
        for row_num, row in enumerate(csv_reader, start=2):
            if len(row) >= 2 and row[0].strip() and row[1].strip():
                name = row[0].strip()
                try:
                    area = float(row[1].strip())
                    if area > 0:
                        room_type = detect_room_type(name)
                        
                        # Skip circulation rooms
                        if room_type == 'circulation':
                            print("  Skipping circulation: {0}".format(name))
                            continue
                        
                        # Warn about very small rooms
                        if area < 2.0:
                            print("  WARNING: Room '{0}' is very small ({1:.1f}m2)".format(name, area))
                        
                        rooms_data.append({
                            'name': name,
                            'area_m2': area,
                            'room_type': room_type
                        })
                except ValueError:
                    print("Warning: Row {0} - Invalid area".format(row_num))
                    
    print("Loaded {0} rooms from CSV\n".format(len(rooms_data)))
    
except Exception as e:
    print("Error reading CSV: {0}".format(e))
    if not AUTO_MODE:
        raw_input()
    sys.exit()

if not rooms_data:
    print("No valid room data found. Exiting...")
    if not AUTO_MODE:
        raw_input()
    sys.exit()

# Show detection
print("Room type detection:")
for i, room in enumerate(rooms_data, 1):
    print("  {0}. {1} ({2:.1f}m2) -> [{3}]".format(
        i, room['name'], room['area_m2'], room['room_type']))

# Find optimal module
optimal_module = find_optimal_module(rooms_data)

# Apply modular dimensions
rooms = apply_modular_dimensions(rooms_data, optimal_module)

# Analyze results
analyze_modular_grid(rooms, optimal_module)

# Save optimization log for launcher to display
script_dir = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(script_dir, "optimization_log.txt")
try:
    with open(log_path, 'w') as log_file:
        log_file.write("OPTIMIZATION SUMMARY\n")
        log_file.write("=" * 50 + "\n\n")
        log_file.write("Module: {}cm ({:.2f}m)\n".format(int(optimal_module), optimal_module/100.0))
        log_file.write("Total rooms: {}\n".format(len(rooms)))
        
        # Count unique dimensions
        all_dims = []
        for room in rooms:
            all_dims.extend(room['dimensions'])
        unique_dims = len(set(all_dims))
        log_file.write("Unique wall dimensions: {}\n".format(unique_dims))
        
        # Area accuracy
        total_requested = sum(r['area_m2'] for r in rooms)
        total_actual = sum(r['area_actual'] for r in rooms)
        variance = ((total_actual - total_requested) / total_requested) * 100
        log_file.write("Requested area: {:.2f}m2\n".format(total_requested))
        log_file.write("Actual area: {:.2f}m2\n".format(total_actual))
        log_file.write("Variance: {:+.2f}%\n".format(variance))
        log_file.write("\nAll walls are multiples of {}cm\n".format(int(optimal_module)))
        log_file.write("Universal connectivity: 100%\n")
except:
    pass

# Floor height
if AUTO_MODE and RUNTIME_CONFIG and 'floor_height' in RUNTIME_CONFIG:
    # Use pre-configured value from launcher
    floor_height = RUNTIME_CONFIG['floor_height']
    print("\n[AUTO] Using pre-configured floor height: {0} cm".format(floor_height))
else:
    # Manual input (fallback)
    floor_height = None
    while floor_height is None:
        try:
            height_input = raw_input("\nFloor-to-floor height in cm (e.g., 300): ")
            floor_height = float(height_input)
            if floor_height <= 0:
                print("Must be greater than 0")
                floor_height = None
            else:
                print("[OK] Height: {0} cm".format(floor_height))
        except ValueError:
            print("Invalid input")

# Generate geometry
print("\nGenerating geometry...")

# Clean up old layers
layer_names = ["ProgramMassing", "ProgramLabels", 
               "Program_Public", "Program_Private", "Program_Service"]
for layer_name in layer_names:
    if rs.IsLayer(layer_name):
        rs.CurrentLayer("Default")
        rs.DeleteLayer(layer_name)

# Create color-coded layers
rs.AddLayer("Program_Public", color=ROOM_COLORS['public'])
rs.AddLayer("Program_Private", color=ROOM_COLORS['private'])
rs.AddLayer("Program_Service", color=ROOM_COLORS['service'])
rs.AddLayer("ProgramLabels", color=(0, 0, 0))

current_x = 0
spacing_cm = 100

for i, room in enumerate(rooms, 1):
    length_cm, width_cm = room['dimensions']
    room_type = room.get('room_type', 'default')
    
    # Get category and set layer
    category = ROOM_CATEGORIES.get(room_type, 'public')
    layer_name = "Program_{0}".format(category.capitalize())
    
    rs.CurrentLayer(layer_name)
    corner = (current_x, 0, 0)
    rectangle = rs.AddRectangle(corner, length_cm, width_cm)
    
    if rectangle:
        surface = rs.AddPlanarSrf([rectangle])
        if surface:
            path = rs.AddLine((0, 0, 0), (0, 0, floor_height))
            box = rs.ExtrudeSurface(surface[0], path)
            rs.DeleteObject(surface[0])
            rs.DeleteObject(path)
            rs.DeleteObject(rectangle)
            
            rs.CurrentLayer("ProgramLabels")
            center_x = current_x + length_cm / 2.0
            center_y = width_cm / 2.0
            
            text_label = "{0}\n{1:.1f}".format(room['name'], room['area_actual'])
            text_dot = rs.AddTextDot(text_label, (center_x, center_y, floor_height))
            
            if box and text_dot:
                group_name = "Room_{0}_{1}".format(i, room['name'].replace(' ', '_'))
                group = rs.AddGroup(group_name)
                rs.AddObjectsToGroup([box, text_dot], group)
                print("  [OK] {0} [{1}]".format(room['name'], category))
    
    current_x += length_cm + spacing_cm

rs.ZoomExtents()
rs.CurrentLayer("Default")

print("\n[DONE] Massing generated successfully!")
print("Module: {0}cm - All walls are multiples!".format(int(optimal_module)))
print("\nLayers created:")
print("  - Program_Public (blue)")
print("  - Program_Private (red)")
print("  - Program_Service (yellow)")
print("  - ProgramLabels")
print("\nAll rooms can connect - walls align on {0}cm grid!".format(int(optimal_module)))