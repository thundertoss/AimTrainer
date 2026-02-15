import pygame
import random
import math
import json
import os

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 60
CONFIG_FILE = "aim_trainer_config.json"

# Default configuration
DEFAULT_CONFIG = {
    "target_radius": 30,
    "middle_radius": 15,
    "bullseye_radius": 5,
    "num_targets": 4,
    "game_duration": 120,
    "special_target_duration": 2,
    "outer_points": 5,
    "middle_points": 10,
    "bullseye_points": 20,
    "special_outer_points": 25,
    "special_middle_points": 40,
    "special_bullseye_points": 60,
    "miss_penalty": -1,
    "high_scores": []
}


# Load or create config file
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Ensure all default keys exist
            for key in DEFAULT_CONFIG:
                if key not in config:
                    config[key] = DEFAULT_CONFIG[key]
            return config
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()


def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)


# Load configuration
config = load_config()

# Extract settings from config
TARGET_RADIUS = config["target_radius"]
MIDDLE_RADIUS = config.get("middle_radius", 15)
BULLSEYE_RADIUS = config["bullseye_radius"]
NUM_TARGETS = config["num_targets"]
GAME_DURATION = config["game_duration"]
SPECIAL_TARGET_DURATION = config["special_target_duration"]

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (100, 100, 100)
CYAN = (0, 255, 255)
BLUE = (0, 100, 255)
PURPLE = (255, 0, 255)
GREEN = (0, 255, 0)

# Set up display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Aim Trainer")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)
input_font = pygame.font.Font(None, 48)


class Target:
    def __init__(self, is_special=False):
        self.x = random.randint(TARGET_RADIUS + 10, WIDTH - TARGET_RADIUS - 10)
        self.y = random.randint(TARGET_RADIUS + 10, HEIGHT - TARGET_RADIUS - 10)
        self.is_special = is_special

    def draw(self):
        if self.is_special:
            # Draw special target (cyan/blue/purple)
            pygame.draw.circle(screen, CYAN, (self.x, self.y), TARGET_RADIUS)
            pygame.draw.circle(screen, BLUE, (self.x, self.y), MIDDLE_RADIUS)
            pygame.draw.circle(screen, PURPLE, (self.x, self.y), BULLSEYE_RADIUS)
        else:
            # Draw regular target (white/yellow/red)
            pygame.draw.circle(screen, WHITE, (self.x, self.y), TARGET_RADIUS)
            pygame.draw.circle(screen, YELLOW, (self.x, self.y), MIDDLE_RADIUS)
            pygame.draw.circle(screen, RED, (self.x, self.y), BULLSEYE_RADIUS)

    def is_hit(self, mouse_pos):
        """Check if click is within target, return points earned"""
        dist = math.sqrt((mouse_pos[0] - self.x) ** 2 + (mouse_pos[1] - self.y) ** 2)
        if self.is_special:
            if dist <= BULLSEYE_RADIUS:
                return config["special_bullseye_points"]
            elif dist <= MIDDLE_RADIUS:
                return config["special_middle_points"]
            elif dist <= TARGET_RADIUS:
                return config["special_outer_points"]
        else:
            if dist <= BULLSEYE_RADIUS:
                return config["bullseye_points"]
            elif dist <= MIDDLE_RADIUS:
                return config["middle_points"]
            elif dist <= TARGET_RADIUS:
                return config["outer_points"]
        return 0

    def relocate(self):
        """Move target to new random position"""
        self.x = random.randint(TARGET_RADIUS + 10, WIDTH - TARGET_RADIUS - 10)
        self.y = random.randint(TARGET_RADIUS + 10, HEIGHT - TARGET_RADIUS - 10)


def is_high_score(score):
    """Check if score qualifies for top 10"""
    high_scores = config["high_scores"]
    if len(high_scores) < 10:
        return True
    return score > min(hs["score"] for hs in high_scores)


def add_high_score(name, score):
    """Add a new high score and save to config"""
    config["high_scores"].append({"name": name, "score": score})
    config["high_scores"].sort(key=lambda x: x["score"], reverse=True)
    config["high_scores"] = config["high_scores"][:10]  # Keep only top 10
    save_config(config)


def draw_text_centered(text, font, color, y):
    """Draw text centered horizontally at given y position"""
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(WIDTH // 2, y))
    screen.blit(text_surface, text_rect)


# Game variables
targets = [Target() for _ in range(NUM_TARGETS)]
score = 0
running = True
game_over = False
entering_name = False
player_name = ""

# Timer variables
start_time = pygame.time.get_ticks()
elapsed_time = 0

# Special target variables
special_target = None
special_target_spawn_time = None
special_targets_spawned = 0
special_spawn_times = sorted(random.sample(range(10, GAME_DURATION - 10), 2))

# Game loop
while running:
    clock.tick(FPS)

    # Update timer
    if not game_over:
        current_time = pygame.time.get_ticks()
        elapsed_time = (current_time - start_time) / 1000
        remaining_time = max(0, GAME_DURATION - elapsed_time)

        # Check if game is over
        if remaining_time <= 0:
            game_over = True
            if is_high_score(score):
                entering_name = True

        # Special target spawning logic
        if special_targets_spawned < 2 and elapsed_time >= special_spawn_times[special_targets_spawned]:
            if special_target is None:
                special_target = Target(is_special=True)
                special_target_spawn_time = current_time
                special_targets_spawned += 1

        # Remove special target after duration
        if special_target is not None:
            if (current_time - special_target_spawn_time) / 1000 >= SPECIAL_TARGET_DURATION:
                special_target = None
                special_target_spawn_time = None

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if entering_name:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and player_name.strip():
                    add_high_score(player_name.strip(), score)
                    entering_name = False
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                elif event.unicode.isprintable() and len(player_name) < 15:
                    player_name += event.unicode
        elif event.type == pygame.MOUSEBUTTONDOWN and not game_over:
            mouse_pos = pygame.mouse.get_pos()
            hit_something = False

            # Check special target first
            if special_target is not None:
                points = special_target.is_hit(mouse_pos)
                if points > 0:
                    score += points
                    special_target = None
                    special_target_spawn_time = None
                    hit_something = True
                    continue

            # Check each regular target for hits
            if not hit_something:
                for target in targets:
                    points = target.is_hit(mouse_pos)
                    if points > 0:
                        score += points
                        target.relocate()
                        hit_something = True
                        break

            # Apply penalty for missing
            if not hit_something:
                score += config["miss_penalty"]

        # Restart game on game over screen
        if game_over and not entering_name and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # Reset game
                targets = [Target() for _ in range(NUM_TARGETS)]
                score = 0
                game_over = False
                entering_name = False
                player_name = ""
                start_time = pygame.time.get_ticks()
                elapsed_time = 0
                special_target = None
                special_target_spawn_time = None
                special_targets_spawned = 0
                special_spawn_times = sorted(random.sample(range(10, GAME_DURATION - 10), 2))

    # Draw everything
    screen.fill(GRAY)

    if entering_name:
        # Name entry screen
        draw_text_centered("NEW HIGH SCORE!", font, GREEN, HEIGHT // 2 - 100)
        draw_text_centered(f"Score: {score}", font, WHITE, HEIGHT // 2 - 50)
        draw_text_centered("Enter your name:", font, WHITE, HEIGHT // 2)

        # Draw input box
        input_box = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 40, 300, 50)
        pygame.draw.rect(screen, WHITE, input_box, 2)
        name_surface = input_font.render(player_name, True, WHITE)
        screen.blit(name_surface, (input_box.x + 10, input_box.y + 5))

        draw_text_centered("Press ENTER to submit", small_font, WHITE, HEIGHT // 2 + 120)

    elif game_over:
        # Game over screen
        draw_text_centered("GAME OVER!", font, BLACK, HEIGHT // 2 - 80)
        draw_text_centered(f"Final Score: {score}", font, BLACK, HEIGHT // 2 - 30)

        # Display high scores
        draw_text_centered("HIGH SCORES", small_font, BLACK, HEIGHT // 2 + 20)
        y_offset = HEIGHT // 2 + 50
        for i, hs in enumerate(config["high_scores"][:5], 1):
            score_text = f"{i}. {hs['name']}: {hs['score']}"
            draw_text_centered(score_text, small_font, BLACK, y_offset)
            y_offset += 25

        # Show restart instruction
        draw_text_centered("Press SPACE to play again", small_font, GREEN, HEIGHT - 50)
    else:
        # Draw all regular targets
        for target in targets:
            target.draw()

        # Draw special target if active
        if special_target is not None:
            special_target.draw()

        # Draw timer (centered at top)
        minutes = int(remaining_time // 60)
        seconds = int(remaining_time % 60)
        timer_text = font.render(f"Time: {minutes}:{seconds:02d}", True, BLACK)
        timer_rect = timer_text.get_rect(center=(WIDTH // 2, 25))
        screen.blit(timer_text, timer_rect)

        # Draw score (top right)
        score_text = font.render(f"Score: {score}", True, BLACK)
        score_rect = score_text.get_rect(topright=(WIDTH - 10, 10))
        screen.blit(score_text, score_rect)

        # Draw crosshair at mouse position
        mouse_x, mouse_y = pygame.mouse.get_pos()
        pygame.draw.line(screen, BLACK, (mouse_x - 10, mouse_y), (mouse_x + 10, mouse_y), 2)
        pygame.draw.line(screen, BLACK, (mouse_x, mouse_y - 10), (mouse_x, mouse_y + 10), 2)

    pygame.display.flip()

pygame.quit()