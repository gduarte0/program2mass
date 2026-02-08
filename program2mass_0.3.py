# -*- coding: utf-8 -*-
"""
Program2Mass 0.3

CSV-driven program massing with intelligent room type detection
By gduarte
"""

import os
import sys
import csv
import math
import rhinoscriptsyntax as rs

# Version
ver = 0.3

# ============================================================================
# ROOM TYPE DETECTION
# ============================================================================

# Keywords to detect room types from room names
ROOM_TYPE_KEYWORDS = {
    'living': ['living', 'sala', 'family room', 'lounge', 'sitting'],
    'bedroom': ['bedroom', 'quarto', 'suite', 'dormitorio', 'bed', 'master'],
    'kitchen': ['kitchen', 'cozinha', 'cocina', 'kitchenette'],
    'bathroom': ['bathroom', 'bath', 'wc', 'toilet', 'lavabo', 'powder', 'restroom'],
    'office': ['office', 'study', 'escritorio', 'home office'],
    'circulation': ['hallway', 'hall', 'corridor', 'corredor', 'circulation', 'entry', 'foyer'],
    'utility': ['storage', 'closet', 'laundry', 'utility', 'pantry', 'despensa', 'lavanderia']
}

# Room type configurations
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

MIN_WALL_LENGTH = 110
PREFERRED_WALL_INCREMENTS = 50

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def detect_room_type(room_name):
    """
    Automatically detect room type from room name
    Returns the detected room type or 'default'
    """
    room_name_lower = room_name.lower()
    
    for room_type, keywords in ROOM_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in room_name_lower:
                return room_type
    
    return 'default'

def round_to_increment(value, increment):
    return round(value / increment) * increment

def get_room_type_ratios(room_type):
    return ROOM_TYPE_RATIOS.get(room_type, ROOM_TYPE_RATIOS['default'])

def get_aspect_constraints(room_type):
    return ROOM_TYPE_CONSTRAINTS.get(room_type, ROOM_TYPE_CONSTRAINTS['default'])

def find_best_dimensions(area_m2, room_type):
    area_cm2 = area_m2 * 10000
    preferred_ratios = get_room_type_ratios(room_type)
    min_aspect, max_aspect = get_aspect_constraints(room_type)
    
    best_dims = None
    best_score = float('inf')
    
    for ratio in preferred_ratios:
        length_ratio, width_ratio = ratio
        length = math.sqrt(area_cm2 * length_ratio / width_ratio)
        width = area_cm2 / length
        
        length_rounded = round_to_increment(length, PREFERRED_WALL_INCREMENTS)
        width_rounded = round_to_increment(width, PREFERRED_WALL_INCREMENTS)
        
        length_rounded = max(length_rounded, MIN_WALL_LENGTH)
        width_rounded = max(width_rounded, MIN_WALL_LENGTH)
        
        actual_area_cm2 = length_rounded * width_rounded
        area_error = abs(actual_area_cm2 - area_cm2)
        aspect = length_rounded / width_rounded
        
        if aspect < min_aspect or aspect > max_aspect:
            continue
        
        ratio_preference = preferred_ratios.index(ratio)
        score = area_error + (ratio_preference * 10000)
        
        if score < best_score:
            best_score = score
            best_dims = (length_rounded, width_rounded)
    
    if best_dims is None:
        side = math.sqrt(area_cm2)
        side_rounded = round_to_increment(side, PREFERRED_WALL_INCREMENTS)
        side_rounded = max(side_rounded, MIN_WALL_LENGTH)
        best_dims = (side_rounded, side_rounded)
    
    return best_dims

def find_common_dimensions(room_list):
    all_dimensions = []
    for room in room_list:
        all_dimensions.extend(room['dimensions'])
    
    dim_counts = {}
    for dim in all_dimensions:
        dim_counts[dim] = dim_counts.get(dim, 0) + 1
    
    return dim_counts

def optimize_room_connections(rooms):
    AREA_TOLERANCE = 0.05
    dim_counts = find_common_dimensions(rooms)
    common_dims = sorted(dim_counts.items(), key=lambda x: x[1], reverse=True)
    
    if len(common_dims) == 0:
        return rooms
    
    optimized_rooms = []
    
    for room in rooms:
        original_area = room['area_m2']
        room_type = room.get('room_type', 'default')
        min_aspect, max_aspect = get_aspect_constraints(room_type)
        
        best_match = None
        best_shared_walls = 0
        
        for common_dim, count in common_dims[:3]:
            test_width = (original_area * 10000) / common_dim
            test_width = round_to_increment(test_width, PREFERRED_WALL_INCREMENTS)
            test_width = max(test_width, MIN_WALL_LENGTH)
            
            test_area = (common_dim * test_width) / 10000
            area_diff = abs(test_area - original_area) / original_area
            
            if area_diff <= AREA_TOLERANCE:
                aspect = common_dim / test_width
                if min_aspect <= aspect <= max_aspect:
                    shared = dim_counts.get(common_dim, 0) + dim_counts.get(test_width, 0)
                    if shared > best_shared_walls:
                        best_shared_walls = shared
                        best_match = (common_dim, test_width, test_area)
            
            test_length = (original_area * 10000) / common_dim
            test_length = round_to_increment(test_length, PREFERRED_WALL_INCREMENTS)
            test_length = max(test_length, MIN_WALL_LENGTH)
            
            test_area = (test_length * common_dim) / 10000
            area_diff = abs(test_area - original_area) / original_area
            
            if area_diff <= AREA_TOLERANCE:
                aspect = test_length / common_dim
                if min_aspect <= aspect <= max_aspect:
                    shared = dim_counts.get(test_length, 0) + dim_counts.get(common_dim, 0)
                    if shared > best_shared_walls:
                        best_shared_walls = shared
                        best_match = (test_length, common_dim, test_area)
        
        if best_match and best_shared_walls > 1:
            optimized_room = room.copy()
            optimized_room['dimensions'] = (best_match[0], best_match[1])
            optimized_room['area_actual'] = best_match[2]
            optimized_room['optimized'] = True
            optimized_rooms.append(optimized_room)
        else:
            optimized_rooms.append(room)
    
    return optimized_rooms

# ============================================================================
# MAIN PROGRAM
# ============================================================================

os.system("cls" if os.name == "nt" else "clear")

print("\n\nProgram2Mass {0} \nBy gduarte \n".format(ver))
print("CSV-driven program massing with AUTO room type detection\n")

print('Press "Enter" to run...')
raw_input()

os.system("cls" if os.name == "nt" else "clear")

print("Select a CSV file with your room program...")
csv_file = rs.OpenFileName("Select CSV File", "CSV Files (*.csv)|*.csv||")

if not csv_file:
    print("No file selected. Exiting...")
    raw_input()
    sys.exit()

os.system("cls" if os.name == "nt" else "clear")

# Read CSV (only 2 columns needed: Room Name, Area)
rooms = []

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
                        # Auto-detect room type from name
                        room_type = detect_room_type(name)
                        
                        length_cm, width_cm = find_best_dimensions(area, room_type)
                        actual_area = (length_cm * width_cm) / 10000.0
                        
                        rooms.append({
                            'name': name,
                            'area_m2': area,
                            'area_actual': actual_area,
                            'dimensions': (length_cm, width_cm),
                            'room_type': room_type,
                            'optimized': False
                        })
                except ValueError:
                    print("Warning: Row {0} - Invalid area value".format(row_num))
                    
    print("\nLoaded {0} rooms from CSV".format(len(rooms)))
    
except Exception as e:
    print("Error reading CSV file: {0}".format(e))
    raw_input()
    sys.exit()

if not rooms:
    print("No valid room data found in CSV. Exiting...")
    raw_input()
    sys.exit()

# Show detected room types
print("\nDetected room types:")
for i, room in enumerate(rooms, 1):
    print("  {0}. {1} -> [{2}]".format(i, room['name'], room['room_type']))

# Optimize
print("\nOptimizing room dimensions...\n")
rooms = optimize_room_connections(rooms)

# Display summary
print("="*70)
print("ROOM SUMMARY")
print("="*70)
print("")

for i, room in enumerate(rooms, 1):
    length_m = room['dimensions'][0] / 100.0
    width_m = room['dimensions'][1] / 100.0
    status = " [OPTIMIZED]" if room['optimized'] else ""
    print("{0}. {1} ({2}): {3:.2f}x{4:.2f}m = {5:.2f}m2{6}".format(
        i, room['name'], room['room_type'], length_m, width_m, 
        room['area_actual'], status))

# Get floor height
floor_height = None
while floor_height is None:
    try:
        print("Enter floor-to-floor height in cm:")
        height_input = raw_input()
        floor_height = float(height_input)
        
        if floor_height <= 0:
            print("Invalid value. Height must be greater than 0.")
            floor_height = None
        else:
            print("[OK] Floor-to-floor height: {0} cm".format(floor_height))
    except ValueError:
        print("Invalid value. Please enter a numeric value.")

# Generate geometry
print("\nGenerating massing geometry...")

if rs.IsLayer("ProgramMassing"):
    rs.CurrentLayer("Default")
    rs.DeleteLayer("ProgramMassing")
if rs.IsLayer("ProgramLabels"):
    rs.CurrentLayer("Default")
    rs.DeleteLayer("ProgramLabels")

rs.AddLayer("ProgramMassing", color=(200, 200, 200))
rs.AddLayer("ProgramLabels", color=(0, 0, 0))

current_x = 0
spacing_cm = 100

for i, room in enumerate(rooms, 1):
    length_cm, width_cm = room['dimensions']
    
    rs.CurrentLayer("ProgramMassing")
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
            
            # Simple label: Room name and area only
            text_label = "{0}\n{1:.1f}".format(
                room['name'], 
                room['area_actual']
            )
            text_dot = rs.AddTextDot(text_label, (center_x, center_y, floor_height))
            
            if box and text_dot:
                group_name = "Room_{0}_{1}".format(i, room['name'].replace(' ', '_'))
                group = rs.AddGroup(group_name)
                rs.AddObjectsToGroup([box, text_dot], group)
                print("  [OK] Room {0}: {1} ({2})".format(i, room['name'], room['room_type']))
    
    current_x += length_cm + spacing_cm

rs.ZoomExtents()
rs.CurrentLayer("Default")

print("\n[OK] Done! Press Enter to close")
raw_input()
