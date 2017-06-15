
import numpy as np

from fidimag.micro import Sim
from fidimag.common import CuboidMesh
from fidimag.micro import UniformExchange, Demag, DMI, UniaxialAnisotropy
from fidimag.micro import Zeeman

import os
import shutil

mu0 = 4 * np.pi * 1e-7


# -------------------------------------------------------------------------
# Initial states ----------------------------------------------------------
# -------------------------------------------------------------------------

def generate_skyrmion_down(pos, sk_radius=1, chirality=1, pi_factor=1):
    """
    Sign will affect the chirality of the skyrmion
    """
    # We will generate a skyrmion in the middle of the stripe
    # (the origin is there) with the core pointing down
    x, y = (pos[0] - CENTRE_X), (pos[1] - CENTRE_Y)

    if np.sqrt(x ** 2 + y ** 2) <= sk_radius:
        # Polar coordinates:
        r = (x ** 2 + y ** 2) ** 0.5
        phi = np.arctan2(y, x) - np.pi * 0.5
        # This determines the profile we want for the
        # skyrmion
        # Single twisting: k = pi / R
        k = pi_factor * np.pi / sk_radius

        # We define here a 'hedgehog' skyrmion pointing down
        return (chirality * np.sin(k * r) * np.cos(phi),
                chirality * np.sin(k * r) * np.sin(phi),
                -np.cos(k * r))
    else:
        return (0, 0, 1)


def generate_skyrmion_up(pos, sk_radius=1, chirality=1, pi_factor=1):
    # We will generate a skyrmion in the middle of the stripe
    # (the origin is there) with the core pointing down
    x, y = (pos[0] - CENTRE_X), (pos[1] - CENTRE_Y)

    if np.sqrt(x ** 2 + y ** 2) <= sk_radius:
        # Polar coordinates:
        r = (x ** 2 + y ** 2) ** 0.5
        phi = np.arctan2(y, x) - np.pi * 0.5
        # This determines the profile we want for the
        # skyrmion
        # Single twisting: k = pi / R
        k = pi_factor * np.pi / sk_radius

        # We define here a 'hedgehog' skyrmion pointing down
        return (chirality * np.sin(k * r) * np.cos(phi),
                chirality * np.sin(k * r) * np.sin(phi),
                np.cos(k * r))
    else:
        return (0, 0, -1)


# Mesh ---------------------------------------------------------------------

# if nanobox:
#     nx = int(nanobox[0] / fd_lengths[0])
#     ny = int(nanobox[1] / fd_lengths[1])
#     nz = int(nanobox[2] / fd_lengths[2])
nanodisk = [80, 1]
fd_lengths = [1, 1, 1]


nx = int(nanodisk[0] / fd_lengths[0])
ny = int(nanodisk[0] / fd_lengths[1])
nz = int(nanodisk[1] / fd_lengths[2])

dx = fd_lengths[0]
dy = fd_lengths[1]
dz = fd_lengths[2]

mesh = CuboidMesh(nx=nx,
                  ny=ny,
                  nz=nz,
                  dx=dx,
                  dy=dy,
                  dz=dz,
                  unit_length=1e-9,
                  )

CENTRE_X = (np.max(mesh.coordinates[:, 0])
            - np.min(mesh.coordinates[:, 0])) * 0.5 + np.min(mesh.coordinates[:, 0])
CENTRE_Y = (np.max(mesh.coordinates[:, 1])
            - np.min(mesh.coordinates[:, 1])) * 0.5 + np.min(mesh.coordinates[:, 1])

# Initiate Fidimag simulation ---------------------------------------------

sim_name = 'skyrmion_bulk_DMI'
sim = Sim(mesh, name=sim_name, integrator='sundials_openmp')

# sim.set_tols(rtol=1e-10, atol=1e-14)
# sim.gamma = 2.211e5

# Material parameters -----------------------------------------------------

# if nanobox:
#     sim.Ms = Ms

Ms = 3.84e5

def disk(r):
    x, y = r[0] - CENTRE_X, r[1] - CENTRE_Y
    if x ** 2. + y ** 2 < (0.5 * nanodisk[0]) ** 2.:
        return Ms
    else:
        return 0

sim.set_Ms(disk)

# -----------------------------------------------------------------------------

A = 8.78e-12
D = -1.58e-3
Bz = 0.8
k_u = False

exch = UniformExchange(A=A)
sim.add(exch)

dmi = DMI(D=D, dmi_type='bulk')
sim.add(dmi)

zeeman = Zeeman((0, 0, Bz / mu0))
sim.add(zeeman, save_field=True)

if k_u:
    # Uniaxial anisotropy along + z-axis
    sim.add(UniaxialAnisotropy(k_u, axis=(0, 0, 1)))

sim.add(Demag())

# -------------------------------------------------------------------------


# Load magnetisation profile ---------------------------------------------
initial_state_skyrmion_down = [60]
initial_state_skyrmion_up = False

# Change the skyrmion initial configuration according to the
# chirality of the system (give by the DMI constant)
if initial_state_skyrmion_down:
    if D > 0:
        chirality = -1
    else:
        chirality = 1

    if len(initial_state_skyrmion_down) == 2:
        pi_factor = initial_state_skyrmion_down[1]
    else:
        pi_factor = 1

    sk_radius = initial_state_skyrmion_down[0]

    sim.set_m(lambda x: generate_skyrmion_down(x,
                                               sk_radius=sk_radius,
                                               chirality=chirality,
                                               pi_factor=pi_factor
                                               ))

elif initial_state_skyrmion_up:
    if D > 0:
        chirality = 1
    else:
        chirality = -1

    if len(initial_state_skyrmion_up) == 2:
        pi_factor = initial_state_skyrmion_up[1]
    else:
        pi_factor = 1

    sk_radius = initial_state_skyrmion_up[0]

    sim.set_m(lambda x: generate_skyrmion_up(x,
                                             sk_radius=sk_radius,
                                             chirality=chirality,
                                             pi_factor=pi_factor
                                             ))


# -------------------------------------------------------------------------
# Initiate simulation -----------------------------------------------------
# -------------------------------------------------------------------------
# Fidimag automatically saves the last state
# Initial state:

sim.save_vtk()
sim.driver.alpha = 0.9
sim.driver.do_precession = False

# if tols:
#     sim.driver.set_tols(rtol=tols[0], atol=tols[1])

sim.relax(dt=1e-13, stopping_dmdt=1e-2,
          max_steps=3000,
          save_m_steps=2000,
          save_vtk_steps=2000)

# Save final states
sim.save_m()
sim.save_vtk()
