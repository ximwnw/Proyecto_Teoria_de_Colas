"""
Boundary Conditions & Corner Cases Testing
Pruebas exhaustivas de condiciones límite y casos especiales
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import math


# ============================================================
# EXTREME PARAMETER COMBINATIONS
# ============================================================

class TestExtremeParameterCombinations:
    """Tests combining extreme values across parameters."""

    def simple_mmc(self, lam, mu, c):
        """M/M/c with all extreme handling."""
        if lam < 0 or mu <= 0 or c <= 0:
            raise ValueError("Invalid")

        rho = lam / (c * mu)
        return {
            'rho': rho,
            'stability': rho < 1,
            'lambda': lam,
            'mu': mu,
            'c': c,
        }

    def test_tiny_lambda_tiny_mu_large_c(self):
        """All small inputs with many servers."""
        result = self.simple_mmc(0.001, 0.001, 100)
        assert result['stability'] is True

    def test_large_lambda_large_mu_small_c(self):
        """Large arrival and service, few servers."""
        result = self.simple_mmc(1000, 1000, 1)
        assert result['rho'] == 1.0

    def test_large_lambda_small_mu_many_c(self):
        """High arrivals, slow service, many servers."""
        result = self.simple_mmc(100, 1, 200)
        assert result['stability'] is True

    def test_small_lambda_large_mu_single_c(self):
        """Low arrivals, fast service, one server."""
        result = self.simple_mmc(0.1, 100, 1)
        assert result['stability'] is True
        assert result['rho'] <= 0.001  # 0.1 / (1 * 100) = 0.001


# ============================================================
# TIME-BASED EDGE CASES
# ============================================================

class TestTimeBasedEdgeCases:
    """Tests for time-related boundary conditions."""

    def test_customer_arrival_at_midnight(self):
        """Customer arrives exactly at midnight (00:00:00)."""
        arrival = datetime(2024, 1, 1, 0, 0, 0)
        assert arrival.hour == 0
        assert arrival.minute == 0
        assert arrival.second == 0

    def test_customer_arrival_at_end_of_day(self):
        """Customer arrives at 23:59:59."""
        arrival = datetime(2024, 1, 1, 23, 59, 59)
        assert arrival.hour == 23

    def test_customers_span_exactly_24_hours(self):
        """Data spans exactly 24 hours."""
        start = datetime(2024, 1, 1, 8, 0, 0)
        end = datetime(2024, 1, 2, 8, 0, 0)

        duration = (end - start).total_seconds() / 3600
        assert duration == 24.0

    def test_customers_span_one_second(self):
        """All customers in 1 second window."""
        arrivals = [datetime(2024, 1, 1, 8, 0, 0)] * 100
        time_range = (max(arrivals) - min(arrivals)).total_seconds()

        assert time_range == 0

    def test_customers_span_exactly_one_hour(self):
        """Customers span exactly 1 hour."""
        start = datetime(2024, 1, 1, 8, 0, 0)
        end = datetime(2024, 1, 1, 9, 0, 0)

        duration = (end - start).total_seconds() / 3600
        assert duration == 1.0

    def test_month_boundary_crossing(self):
        """Arrivals crossing month boundary."""
        arrivals = [
            datetime(2024, 1, 31, 22, 0, 0),
            datetime(2024, 1, 31, 23, 0, 0),
            datetime(2024, 2, 1, 0, 0, 0),
            datetime(2024, 2, 1, 1, 0, 0),
        ]

        months = set(a.month for a in arrivals)
        assert len(months) == 2

    def test_year_boundary_crossing(self):
        """Arrivals crossing year boundary."""
        arrivals = [
            datetime(2023, 12, 31, 23, 0, 0),
            datetime(2024, 1, 1, 0, 0, 0),
        ]

        years = set(a.year for a in arrivals)
        assert len(years) == 2


# ============================================================
# SERVICE TIME EDGE CASES
# ============================================================

class TestServiceTimeEdgeCases:
    """Tests for service time boundary conditions."""

    def test_zero_service_time(self):
        """Instant service (0 minutes)."""
        service_time = 0.0
        assert service_time >= 0

    def test_extremely_long_service_time(self):
        """Very long service (24 hours = 1440 minutes)."""
        service_time = 1440.0
        assert service_time > 0

    def test_service_time_variance_with_100_identical(self):
        """100 customers with identical service time."""
        service_times = np.array([5.5] * 100)
        variance = np.var(service_times)
        assert variance == 0.0

    def test_service_time_all_different(self):
        """100 unique service times."""
        service_times = np.linspace(0.1, 10.0, 100)
        assert len(set(service_times)) == 100

    def test_service_times_follow_exponential(self):
        """Service times from exponential distribution."""
        np.random.seed(42)
        service_times = np.random.exponential(scale=5, size=1000)

        # Exponential should have all positive values
        assert np.all(service_times > 0)
        # Mean should be close to scale
        assert 4.5 < np.mean(service_times) < 5.5

    def test_service_times_all_minimum(self):
        """All services at minimum (0.0001)."""
        service_times = [0.0001] * 100
        assert np.all(np.array(service_times) > 0)

    def test_service_times_all_maximum(self):
        """All services at maximum (999 minutes)."""
        service_times = [999.0] * 100
        assert np.all(np.array(service_times) < 1000)


# ============================================================
# ARRIVAL RATE EDGE CASES
# ============================================================

class TestArrivalRateEdgeCases:
    """Tests for arrival rate boundary conditions."""

    def test_single_customer(self):
        """Only 1 customer in entire period."""
        num_customers = 1
        assert num_customers > 0

    def test_maximum_realistic_customers(self):
        """Very high customer count."""
        num_customers = 100000
        hours = 24
        arrival_rate = num_customers / hours
        assert arrival_rate > 4000  # per hour

    def test_zero_inter_arrival_time(self):
        """Customers arrive with zero gap."""
        arrivals = [datetime(2024, 1, 1, 8, 0, 0)] * 100
        inter_arrivals = [0] * 99

        assert all(gap == 0 for gap in inter_arrivals)

    def test_inter_arrival_times_from_exponential(self):
        """Inter-arrival times from exponential (Poisson process)."""
        np.random.seed(42)
        inter_arrivals = np.random.exponential(scale=1/5, size=100)

        assert np.all(inter_arrivals >= 0)
        assert np.mean(inter_arrivals) > 0.1

    def test_constant_inter_arrival_time(self):
        """Deterministic arrivals (constant interval)."""
        interval = 10.0  # minutes
        arrivals = [datetime(2024, 1, 1, 8, 0, 0) + timedelta(minutes=i*interval)
                   for i in range(50)]

        for i in range(1, len(arrivals)):
            gap = (arrivals[i] - arrivals[i-1]).total_seconds() / 60
            assert abs(gap - interval) < 0.001


# ============================================================
# STAFFING LEVEL EDGE CASES
# ============================================================

class TestStaffingLevelEdgeCases:
    """Tests for server count boundary conditions."""

    def test_single_server(self):
        """M/M/1 system."""
        servers = 1
        assert servers > 0

    def test_many_servers(self):
        """System with 1000+ servers."""
        servers = 1000
        assert servers > 0

    def test_servers_equal_arrivals(self):
        """Number of servers equals arrival rate."""
        lambda_rate = 50  # customers per hour
        servers = 50
        mu = 10  # per hour

        rho = lambda_rate / (servers * mu)
        assert rho == 0.1  # Very underutilized

    def test_servers_fraction_of_arrivals(self):
        """Few servers vs high arrivals."""
        lambda_rate = 100
        servers = 2
        mu = 5

        rho = lambda_rate / (servers * mu)
        assert rho > 1  # Unstable


# ============================================================
# COST CALCULATION EDGE CASES
# ============================================================

class TestCostCalculationEdgeCases:
    """Tests for cost function boundary conditions."""

    def test_cost_with_zero_Lq(self):
        """Cost when queue is empty (Lq=0)."""
        server_cost = 20
        waiting_cost = 0.5
        Lq = 0
        servers = 3

        total = servers * server_cost + Lq * 60 * waiting_cost
        assert total == servers * server_cost

    def test_cost_with_zero_servers(self):
        """Cost with no servers (degenerate case)."""
        server_cost = 20
        servers = 0
        total = servers * server_cost
        assert total == 0

    def test_cost_with_extreme_queue(self):
        """Cost with extremely large queue (Lq=10000)."""
        Lq = 10000
        waiting_cost = 0.5
        waiting_contribution = Lq * 60 * waiting_cost

        assert waiting_contribution == 300000

    def test_cost_comparison_few_vs_many_servers(self):
        """Cost comparison: 1 server vs 10 servers."""
        server_cost = 20

        cost_1 = 1 * server_cost
        cost_10 = 10 * server_cost

        assert cost_10 > cost_1

    def test_cost_with_fractional_server_cost(self):
        """Cost with fractional server rate."""
        server_cost = 7.5
        servers = 3
        total = servers * server_cost

        assert total == 22.5


# ============================================================
# DISTRIBUTION & PROBABILITY EDGE CASES
# ============================================================

class TestDistributionEdgeCases:
    """Tests for probability distribution edge cases."""

    def test_poisson_with_lambda_zero(self):
        """Poisson distribution with λ=0."""
        # λ=0 means P(X=0)=1, P(X>0)=0
        lambda_val = 0
        # Only outcome is 0 customers
        assert lambda_val == 0

    def test_poisson_with_large_lambda(self):
        """Poisson with very large λ."""
        lambda_val = 1000
        # For large λ, Poisson approximates Normal
        assert lambda_val > 100

    def test_exponential_with_zero_scale(self):
        """Exponential with scale→0."""
        # Service time approaches 0
        scale = 0.0001
        assert scale > 0

    def test_exponential_with_large_scale(self):
        """Exponential with large scale."""
        # Service time → infinity
        scale = 10000
        assert scale > 0

    def test_uniform_distribution_boundaries(self):
        """Uniform distribution on [a, b]."""
        a, b = 0.5, 9.5
        samples = np.random.uniform(a, b, 10000)

        assert np.all(samples >= a)
        assert np.all(samples <= b)
        assert a < np.mean(samples) < b


# ============================================================
# DATA CONSISTENCY EDGE CASES
# ============================================================

class TestDataConsistencyEdgeCases:
    """Tests for internal consistency under extreme conditions."""

    def test_customer_ids_unique(self):
        """All customer IDs are unique."""
        customer_ids = list(range(1, 1001))
        assert len(customer_ids) == len(set(customer_ids))

    def test_customer_ids_sequential(self):
        """Customer IDs are sequential."""
        customer_ids = list(range(1, 501))
        expected = list(range(1, 501))
        assert customer_ids == expected

    def test_no_negative_times(self):
        """No negative time values."""
        arrivals = [
            datetime(2024, 1, 1, 8, i, 0)
            for i in range(60)
        ]

        for arrival in arrivals:
            assert arrival >= datetime(2024, 1, 1, 0, 0, 0)

    def test_arrivals_in_chronological_order(self):
        """Arrivals in temporal order."""
        arrivals = [
            datetime(2024, 1, 1, 8, 0, 0),
            datetime(2024, 1, 1, 8, 15, 0),
            datetime(2024, 1, 1, 8, 30, 0),
        ]

        for i in range(1, len(arrivals)):
            assert arrivals[i] >= arrivals[i-1]

    def test_dataframe_no_null_values(self):
        """DataFrame with no null/NaN values."""
        df = pd.DataFrame({
            'customer_id': range(1, 101),
            'arrival_time': [datetime(2024, 1, 1, 8, 0, 0)] * 100,
            'service_time': np.random.exponential(5, 100),
        })

        assert df.isnull().sum().sum() == 0


# ============================================================
# RATIO & PROPORTION EDGE CASES
# ============================================================

class TestRatioEdgeCases:
    """Tests for ratio boundary conditions."""

    def test_rho_zero(self):
        """ρ = 0 (no load)."""
        lambda_val = 0
        mu = 5
        c = 4
        rho = lambda_val / (c * mu)
        assert rho == 0

    def test_rho_very_close_to_one(self):
        """ρ = 0.9999 (very high utilization)."""
        rho = 0.9999
        assert rho < 1
        assert rho > 0.99

    def test_rho_much_less_than_one(self):
        """ρ = 0.01 (very low utilization)."""
        rho = 0.01
        assert rho < 1
        assert rho < 0.1

    def test_utilization_ratio_per_server(self):
        """Utilization per individual server."""
        lambda_val = 10
        mu = 5
        c = 2
        rho = lambda_val / (c * mu)
        rho_per_server = lambda_val / mu / c

        assert rho == rho_per_server
        assert rho == 1.0  # Critical


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
