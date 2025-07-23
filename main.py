# -*- coding: utf-8 -*-
import pgzrun
import pygame # Class Rect

# --- Window Settings ---
WIDTH = 1300
HEIGHT = 700
TITLE = "Pixel Peak"
FULLSCREEN = False

# --- Game State Management ---
GAME_STATE_MAIN_MENU = 'main_menu'
GAME_STATE_IN_GAME = 'in_game'
GAME_STATE_WON = 'won'
GAME_STATE_GAME_OVER = 'game_over'
GAME_STATE_EXIT = 'exit'

current_game_state = GAME_STATE_MAIN_MENU

# --- Sound Variables ---
is_sound_on = True

# --- Menu Settings ---
SKY_BLUE = (135, 206, 235)
STEEL_BLUE = (70, 130, 180)
WHITE = (255, 255, 255)
BUTTON_RADIUS = 15

# --- Menu Buttons ---
start_button = pygame.Rect((WIDTH / 2 - 150, HEIGHT / 2 - 50), (300, 60))
sound_button = pygame.Rect((WIDTH / 2 - 150, HEIGHT / 2 + 30), (300, 60))
exit_button = pygame.Rect((WIDTH / 2 - 150, HEIGHT / 2 + 110), (300, 60))

# --- Helper Drawing Functions ---
def draw_rounded_rect(rect, color, radius):
    screen.draw.filled_rect(pygame.Rect(rect.left + radius, rect.top, rect.width - 2 * radius, rect.height), color)
    screen.draw.filled_rect(pygame.Rect(rect.left, rect.top + radius, rect.width, rect.height - 2 * radius), color)
    
    screen.draw.filled_circle((rect.left + radius, rect.top + radius), radius, color)
    screen.draw.filled_circle((rect.right - radius, rect.top + radius), radius, color)
    screen.draw.filled_circle((rect.left + radius, rect.bottom - radius), radius, color)
    screen.draw.filled_circle((rect.right - radius, rect.bottom - radius), radius, color)

# --- Game Variables and Classes ---

# Colors
BACKGROUND_COLOR = (173, 216, 230)
DEBUG_MISSING_IMAGE_COLOR_PLATFORM = (255, 0, 0)
DEBUG_MISSING_IMAGE_COLOR_PLAYER = (0, 0, 255)
DEBUG_MISSING_IMAGE_COLOR_ENEMY = (255, 255, 0)
DEBUG_MISSING_IMAGE_COLOR_FLAG = (0, 255, 0)

# Image Asset Definitions
GROUND_TILE_NAME = 'ground'
FLOATING_TILE_PREFIX = 'platform'
TRAMPOLINE_IDLE_NAME = 'spring'
TRAMPOLINE_ACTIVE_NAME = 'spring_out'
TRAMPOLINE_JUMP_BOOST = -800
TRAMPOLINE_ANIMATION_DURATION = 0.2

# Y position of the ground top
GROUND_TOP_Y = HEIGHT - 50

# Dictionary to store pre-loaded images
_images_loaded = {}

def get_image_asset(image_name):
    if image_name not in _images_loaded:
        try:
            _images_loaded[image_name] = pygame.image.load(f"images/{image_name}.png").convert_alpha()
        except FileNotFoundError:
            _images_loaded[image_name] = None
        except Exception:
            _images_loaded[image_name] = None
    return _images_loaded[image_name]

# --- Actor Classes (Player, Enemy, Flag) ---
class Player(Actor):
    def __init__(self):
        try:
            super().__init__('player_idle_0')
            self.image_loaded_successfully = True
        except Exception:
            super().__init__('blank')
            self.width = 60
            self.height = 80
            self.image_loaded_successfully = False

        self.midbottom = (WIDTH - 100, GROUND_TOP_Y)
        self.vx = 0
        self.vy = 0
        self.speed = 300
        self.jump_power = -570
        self.gravity = 800
        self.on_ground = True

        self.current_animation_state = "idle"
        self.facing_direction = "right"

        self.idle_frames = ["player_idle_0", "player_idle_1"]
        self.walk_right_frame = "player_right"
        self.walk_left_frame = "player_left"
        self.jump_frame = "player_jump"

        self.current_frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 0.5

    def update(self, dt):
        global current_game_state

        if current_game_state not in [GAME_STATE_IN_GAME]:
            return

        self.animation_timer += dt

        self.vx = 0
        is_moving_horizontally = False

        if keyboard.left or keyboard.a:
            self.vx = -self.speed
            self.facing_direction = "left"
            is_moving_horizontally = True
        elif keyboard.right or keyboard.d:
            self.vx = self.speed
            self.facing_direction = "right"
            is_moving_horizontally = True

        if not self.on_ground:
            self.vy += self.gravity * dt
            if self.vy > 500:
                self.vy = 500

        if keyboard.space and self.on_ground:
            self.vy = self.jump_power
            self.on_ground = False
            self.current_animation_state = "jumping"

        if not self.on_ground:
            if self.vy < 0:
                self.current_animation_state = "jumping"
            elif self.vy > 0:
                self.current_animation_state = "falling"
        elif is_moving_horizontally:
            self.current_animation_state = "walking"
        elif self.on_ground and not is_moving_horizontally:
            self.current_animation_state = "idle"

        self.x += self.vx * dt
        for platform_data in PLATFORMS:
            platform_rect = platform_data['rect']
            if self.colliderect(platform_rect):
                if self.vx > 0:
                    self.right = platform_rect.left
                elif self.vx < 0:
                    self.left = platform_rect.right

        if self.left < 0:
            self.left = 0
            self.vx = 0
        if self.right > WIDTH:
            self.right = WIDTH
            self.vx = 0

        self.y += self.vy * dt
        was_on_ground_this_frame = False

        for platform_data in PLATFORMS:
            platform_rect = platform_data['rect']
            if self.colliderect(platform_rect):
                if self.vy >= 0: 
                    self.bottom = platform_rect.top
                    self.vy = 0
                    was_on_ground_this_frame = True

                    if platform_data['type'] == 'trampoline':
                        self.vy = TRAMPOLINE_JUMP_BOOST
                        self.on_ground = False
                        self.current_animation_state = "jumping"
                        platform_data['animation_timer'] = TRAMPOLINE_ANIMATION_DURATION

                    if self.current_animation_state in ["jumping", "falling"]:
                        if is_moving_horizontally:
                            self.current_animation_state = "walking"
                        else:
                            self.current_animation_state = "idle"

                elif self.vy < 0:
                    self.top = platform_rect.bottom
                    self.vy = 0
                    self.current_animation_state = "falling"

        # --- Enemy Collision Logic ---
        for enemy in ENEMIES:
            if not enemy.is_squashed and self.colliderect(enemy):
                if self.vy >= 0 and self.bottom <= enemy.top + (enemy.height / 3):
                    enemy.squash()
                    self.vy = self.jump_power / 2
                    self.on_ground = False
                else:
                    current_game_state = GAME_STATE_GAME_OVER
                    if is_sound_on:
                        sounds.game_over_sound.play()
                    return

        # --- Flag Collision Logic ---
        global flag
        if flag and not flag.collected and self.colliderect(flag):
            flag.collect()
            current_game_state = GAME_STATE_WON
            if is_sound_on:
                music.stop()
                sounds.win_sound.play()
            return

        self.on_ground = was_on_ground_this_frame

        if self.top > HEIGHT: 
            current_game_state = GAME_STATE_GAME_OVER
            if is_sound_on:
                music.stop()
                sounds.game_over_sound.play()
            return

        # Player Animation Logic
        if self.image_loaded_successfully:
            if self.current_animation_state == "idle":
                frames_to_use = self.idle_frames
                if self.animation_timer >= self.animation_speed:
                    self.animation_timer = 0
                    self.current_frame_index = (self.current_frame_index + 1) % len(frames_to_use)
                    self.image = frames_to_use[self.current_frame_index]
                elif self.image not in self.idle_frames:
                    self.image = frames_to_use[self.current_frame_index]
            elif self.current_animation_state == "walking":
                if self.facing_direction == "right":
                    self.image = self.walk_right_frame
                else:
                    self.image = self.walk_left_frame
                if self.image not in [self.walk_right_frame, self.walk_left_frame]:
                    self.current_frame_index = 0
                    self.animation_timer = 0
            elif self.current_animation_state in ["jumping", "falling"]:
                self.image = self.jump_frame
                if self.image != self.jump_frame:
                    self.current_frame_index = 0
                    self.animation_timer = 0


class Enemy(Actor):
    def __init__(self, start_pos, movement_range, platform_rect=None):
        try:
            super().__init__('enemy_walk_right_0')
            self.image_loaded_successfully = True
        except Exception:
            super().__init__('blank')
            self.width = 60
            self.height = 60
            self.image_loaded_successfully = False

        self.midbottom = start_pos
        self.speed = 100
        self.vx = self.speed
        self.movement_start = movement_range[0]
        self.movement_end = movement_range[1]
        self.platform_rect = platform_rect

        self.walk_right_frames = ["enemy_walk_right_0", "enemy_walk_right_1"]
        self.walk_left_frames = ["enemy_walk_left_0", "enemy_walk_left_1"]
        self.squashed_frame = "enemy_squashed"

        self.current_frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 0.4

        self.is_squashed = False
        self.squashed_timer = 0.0
        self.SQUASH_DURATION = 0.5

    def update(self, dt):
        global current_game_state

        if current_game_state not in [GAME_STATE_IN_GAME]:
            return

        if self.is_squashed:
            self.squashed_timer -= dt
            if self.squashed_timer <= 0:
                if self in ENEMIES:
                    ENEMIES.remove(self)
            return

        self.animation_timer += dt

        self.x += self.vx * dt

        if self.platform_rect:
            if self.vx < 0 and self.left <= self.platform_rect.left:
                self.left = self.platform_rect.left
                self.vx = self.speed
            elif self.vx > 0 and self.right >= self.platform_rect.right:
                self.right = self.platform_rect.right
                self.vx = -self.speed
        else:
            if (self.vx < 0 and self.left <= self.movement_start) or \
               (self.vx > 0 and self.right >= self.movement_end):
                self.vx *= -1

        if self.image_loaded_successfully and not self.is_squashed:
            frames_to_use = []
            if self.vx > 0:
                frames_to_use = self.walk_right_frames
            elif self.vx < 0:
                frames_to_use = self.walk_left_frames

            if frames_to_use:
                if self.animation_timer >= self.animation_speed:
                    self.animation_timer = 0
                    self.current_frame_index = (self.current_frame_index + 1) % len(frames_to_use)
                    self.image = frames_to_use[self.current_frame_index]
                elif self.image not in frames_to_use:
                    self.image = frames_to_use[self.current_frame_index]

        self.on_ground = False
        for platform_data in PLATFORMS:
            platform_rect = platform_data['rect']
            if self.colliderect(platform_rect) and \
               self.bottom <= platform_rect.top + 5 and \
               self.bottom >= platform_rect.top - 5:
                self.bottom = platform_rect.top
                self.on_ground = True
                break
        
        if not self.on_ground:
            self.y += 150 * dt
            if self.top > HEIGHT:
                self.is_squashed = True
                self.squashed_timer = 0

    def squash(self):
        self.is_squashed = True
        self.image = self.squashed_frame
        self.squashed_timer = self.SQUASH_DURATION
        if is_sound_on:
            sounds.squash_sound.play()


class Flag(Actor):
    def __init__(self, pos):
        try:
            super().__init__('flag_0')
            self.image_loaded_successfully = True
        except Exception:
            super().__init__('blank')
            self.width = 80
            self.height = 80
            self.image_loaded_successfully = False
        
        self.pos = pos
        self.collected = False

        self.flag_frames = ["flag_0", "flag_1"]
        self.current_frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 0.3

    def update(self, dt):
        if not self.collected and self.image_loaded_successfully:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.current_frame_index = (self.current_frame_index + 1) % len(self.flag_frames)
                self.image = self.flag_frames[self.current_frame_index]

    def collect(self):
        self.collected = True

# --- Global Game Instances ---
player = None
ENEMIES = []
PLATFORMS = []
flag = None

def initialize_game_elements():
    global player, ENEMIES, PLATFORMS, flag

    # Redefine platforms to ensure trampoline state is reset
    PLATFORMS = [
        {'rect': pygame.Rect(0, GROUND_TOP_Y, WIDTH, 50), 'type': 'ground'},
        {'rect': pygame.Rect(150, HEIGHT - 380, 256, 50), 'type': 'floating'},
        {'rect': pygame.Rect(WIDTH - 256 - 110, HEIGHT - 290, 256, 50), 'type': 'floating'},
        {'rect': pygame.Rect(WIDTH // 2 - 192, HEIGHT - 560, 384, 50), 'type': 'floating'},
        {'rect': pygame.Rect(30, GROUND_TOP_Y - 50, 60, 50), 'type': 'trampoline', 'animation_timer': 0.0}
    ]

    player = Player()

    ENEMIES = [
        Enemy(
            start_pos=(200, GROUND_TOP_Y),
            movement_range=(100, WIDTH - 100)
        ),
        Enemy(
            start_pos=(PLATFORMS[1]['rect'].x + PLATFORMS[1]['rect'].width // 2, PLATFORMS[1]['rect'].top),
            movement_range=(PLATFORMS[1]['rect'].left, PLATFORMS[1]['rect'].right),
            platform_rect=PLATFORMS[1]['rect']
        ),
        Enemy(
            start_pos=(PLATFORMS[3]['rect'].x + PLATFORMS[3]['rect'].width // 2, PLATFORMS[3]['rect'].top),
            movement_range=(PLATFORMS[3]['rect'].left, PLATFORMS[3]['rect'].right),
            platform_rect=PLATFORMS[3]['rect']
        )
    ]

    flag_platform = PLATFORMS[2]['rect']
    flag = Flag((flag_platform.centerx, flag_platform.top - 30))

# --- Main PgZero Functions ---

def draw():
    if current_game_state == GAME_STATE_MAIN_MENU:
        screen.fill(SKY_BLUE)
        screen.draw.text("Pixel Peak", center=(WIDTH / 2, 150), fontsize=70, color=STEEL_BLUE, owidth=1.5, ocolor=WHITE)

        draw_rounded_rect(start_button, STEEL_BLUE, BUTTON_RADIUS)
        screen.draw.text("Jogar", center=start_button.center, fontsize=35, color=WHITE)

        draw_rounded_rect(sound_button, STEEL_BLUE, BUTTON_RADIUS)
        sound_text = "Músicas e sons: ON" if is_sound_on else "Músicas e sons: OFF"
        screen.draw.text(sound_text, center=sound_button.center, fontsize=35, color=WHITE)

        draw_rounded_rect(exit_button, STEEL_BLUE, BUTTON_RADIUS)
        screen.draw.text("Sair", center=exit_button.center, fontsize=35, color=WHITE)

    elif current_game_state in [GAME_STATE_IN_GAME, GAME_STATE_WON, GAME_STATE_GAME_OVER]:
        screen.fill(BACKGROUND_COLOR)

        # Draw Platforms
        for platform_data in PLATFORMS:
            platform_rect = platform_data['rect']
            platform_type = platform_data['type']

            if platform_type == 'ground':
                ground_image = get_image_asset(GROUND_TILE_NAME)
                if ground_image is None:
                    screen.draw.filled_rect(platform_rect, DEBUG_MISSING_IMAGE_COLOR_PLATFORM)
                    continue

                tile_width = ground_image.get_width()
                scaled_ground_image = ground_image
                if ground_image.get_height() != platform_rect.height:
                    scaled_ground_image = pygame.transform.scale(ground_image, (tile_width, platform_rect.height))

                for x_offset in range(0, platform_rect.width, tile_width):
                    screen.blit(scaled_ground_image, (platform_rect.x + x_offset, platform_rect.y))

            elif platform_type == 'floating':
                left_edge_name = f"{FLOATING_TILE_PREFIX}_left"
                middle_name = f"{FLOATING_TILE_PREFIX}_middle"
                right_edge_name = f"{FLOATING_TILE_PREFIX}_right"

                img_left_edge = get_image_asset(left_edge_name)
                img_middle = get_image_asset(middle_name)
                img_right_edge = get_image_asset(right_edge_name)

                if img_middle is None:
                    screen.draw.filled_rect(platform_rect, DEBUG_MISSING_IMAGE_COLOR_PLATFORM)
                    continue

                original_tile_width = img_middle.get_width()
                original_tile_height = img_middle.get_height()
                target_tile_height = platform_rect.height

                scaled_img_left_edge = img_left_edge
                scaled_img_middle = img_middle
                scaled_img_right_edge = img_right_edge

                if original_tile_height != target_tile_height:
                    if img_left_edge: scaled_img_left_edge = pygame.transform.scale(img_left_edge, (original_tile_width, target_tile_height))
                    if img_middle: scaled_img_middle = pygame.transform.scale(img_middle, (original_tile_width, target_tile_height))
                    if img_right_edge: scaled_img_right_edge = pygame.transform.scale(img_right_edge, (original_tile_width, target_tile_height))

                if scaled_img_left_edge:
                    screen.blit(scaled_img_left_edge, (platform_rect.x, platform_rect.y))
                else:
                    screen.draw.filled_rect(pygame.Rect(platform_rect.x, platform_rect.y, original_tile_width, target_tile_height), DEBUG_MISSING_IMAGE_COLOR_PLATFORM)

                middle_tiles_width = platform_rect.width - (2 * original_tile_width)
                if middle_tiles_width > 0:
                    for x_offset in range(original_tile_width, platform_rect.width - original_tile_width, original_tile_width):
                        if scaled_img_middle:
                            screen.blit(scaled_img_middle, (platform_rect.x + x_offset, platform_rect.y))

                if scaled_img_right_edge:
                    screen.blit(scaled_img_right_edge, (platform_rect.x + platform_rect.width - original_tile_width, platform_rect.y))
                else:
                    screen.draw.filled_rect(pygame.Rect(platform_rect.x + platform_rect.y, original_tile_width, target_tile_height), DEBUG_MISSING_IMAGE_COLOR_PLATFORM)

            elif platform_type == 'trampoline':
                current_trampoline_image_name = TRAMPOLINE_IDLE_NAME
                if platform_data['animation_timer'] > 0:
                    current_trampoline_image_name = TRAMPOLINE_ACTIVE_NAME
                trampoline_image = get_image_asset(current_trampoline_image_name)

                if trampoline_image is None:
                    screen.draw.filled_rect(platform_rect, DEBUG_MISSING_IMAGE_COLOR_PLATFORM)
                else:
                    scaled_trampoline_image = pygame.transform.scale(trampoline_image, (platform_rect.width, platform_rect.height))
                    screen.blit(scaled_trampoline_image, platform_rect.topleft)

        # Draw Flag
        if flag and not flag.collected:
            if flag.image_loaded_successfully:
                flag.draw()
            else:
                screen.draw.filled_rect(flag.rect, DEBUG_MISSING_IMAGE_COLOR_FLAG)

        # Draw Enemies
        for enemy in ENEMIES:
            if not enemy.is_squashed or enemy.squashed_timer > 0:
                if enemy.image_loaded_successfully:
                    enemy.draw()
                else:
                    screen.draw.filled_rect(enemy.rect, DEBUG_MISSING_IMAGE_COLOR_ENEMY)

        # Draw Player
        if player:
            if player.image_loaded_successfully:
                player.draw()
            else:
                screen.draw.filled_rect(player.rect, DEBUG_MISSING_IMAGE_COLOR_PLAYER)

        # Draw final game state messages (won/lost)
        if current_game_state == GAME_STATE_WON:
            screen.draw.text("VOCÊ VENCEU!", center=(WIDTH // 2, HEIGHT // 2), color="green", fontsize=100)
            screen.draw.text("Aperte 'R' para voltar ao MENU ou 'ESC' para fechar o jogo", center=(WIDTH // 2, HEIGHT // 2 + 80), color="white", fontsize=30)
        elif current_game_state == GAME_STATE_GAME_OVER:
            screen.draw.text("FIM DE JOGO!", center=(WIDTH // 2, HEIGHT // 2), color="red", fontsize=100)
            screen.draw.text("Aperte 'R' para voltar ao MENU ou 'ESC' para fechar o jogo", center=(WIDTH // 2, HEIGHT // 2 + 80), color="white", fontsize=30)

    elif current_game_state == GAME_STATE_EXIT:
        pass


def update(dt):
    global current_game_state, is_sound_on

    if current_game_state == GAME_STATE_MAIN_MENU:
        pass
    elif current_game_state == GAME_STATE_IN_GAME:
        if player:
            player.update(dt)

        if flag and not flag.collected:
            flag.update(dt)

        for enemy in list(ENEMIES):
            enemy.update(dt)

        for platform_data in PLATFORMS:
            if platform_data['type'] == 'trampoline':
                if platform_data['animation_timer'] > 0:
                    platform_data['animation_timer'] -= dt
                    if platform_data['animation_timer'] < 0:
                        platform_data['animation_timer'] = 0
    elif current_game_state in [GAME_STATE_WON, GAME_STATE_GAME_OVER]:
        pass
    elif current_game_state == GAME_STATE_EXIT:
        exit()


def on_mouse_down(pos):
    global current_game_state, is_sound_on

    if current_game_state == GAME_STATE_MAIN_MENU:
        if start_button.collidepoint(pos):
            current_game_state = GAME_STATE_IN_GAME
            initialize_game_elements()
            if is_sound_on:
                music.stop()
                music.play("game_music")
        elif sound_button.collidepoint(pos):
            is_sound_on = not is_sound_on
            if is_sound_on:
                music.set_volume(1)
                if current_game_state == GAME_STATE_MAIN_MENU:
                    music.play("menu_music")
                elif current_game_state == GAME_STATE_IN_GAME and not music.is_playing("game_music"):
                     music.play("game_music")
            else:
                music.set_volume(0)
        elif exit_button.collidepoint(pos):
            current_game_state = GAME_STATE_EXIT

def on_key_down(key):
    global current_game_state

    if current_game_state in [GAME_STATE_WON, GAME_STATE_GAME_OVER]:
        if key == keys.R:
            current_game_state = GAME_STATE_MAIN_MENU
            if is_sound_on:
                music.stop()
                music.play("menu_music")
        elif key == keys.ESCAPE:
            current_game_state = GAME_STATE_EXIT
    elif current_game_state == GAME_STATE_IN_GAME:
        if key == keys.ESCAPE:
             current_game_state = GAME_STATE_MAIN_MENU
             if is_sound_on:
                music.stop()
                music.play("menu_music")
            
# --- Initialization ---
if is_sound_on:
    music.play("menu_music")

pgzrun.go()