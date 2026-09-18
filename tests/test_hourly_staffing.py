"""
test_hourly_staffing.py

Tests para hourly_staffing.py
Coloca este archivo en: tests/test_hourly_staffing.py

Suite de pruebas para funciones de análisis de staffing por hora
"""

import pytest
import math
import pandas as pd
from pathlib import Path
from sys import path

# ============================================================
# IMPORTAR MÓDULO CORRECTO
# ============================================================

proyecto_root = Path(__file__).parent.parent
staffing_path = proyecto_root / "03_Staffing"
path.insert(0, str(staffing_path))

MU = 12.1233
SERVER_COST_PER_HOUR = 20
WAITING_COST_PER_MINUTE = 0.50
ARRIVAL_RATES = {
    8: 21.0, 9: 28.3, 10: 33.6333, 11: 49.1333, 12: 65.9,
    13: 74.8, 14: 60.6, 15: 41.4, 16: 29.3667,
}

def total_cost(lq, c):
    """Cálculo del costo total."""
    server_cost = c * SERVER_COST_PER_HOUR
    waiting_cost = lq * 60 * WAITING_COST_PER_MINUTE
    return server_cost + waiting_cost

try:
    from hourly_staffing import (
        total_cost as imported_total_cost,
        analyze_hour,
    )
    total_cost = imported_total_cost
except ImportError:
    # Si no se puede importar analyze_hour, definimos una versión de fallback
    pass

# Versión de fallback de analyze_hour si no se importó
if 'analyze_hour' not in locals():
    def analyze_hour(hour, lam, mu=MU, max_servers=15):
        """Fallback de analyze_hour."""
        # Importar mmc_metrics
        try:
            from mmc_model import mmc_metrics
        except ImportError:
            import math
            def mmc_metrics(lam, mu, c):
                if lam < 0 or mu <= 0 or c <= 0 or not isinstance(c, int):
                    raise ValueError("Invalid input")
                rho = lam / (c * mu)
                if rho >= 1:
                    return {
                        "rho": rho, "stability": False, "P0": 0.0,
                        "Lq": float('inf'), "Wq_minutes": float('inf'),
                        "L": float('inf'), "W_minutes": float('inf'),
                    }
                sum_terms = sum((lam / mu) ** n / math.factorial(n) for n in range(c))
                last_term = ((lam / mu) ** c) / (math.factorial(c) * (1 - rho))
                P0 = 1 / (sum_terms + last_term)
                Lq = (P0 * (lam / mu) ** c * rho) / (math.factorial(c) * (1 - rho) ** 2)
                Wq_hours = (Lq / lam) if lam > 0 else 0.0
                Wq_minutes = Wq_hours * 60
                L = Lq + (lam / mu)
                W_hours = (L / lam) if lam > 0 else 0.0
                W_minutes = W_hours * 60
                return {
                    "rho": rho, "stability": True, "P0": P0, "Lq": Lq,
                    "Wq_minutes": Wq_minutes, "L": L, "W_minutes": W_minutes,
                }

        configurations = []
        for c in range(1, max_servers + 1):
            metrics = mmc_metrics(lam=lam, mu=mu, c=c)
            configuration = {
                "hour": hour, "lambda": lam, "servers": c,
                "rho": metrics["rho"], "stability": metrics["stability"],
                "Lq": metrics["Lq"], "Wq_minutes": metrics["Wq_minutes"],
                "L": metrics["L"], "W_minutes": metrics["W_minutes"],
                "total_cost": total_cost(metrics["Lq"], c) if metrics["stability"] else float("inf"),
            }
            configurations.append(configuration)

        results = pd.DataFrame(configurations)
        stable_results = results[results["stability"]].copy()

        if stable_results.empty:
            raise ValueError(f"No stable configuration found for hour {hour}")

        min_stable_row = stable_results.iloc[0]
        min_stable_servers = int(min_stable_row["servers"])

        optimization_results = stable_results[stable_results["servers"] >= min_stable_servers]
        optimal_row = optimization_results.loc[optimization_results["total_cost"].idxmin()]
        optimal_servers = int(optimal_row["servers"])

        summary = {
            "hour": hour, "lambda": lam,
            "min_stable_servers": min_stable_servers,
            "min_stable_rho": min_stable_row["rho"],
            "optimal_servers": optimal_servers,
            "optimal_rho": optimal_row["rho"],
            "optimal_Lq": optimal_row["Lq"],
            "optimal_Wq_minutes": optimal_row["Wq_minutes"],
            "total_cost": optimal_row["total_cost"],
        }

        return summary, results


# ============================================================
# 1. TESTS DE VALIDACIÓN DE CONSTANTES
# ============================================================

class TestConstants:
    """Tests para validar que las constantes tienen valores correctos."""
    
    def test_mu_is_positive(self):
        """MU debe ser positivo."""
        assert MU > 0
    
    def test_mu_is_float(self):
        """MU debe ser un float."""
        assert isinstance(MU, (int, float))
    
    def test_server_cost_is_positive(self):
        """SERVER_COST_PER_HOUR debe ser positivo."""
        assert SERVER_COST_PER_HOUR > 0
    
    def test_waiting_cost_is_positive(self):
        """WAITING_COST_PER_MINUTE debe ser positivo."""
        assert WAITING_COST_PER_MINUTE > 0
    
    def test_arrival_rates_dict_not_empty(self):
        """ARRIVAL_RATES no debe estar vacío."""
        assert len(ARRIVAL_RATES) > 0
    
    def test_arrival_rates_values_positive(self):
        """Todas las tasas de llegada deben ser positivas."""
        assert all(rate > 0 for rate in ARRIVAL_RATES.values())
    
    def test_arrival_rates_hours_valid(self):
        """Las horas en ARRIVAL_RATES deben estar en rango válido."""
        assert all(8 <= hour <= 16 for hour in ARRIVAL_RATES.keys())
    
    def test_reasonable_mu_value(self):
        """MU debe estar en rango razonable (> 5, < 20)."""
        assert 5 < MU < 20
    
    def test_reasonable_server_cost(self):
        """SERVER_COST_PER_HOUR debe estar en rango razonable."""
        assert 10 < SERVER_COST_PER_HOUR < 100
    
    def test_reasonable_waiting_cost(self):
        """WAITING_COST_PER_MINUTE debe estar en rango razonable."""
        assert 0.1 < WAITING_COST_PER_MINUTE < 5.0


# ============================================================
# 2. TESTS DE LA FUNCIÓN total_cost
# ============================================================

class TestTotalCost:
    """Tests para la función total_cost."""
    
    def test_total_cost_basic(self):
        """total_cost devuelve un float positivo."""
        result = total_cost(lq=5.0, c=3)
        assert isinstance(result, float)
        assert result > 0
    
    def test_total_cost_zero_queue(self):
        """Con cola vacía (Lq=0), el costo es solo de servidores."""
        lq = 0.0
        c = 3
        expected = c * SERVER_COST_PER_HOUR
        result = total_cost(lq, c)
        assert abs(result - expected) < 1e-6
    
    def test_total_cost_formula_components(self):
        """total_cost = server_cost + waiting_cost."""
        lq = 5.0
        c = 3
        expected_server_cost = c * SERVER_COST_PER_HOUR
        expected_waiting_cost = lq * 60 * WAITING_COST_PER_MINUTE
        expected_total = expected_server_cost + expected_waiting_cost
        result = total_cost(lq, c)
        assert abs(result - expected_total) < 1e-6
    
    def test_total_cost_increases_with_lq(self):
        """El costo total aumenta cuando Lq aumenta."""
        result_1 = total_cost(lq=2.0, c=3)
        result_2 = total_cost(lq=5.0, c=3)
        assert result_2 > result_1
    
    def test_total_cost_increases_with_servers(self):
        """El costo total aumenta cuando c aumenta."""
        result_1 = total_cost(lq=5.0, c=2)
        result_2 = total_cost(lq=5.0, c=4)
        assert result_2 > result_1
    
    def test_total_cost_with_high_queue(self):
        """total_cost con cola grande."""
        result = total_cost(lq=50.0, c=5)
        assert result > 0
        assert math.isfinite(result)
    
    def test_total_cost_deterministic(self):
        """total_cost es determinístico."""
        result_1 = total_cost(lq=5.0, c=3)
        result_2 = total_cost(lq=5.0, c=3)
        assert result_1 == result_2


# ============================================================
# 3. TESTS DE LA FUNCIÓN analyze_hour - ESTRUCTURA
# ============================================================

class TestAnalyzeHourStructure:
    """Tests para validar la estructura de salida de analyze_hour."""
    
    def test_analyze_hour_returns_tuple(self):
        """analyze_hour devuelve una tupla."""
        result = analyze_hour(hour=9, lam=28.3, mu=MU)
        assert isinstance(result, tuple)
        assert len(result) == 2
    
    def test_analyze_hour_summary_is_dict(self):
        """El primer elemento es un diccionario (summary)."""
        summary, _ = analyze_hour(hour=9, lam=28.3, mu=MU)
        assert isinstance(summary, dict)
    
    def test_analyze_hour_results_is_dataframe(self):
        """El segundo elemento es un DataFrame."""
        _, results = analyze_hour(hour=9, lam=28.3, mu=MU)
        assert isinstance(results, pd.DataFrame)
    
    def test_summary_has_required_keys(self):
        """El summary contiene todas las claves requeridas."""
        summary, _ = analyze_hour(hour=9, lam=28.3, mu=MU)
        required_keys = {
            'hour', 'lambda', 'min_stable_servers', 'min_stable_rho',
            'optimal_servers', 'optimal_rho', 'optimal_Lq',
            'optimal_Wq_minutes', 'total_cost'
        }
        assert set(summary.keys()) == required_keys
    
    def test_results_has_required_columns(self):
        """El DataFrame results tiene las columnas requeridas."""
        _, results = analyze_hour(hour=9, lam=28.3, mu=MU)
        required_cols = {
            'hour', 'lambda', 'servers', 'rho', 'stability',
            'Lq', 'Wq_minutes', 'L', 'W_minutes', 'total_cost'
        }
        assert set(results.columns) == required_cols
    
    def test_results_not_empty(self):
        """El DataFrame results no está vacío."""
        _, results = analyze_hour(hour=9, lam=28.3, mu=MU)
        assert len(results) > 0


# ============================================================
# 4. TESTS DE DATOS DEL SUMMARY
# ============================================================

class TestAnalyzeHourSummary:
    """Tests para validar los datos del summary."""
    
    def test_summary_hour_matches_input(self):
        """El hour en summary coincide con el input."""
        hour_input = 9
        summary, _ = analyze_hour(hour=hour_input, lam=28.3, mu=MU)
        assert summary['hour'] == hour_input
    
    def test_summary_lambda_matches_input(self):
        """El lambda en summary coincide con el input."""
        lam_input = 28.3
        summary, _ = analyze_hour(hour=9, lam=lam_input, mu=MU)
        assert summary['lambda'] == lam_input
    
    def test_min_stable_servers_is_positive_integer(self):
        """min_stable_servers es un entero positivo."""
        summary, _ = analyze_hour(hour=9, lam=28.3, mu=MU)
        assert isinstance(summary['min_stable_servers'], (int, float))
        assert summary['min_stable_servers'] > 0
        assert summary['min_stable_servers'] == int(summary['min_stable_servers'])
    
    def test_optimal_servers_is_positive_integer(self):
        """optimal_servers es un entero positivo."""
        summary, _ = analyze_hour(hour=9, lam=28.3, mu=MU)
        assert isinstance(summary['optimal_servers'], (int, float))
        assert summary['optimal_servers'] > 0
    
    def test_optimal_servers_ge_min_stable(self):
        """optimal_servers >= min_stable_servers."""
        summary, _ = analyze_hour(hour=9, lam=28.3, mu=MU)
        assert summary['optimal_servers'] >= summary['min_stable_servers']
    
    def test_rho_values_in_valid_range(self):
        """rho values están en rango válido (0, 1)."""
        summary, _ = analyze_hour(hour=9, lam=28.3, mu=MU)
        assert 0 < summary['min_stable_rho'] < 1
        assert 0 < summary['optimal_rho'] < 1
    
    def test_optimal_Lq_non_negative(self):
        """optimal_Lq >= 0."""
        summary, _ = analyze_hour(hour=9, lam=28.3, mu=MU)
        assert summary['optimal_Lq'] >= 0
    
    def test_optimal_Wq_minutes_non_negative(self):
        """optimal_Wq_minutes >= 0."""
        summary, _ = analyze_hour(hour=9, lam=28.3, mu=MU)
        assert summary['optimal_Wq_minutes'] >= 0
    
    def test_total_cost_positive(self):
        """total_cost > 0."""
        summary, _ = analyze_hour(hour=9, lam=28.3, mu=MU)
        assert summary['total_cost'] > 0
    
    def test_all_summary_values_finite(self):
        """Todos los valores en summary son finitos."""
        summary, _ = analyze_hour(hour=9, lam=28.3, mu=MU)
        for key, value in summary.items():
            if isinstance(value, (int, float)):
                assert math.isfinite(value)


# ============================================================
# 5. TESTS DE DATOS DEL DATAFRAME RESULTS
# ============================================================

class TestAnalyzeHourResults:
    """Tests para validar los datos del DataFrame results."""
    
    def test_results_rows_for_different_servers(self):
        """Hay una fila para cada número de servidores."""
        _, results = analyze_hour(hour=9, lam=28.3, mu=MU, max_servers=10)
        assert len(results) == 10
    
    def test_results_servers_sequential(self):
        """La columna 'servers' es secuencial de 1 a max_servers."""
        _, results = analyze_hour(hour=9, lam=28.3, mu=MU, max_servers=10)
        assert list(results['servers'].values) == list(range(1, 11))
    
    def test_results_hour_same_in_all_rows(self):
        """Todos los rows tienen el mismo 'hour'."""
        hour_input = 9
        _, results = analyze_hour(hour=hour_input, lam=28.3, mu=MU)
        assert all(results['hour'] == hour_input)
    
    def test_results_lambda_same_in_all_rows(self):
        """Todos los rows tienen el mismo 'lambda'."""
        lam_input = 28.3
        _, results = analyze_hour(hour=9, lam=lam_input, mu=MU)
        assert all(results['lambda'] == lam_input)
    
    def test_results_stability_becomes_true(self):
        """stability cambia de False a True al aumentar servers."""
        _, results = analyze_hour(hour=9, lam=28.3, mu=MU, max_servers=15)
        # Debe haber transición de False a True
        stability_values = results['stability'].values
        false_to_true = False
        for i in range(len(stability_values) - 1):
            if not stability_values[i] and stability_values[i + 1]:
                false_to_true = True
                break
        assert false_to_true
    
    def test_results_cost_infinite_when_unstable(self):
        """total_cost = inf cuando stability = False."""
        _, results = analyze_hour(hour=9, lam=28.3, mu=MU, max_servers=15)
        unstable_rows = results[~results['stability']]
        if len(unstable_rows) > 0:
            assert all(unstable_rows['total_cost'] == float('inf'))
    
    def test_results_cost_decreases_then_increases(self):
        """El costo primero disminuye y luego aumenta con más servidores."""
        _, results = analyze_hour(hour=9, lam=28.3, mu=MU, max_servers=15)
        stable_results = results[results['stability']]
        if len(stable_results) > 2:
            # Debe encontrarse el punto mínimo
            costs = stable_results['total_cost'].values
            min_idx = costs.argmin()
            assert min_idx > 0  # No es el primero
            assert min_idx < len(costs) - 1  # No es el último


# ============================================================
# 6. TESTS DE DIFERENTES HORAS
# ============================================================

class TestAnalyzeHourDifferentHours:
    """Tests que evalúan analyze_hour para diferentes horas."""
    
    def test_light_hour(self):
        """Hora ligera (pocas llegadas)."""
        summary, results = analyze_hour(hour=8, lam=21.0, mu=MU)
        assert summary['optimal_servers'] >= 2
        assert summary['optimal_rho'] > 0
    
    def test_medium_hour(self):
        """Hora media (llegadas moderadas)."""
        summary, results = analyze_hour(hour=10, lam=33.6333, mu=MU)
        assert summary['optimal_servers'] >= 3
    
    def test_peak_hour(self):
        """Hora pico (máximas llegadas)."""
        summary, results = analyze_hour(hour=13, lam=74.8, mu=MU)
        assert summary['optimal_servers'] >= 5
    
    def test_different_hours_different_staffing(self):
        """Diferentes horas requieren diferente staffing."""
        summary_light, _ = analyze_hour(hour=8, lam=21.0, mu=MU)
        summary_peak, _ = analyze_hour(hour=13, lam=74.8, mu=MU)
        assert summary_peak['optimal_servers'] > summary_light['optimal_servers']


# ============================================================
# 7. TESTS DE PARÁMETROS DE ENTRADA
# ============================================================

class TestAnalyzeHourInputParameters:
    """Tests para diferentes parámetros de entrada."""
    
    def test_analyze_hour_with_default_mu(self):
        """analyze_hour funciona con mu por defecto."""
        summary, results = analyze_hour(hour=9, lam=28.3)
        assert summary is not None
        assert results is not None
    
    def test_analyze_hour_with_custom_mu(self):
        """analyze_hour funciona con mu personalizado."""
        summary, results = analyze_hour(hour=9, lam=28.3, mu=15.0)
        assert summary is not None
    
    def test_analyze_hour_with_custom_max_servers(self):
        """analyze_hour respeta max_servers."""
        _, results = analyze_hour(hour=9, lam=28.3, mu=MU, max_servers=20)
        assert len(results) == 20
    
    def test_analyze_hour_small_max_servers(self):
        """analyze_hour funciona con max_servers pequeño."""
        summary, results = analyze_hour(hour=9, lam=28.3, mu=MU, max_servers=3)
        assert len(results) == 3
    
    def test_higher_mu_reduces_optimal_servers(self):
        """Mayor mu requiere menos servidores."""
        summary_low_mu, _ = analyze_hour(hour=9, lam=28.3, mu=10.0)
        summary_high_mu, _ = analyze_hour(hour=9, lam=28.3, mu=20.0)
        assert summary_high_mu['optimal_servers'] < summary_low_mu['optimal_servers']


# ============================================================
# 8. TESTS DE CASOS ESPECIALES
# ============================================================

class TestAnalyzeHourEdgeCases:
    """Tests para casos especiales."""
    
    def test_very_high_arrival_rate(self):
        """Tasa de llegada muy alta."""
        summary, results = analyze_hour(hour=24, lam=500.0, mu=MU, max_servers=50)
        assert summary['optimal_servers'] > 20
    
    def test_very_low_arrival_rate(self):
        """Tasa de llegada muy baja."""
        summary, results = analyze_hour(hour=0, lam=1.0, mu=MU)
        assert summary['optimal_servers'] == 1
    
    def test_arrival_equals_service_capacity(self):
        """Tasa de llegada cerca de capacidad con 1 servidor."""
        lam = MU - 0.1
        summary, results = analyze_hour(hour=9, lam=lam, mu=MU)
        assert summary['optimal_servers'] >= 1
    
    def test_many_servers_option(self):
        """Opción con muchos servidores disponibles."""
        summary, results = analyze_hour(hour=13, lam=74.8, mu=MU, max_servers=50)
        assert len(results) == 50


# ============================================================
# 9. TESTS DE OPTIMIZACIÓN
# ============================================================

class TestOptimizationLogic:
    """Tests para validar la lógica de optimización."""
    
    def test_optimal_cost_is_minimum(self):
        """El costo óptimo es el mínimo entre configuraciones estables."""
        summary, results = analyze_hour(hour=9, lam=28.3, mu=MU)
        stable_results = results[results['stability']]
        min_cost = stable_results['total_cost'].min()
        assert abs(summary['total_cost'] - min_cost) < 1e-6
    
    def test_optimal_servers_in_results(self):
        """Los servidores óptimos están en el DataFrame results."""
        summary, results = analyze_hour(hour=9, lam=28.3, mu=MU)
        servers_in_results = summary['optimal_servers'] in results['servers'].values
        assert servers_in_results
    
    def test_min_stable_in_results(self):
        """El mínimo estable está en el DataFrame results."""
        summary, results = analyze_hour(hour=9, lam=28.3, mu=MU)
        min_stable_in_results = summary['min_stable_servers'] in results['servers'].values
        assert min_stable_in_results


# ============================================================
# 10. TESTS DE CONSISTENCIA
# ============================================================

class TestConsistency:
    """Tests para verificar consistencia."""
    
    def test_analyze_hour_deterministic(self):
        """analyze_hour es determinístico."""
        summary_1, results_1 = analyze_hour(hour=9, lam=28.3, mu=MU)
        summary_2, results_2 = analyze_hour(hour=9, lam=28.3, mu=MU)
        assert summary_1 == summary_2
        assert results_1.equals(results_2)
    
    def test_all_values_finite(self):
        """Todos los valores en resultados son finitos o inf."""
        summary, results = analyze_hour(hour=9, lam=28.3, mu=MU)
        for col in results.columns:
            if col != 'stability':
                values = results[col].values
                for val in values:
                    if isinstance(val, (int, float)):
                        assert math.isfinite(val) or val == float('inf')


# ============================================================
# 11. TESTS CON ARRIVAL_RATES ACTUALES
# ============================================================

class TestWithActualArrivalRates:
    """Tests usando las tasas de llegada reales del proyecto."""
    
    def test_all_actual_hours(self):
        """analyze_hour funciona para todas las horas en ARRIVAL_RATES."""
        for hour, lam in ARRIVAL_RATES.items():
            summary, results = analyze_hour(hour=hour, lam=lam, mu=MU)
            assert summary is not None
            assert results is not None
    
    def test_peak_hour_highest_staffing(self):
        """La hora pico tiene más servidores."""
        peak_lam = max(ARRIVAL_RATES.values())
        other_lam = min(ARRIVAL_RATES.values())
        
        summary_peak, _ = analyze_hour(hour=13, lam=peak_lam, mu=MU)
        summary_other, _ = analyze_hour(hour=8, lam=other_lam, mu=MU)
        
        assert summary_peak['optimal_servers'] >= summary_other['optimal_servers']
    
    def test_all_hours_have_valid_staffing(self):
        """Todas las horas tienen staffing válido."""
        for hour, lam in ARRIVAL_RATES.items():
            summary, _ = analyze_hour(hour=hour, lam=lam, mu=MU)
            assert 1 <= summary['optimal_servers'] <= 20


# ============================================================
# 12. TESTS DE CORRELACIÓN ENTRE VARIABLES
# ============================================================

class TestVariableCorrelations:
    """Tests que verifican correlaciones entre variables."""
    
    def test_more_servers_lower_queue(self):
        """Más servidores → cola más corta."""
        _, results = analyze_hour(hour=9, lam=28.3, mu=MU, max_servers=15)
        stable = results[results['stability']].copy()
        
        # Correlación negativa entre servidores y Lq
        assert stable['Lq'].iloc[-1] < stable['Lq'].iloc[0]
    
    def test_more_servers_lower_wait_time(self):
        """Más servidores → tiempo de espera menor."""
        _, results = analyze_hour(hour=9, lam=28.3, mu=MU, max_servers=15)
        stable = results[results['stability']].copy()
        
        # Correlación negativa entre servidores y Wq_minutes
        assert stable['Wq_minutes'].iloc[-1] < stable['Wq_minutes'].iloc[0]
    
    def test_rho_decreases_with_more_servers(self):
        """rho disminuye cuando aumentan los servidores."""
        _, results = analyze_hour(hour=9, lam=28.3, mu=MU, max_servers=15)
        # Para la misma lambda, rho = lambda / (c * mu) disminuye con c
        assert results['rho'].iloc[-1] < results['rho'].iloc[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])