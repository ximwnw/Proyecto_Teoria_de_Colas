"""
Módulo M/M/c - Modelo de Teoría de Colas

Este módulo implementa el modelo M/M/c (Markovian arrivals, Markovian service times,
c servers) de la teoría de colas. Calcula métricas clave del sistema de colas como
utilización (ρ), probabilidad de sistema vacío (P0), longitud de cola (Lq),
y tiempos de espera (Wq, W).

Ecuaciones matemáticas implementadas:
    ρ = λ / (c * μ)  - Factor de utilización
    P0 = 1 / (Σ(λ/μ)^n / n! + (λ/μ)^c / (c!(1-ρ)))  - Probabilidad de sistema vacío
    Lq = P0 * (λ/μ)^c * ρ / (c! * (1-ρ)^2)  - Longitud promedio de cola
    Wq = Lq / λ  - Tiempo promedio en cola
    L = Lq + λ/μ  - Longitud promedio del sistema
    W = L / λ  - Tiempo promedio en sistema

Referencias:
    - Gross, D., & Harris, C. M. (2008). Fundamentals of Queueing Theory
    - Kleinrock, L. (1975). Queueing Systems, Volume 1: Theory
"""

import math
from typing import Dict, Union, Tuple


def mmc_metrics(
    lam: float,
    mu: float,
    c: int
) -> Dict[str, Union[float, bool]]:
    """
    Calcula las métricas de un sistema de colas M/M/c.

    Parámetros:
    -----------
    lam : float
        Tasa de llegada (lambda) en clientes por hora.
        Representa el número promedio de clientes que llegan por unidad de tiempo.
        Condición: lam >= 0

    mu : float
        Tasa de servicio (mu) por servidor en clientes por hora.
        Representa cuántos clientes puede atender un servidor por unidad de tiempo.
        Condición: mu > 0

    c : int
        Número de servidores en el sistema.
        Representa la capacidad paralela del sistema.
        Condición: c > 0 y c es entero

    Retorna:
    --------
    Dict con las siguientes claves:

        'rho' : float
            Factor de utilización del sistema: ρ = λ / (c * μ)
            Rango: [0, ∞)
            Interpretación:
                - ρ < 1: Sistema estable (cola finita)
                - ρ = 1: Límite crítico (cola tiende a infinito)
                - ρ > 1: Sistema inestable (cola crece infinitamente)

        'stability' : bool
            True si el sistema es estable (ρ < 1), False si es inestable (ρ >= 1)

        'P0' : float
            Probabilidad de que el sistema esté vacío.
            Rango: (0, 1] si estable, 0 si inestable.
            Interpretación: Porcentaje de tiempo en que no hay clientes.

        'Lq' : float
            Longitud promedio de la cola (sin contar en servicio).
            Rango: [0, ∞)
            Interpretación: Número esperado de clientes esperando.

        'Wq_minutes' : float
            Tiempo promedio de espera en cola en minutos.
            Rango: [0, ∞)
            Interpretación: Cuánto tiempo espera un cliente antes de ser servido.

        'L' : float
            Longitud promedio del sistema (en cola + en servicio).
            Rango: [0, ∞)
            Interpretación: Número total esperado de clientes en el sistema.

        'W_minutes' : float
            Tiempo promedio en el sistema (espera + servicio) en minutos.
            Rango: [0, ∞)
            Interpretación: Tiempo total que un cliente pasa en el sistema.

    Raises:
    -------
    ValueError
        Si alguno de los parámetros viola las condiciones.

        - "lambda must be non-negative." si lam < 0
        - "mu must be greater than zero." si mu <= 0
        - "servers must be a positive integer." si c <= 0 o c no es entero

    Ejemplos:
    ---------
    >>> # Sistema M/M/4: 40 clientes/hora, 12 servidores/hora, 4 servidores
    >>> resultado = mmc_metrics(40, 12, 4)
    >>> print(f"Utilización: {resultado['rho']:.2%}")
    >>> print(f"Tiempo en cola: {resultado['Wq_minutes']:.2f} minutos")

    >>> # Sistema M/M/1 (un servidor)
    >>> resultado = mmc_metrics(10, 15, 1)
    >>> print(f"Clientes en sistema: {resultado['L']:.2f}")

    Notas:
    ------
    1. Sistema Estable: Solo si ρ < 1 el sistema alcanza un estado estacionario.

    2. Relaciones importantes:
       - L = Lq + λ/μ (clientes en sistema = en cola + en servicio)
       - W = Wq + 1/μ (tiempo total = espera + servicio)
       - Wq = Lq / λ (Little's Law)

    3. Interpretación práctica:
       - Si ρ → 1, Wq y Lq → ∞ (sistema muy congestionado)
       - Si ρ → 0, Wq y Lq → 0 (sistema poco utilizado)

    4. Complejidad: O(c) por el cálculo de P0 (suma hasta c términos)
    """

    # ==================== VALIDACIÓN DE INPUTS ====================
    if lam < 0:
        raise ValueError("lambda must be non-negative.")
    if mu <= 0:
        raise ValueError("mu must be greater than zero.")
    if c <= 0 or not isinstance(c, int):
        raise ValueError("servers must be a positive integer.")

    # ==================== CÁLCULO DE UTILIZACIÓN ====================
    # ρ = λ / (c * μ)
    rho = lam / (c * mu)

    # ==================== VERIFICACIÓN DE ESTABILIDAD ====================
    # Sistema estable solo si ρ < 1
    if rho >= 1:
        # Sistema inestable: retornar infinitos
        return {
            "rho": rho,
            "stability": False,
            "P0": 0.0,
            "Lq": float('inf'),
            "Wq_minutes": float('inf'),
            "L": float('inf'),
            "W_minutes": float('inf'),
        }

    # ==================== CÁLCULO DE P0 (Erlang C) ====================
    # P0 = 1 / (Σ_{n=0}^{c-1} (λ/μ)^n / n! + (λ/μ)^c / (c! * (1-ρ)))

    # Primer término: suma de 0 a c-1
    sum_terms = sum((lam / mu) ** n / math.factorial(n) for n in range(c))

    # Segundo término: (λ/μ)^c / (c! * (1-ρ))
    last_term = ((lam / mu) ** c) / (math.factorial(c) * (1 - rho))

    # P0 final
    P0 = 1 / (sum_terms + last_term)

    # ==================== CÁLCULO DE Lq (Longitud de Cola) ====================
    # Lq = P0 * (λ/μ)^c * ρ / (c! * (1-ρ)^2)
    Lq = (P0 * (lam / mu) ** c * rho) / (math.factorial(c) * (1 - rho) ** 2)

    # ==================== CÁLCULO DE TIEMPOS DE ESPERA ====================
    # Wq = Lq / λ (convertir a minutos)
    if lam > 0:
        Wq_hours = Lq / lam
        Wq_minutes = Wq_hours * 60
    else:
        # Si no hay llegadas, no hay espera
        Wq_minutes = 0.0

    # ==================== CÁLCULO DE MÉTRICAS DEL SISTEMA ====================
    # L = Lq + λ/μ (Little's Law)
    L = Lq + (lam / mu)

    # W = L / λ (convertir a minutos)
    if lam > 0:
        W_hours = L / lam
        W_minutes = W_hours * 60
    else:
        W_minutes = 0.0

    # ==================== RETORNO DE RESULTADOS ====================
    return {
        "rho": rho,
        "stability": True,
        "P0": P0,
        "Lq": Lq,
        "Wq_minutes": Wq_minutes,
        "L": L,
        "W_minutes": W_minutes,
    }


def mmc_metrics_batch(
    parameters: list
) -> list:
    """
    Calcula métricas para múltiples configuraciones de M/M/c.

    Parámetros:
    -----------
    parameters : list[tuple]
        Lista de tuplas (lam, mu, c) para calcular.

    Retorna:
    --------
    list[dict]
        Lista de resultados, uno por cada configuración.

    Ejemplo:
    --------
    >>> configs = [(10, 5, 2), (20, 5, 3), (15, 5, 4)]
    >>> resultados = mmc_metrics_batch(configs)
    >>> for r in resultados:
    ...     print(f"ρ = {r['rho']:.2f}, Wq = {r['Wq_minutes']:.2f} min")
    """
    return [mmc_metrics(lam, mu, c) for lam, mu, c in parameters]


def calculate_optimal_servers(
    lam: float,
    mu: float,
    max_wait_minutes: float,
    cost_per_server: float = 20.0,
    cost_per_wait_minute: float = 0.5
) -> Tuple[int, Dict]:
    """
    Encuentra el número óptimo de servidores minimizando costo total.

    Parámetros:
    -----------
    lam : float
        Tasa de llegada
    mu : float
        Tasa de servicio por servidor
    max_wait_minutes : float
        Tiempo máximo aceptable de espera
    cost_per_server : float
        Costo por hora de un servidor
    cost_per_wait_minute : float
        Costo por minuto de tiempo de espera del cliente

    Retorna:
    --------
    tuple (servers_optimo, resultado_optimo)
        Número óptimo de servidores y sus métricas.

    Ejemplo:
    --------
    >>> servers, metrics = calculate_optimal_servers(40, 12, 5)
    >>> print(f"Servidores óptimos: {servers}")
    """
    best_cost = float('inf')
    best_servers = 1
    best_result = None

    # Probar de 1 a 20 servidores
    for c in range(1, 21):
        result = mmc_metrics(lam, mu, c)

        if result['stability'] and result['Wq_minutes'] <= max_wait_minutes:
            # Calcular costo total
            total_cost = (c * cost_per_server) + (result['Lq'] * 60 * cost_per_wait_minute)

            if total_cost < best_cost:
                best_cost = total_cost
                best_servers = c
                best_result = result

    return best_servers, best_result
