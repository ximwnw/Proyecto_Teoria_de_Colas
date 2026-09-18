import math
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# MODELO M/M/c
# ============================================================

def mmc_metrics(lam, mu, c):

    # Utilización
    rho = lam / (c * mu)

    # Sistema inestable
    if rho >= 1:

        return {
            "servers": c,
            "rho": rho,
            "stable": False,
            "Lq": math.inf,
            "Wq_minutes": math.inf
        }

    # Probabilidad de sistema vacío
    sum_terms = sum(
        (lam / mu) ** n / math.factorial(n)
        for n in range(c)
    )

    last_term = (
        (lam / mu) ** c
        / math.factorial(c)
    ) * (1 / (1 - rho))

    P0 = 1 / (sum_terms + last_term)

    # Número promedio de clientes en cola
    Lq = (
        P0
        * (lam / mu) ** c
        * rho
        / (
            math.factorial(c)
            * (1 - rho) ** 2
        )
    )

    # Tiempo promedio de espera
    Wq = Lq / lam

    Wq_minutes = Wq * 60

    return {
        "servers": c,
        "rho": rho,
        "stable": True,
        "Lq": Lq,
        "Wq_minutes": Wq_minutes
    }


# ============================================================
# PARÁMETROS
# ============================================================

LAMBDA = 74.8
MU = 12.1233

SERVER_COST = 20

WAITING_COSTS = [
    0.10,
    0.25,
    0.50,
    1.00,
    2.00
]


# ============================================================
# ANÁLISIS DE SENSIBILIDAD
# ============================================================

results = []


for waiting_cost in WAITING_COSTS:

    best_servers = None
    best_cost = float("inf")

    for c in range(1, 16):

        metrics = mmc_metrics(
            LAMBDA,
            MU,
            c
        )

        if not metrics["stable"]:
            continue

        server_cost = c * SERVER_COST

        waiting_cost_total = (
            metrics["Lq"]
            * 60
            * waiting_cost
        )

        total_cost = (
            server_cost
            + waiting_cost_total
        )

        if total_cost < best_cost:

            best_cost = total_cost
            best_servers = c

    results.append({
        "waiting_cost": waiting_cost,
        "optimal_servers": best_servers,
        "total_cost": best_cost
    })


# ============================================================
# RESULTADOS
# ============================================================

results_df = pd.DataFrame(results)

print("=" * 70)
print("ANÁLISIS DE SENSIBILIDAD")
print("=" * 70)

print()

print(results_df.to_string(index=False))


# ============================================================
# GRÁFICA
# ============================================================

plt.figure(figsize=(10, 6))

plt.plot(
    results_df["waiting_cost"],
    results_df["optimal_servers"],
    marker="o",
    linewidth=2
)

plt.xlabel(
    "Costo de espera ($/minuto)"
)

plt.ylabel(
    "Número óptimo de servidores"
)

plt.title(
    "Sensibilidad del número óptimo de servidores"
)

plt.grid(alpha=0.3)

plt.tight_layout()

plt.show()