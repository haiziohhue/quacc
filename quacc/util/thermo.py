"""
Utility functions for thermochemistry
"""
from __future__ import annotations

import numpy as np
from ase import Atoms, units
from ase.thermochemistry import IdealGasThermo

from quacc.schemas.atoms import atoms_to_metadata


def ideal_gas(
    atoms: Atoms,
    vib_freqs: list[float | complex],
    atom_indices: list[int] = None,
    energy: float = 0.0,
    spin_multiplicity: float = None,
) -> IdealGasThermo:
    """
    Calculate thermodynamic properties for a molecule from a given vibrational analysis.
    This is for free gases only and will not be valid for solids or adsorbates on surfaces.

    Parameters
    ----------
    atoms
        The Atoms object associated with the vibrational analysis.
    vib_freqs
        The list of vibrations to use, typically obtained from Vibrations.get_frequencies().
    atom_indices
        The indices of the atoms allowed to vibrate. If None, it's assumed they all vibrate.
    energy
        Potential energy in eV. If 0 eV, then the thermochemical correction is computed.
    spin_multiplicity
        The spin multiplicity. If None, this will be determined automatically from the
        attached magnetic moments.

    Returns
    -------
    IdealGasThermo object
    """

    if atom_indices:
        atoms = atoms[atom_indices]

    # Switch off PBC since this is only for molecules
    atoms.set_pbc(False)

    # Ensure all imaginary modes are actually negatives
    for i, f in enumerate(vib_freqs):
        if isinstance(f, complex) and np.imag(f) != 0:
            vib_freqs[i] = complex(0 - f * 1j)

    vib_energies = [f * units.invcm for f in vib_freqs]
    real_vib_energies = np.real(vib_energies)

    for i, f in enumerate(vib_freqs):
        if not isinstance(f, complex) and f < 0:
            vib_freqs[i] = complex(0 - f * 1j)

    # Get the spin from the Atoms object
    if spin_multiplicity:
        spin = (spin_multiplicity - 1) / 2
    elif (
        getattr(atoms, "calc", None) is not None
        and getattr(atoms.calc, "results", None) is not None
    ):
        spin = round(atoms.calc.results.get("magmom", 0)) / 2
    elif atoms.has("initial_magmoms"):
        spin = round(np.sum(atoms.get_initial_magnetic_moments())) / 2
    else:
        spin = 0

    # Get symmetry for later use
    natoms = len(atoms)
    metadata = atoms_to_metadata(atoms)

    # Get the geometry
    if natoms == 1:
        geometry = "monatomic"
    elif metadata["symmetry"]["linear"]:
        geometry = "linear"
    else:
        geometry = "nonlinear"

    return IdealGasThermo(
        real_vib_energies,
        geometry,
        potentialenergy=energy,
        atoms=atoms,
        symmetrynumber=metadata["symmetry"]["rotation_number"],
        spin=spin,
    )