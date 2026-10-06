"""
Game entities and particle systems for Cosmic Star Catcher.
All visual assets are rendered using vibrant vector geometry and particle effects.
"""

import math
import random
import pygame

# Color definitions
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GOLD = (255, 215, 0)
YELLOW = (255, 240, 50)
CYAN = (0, 240, 255)
MAGENTA = (255, 0, 180)
NEON_GREEN = (50, 255, 100)
ORANGE = (255, 140, 0)
RED = (255, 60, 60)
PURPLE = (160, 32, 240)
SLATE_BLUE = (30, 40, 70)

class Particle:
    def __init__(self, x, y, vx, vy, color, radius=4, decay=0.95, life=30):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.radius = radius
        self.decay = decay
        self.life = life
        self.max_life = life

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= self.decay
        self.vy *= self.decay
        self.radius = max(0.5, self.radius * 0.96)
        self.life -= 1

    def draw(self, surface):
        if self.life > 0 and self.radius > 0.5:
            alpha = int(255 * (self.life / self.max_life))
            temp_surface = pygame.Surface((int(self.radius * 2 + 2), int(self.radius * 2 + 2)), pygame.SRCALPHA)
            pygame.draw.circle(temp_surface, (*self.color[:3], alpha), (int(self.radius + 1), int(self.radius + 1)), int(self.radius))
            surface.blit(temp_surface, (self.x - self.radius, self.y - self.radius))

    def is_dead(self):
        return self.life <= 0 or self.radius <= 0.5


class Star:
    def __init__(self, x, y, is_rainbow=False):
        self.x = x
        self.y = y
        self.speed = random.uniform(2.5, 4.5)
        self.is_rainbow = is_rainbow
        self.points = 500 if is_rainbow else 100
        self.size = 18 if is_rainbow else 14
        self.angle = random.uniform(0, 360)
        self.rot_speed = random.uniform(2, 5)
        self.color = MAGENTA if is_rainbow else GOLD
        self.pulse = random.uniform(0, math.pi * 2)

    def update(self, player_x=None, player_y=None, magnet_active=False):
        self.y += self.speed
        self.angle += self.rot_speed
        self.pulse += 0.1

        # Magnetic attraction towards player
        if magnet_active and player_x is not None and player_y is not None:
            dx = player_x - self.x
            dy = player_y - self.y
            dist = math.hypot(dx, dy)
            if dist < 220 and dist > 0:
                self.x += (dx / dist) * 7.0
                self.y += (dy / dist) * 7.0

    def draw(self, surface):
        scale = self.size + math.sin(self.pulse) * 3
        # 5-pointed star polygon
        points = []
        for i in range(10):
            r = scale if i % 2 == 0 else scale * 0.45
            a = math.radians(self.angle + i * 36)
            points.append((self.x + r * math.sin(a), self.y - r * math.cos(a)))
        
        star_color = (
            int(128 + 127 * math.sin(self.pulse)),
            int(128 + 127 * math.sin(self.pulse + 2)),
            int(128 + 127 * math.sin(self.pulse + 4))
        ) if self.is_rainbow else GOLD

        pygame.draw.polygon(surface, star_color, points)
        pygame.draw.polygon(surface, WHITE, points, 1)

    @property
    def rect(self):
        return pygame.Rect(self.x - self.size, self.y - self.size, self.size * 2, self.size * 2)


class Asteroid:
    def __init__(self, x, y, speed_mult=1.0):
        self.x = x
        self.y = y
        self.radius = random.randint(18, 30)
        self.speed = random.uniform(2.0, 4.0) * speed_mult
        self.angle = random.uniform(0, 360)
        self.rot_speed = random.uniform(-3, 3)
        self.color = random.choice([(140, 110, 100), (120, 120, 140), (160, 90, 80)])
        
        # Jagged polygon vertices
        self.offsets = []
        num_pts = 8
        for i in range(num_pts):
            r = self.radius + random.uniform(-4, 5)
            self.offsets.append(r)

    def update(self):
        self.y += self.speed
        self.angle += self.rot_speed

    def draw(self, surface):
        points = []
        num_pts = len(self.offsets)
        for i, r in enumerate(self.offsets):
            a = math.radians(self.angle + i * (360 / num_pts))
            points.append((self.x + r * math.cos(a), self.y + r * math.sin(a)))
        
        pygame.draw.polygon(surface, self.color, points)
        pygame.draw.polygon(surface, (80, 60, 60), points, 2)
        # Small cute crater details
        pygame.draw.circle(surface, (70, 50, 50), (int(self.x + 3), int(self.y - 4)), int(self.radius * 0.25))

    @property
    def rect(self):
        return pygame.Rect(self.x - self.radius * 0.8, self.y - self.radius * 0.8, self.radius * 1.6, self.radius * 1.6)


class PowerUp:
    TYPE_SHIELD = "shield"
    TYPE_MAGNET = "magnet"
    TYPE_TURBO = "turbo"
    
    TYPES = [TYPE_SHIELD, TYPE_MAGNET, TYPE_TURBO]

    def __init__(self, x, y, ptype=None):
        self.x = x
        self.y = y
        self.speed = 2.8
        self.type = ptype if ptype else random.choice(self.TYPES)
        self.radius = 16
        self.pulse = 0.0

    def update(self):
        self.y += self.speed
        self.pulse += 0.08

    def draw(self, surface):
        glow = math.sin(self.pulse) * 3
        
        if self.type == self.TYPE_SHIELD:
            color = CYAN
            icon = "🛡️"
        elif self.type == self.TYPE_MAGNET:
            color = RED
            icon = "🧲"
        else:
            color = NEON_GREEN
            icon = "⚡"

        # Outer glowing ring
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(self.radius + glow), 2)
        # Inner fill circle
        pygame.draw.circle(surface, (20, 30, 60), (int(self.x), int(self.y)), int(self.radius))
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(self.radius - 3), 2)

        # Draw symbol/initial in center
        font = pygame.font.SysFont("arial", 14, bold=True)
        symbol = "S" if self.type == self.TYPE_SHIELD else ("M" if self.type == self.TYPE_MAGNET else "T")
        txt = font.render(symbol, True, color)
        surface.blit(txt, txt.get_rect(center=(int(self.x), int(self.y))))

    @property
    def rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)


class Player:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.x = screen_width // 2
        self.y = screen_height - 100
        self.vx = 0.0
        self.vy = 0.0
        self.speed = 7.5
        self.width = 44
        self.height = 54
        self.tilt = 0.0  # Bank angle in degrees

        # Power-up states (timers in frames)
        self.shield_timer = 0
        self.magnet_timer = 0
        self.turbo_timer = 0
        self.invulnerable_timer = 0

    def update(self, move_left, move_right, boost_up, boost_down, particles):
        # Target horizontal movement
        target_vx = 0.0
        if move_left:
            target_vx -= self.speed * (1.6 if self.turbo_timer > 0 else 1.0)
        if move_right:
            target_vx += self.speed * (1.6 if self.turbo_timer > 0 else 1.0)

        # Smooth horizontal acceleration
        self.vx += (target_vx - self.vx) * 0.25
        self.x += self.vx

        # Vertical movement (Jump / Jetpack boost)
        target_vy = 0.0
        if boost_up:
            target_vy -= 5.0
        if boost_down:
            target_vy += 5.0

        self.vy += (target_vy - self.vy) * 0.2
        self.y += self.vy

        # Screen boundaries
        self.x = max(30, min(self.screen_width - 30, self.x))
        self.y = max(100, min(self.screen_height - 50, self.y))

        # Dynamic ship tilt banking
        target_tilt = (self.vx / self.speed) * 22.0
        self.tilt += (target_tilt - self.tilt) * 0.2

        # Decrement power-up timers
        if self.shield_timer > 0: self.shield_timer -= 1
        if self.magnet_timer > 0: self.magnet_timer -= 1
        if self.turbo_timer > 0: self.turbo_timer -= 1
        if self.invulnerable_timer > 0: self.invulnerable_timer -= 1

        # Emit thruster flame particles
        flame_color = (
            random.choice([CYAN, MAGENTA, YELLOW]) if self.turbo_timer > 0 
            else random.choice([ORANGE, YELLOW, RED])
        )
        for _ in range(2 if self.turbo_timer > 0 else 1):
            px = self.x + random.uniform(-6, 6)
            py = self.y + 24
            vx = random.uniform(-0.8, 0.8) - self.vx * 0.1
            vy = random.uniform(3.5, 7.0)
            particles.append(Particle(px, py, vx, vy, flame_color, radius=random.uniform(4, 7), life=22))

    def activate_powerup(self, ptype):
        duration = 360  # 6 seconds at 60 FPS
        if ptype == PowerUp.TYPE_SHIELD:
            self.shield_timer = duration
        elif ptype == PowerUp.TYPE_MAGNET:
            self.magnet_timer = duration
        elif ptype == PowerUp.TYPE_TURBO:
            self.turbo_timer = duration

    def hit(self):
        """Called when taking damage. Returns True if protected by shield."""
        if self.shield_timer > 0:
            self.shield_timer = 0
            self.invulnerable_timer = 60
            return True
        if self.invulnerable_timer > 0:
            return True
        self.invulnerable_timer = 90
        return False

    def draw(self, surface):
        # Flicker when invulnerable
        if self.invulnerable_timer > 0 and (self.invulnerable_timer // 6) % 2 == 0:
            return

        # Create ship surface with banking rotation
        ship_surf = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
        cx, cy = (self.width + 20) // 2, (self.height + 20) // 2

        # Draw Rocket Body
        body_color = WHITE
        fin_color = RED if self.turbo_timer == 0 else CYAN
        nose_color = RED
        
        # Fins / Wings
        pygame.draw.polygon(ship_surf, fin_color, [
            (cx - 20, cy + 18),
            (cx - 6, cy + 6),
            (cx - 6, cy + 20)
        ])
        pygame.draw.polygon(ship_surf, fin_color, [
            (cx + 20, cy + 18),
            (cx + 6, cy + 6),
            (cx + 6, cy + 20)
        ])

        # Main Fuselage
        pygame.draw.polygon(ship_surf, body_color, [
            (cx, cy - 22),       # Nose tip
            (cx - 12, cy + 6),   # Left mid
            (cx - 8, cy + 20),   # Left bottom
            (cx + 8, cy + 20),   # Right bottom
            (cx + 12, cy + 6)    # Right mid
        ])
        
        # Nose cone
        pygame.draw.polygon(ship_surf, nose_color, [
            (cx, cy - 22),
            (cx - 7, cy - 8),
            (cx + 7, cy - 8)
        ])

        # Cockpit Window (Glowing cyan bubble)
        pygame.draw.circle(ship_surf, CYAN, (cx, cy), 6)
        pygame.draw.circle(ship_surf, WHITE, (cx - 2, cy - 2), 2)

        # Rotate according to bank angle
        rotated_surf = pygame.transform.rotate(ship_surf, -self.tilt)
        rot_rect = rotated_surf.get_rect(center=(self.x, self.y))
        surface.blit(rotated_surf, rot_rect)

        # Draw Shield Bubble if active
        if self.shield_timer > 0:
            shield_radius = 34 + math.sin(pygame.time.get_ticks() * 0.01) * 3
            shield_surf = pygame.Surface((int(shield_radius * 2 + 10), int(shield_radius * 2 + 10)), pygame.SRCALPHA)
            alpha = int(120 + 60 * math.sin(pygame.time.get_ticks() * 0.01))
            pygame.draw.circle(shield_surf, (*CYAN, alpha), (int(shield_radius + 5), int(shield_radius + 5)), int(shield_radius), 3)
            pygame.draw.circle(shield_surf, (*WHITE, 40), (int(shield_radius + 5), int(shield_radius + 5)), int(shield_radius - 4))
            surface.blit(shield_surf, (self.x - shield_radius - 5, self.y - shield_radius - 5))

    @property
    def rect(self):
        return pygame.Rect(self.x - 16, self.y - 18, 32, 38)
