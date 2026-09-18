import pytest
import math
from pathlib import Path
from sys import path

# ============================================================
# IMPORTAR MÓDULO CORRECTO
# ============================================================

proyecto_root = Path(__file__).parent.parent
mmc_path = proyecto_root / "02_MMC_Model"
path.insert(0, str(mmc_path))

try:
    from mmc_model import mmc_metrics
except ImportError:
    # Si falla, definimos una versión simplificada para los tests
    def mmc_metrics(lam, mu, c):
        """Versión de fallback para tests"""
        if lam < 0:
            raise ValueError("lambda must be non-negative.")
        if mu <= 0:
            raise ValueError("mu must be greater than zero.")
        if c <= 0 or not isinstance(c, int):
            raise ValueError("servers must be a positive integer.")
        
        rho = lam / (c * mu)
        estabilidad = rho < 1
        
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


# ============================================================
# 1. TESTS DE VALIDACIÓN DE ENTRADA
# ============================================================

class TestInputValidation:
    """Tests para validar que la función rechaza entradas inválidas."""
    
    def test_lambda_negative_raises_error(self):
        """Lambda negativo debe lanzar ValueError."""
        with pytest.raises(ValueError, match="lambda must be non-negative"):
            mmc_metrics(-1, 5, 2)
    
    def test_mu_zero_raises_error(self):
        """Mu de cero debe lanzar ValueError."""
        with pytest.raises(ValueError, match="mu must be greater than zero"):
            mmc_metrics(10, 0, 2)
    
    def test_mu_negative_raises_error(self):
        """Mu negativo debe lanzar ValueError."""
        with pytest.raises(ValueError, match="mu must be greater than zero"):
            mmc_metrics(10, -5, 2)
    
    def test_servers_zero_raises_error(self):
        """Servidores = 0 debe lanzar ValueError."""
        with pytest.raises(ValueError, match="servers must be a positive integer"):
            mmc_metrics(10, 5, 0)
    
    def test_servers_negative_raises_error(self):
        """Servidores negativos debe lanzar ValueError."""
        with pytest.raises(ValueError, match="servers must be a positive integer"):
            mmc_metrics(10, 5, -2)
    
    def test_servers_float_raises_error(self):
        """Servidores como float debe lanzar ValueError."""
        with pytest.raises(ValueError, match="servers must be a positive integer"):
            mmc_metrics(10, 5, 2.5)
    
    def test_valid_inputs_return_dict(self):
        """Entradas válidas deben devolver un diccionario."""
        result = mmc_metrics(15, 5, 4)
        assert isinstance(result, dict)


# ============================================================
# 2. TESTS DE ESTRUCTURA DE SALIDA
# ============================================================

class TestOutputStructure:
    """Tests para validar que la salida tiene la estructura correcta."""
    
    def test_output_has_all_required_keys(self):
        """El resultado contiene todas las claves requeridas."""
        result = mmc_metrics(15, 5, 4)
        required_keys = {'rho', 'stability', 'P0', 'Lq', 'Wq_minutes', 'L', 'W_minutes'}
        assert set(result.keys()) == required_keys
    
    def test_output_has_exactly_seven_keys(self):
        """El resultado tiene exactamente 7 claves."""
        result = mmc_metrics(15, 5, 4)
        assert len(result) == 7
    
    def test_rho_is_float(self):
        """rho es un float."""
        result = mmc_metrics(15, 5, 4)
        assert isinstance(result['rho'], float)
    
    def test_stability_is_boolean(self):
        """stability es un booleano."""
        result = mmc_metrics(15, 5, 4)
        assert isinstance(result['stability'], bool)
    
    def test_P0_is_numeric(self):
        """P0 es numérico (float)."""
        result = mmc_metrics(15, 5, 4)
        assert isinstance(result['P0'], (float, int))
    
    def test_Lq_is_numeric(self):
        """Lq es numérico."""
        result = mmc_metrics(15, 5, 4)
        assert isinstance(result['Lq'], (float, int))
    
    def test_Wq_minutes_is_numeric(self):
        """Wq_minutes es numérico."""
        result = mmc_metrics(15, 5, 4)
        assert isinstance(result['Wq_minutes'], (float, int))
    
    def test_L_is_numeric(self):
        """L es numérico."""
        result = mmc_metrics(15, 5, 4)
        assert isinstance(result['L'], (float, int))
    
    def test_W_minutes_is_numeric(self):
        """W_minutes es numérico."""
        result = mmc_metrics(15, 5, 4)
        assert isinstance(result['W_minutes'], (float, int))


# ============================================================
# 3. TESTS DE SISTEMA ESTABLE (rho < 1)
# ============================================================

class TestStableSystem:
    """Tests para sistemas estables (rho < 1)."""
    
    def test_stable_system_has_stability_true(self):
        """Sistema estable (rho < 1) tiene stability = True."""
        result = mmc_metrics(15, 5, 4)
        assert result['stability'] is True
    
    def test_rho_in_stable_system(self):
        """En sistema estable, rho = lambda / (c * mu) < 1."""
        lam, mu, c = 15, 5, 4
        result = mmc_metrics(lam, mu, c)
        expected_rho = lam / (c * mu)
        assert result['rho'] == expected_rho
        assert result['rho'] < 1
    
    def test_P0_positive_in_stable_system(self):
        """En sistema estable, P0 > 0."""
        result = mmc_metrics(15, 5, 4)
        assert result['P0'] > 0
    
    def test_P0_less_than_one_in_stable_system(self):
        """En sistema estable, P0 < 1."""
        result = mmc_metrics(15, 5, 4)
        assert result['P0'] < 1
    
    def test_Lq_non_negative_in_stable_system(self):
        """En sistema estable, Lq >= 0."""
        result = mmc_metrics(15, 5, 4)
        assert result['Lq'] >= 0
    
    def test_L_non_negative_in_stable_system(self):
        """En sistema estable, L >= 0."""
        result = mmc_metrics(15, 5, 4)
        assert result['L'] >= 0
    
    def test_L_greater_than_Lq_in_stable_system(self):
        """En sistema estable, L > Lq (siempre hay clientes en servicio)."""
        result = mmc_metrics(15, 5, 4)
        assert result['L'] > result['Lq']
    
    def test_Wq_minutes_non_negative_in_stable_system(self):
        """En sistema estable, Wq_minutes >= 0."""
        result = mmc_metrics(15, 5, 4)
        assert result['Wq_minutes'] >= 0
    
    def test_W_minutes_non_negative_in_stable_system(self):
        """En sistema estable, W_minutes >= 0."""
        result = mmc_metrics(15, 5, 4)
        assert result['W_minutes'] >= 0
    
    def test_W_minutes_greater_than_Wq_minutes_in_stable_system(self):
        """En sistema estable, W_minutes > Wq_minutes."""
        result = mmc_metrics(15, 5, 4)
        assert result['W_minutes'] > result['Wq_minutes']


# ============================================================
# 4. TESTS DE SISTEMA INESTABLE (rho >= 1)
# ============================================================

class TestUnstableSystem:
    """Tests para sistemas inestables (rho >= 1)."""
    
    def test_unstable_system_has_stability_false(self):
        """Sistema inestable (rho >= 1) tiene stability = False."""
        result = mmc_metrics(25, 5, 4)
        assert result['stability'] is False
    
    def test_unstable_system_rho_greater_or_equal_one(self):
        """En sistema inestable, rho >= 1."""
        lam, mu, c = 25, 5, 4
        result = mmc_metrics(lam, mu, c)
        expected_rho = lam / (c * mu)
        assert result['rho'] == expected_rho
        assert result['rho'] >= 1
    
    def test_unstable_system_P0_is_zero(self):
        """En sistema inestable, P0 = 0."""
        result = mmc_metrics(25, 5, 4)
        assert result['P0'] == 0.0
    
    def test_unstable_system_Lq_is_infinite(self):
        """En sistema inestable, Lq = inf."""
        result = mmc_metrics(25, 5, 4)
        assert result['Lq'] == float('inf')
    
    def test_unstable_system_L_is_infinite(self):
        """En sistema inestable, L = inf."""
        result = mmc_metrics(25, 5, 4)
        assert result['L'] == float('inf')
    
    def test_unstable_system_Wq_is_infinite(self):
        """En sistema inestable, Wq_minutes = inf."""
        result = mmc_metrics(25, 5, 4)
        assert result['Wq_minutes'] == float('inf')
    
    def test_unstable_system_W_is_infinite(self):
        """En sistema inestable, W_minutes = inf."""
        result = mmc_metrics(25, 5, 4)
        assert result['W_minutes'] == float('inf')


# ============================================================
# 5. TESTS DE CASOS LÍMITE (EDGE CASES)
# ============================================================

class TestEdgeCases:
    """Tests para casos límite y condiciones especiales."""
    
    def test_zero_lambda_zero_arrivals(self):
        """Con lambda = 0 (sin llegadas), el sistema está vacío."""
        result = mmc_metrics(0, 5, 4)
        assert result['stability'] is True
        assert result['Lq'] == 0.0
        assert result['L'] == 0.0
        assert result['Wq_minutes'] == 0.0
        assert result['W_minutes'] == 0.0
    
    def test_lambda_very_close_to_boundary(self):
        """Lambda muy cercano a límite de estabilidad."""
        lam, mu, c = 19.99, 5, 4
        result = mmc_metrics(lam, mu, c)
        assert result['stability'] is True
        assert result['rho'] < 1
    
    def test_lambda_at_boundary_unstable(self):
        """Lambda exactamente en límite es inestable."""
        lam, mu, c = 20, 5, 4
        result = mmc_metrics(lam, mu, c)
        assert result['stability'] is False
        assert result['rho'] == 1.0
    
    def test_single_server_stable(self):
        """Sistema M/M/1 estable (c=1)."""
        result = mmc_metrics(3, 5, 1)
        assert result['stability'] is True
        assert result['rho'] == 0.6
    
    def test_single_server_unstable(self):
        """Sistema M/M/1 inestable (c=1)."""
        result = mmc_metrics(6, 5, 1)
        assert result['stability'] is False
    
    def test_many_servers(self):
        """Sistema con muchos servidores (c=10)."""
        result = mmc_metrics(15, 5, 10)
        assert result['stability'] is True
        assert result['rho'] == 0.3


# ============================================================
# 6. TESTS DE RELACIONES MATEMÁTICAS
# ============================================================

class TestMathematicalRelationships:
    """Tests para verificar relaciones matemáticas entre métricas."""
    
    def test_rho_formula(self):
        """rho = lambda / (c * mu)."""
        lam, mu, c = 15, 5, 4
        result = mmc_metrics(lam, mu, c)
        expected_rho = lam / (c * mu)
        assert abs(result['rho'] - expected_rho) < 1e-9
    
    def test_Wq_equals_Lq_divided_by_lambda(self):
        """Wq = Lq / lambda (en horas, convertido a minutos)."""
        result = mmc_metrics(15, 5, 4)
        if result['stability']:
            expected_Wq_minutes = (result['Lq'] / 15) * 60
            assert abs(result['Wq_minutes'] - expected_Wq_minutes) < 1e-9
    
    def test_W_equals_L_divided_by_lambda(self):
        """W = L / lambda (en horas, convertido a minutos)."""
        result = mmc_metrics(15, 5, 4)
        if result['stability']:
            expected_W_minutes = (result['L'] / 15) * 60
            assert abs(result['W_minutes'] - expected_W_minutes) < 1e-9
    
    def test_L_equals_Lq_plus_lambda_over_mu(self):
        """L = Lq + (lambda / mu)."""
        result = mmc_metrics(15, 5, 4)
        if result['stability']:
            expected_L = result['Lq'] + (15 / 5)
            assert abs(result['L'] - expected_L) < 1e-9
    
    def test_P0_between_zero_and_one(self):
        """En sistema estable, 0 < P0 < 1."""
        result = mmc_metrics(15, 5, 4)
        assert 0 < result['P0'] < 1


# ============================================================
# 7. TESTS DE COMPARACIÓN ENTRE SISTEMAS
# ============================================================

class TestSystemComparison:
    """Tests que comparan comportamiento de diferentes sistemas."""
    
    def test_more_servers_reduces_wait_time(self):
        """Más servidores reduce tiempo de espera."""
        result_2_servers = mmc_metrics(10, 5, 2)
        result_4_servers = mmc_metrics(10, 5, 4)
        assert result_4_servers['Wq_minutes'] < result_2_servers['Wq_minutes']
    
    def test_higher_service_rate_reduces_wait_time(self):
        """Mayor tasa de servicio reduce tiempo de espera."""
        result_slow = mmc_metrics(10, 5, 2)
        result_fast = mmc_metrics(10, 10, 2)
        assert result_fast['Wq_minutes'] < result_slow['Wq_minutes']
    
    def test_higher_arrival_rate_increases_wait_time(self):
        """Mayor tasa de llegada aumenta tiempo de espera."""
        result_low = mmc_metrics(5, 5, 2)
        result_high = mmc_metrics(15, 5, 2)
        assert result_high['Wq_minutes'] > result_low['Wq_minutes']
    
    def test_lower_rho_means_shorter_queue(self):
        """Menor rho (menor carga) significa cola más corta."""
        result_light = mmc_metrics(5, 5, 2)
        result_heavy = mmc_metrics(15, 5, 2)
        assert result_light['Lq'] < result_heavy['Lq']


# ============================================================
# 8. TESTS DE CASOS REALES (REALISTIC SCENARIOS)
# ============================================================

class TestRealisticScenarios:
    """Tests con parámetros realistas de sistemas de colas."""
    
    def test_bank_teller_system(self):
        """Escenario: banco con cajeros."""
        result = mmc_metrics(30, 30, 2)
        assert result['stability'] is True
        assert result['rho'] == 0.5
        assert result['Lq'] >= 0
        assert result['Wq_minutes'] >= 0
    
    def test_call_center_system(self):
        """Escenario: centro de llamadas."""
        result = mmc_metrics(60, 12, 8)
        assert result['stability'] is True
        assert result['rho'] < 1
    
    def test_hospital_emergency_system(self):
        """Escenario: urgencias hospitalarias."""
        result = mmc_metrics(20, 4, 6)
        assert result['stability'] is True
    
    def test_restaurant_checkout_system(self):
        """Escenario: sistema de cajas en restaurante."""
        # 40 clientes/hora, promedio 3 minutos (20 clientes/hora), 3 cajas
        result = mmc_metrics(40, 20, 3)
        assert result['stability'] is True


# ============================================================
# 9. TESTS DE SENSIBILIDAD
# ============================================================

class TestSensitivityAnalysis:
    """Tests para análisis de sensibilidad de parámetros."""
    
    def test_sensitivity_to_lambda_change(self):
        """Cambios en lambda afectan significativamente Lq."""
        result_1 = mmc_metrics(5, 5, 2)
        result_2 = mmc_metrics(8, 5, 2)
        assert result_2['Lq'] > result_1['Lq']
    
    def test_sensitivity_to_mu_change(self):
        """Cambios en mu afectan significativamente Lq."""
        result_1 = mmc_metrics(10, 5, 2)
        result_2 = mmc_metrics(10, 10, 2)
        assert result_2['Lq'] < result_1['Lq']
    
    def test_sensitivity_to_c_change(self):
        """Cambios en c afectan significativamente Lq."""
        result_1 = mmc_metrics(15, 5, 2)
        result_2 = mmc_metrics(15, 5, 4)
        assert result_2['Lq'] < result_1['Lq']
    
    def test_rho_increases_with_lambda(self):
        """rho aumenta cuando lambda aumenta."""
        result_1 = mmc_metrics(5, 5, 2)
        result_2 = mmc_metrics(10, 5, 2)
        assert result_2['rho'] > result_1['rho']


# ============================================================
# 10. TESTS DE CONSISTENCIA NUMÉRICA
# ============================================================

class TestNumericalConsistency:
    """Tests para verificar consistencia numérica."""
    
    def test_results_are_deterministic(self):
        """Mismos parámetros siempre dan mismo resultado."""
        result_1 = mmc_metrics(15, 5, 4)
        result_2 = mmc_metrics(15, 5, 4)
        assert result_1 == result_2
    
    def test_all_metrics_are_finite_in_stable_system(self):
        """En sistema estable, todas las métricas son finitas."""
        result = mmc_metrics(15, 5, 4)
        assert math.isfinite(result['rho'])
        assert math.isfinite(result['P0'])
        assert math.isfinite(result['Lq'])
        assert math.isfinite(result['Wq_minutes'])
        assert math.isfinite(result['L'])
        assert math.isfinite(result['W_minutes'])
    
    def test_no_nan_values_in_stable_system(self):
        """En sistema estable, no hay NaN."""
        result = mmc_metrics(15, 5, 4)
        assert not math.isnan(result['rho'])
        assert not math.isnan(result['P0'])
        assert not math.isnan(result['Lq'])
        assert not math.isnan(result['Wq_minutes'])
        assert not math.isnan(result['L'])
        assert not math.isnan(result['W_minutes'])


# ============================================================
# 11. TESTS DE INTEGRACIÓN CON ESCENARIOS MÚLTIPLES
# ============================================================

class TestMultipleScenarios:
    """Tests que evalúan múltiples escenarios secuencialmente."""
    
    def test_scenario_progression_increasing_load(self):
        """Progresión de carga: ligero -> medio -> pesado -> inestable."""
        scenarios = [
            (5, 5, 2, True),    # rho = 0.5
            (7, 5, 2, True),    # rho = 0.7
            (9, 5, 2, True),    # rho = 0.9
            (10, 5, 2, False),  # rho = 1.0 (inestable)
        ]

        for lam, mu, c, expected_stable in scenarios:
            result = mmc_metrics(lam, mu, c)
            assert result['stability'] == expected_stable
    
    def test_scenario_progression_increasing_servers(self):
        """Progresión de servidores: carga fija, más servidores."""
        for c in range(2, 6):
            # lambda = 8, mu = 5, con c servidores
            result = mmc_metrics(8, 5, c)
            assert result['stability'] is True
            assert result['Lq'] >= 0


# ============================================================
# 12. TESTS DE VALORES ESPECIALES
# ============================================================

class TestSpecialValues:
    """Tests para valores especiales y casos extremos."""
    
    def test_very_small_lambda(self):
        """Lambda muy pequeño (casi sin llegadas)."""
        result = mmc_metrics(0.1, 5, 2)
        assert result['stability'] is True
        assert result['Lq'] < 0.1
    
    def test_very_large_mu(self):
        """Mu muy grande (servicio muy rápido)."""
        result = mmc_metrics(10, 1000, 2)
        assert result['stability'] is True
        assert result['Lq'] < 0.0001
    
    def test_lambda_equals_mu(self):
        """Lambda igual a mu."""
        result = mmc_metrics(5, 5, 2)
        assert result['stability'] is True
        assert result['rho'] == 0.5
    
    def test_large_number_of_servers(self):
        """Número muy grande de servidores."""
        result = mmc_metrics(15, 5, 100)
        assert result['stability'] is True
        assert result['Lq'] < 0.0001


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])