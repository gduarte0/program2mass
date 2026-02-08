# -*- coding: utf-8 -*-
"""
Program2Mass v0.4 - Enhanced Optimization
Multi-pass optimization, dimension clustering, and intelligent wall value scoring
By gduarte
"""

import os
import sys
import csv
import math
import rhinoscriptsyntax as rs

ver = "0.4"

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

# Adjacency preferences for wall value scoring
ADJACENCY_PREFERENCES = {
    'kitchen': {
        'preferred': ['living', 'dining'],
        'avoid': ['bedroom', 'bathroom'],
        'bonus': 40
    },
    'bathroom': {
        'preferred': ['bedroom'],
        'avoid': ['kitchen', 'living'],
        'bonus': 50
    },
    'bedroom': {
        'preferred': ['bedroom', 'bathroom'],
        'avoid': ['kitchen'],
        'bonus': 30
    },
    'utility': {
        'preferred': ['kitchen', 'bathroom'],
        'avoid': [],
        'bonus': 35
    },
    'living': {
        'preferred': ['kitchen', 'dining'],
        'avoid': ['bathroom'],
        'bonus': 25
    }
}

MIN_WALL_LENGTH = 120
PREFERRED_WALL_INCREMENTS = 50

# Room category colors (pastel RGB)
ROOM_COLORS = {
    'public': (150, 180, 255),    # Light blue
    'private': (255, 150, 150),   # Light red/pink
    'service': (255, 255, 150)    # Light yellow
}

# Room type to category mapping
ROOM_CATEGORIES = {
    'living': 'public',
    'kitchen': 'public',
    'office': 'private',
    'bedroom': 'private',
    'bathroom': 'private',
    'utility': 'service',
    'circulation': 'service',  # Won't be used since circulation is filtered
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

def round_to_increment(value, increment):
    """Round value to nearest increment"""
    return round(value / increment) * increment

def get_room_type_ratios(room_type):
    """Get preferred proportions for room type"""
    return ROOM_TYPE_RATIOS.get(room_type, ROOM_TYPE_RATIOS['default'])

def get_aspect_constraints(room_type):
    """Get aspect ratio constraints for room type"""
    return ROOM_TYPE_CONSTRAINTS.get(room_type, ROOM_TYPE_CONSTRAINTS['default'])

def find_best_dimensions(area_m2, room_type):
    """Calculate optimal dimensions for room based on type and area"""
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

# ============================================================================
# OPTIMIZATION 1: DIMENSION CLUSTERING
# ============================================================================

def find_dimension_clusters(all_dimensions, tolerance=50):
    """
    Group similar dimensions within tolerance into clusters.
    This catches near-misses (e.g., 450, 500, 550 → one cluster at 500)
    """
    if not all_dimensions:
        return []
    
    clusters = []
    sorted_dims = sorted(set(all_dimensions))
    
    for dim in sorted_dims:
        found_cluster = False
        
        # Try to add to existing cluster
        for cluster in clusters:
            if abs(cluster['center'] - dim) <= tolerance:
                cluster['members'].append(dim)
                cluster['count'] += all_dimensions.count(dim)
                # Recalculate center as weighted average
                total = sum(m * all_dimensions.count(m) for m in cluster['members'])
                cluster['center'] = total / cluster['count']
                cluster['center'] = round_to_increment(cluster['center'], PREFERRED_WALL_INCREMENTS)
                found_cluster = True
                break
        
        if not found_cluster:
            clusters.append({
                'center': dim,
                'members': [dim],
                'count': all_dimensions.count(dim)
            })
    
    # Sort by count (most common first)
    clusters.sort(key=lambda x: x['count'], reverse=True)
    
    return clusters

# ============================================================================
# OPTIMIZATION 2: WALL VALUE SCORING
# ============================================================================

def calculate_wall_value(dimension, room1, room2):
    """
    Calculate value score for sharing a wall between two rooms.
    Higher scores = more desirable connections.
    """
    score = 0.0
    
    # Base score: longer walls are more structurally valuable
    score += dimension / 10.0  # 500cm wall = 50 base points
    
    room1_type = room1.get('room_type', 'default')
    room2_type = room2.get('room_type', 'default')
    
    # Adjacency preference bonus
    if room1_type in ADJACENCY_PREFERENCES:
        prefs = ADJACENCY_PREFERENCES[room1_type]
        if room2_type in prefs['preferred']:
            score += prefs['bonus']
        elif room2_type in prefs.get('avoid', []):
            score -= 30  # Penalty for undesirable adjacency
    
    if room2_type in ADJACENCY_PREFERENCES:
        prefs = ADJACENCY_PREFERENCES[room2_type]
        if room1_type in prefs['preferred']:
            score += prefs['bonus']
        elif room1_type in prefs.get('avoid', []):
            score -= 30
    
    # Plumbing bonus: wet rooms should be adjacent for efficiency
    wet_rooms = ['kitchen', 'bathroom', 'utility']
    if room1_type in wet_rooms and room2_type in wet_rooms:
        score += 45
    
    # Same-type bonus: bedrooms near bedrooms, offices near offices
    if room1_type == room2_type and room1_type != 'default':
        score += 25
    
    # Structural continuity bonus: prefer dimensions that create alignment
    if dimension >= 400:  # Walls 4m+ are structurally significant
        score += 15
    
    return score

def calculate_room_connection_value(room, target_dims, all_rooms):
    """
    Calculate total value of connecting a room using target dimensions
    """
    total_value = 0.0
    connections = 0
    
    for other_room in all_rooms:
        if other_room is room:
            continue
        
        # Check if any target dimension matches other room's dimensions
        for target_dim in target_dims:
            if target_dim in other_room['dimensions']:
                wall_value = calculate_wall_value(target_dim, room, other_room)
                total_value += wall_value
                connections += 1
    
    return total_value, connections

# ============================================================================
# OPTIMIZATION 3: MULTI-PASS OPTIMIZATION WITH TIGHTER TOLERANCE
# ============================================================================

def optimize_room_connections_multipass(rooms, max_passes=3):
    """
    Multi-pass optimization with progressively tighter tolerances.
    Each pass refines the previous results.
    """
    
    print("\n" + "="*70)
    print("ENHANCED OPTIMIZATION")
    print("="*70)
    
    improvements_made = []
    
    for pass_num in range(1, max_passes + 1):
        # Progressive tolerance: 6% → 5% → 4%
        area_tolerance = 0.07 - (pass_num - 1) * 0.01
        
        print("\nPass {0}/3: Area tolerance = {1:.1f}%".format(pass_num, area_tolerance * 100))
        
        # Collect all current dimensions
        all_dimensions = []
        for room in rooms:
            all_dimensions.extend(room['dimensions'])
        
        # Find dimension clusters
        clusters = find_dimension_clusters(all_dimensions, tolerance=50)
        
        print("  Found {0} dimension clusters".format(len(clusters)))
        
        # Show top clusters on first pass
        if pass_num == 1:
            for i, cluster in enumerate(clusters[:3], 1):
                members_str = ", ".join([str(int(m)) for m in sorted(set(cluster['members']))])
                print("    #{0}: {1}cm ({2} walls) [merged from: {3}cm]".format(
                    i, int(cluster['center']), cluster['count'], members_str))
        
        # Extract preferred dimensions from clusters
        preferred_dims = [c['center'] for c in clusters]
        
        # Optimize each room
        optimized_this_pass = 0
        
        for room in rooms:
            original_area = room['area_m2']
            original_dims = room['dimensions']
            room_type = room.get('room_type', 'default')
            min_aspect, max_aspect = get_aspect_constraints(room_type)
            
            best_match = None
            best_value = 0
            
            # Try each preferred dimension from clusters
            for target_dim in preferred_dims[:6]:  # Top 6 dimensions
                
                # Try target_dim as length
                test_width = (original_area * 10000) / target_dim
                test_width = round_to_increment(test_width, PREFERRED_WALL_INCREMENTS)
                test_width = max(test_width, MIN_WALL_LENGTH)
                
                test_area = (target_dim * test_width) / 10000
                area_diff = abs(test_area - original_area) / original_area
                
                if area_diff <= area_tolerance:
                    aspect = target_dim / test_width
                    if min_aspect <= aspect <= max_aspect:
                        value, connections = calculate_room_connection_value(
                            room, [target_dim, test_width], rooms
                        )
                        
                        if value > best_value:
                            best_value = value
                            best_match = (target_dim, test_width, test_area, connections)
                
                # Try target_dim as width
                test_length = (original_area * 10000) / target_dim
                test_length = round_to_increment(test_length, PREFERRED_WALL_INCREMENTS)
                test_length = max(test_length, MIN_WALL_LENGTH)
                
                test_area = (test_length * target_dim) / 10000
                area_diff = abs(test_area - original_area) / original_area
                
                if area_diff <= area_tolerance:
                    aspect = test_length / target_dim
                    if min_aspect <= aspect <= max_aspect:
                        value, connections = calculate_room_connection_value(
                            room, [test_length, target_dim], rooms
                        )
                        
                        if value > best_value:
                            best_value = value
                            best_match = (test_length, target_dim, test_area, connections)
            
            # Apply optimization if valuable enough
            if best_match and best_value > 60:  # Threshold for worthwhile change
                if room['dimensions'] != (best_match[0], best_match[1]):
                    room['dimensions'] = (best_match[0], best_match[1])
                    room['area_actual'] = best_match[2]
                    room['optimized'] = True
                    optimized_this_pass += 1
                    
                    improvements_made.append({
                        'pass': pass_num,
                        'room': room['name'],
                        'old': original_dims,
                        'new': (best_match[0], best_match[1]),
                        'value': best_value,
                        'connections': best_match[3]
                    })
        
        print("  Optimized: {0} rooms".format(optimized_this_pass))
        
        # Stop if no improvements
        if optimized_this_pass == 0:
            print("  No improvements found - optimization complete")
            break
    
    # Show key improvements
    if improvements_made and len(improvements_made) <= 5:
        print("\nKey improvements:")
        for imp in improvements_made[:5]:
            print("  {0}: {1:.0f}×{2:.0f} -> {3:.0f}×{4:.0f}cm ({5} connections, score: {6:.0f})".format(
                imp['room'][:25], 
                imp['old'][0], imp['old'][1],
                imp['new'][0], imp['new'][1],
                imp['connections'], imp['value']
            ))
    
    return rooms

# ============================================================================
# STATISTICS AND ANALYSIS
# ============================================================================

def analyze_optimization_results(rooms):
    """Generate detailed statistics about optimization results"""
    
    # Collect all dimensions
    all_dimensions = []
    for room in rooms:
        all_dimensions.extend(room['dimensions'])
    
    # Calculate statistics
    unique_dims = set(all_dimensions)
    dim_counts = {}
    for dim in all_dimensions:
        dim_counts[dim] = dim_counts.get(dim, 0) + 1
    
    # Shared walls
    shared_wall_count = sum(count for count in dim_counts.values() if count > 1)
    total_walls = len(all_dimensions)
    sharing_pct = (shared_wall_count / float(total_walls)) * 100 if total_walls > 0 else 0
    
    # Optimized rooms
    optimized_rooms = [r for r in rooms if r.get('optimized', False)]
    
    # Area accuracy
    total_requested = sum(r['area_m2'] for r in rooms)
    total_actual = sum(r['area_actual'] for r in rooms)
    area_variance = ((total_actual - total_requested) / total_requested) * 100
    
    # Display results
    print("\n" + "="*70)
    print("OPTIMIZATION RESULTS")
    print("="*70)
    print("")
    print("Rooms:")
    print("  Total: {0}".format(len(rooms)))
    print("  Optimized: {0} ({1:.0f}%)".format(len(optimized_rooms), 
          (len(optimized_rooms)/float(len(rooms)))*100))
    print("")
    print("Dimensions:")
    print("  Total wall surfaces: {0}".format(total_walls))
    print("  Unique dimensions: {0}".format(len(unique_dims)))
    print("  Walls in shared dimensions: {0} ({1:.0f}%)".format(
          shared_wall_count, sharing_pct))
    print("")
    print("Area Accuracy:")
    print("  Requested: {0:.2f} m2".format(total_requested))
    print("  Actual: {0:.2f} m2".format(total_actual))
    print("  Variance: {0:+.2f}%".format(area_variance))
    print("")
    print("Most common dimensions:")
    sorted_dims = sorted(dim_counts.items(), key=lambda x: x[1], reverse=True)
    for dim, count in sorted_dims[:5]:
        pct = (count / float(total_walls)) * 100
        rooms_using = [r['name'] for r in rooms if dim in r['dimensions']]
        print("  {0:.2f}m: {1} walls ({2:.0f}%) - {3}".format(
              dim/100.0, count, pct, ", ".join(rooms_using[:3])))

# ============================================================================
# MAIN PROGRAM
# ============================================================================

os.system("cls" if os.name == "nt" else "clear")

print("\n\nProgram2Mass {0}".format(ver))
print("By gduarte\n")
print("Enhanced optimization: multi-pass + dimension clustering + wall scoring\n")

print('Press "Enter" to run...')
raw_input()

os.system("cls" if os.name == "nt" else "clear")

# File selection
print("Select a CSV file with your room program...")
csv_file = rs.OpenFileName("Select CSV File", "CSV Files (*.csv)|*.csv||")

if not csv_file:
    print("No file selected. Exiting...")
    raw_input()
    sys.exit()

os.system("cls" if os.name == "nt" else "clear")

# Read CSV
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
                        room_type = detect_room_type(name)
                        
                        # Skip circulation rooms
                        if room_type == 'circulation':
                            print("  Skipping circulation room: {0}".format(name))
                            continue
                        
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
                    print("Warning: Row {0} - Invalid area".format(row_num))
                    
    print("Loaded {0} rooms from CSV\n".format(len(rooms)))
    
except Exception as e:
    print("Error reading CSV: {0}".format(e))
    raw_input()
    sys.exit()

if not rooms:
    print("No valid room data found. Exiting...")
    raw_input()
    sys.exit()

# Show detection
print("Room type detection:")
for i, room in enumerate(rooms, 1):
    print("  {0}. {1} -> [{2}]".format(i, room['name'], room['room_type']))

# Run enhanced optimization
rooms = optimize_room_connections_multipass(rooms, max_passes=3)

# Show results
analyze_optimization_results(rooms)

print("\n" + "="*70)
print("FINAL DIMENSIONS")
print("="*70)

for i, room in enumerate(rooms, 1):
    length_m = room['dimensions'][0] / 100.0
    width_m = room['dimensions'][1] / 100.0
    status = " [OPTIMIZED]" if room['optimized'] else ""
    area_diff = room['area_actual'] - room['area_m2']
    print("{0}. {1} ({2}): {3:.2f}×{4:.2f}m = {5:.2f}m2 ({6:+.1f}m2){7}".format(
        i, room['name'], room['room_type'], length_m, width_m, 
        room['area_actual'], area_diff, status))

# Floor height
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

# Create color-coded layers by category
rs.AddLayer("Program_Public", color=ROOM_COLORS['public'])
rs.AddLayer("Program_Private", color=ROOM_COLORS['private'])
rs.AddLayer("Program_Service", color=ROOM_COLORS['service'])
rs.AddLayer("ProgramLabels", color=(0, 0, 0))

current_x = 0
spacing_cm = 100

for i, room in enumerate(rooms, 1):
    length_cm, width_cm = room['dimensions']
    room_type = room.get('room_type', 'default')
    
    # Get category and set appropriate layer
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
print("Layers created:")
print("  - Program_Public (blue) - Living rooms, kitchens, public spaces")
print("  - Program_Private (red) - Bedrooms, bathrooms, offices")
print("  - Program_Service (yellow) - Utility, storage spaces")
print("  - ProgramLabels - Text labels")

