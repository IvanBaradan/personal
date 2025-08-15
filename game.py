import requests
import time
from cat import Cat

WIDTH = 640
HEIGHT = 480
TILE = 32
HALF = TILE // 2
TITLE = "Игра с Котиками"
SERVER_URL = "http://localhost:5000"

cats = {}  
coin_position = None
last_update = 0
update_interval = 0.04  

def draw():
    draw_background()

    if coin_position:
        screen.draw.filled_circle(
            (coin_position['x'] * TILE + HALF, coin_position['y'] * TILE + HALF),
            HALF // 2,
            (255, 215, 0)  
        )

    for cat in cats.values():
        cat.draw(screen)

    draw_ui()

def update():
    global last_update

    current_time = time.time()
    if current_time - last_update > update_interval:
        update_game_state()
        last_update = current_time
    
    for cat in cats.values():
        cat.update()

def draw_background():
    color_a = (170, 210, 255) 
    color_b = (150, 195, 245) 
    for gy in range(0, HEIGHT, TILE):
        for gx in range(0, WIDTH, TILE):
            use_a = ((gx // TILE) + (gy // TILE)) % 2 == 0
            c = color_a if use_a else color_b
            screen.draw.filled_rect(Rect((gx, gy), (TILE, TILE)), c)

def draw_ui():
    player_count = len(cats)
    screen.draw.text(
        f"Игроков онлайн: {player_count}",
        (10, 10),
        color='white',
        fontsize=18
    )

def update_game_state():

    global cats, coin_position
    
    try:
        response = requests.get(f"{SERVER_URL}/api/game_state", timeout=0.2)
        if response.status_code == 200:
            data = response.json()

            coin_position = data.get('coin')

            current_players = data.get('players', [])
            current_usernames = set()
            
            for player_data in current_players:
                username = player_data['username']
                x = player_data['x']
                y = player_data['y']
                current_usernames.add(username)
                if username not in cats:
                    cats[username] = Cat(username, x, y)
                else:
                    cats[username].update_position(x, y)
            cats_to_remove = []
            for username in cats:
                if username not in current_usernames:
                    cats_to_remove.append(username)
            
            for username in cats_to_remove:
                del cats[username]
                
    except requests.exceptions.RequestException:
        pass

def on_key_down(key):
    if key == keys.R:
        update_game_state()
    elif key == keys.ESCAPE:
        quit()

print("Окно игры запущено")

if __name__ == "__main__":
    import pgzrun
    pgzrun.go()
