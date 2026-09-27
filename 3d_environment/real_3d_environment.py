"""
3D Environment with Real 3D Fly Model
Using Ursina Engine for real 3D simulation
"""

try:
    from ursina import *
    from ursina.prefabs.first_person_controller import FirstPersonController
    import sys
    import os
    import math
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    
    print("Starting 3D Fruit Fly Environment...")
    
    # Initialize Ursina
    app = Ursina()
    
    # Set up the window
    window.title = "Fruit Fly AI - 3D Environment"
    window.borderless = False
    window.fullscreen = False
    window.exit_button.visible = False
    
    # Create the enclosure box (large room)
    room_size = 20
    wall_thickness = 1
    
    # Floor
    floor = Entity(
        model='plane',
        scale=(room_size, 1, room_size),
        color=color.gray,
        texture='white_cube',
        collider='box',
        position=(0, 0, 0)
    )
    
    # Ceiling
    ceiling = Entity(
        model='plane',
        scale=(room_size, 1, room_size),
        color=color.light_gray,
        texture='white_cube',
        collider='box',
        position=(0, room_size/2, 0),
        rotation=(180, 0, 0)
    )
    
    # Walls
    wall_positions = [
        (0, room_size/4, -room_size/2),  # Back wall
        (0, room_size/4, room_size/2),   # Front wall
        (-room_size/2, room_size/4, 0),  # Left wall
        (room_size/2, room_size/4, 0),   # Right wall
    ]
    
    wall_rotations = [
        (0, 0, 0),     # Back wall
        (0, 180, 0),    # Front wall
        (0, 90, 0),     # Left wall
        (0, -90, 0),    # Right wall
    ]
    
    walls = []
    for pos, rot in zip(wall_positions, wall_rotations):
        wall = Entity(
            model='cube',
            scale=(room_size, room_size/2, wall_thickness),
            color=color.azure,
            texture='white_cube',
            collider='box',
            position=pos,
            rotation=rot
        )
        walls.append(wall)
    
    # Food locations (red spheres in corners)
    food_positions = [
        (-room_size/2 + 2, 1, -room_size/2 + 2),
        (room_size/2 - 2, 1, -room_size/2 + 2),
        (-room_size/2 + 2, 1, room_size/2 - 2),
        (room_size/2 - 2, 1, room_size/2 - 2),
    ]
    
    food_items = []
    for pos in food_positions:
        food = Entity(
            model='sphere',
            scale=1,
            color=color.red,
            position=pos,
            collider='sphere'
        )
        food_items.append(food)
    
    # Create 3D fly model (using basic shapes for now)
    # Body
    fly_body = Entity(
        model='sphere',
        scale=(0.5, 0.3, 0.8),
        color=color.brown,
        position=(0, 1, 0),
        collider='box'
    )
    
    # Head
    fly_head = Entity(
        model='sphere',
        scale=0.25,
        color=color.dark_gray,
        position=(0, 1.1, 0.4),
        parent=fly_body
    )
    
    # Wings (simple planes)
    left_wing = Entity(
        model='plane',
        scale=(0.8, 0.4),
        color=color.cyan,
        position=(-0.4, 0.1, 0),
        parent=fly_body,
        rotation=(0, 0, 30)
    )
    
    right_wing = Entity(
        model='plane',
        scale=(0.8, 0.4),
        color=color.cyan,
        position=(0.4, 0.1, 0),
        parent=fly_body,
        rotation=(0, 0, -30)
    )
    
    # Eyes
    left_eye = Entity(
        model='sphere',
        scale=0.08,
        color=color.black,
        position=(-0.1, 0.1, 0.1),
        parent=fly_head
    )
    
    right_eye = Entity(
        model='sphere',
        scale=0.08,
        color=color.black,
        position=(0.1, 0.1, 0.1),
        parent=fly_head
    )
    
    # Fly movement variables
    fly_speed = 2
    fly_direction = Vec3(1, 0, 0)
    target_food = None
    is_eating = False
    
    # Player controller (to move around the environment)
    player = FirstPersonController()
    player.position = (0, 2, -room_size/2 + 3)
    player.cursor.visible = True
    
    # UI Text
    info_text = Text(
        text='WASD to move | Mouse to look | Fly AI will move autonomously',
        position=(-0.85, 0.45),
        scale=1,
        color=color.white
    )
    
    status_text = Text(
        text='Fly Status: Searching for food...',
        position=(-0.85, 0.40),
        scale=1,
        color=color.yellow
    )
    
    def update():
        """Update function called every frame"""
        global target_food, is_eating
        
        # Fly AI movement
        if not is_eating:
            # Simple AI: move towards nearest food
            nearest_food = None
            min_distance = float('inf')
            
            for food in food_items:
                distance = distance_xz(fly_body.position, food.position)
                if distance < min_distance:
                    min_distance = distance
                    nearest_food = food
            
            if nearest_food:
                target_food = nearest_food
                direction = (target_food.position - fly_body.position).normalized()
                fly_body.position += direction * fly_speed * time.dt
                
                # Face the direction of movement
                fly_body.look_at(target_food.position)
                
                # Wing flapping animation
                import math
                wing_flap = math.sin(time.time() * 20) * 30
                left_wing.rotation_z = 30 + wing_flap
                right_wing.rotation_z = -30 - wing_flap
                
                status_text.text = f'Fly Status: Moving to food (Distance: {min_distance:.2f})'
                status_text.color = color.yellow
                
                # Check if reached food
                if min_distance < 0.5:
                    is_eating = True
                    status_text.text = 'Fly Status: Eating...'
                    status_text.color = color.green
            else:
                # Random movement if no food
                fly_body.position += fly_direction * fly_speed * time.dt * 0.5
                status_text.text = 'Fly Status: Searching...'
                status_text.color = color.white
        else:
            # Eating behavior
            eat_timer = 2  # Eat for 2 seconds
            if eat_timer > 0:
                eat_timer -= time.dt
                status_text.text = f'Fly Status: Eating ({eat_timer:.1f}s remaining)'
            else:
                is_eating = False
                # Remove eaten food
                if target_food in food_items:
                    food_items.remove(target_food)
                    destroy(target_food)
                    target_food = None
                    status_text.text = 'Fly Status: Food consumed!'
        
        # Keep fly within bounds
        fly_body.x = clamp(fly_body.x, -room_size/2 + 1, room_size/2 - 1)
        fly_body.z = clamp(fly_body.z, -room_size/2 + 1, room_size/2 - 1)
        fly_body.y = clamp(fly_body.y, 0.5, room_size/2 - 1)
    
    # Instructions
    print("3D Environment Controls:")
    print("WASD - Move around")
    print("Mouse - Look around")
    print("ESC - Exit")
    print("The fly will autonomously search for and eat food")
    
    # Run the app
    app.run()
    
except ImportError:
    print("Ursina Engine not installed.")
    print("Install with: pip install ursina")
    print("This is required for real 3D environments.")
    
    # Fallback: Show instructions
    print("\nTo get real 3D functionality:")
    print("1. Install Ursina: pip install ursina")
    print("2. Run this script again")
    print("3. You'll be able to:")
    print("   - Move around in 3D space")
    print("   - Watch the fly move in 3D")
    print("   - See the fly eat food in 3D")
    print("   - Navigate the environment")