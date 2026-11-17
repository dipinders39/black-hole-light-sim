# black-hole-light-sim

A Python and Pygame simulation of a single ray of light passing a non-spinning (Schwarzschild) black hole. Change one number, the impact parameter b, and the light either bends round the black hole and escapes, or spirals in and gets captured.

## What it shows

Light always travels at c, but a black hole curves spacetime so much that the path of the light bends. Whether a ray escapes depends on how far off-centre it is aimed:

| Impact parameter | What happens |
|---|---|
| b = 6.0 | Bends round the black hole, then escapes |
| b = 5.196152 | Just below the critical value: loops near the photon sphere about 2.7 times, then falls in |
| b = 5.0 | Captured, crosses the event horizon |

The dividing line is the critical impact parameter

b_c = 3√3 M ≈ 5.196

Light aimed below b_c is captured and light aimed above it escapes. Exactly at b_c the light would get closer and closer to the photon sphere orbit forever. That orbit is unstable, though, so in practice any tiny difference sends the light one way or the other.

## Running it

You need Python 3 and pygame-ce, which installs from requirements.txt:

```bash
pip install -r requirements.txt
python main.py
```

The window sizes itself to fit your screen.

## Controls

| Key | Action |
|---|---|
| 1 | b = 6.0 (escapes) |
| 2 | b = 5.196152 (loops, then captured) |
| 3 | b = 5.0 (captured) |
| R | Restart the current run |
| H | Hide or show the key hints |
| Esc | Quit |

## The physics

The simulation uses geometric units, G = c = 1, with the black hole mass M = 1. In these units the event horizon (Schwarzschild radius) is at r = 2M and the photon sphere is at r = 3M. Distances are in units of GM/c², which is about 1.48 km for a black hole with the mass of the Sun.

I track the ray in polar coordinates: its distance r from the black hole and its angle φ. For light around a Schwarzschild black hole these obey

```
d²r/dλ² = b²(r − 3M) / r⁴
dφ/dλ   = b / r²
```

where λ is a parameter along the path (an affine parameter) and b is the impact parameter, the ratio of the light's angular momentum to its energy.

The first equation is where the photon sphere comes from. Outside r = 3M the right-hand side is positive, so it pushes the light outwards. Inside r = 3M it is negative and pulls the light in. At exactly r = 3M it is zero, so light can orbit there, but only unstably.

The ray starts 7 units to the left of the black hole at height b, heading towards it. Its starting radial speed comes from the null condition, which says light always moves at c:

```
dr/dλ = −√(1 − (b²/r²)(1 − 2M/r))
```

A run ends when the ray reaches r = 2M (captured) or moves outwards past r = 15 (escaped).

## Numerical method

The equations are stepped forward with fourth-order Runge-Kutta (RK4), using a step size of 0.02 and two steps per frame.

I started with the Euler method. Near the photon sphere the path is extremely sensitive to small errors, and with Euler the b = 5.196152 ray escaped after about 1.6 turns, which is wrong. RK4 measures the slope four times per step and takes a weighted average, so for the same step size its error is far smaller. With RK4 the ray loops about 2.7 times and is then captured, which is the correct result.

## Visual effects

The starfield, the glow around the event horizon and photon sphere, the coloured trail, and the flare and ripples when light is captured are only there to make the demo easier to follow, and aren't part of the physics. A real observer would see no flash: light crossing the event horizon just stops reaching them.

The trail colour shows distance from the black hole, blue far away and white-gold close in.

## Limitations

- It is a 2D slice. Light around a Schwarzschild black hole always moves in a single plane, so this is exact for one ray, but it is not a rendered 3D image of what you would see.
- The black hole doesn't spin. A spinning (Kerr) black hole would behave differently.
- 64-bit floats limit how close to b_c you can get, so even typing b_c in exactly only gives about 5 to 6 loops before the ray peels away.

## Files

| File | Purpose |
|---|---|
| main.py | Simulation, rendering and controls |
| settings.py | Window size, frame rate, colours, black hole mass and radii |
| requirements.txt | Python dependencies |

Made by Dipinder Singh.
