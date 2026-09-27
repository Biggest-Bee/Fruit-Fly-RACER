"""
3D Environment with a brain-driven fly

The fly is not scripted: its wings are driven by the spiking network in
brain_controller.py, which reads the fly's senses and produces thrust, yaw and
pitch commands. The enclosure is a closed box with a food source in each of its
four bottom corners, and hunger can be switched on and off at runtime.

Simulation coordinates are Z-up (x, y, z); Ursina is Y-up, so a simulation
position (x, y, z) is drawn at (x, z, y).
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from brain_controller import BrainFlyController

ROOM_SIZE = 20.0  # Width and depth of the enclosure
ROOM_HEIGHT = 12.0  # Height of the enclosure
FOOD_INSET = 2.0  # How far the corner food sits from the walls
FOOD_CAPACITY = 100.0
FOOD_REGROWTH = 2.0  # Units of food per second


def corner_food_sources():
    """A food source in each of the four bottom corners of the box."""
    edge = ROOM_SIZE / 2.0 - FOOD_INSET
    return [
        {"position": (-edge, -edge, 0.8), "amount": FOOD_CAPACITY},
        {"position": (edge, -edge, 0.8), "amount": FOOD_CAPACITY},
        {"position": (-edge, edge, 0.8), "amount": FOOD_CAPACITY},
        {"position": (edge, edge, 0.8), "amount": FOOD_CAPACITY},
    ]


def run():
    """Open the Ursina window and run the simulation."""
    from ursina import (
        Entity, Text, Ursina, Vec3, application, camera, color, held_keys,
        mouse, time, window,
    )

    app = Ursina()
    window.title = "Fruit Fly AI - 3D Environment"
    window.borderless = False
    window.fullscreen = False
    window.exit_button.visible = False
    window.color = color.rgb(12, 12, 18)

    controller = BrainFlyController(bounds=(ROOM_SIZE, ROOM_SIZE, ROOM_HEIGHT))
    food_sources = corner_food_sources()

    # ---------------------------------------------------------------- enclosure
    Entity(model='plane', scale=(ROOM_SIZE, 1, ROOM_SIZE),
           color=color.rgb(70, 70, 80), texture='white_cube', position=(0, 0, 0))
    Entity(model='plane', scale=(ROOM_SIZE, 1, ROOM_SIZE),
           color=color.rgb(55, 55, 65), texture='white_cube',
           position=(0, ROOM_HEIGHT, 0), rotation=(180, 0, 0))

    half = ROOM_SIZE / 2.0
    wall_specs = [
        ((0, ROOM_HEIGHT / 2, -half), (0, 0, 0)),
        ((0, ROOM_HEIGHT / 2, half), (0, 180, 0)),
        ((-half, ROOM_HEIGHT / 2, 0), (0, 90, 0)),
        ((half, ROOM_HEIGHT / 2, 0), (0, -90, 0)),
    ]
    for position, rotation in wall_specs:
        Entity(model='plane', scale=(ROOM_SIZE, 1, ROOM_HEIGHT),
               color=color.rgba(120, 170, 220, 60), texture='white_cube',
               position=position, rotation=(90, rotation[1], 0), double_sided=True)

    # -------------------------------------------------------------------- food
    food_entities = []
    for source in food_sources:
        x, y, z = source["position"]
        food_entities.append(Entity(model='sphere', scale=1.0, color=color.red,
                                    position=(x, z, y)))

    # --------------------------------------------------------------------- fly
    fly = Entity(model='sphere', scale=(0.8, 0.35, 0.45), color=color.rgb(90, 60, 40))
    Entity(model='sphere', scale=(0.35, 0.8, 0.8), color=color.dark_gray,
           position=(0.55, 0.15, 0), parent=fly)
    Entity(model='sphere', scale=(0.18, 0.4, 0.4), color=color.red,
           position=(0.75, 0.2, 0.35), parent=fly)
    Entity(model='sphere', scale=(0.18, 0.4, 0.4), color=color.red,
           position=(0.75, 0.2, -0.35), parent=fly)
    left_wing = Entity(model='cube', scale=(0.7, 0.05, 1.6),
                       color=color.rgba(200, 230, 255, 140),
                       position=(-0.1, 0.35, 0.9), parent=fly)
    right_wing = Entity(model='cube', scale=(0.7, 0.05, 1.6),
                        color=color.rgba(200, 230, 255, 140),
                        position=(-0.1, 0.35, -0.9), parent=fly)

    # ---------------------------------------------------------------- free cam
    camera.position = (0, ROOM_HEIGHT * 0.6, -ROOM_SIZE)
    camera.rotation = (10, 0, 0)
    camera_angle = [0.0, 10.0]

    hud = Text(text='', position=(-0.86, 0.46), scale=0.9, color=color.white)
    Text(
        text='[H] hunger on/off   [R] reset fly   [F] feed fly   '
             '[WASD/QE] move camera   [right-drag] look   [ESC] quit',
        position=(-0.86, -0.46), scale=0.8, color=color.light_gray)

    def update():
        dt = min(time.dt, 0.05)

        # Food slowly regrows so the fly always has something to find
        for source in food_sources:
            source["amount"] = min(FOOD_CAPACITY, source["amount"] + FOOD_REGROWTH * dt)

        state = controller.update(dt, food_sources)

        x, y, z = state["position"]
        fly.position = Vec3(x, z, y)
        fly.rotation = (
            math.degrees(state["pitch"]),
            -math.degrees(state["yaw"]),
            math.degrees(state["roll"]),
        )

        flap = math.sin(state["wing_beat_phase"]) * 55.0
        left_wing.rotation_x = flap
        right_wing.rotation_x = -flap

        for entity, source in zip(food_entities, food_sources):
            fraction = source["amount"] / FOOD_CAPACITY
            entity.scale = 0.35 + 1.1 * fraction
            entity.color = color.red if fraction > 0.25 else color.rgb(120, 70, 70)

        brain = state["brain"]
        motor = state["motor"]
        hud.text = (
            f"behaviour: {state['behavior']}\n"
            f"hunger: {'ON' if state['hunger_enabled'] else 'OFF'}   "
            f"energy: {state['energy']:.0f}%   meals: {state['meals_eaten']}\n"
            f"position: ({x:.1f}, {y:.1f}, {z:.1f})   speed: {state['speed']:.1f}\n"
            f"neurons: {brain['neurons']} "
            f"({brain['recurrent_connections']} recurrent connections)   "
            f"spikes: {brain['total_spikes']}\n"
            f"motor: thrust {motor['thrust']:.2f}  "
            f"yaw {motor['yaw_left'] - motor['yaw_right']:+.2f}  "
            f"pitch {motor['pitch_up'] - motor['pitch_down']:+.2f}"
        )
        hud.color = color.green if state["hunger_enabled"] else color.cyan

        # Free-look camera
        speed = 12.0 * dt
        camera.position += camera.forward * (held_keys['w'] - held_keys['s']) * speed
        camera.position += camera.right * (held_keys['d'] - held_keys['a']) * speed
        camera.position += camera.up * (held_keys['e'] - held_keys['q']) * speed
        if mouse.right:
            camera_angle[0] += mouse.velocity[0] * 120.0
            camera_angle[1] -= mouse.velocity[1] * 120.0
            camera.rotation = (camera_angle[1], camera_angle[0], 0)

    def input(key):
        if key == 'h':
            controller.toggle_hunger()
        elif key == 'r':
            controller.reset()
        elif key == 'f':
            controller.feed(30.0)
        elif key == 'escape':
            application.quit()

    # Ursina calls the module level `update` and `input` functions each frame
    globals()['update'] = update
    globals()['input'] = input
    app.run()


if __name__ == "__main__":
    try:
        run()
    except ImportError as error:
        print(f"Ursina Engine not available ({error}).")
        print("Install it with: pip install ursina")
