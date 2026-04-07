import pygame
import math
import random

pygame.init()

WIDTH, HEIGHT = 1280, 800
win = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Solar System Simulation")

WHITE  = (255, 255, 255)
YELLOW = (255, 220, 50)
BLUE   = (100, 149, 237)
RED    = (188, 60, 50)
GREY   = (180, 180, 180)
ORANGE = (230, 180, 80)
BROWN  = (200, 160, 110)
TAN    = (210, 190, 130)
BLACK  = (5, 5, 20)

FONT_SM = pygame.font.SysFont("consolas", 12)
FONT_MD = pygame.font.SysFont("consolas", 14)
FONT_LG = pygame.font.SysFont("consolas", 18)

AU       = 1.496e11
G        = 6.67428e-11
TIMESTEP = 3600 * 24   # 1 day


# ── Background stars ────────────────────────────────────────────────────────
class Star:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x          = random.randint(0, WIDTH)
        self.y          = random.randint(0, HEIGHT)
        self.brightness = random.randint(60, 210)
        self.size       = random.choice([1, 1, 1, 2])
        self.twinkle    = random.uniform(0.02, 0.08)
        self.phase      = random.uniform(0, math.pi * 2)

    def draw(self, win, t):
        b = int(self.brightness + math.sin(t * self.twinkle + self.phase) * 30)
        b = max(0, min(255, b))
        pygame.draw.circle(win, (b, b, b), (self.x, self.y), self.size)


# ── Asteroid (lightweight, no name/label) ───────────────────────────────────
class Asteroid:
    def __init__(self, x, y, vx, vy):
        self.x  = x;  self.y  = y
        self.vx = vx; self.vy = vy
        self.mass = 1e15
        self.trail = []

    def update(self, sun_mass, sun_x, sun_y):
        dx = sun_x - self.x
        dy = sun_y - self.y
        dist = math.hypot(dx, dy)
        if dist < 1: return
        f  = G * self.mass * sun_mass / dist**2
        th = math.atan2(dy, dx)
        self.vx += math.cos(th) * f / self.mass * TIMESTEP
        self.vy += math.sin(th) * f / self.mass * TIMESTEP
        self.x  += self.vx * TIMESTEP
        self.y  += self.vy * TIMESTEP

    def draw(self, win, scale, cx, cy):
        sx = int(self.x * scale + cx)
        sy = int(self.y * scale + cy)
        if 0 <= sx < WIDTH and 0 <= sy < HEIGHT:
            pygame.draw.circle(win, (110, 100, 90), (sx, sy), 1)


# ── Planet ───────────────────────────────────────────────────────────────────
class Planet:
    def __init__(self, x, y, radius, color, mass, name="",
                 orbital_v=0, period="", fun_fact="",
                 has_ring=False, ring_color=None):
        self.x     = x;  self.y     = y
        self.xv    = 0;  self.yv    = orbital_v
        self.radius = radius
        self.color  = color
        self.mass   = mass
        self.name   = name
        self.sun    = False
        self.trail  = []
        self.dist_to_sun = 0
        self.period   = period
        self.fun_fact = fun_fact
        self.has_ring    = has_ring
        self.ring_color  = ring_color or (200, 170, 100)

    # Physics
    def update(self, planets):
        if self.sun:
            return
        fx = fy = 0.0
        for p in planets:
            if p is self:
                continue
            dx    = p.x - self.x
            dy    = p.y - self.y
            dist  = math.hypot(dx, dy)
            if dist < 1:
                continue
            if p.sun:
                self.dist_to_sun = dist
            force = G * self.mass * p.mass / dist**2
            th    = math.atan2(dy, dx)
            fx   += math.cos(th) * force
            fy   += math.sin(th) * force
        self.xv += fx / self.mass * TIMESTEP
        self.yv += fy / self.mass * TIMESTEP
        self.x  += self.xv * TIMESTEP
        self.y  += self.yv * TIMESTEP

    # Draw
    def draw(self, win, scale, cx, cy, selected=False, show_labels=True):
        sx = int(self.x * scale + cx)
        sy = int(self.y * scale + cy)

        # Trail
        self.trail.append((sx, sy))
        if len(self.trail) > 400:
            self.trail.pop(0)

        if not self.sun and len(self.trail) > 2:
            for i in range(1, len(self.trail)):
                alpha  = i / len(self.trail)
                lc     = tuple(int(c * alpha * 0.45) for c in self.color)
                pygame.draw.line(win, lc, self.trail[i-1], self.trail[i], 1)

        # Sun glow
        if self.sun:
            glow_surf = pygame.Surface((self.radius*8, self.radius*8), pygame.SRCALPHA)
            for i in range(5, 0, -1):
                gr  = self.radius + i * 12
                ga  = 55 - i * 9
                pygame.draw.circle(glow_surf, (255, 200, 50, ga),
                                   (self.radius*4, self.radius*4), gr)
            win.blit(glow_surf, (sx - self.radius*4, sy - self.radius*4))

        # Saturn-style ring (drawn behind planet)
        if self.has_ring:
            rw = int(self.radius * 2.4)
            rh = int(self.radius * 0.7)
            ring_surf = pygame.Surface((rw*2+4, rh*2+4), pygame.SRCALPHA)
            rc = (*self.ring_color, 140)
            pygame.draw.ellipse(ring_surf, rc,
                                (2, 2, rw*2, rh*2), max(1, self.radius//3))
            win.blit(ring_surf, (sx - rw - 2, sy - rh - 2))

        # Selection ring
        if selected:
            pygame.draw.circle(win, (255, 255, 255), (sx, sy), self.radius + 6, 1)

        # Planet body
        pygame.draw.circle(win, self.color, (sx, sy), self.radius)

        # Labels
        if show_labels and self.name:
            label = FONT_SM.render(self.name, True, (220, 220, 220))
            win.blit(label, (sx - label.get_width()//2, sy + self.radius + 5))

        if show_labels and not self.sun and self.dist_to_sun:
            dist_txt = FONT_SM.render(
                f"{self.dist_to_sun/1e9:.1f}M km", True, (130, 130, 130))
            win.blit(dist_txt, (sx - dist_txt.get_width()//2, sy + self.radius + 19))

    def hit_test(self, mx, my, scale, cx, cy):
        sx = self.x * scale + cx
        sy = self.y * scale + cy
        return math.hypot(mx - sx, my - sy) < max(self.radius + 6, 12)


# ── HUD ──────────────────────────────────────────────────────────────────────
def draw_info_panel(win, planet, day, paused, speed):
    """Bottom-left info panel."""
    lines = []
    if planet:
        lines.append(("name",  planet.name))
        if not planet.sun:
            vel = math.hypot(planet.xv, planet.yv) / 1000
            lines.append(("key",  f"Distance : {planet.dist_to_sun/1e9:.2f} M km"))
            lines.append(("key",  f"Velocity  : {vel:.2f} km/s"))
            lines.append(("key",  f"Period    : {planet.period}"))
            if planet.fun_fact:
                lines.append(("fact", planet.fun_fact))
        else:
            lines.append(("key",  "Mass : 1.989 × 10³⁰ kg"))
            lines.append(("key",  "G2V yellow dwarf star"))

    # Panel size
    pad   = 12
    lh    = 18
    ph    = pad*2 + lh * max(len(lines), 1) + 10
    pw    = 260
    px    = 12
    py    = HEIGHT - ph - 12

    panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
    panel.fill((10, 10, 30, 180))
    pygame.draw.rect(panel, (80, 80, 120, 120), (0, 0, pw, ph), 1)
    win.blit(panel, (px, py))

    y = py + pad
    for kind, text in lines:
        if kind == "name":
            surf = FONT_LG.render(text, True, (255, 220, 120))
        elif kind == "fact":
            surf = FONT_SM.render(text, True, (160, 160, 200))
        else:
            surf = FONT_SM.render(text, True, (180, 200, 220))
        win.blit(surf, (px + pad, y))
        y += lh

    # Top-right: day / status
    status = f"{'[PAUSED]  ' if paused else ''}Day {day:,}   Speed {speed}x"
    s = FONT_MD.render(status, True, (160, 160, 180))
    win.blit(s, (WIDTH - s.get_width() - 14, 14))

    # Controls hint
    hint = FONT_SM.render(
        "SPACE pause  ↑↓ speed  scroll zoom  drag pan  click select",
        True, (80, 80, 110))
    win.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 18))


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    global win
    clock    = pygame.time.Clock()
    run      = True
    paused   = False
    speed    = 1          # days per frame
    day      = 0
    t        = 0.0        # time for twinkle
    selected = None

    # View state
    scale    = 150 / AU
    offset_x = 0.0
    offset_y = 0.0
    dragging = False
    drag_start = (0, 0)
    drag_off   = (0.0, 0.0)

    # Stars
    stars = [Star() for _ in range(220)]

    # ── Planets ──────────────────────────────────────────────────────────────
    sun = Planet(0, 0, 24, YELLOW, 1.98892e30, "Sun")
    sun.sun = True

    mercury = Planet(0.387*AU, 0, 4,  GREY,   3.30e23, "Mercury",
                     -47_400, "88 days",  "Temp swings 600 °C day/night")
    venus   = Planet(0.723*AU, 0, 7,  ORANGE, 4.87e24, "Venus",
                     -35_000, "225 days", "Hottest planet (462 °C avg)")
    earth   = Planet(-1*AU,    0, 8,  BLUE,   5.97e24, "Earth",
                      29_783, "365 days", "Only known life-bearing world")
    mars    = Planet(-1.524*AU,0, 6,  RED,    6.39e23, "Mars",
                      24_100, "687 days", "Home of Olympus Mons (21 km)")
    jupiter = Planet(5.203*AU, 0, 16, BROWN,  1.898e27,"Jupiter",
                     -13_070, "11.9 yrs", "Largest planet, 95 known moons")
    saturn  = Planet(-9.537*AU,0, 13, TAN,    5.683e26,"Saturn",
                       9_690, "29.4 yrs", "Rings span 282,000 km",
                     has_ring=True, ring_color=(190, 160, 90))
    uranus  = Planet(19.19*AU, 0, 10, (130,210,210), 8.681e25, "Uranus",
                     -6_810, "84 yrs",   "Rotates on its side (98°)")
    neptune = Planet(-30.07*AU,0, 9,  (60,100,200),  1.024e26, "Neptune",
                      5_430, "165 yrs",  "Winds reach 2,100 km/h")

    planets = [sun, mercury, venus, earth, mars, jupiter, saturn, uranus, neptune]

    # ── Asteroid belt (Mars–Jupiter gap) ─────────────────────────────────────
    asteroids = []
    for _ in range(150):
        angle = random.uniform(0, math.pi * 2)
        dist  = random.uniform(2.2, 3.2) * AU
        ax    = math.cos(angle) * dist
        ay    = math.sin(angle) * dist
        v     = math.sqrt(G * sun.mass / dist)
        vx    = -math.sin(angle) * v
        vy    =  math.cos(angle) * v
        asteroids.append(Asteroid(ax, ay, vx, vy))

    # ── Main loop ─────────────────────────────────────────────────────────────
    while run:
        clock.tick(60)
        t += 0.05

        W = win.get_width()
        H = win.get_height()
        cx = W / 2 + offset_x
        cy = H / 2 + offset_y

        # ── Events ────────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            elif event.type == pygame.VIDEORESIZE:
                win = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key in (pygame.K_UP, pygame.K_EQUALS, pygame.K_PLUS):
                    speed = min(speed + 1, 30)
                elif event.key in (pygame.K_DOWN, pygame.K_MINUS):
                    speed = max(speed - 1, 1)
                elif event.key == pygame.K_r:
                    scale = 150 / AU; offset_x = offset_y = 0
                elif event.key == pygame.K_ESCAPE:
                    selected = None

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if event.button == 1:
                    hit = False
                    for p in planets:
                        if p.hit_test(mx, my, scale, cx, cy):
                            selected = p
                            hit = True
                            break
                    if not hit:
                        selected = None
                        dragging    = True
                        drag_start  = (mx, my)
                        drag_off    = (offset_x, offset_y)
                elif event.button == 4:
                    scale *= 1.12
                elif event.button == 5:
                    scale *= 0.89

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging = False

            elif event.type == pygame.MOUSEMOTION:
                if dragging:
                    mx, my      = event.pos
                    offset_x    = drag_off[0] + (mx - drag_start[0])
                    offset_y    = drag_off[1] + (my - drag_start[1])

        # ── Physics ───────────────────────────────────────────────────────────
        if not paused:
            for _ in range(speed):
                for p in planets:
                    p.update(planets)
                for a in asteroids:
                    a.update(sun.mass, sun.x, sun.y)
                day += 1

        # ── Draw ──────────────────────────────────────────────────────────────
        win.fill(BLACK)

        for star in stars:
            star.draw(win, t)

        for a in asteroids:
            a.draw(win, scale, cx, cy)

        for p in planets:
            p.draw(win, scale, cx, cy,
                   selected=(p is selected),
                   show_labels=(scale > 70 / AU))

        draw_info_panel(win, selected, day, paused, speed)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
