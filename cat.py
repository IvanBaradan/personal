from pgzero.actor import Actor
from pgzero import loaders

loaders.images = loaders.ImageLoader('sprites')

class Cat:
    def __init__(self, username, x, y, sprites_dir="sprites"):

        self.username = username
        self.grid_x = x
        self.grid_y = y

    
        self.tile_size = 32  
        self.target_x = x * self.tile_size
        self.target_y = y * self.tile_size

        self.current_x = self.target_x
        self.current_y = self.target_y

        self.move_speed = 4  

        self.animation_frame = 0
        self.animation_speed = 0.3  
        self.animation_counter = 0

    
        self.direction = 'down'  
        self.is_moving = False

        self.sprites = {
            'wait_down': [Actor("wait_down/0")],
            'wait_up': [Actor("wait_up/0")],
            'wait_left': [Actor("wait_left/0")],
            'wait_right': [Actor("wait_right/0")],
            'walk_down': [
                Actor("walk_down/0"),
                Actor("walk_down/1"),
                Actor("walk_down/2"),
                Actor("walk_down/3"),
            ],
            'walk_up': [
                Actor("walk_up/0"),
                Actor("walk_up/1"),
                Actor("walk_up/2"),
                Actor("walk_up/3"),
            ],
            'walk_left': [
                Actor("walk_left/0"),
                Actor("walk_left/1"),
                Actor("walk_left/2"),
                Actor("walk_left/3"),
            ],
            'walk_right': [
                Actor("walk_right/0"),
                Actor("walk_right/1"),
                Actor("walk_right/2"),
                Actor("walk_right/3"),
            ],
        }

        self.current_sprite = self.sprites['wait_down'][0]
        self.current_sprite.pos = (self.current_x + 16, self.current_y + 16)
    
    def update_position(self, new_grid_x, new_grid_y):
        if new_grid_x != self.grid_x or new_grid_y != self.grid_y:
            self.grid_x = new_grid_x
            self.grid_y = new_grid_y
            self.target_x = new_grid_x * self.tile_size
            self.target_y = new_grid_y * self.tile_size
            self.is_moving = True
    
    def update(self):
        if self.is_moving:
            dx = self.target_x - self.current_x
            dy = self.target_y - self.current_y
            if abs(dx) > abs(dy):
                if dx > 0:
                    self.direction = 'right'
                else:
                    self.direction = 'left'
            else:
                if dy > 0:
                    self.direction = 'down'
                else:
                    self.direction = 'up'
            if abs(dx) > self.move_speed:
                self.current_x += self.move_speed if dx > 0 else -self.move_speed
            else:
                self.current_x = self.target_x
            
            if abs(dy) > self.move_speed:
                self.current_y += self.move_speed if dy > 0 else -self.move_speed
            else:
                self.current_y = self.target_y

            if abs(self.current_x - self.target_x) < self.move_speed and abs(self.current_y - self.target_y) < self.move_speed:
                self.current_x = self.target_x
                self.current_y = self.target_y
                self.is_moving = False
                self.animation_frame = 0
        self.animation_counter += self.animation_speed
        if self.animation_counter >= 1:
            self.animation_counter = 0
            if self.is_moving:
                self.animation_frame = (self.animation_frame + 1) % 4
            else:
                self.animation_frame = 0
        if not self.is_moving:
            self.animation_frame = 0
        if self.is_moving:
            sprite_key = f'walk_{self.direction}'
        else:
            sprite_key = f'wait_{self.direction}'

        self.current_sprite = self.sprites[sprite_key][self.animation_frame]
        self.current_sprite.pos = (self.current_x + 16, self.current_y + 16)
    
    def draw(self, screen):

        self.current_sprite.draw()

        screen.draw.text(
            self.username,
            (self.current_x + 16, self.current_y - 10),
            color='white',
            fontsize=12,
            anchor=(0.5, 0.5)
        )
