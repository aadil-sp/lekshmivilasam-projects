#!/usr/bin/env python3
"""
Cosmic Star Catcher - A kid-friendly space arcade game.
Controlled via Bluetooth using M5StickC PLUS 2 or Mac Keyboard!

Controls:
  - Tilt Left / Right or Left/Right Arrow Keys : Steer Rocket
  - M5 Front Button or UP Arrow / Space      : Boost / Jetpack Jump
  - Side Button or DOWN Arrow / Enter        : Secondary Action / Power
  - P / ESC                                  : Pause
"""

import sys
import math
import random
import argparse
import pygame

from sound_fx import SoundManager
from game_objects import (
    Player, Star, Asteroid, PowerUp, Particle,
    WHITE, BLACK, GOLD, YELLOW, CYAN, MAGENTA, NEON_GREEN, ORANGE, RED, PURPLE, SLATE_BLUE
)

# Game Window Constants
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 750
FPS = 60

class FloatingText:
    def __init__(self, x, y, text, color, size=24, life=45):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.size = size
        self.life = life
        self.max_life = life

    def update(self):
        self.y -= 1.4
        self.life -= 1

    def draw(self, surface):
        if self.life > 0:
            alpha = int(255 * (self.life / self.max_life))
            font = pygame.font.SysFont("impact", self.size)
            txt_surf = font.render(self.text, True, self.color)
            txt_surf.set_alpha(alpha)
            surface.blit(txt_surf, txt_surf.get_rect(center=(self.x, self.y)))


class Starfield:
    """Parallax scrolling starfield with multiple speed layers."""
    def __init__(self, count=90):
        self.stars = []
        for _ in range(count):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            speed = random.choice([0.8, 1.8, 3.2])
            size = 1 if speed < 1.0 else (2 if speed < 2.5 else 3)
            color = random.choice([WHITE, (200, 220, 255), (255, 240, 200)])
            self.stars.append([x, y, speed, size, color])

    def update(self, turbo_mult=1.0):
        for s in self.stars:
            s[1] += s[2] * turbo_mult
            if s[1] > SCREEN_HEIGHT:
                s[1] = 0
                s[0] = random.randint(0, SCREEN_WIDTH)

    def draw(self, surface):
        for x, y, speed, size, color in self.stars:
            pygame.draw.circle(surface, color, (int(x), int(y)), size)


class CosmicStarCatcher:
    STATE_START = "start"
    STATE_PLAY = "play"
    STATE_PAUSE = "pause"
    STATE_GAMEOVER = "gameover"

    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        pygame.init()
        pygame.display.set_caption("Cosmic Star Catcher 🚀 (M5StickC BLE Controller)")
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.sound = SoundManager()
        self.starfield = Starfield()

        # Fonts
        self.title_font = pygame.font.SysFont("impact", 46)
        self.hud_font = pygame.font.SysFont("arial", 22, bold=True)
        self.sub_font = pygame.font.SysFont("arial", 18)
        self.combo_font = pygame.font.SysFont("impact", 28)

        # High Score Tracking
        self.high_score = 0

        # Initialize Game State
        self.reset_game()
        self.state = self.STATE_START

    def reset_game(self):
        self.player = Player(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.stars = []
        self.asteroids = []
        self.powerups = []
        self.particles = []
        self.floating_texts = []
        
        self.score = 0
        self.display_score = 0
        self.lives = 3
        self.combo = 0
        self.max_combo = 0
        self.stars_caught = 0
        self.spawn_timer = 0
        self.difficulty_timer = 0
        self.screen_shake = 0

    def add_floating_text(self, x, y, text, color, size=24):
        self.floating_texts.append(FloatingText(x, y, text, color, size))

    def trigger_confetti(self, x, y, count=30):
        colors = [GOLD, CYAN, MAGENTA, NEON_GREEN, ORANGE, WHITE]
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            spd = random.uniform(3.0, 9.0)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            self.particles.append(Particle(x, y, vx, vy, random.choice(colors), radius=random.uniform(3, 6), life=40))

    def spawn_entities(self):
        self.spawn_timer += 1
        self.difficulty_timer += 1

        # Difficulty progression
        asteroid_interval = max(35, 80 - (self.difficulty_timer // 300) * 5)
        speed_mult = 1.0 + min(1.2, self.difficulty_timer / 3600.0)

        # Spawn Stars
        if self.spawn_timer % 30 == 0:
            is_rainbow = random.random() < 0.15
            sx = random.randint(40, SCREEN_WIDTH - 40)
            self.stars.append(Star(sx, -20, is_rainbow=is_rainbow))

        # Spawn Asteroids
        if self.spawn_timer % asteroid_interval == 0:
            ax = random.randint(30, SCREEN_WIDTH - 30)
            self.asteroids.append(Asteroid(ax, -30, speed_mult=speed_mult))

        # Spawn Power-ups (occasional)
        if self.spawn_timer % 420 == 0 and random.random() < 0.8:
            px = random.randint(50, SCREEN_WIDTH - 50)
            self.powerups.append(PowerUp(px, -20))

    def update_game(self, keys):
        # Input states (works via M5Stick BLE keyboard arrow keys or physical keyboard)
        move_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        move_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        boost_up = keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]
        boost_down = keys[pygame.K_DOWN] or keys[pygame.K_s]

        # Update Player & Particles
        self.player.update(move_left, move_right, boost_up, boost_down, self.particles)

        # Update Starfield (faster when turbo boost active)
        turbo_mult = 2.4 if self.player.turbo_timer > 0 else 1.0
        self.starfield.update(turbo_mult)

        # Spawn objects
        self.spawn_entities()

        # Update and collect Stars
        magnet_active = (self.player.magnet_timer > 0)
        for s in self.stars[:]:
            s.update(self.player.x, self.player.y, magnet_active)
            
            # Catch star
            if self.player.rect.colliderect(s.rect):
                self.combo += 1
                self.max_combo = max(self.max_combo, self.combo)
                pts = s.points * min(5, 1 + (self.combo // 4))
                self.score += pts
                self.stars_caught += 1
                self.sound.play("star")
                
                # Floating score popup
                msg = f"+{pts}"
                if self.combo > 1 and self.combo % 3 == 0:
                    msg += f" ({self.combo}x COMBO!)"
                self.add_floating_text(s.x, s.y, msg, MAGENTA if s.is_rainbow else GOLD, size=22 if s.is_rainbow else 18)
                
                # Sparkle burst
                self.trigger_confetti(s.x, s.y, count=12 if s.is_rainbow else 8)
                self.stars.remove(s)
            elif s.y > SCREEN_HEIGHT + 30:
                self.stars.remove(s)
                # Reset combo if a star falls off screen
                if not s.is_rainbow:
                    self.combo = 0

        # Update Asteroids & check collisions
        for a in self.asteroids[:]:
            a.update()
            
            if self.player.rect.colliderect(a.rect):
                if self.player.hit():
                    # Shield absorbed hit
                    self.sound.play("shield")
                    self.trigger_confetti(a.x, a.y, count=15)
                    self.add_floating_text(a.x, a.y, "SHIELD BLOCKED!", CYAN, size=20)
                else:
                    # Took damage
                    self.lives -= 1
                    self.combo = 0
                    self.screen_shake = 18
                    self.sound.play("hit")
                    self.trigger_confetti(self.player.x, self.player.y, count=25)
                    self.add_floating_text(self.player.x, self.player.y - 20, "OUCH! ❤️-1", RED, size=24)

                    if self.lives <= 0:
                        self.state = self.STATE_GAMEOVER
                        self.high_score = max(self.high_score, self.score)
                        self.sound.play("gameover")
                        return

                self.asteroids.remove(a)
            elif a.y > SCREEN_HEIGHT + 40:
                self.asteroids.remove(a)

        # Update PowerUps
        for p in self.powerups[:]:
            p.update()
            if self.player.rect.colliderect(p.rect):
                self.player.activate_powerup(p.type)
                self.sound.play("powerup")
                self.trigger_confetti(p.x, p.y, count=20)
                
                name_map = {
                    PowerUp.TYPE_SHIELD: ("SHIELD ACTIVATED! 🛡️", CYAN),
                    PowerUp.TYPE_MAGNET: ("STAR MAGNET ON! 🧲", RED),
                    PowerUp.TYPE_TURBO: ("HYPER SPEED BOOST! ⚡", NEON_GREEN)
                }
                title, col = name_map[p.type]
                self.add_floating_text(p.x, p.y, title, col, size=22)
                self.powerups.remove(p)
            elif p.y > SCREEN_HEIGHT + 30:
                self.powerups.remove(p)

        # Update Particles
        for part in self.particles[:]:
            part.update()
            if part.is_dead():
                self.particles.remove(part)

        # Update Floating Texts
        for ft in self.floating_texts[:]:
            ft.update()
            if ft.life <= 0:
                self.floating_texts.remove(ft)

        # Smooth score animation
        if self.display_score < self.score:
            self.display_score += max(1, (self.score - self.display_score) // 6)

        # Screen shake dampening
        if self.screen_shake > 0:
            self.screen_shake -= 1

    def draw_hud(self, surface):
        # Top HUD Bar
        hud_bar = pygame.Surface((SCREEN_WIDTH, 44), pygame.SRCALPHA)
        hud_bar.fill((10, 15, 30, 210))
        surface.blit(hud_bar, (0, 0))

        # Score
        score_surf = self.hud_font.render(f"SCORE: {self.display_score:,}", True, GOLD)
        surface.blit(score_surf, (15, 10))

        # High Score
        hi_surf = self.sub_font.render(f"BEST: {self.high_score:,}", True, (180, 190, 210))
        surface.blit(hi_surf, (220, 14))

        # Hearts / Lives
        hearts_str = "❤️ " * self.lives
        lives_surf = self.hud_font.render(hearts_str, True, RED)
        surface.blit(lives_surf, (SCREEN_WIDTH - 15 - lives_surf.get_width(), 10))

        # Combo Streak Banner
        if self.combo >= 2:
            combo_color = YELLOW if self.combo < 6 else (CYAN if self.combo < 10 else MAGENTA)
            combo_surf = self.combo_font.render(f"{self.combo}x STREAK!", True, combo_color)
            surface.blit(combo_surf, (SCREEN_WIDTH // 2 - combo_surf.get_width() // 2, 48))

        # Active Power-up Status Bars (Bottom of screen)
        p_offset = 0
        if self.player.shield_timer > 0:
            self._draw_powerup_bar(surface, 15 + p_offset, "SHIELD 🛡️", self.player.shield_timer / 360.0, CYAN)
            p_offset += 160
        if self.player.magnet_timer > 0:
            self._draw_powerup_bar(surface, 15 + p_offset, "MAGNET 🧲", self.player.magnet_timer / 360.0, RED)
            p_offset += 160
        if self.player.turbo_timer > 0:
            self._draw_powerup_bar(surface, 15 + p_offset, "TURBO ⚡", self.player.turbo_timer / 360.0, NEON_GREEN)
            p_offset += 160

        # Bluetooth Controller Prompt Indicator (Bottom corner)
        bt_badge = self.sub_font.render("🎮 M5Stick BLE Active", True, (120, 200, 255))
        surface.blit(bt_badge, (SCREEN_WIDTH - bt_badge.get_width() - 15, SCREEN_HEIGHT - 28))

    def _draw_powerup_bar(self, surface, x, label, ratio, color):
        lbl = self.sub_font.render(label, True, color)
        surface.blit(lbl, (x, SCREEN_HEIGHT - 48))
        pygame.draw.rect(surface, (40, 50, 70), (x, SCREEN_HEIGHT - 26, 140, 10), border_radius=4)
        pygame.draw.rect(surface, color, (x, SCREEN_HEIGHT - 26, int(140 * max(0.0, ratio)), 10), border_radius=4)

    def draw_start_screen(self, surface):
        self.starfield.update(0.8)
        self.starfield.draw(surface)

        # Title Card
        title_surf = self.title_font.render("COSMIC STAR", True, GOLD)
        title_surf2 = self.title_font.render("CATCHER", True, CYAN)
        surface.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 140)))
        surface.blit(title_surf2, title_surf2.get_rect(center=(SCREEN_WIDTH // 2, 195)))

        # Cute Floating Ship Preview
        pulse_y = 290 + math.sin(pygame.time.get_ticks() * 0.005) * 12
        pygame.draw.polygon(surface, WHITE, [
            (SCREEN_WIDTH // 2, pulse_y - 28),
            (SCREEN_WIDTH // 2 - 18, pulse_y + 16),
            (SCREEN_WIDTH // 2 + 18, pulse_y + 16)
        ])
        pygame.draw.polygon(surface, RED, [
            (SCREEN_WIDTH // 2, pulse_y - 28),
            (SCREEN_WIDTH // 2 - 10, pulse_y - 6),
            (SCREEN_WIDTH // 2 + 10, pulse_y - 6)
        ])
        pygame.draw.circle(surface, CYAN, (SCREEN_WIDTH // 2, int(pulse_y)), 7)

        # Instructions Box
        box_rect = pygame.Rect(50, 360, SCREEN_WIDTH - 100, 240)
        pygame.draw.rect(surface, (20, 30, 55, 230), box_rect, border_radius=12)
        pygame.draw.rect(surface, (70, 110, 180), box_rect, 2, border_radius=12)

        instr = [
            ("🎮 HOW TO PLAY WITH M5STICK:", GOLD, True),
            ("1. Tilt Left / Right to Steer Ship", WHITE, False),
            ("2. Front M5 Button (A) = Boost / Jetpack", WHITE, False),
            ("3. Side Button (B) = Action / Power", WHITE, False),
            ("⭐ Collect Stars & Gems for Multipliers!", YELLOW, False),
            ("🪨 Dodge Asteroids | Grab Shields & Magnets", CYAN, False),
            ("💡 Or use Keyboard Arrow Keys / Space", (180, 200, 220), False)
        ]

        iy = 378
        for line, col, is_bold in instr:
            font = pygame.font.SysFont("arial", 17, bold=is_bold)
            ts = font.render(line, True, col)
            surface.blit(ts, (70, iy))
            iy += 29

        # Pulsing Start Prompt
        prompt_alpha = int(180 + 75 * math.sin(pygame.time.get_ticks() * 0.008))
        prompt_font = pygame.font.SysFont("impact", 26)
        prompt_surf = prompt_font.render("PRESS M5 BUTTON OR SPACE TO LAUNCH!", True, NEON_GREEN)
        prompt_surf.set_alpha(prompt_alpha)
        surface.blit(prompt_surf, prompt_surf.get_rect(center=(SCREEN_WIDTH // 2, 650)))

    def draw_gameover_screen(self, surface):
        self.starfield.draw(surface)

        # Dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 25, 220))
        surface.blit(overlay, (0, 0))

        # Game Over Title
        go_surf = self.title_font.render("MISSION COMPLETE!", True, GOLD)
        surface.blit(go_surf, go_surf.get_rect(center=(SCREEN_WIDTH // 2, 160)))

        # Stats Card
        box_rect = pygame.Rect(70, 230, SCREEN_WIDTH - 140, 280)
        pygame.draw.rect(surface, (25, 35, 60), box_rect, border_radius=12)
        pygame.draw.rect(surface, GOLD if self.score >= self.high_score and self.score > 0 else (70, 90, 130), box_rect, 3, border_radius=12)

        stats = [
            (f"FINAL SCORE: {self.score:,}", GOLD, 28),
            (f"HIGH SCORE: {self.high_score:,}", CYAN, 22),
            (f"⭐ Stars Caught: {self.stars_caught}", YELLOW, 20),
            (f"🔥 Best Streak: {self.max_combo}x", MAGENTA, 20),
        ]

        sy = 265
        for text, color, sz in stats:
            f = pygame.font.SysFont("impact", sz)
            st = f.render(text, True, color)
            surface.blit(st, st.get_rect(center=(SCREEN_WIDTH // 2, sy)))
            sy += 45

        # Restart Prompt
        prompt_font = pygame.font.SysFont("impact", 24)
        prompt_surf = prompt_font.render("PRESS M5 (A) OR SPACE TO PLAY AGAIN!", True, NEON_GREEN)
        surface.blit(prompt_surf, prompt_surf.get_rect(center=(SCREEN_WIDTH // 2, 570)))

    def run(self):
        running = True
        frame_count = 0

        while running:
            # Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q and (pygame.key.get_mods() & pygame.KMOD_META or pygame.key.get_mods() & pygame.KMOD_CTRL):
                        running = False
                    
                    # State transitions
                    if self.state == self.STATE_START:
                        if event.key in [pygame.K_SPACE, pygame.K_RETURN, pygame.K_UP]:
                            self.reset_game()
                            self.state = self.STATE_PLAY
                            self.sound.play("powerup")
                    elif self.state == self.STATE_PLAY:
                        if event.key in [pygame.K_p, pygame.K_ESCAPE]:
                            self.state = self.STATE_PAUSE
                    elif self.state == self.STATE_PAUSE:
                        if event.key in [pygame.K_p, pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN]:
                            self.state = self.STATE_PLAY
                    elif self.state == self.STATE_GAMEOVER:
                        if event.key in [pygame.K_SPACE, pygame.K_RETURN, pygame.K_UP]:
                            self.reset_game()
                            self.state = self.STATE_PLAY
                            self.sound.play("powerup")

            # Update & Render
            keys = pygame.key.get_pressed()

            # Apply screen shake offset if active
            shake_x = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
            shake_y = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0

            render_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            render_surf.fill((10, 14, 28))  # Deep space background

            if self.state == self.STATE_START:
                self.draw_start_screen(render_surf)
            elif self.state == self.STATE_PLAY:
                self.update_game(keys)
                self.starfield.draw(render_surf)
                
                # Draw entities
                for s in self.stars: s.draw(render_surf)
                for p in self.powerups: p.draw(render_surf)
                for a in self.asteroids: a.draw(render_surf)
                for part in self.particles: part.draw(render_surf)
                self.player.draw(render_surf)
                for ft in self.floating_texts: ft.draw(render_surf)
                
                self.draw_hud(render_surf)
            elif self.state == self.STATE_PAUSE:
                self.starfield.draw(render_surf)
                self.draw_hud(render_surf)
                # Pause overlay
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 160))
                render_surf.blit(overlay, (0, 0))
                p_txt = self.title_font.render("GAME PAUSED", True, WHITE)
                render_surf.blit(p_txt, p_txt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
            elif self.state == self.STATE_GAMEOVER:
                self.draw_gameover_screen(render_surf)

            # Blit rendered frame to display window
            self.screen.blit(render_surf, (shake_x, shake_y))
            pygame.display.flip()
            self.clock.tick(FPS)

            frame_count += 1
            if self.test_mode and frame_count >= 120:
                print("[Test Mode] 120 frames verified successfully!")
                break

        pygame.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cosmic Star Catcher")
    parser.add_argument("--test-mode", action="store_true", help="Run automated test for 120 frames and exit")
    args = parser.parse_args()

    game = CosmicStarCatcher(test_mode=args.test_mode)
    game.run()
