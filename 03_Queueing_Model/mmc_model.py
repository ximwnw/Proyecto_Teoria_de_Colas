import math

def mmc_metrics(lam, mu, c):
    # VALIDACIÓN PRIMERO
    if lam < 0:
        raise ValueError("lambda must be non-negative.")
    if mu <= 0:
        raise ValueError("mu must be greater than zero.")
    if c <= 0 or not isinstance(c, int):
        raise ValueError("servers must be a positive integer.")

    # Cálculo de rho
    rho = lam / (c * mu)
    estabilidad = rho < 1

    # Sistema inestable
    if not estabilidad:
        return {
            "rho": rho,
            "stability": False,
            "P0": 0.0,
            "Lq": float('inf'),
            "Wq_minutes": float('inf'),
            "L": float('inf'),
            "W_minutes": float('inf'),
        }

    # Sistema estable
    sum_terms = sum((lam / mu) ** n / math.factorial(n) for n in range(c))
    last_term = ((lam / mu) ** c) / (math.factorial(c) * (1 - rho))
    P0 = 1 / (sum_terms + last_term)

    Lq = (P0 * (lam / mu) ** c * rho) / (math.factorial(c) * (1 - rho) ** 2)

    if lam > 0:
        Wq_hours = Lq / lam
        Wq_minutes = Wq_hours * 60
    else:
        Wq_minutes = 0.0

    L = Lq + (lam / mu)

    if lam > 0:
        W_hours = L / lam
        W_minutes = W_hours * 60
    else:
        W_minutes = 0.0

    return {
        "rho": rho,
        "stability": estabilidad,
        "P0": P0,
        "Lq": Lq,
        "Wq_minutes": Wq_minutes,
        "L": L,
        "W_minutes": W_minutes,
    }
