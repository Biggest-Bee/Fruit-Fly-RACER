# Fruit Fly Racer — Application Summary & Feature Reference

## What the app is

Fruit Fly Racer is a Python-based simulation application featuring a virtual fruit fly driven by a scanned connectome-inspired neural model, navigating through a challenging 3D obstacle tunnel with dynamic wind and strict physics limits.

### Technical Stack
- **Language:** Python 3.10+
- **Physics Engine:** MuJoCo (using the official `flybody` biological rig for the fly body)
- **Neural/Math Backend:** NumPy and pickle for serialization
- **Connectome:** MaleCNS v1.0 fruit fly connectome (211,577 neurons / ~151.8M connections)

## Core Features

### 1. 3D Obstacle Tunnel Environment (`environment.py`)
- **Continuous Racing Tunnel:** A 3D tunnel with dynamic, shifting wind fields (turbulence) that affect the fly's flight path
- **Procedural Obstacle Generation:** Randomized obstacles including:
  - Triangles, cubes, rectangles, flat planes, walls, and cones
  - Variant versions with custom **holes/apertures** for navigation
- **Physics Limits:**
  - Strict maximum speed limit (5.0 m/s)
  - Continuous tracking of velocity, speed, altitude, direction, and 3D position
- **Collision Detection:** Real-time collision checking with obstacles and tunnel walls
- **Progress Tracking:** Calculate progress to finish line (0 to 1)

### 2. Sensory & Neural Inputs (`agent_logic.py`)
Feed telemetry and environmental data into the fly's neural network:
- Current altitude and direction vector
- Current speed and velocity vector
- Localized positional awareness (visual field with 20 angular bins)
- Detected obstacles and relative layout data (20 nearest obstacles)
- Speed limit enforcement

### 3. Reward & Penalty System (`rewards.py`)
- **Positive Rewards:** Dense distance-based progression shaping (closer to finish = more points)
- **Negative Penalties:** Collision penalties (-50 points per collision)
- **Score Tracking:** Total points (max 1000), collision count, best progress

### 4. Neural Memory & Cloud Sync (`sync_manager.py`)
- **Synaptic Weight Checkpointing:** Separate static connectome from mutable synaptic weights (`fly_memory.pkl`)
- **Cloud Synchronization:** Fetch updated memory weights from remote repository
- **Version Tracking:** Track memory version and sync timestamps
- **Connectome Initialization:** Create initial checkpoint from connectome weights

### 5. Core Brain Simulation (`brain_sim/`)
- **brain_engine.py:** Core brain simulation engine
- **neuron_models.py:** Integrate-and-fire neuron models
- **synapse_models.py:** Synapse models with plasticity

## Project Structure

```
fruit-fly-racer/
├── environment.py           # 3D obstacle tunnel with MuJoCo physics
├── agent_logic.py           # Sensory & neural inputs
├── rewards.py              # Reward and penalty system
├── sync_manager.py          # Neural memory and cloud sync
├── brain_sim/
│   ├── brain_engine.py      # Core brain simulation
│   ├── neuron_models.py     # Neuron models
│   └── synapse_models.py    # Synapse models
├── data/
│   ├── connectome-weights-male-cns-v1.0-minconf-0.5.feather
│   └── body-annotations-male-cns-v1.0-minconf-0.5.feather
├── fly_memory.pkl           # Neural memory checkpoint (auto-generated)
├── env.example              # Environment configuration template
├── .env                     # Environment configuration (local, ignored)
├── FEATURES.md              # This file
├── PROJECT_PLAN.md          # Project plan and roadmap
└── agent_memory.md          # Development memory and notes
```

## Recent Updates (2026-10-03)

**MAJOR PIVOT:** Complete rewrite from coding training to racing simulation
- Deleted all coding training files
- Created new racing simulation modules
- Implemented MuJoCo physics engine
- Added procedural obstacle generation
- Implemented reward/penalty system
- Added neural memory with cloud sync
