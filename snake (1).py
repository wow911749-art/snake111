import pygame
import random
import sys
import math
import time

pygame.init()

# ── Настройки ──────────────────────────────────────────────────────────────
W, H       = 700, 700
COLS, ROWS = 25, 25
CELL       = W // COLS          # 28px
PANEL      = 60                 # верхняя панель

FPS = 60

# ── Цвета ──────────────────────────────────────────────────────────────────
BG          = (10,  12,  20)
GRID_COLOR  = (20,  25,  40)
SNAKE_HEAD  = (100, 240, 180)
SNAKE_BODY  = (40,  180, 120)
SNAKE_OUT   = (20,  120,  80)
FOOD_COLOR  = (230,  60,  80)
FOOD_GLOW   = (255, 100, 100)
PANEL_BG    = (14,  18,  32)
TEXT_MAIN   = (220, 220, 220)
TEXT_DIM    = (80,  90, 120)
ACCENT      = (100, 240, 180)
DANGER      = (230,  60,  80)
STAR_COLOR  = (255, 255, 255)

# ── Шрифты ─────────────────────────────────────────────────────────────────
font_big   = pygame.font.SysFont("consolas", 36, bold=True)
font_med   = pygame.font.SysFont("consolas", 22, bold=True)
font_small = pygame.font.SysFont("consolas", 16)

# ── Окно ───────────────────────────────────────────────────────────────────
screen = pygame.display.set_mode((W, H + PANEL))
pygame.display.set_caption("🐍  SNAKE")
clock  = pygame.time.Clock()


# ── Звёзды на фоне ─────────────────────────────────────────────────────────
class Star:
    def __init__(self):
        self.reset(random.randint(0, H + PANEL))

    def reset(self, y=None):
        self.x   = random.randint(0, W)
        self.y   = y if y is not None else 0
        self.r   = random.uniform(0.5, 2.0)
        self.spd = random.uniform(0.05, 0.25)
        self.alp = random.randint(60, 200)

    def update(self):
        self.y += self.spd
        if self.y > H + PANEL:
            self.reset()

    def draw(self, surf):
        color = (self.alp, self.alp, self.alp)
        pygame.draw.circle(surf, color, (int(self.x), int(self.y)), max(1, int(self.r)))

stars = [Star() for _ in range(120)]


# ── Частицы при поедании еды ────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(2, 6)
        self.x   = x
        self.y   = y
        self.vx  = math.cos(angle) * speed
        self.vy  = math.sin(angle) * speed
        self.life= 1.0
        self.r   = random.randint(3, 7)
        hue_var  = random.choice([FOOD_COLOR, FOOD_GLOW, ACCENT])
        self.col = hue_var

    def update(self):
        self.x   += self.vx
        self.y   += self.vy
        self.vy  += 0.15
        self.life -= 0.04
        self.r    = max(1, self.r - 0.15)

    def draw(self, surf):
        if self.life > 0:
            alpha = max(0, int(self.life * 255))
            c = tuple(min(255, v) for v in self.col)
            pygame.draw.circle(surf, c, (int(self.x), int(self.y)), int(self.r))

particles = []


# ── Рисование скруглённого прямоугольника ──────────────────────────────────
def draw_rounded(surf, color, rect, radius=6, border_color=None, border_w=2):
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border_color:
        pygame.draw.rect(surf, border_color, rect, border_w, border_radius=radius)


# ── Фоновая сетка ──────────────────────────────────────────────────────────
def draw_grid():
    for x in range(0, W, CELL):
        pygame.draw.line(screen, GRID_COLOR, (x, PANEL), (x, PANEL + H))
    for y in range(PANEL, PANEL + H + 1, CELL):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (W, y))


# ── Панель информации ──────────────────────────────────────────────────────
def draw_panel(score, best, level, paused):
    pygame.draw.rect(screen, PANEL_BG, (0, 0, W, PANEL))
    pygame.draw.line(screen, GRID_COLOR, (0, PANEL), (W, PANEL), 2)

    # Очки
    lbl  = font_small.render("ОЧКИ", True, TEXT_DIM)
    val  = font_med.render(str(score), True, ACCENT)
    screen.blit(lbl, (24, 8))
    screen.blit(val, (24, 26))

    # Рекорд
    lbl2 = font_small.render("РЕКОРД", True, TEXT_DIM)
    val2 = font_med.render(str(best), True, TEXT_MAIN)
    screen.blit(lbl2, (180, 8))
    screen.blit(val2, (180, 26))

    # Уровень
    lbl3 = font_small.render("УРОВЕНЬ", True, TEXT_DIM)
    val3 = font_med.render(str(level), True, TEXT_MAIN)
    screen.blit(lbl3, (340, 8))
    screen.blit(val3, (340, 26))

    # Управление
    hint = font_small.render("ПАУЗА: P  |  ВЫХОД: ESC", True, TEXT_DIM)
    screen.blit(hint, (W - hint.get_width() - 20, 22))

    if paused:
        p = font_med.render("[ ПАУЗА ]", True, DANGER)
        screen.blit(p, (W // 2 - p.get_width() // 2, 18))


# ── Сегмент змейки ──────────────────────────────────────────────────────────
def draw_snake(snake):
    for i, (cx, cy) in enumerate(snake):
        x = cx * CELL
        y = cy * CELL + PANEL
        rect = pygame.Rect(x + 2, y + 2, CELL - 4, CELL - 4)
        if i == 0:
            draw_rounded(screen, SNAKE_HEAD, rect, radius=8, border_color=ACCENT, border_w=2)
            # Глаза
            dir_next = (snake[1][0] - cx, snake[1][1] - cy) if len(snake) > 1 else (0, 0)
            eye_off = {(1,0): [(CELL-10,6),(CELL-10,CELL-10)],
                       (-1,0): [(4,6),(4,CELL-10)],
                       (0,1): [(6,CELL-10),(CELL-10,CELL-10)],
                       (0,-1): [(6,4),(CELL-10,4)]}.get((-dir_next[0],-dir_next[1]), [(6,6),(CELL-10,6)])
            for ex, ey in eye_off:
                pygame.draw.circle(screen, BG, (x + ex, y + ey), 3)
                pygame.draw.circle(screen, TEXT_MAIN, (x + ex, y + ey), 1)
        else:
            t = i / len(snake)
            r = int(SNAKE_BODY[0] * (1 - t * 0.5))
            g = int(SNAKE_BODY[1] * (1 - t * 0.4))
            b = int(SNAKE_BODY[2] * (1 - t * 0.2))
            draw_rounded(screen, (r, g, b), rect, radius=6, border_color=SNAKE_OUT, border_w=1)


# ── Еда с пульсирующим свечением ────────────────────────────────────────────
def draw_food(fx, fy, tick):
    pulse = math.sin(tick * 0.1) * 0.3 + 0.7
    x = fx * CELL + PANEL // 2
    y = fy * CELL + PANEL

    # Свечение
    glow_r = int((CELL // 2 + 6) * pulse)
    glow_surf = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4), pygame.SRCALPHA)
    pygame.draw.circle(glow_surf, (*FOOD_GLOW, 40), (glow_r + 2, glow_r + 2), glow_r)
    screen.blit(glow_surf, (x - glow_r - 2, y - glow_r + CELL // 2 - 2))

    # Сам кружок
    r_food = int((CELL // 2 - 4) * pulse + 3)
    pygame.draw.circle(screen, FOOD_COLOR, (x + CELL // 2, y + CELL // 2), r_food)
    pygame.draw.circle(screen, FOOD_GLOW,  (x + CELL // 2 - 2, y + CELL // 2 - 2), max(1, r_food // 3))


# ── Экран старта / game over ─────────────────────────────────────────────────
def draw_overlay(title, subtitle, score=None, best=None):
    overlay = pygame.Surface((W, H + PANEL), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))

    t1 = font_big.render(title, True, ACCENT)
    screen.blit(t1, (W // 2 - t1.get_width() // 2, H // 2 - 60 + PANEL // 2))

    t2 = font_med.render(subtitle, True, TEXT_DIM)
    screen.blit(t2, (W // 2 - t2.get_width() // 2, H // 2 + PANEL // 2))

    if score is not None:
        s = font_med.render(f"Очки: {score}   Рекорд: {best}", True, TEXT_MAIN)
        screen.blit(s, (W // 2 - s.get_width() // 2, H // 2 + 40 + PANEL // 2))


# ── Основной игровой цикл ────────────────────────────────────────────────────
def main():
    global particles

    # Начальное состояние
    def new_game():
        snake  = [(12, 12), (11, 12), (10, 12)]
        dir_   = (1, 0)
        food   = place_food(snake)
        return snake, dir_, food, 0

    def place_food(snake):
        while True:
            fx = random.randint(0, COLS - 1)
            fy = random.randint(0, ROWS - 1)
            if (fx, fy) not in snake:
                return (fx, fy)

    snake, direction, food, score = new_game()
    best     = 0
    level    = 1
    tick     = 0
    move_acc = 0.0
    interval = 150       # мс между шагами
    next_dir = direction
    running  = False     # ждём старта
    paused   = False
    game_over= False
    particles= []

    while True:
        dt = clock.tick(FPS)

        # ── Events ──────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

                # Старт / рестарт
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if not running or game_over:
                        snake, direction, food, score = new_game()
                        next_dir  = direction
                        level     = 1
                        interval  = 150
                        particles = []
                        running   = True
                        game_over = False
                        paused    = False
                        move_acc  = 0

                # Пауза
                if event.key == pygame.K_p and running and not game_over:
                    paused = not paused

                # Направление
                if running and not paused and not game_over:
                    if event.key in (pygame.K_UP,    pygame.K_w) and direction != (0,  1): next_dir = (0, -1)
                    if event.key in (pygame.K_DOWN,  pygame.K_s) and direction != (0, -1): next_dir = (0,  1)
                    if event.key in (pygame.K_LEFT,  pygame.K_a) and direction != (1,  0): next_dir = (-1, 0)
                    if event.key in (pygame.K_RIGHT, pygame.K_d) and direction != (-1, 0): next_dir = (1,  0)

        # ── Логика ──────────────────────────────────────────────────────────
        if running and not paused and not game_over:
            move_acc += dt
            if move_acc >= interval:
                move_acc = 0
                direction = next_dir
                hx = (snake[0][0] + direction[0]) % COLS
                hy = (snake[0][1] + direction[1]) % ROWS

                # Столкновение с собой
                if (hx, hy) in snake[1:]:
                    game_over = True
                    if score > best:
                        best = score
                else:
                    snake.insert(0, (hx, hy))
                    if (hx, hy) == food:
                        score += 1
                        if score > best:
                            best = score
                        # Частицы
                        px = food[0] * CELL + CELL // 2
                        py = food[1] * CELL + PANEL + CELL // 2
                        for _ in range(18):
                            particles.append(Particle(px, py))
                        food = place_food(snake)
                        # Уровень
                        level = score // 5 + 1
                        interval = max(60, 150 - (level - 1) * 12)
                    else:
                        snake.pop()

        # ── Рисование ───────────────────────────────────────────────────────
        screen.fill(BG)

        for s in stars:
            s.update()
            s.draw(screen)

        draw_grid()
        draw_food(food[0], food[1], tick)
        draw_snake(snake)

        # Частицы
        for p in particles[:]:
            p.update()
            p.draw(screen)
            if p.life <= 0:
                particles.remove(p)

        draw_panel(score, best, level, paused)

        if not running:
            draw_overlay("🐍  SNAKE", "Нажми ENTER или ПРОБЕЛ чтобы начать")
        elif game_over:
            draw_overlay("ИГРА ОКОНЧЕНА", "Нажми ENTER чтобы сыграть снова", score, best)

        pygame.display.flip()
        tick += 1


if __name__ == "__main__":
    main()
