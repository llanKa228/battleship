import pygame
import sys
import random


pygame.init()

# Настройки
CELL_SIZE = 40
GRID_SIZE = 10
WIDTH, HEIGHT = 900, 600
PLAYER_GRID_ORIGIN = (50, 100)
ENEMY_GRID_ORIGIN = (500, 100)
FPS = 60

# Цвета
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Экран
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Морской бой")
clock = pygame.time.Clock()

# Загрузка изображений
try:
    water_texture = pygame.image.load("water_texture.PNG")
    water_texture = pygame.transform.scale(water_texture, (CELL_SIZE * GRID_SIZE, CELL_SIZE * GRID_SIZE))
    hit_image = pygame.image.load("hit11.PNG")
    hit_image = pygame.transform.scale(hit_image, (CELL_SIZE, CELL_SIZE))
    splash_image = pygame.image.load("splash1.png")
    splash_image = pygame.transform.scale(splash_image, (CELL_SIZE, CELL_SIZE))
    # Загрузка фона для меню
    try:
        menu_background = pygame.image.load("fon.png")
        menu_background = pygame.transform.scale(menu_background, (WIDTH, HEIGHT))
    except:
        menu_background = pygame.Surface((WIDTH, HEIGHT))
        menu_background.fill(BLUE)
except:
    # Если изображения не загрузились, создаем заглушки
    water_texture = pygame.Surface((CELL_SIZE * GRID_SIZE, CELL_SIZE * GRID_SIZE))
    water_texture.fill(BLUE)
    hit_image = pygame.Surface((CELL_SIZE, CELL_SIZE))
    hit_image.fill(RED)
    splash_image = pygame.Surface((CELL_SIZE, CELL_SIZE))
    splash_image.fill(WHITE)
    menu_background = pygame.Surface((WIDTH, HEIGHT))
    menu_background.fill(BLUE)


def load_ship_image(filename, size):
    try:
        image = pygame.image.load(filename).convert_alpha()
        return pygame.transform.scale(image, size)
    except:
        # Заглушка если изображение не найдено
        surface = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(surface, GREEN, (0, 0, size[0], size[1]))
        return surface


ship_images = {
    1: load_ship_image("ship1.PNG", (CELL_SIZE, CELL_SIZE)),
    2: load_ship_image("ship2.PNG", (CELL_SIZE * 2, CELL_SIZE)),
    3: load_ship_image("ship3.PNG", (CELL_SIZE * 3, CELL_SIZE)),
    4: load_ship_image("ship4.png", (CELL_SIZE * 4, CELL_SIZE))
}


def get_initial_ship_positions():
    ships = []
    counts = {1: 4, 2: 3, 3: 2, 4: 1}
    x_start = PLAYER_GRID_ORIGIN[0] + CELL_SIZE * GRID_SIZE + 50
    y = 100
    for length in sorted(counts.keys()):
        for _ in range(counts[length]):
            ships.append({
                "length": length,
                "image": ship_images[length],
                "rect": pygame.Rect(x_start, y, CELL_SIZE * length, CELL_SIZE),
                "rotation": 0,
                "placed": False,
                "grid_pos": None,
                "hits": []
            })
            y += CELL_SIZE + 10
    return ships


def mark_ship_surroundings(ship):
    positions_to_mark = set()
    for (x, y) in ship["positions"]:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    positions_to_mark.add((nx, ny))

    # Исключаем сами позиции корабля
    positions_to_mark -= set(ship["positions"])

    # Добавляем только те позиции, которые еще не отмечены
    for pos in positions_to_mark:
        if pos not in player_hits and pos not in player_misses:
            player_misses.append(pos)


def mark_player_ship_surroundings(ship):
    positions_to_mark = set()
    for (x, y) in ship["positions"]:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    positions_to_mark.add((nx, ny))

    # Исключаем сами позиции корабля
    positions_to_mark -= set(ship["positions"])

    # Добавляем только те позиции, которые еще не отмечены
    for pos in positions_to_mark:
        if pos not in computer_hits and pos not in computer_misses:
            computer_misses.append(pos)


def initialize_game():
    global ships, enemy_ships, enemy_board, player_hits, player_misses, computer_hits, computer_misses
    global marked_sunk_ships, dragging_ship, mouse_offset, game_started, player_turn
    global computer_target_mode, computer_targets, computer_last_hit, computer_hit_direction
    global game_over, winner, in_menu

    ships = get_initial_ship_positions()
    enemy_ships = []
    enemy_board = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    player_hits = []
    player_misses = []
    computer_hits = []
    computer_misses = []

    marked_sunk_ships = set()

    dragging_ship = None
    mouse_offset = (0, 0)
    game_started = False
    player_turn = True
    game_over = False
    winner = None
    in_menu = True  # Добавляем флаг для меню

    computer_target_mode = False
    computer_targets = []
    computer_last_hit = None
    computer_hit_direction = None


def draw_grid(origin, label):
    screen.blit(water_texture, origin)
    for i in range(GRID_SIZE + 1):
        pygame.draw.line(screen, BLACK, (origin[0] + i * CELL_SIZE, origin[1]),
                         (origin[0] + i * CELL_SIZE, origin[1] + CELL_SIZE * GRID_SIZE))
        pygame.draw.line(screen, BLACK, (origin[0], origin[1] + i * CELL_SIZE),
                         (origin[0] + CELL_SIZE * GRID_SIZE, origin[1] + i * CELL_SIZE))

    font = pygame.font.SysFont(None, 24)
    for i in range(GRID_SIZE):
        letter = font.render(chr(ord('A') + i), True, BLACK)
        number = font.render(str(i + 1), True, BLACK)
        screen.blit(letter, (origin[0] + i * CELL_SIZE + CELL_SIZE // 3, origin[1] - 20))
        screen.blit(number, (origin[0] - 20, origin[1] + i * CELL_SIZE + CELL_SIZE // 4))

    title_font = pygame.font.SysFont(None, 32)
    label_surface = title_font.render(label, True, BLACK)
    screen.blit(label_surface, (origin[0] + CELL_SIZE * 3, origin[1] - 50))


def draw_ready_button():
    pygame.draw.rect(screen, GRAY, BUTTON_RECT)
    font = pygame.font.SysFont(None, 30)
    text = font.render("Готов", True, BLACK)
    screen.blit(text, (BUTTON_RECT.x + 40, BUTTON_RECT.y + 15))


def draw_menu():
    screen.blit(menu_background, (0, 0))

    # Рисуем заголовок
    title_font = pygame.font.SysFont(None, 72)
    title = title_font.render("Морской Бой", True, BLACK)

    title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 4))
    screen.blit(title, title_rect)

    # Рисуем кнопку "Начать"
    pygame.draw.rect(screen, GREEN, START_BUTTON_RECT)
    button_font = pygame.font.SysFont(None, 50)
    start_text = button_font.render("Начать", True, BLACK)
    text_rect = start_text.get_rect(center=START_BUTTON_RECT.center)
    screen.blit(start_text, text_rect)


def is_valid_placement(ships):
    board = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    for ship in ships:
        if not ship["placed"] or not ship["grid_pos"]:
            return False
        x, y = ship["grid_pos"]
        dx, dy = (1, 0) if ship["rotation"] == 0 else (0, 1)
        for i in range(ship["length"]):
            nx, ny = x + dx * i, y + dy * i
            if not (0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE):
                return False
            if board[ny][nx] == 1:
                return False
            for dy2 in [-1, 0, 1]:
                for dx2 in [-1, 0, 1]:
                    tx, ty = nx + dx2, ny + dy2
                    if 0 <= tx < GRID_SIZE and 0 <= ty < GRID_SIZE:
                        if board[ty][tx] == 1:
                            return False
        for i in range(ship["length"]):
            nx, ny = x + dx * i, y + dy * i
            board[ny][nx] = 1
    return True


def place_enemy_ships():
    enemy_ship_lengths = [4] + [3] * 2 + [2] * 3 + [1] * 4
    for length in enemy_ship_lengths:
        placed = False
        while not placed:
            rotation = random.choice([0, 90])
            dx, dy = (1, 0) if rotation == 0 else (0, 1)
            x = random.randint(0, GRID_SIZE - (length if dx else 1))
            y = random.randint(0, GRID_SIZE - (length if dy else 1))
            valid = True
            for i in range(length):
                nx, ny = x + dx * i, y + dy * i
                if enemy_board[ny][nx] != 0:
                    valid = False
                    break
                for dy2 in [-1, 0, 1]:
                    for dx2 in [-1, 0, 1]:
                        tx, ty = nx + dx2, ny + dy2
                        if 0 <= tx < GRID_SIZE and 0 <= ty < GRID_SIZE and enemy_board[ty][tx] != 0:
                            valid = False
            if valid:
                for i in range(length):
                    nx, ny = x + dx * i, y + dy * i
                    enemy_board[ny][nx] = 1
                enemy_ships.append({
                    "length": length,
                    "positions": [(x + dx * i, y + dy * i) for i in range(length)],
                    "hits": []
                })
                placed = True


def computer_turn():
    global player_turn, computer_target_mode, computer_targets, computer_last_hit, computer_hit_direction

    if computer_target_mode and computer_targets:
        # Продолжаем добивать корабль
        x, y = computer_targets.pop(0)
        if (x, y) not in computer_hits and (x, y) not in computer_misses:
            make_computer_move(x, y)
            return

    # Если не в режиме добивания или цели закончились, ищем новую цель
    if computer_last_hit and not computer_target_mode:
        # Пытаемся определить направление корабля
        x, y = computer_last_hit
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        possible_targets = []

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                if (nx, ny) not in computer_hits and (nx, ny) not in computer_misses:
                    possible_targets.append((nx, ny))

        if possible_targets:
            x, y = random.choice(possible_targets)
            make_computer_move(x, y)
            return

    # Если нет целей, стреляем случайно
    attempts = 0
    while attempts < 100:
        x = random.randint(0, GRID_SIZE - 1)
        y = random.randint(0, GRID_SIZE - 1)
        if (x, y) not in computer_hits and (x, y) not in computer_misses:
            make_computer_move(x, y)
            return
        attempts += 1

    # Если не удалось найти случайную клетку (маловероятно)
    player_turn = True


def make_computer_move(x, y):
    global player_turn, computer_target_mode, computer_targets, computer_last_hit, computer_hit_direction

    hit = False
    for ship in ships:
        if ship["placed"] and ship["grid_pos"]:
            sx, sy = ship["grid_pos"]
            dx, dy = (1, 0) if ship["rotation"] == 0 else (0, 1)
            for i in range(ship["length"]):
                if (sx + dx * i == x) and (sy + dy * i == y):
                    computer_hits.append((x, y))
                    if "positions" not in ship:
                        ship["positions"] = [(sx + dx * j, sy + dy * j) for j in range(ship["length"])]
                    ship["hits"].append((x, y))

                    # Входим в режим добивания
                    computer_target_mode = True
                    computer_last_hit = (x, y)

                    # Добавляем соседние клетки как цели
                    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                            if (nx, ny) not in computer_hits and (nx, ny) not in computer_misses:
                                computer_targets.append((nx, ny))

                    if len(ship["hits"]) == ship["length"]:
                        if id(ship) not in marked_sunk_ships:
                            mark_player_ship_surroundings(ship)
                            marked_sunk_ships.add(id(ship))
                        # Выходим из режима добивания
                        computer_target_mode = False
                        computer_targets = []
                        computer_last_hit = None

                    hit = True
                    break
            if hit:
                break

    if not hit:
        computer_misses.append((x, y))
        player_turn = True


def check_game_over():
    if not game_started:
        return None

    # Проверяем все ли корабли игрока уничтожены
    player_alive = any(
        len(ship.get("hits", [])) < ship["length"]
        for ship in ships
        if ship["placed"] and ship["grid_pos"]
    )

    # Проверяем все ли корабли противника уничтожены
    enemy_alive = any(
        len(ship["hits"]) < len(ship["positions"])
        for ship in enemy_ships
    )

    if not player_alive and not enemy_alive:
        return "draw"
    elif not player_alive:
        return "computer"
    elif not enemy_alive:
        return "player"
    else:
        return None


def draw_game_over_message(winner):
    # Полупрозрачный фон
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    font = pygame.font.SysFont(None, 72)
    if winner == "player":
        text = font.render("Вы победили!", True, GREEN)
    elif winner == "computer":
        text = font.render("Вы проиграли!", True, RED)
    else:
        text = font.render("Ничья!", True, WHITE)

    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
    screen.blit(text, text_rect)

    restart_font = pygame.font.SysFont(None, 36)
    restart_text = restart_font.render("Нажмите R для перезапуска", True, WHITE)
    restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
    screen.blit(restart_text, restart_rect)


# Инициализация игры
initialize_game()
BUTTON_RECT = pygame.Rect(700, 500, 150, 50)
START_BUTTON_RECT = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2, 200, 60)  # Кнопка "Начать" в меню

# Основной игровой цикл
running = True
while running:
    screen.fill(WHITE)

    if in_menu:
        draw_menu()
    elif not game_over:
        draw_grid(PLAYER_GRID_ORIGIN, "Игрок")
        if game_started:
            draw_grid(ENEMY_GRID_ORIGIN, "Враг")
        else:
            draw_ready_button()

        # Отрисовка кораблей игрока
        for ship in ships:
            if game_started and ship["placed"]:
                screen.blit(ship["image"], ship["rect"])
            elif not game_started:
                screen.blit(ship["image"], ship["rect"])

        # Промахи и попадания игрока
        for x, y in player_hits:
            screen.blit(hit_image, (ENEMY_GRID_ORIGIN[0] + x * CELL_SIZE, ENEMY_GRID_ORIGIN[1] + y * CELL_SIZE))
        for x, y in player_misses:
            screen.blit(splash_image, (ENEMY_GRID_ORIGIN[0] + x * CELL_SIZE, ENEMY_GRID_ORIGIN[1] + y * CELL_SIZE))

        # Промахи и попадания компьютера
        for x, y in computer_hits:
            screen.blit(hit_image, (PLAYER_GRID_ORIGIN[0] + x * CELL_SIZE, PLAYER_GRID_ORIGIN[1] + y * CELL_SIZE))
        for x, y in computer_misses:
            screen.blit(splash_image, (PLAYER_GRID_ORIGIN[0] + x * CELL_SIZE, PLAYER_GRID_ORIGIN[1] + y * CELL_SIZE))

        if game_started and not player_turn:
            computer_turn()

        # Проверка окончания игры
        if game_started:
            game_result = check_game_over()
            if game_result:
                game_over = True
                winner = game_result
                # Помечаем окружение всех оставшихся кораблей
                if winner == "player":
                    for ship in enemy_ships:
                        if len(ship["hits"]) < len(ship["positions"]):
                            mark_ship_surroundings(ship)
                elif winner == "computer":
                    for ship in ships:
                        if ship["placed"] and len(ship.get("hits", [])) < ship["length"]:
                            mark_player_ship_surroundings(ship)
    else:
        # Отрисовка завершенной игры
        draw_grid(PLAYER_GRID_ORIGIN, "Игрок")
        draw_grid(ENEMY_GRID_ORIGIN, "Враг")

        # Корабли
        for ship in ships:
            if ship["placed"]:
                screen.blit(ship["image"], ship["rect"])

        # Выстрелы
        for x, y in player_hits:
            screen.blit(hit_image, (ENEMY_GRID_ORIGIN[0] + x * CELL_SIZE, ENEMY_GRID_ORIGIN[1] + y * CELL_SIZE))
        for x, y in player_misses:
            screen.blit(splash_image, (ENEMY_GRID_ORIGIN[0] + x * CELL_SIZE, ENEMY_GRID_ORIGIN[1] + y * CELL_SIZE))
        for x, y in computer_hits:
            screen.blit(hit_image, (PLAYER_GRID_ORIGIN[0] + x * CELL_SIZE, PLAYER_GRID_ORIGIN[1] + y * CELL_SIZE))
        for x, y in computer_misses:
            screen.blit(splash_image, (PLAYER_GRID_ORIGIN[0] + x * CELL_SIZE, PLAYER_GRID_ORIGIN[1] + y * CELL_SIZE))

        draw_game_over_message(winner)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and game_over:
                initialize_game()
        elif event.type == pygame.MOUSEBUTTONDOWN and not game_over:
            if event.button == 1:
                if in_menu:
                    if START_BUTTON_RECT.collidepoint(event.pos):
                        in_menu = False
                elif BUTTON_RECT.collidepoint(event.pos) and not game_started:
                    if is_valid_placement(ships):
                        game_started = True
                        place_enemy_ships()
                        for ship in ships:
                            if ship["grid_pos"]:
                                gx, gy = ship["grid_pos"]
                                dx, dy = (1, 0) if ship["rotation"] == 0 else (0, 1)
                                ship["rect"].x = PLAYER_GRID_ORIGIN[0] + gx * CELL_SIZE
                                ship["rect"].y = PLAYER_GRID_ORIGIN[1] + gy * CELL_SIZE
                                ship["positions"] = [(gx + dx * i, gy + dy * i) for i in range(ship["length"])]
                    else:
                        print("Ошибка: неверная расстановка")
                        continue
                if not game_started and not in_menu:
                    for ship in reversed(ships):
                        if ship["rect"].collidepoint(event.pos):
                            dragging_ship = ship
                            mouse_offset = (event.pos[0] - ship["rect"].x, event.pos[1] - ship["rect"].y)
                            break
                if game_started and player_turn and not in_menu:
                    mx, my = event.pos
                    gx = (mx - ENEMY_GRID_ORIGIN[0]) // CELL_SIZE
                    gy = (my - ENEMY_GRID_ORIGIN[1]) // CELL_SIZE
                    if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
                        if (gx, gy) not in player_hits and (gx, gy) not in player_misses:
                            hit = False
                            for ship in enemy_ships:
                                if (gx, gy) in ship["positions"]:
                                    ship["hits"].append((gx, gy))
                                    player_hits.append((gx, gy))
                                    hit = True
                                    if len(ship["hits"]) == len(ship["positions"]):
                                        if id(ship) not in marked_sunk_ships:
                                            mark_ship_surroundings(ship)
                                            marked_sunk_ships.add(id(ship))
                                    break
                            if not hit:
                                player_misses.append((gx, gy))
                                player_turn = False
            elif event.button == 3 and not game_started and not game_over and not in_menu:
                for ship in ships:
                    if ship["rect"].collidepoint(event.pos):
                        ship["rotation"] = (ship["rotation"] + 90) % 180
                        w = CELL_SIZE * ship["length"] if ship["rotation"] == 0 else CELL_SIZE
                        h = CELL_SIZE if ship["rotation"] == 0 else CELL_SIZE * ship["length"]
                        ship["image"] = pygame.transform.rotate(ship_images[ship["length"]], ship["rotation"])
                        ship["rect"].width = w
                        ship["rect"].height = h
                        break
        elif event.type == pygame.MOUSEBUTTONUP and dragging_ship and not game_over and not in_menu:
            x, y = event.pos
            gx = (x - PLAYER_GRID_ORIGIN[0]) // CELL_SIZE
            gy = (y - PLAYER_GRID_ORIGIN[1]) // CELL_SIZE
            if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
                dragging_ship["rect"].x = PLAYER_GRID_ORIGIN[0] + gx * CELL_SIZE
                dragging_ship["rect"].y = PLAYER_GRID_ORIGIN[1] + gy * CELL_SIZE
                dragging_ship["grid_pos"] = (gx, gy)
                dragging_ship["placed"] = True
            dragging_ship = None
        elif event.type == pygame.MOUSEMOTION and dragging_ship and not game_started and not game_over and not in_menu:
            x, y = event.pos
            dragging_ship["rect"].x = x - mouse_offset[0]
            dragging_ship["rect"].y = y - mouse_offset[1]

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()