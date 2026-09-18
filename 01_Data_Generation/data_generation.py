import numpy as np
import pandas as pd
from pathlib import Path

# ============================================================
# CONFIGURACIÓN
# ============================================================

np.random.seed(42)

NUM_DAYS = 30

# Horario de operación: 8:00 a 17:00
START_HOUR = 8
END_HOUR = 17

# Tasa promedio de llegada por hora (clientes/hora)
ARRIVAL_RATES = {
    8: 20,
    9: 28,
    10: 35,
    11: 48,
    12: 65,
    13: 72,
    14: 60,
    15: 42,
    16: 30
}

# Tiempo promedio de servicio
MEAN_SERVICE_TIME = 5  # minutos


# ============================================================
# GENERACIÓN DE DATOS
# ============================================================

all_customers = []

customer_id = 1

start_date = pd.Timestamp("2026-01-01")


for day in range(NUM_DAYS):

    current_date = start_date + pd.Timedelta(days=day)

    for hour, arrival_rate in ARRIVAL_RATES.items():

        # Número de clientes que llegan durante esta hora
        number_of_customers = np.random.poisson(arrival_rate)

        # Minuto y segundo aleatorio dentro de la hora
        arrival_minutes = np.random.uniform(
            0,
            60,
            number_of_customers
        )

        for minute in arrival_minutes:

            arrival_time = (
                current_date
                + pd.Timedelta(hours=hour)
                + pd.Timedelta(minutes=float(minute))
            )

            # Tiempo de servicio ~ Exponencial
            service_time = np.random.exponential(
                scale=MEAN_SERVICE_TIME
            )

            all_customers.append({
                "customer_id": customer_id,
                "arrival_time": arrival_time,
                "service_time_min": service_time,
                "hour": hour,
                "day_of_week": current_date.day_name()
            })

            customer_id += 1


# ============================================================
# CREAR DATAFRAME
# ============================================================

df = pd.DataFrame(all_customers)


# ============================================================
# ORDENAR DATOS
# ============================================================

df = df.sort_values(
    "arrival_time"
).reset_index(drop=True)


# ============================================================
# CREAR CARPETA DE DATOS
# ============================================================

output_folder = Path("data/raw")

output_folder.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# GUARDAR DATASET
# ============================================================

output_file = output_folder / "customers.csv"

df.to_csv(
    output_file,
    index=False
)


# ============================================================
# RESULTADOS
# ============================================================

print("=" * 60)
print("GENERACIÓN DE DATOS COMPLETADA")
print("=" * 60)

print(f"\nNúmero total de clientes: {len(df):,}")

print(
    f"Periodo: "
    f"{df['arrival_time'].min()} "
    f"hasta "
    f"{df['arrival_time'].max()}"
)

print("\nEstadísticas del tiempo de servicio:")

print(
    df["service_time_min"].describe()
)


print("\nClientes por hora:")

customers_per_hour = (
    df.groupby("hour")
      .size()
)

print(customers_per_hour)


print("\nPromedio de clientes por hora:")

print(
    customers_per_hour / NUM_DAYS
)


print("\nArchivo guardado en:")

print(output_file)