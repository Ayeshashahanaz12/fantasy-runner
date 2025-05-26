import pygame
import random
import sys
import math

pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 900, 450
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fantasy Runner - Hackathon Edition")

# Clock and FPS
FPS = 60
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
SKY_BLUE_DAY = (135, 206, 235)
SKY_BLUE_NIGHT = (18, 18, 48)
GROUND_COLOR = (50, 50, 40)
TEXT_COLOR = (250, 240, 230)
GOLD = (255, 215, 0)
RED = (200, 30, 30)
GREEN = (35, 140, 35)

# Fonts
FONT_BIG = pygame.font.SysFont('Verdana', 48)
FONT_MED = pygame.font.SysFont('Verdana', 28)
FONT_SMALL = pygame.font.SysFont('Verdana', 20)

# Game constants
GRAVITY = 0.85
GROUND_Y = HEIGHT - 70
MAX_SPEED = 20

# Load sounds (optional, use placeholder if not found)
def load_sound(path):
    try:
        return pygame.mixer.Sound(path)
    except Exception:
        return None

SOUND_JUMP = load_sound("jump.wav")
SOUND_COIN = load_sound("coin.wav")
SOUND_GAMEOVER = load_sound("gameover.wav")

# Utility to draw text with shadow
def draw_text(surface, text, font, color, x, y, shadow_color=(0,0,0), shadow_offset=2):
    shadow = font.render(text, True, shadow_color)
    surface.blit(shadow, (x + shadow_offset, y + shadow_offset))
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, (x, y))

# Parallax Layer Class
class ParallaxLayer:
    def __init__(self, image, speed_factor, y_offset):
        self.image = image
        self.speed_factor = speed_factor
        self.y_offset = y_offset
        self.x = 0

    def update(self, game_speed):
        self.x -= game_speed * self.speed_factor
        if self.x <= -self.image.get_width():
            self.x = 0

    def draw(self, win):
        win.blit(self.image, (self.x, self.y_offset))
        win.blit(self.image, (self.x + self.image.get_width(), self.y_offset))

# Player Class with Animation
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.run_frames = []
        self.jump_frame = None
        self.load_images()

        self.index = 0
        self.image = self.run_frames[self.index]
        self.rect = self.image.get_rect(midbottom=(x, y))

        self.vel_y = 0
        self.is_jumping = False
        self.animation_speed = 0.15
        self.animation_timer = 0

    def load_images(self):
        # For demonstration, create animated rectangles with different shades
        for i in range(6):
            surf = pygame.Surface((50, 70), pygame.SRCALPHA)
            green_val = 50 + i*30
            pygame.draw.rect(surf, (30, green_val, 30), surf.get_rect(), border_radius=12)
            self.run_frames.append(surf)
        # Jump frame
        jump_surf = pygame.Surface((50, 70), pygame.SRCALPHA)
        pygame.draw.rect(jump_surf, (10, 100, 10), jump_surf.get_rect(), border_radius=12)
        self.jump_frame = jump_surf

    def update(self):
        self.apply_gravity()
        self.animate()

    def jump(self):
        if not self.is_jumping:
            self.vel_y = -18
            self.is_jumping = True
            if SOUND_JUMP:
                SOUND_JUMP.play()

    def apply_gravity(self):
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.is_jumping = False
            self.vel_y = 0

    def animate(self):
        if self.is_jumping:
            self.image = self.jump_frame
        else:
            self.animation_timer += self.animation_speed
            if self.animation_timer >= len(self.run_frames):
                self.animation_timer = 0
            self.index = int(self.animation_timer)
            self.image = self.run_frames[self.index]

# Coin Class with sparkle animation
class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.frames = []
        self.load_frames()
        self.index = 0
        self.image = self.frames[self.index]
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 0
        self.animation_speed = 0.25
        self.animation_timer = 0

    def load_frames(self):
        # Create a sparkle animation by drawing gold circles of varying brightness
        for i in range(6):
            surf = pygame.Surface((30, 30), pygame.SRCALPHA)
            alpha = 150 + i * 17
            pygame.draw.circle(surf, (255, 215, 0, alpha), (15, 15), 15)
            self.frames.append(surf)

    def update(self):
        self.rect.x -= self.speed
        self.animate()
        if self.rect.right < 0:
            self.kill()

    def animate(self):
        self.animation_timer += self.animation_speed
        if self.animation_timer >= len(self.frames):
            self.animation_timer = 0
        self.index = int(self.animation_timer)
        self.image = self.frames[self.index]

# Obstacle Class with simple animation
class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.frames = []
        self.load_frames()
        self.index = 0
        self.image = self.frames[self.index]
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.speed = 0
        self.animation_speed = 0.2
        self.animation_timer = 0

    def load_frames(self):
        # Simple pulsing red rectangles
        for i in range(5):
            surf = pygame.Surface((40, 60), pygame.SRCALPHA)
            red_val = 120 + i*25
            pygame.draw.rect(surf, (red_val, 20, 20), surf.get_rect(), border_radius=8)
            self.frames.append(surf)

    def update(self):
        self.rect.x -= self.speed
        self.animate()
        if self.rect.right < 0:
            self.kill()

    def animate(self):
        self.animation_timer += self.animation_speed
        if self.animation_timer >= len(self.frames):
            self.animation_timer = 0
        self.index = int(self.animation_timer)
        self.image = self.frames[self.index]

# Background with dynamic day-night cycle
class DynamicBackground:
    def __init__(self):
        self.time = 0  # Time cycles from 0 to 1 (day-night cycle)
        self.cycle_speed = 0.001  # Adjust for faster/slower cycle

        # Generate simple parallax layers (rectangles simulating mountains, trees, clouds)
        self.mountains = pygame.Surface((WIDTH, 150), pygame.SRCALPHA)
        self.mountains.fill((40, 40, 70))
        pygame.draw.polygon(self.mountains, (70, 70, 120), [(0,150),(100,30),(180,150)])
        pygame.draw.polygon(self.mountains, (60, 60, 110), [(150,150),(300,60),(400,150)])
        pygame.draw.polygon(self.mountains, (80, 80, 130), [(350,150),(500,40),(600,150)])
        pygame.draw.polygon(self.mountains, (70, 70, 120), [(580,150),(720,50),(800,150)])

        self.trees = pygame.Surface((WIDTH, 100), pygame.SRCALPHA)
        for i in range(0, WIDTH, 50):
            pygame.draw.polygon(self.trees, (15, 70, 20), [(i+25, 100), (i, 50), (i+50, 50)])

        self.clouds = pygame.Surface((WIDTH, 100), pygame.SRCALPHA)
        for i in range(0, WIDTH, 150):
            pygame.draw.ellipse(self.clouds, (255,255,255,180), (i, 30, 90, 50))

        self.ground = pygame.Surface((WIDTH, 70))
        self.ground.fill(GROUND_COLOR)

        self.offset_mountains = 0
        self.offset_trees = 0
        self.offset_clouds = 0

    def update(self, speed):
        self.time += self.cycle_speed
        if self.time > 1:
            self.time = 0

        # Move parallax layers at different speeds
        self.offset_mountains -= speed * 0.2
        if self.offset_mountains <= -WIDTH:
            self.offset_mountains = 0

        self.offset_trees -= speed * 0.6
        if self.offset_trees <= -WIDTH:
            self.offset_trees = 0

        self.offset_clouds -= speed * 0.8
        if self.offset_clouds <= -WIDTH:
            self.offset_clouds = 0

    def draw(self, win):
        # Calculate sky color for day-night cycle
        # Transition between day blue and night blue smoothly
        t = self.time
        sky_color = (
            int(SKY_BLUE_DAY[0] * (1 - t) + SKY_BLUE_NIGHT[0] * t),
            int(SKY_BLUE_DAY[1] * (1 - t) + SKY_BLUE_NIGHT[1] * t),
            int(SKY_BLUE_DAY[2] * (1 - t) + SKY_BLUE_NIGHT[2] * t)
        )
        win.fill(sky_color)

        # Draw clouds with slight transparency, fade with time (disappear at night)
        cloud_alpha = int(255 * (1 - abs(0.5 - t)*2))
        clouds = self.clouds.copy()
        clouds.set_alpha(cloud_alpha)
        win.blit(clouds, (self.offset_clouds, 40))
        win.blit(clouds, (self.offset_clouds + WIDTH, 40))

        # Draw mountains
        win.blit(self.mountains, (self.offset_mountains, GROUND_Y - 150))
        win.blit(self.mountains, (self.offset_mountains + WIDTH, GROUND_Y - 150))

        # Draw trees
        win.blit(self.trees, (self.offset_trees, GROUND_Y - 100))
        win.blit(self.trees, (self.offset_trees + WIDTH, GROUND_Y - 100))

        # Draw ground
        win.blit(self.ground, (0, GROUND_Y))

# Game class encapsulating the whole game logic
class FantasyRunnerGame:
    def __init__(self):
        self.player = Player(140, GROUND_Y)
        self.player_group = pygame.sprite.GroupSingle(self.player)

        self.coins = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()

        self.background = DynamicBackground()

        self.spawn_coin_timer = 0
        self.spawn_obstacle_timer = 0

        self.score_coins = 0
        self.score_distance = 0
        self.game_speed = 8.0

        self.state = 'start'  # 'start', 'playing', 'gameover'

    def spawn_coin(self):
        y = random.randint(GROUND_Y - 170, GROUND_Y - 80)
        coin = Coin(WIDTH + 30, y)
        coin.speed = self.game_speed
        self.coins.add(coin)

    def spawn_obstacle(self):
        obstacle = Obstacle(WIDTH + 40, GROUND_Y)
        obstacle.speed = self.game_speed
        self.obstacles.add(obstacle)

    def reset(self):
        self.coins.empty()
        self.obstacles.empty()
        self.player.rect.midbottom = (140, GROUND_Y)
        self.player.vel_y = 0
        self.player.is_jumping = False
        self.score_coins = 0
        self.score_distance = 0
        self.game_speed = 8.0
        self.spawn_coin_timer = 0
        self.spawn_obstacle_timer = 0
        self.state = 'playing'

    def update(self, dt):
        if self.state == 'playing':
            self.background.update(self.game_speed)

            self.player_group.update()

            # Spawn coins at intervals
            self.spawn_coin_timer += dt
            if self.spawn_coin_timer > 1300:
                self.spawn_coin()
                self.spawn_coin_timer = 0

            # Spawn obstacles at intervals
            self.spawn_obstacle_timer += dt
            if self.spawn_obstacle_timer > 1100:
                self.spawn_obstacle()
                self.spawn_obstacle_timer = 0

            # Update coins and obstacles speeds
            for coin in self.coins:
                coin.speed = self.game_speed
            for obstacle in self.obstacles:
                obstacle.speed = self.game_speed

            self.coins.update()
            self.obstacles.update()

            # Collect coins
            collected = pygame.sprite.spritecollide(self.player, self.coins, True)
            if collected:
                self.score_coins += len(collected)
                if SOUND_COIN:
                    SOUND_COIN.play()

            # Check collision with obstacles
            if pygame.sprite.spritecollide(self.player, self.obstacles, False):
                self.state = 'gameover'
                if SOUND_GAMEOVER:
                    SOUND_GAMEOVER.play()

            # Update distance and increase speed gradually
            self.score_distance += self.game_speed * dt / 1000
            self.game_speed = min(MAX_SPEED, self.game_speed + 0.002 * dt)

    def draw(self, win):
        self.background.draw(win)

        self.coins.draw(win)
        self.obstacles.draw(win)
        self.player_group.draw(win)

        # HUD - Display score
        draw_text(win, f"Coins: {self.score_coins}", FONT_MED, GOLD, 15, 15)
        draw_text(win, f"Distance: {int(self.score_distance)} m", FONT_MED, WHITE, 15, 50)
        draw_text(win, f"Speed: {self.game_speed:.1f}", FONT_MED, WHITE, 15, 85)

        if self.state == 'start':
            draw_text(win, "Press SPACE to Start", FONT_BIG, WHITE, WIDTH//2 - 230, HEIGHT//2 - 50)
        elif self.state == 'gameover':
            draw_text(win, "GAME OVER", FONT_BIG, RED, WIDTH//2 - 150, HEIGHT//2 - 80)
            draw_text(win, f"Coins Collected: {self.score_coins}", FONT_MED, GOLD, WIDTH//2 - 130, HEIGHT//2)
            draw_text(win, f"Distance Covered: {int(self.score_distance)} m", FONT_MED, WHITE, WIDTH//2 - 160, HEIGHT//2 + 40)
            draw_text(win, "Press R to Restart or Q to Quit", FONT_SMALL, WHITE, WIDTH//2 - 160, HEIGHT//2 + 100)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if self.state == 'start':
                if event.key == pygame.K_SPACE:
                    self.reset()
            elif self.state == 'playing':
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    self.player.jump()
            elif self.state == 'gameover':
                if event.key == pygame.K_r:
                    self.reset()
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

def main():
    game = FantasyRunnerGame()

    running = True
    while running:
        dt = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            game.handle_event(event)

        game.update(dt)
        game.draw(WIN)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
