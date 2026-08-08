"""
ChemLab Analytics - Chemistry Calculation Engine
Handles molecular mass, mole/mass conversions, molarity, dilution,
density, concentration, ideal gas law, and basic stoichiometry.
"""

import re

# ---------------------------------------------------------------------------
# Periodic table: atomic weights (g/mol) for common elements
# ---------------------------------------------------------------------------
ATOMIC_WEIGHTS = {
    "H": 1.008, "He": 4.0026, "Li": 6.94, "Be": 9.0122, "B": 10.81,
    "C": 12.011, "N": 14.007, "O": 15.999, "F": 18.998, "Ne": 20.180,
    "Na": 22.990, "Mg": 24.305, "Al": 26.982, "Si": 28.085, "P": 30.974,
    "S": 32.06, "Cl": 35.45, "Ar": 39.948, "K": 39.098, "Ca": 40.078,
    "Sc": 44.956, "Ti": 47.867, "V": 50.942, "Cr": 51.996, "Mn": 54.938,
    "Fe": 55.845, "Co": 58.933, "Ni": 58.693, "Cu": 63.546, "Zn": 65.38,
    "Ga": 69.723, "Ge": 72.630, "As": 74.922, "Se": 78.971, "Br": 79.904,
    "Kr": 83.798, "Rb": 85.468, "Sr": 87.62, "Y": 88.906, "Zr": 91.224,
    "Nb": 92.906, "Mo": 95.95, "Ag": 107.87, "Cd": 112.41, "Sn": 118.71,
    "Sb": 121.76, "I": 126.90, "Xe": 131.29, "Cs": 132.91, "Ba": 137.33,
    "Pt": 195.08, "Au": 196.97, "Hg": 200.59, "Pb": 207.2, "Bi": 208.98,
    "U": 238.03,
}

GAS_CONSTANT = 0.082057  # L·atm / (mol·K)


class ChemistryError(ValueError):
    """Raised when a chemistry input cannot be parsed or is invalid."""


# ---------------------------------------------------------------------------
# Molecular mass parsing (supports nested parentheses, e.g. Ca(OH)2, Al2(SO4)3)
# ---------------------------------------------------------------------------
def parse_formula(formula: str) -> dict:
    """Parse a chemical formula string into an element:count dictionary."""
    formula = formula.strip().replace(" ", "")
    if not formula:
        raise ChemistryError("Formula cannot be empty.")

    token_pattern = re.compile(r"([A-Z][a-z]?|\(|\)|\d+)")
    tokens = token_pattern.findall(formula)
    if "".join(tokens) != formula:
        raise ChemistryError(f"Could not fully parse formula '{formula}'.")

    stack = [{}]
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "(":
            stack.append({})
            i += 1
        elif tok == ")":
            i += 1
            multiplier = 1
            if i < len(tokens) and tokens[i].isdigit():
                multiplier = int(tokens[i])
                i += 1
            group = stack.pop()
            for el, cnt in group.items():
                stack[-1][el] = stack[-1].get(el, 0) + cnt * multiplier
        elif re.match(r"[A-Z][a-z]?$", tok):
            if tok not in ATOMIC_WEIGHTS:
                raise ChemistryError(f"Unknown element symbol '{tok}'.")
            count = 1
            if i + 1 < len(tokens) and tokens[i + 1].isdigit():
                count = int(tokens[i + 1])
                i += 1
            stack[-1][tok] = stack[-1].get(tok, 0) + count
            i += 1
        else:
            raise ChemistryError(f"Unexpected token '{tok}' in formula.")
    if len(stack) != 1:
        raise ChemistryError("Unbalanced parentheses in formula.")
    return stack[0]


def molecular_mass(formula: str) -> dict:
    """Return total molar mass and per-element breakdown for a formula."""
    composition = parse_formula(formula)
    breakdown = []
    total = 0.0
    for el, count in composition.items():
        mass = ATOMIC_WEIGHTS[el] * count
        total += mass
        breakdown.append({
            "element": el,
            "count": count,
            "atomic_weight": ATOMIC_WEIGHTS[el],
            "subtotal": round(mass, 4),
        })
    return {
        "formula": formula,
        "molar_mass": round(total, 4),
        "breakdown": breakdown,
    }


# ---------------------------------------------------------------------------
# Moles <-> mass
# ---------------------------------------------------------------------------
def moles_from_mass(mass_g: float, molar_mass: float) -> float:
    if molar_mass <= 0:
        raise ChemistryError("Molar mass must be greater than zero.")
    return mass_g / molar_mass


def mass_from_moles(moles: float, molar_mass: float) -> float:
    if molar_mass <= 0:
        raise ChemistryError("Molar mass must be greater than zero.")
    return moles * molar_mass


# ---------------------------------------------------------------------------
# Molarity: M = mol / L
# ---------------------------------------------------------------------------
def molarity(moles: float, volume_l: float) -> float:
    if volume_l <= 0:
        raise ChemistryError("Volume must be greater than zero.")
    return moles / volume_l


# ---------------------------------------------------------------------------
# Dilution: C1V1 = C2V2  (solve for whichever variable is None)
# ---------------------------------------------------------------------------
def dilution(c1=None, v1=None, c2=None, v2=None) -> dict:
    values = {"c1": c1, "v1": v1, "c2": c2, "v2": v2}
    missing = [k for k, v in values.items() if v is None]
    if len(missing) != 1:
        raise ChemistryError("Provide exactly three of c1, v1, c2, v2 and leave one blank.")
    target = missing[0]
    try:
        if target == "c1":
            values["c1"] = (c2 * v2) / v1
        elif target == "v1":
            values["v1"] = (c2 * v2) / c1
        elif target == "c2":
            values["c2"] = (c1 * v1) / v2
        elif target == "v2":
            values["v2"] = (c1 * v1) / c2
    except ZeroDivisionError:
        raise ChemistryError("Cannot divide by zero — check your inputs.")
    values["solved_for"] = target
    return values


# ---------------------------------------------------------------------------
# Density: d = m / V
# ---------------------------------------------------------------------------
def density(mass=None, volume=None, density_val=None) -> dict:
    provided = [x is not None for x in (mass, volume, density_val)]
    if sum(provided) != 2:
        raise ChemistryError("Provide exactly two of mass, volume, density.")
    if density_val is None:
        if volume == 0:
            raise ChemistryError("Volume cannot be zero.")
        density_val = mass / volume
        return {"mass": mass, "volume": volume, "density": round(density_val, 5), "solved_for": "density"}
    if mass is None:
        mass = density_val * volume
        return {"mass": round(mass, 5), "volume": volume, "density": density_val, "solved_for": "mass"}
    if volume is None:
        if density_val == 0:
            raise ChemistryError("Density cannot be zero.")
        volume = mass / density_val
        return {"mass": mass, "volume": round(volume, 5), "density": density_val, "solved_for": "volume"}


# ---------------------------------------------------------------------------
# Percentage concentration
# ---------------------------------------------------------------------------
def percent_concentration(solute_mass=None, solution_mass=None, percent=None) -> dict:
    """% w/w = (mass of solute / mass of solution) * 100. Solve for the missing value."""
    provided = [x is not None for x in (solute_mass, solution_mass, percent)]
    if sum(provided) != 2:
        raise ChemistryError("Provide exactly two of solute_mass, solution_mass, percent.")
    if percent is None:
        if solution_mass == 0:
            raise ChemistryError("Solution mass cannot be zero.")
        percent = (solute_mass / solution_mass) * 100
        return {"solute_mass": solute_mass, "solution_mass": solution_mass,
                "percent": round(percent, 4), "solved_for": "percent"}
    if solute_mass is None:
        solute_mass = (percent / 100) * solution_mass
        return {"solute_mass": round(solute_mass, 5), "solution_mass": solution_mass,
                "percent": percent, "solved_for": "solute_mass"}
    if solution_mass is None:
        if percent == 0:
            raise ChemistryError("Percent cannot be zero.")
        solution_mass = solute_mass / (percent / 100)
        return {"solute_mass": solute_mass, "solution_mass": round(solution_mass, 5),
                "percent": percent, "solved_for": "solution_mass"}


# ---------------------------------------------------------------------------
# Ideal gas law: PV = nRT  (solve for whichever is None)
# ---------------------------------------------------------------------------
def ideal_gas_law(p=None, v=None, n=None, t=None) -> dict:
    values = {"P": p, "V": v, "n": n, "T": t}
    missing = [k for k, val in values.items() if val is None]
    if len(missing) != 1:
        raise ChemistryError("Provide exactly three of P (atm), V (L), n (mol), T (K) and leave one blank.")
    target = missing[0]
    try:
        if target == "P":
            values["P"] = (n * GAS_CONSTANT * t) / v
        elif target == "V":
            values["V"] = (n * GAS_CONSTANT * t) / p
        elif target == "n":
            values["n"] = (p * v) / (GAS_CONSTANT * t)
        elif target == "T":
            values["T"] = (p * v) / (GAS_CONSTANT * n)
    except ZeroDivisionError:
        raise ChemistryError("Cannot divide by zero — check your inputs.")
    values["solved_for"] = target
    values["R"] = GAS_CONSTANT
    return values


# ---------------------------------------------------------------------------
# Basic stoichiometry: given a balanced reaction ratio, compute product amount
# ---------------------------------------------------------------------------
def stoichiometry(mass_a: float, molar_mass_a: float, molar_mass_b: float,
                   coeff_a: float = 1, coeff_b: float = 1) -> dict:
    """
    For a reaction  coeff_a * A -> coeff_b * B (or any two species tied by
    a mole ratio), compute moles of A, moles of B, and mass of B.
    """
    if molar_mass_a <= 0 or molar_mass_b <= 0 or coeff_a <= 0 or coeff_b <= 0:
        raise ChemistryError("Molar masses and coefficients must be positive.")
    moles_a = mass_a / molar_mass_a
    moles_b = moles_a * (coeff_b / coeff_a)
    mass_b = moles_b * molar_mass_b
    return {
        "moles_a": round(moles_a, 5),
        "moles_b": round(moles_b, 5),
        "mass_b": round(mass_b, 5),
    }
