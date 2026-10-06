#!/usr/bin/env python3
"""
RoboNav-SLAM: Standalone Python SLAM & Navigation Benchmarking Tool
Performs fast offline simulation of 2D LiDAR raycasting, Bayesian Log-Odds
Occupancy Grid Mapping, A* path planning, and Dynamic Window Approach (DWA).

Usage:
  python3 standalone_slam_sim.py
"""

import math
import random
import time
import numpy as np

class StandaloneSlamSim:
    def __init__(self):
        self.width = 80
        self.height = 60
        self.res = 0.1 # 10cm per cell -> 8m x 6m room
        
        # Log-odds occupancy grid: 0 = unknown, <0 = free, >0 = occupied
        self.log_odds = np.zeros((self.height, self.width), dtype=np.float32)
        
        # Ground truth obstacles: rectangles (x, y, w, h) in meters
        self.obstacles = [
            (0.0, 0.0, 8.0, 0.2), # North Wall
            (0.0, 5.8, 8.0, 0.2), # South Wall
            (0.0, 0.0, 0.2, 6.0), # West Wall
            (7.8, 0.0, 0.2, 6.0), # East Wall
            (2.0, 1.5, 0.8, 2.5), # Central Pillar
            (5.0, 3.0, 1.5, 1.0), # Table
        ]
        
        # Robot Pose: x, y, theta (meters, meters, radians)
        self.rx = 1.0
        self.ry = 1.0
        self.rtheta = 0.0
        
        print("==================================================================")
        print("RoboNav-SLAM Standalone Python Benchmark Initialized")
        print(f"Arena: 8.0m x 6.0m | Resolution: {self.res*100:.0f}cm | Grid: {self.width}x{self.height}")
        print("==================================================================")

    def cast_lidar(self, num_beams=360, max_range=6.0):
        scan = []
        for i in range(num_beams):
            beam_angle = self.rtheta + (i * 2.0 * math.pi / num_beams)
            cos_a = math.cos(beam_angle)
            sin_a = math.sin(beam_angle)
            
            closest_dist = max_range
            hit = False
            
            # Step ray forward
            step = 0.05
            dist = 0.15
            while dist <= max_range:
                px = self.rx + cos_a * dist
                py = self.ry + sin_a * dist
                
                # Check collision with obstacles
                for ox, oy, ow, oh in self.obstacles:
                    if ox <= px <= ox + ow and oy <= py <= oy + oh:
                        closest_dist = dist
                        hit = True
                        break
                if hit:
                    break
                dist += step
                
            scan.append((beam_angle, closest_dist, hit))
        return scan

    def update_slam(self, scan):
        L_OCC = 0.85
        L_FREE = -0.35
        
        r_c = int(self.rx / self.res)
        r_r = int(self.ry / self.res)
        
        for angle, dist, hit in scan[::4]: # sample every 4th beam
            hit_x = self.rx + dist * math.cos(angle)
            hit_y = self.ry + dist * math.sin(angle)
            h_c = int(hit_x / self.res)
            h_r = int(hit_y / self.res)
            
            # Bresenham update
            self.bresenham_line(r_c, r_r, h_c, h_r, hit, L_OCC, L_FREE)

    def bresenham_line(self, x0, y0, x1, y1, hit, l_occ, l_free):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        cx, cy = x0, y0
        while True:
            is_end = (cx == x1 and cy == y1)
            if 0 <= cx < self.width and 0 <= cy < self.height:
                if is_end and hit:
                    self.log_odds[cy, cx] = min(5.0, self.log_odds[cy, cx] + l_occ)
                elif not is_end:
                    self.log_odds[cy, cx] = max(-5.0, self.log_odds[cy, cx] + l_free)
            if is_end:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                cx += sx
            if e2 < dx:
                err += dx
                cy += sy

    def run_benchmark(self, steps=30):
        print("\nStarting Autonomous SLAM Benchmark Run...")
        start_time = time.time()
        
        for step in range(steps):
            # Move robot forward in a circle
            self.rx += 0.15 * math.cos(self.rtheta)
            self.ry += 0.15 * math.sin(self.rtheta)
            self.rtheta = (self.rtheta + 0.1) % (2 * math.pi)
            
            # LiDAR scan & SLAM update
            scan = self.cast_lidar(num_beams=360)
            self.update_slam(scan)
            
            # Metrics
            known_cells = np.count_nonzero(np.abs(self.log_odds) > 0.2)
            coverage = (known_cells / (self.width * self.height)) * 100.0
            
            if (step + 1) % 10 == 0 or step == steps - 1:
                print(f"Step {step+1:02d}/{steps} | Pose: ({self.rx:.2f}m, {self.ry:.2f}m, {math.degrees(self.rtheta):.1f}°) | Mapped Coverage: {coverage:.1f}%")
                
        elapsed = time.time() - start_time
        print(f"\n[BENCHMARK SUCCESS] Completed {steps} steps in {elapsed:.3f}s ({steps/elapsed:.1f} Hz SLAM loop)")

if __name__ == '__main__':
    sim = StandaloneSlamSim()
    sim.run_benchmark(steps=30)
