import math
import random
import pygame
import settings

try:    # Windows: use real pixels, not display-scaled ones
    import ctypes
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

pygame.init()

# Fit the window to the screen. A window bigger than the screen gets pushed
# partly off it, which can hide the title text and key hints at the top.
sizes = pygame.display.get_desktop_sizes()
desk_w, desk_h = sizes[0] if sizes else (settings.WIDTH, settings.HEIGHT)
W = min(settings.WIDTH, desk_w - 60)
H = min(settings.HEIGHT, desk_h - 160)

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Can Light Escape a Black Hole?")
clock = pygame.time.Clock()

CX, CY = W // 2, H // 2
M = settings.BLACK_HOLE_MASS          # Schwarzschild black hole (G = c = 1)
SCALE = H / 16                        # pixels per unit: view shows +/-8 units vertically

D_LAMBDA = 0.02                       # physics step size
STEPS_PER_FRAME = 2                   # raise to speed the demo up, lower to slow it down
START_X = -7.0
ESCAPE_R = 15.0

B_VALUES = {pygame.K_1: 6.0, pygame.K_2: 5.196152, pygame.K_3: 5.0}

font_big = pygame.font.Font(None, 110)
font_hud = pygame.font.Font(None, 44)
font_label = pygame.font.Font(None, 36)

HOT = (255, 170, 70)     # warm glow colour
TRAIL_HOT = (255, 240, 190)  # light close to the hole
COOL = (90, 150, 255)    # light far away
LABEL_GREY = (170, 175, 190)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def scaled(colour, k):
    return tuple(min(255, int(c * k)) for c in colour)


def glow_sprite(radius, colour, strength):
    """Soft round blob, meant to be added onto the scene (BLEND_ADD)."""
    s = pygame.Surface((radius * 2, radius * 2))
    for y in range(radius * 2):
        for x in range(radius * 2):
            d = math.hypot(x - radius + 0.5, y - radius + 0.5) / radius
            if d < 1:
                s.set_at((x, y), scaled(colour, (1 - d) ** 2 * strength))
    return s


N_SPRITES = 32
SPRITE_R = 14
TRAIL_SPRITES = [
    glow_sprite(SPRITE_R, lerp(TRAIL_HOT, COOL, i / (N_SPRITES - 1)), 0.16)
    for i in range(N_SPRITES)
]
HEAD_R = 40
HEAD_SPRITE = glow_sprite(HEAD_R, (255, 255, 255), 0.9)


def build_base():
    """Starfield + warm halo + glowing photon sphere. Built once."""
    base = pygame.Surface((W, H))
    rng = random.Random(7)
    for _ in range(700):
        v = rng.choice((70, 110, 160, 220, 255))
        c = (v, v, min(255, v + rng.randrange(0, 30)))
        size = 2 if v > 200 and rng.random() < 0.3 else 1
        pygame.draw.circle(base, c, (rng.randrange(W), rng.randrange(H)), size)

    R = int(5 * SCALE)
    halo = pygame.Surface((2 * R, 2 * R))
    for i in range(R, 0, -4):
        pygame.draw.circle(halo, scaled(HOT, (1 - i / R) ** 3 * 0.35), (R, R), i)
    base.blit(halo, (CX - R, CY - R), special_flags=pygame.BLEND_ADD)

    ring = pygame.Surface((2 * R, 2 * R))
    rp = int(settings.PHOTON_SPHERE_RADIUS * SCALE)
    for width, k in ((18, 0.05), (11, 0.09), (6, 0.16), (2, 0.45)):
        pygame.draw.circle(ring, scaled(HOT, k), (R, R), rp + width // 2, width)
    base.blit(ring, (CX - R, CY - R), special_flags=pygame.BLEND_ADD)
    return base


BASE = build_base()

horizon_px = int(settings.SCHWARZSCHILD_RADIUS * SCALE)


def build_hole_glow(frames=24, pad=int(1.2 * SCALE)):
    """Glowing edge around the event horizon, gently pulsing (pre-rendered)."""
    R = horizon_px + pad
    out = []
    for f in range(frames):
        k = 0.85 + 0.15 * math.sin(2 * math.pi * f / frames)
        surf = pygame.Surface((2 * R, 2 * R))
        for i in range(pad, 0, -2):
            t = i / pad    # 1 = outer edge of the glow, 0 = at the horizon
            colour = lerp((255, 235, 190), (170, 40, 10), min(1.0, t * 1.6))
            pygame.draw.circle(surf, scaled(colour, (1 - t) ** 2.2 * k * 0.75),
                               (R, R), horizon_px + i)
        pygame.draw.circle(surf, (0, 0, 0), (R, R), horizon_px)   # keep the inside black
        out.append(surf)
    return out, R


HOLE_GLOW, HOLE_R = build_hole_glow()
LABEL_PHOTON = font_label.render("Photon sphere  r = 3M", True, scaled(HOT, 0.9))
LABEL_HORIZON = font_label.render("Event horizon  r = 2M", True, LABEL_GREY)
off = int(settings.PHOTON_SPHERE_RADIUS * SCALE * 0.72) + 12


def to_screen(x, y):
    return int(CX + x * SCALE), int(CY - y * SCALE)


def deriv(r, dr, b):
    """Returns (dr/dlambda, d2r/dlambda2, dphi/dlambda) for a photon.
    dphi is negative: the photon travels left -> right (clockwise)."""
    return dr, b**2 * (r - 3 * M) / r**4, -b / r**2


def reset(b):
    r = math.hypot(START_X, b)
    phi = math.atan2(b, START_X)
    dr = -math.sqrt(1 - (b**2 / r**2) * (1 - 2 * M / r))
    return r, dr, phi, BASE.copy(), None


def render_hud(b):
    return font_hud.render(
        f"b = {b}      [1] 6.0   [2] 5.196152   [3] 5.0   [R] restart   [H] hide this",
        True, (130, 135, 150))


b = B_VALUES[pygame.K_1]
r, dr, phi, scene, result = reset(b)
hud = render_hud(b)
show_hud = True
capture_t = None
running = True

while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key in B_VALUES:
                b = B_VALUES[event.key]
                hud = render_hud(b)
                r, dr, phi, scene, result = reset(b)
            elif event.key == pygame.K_r:
                r, dr, phi, scene, result = reset(b)
            elif event.key == pygame.K_h:
                show_hud = not show_hud

    for _ in range(STEPS_PER_FRAME):
        if result is not None:
            break
        # Fourth-order Runge-Kutta step
        h = D_LAMBDA
        k1 = deriv(r, dr, b)
        k2 = deriv(r + h / 2 * k1[0], dr + h / 2 * k1[1], b)
        k3 = deriv(r + h / 2 * k2[0], dr + h / 2 * k2[1], b)
        k4 = deriv(r + h * k3[0], dr + h * k3[1], b)
        r += h / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
        dr += h / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
        phi += h / 6 * (k1[2] + 2 * k2[2] + 2 * k3[2] + k4[2])

        if r <= settings.SCHWARZSCHILD_RADIUS:
            result = "LIGHT CAPTURED"
        elif r > ESCAPE_R and dr > 0:
            result = "LIGHT ESCAPED"

        # Leave a glowing trail: hot colour near the hole, cool far away
        px, py = to_screen(r * math.cos(phi), r * math.sin(phi))
        idx = int(max(0.0, min(1.0, (r - 2) / 6)) * (N_SPRITES - 1))
        scene.blit(TRAIL_SPRITES[idx], (px - SPRITE_R, py - SPRITE_R),
                   special_flags=pygame.BLEND_ADD)

    px, py = to_screen(r * math.cos(phi), r * math.sin(phi))

    screen.blit(scene, (0, 0))

    # Event horizon
    pygame.draw.circle(screen, (0, 0, 0), (CX, CY), horizon_px)
    glow = HOLE_GLOW[(pygame.time.get_ticks() // 100) % len(HOLE_GLOW)]
    screen.blit(glow, (CX - HOLE_R, CY - HOLE_R), special_flags=pygame.BLEND_ADD)
    pygame.draw.circle(screen, (255, 200, 130), (CX, CY), horizon_px, 2)

    # Capture effect: the hole flares and ripples when light falls in
    if result == "LIGHT CAPTURED":
        if capture_t is None:
            capture_t = pygame.time.get_ticks()
        since = (pygame.time.get_ticks() - capture_t) / 1000
        for _ in range(int(max(0.0, 1 - since / 1.5) * 3)):
            screen.blit(glow, (CX - HOLE_R, CY - HOLE_R),
                        special_flags=pygame.BLEND_ADD)
        for delay in (0.0, 0.35):
            u = (since - delay) / 1.6
            if 0 <= u < 1:
                pygame.draw.circle(screen, scaled(HOT, (1 - u) ** 2), (CX, CY),
                                   horizon_px + int(u * 4 * SCALE), 4)
    else:
        capture_t = None
        since = None

    # Labels
    screen.blit(LABEL_PHOTON, (CX + off, CY - off - 30))
    screen.blit(LABEL_HORIZON, LABEL_HORIZON.get_rect(
        center=(CX, CY + int(2.5 * SCALE))))

    # Photon
    if result != "LIGHT CAPTURED":
        screen.blit(HEAD_SPRITE, (px - HEAD_R, py - HEAD_R),
                    special_flags=pygame.BLEND_ADD)
        pygame.draw.circle(screen, (255, 255, 255), (px, py), 5)

    if show_hud:
        screen.blit(hud, (30, 30))
    if result is not None:
        colour = (255, 110, 110) if result == "LIGHT CAPTURED" else (120, 225, 150)
        fade = 1.0 if since is None else min(1.0, since / 0.6)
        text = font_big.render(result, True, scaled(colour, fade))
        screen.blit(text, text.get_rect(center=(CX, 140)))

    pygame.display.flip()
    clock.tick(settings.FPS)

pygame.quit()
