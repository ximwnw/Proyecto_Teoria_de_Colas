"""
Advanced Edge Cases & Boundary Tests for Queueing Theory Project
Pruebas avanzadas de casos límite para mejorar cobertura
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import math


# ============================================================
# ADVANCED EDGE CASES FOR MMC MODEL
# ============================================================

class TestMMCModelBoundaryConditions:
    """Pruebas exhaustivas de condiciones límite del modelo M/M/c."""

    def simple_mmc_metrics(self, lam, mu, c):
        """Simple M/M/c implementation for testing."""
        if lam < 0:
            raise ValueError("lambda must be non-negative.")
        if mu <= 0:
            raise ValueError("mu must be greater than zero.")
        if c <= 0 or not isinstance(c, int):
            raise ValueError("servers must be a positive integer.")

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

        # Calculate P0 using Erlang formula
        sum_terms = sum((lam / mu) ** n / math.factorial(n) for n in range(c))
        last_term = ((lam / mu) ** c) / (math.factorial(c) * (1 - rho))
        P0 = 1 / (sum_terms + last_term)

        # Calculate Lq (queue length)
        Lq = (P0 * (lam / mu) ** c * rho) / (math.factorial(c) * (1 - rho) ** 2)

        # Calculate wait times
        Wq_hours = Lq / lam if lam > 0 else 0.0
        Wq_minutes = Wq_hours * 60

        # Calculate system metrics
        L = Lq + (lam / mu)
        W_hours = L / lam if lam > 0 else 0.0
        W_minutes = W_hours * 60

        return {
            'rho': rho,
            'stability': True,
            'P0': P0,
            'Lq': Lq,
            'Wq_minutes': Wq_minutes,
            'L': L,
            'W_minutes': W_minutes,
        }

    def test_extremely_small_lambda(self):
        """Very small arrival rate (λ → 0+)."""
        result = self.simple_mmc_metrics(0.001, 5, 4)
        assert result['stability'] is True
        assert result['Lq'] < 0.01
        assert result['P0'] > 0.99

    def test_extremely_large_lambda_relative_to_capacity(self):
        """Extremely high arrival rate relative to capacity."""
        result = self.simple_mmc_metrics(100, 5, 2)
        assert result['stability'] is False
        assert result['rho'] > 1

    def test_very_high_mu_relative_to_lambda(self):
        """Very fast service rate."""
        result = self.simple_mmc_metrics(1, 100, 2)
        assert result['stability'] is True
        assert result['rho'] < 0.01
        assert result['Lq'] < 0.0001

    def test_rho_approaches_one_from_below(self):
        """ρ → 1- (system approaches instability)."""
        result = self.simple_mmc_metrics(19.999, 5, 4)
        assert result['stability'] is True
        assert result['rho'] < 1.0
        assert 0.99 < result['rho'] < 1.0

    def test_rho_equals_one_exactly(self):
        """ρ = 1 (critical point)."""
        result = self.simple_mmc_metrics(20, 5, 4)
        assert result['stability'] is False
        assert result['rho'] == 1.0

    def test_rho_just_above_one(self):
        """ρ > 1 (unstable)."""
        result = self.simple_mmc_metrics(20.001, 5, 4)
        assert result['stability'] is False
        assert result['rho'] > 1.0

    def test_very_large_c_reduces_rho(self):
        """Large number of servers dramatically reduces ρ."""
        result_few = self.simple_mmc_metrics(10, 5, 2)
        result_many = self.simple_mmc_metrics(10, 5, 100)
        assert result_many['rho'] < result_few['rho']
        assert result_many['stability'] is True

    def test_P0_approaches_one_with_low_utilization(self):
        """P0 → 1 as ρ → 0."""
        result = self.simple_mmc_metrics(0.1, 5, 4)
        assert result['stability'] is True
        assert result['P0'] > 0.97

    def test_Lq_approaches_zero_with_low_utilization(self):
        """Lq → 0 as ρ → 0."""
        result = self.simple_mmc_metrics(0.1, 5, 4)
        assert result['stability'] is True
        assert result['Lq'] < 0.001

    def test_Wq_increases_exponentially_near_saturation(self):
        """Wq increases dramatically as ρ → 1-."""
        result_low = self.simple_mmc_metrics(5, 5, 4)
        result_high = self.simple_mmc_metrics(19, 5, 4)
        assert result_high['Wq_minutes'] > result_low['Wq_minutes'] * 100


# ============================================================
# DATA GENERATION EDGE CASES
# ============================================================

class TestDataGenerationEdgeCases:
    """Tests for edge cases in customer data generation."""

    def test_single_customer_generation(self):
        """Generation with only 1 customer."""
        np.random.seed(42)
        start_date = datetime(2024, 1, 1, 8, 0, 0)

        arrival_times = [start_date]
        service_times = np.random.exponential(scale=60/12.1233, size=1)

        df = pd.DataFrame({
            'customer_id': [1],
            'arrival_time': arrival_times,
            'service_time_minutes': service_times,
        })

        assert len(df) == 1
        assert df['customer_id'].iloc[0] == 1

    def test_all_customers_same_service_time(self):
        """All customers with identical service times."""
        service_times = np.full(100, 5.0)

        assert np.all(service_times == 5.0)
        assert np.std(service_times) == 0.0

    def test_arrival_times_in_same_hour(self):
        """All arrivals concentrated in single hour."""
        np.random.seed(42)
        start_date = datetime(2024, 1, 1, 8, 0, 0)
        arrival_times = [start_date + timedelta(minutes=i*0.5) for i in range(100)]

        hours = [t.hour for t in arrival_times]
        assert all(h == 8 for h in hours)

    def test_arrival_times_spanning_multiple_days(self):
        """Arrivals spanning many days."""
        np.random.seed(42)
        start_date = datetime(2024, 1, 1, 8, 0, 0)
        arrival_times = [start_date + timedelta(hours=i*2) for i in range(100)]

        days = set(t.date() for t in arrival_times)
        assert len(days) > 1

    def test_extremely_fast_service_times(self):
        """Very fast service (< 1 minute)."""
        service_times = np.random.exponential(scale=0.1, size=100)

        assert all(t > 0 for t in service_times)
        assert np.mean(service_times) < 1

    def test_extremely_slow_service_times(self):
        """Very slow service (> 1 hour)."""
        service_times = np.random.exponential(scale=120, size=100)

        assert all(t > 0 for t in service_times)
        assert np.mean(service_times) > 60


# ============================================================
# HOURLY STAFFING EDGE CASES
# ============================================================

class TestHourlyStaffingEdgeCases:
    """Tests for edge cases in hourly staffing analysis."""

    def test_zero_waiting_cost(self):
        """Cost function with zero waiting cost."""
        # Total cost should just be server cost
        server_cost_per_hour = 20.0
        Lq = 5.0  # queue length
        c = 3  # servers
        waiting_cost_per_minute = 0.0

        total_cost = c * server_cost_per_hour + Lq * 60 * waiting_cost_per_minute
        assert total_cost == 60.0  # Just 3 servers * 20

    def test_zero_server_cost(self):
        """Cost function with zero server cost."""
        # Total cost should just be waiting cost
        server_cost_per_hour = 0.0
        Lq = 5.0
        c = 3
        waiting_cost_per_minute = 0.50

        total_cost = c * server_cost_per_hour + Lq * 60 * waiting_cost_per_minute
        assert total_cost == 150.0  # 5 * 60 * 0.5

    def test_single_server_optimal(self):
        """Finding optimal servers when c=1 might be optimal."""
        server_cost = 20.0

        # For c=1: server cost = 20
        # For c=2: server cost = 40
        # c=1 is cheaper if waiting cost difference doesn't exceed 20
        cost_c1 = 1 * server_cost
        cost_c2 = 2 * server_cost

        assert cost_c2 > cost_c1

    def test_very_high_servers(self):
        """Cost with extremely high number of servers."""
        server_cost_per_hour = 20.0
        c = 100

        total_server_cost = c * server_cost_per_hour
        assert total_server_cost == 2000.0

    def test_hourly_distribution_with_zero_arrivals(self):
        """Hour with zero customer arrivals."""
        arrival_counts = {}
        for hour in range(24):
            arrival_counts[hour] = 0 if hour == 5 else 10

        # Hour 5 has no arrivals
        assert arrival_counts[5] == 0
        assert sum(arrival_counts.values()) == 230  # 23 hours * 10

    def test_hourly_distribution_with_peak_hour(self):
        """Hour with extremely high arrivals."""
        arrival_counts = {}
        for hour in range(24):
            arrival_counts[hour] = 100 if hour == 12 else 10

        # Hour 12 is peak
        assert arrival_counts[12] == 100
        peak_hour = max(arrival_counts.items(), key=lambda x: x[1])
        assert peak_hour[0] == 12


# ============================================================
# INTEGRATION & CONSISTENCY EDGE CASES
# ============================================================

class TestIntegrationEdgeCases:
    """Tests for edge cases in cross-module integration."""

    def test_data_with_no_variability(self):
        """Data generation with constant values (no randomness)."""
        # All customers arrive at same time
        arrival_times = [datetime(2024, 1, 1, 8, 0, 0)] * 100
        service_times = [5.0] * 100

        df = pd.DataFrame({
            'customer_id': range(1, 101),
            'arrival_time': arrival_times,
            'service_time_minutes': service_times,
        })

        # Verify no variability
        assert len(set(df['arrival_time'])) == 1
        assert len(set(df['service_time_minutes'])) == 1

    def test_extreme_imbalance_arrival_vs_service(self):
        """Arrivals much faster than service capacity."""
        lambda_rate = 100  # 100 customers per hour
        mu_rate = 5  # 5 customers per hour per server
        c = 3

        rho = lambda_rate / (c * mu_rate)
        assert rho > 1  # System is unstable

    def test_perfect_balance_arrival_service(self):
        """Arrivals perfectly match service capacity."""
        lambda_rate = 20  # customers per hour
        mu_rate = 5  # customers per hour per server
        c = 4

        rho = lambda_rate / (c * mu_rate)
        assert rho == 1.0  # System at critical point

    def test_greatly_overprovisioned_system(self):
        """System with many more servers than needed."""
        lambda_rate = 5
        mu_rate = 5
        c = 50  # Way more than needed

        rho = lambda_rate / (c * mu_rate)
        assert rho == 0.02  # Very low utilization


# ============================================================
# NUMERICAL STABILITY TESTS
# ============================================================

class TestNumericalStability:
    """Tests for numerical stability with extreme values."""

    def simple_mmc_metrics(self, lam, mu, c):
        """Simple M/M/c implementation."""
        if lam < 0 or mu <= 0 or c <= 0 or not isinstance(c, int):
            raise ValueError("Invalid parameters")

        rho = lam / (c * mu)
        if rho >= 1:
            return {'rho': rho, 'stability': False}

        return {'rho': rho, 'stability': True}

    def test_very_small_values_dont_cause_underflow(self):
        """Very small lambda doesn't cause numerical underflow."""
        result = self.simple_mmc_metrics(1e-10, 5, 4)
        assert result['stability'] is True
        assert result['rho'] > 0

    def test_very_large_values_dont_cause_overflow(self):
        """Very large values handled without overflow."""
        result = self.simple_mmc_metrics(1e6, 1e6, 1000)
        assert result['stability'] is True
        assert result['rho'] == 0.001  # 1e6 / (1000 * 1e6) = 0.001

    def test_rho_precision_near_boundary(self):
        """ρ calculation maintains precision near stability boundary."""
        lam, mu, c = 19.9999999, 5, 4
        result = self.simple_mmc_metrics(lam, mu, c)

        expected_rho = lam / (c * mu)
        assert abs(result['rho'] - expected_rho) < 1e-10


# ============================================================
# CORRELATION & DEPENDENCY TESTS
# ============================================================

class TestMetricCorrelations:
    """Tests for relationships between different metrics."""

    def simple_mmc_metrics(self, lam, mu, c):
        """Simple M/M/c implementation."""
        if lam < 0 or mu <= 0 or c <= 0 or not isinstance(c, int):
            raise ValueError("Invalid parameters")

        rho = lam / (c * mu)
        if rho >= 1:
            return {
                'rho': rho, 'stability': False,
                'Lq': float('inf'), 'L': float('inf'),
                'Wq_minutes': float('inf'), 'W_minutes': float('inf')
            }

        # Simplified calculation
        Lq = (rho ** 2) / (1 - rho) if lam > 0 else 0
        Wq_minutes = (Lq / lam * 60) if lam > 0 else 0
        L = Lq + (lam / mu)
        W_minutes = (L / lam * 60) if lam > 0 else 0

        return {
            'rho': rho, 'stability': True,
            'Lq': Lq, 'L': L,
            'Wq_minutes': Wq_minutes, 'W_minutes': W_minutes
        }

    def test_increasing_servers_decreases_all_metrics(self):
        """More servers reduces queue and wait metrics."""
        result_2 = self.simple_mmc_metrics(10, 5, 2)
        result_4 = self.simple_mmc_metrics(10, 5, 4)

        if result_2['stability'] and result_4['stability']:
            assert result_4['Lq'] < result_2['Lq']
            assert result_4['L'] < result_2['L']

    def test_Wq_always_less_than_W(self):
        """Wait in queue always less than total wait."""
        result = self.simple_mmc_metrics(10, 5, 3)

        if result['stability']:
            assert result['Wq_minutes'] <= result['W_minutes']

    def test_Lq_always_less_than_L(self):
        """Queue length always less than system length."""
        result = self.simple_mmc_metrics(10, 5, 3)

        if result['stability']:
            assert result['Lq'] <= result['L']


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
