"""
Sync Manager Module - Neural Memory & Cloud Sync
Handles synaptic weight checkpointing and cloud synchronization.
Uses NumPy for neural network operations (PyTorch-compatible architecture).
"""

import numpy as np
import os
import requests
from typing import Dict, Optional
import json
from datetime import datetime
import pickle


class SyncManager:
    """
    Manages neural memory checkpoints and cloud synchronization
    """
    
    def __init__(self, checkpoint_file: str = "fly_memory.pt", remote_url: Optional[str] = None):
        """
        Initialize sync manager
        
        Args:
            checkpoint_file: Local checkpoint file for synaptic weights
            remote_url: Remote repository URL for cloud sync
        """
        self.checkpoint_file = checkpoint_file
        self.remote_url = remote_url
        
        # Neural memory (synaptic weights)
        self.neural_memory = {}
        self.memory_version = 1
        
        # Sync status
        self.last_sync_time = None
        self.is_connected = False
        
        print(f"Sync Manager initialized with checkpoint: {checkpoint_file}")
        
        # Check for remote connection
        if remote_url:
            self.check_remote_connection()
    
    def check_remote_connection(self) -> bool:
        """
        Check if remote repository is accessible
        
        updated memory weights so the fly's learned piloting skills persist and improve across updates.
        
        Returns:
            True if connected, False otherwise
        """
        if not self.remote_url:
            self.is_connected = False
            return False
        
        try:
            response = requests.get(self.remote_url, timeout=5)
            self.is_connected = response.status_code == 200
            print(f"Remote connection: {self.is_connected}")
            return self.is_connected
        except Exception as e:
            print(f"Remote connection failed: {e}")
            self.is_connected = False
            return False
    
    def save_checkpoint(self, neural_weights: Dict):
        """
        Save neural weights to local checkpoint file
        
        Args:
            neural_weights: Dictionary of neural network weights
        """
        self.neural_memory = neural_weights
        self.memory_version += 1
        
        # Save using pickle
        checkpoint = {
            'weights': neural_weights,
            'version': self.memory_version,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(self.checkpoint_file, 'wb') as f:
            pickle.dump(checkpoint, f)
        print(f"Checkpoint saved: {self.checkpoint_file} (version {self.memory_version})")
    
    def load_checkpoint(self) -> Dict:
        """
        Load neural weights from local checkpoint file
        
        Returns:
            Dictionary of neural network weights
        """
        if not os.path.exists(self.checkpoint_file):
            print(f"No checkpoint file found: {self.checkpoint_file}")
            return {}
        
        try:
            with open(self.checkpoint_file, 'rb') as f:
                checkpoint = pickle.load(f)
            self.neural_memory = checkpoint['weights']
            self.memory_version = checkpoint['version']
            print(f"Checkpoint loaded: {self.checkpoint_file} (version {self.memory_version})")
            return self.neural_memory
        except Exception as e:
            print(f"Error loading checkpoint: {e}")
            return {}
    
    def fetch_remote_checkpoint(self) -> Optional[Dict]:
        """
        Fetch updated memory weights from remote repository
        
        Returns:
            Dictionary of neural network weights, or None if unavailable
        """
        if not self.is_connected or not self.remote_url:
            print("Remote not connected, cannot fetch checkpoint")
            return None
        
        try:
            response = requests.get(f"{self.remote_url}/fly_memory.pkl", timeout=30)
            if response.status_code == 200:
                # Save to local file
                with open(self.checkpoint_file, 'wb') as f:
                    f.write(response.content)
                
                # Load checkpoint
                with open(self.checkpoint_file, 'rb') as f:
                    checkpoint = pickle.load(f)
                self.neural_memory = checkpoint['weights']
                self.memory_version = checkpoint['version']
                self.last_sync_time = datetime.now()
                
                print(f"Remote checkpoint fetched (version {self.memory_version})")
                return self.neural_memory
            else:
                print(f"Failed to fetch remote checkpoint: HTTP {response.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching remote checkpoint: {e}")
            return None
    
    def upload_checkpoint(self):
        """
        Upload local checkpoint to remote repository
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected or not self.remote_url:
            print("Remote not connected, cannot upload checkpoint")
            return False
        
        try:
            with open(self.checkpoint_file, 'rb') as f:
                files = {'file': (f'fly_memory_v{self.memory_version}.pkl', f)}
                response = requests.post(f"{self.remote_url}/upload", files=files, timeout=30)
            
            if response.status_code == 200:
                self.last_sync_time = datetime.now()
                print(f"Checkpoint uploaded successfully")
                return True
            else:
                print(f"Failed to upload checkpoint: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"Error uploading checkpoint: {e}")
            return False
    
    def get_sync_status(self) -> Dict:
        """
        Get current sync status
        
        Returns:
            Dictionary with sync status information
        """
        return {
            'is_connected': self.is_connected,
            'last_sync_time': self.last_sync_time,
            'memory_version': self.memory_version,
            'checkpoint_file': self.checkpoint_file,
            'has_local_checkpoint': os.path.exists(self.checkpoint_file)
        }
    
    def create_initial_checkpoint(self, connectome_weights: np.ndarray):
        """
        Create initial checkpoint from connectome weights
        
        Args:
            connectome_weights: Connectome weight matrix
        """
        # Save connectome weights as initial memory
        initial_weights = {
            'connectome_weights': connectome_weights,
            'learned_modifications': np.zeros_like(connectome_weights),
            'training_history': []
        }
        
        self.save_checkpoint(initial_weights)
        print("Initial checkpoint created from connectome weights")


if __name__ == "__main__":
    sync_manager = SyncManager()
    print("Sync Manager module loaded")
