import pygame
import random
import sys
import os
from pygame.locals import *

# Initialize Pygame and mixer
pygame.init()
pygame.mixer.init()

# Screen settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flight Game Final Version")

# Color constants
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
SKY_BLUE = (135, 206, 235)

# Game constants
MAX_LEVEL = 10
SCORE_PER_LEVEL = 10000
BASE_ENEMY_SPEED = 3

# Button class
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.font = pygame.font.SysFont(None, 36)
    
    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=10)
        
        text_surf = self.font.render(self.text, True, BLACK)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
    
    def is_clicked(self, pos, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False


# Sound effects
def load_sound(filename):
    try: 
        return pygame.mixer.Sound(filename)
    except:
        print(f"Failed to load {filename}, using silent sound")
        return pygame.mixer.Sound(buffer=bytearray(100))  # Silent fallback

# Create assets directory if not exists
if not os.path.exists("assets/sounds"):
    os.makedirs("assets/sounds")

missile_sound = load_sound("assets/sounds/missile.mp3")
explosion_sound = load_sound("assets/sounds/explosion.wav")

# Animation loader with fallback
def load_animation(folder, default_size, default_color, scale=1.0, frame_count=3):
    frames = []
    try:
        if os.path.exists(folder):
            files = sorted([f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg'))])
            for file in files[:frame_count]:
                frame = pygame.image.load(os.path.join(folder, file)).convert_alpha()
                if scale != 1.0:
                    size = (int(frame.get_width() * scale), int(frame.get_height() * scale))
                    frame = pygame.transform.scale(frame, size)
                frames.append(frame)
    except Exception as e:
        print(f"Error loading {folder}: {e}")
    
    if not frames:
        for i in range(frame_count):
            surf = pygame.Surface(default_size, pygame.SRCALPHA)
            color = (
                min(default_color[0] + i*20, 255),
                min(default_color[1] + i*10, 255),
                min(default_color[2] + i*30, 255)
            )
            pygame.draw.rect(surf, color, (0, 0, *default_size))
            frames.append(surf)
    return frames

# Load all animations (with fallback)
player_frames = load_animation("assets/player", (50, 30), BLUE, 0.7)
enemy_frames = load_animation("assets/enemies", (50, 30), RED, 0.7)
missile_frames = load_animation("assets/missiles", (20, 10), YELLOW, 0.5)
explosion_frames = load_animation("assets/explosions", (60, 60), ORANGE, 1.0, 8)
background_frames = load_animation("assets/background", (SCREEN_WIDTH, SCREEN_HEIGHT), SKY_BLUE, 1.0, 1)

class Background:
    def __init__(self, frames):
        self.frames = frames
        self.current_frame = 0
        self.animation_speed = 0.05
        self.frame_counter = 0
    
    def update(self):
        self.frame_counter += 1
        if self.frame_counter >= self.animation_speed:
            self.frame_counter = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
    
    def draw(self, surface):
        surface.blit(self.frames[self.current_frame], (0, 0))

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.frames = player_frames
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(100, SCREEN_HEIGHT//2))
        self.anim_speed = 0.15
        self.frame_count = 0
        self.current_frame = 0
        self.speed = 5
        self.missile_cooldown = 0
    
    def update(self):
        self.frame_count += 1
        if self.frame_count >= self.anim_speed:
            self.frame_count = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]
        
        keys = pygame.key.get_pressed()
        if keys[K_UP]: self.rect.y = max(0, self.rect.y - self.speed)
        if keys[K_DOWN]: self.rect.y = min(SCREEN_HEIGHT-self.rect.height, self.rect.y + self.speed)
        if keys[K_LEFT]: self.rect.x = max(0, self.rect.x - self.speed)
        if keys[K_RIGHT]: self.rect.x = min(SCREEN_WIDTH-self.rect.width, self.rect.x + self.speed)
        
        if self.missile_cooldown > 0:
            self.missile_cooldown -= 1
    
    def fire_missile(self):
        if self.missile_cooldown == 0:
            self.missile_cooldown = 15
            missile_sound.play()
            return Missile(self.rect.right, self.rect.centery)
        return None

class Enemy(pygame.sprite.Sprite):
    def __init__(self, speed):
        x = SCREEN_WIDTH
        y = random.randint(50, SCREEN_HEIGHT-50)
        super().__init__()
        self.frames = enemy_frames
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(x, y))
        self.anim_speed = 0.2
        self.frame_count = 0
        self.current_frame = 0
        self.speed = speed
    def update(self):
        self.frame_count += 1
        if self.frame_count >= self.anim_speed:
            self.frame_count = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]
        
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()

class Missile(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.frames = missile_frames
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(x, y))
        self.anim_speed = 0.1
        self.frame_count = 0
        self.current_frame = 0
        self.speed = 10
    
    def update(self):
        self.frame_count += 1
        if self.frame_count >= self.anim_speed:
            self.frame_count = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]
        
        self.rect.x += self.speed
        if self.rect.left > SCREEN_WIDTH:
            self.kill()

class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.frames = explosion_frames
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(x, y))
        self.anim_speed = 0.5
        self.frame_count = 0
        self.current_frame = 0
        self.lifetime = len(explosion_frames) * 2
    
    def update(self):
        self.frame_count += 1
        if self.frame_count >= self.anim_speed:
            self.frame_count = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]
        
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()

class GameState:
    def __init__(self):
        self.score = 0
        self.level = 1
        self.enemy_speed = BASE_ENEMY_SPEED
    
    def add_score(self, points):
        self.score += points
        new_level = min(self.score // SCORE_PER_LEVEL + 1, MAX_LEVEL)
        if new_level > self.level:
            self.level = new_level
            self.enemy_speed = BASE_ENEMY_SPEED * (1.5 ** (self.level - 1))
    
    def get_enemy_speed(self):
        return self.enemy_speed


def game_loop():
    clock = pygame.time.Clock()
    background = Background(background_frames)
    game_state = GameState()
    player = Player()
    all_sprites = pygame.sprite.Group(player)
    enemies = pygame.sprite.Group()
    missiles = pygame.sprite.Group()
    explosions = pygame.sprite.Group()
    font = pygame.font.SysFont(None, 36)
    
    enemy_spawn_timer = 0
    running = True
    game_over = False
    
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            
            if game_over:
                if restart_button.is_clicked(mouse_pos, event):
                    return True  # Restart game
                if quit_button.is_clicked(mouse_pos, event):
                    pygame.quit()
                    sys.exit()
            else:
                #if event.type == KEYDOWN:
                #    if event.key == K_SPACE:
                #        if missile := player.fire_missile():
                #            missiles.add(missile)
                #            all_sprites.add(missile)
                # Handle both keyboard and mouse input
                if event.type == KEYDOWN:
                    if event.key == K_SPACE:
                        if missile := player.fire_missile():
                            missiles.add(missile)
                            all_sprites.add(missile)
                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button
                        mouse_clicked = True
                        if missile := player.fire_missile():
                            missiles.add(missile)
                            all_sprites.add(missile)
        
        if not game_over:
            # Game logic
            enemy_spawn_timer += 1
            if enemy_spawn_timer > 60 - (game_state.level * 2):
                enemy_spawn_timer = 0
                enemy = Enemy(game_state.get_enemy_speed())
                enemies.add(enemy)
                all_sprites.add(enemy)
            
            background.update()
            all_sprites.update()
            
            hits = pygame.sprite.groupcollide(enemies, missiles, True, True)
            for enemy in hits:
                explosion = Explosion(enemy.rect.centerx, enemy.rect.centery)
                explosions.add(explosion)
                all_sprites.add(explosion)
                explosion_sound.play()
                game_state.add_score(100)
            
            if pygame.sprite.spritecollide(player, enemies, False):
                game_over = True
            
            game_state.add_score(1)
        
        # Drawing
        background.draw(screen)
        all_sprites.draw(screen)
        
        # UI
        score_text = font.render(f"Score: {game_state.score}", True, WHITE)
        level_text = font.render(f"Level: {game_state.level}/{MAX_LEVEL}", True, WHITE)
        screen.blit(score_text, (10, 10))
        screen.blit(level_text, (10, 50))
        
        if game_over:
            # Game over overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            game_over_text = font.render("GAME OVER", True, RED)
            final_score_text = font.render(f"Final Score: {game_state.score}", True, WHITE)
            screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, 200))
            screen.blit(final_score_text, (SCREEN_WIDTH//2 - final_score_text.get_width()//2, 250))
            
            # Buttons
            restart_button.check_hover(mouse_pos)
            quit_button.check_hover(mouse_pos)
            restart_button.draw(screen)
            quit_button.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    return False  # Don't restart
# Create buttons
restart_button = Button(SCREEN_WIDTH//2 - 150, 350, 300, 50, "RESTART", GREEN, (100, 255, 100))
quit_button = Button(SCREEN_WIDTH//2 - 150, 420, 300, 50, "QUIT", RED, (255, 100, 100))

def main():
    # Initialize sound (same as before)
    # [Previous sound initialization code...]
    
    while True:
        should_restart = game_loop()
        if not should_restart:
            break

if __name__ == "__main__":
    main()
    pygame.quit()
    sys.exit()


'''
def main():
    clock = pygame.time.Clock()
    background = Background(background_frames)
    game_state = GameState()
    player = Player()
    all_sprites = pygame.sprite.Group(player)
    enemies = pygame.sprite.Group()
    missiles = pygame.sprite.Group()
    explosions = pygame.sprite.Group()
    font = pygame.font.SysFont(None, 36)
    
    enemy_spawn_timer = 0
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    if missile := player.fire_missile():
                        missiles.add(missile)
                        all_sprites.add(missile)
        
        enemy_spawn_timer += 1
        if enemy_spawn_timer > 60 - (game_state.level * 2):
            enemy_spawn_timer = 0
            enemy = Enemy(game_state.get_enemy_speed())
            enemies.add(enemy)
            all_sprites.add(enemy)
        
        background.update()
        all_sprites.update()
        
        hits = pygame.sprite.groupcollide(enemies, missiles, True, True)
        for enemy in hits:
            explosion = Explosion(enemy.rect.centerx, enemy.rect.centery)
            explosions.add(explosion)
            all_sprites.add(explosion)
            explosion_sound.play()
            game_state.add_score(100)
        
        if pygame.sprite.spritecollide(player, enemies, False):
            running = False
        
        game_state.add_score(1)
        
        background.draw(screen)
        all_sprites.draw(screen)
        
        score_text = font.render(f"Score: {game_state.score}", True, WHITE)
        level_text = font.render(f"Level: {game_state.level}/{MAX_LEVEL}", True, WHITE)
        speed_text = font.render(f"Speed: {game_state.enemy_speed:.1f}", True, WHITE)
        next_text = font.render(f"Next Level: {max(0, game_state.level * SCORE_PER_LEVEL - game_state.score)}", True, WHITE)
        
        screen.blit(score_text, (10, 10))
        screen.blit(level_text, (10, 50))
        screen.blit(speed_text, (10, 90))
        screen.blit(next_text, (10, 130))
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
    pygame.quit()
    sys.exit()
'''