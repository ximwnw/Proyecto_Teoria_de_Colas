"""
Tests de Exactitud Matemática - Validar contra Fórmulas Teóricas de Erlang
Verifica que la implementación cumple con las ecuaciones teóricas de teoría de colas
"""

import pytest
import math
from typing import Dict, Tuple


def erlang_b(lam: float, mu: float, c: int) -> float:
    """
    Calcula la fórmula de Erlang B (Erlang Loss Formula).
    Usada para sistemas M/M/c con rechazo de llamadas.
    
    Erlang B = (λ/μ)^c / c! / (Σ_{n=0}^{c} (λ/μ)^n / n!)
    """
    a = lam / mu  # intensidad de tráfico
    
    # Calcular numerador: a^c / c!
    numerator = (a ** c) / math.factorial(c)
    
    # Calcular denominador: suma de a^n / n! para n de 0 a c
    denominator = sum((a ** n) / math.factorial(n) for n in range(c + 1))
    
    return numerator / denominator


def erlang_c(lam: float, mu: float, c: int) -> float:
    """
    Calcula la fórmula de Erlang C (Erlang Delay Formula).
    Probabilidad de que un cliente deba esperar en cola.
    """
    a = lam / mu
    rho = a / c
    
    if rho >= 1:
        return 1.0
    
    numerator = ((a ** c) / math.factorial(c)) * (c / (c - a))
    sum_terms = sum((a ** n) / math.factorial(n) for n in range(c))
    denominator = sum_terms + ((a ** c) / math.factorial(c)) * (c / (c - a))
    
    return numerator / denominator


def theoretical_P0(lam: float, mu: float, c: int) -> float:
    """Calcula P0 usando la fórmula teórica de Erlang."""
    a = lam / mu
    rho = a / c
    
    if rho >= 1:
        return 0.0
    
    sum_terms = sum((a ** n) / math.factorial(n) for n in range(c))
    last_term = ((a ** c) / math.factorial(c)) * (c / (c - a))
    
    return 1 / (sum_terms + last_term)


def theoretical_Lq(lam: float, mu: float, c: int) -> float:
    """Calcula Lq usando la fórmula teórica."""
    a = lam / mu
    rho = a / c
    
    if rho >= 1:
        return float('inf')
    
    P0 = theoretical_P0(lam, mu, c)
    Lq = (P0 * (a ** c) * rho) / (math.factorial(c) * ((1 - rho) ** 2))
    
    return Lq


def theoretical_Wq(lam: float, mu: float, c: int) -> float:
    """Calcula Wq usando Little's Law."""
    if lam == 0:
        return 0.0
    
    Lq = theoretical_Lq(lam, mu, c)
    
    if Lq == float('inf'):
        return float('inf')
    
    return Lq / lam


def theoretical_L(lam: float, mu: float, c: int) -> float:
    """Calcula L usando Little's Law."""
    Lq = theoretical_Lq(lam, mu, c)
    
    if Lq == float('inf'):
        return float('inf')
    
    return Lq + (lam / mu)


def theoretical_W(lam: float, mu: float, c: int) -> float:
    """Calcula W usando Little's Law."""
    if lam == 0:
        return 0.0
    
    L = theoretical_L(lam, mu, c)
    
    if L == float('inf'):
        return float('inf')
    
    return L / lam


def simple_mmc_metrics(lam: float, mu: float, c: int) -> Dict:
    """Simple M/M/c implementation for testing."""
    if lam < 0 or mu <= 0 or c <= 0 or not isinstance(c, int):
        raise ValueError("Invalid parameters")

    rho = lam / (c * mu)
    if rho >= 1:
        return {
            'rho': rho,
            'stability': False,
            'P0': 0.0,
            'Lq': float('inf'),
            'Wq_minutes': float('inf'),
            'L': float('inf'),
            'W_minutes': float('inf'),
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
        "stability": True,
        "P0": P0,
        "Lq": Lq,
        "Wq_minutes": Wq_minutes,
        "L": L,
        "W_minutes": W_minutes,
    }


class TestMathematicalAccuracy:
    """Tests de exactitud contra fórmulas teóricas de Erlang."""

    def test_P0_accuracy_erlang_formula(self):
        """P0 debe coincidir exactamente con la fórmula de Erlang."""
        test_cases = [
            (10, 5, 3),
            (15, 10, 2),
            (20, 8, 4),
            (5, 5, 2),
            (2, 3, 1),
        ]
        
        for lam, mu, c in test_cases:
            result = simple_mmc_metrics(lam, mu, c)
            theoretical = theoretical_P0(lam, mu, c)
            
            if theoretical > 0:
                relative_error = abs(result['P0'] - theoretical) / theoretical
                assert relative_error < 0.0001, \
                    f"P0 mismatch for λ={lam}, μ={mu}, c={c}: " \
                    f"calculated={result['P0']:.6f}, theoretical={theoretical:.6f}, " \
                    f"error={relative_error*100:.4f}%"

    def test_Lq_accuracy_erlang_formula(self):
        """Lq debe coincidir exactamente con la fórmula de Erlang."""
        test_cases = [
            (10, 5, 3),
            (15, 10, 2),
            (20, 8, 4),
            (5, 5, 2),
        ]
        
        for lam, mu, c in test_cases:
            result = simple_mmc_metrics(lam, mu, c)
            theoretical = theoretical_Lq(lam, mu, c)
            
            if theoretical > 0.001:
                relative_error = abs(result['Lq'] - theoretical) / theoretical
                assert relative_error < 0.0001

    def test_littles_law_L_equals_Lq_plus_lambda_over_mu(self):
        """Little's Law: L = Lq + λ/μ."""
        test_cases = [
            (10, 5, 3),
            (15, 10, 2),
            (20, 8, 4),
        ]
        
        for lam, mu, c in test_cases:
            result = simple_mmc_metrics(lam, mu, c)
            expected_L = result['Lq'] + (lam / mu)
            relative_error = abs(result['L'] - expected_L) / expected_L
            assert relative_error < 0.00001

    def test_littles_law_W_equals_Wq_plus_one_over_mu(self):
        """Little's Law: W = Wq + 1/μ (en minutos)."""
        test_cases = [
            (10, 5, 3),
            (15, 10, 2),
            (20, 8, 4),
        ]
        
        for lam, mu, c in test_cases:
            result = simple_mmc_metrics(lam, mu, c)
            service_time_minutes = 60 / mu
            expected_W = result['Wq_minutes'] + service_time_minutes
            relative_error = abs(result['W_minutes'] - expected_W) / expected_W
            assert relative_error < 0.00001

    def test_utilization_rho_calculation(self):
        """ρ debe ser λ / (c * μ)."""
        test_cases = [
            (10, 5, 3),
            (15, 10, 2),
            (20, 8, 4),
            (5, 5, 2),
        ]
        
        for lam, mu, c in test_cases:
            result = simple_mmc_metrics(lam, mu, c)
            expected_rho = lam / (c * mu)
            assert abs(result['rho'] - expected_rho) < 1e-10

    def test_stability_condition_rho_less_than_one(self):
        """Sistema estable si y solo si ρ < 1."""
        result_stable = simple_mmc_metrics(10, 5, 3)
        assert result_stable['stability'] == True
        assert result_stable['rho'] < 1
        
        result_unstable = simple_mmc_metrics(15, 5, 2)
        assert result_unstable['stability'] == False
        assert result_unstable['rho'] >= 1

    def test_P0_bounds_between_zero_and_one(self):
        """P0 debe estar entre 0 y 1 para sistemas estables."""
        test_cases = [
            (10, 5, 3),
            (15, 10, 2),
            (20, 8, 4),
            (5, 5, 2),
        ]
        
        for lam, mu, c in test_cases:
            result = simple_mmc_metrics(lam, mu, c)
            assert 0 < result['P0'] <= 1

    def test_Lq_non_negative(self):
        """Lq siempre debe ser no-negativo."""
        test_cases = [
            (10, 5, 3),
            (15, 10, 2),
            (20, 8, 4),
            (0, 5, 2),
        ]
        
        for lam, mu, c in test_cases:
            result = simple_mmc_metrics(lam, mu, c)
            assert result['Lq'] >= 0

    def test_rho_boundary_stability(self):
        """En el límite ρ ≈ 1, el sistema se vuelve inestable."""
        lam = 9.999
        mu = 5
        c = 2
        
        result = simple_mmc_metrics(lam, mu, c)
        assert result['stability'] == True
        assert result['Lq'] > 100

    def test_erlang_c_relationship(self):
        """La probabilidad de espera Pw = Erlang C."""
        lam, mu, c = 10, 5, 3
        rho = lam / (c * mu)
        
        result = simple_mmc_metrics(lam, mu, c)
        a = lam / mu
        Pw_formula = (result['P0'] * (a ** c)) / (math.factorial(c) * (1 - rho))
        Pw_erlang = erlang_c(lam, mu, c)
        
        relative_error = abs(Pw_formula - Pw_erlang) / Pw_erlang
        assert relative_error < 0.0001

    def test_zero_arrivals_edge_case(self):
        """Con λ=0, no hay clientes, sin espera."""
        result = simple_mmc_metrics(0, 5, 3)
        
        assert result['rho'] == 0
        assert result['stability'] == True
        assert result['Lq'] == 0
        assert result['Wq_minutes'] == 0
        assert result['L'] == 0
        assert result['W_minutes'] == 0

    def test_single_server_m_m_1(self):
        """Caso especial M/M/1: un solo servidor."""
        lam, mu, c = 3, 5, 1
        result = simple_mmc_metrics(lam, mu, c)
        expected_Lq = (lam ** 2) / (mu * (mu - lam))
        relative_error = abs(result['Lq'] - expected_Lq) / expected_Lq
        assert relative_error < 0.0001

    def test_metric_relationships_consistency(self):
        """Verificar que todas las métricas son consistentes entre sí."""
        test_cases = [
            (10, 5, 3),
            (15, 10, 2),
            (20, 8, 4),
        ]
        
        for lam, mu, c in test_cases:
            result = simple_mmc_metrics(lam, mu, c)
            
            expected_L = result['Lq'] + (lam / mu)
            assert abs(result['L'] - expected_L) < 1e-6
            
            expected_W = result['Wq_minutes'] + (60 / mu)
            assert abs(result['W_minutes'] - expected_W) < 1e-6
            
            if lam > 0:
                expected_Wq = (result['Lq'] / lam) * 60
                assert abs(result['Wq_minutes'] - expected_Wq) < 1e-6


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
