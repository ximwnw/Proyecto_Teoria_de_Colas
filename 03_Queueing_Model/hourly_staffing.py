import matplotlib.pyplot as plt
import pandas as pd

from mmc_model import mmc_metrics


# ============================================================
# Parámetros del modelo
# ============================================================

# Tasa de servicio estimada a partir de los datos.
# Unidad: clientes/hora/servidor.

MU = 12.1233

# Costo de mantener un servidor activo durante una hora.
# Unidad: $/servidor/hora.

SERVER_COST_PER_HOUR = 20

# Costo asociado a un cliente esperando en la cola.
# Unidad: $/cliente/minuto.

WAITING_COST_PER_MINUTE = 0.50


# ============================================================
# Tasas de llegada por hora
# ============================================================

# Tasas promedio de llegada estimadas a partir de los 30 días
# de observaciones.
#
# Unidad: clientes/hora.

ARRIVAL_RATES = {
    8: 21.0,
    9: 28.3,
    10: 33.6333,
    11: 49.1333,
    12: 65.9,
    13: 74.8,
    14: 60.6,
    15: 41.4,
    16: 29.3667,
}


# ============================================================
# Función para calcular el costo total
# ============================================================

def total_cost(lq, c):
    """
    Calcula el costo total por hora de una configuración.

    Parámetros
    ----------
    lq : float
        Número esperado de clientes en la cola.
    c : int
        Número de servidores.

    Retorna
    -------
    float
        Costo total por hora.
    """

    # Costo de servidores:
    #
    # c * costo_por_servidor

    server_cost = c * SERVER_COST_PER_HOUR

    # Costo de espera:
    #
    # Lq [clientes]
    # × 60 [minutos/hora]
    # × costo [$/cliente/minuto]
    #
    # Resultado: $/hora

    waiting_cost = (
        lq
        * 60
        * WAITING_COST_PER_MINUTE
    )

    return server_cost + waiting_cost


# ============================================================
# Análisis de staffing por hora
# ============================================================

def analyze_hour(hour, lam, mu=MU, max_servers=15):
    """
    Analiza las configuraciones de servidores para una hora
    determinada.

    Primero identifica el mínimo número de servidores que
    mantiene estable al sistema.

    Después busca la configuración estable con menor costo total.

    Parámetros
    ----------
    hour : int
        Hora del día.
    lam : float
        Tasa de llegada (clientes/hora).
    mu : float
        Tasa de servicio por servidor (clientes/hora/servidor).
    max_servers : int
        Número máximo de servidores a evaluar.

    Retorna
    -------
    dict
        Resultados principales de staffing para esa hora.
    """

    configurations = []

    # --------------------------------------------------------
    # Evaluar diferentes números de servidores
    # --------------------------------------------------------

    for c in range(1, max_servers + 1):

        # Utilizamos el motor matemático M/M/c.
        metrics = mmc_metrics(
            lam=lam,
            mu=mu,
            c=c
        )

        # Guardamos los resultados de cada configuración.

        configuration = {
            "hour": hour,
            "lambda": lam,
            "servers": c,
            "rho": metrics["rho"],
            "stability": metrics["stability"],
            "Lq": metrics["Lq"],
            "Wq_minutes": metrics["Wq_minutes"],
            "L": metrics["L"],
            "W_minutes": metrics["W_minutes"],
        }

        # Solo calculamos el costo cuando el sistema es estable.
        #
        # Una configuración con rho >= 1 no representa un
        # sistema estable en estado estacionario.

        if metrics["stability"]:
            configuration["total_cost"] = total_cost(
                metrics["Lq"],
                c
            )
        else:
            configuration["total_cost"] = float("inf")

        configurations.append(configuration)

    # Convertimos las configuraciones a DataFrame.

    results = pd.DataFrame(configurations)

    # --------------------------------------------------------
    # Identificar el mínimo número de servidores estable
    # --------------------------------------------------------

    stable_results = results[
        results["stability"]
    ].copy()

    if stable_results.empty:
        raise ValueError(
            f"No se encontró una configuración estable para "
            f"la hora {hour}."
        )

    # El primer servidor que produce rho < 1 es el mínimo
    # número de servidores necesario para estabilidad.

    min_stable_row = stable_results.iloc[0]

    min_stable_servers = int(
        min_stable_row["servers"]
    )

    # --------------------------------------------------------
    # Optimización del costo
    # --------------------------------------------------------

    # Solo consideramos configuraciones desde el mínimo
    # estable hasta max_servers.

    optimization_results = stable_results[
        stable_results["servers"] >= min_stable_servers
    ]

    # Encontramos la configuración con menor costo total.

    optimal_row = optimization_results.loc[
        optimization_results["total_cost"].idxmin()
    ]

    optimal_servers = int(
        optimal_row["servers"]
    )

    # --------------------------------------------------------
    # Resultados principales
    # --------------------------------------------------------

    summary = {
        "hour": hour,
        "lambda": lam,

        # Configuración mínima para estabilidad
        "min_stable_servers": min_stable_servers,
        "min_stable_rho": min_stable_row["rho"],

        # Configuración óptima por costo
        "optimal_servers": optimal_servers,
        "optimal_rho": optimal_row["rho"],
        "optimal_Lq": optimal_row["Lq"],
        "optimal_Wq_minutes": optimal_row["Wq_minutes"],
        "total_cost": optimal_row["total_cost"],
    }

    return summary, results


# ============================================================
# Análisis de todas las horas
# ============================================================

all_summaries = []
all_configurations = []

for hour, lam in ARRIVAL_RATES.items():

    summary, configurations = analyze_hour(
        hour=hour,
        lam=lam,
        mu=MU,
        max_servers=15
    )

    all_summaries.append(summary)
    all_configurations.append(configurations)


# ============================================================
# Construir tablas de resultados
# ============================================================

staffing_results = pd.DataFrame(
    all_summaries
)

configuration_results = pd.concat(
    all_configurations,
    ignore_index=True
)


# ============================================================
# Mostrar resultados principales
# ============================================================

print("\n" + "=" * 70)
print("ANÁLISIS DE STAFFING POR HORA - MODELO M/M/c")
print("=" * 70)

print(
    staffing_results[
        [
            "hour",
            "lambda",
            "min_stable_servers",
            "min_stable_rho",
            "optimal_servers",
            "optimal_rho",
            "optimal_Lq",
            "optimal_Wq_minutes",
            "total_cost",
        ]
    ].to_string(index=False)
)


# ============================================================
# Identificar la hora pico
# ============================================================

peak_hour = staffing_results.loc[
    staffing_results["lambda"].idxmax()
]

print("\n" + "=" * 70)
print("HORA PICO")
print("=" * 70)

print(
    f"Hora pico: {int(peak_hour['hour'])}:00"
)

print(
    f"Tasa de llegada: "
    f"{peak_hour['lambda']:.2f} clientes/hora"
)

print(
    f"Mínimo de servidores para estabilidad: "
    f"{int(peak_hour['min_stable_servers'])}"
)

print(
    f"Servidores óptimos por costo: "
    f"{int(peak_hour['optimal_servers'])}"
)

print(
    f"Utilización con configuración óptima: "
    f"{peak_hour['optimal_rho']:.3f}"
)

print(
    f"Clientes promedio en cola: "
    f"{peak_hour['optimal_Lq']:.3f}"
)

print(
    f"Tiempo promedio de espera: "
    f"{peak_hour['optimal_Wq_minutes']:.3f} minutos"
)

print(
    f"Costo total: "
    f"${peak_hour['total_cost']:.2f}/hora"
)


# ============================================================
# Gráfica 1: Servidores mínimos vs. óptimos
# ============================================================

plt.figure(figsize=(10, 6))

plt.plot(
    staffing_results["hour"],
    staffing_results["min_stable_servers"],
    marker="o",
    label="Mínimo estable"
)

plt.plot(
    staffing_results["hour"],
    staffing_results["optimal_servers"],
    marker="o",
    label="Óptimo por costo"
)

plt.xlabel("Hora")
plt.ylabel("Número de servidores")
plt.title(
    "Servidores mínimos y óptimos por hora"
)

plt.xticks(
    list(ARRIVAL_RATES.keys())
)

plt.grid(True)
plt.legend()
plt.tight_layout()

plt.show()


# ============================================================
# Gráfica 2: Demanda y servidores óptimos
# ============================================================

fig, ax1 = plt.subplots(figsize=(10, 6))

ax1.plot(
    staffing_results["hour"],
    staffing_results["lambda"],
    marker="o",
    label="Tasa de llegada"
)

ax1.set_xlabel("Hora")
ax1.set_ylabel(
    "Tasa de llegada (clientes/hora)"
)

ax1.set_xticks(
    list(ARRIVAL_RATES.keys())
)

ax2 = ax1.twinx()

ax2.plot(
    staffing_results["hour"],
    staffing_results["optimal_servers"],
    marker="o",
    linestyle="--",
    label="Servidores óptimos"
)

ax2.set_ylabel(
    "Servidores óptimos"
)

plt.title(
    "Demanda y número óptimo de servidores"
)

fig.tight_layout()

plt.show()
