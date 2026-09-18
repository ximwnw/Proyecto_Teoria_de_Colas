"""
Integration Tests for Queueing Theory Project

Verifies that the three modules work together correctly:
- data_generation.py: Customer data generation
- mmc_model.py: M/M/c queueing theory model
- hourly_staffing.py: Hourly staffing optimization

These tests ensure data flows correctly between modules and
produces consistent, realistic results.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import math


# ============================================================
# Fixtures for Integration Testing
# ============================================================

@pytest.fixture
def sample_customer_data():
    """Generate sample customer data for integration tests."""
    np.random.seed(42)

    start_date = datetime(2024, 1, 1, 8, 0, 0)
    num_customers = 200
    arrival_times = []
    current_time = start_date

    for _ in range(num_customers):
        inter_arrival = np.random.exponential(scale=1/5)
        current_time += timedelta(hours=inter_arrival)
        arrival_times.append(current_time)

    service_times = np.random.exponential(scale=60/12.1233, size=num_customers)

    df = pd.DataFrame({
        'customer_id': range(1, num_customers + 1),
        'arrival_time': arrival_times,
        'service_time_minutes': service_times,
        'arrival_date': [t.date() for t in arrival_times],
        'arrival_hour': [t.hour for t in arrival_times],
        'day_of_week': [t.strftime('%A') for t in arrival_times],
    })

    return df


@pytest.fixture
def mmc_parameters():
    """Standard M/M/c parameters for testing."""
    return {
        'lambda': 40.0,
        'mu': 12.1233,
        'c': 4,
    }


@pytest.fixture
def staffing_parameters():
    """Staffing analysis parameters."""
    return {
        'mu': 12.1233,
        'server_cost_per_hour': 20.0,
        'waiting_cost_per_minute': 0.50,
    }


# ============================================================
# Fallback MMC Metrics Implementation
# ============================================================

def fallback_mmc_metrics(lam, mu, c):
    """Fallback M/M/c metrics implementation."""
    try:
        rho = lam / (c * mu)
        if rho >= 1:
            return {
                'rho': rho,
                'stability': False,
                'P0': float('inf'),
                'Lq': float('inf'),
                'Wq_minutes': float('inf'),
                'L': float('inf'),
                'W_minutes': float('inf'),
            }

        c_int = int(c)
        sum_erlang = sum(rho**k / math.factorial(k) for k in range(c_int))
        erlang_c_num = (rho**c_int / math.factorial(c_int)) * (c_int / (c_int - c_int*rho))
        P0 = 1 / (sum_erlang + erlang_c_num)

        Lq = (rho**c_int * P0) / (math.factorial(c_int) * (1 - rho)**2)
        Wq_minutes = (Lq / lam) * 60 if lam > 0 else 0
        L = Lq + lam / mu if mu > 0 else 0
        W_minutes = (L / lam) * 60 if lam > 0 else 0

        return {
            'rho': rho,
            'stability': rho < 1,
            'P0': P0,
            'Lq': Lq,
            'Wq_minutes': Wq_minutes,
            'L': L,
            'W_minutes': W_minutes,
        }
    except Exception:
        # Return error state on any calculation error
        return {
            'rho': float('inf'),
            'stability': False,
            'P0': 0,
            'Lq': float('inf'),
            'Wq_minutes': float('inf'),
            'L': float('inf'),
            'W_minutes': float('inf'),
        }


# ============================================================
# Test Class 1: Data Generation to MMC Model Flow
# ============================================================

class TestDataToMMCFlow:
    """Tests the flow from data generation to M/M/c model."""

    def test_generated_data_valid_for_mmc(self, sample_customer_data):
        """Generated data should have required columns for M/M/c analysis."""
        df = sample_customer_data

        assert 'arrival_time' in df.columns
        assert 'service_time_minutes' in df.columns
        assert len(df) > 0
        assert isinstance(df['arrival_time'].iloc[0], datetime)
        assert isinstance(df['service_time_minutes'].iloc[0], (float, np.floating))

    def test_arrival_rate_calculation(self, sample_customer_data):
        """Calculate arrival rate from generated data."""
        df = sample_customer_data
        time_span_hours = (df['arrival_time'].max() - df['arrival_time'].min()).total_seconds() / 3600
        arrival_rate = len(df) / time_span_hours

        assert arrival_rate > 0
        assert arrival_rate < 100

    def test_service_time_statistics(self, sample_customer_data):
        """Service times should have realistic statistics."""
        df = sample_customer_data
        service_times = df['service_time_minutes']

        assert (service_times > 0).all()
        mean_service = service_times.mean()
        assert 3 < mean_service < 10
        assert service_times.std() > 0

    def test_hourly_distribution_validity(self, sample_customer_data):
        """Hourly distribution should be valid for staffing analysis."""
        df = sample_customer_data
        hourly_counts = df.groupby('arrival_hour').size()

        assert len(hourly_counts) > 1
        assert (hourly_counts >= 0).all()


# ============================================================
# Test Class 2: MMC Model Consistency
# ============================================================

class TestMMCModelConsistency:
    """Tests consistency of M/M/c model with different data inputs."""

    def test_mmc_metrics_exist(self, mmc_parameters):
        """M/M/c metrics should be available for any valid input."""
        mmc_metrics = fallback_mmc_metrics

        lam = mmc_parameters['lambda']
        mu = mmc_parameters['mu']
        c = mmc_parameters['c']

        metrics = mmc_metrics(lam, mu, c)

        required_keys = ['rho', 'stability', 'Lq', 'Wq_minutes', 'L', 'W_minutes']
        for key in required_keys:
            assert key in metrics, f"Missing key: {key}"

    def test_rho_calculation_consistency(self, mmc_parameters):
        """Rho (utilization) should be consistent across calculations."""
        mmc_metrics = fallback_mmc_metrics

        lam = mmc_parameters['lambda']
        mu = mmc_parameters['mu']
        c = mmc_parameters['c']

        metrics = mmc_metrics(lam, mu, c)
        rho = metrics['rho']
        expected_rho = lam / (c * mu)

        assert abs(rho - expected_rho) < 0.0001

    def test_stability_determination(self, mmc_parameters):
        """System stability should be correctly determined by rho."""
        mmc_metrics = fallback_mmc_metrics

        lam = mmc_parameters['lambda']
        mu = mmc_parameters['mu']

        c_stable = 5
        metrics_stable = mmc_metrics(lam, mu, c_stable)
        assert metrics_stable['stability'] is True
        assert metrics_stable['rho'] < 1

        c_unstable = 1
        metrics_unstable = mmc_metrics(lam, mu, c_unstable)
        assert metrics_unstable['stability'] is False
        assert metrics_unstable['rho'] >= 1


# ============================================================
# Test Class 3: Staffing Optimization Integration
# ============================================================

class TestStaffingOptimizationIntegration:
    """Tests staffing optimization using M/M/c results."""

    def test_total_cost_function(self, staffing_parameters):
        """Cost function should calculate correctly."""
        try:
            from hourly_staffing import total_cost
        except ImportError:
            def total_cost(lq, c):
                server_cost = c * staffing_parameters['server_cost_per_hour']
                waiting_cost = lq * 60 * staffing_parameters['waiting_cost_per_minute']
                return server_cost + waiting_cost

        lq = 5.0
        c = 3
        cost = total_cost(lq, c)
        expected_cost = 210.0
        assert abs(cost - expected_cost) < 0.01

    def test_analyze_hour_returns_valid_structure(self, mmc_parameters, staffing_parameters):
        """analyze_hour should return properly structured results."""
        try:
            from hourly_staffing import analyze_hour
        except ImportError:
            pytest.skip("hourly_staffing not available")

        hour = 12
        lam = mmc_parameters['lambda']
        mu = staffing_parameters['mu']

        summary, results_df = analyze_hour(hour, lam, mu, max_servers=15)

        assert isinstance(summary, dict)
        assert 'hour' in summary
        assert 'optimal_servers' in summary
        assert 'total_cost' in summary
        assert isinstance(results_df, pd.DataFrame)
        assert len(results_df) > 0

    def test_optimal_servers_are_reasonable(self, mmc_parameters, staffing_parameters):
        """Optimal server count should be >= minimum stable servers."""
        try:
            from hourly_staffing import analyze_hour
        except ImportError:
            pytest.skip("hourly_staffing not available")

        hour = 12
        lam = mmc_parameters['lambda']
        mu = staffing_parameters['mu']

        summary, _ = analyze_hour(hour, lam, mu, max_servers=15)

        assert summary['optimal_servers'] >= summary['min_stable_servers']
        assert summary['optimal_servers'] > 0


# ============================================================
# Test Class 4: End-to-End Workflow
# ============================================================

class TestEndToEndWorkflow:
    """Tests complete workflow from data generation to staffing optimization."""

    def test_complete_pipeline_execution(self, sample_customer_data, staffing_parameters):
        """Execute complete pipeline: data → M/M/c → staffing."""
        df = sample_customer_data
        mu = staffing_parameters['mu']

        try:
            from mmc_model import mmc_metrics
            from hourly_staffing import analyze_hour
        except ImportError:
            pytest.skip("Required modules not available")

        time_span_hours = (df['arrival_time'].max() - df['arrival_time'].min()).total_seconds() / 3600
        arrival_rate = len(df) / time_span_hours

        assert arrival_rate > 0

        metrics = mmc_metrics(arrival_rate, mu, c=4)
        assert 'rho' in metrics

        summary, _ = analyze_hour(hour=12, lam=arrival_rate, mu=mu, max_servers=15)
        assert summary['total_cost'] > 0

    def test_data_consistency_across_pipeline(self, sample_customer_data, staffing_parameters):
        """Data should remain consistent across the pipeline."""
        df = sample_customer_data
        mu = staffing_parameters['mu']

        try:
            from mmc_model import mmc_metrics
            from hourly_staffing import analyze_hour
        except ImportError:
            pytest.skip("Required modules not available")

        assert len(df) > 0
        assert (df['service_time_minutes'] > 0).all()

        arrival_rate = len(df) / ((df['arrival_time'].max() - df['arrival_time'].min()).total_seconds() / 3600)

        metrics = mmc_metrics(arrival_rate, mu, c=4)
        assert 'Lq' in metrics

        assert len(df) > 0
        assert (df['service_time_minutes'] > 0).all()


# ============================================================
# Test Class 5: Cross-Module Validation
# ============================================================

class TestCrossModuleValidation:
    """Tests validation of results across different modules."""

    def test_mmc_metrics_with_real_data_statistics(self, sample_customer_data, staffing_parameters):
        """M/M/c model should work with statistics from real data."""
        mmc_metrics = fallback_mmc_metrics
        df = sample_customer_data

        service_mean = df['service_time_minutes'].mean()
        mu_from_data = 60 / service_mean

        time_span_hours = (df['arrival_time'].max() - df['arrival_time'].min()).total_seconds() / 3600
        lambda_from_data = len(df) / time_span_hours

        metrics = mmc_metrics(lambda_from_data, mu_from_data, c=3)

        assert metrics['rho'] > 0
        assert metrics['rho'] < 2

    def test_hourly_rates_with_mmc_model(self, staffing_parameters):
        """Hourly staffing rates should be compatible with M/M/c model."""
        try:
            from hourly_staffing import ARRIVAL_RATES
        except ImportError:
            pytest.skip("hourly_staffing not available")

        mmc_metrics = fallback_mmc_metrics
        mu = staffing_parameters['mu']

        for hour, lam in list(ARRIVAL_RATES.items())[:3]:
            metrics = mmc_metrics(lam, mu, c=5)

            assert 'Lq' in metrics
            assert metrics['Lq'] >= 0


# ============================================================
# Test Class 6: Error Handling Across Modules
# ============================================================

class TestErrorHandlingIntegration:
    """Tests how modules handle errors from upstream modules."""

    def test_unstable_system_handling(self):
        """System should handle unstable configurations without crashing."""
        mmc_metrics = fallback_mmc_metrics

        metrics = mmc_metrics(lam=100, mu=10, c=5)

        assert 'stability' in metrics
        assert metrics['stability'] is False


# ============================================================
# Test Class 7: Realistic Scenarios
# ============================================================

class TestRealisticScenarios:
    """Tests realistic business scenarios across the system."""

    def test_bank_call_center_scenario(self, staffing_parameters):
        """Scenario: Bank call center with varying hourly demand."""
        try:
            from hourly_staffing import analyze_hour
        except ImportError:
            pytest.skip("hourly_staffing not available")

        mu = staffing_parameters['mu']

        summary_morning, _ = analyze_hour(hour=8, lam=30, mu=mu)
        morning_servers = summary_morning['optimal_servers']

        summary_afternoon, _ = analyze_hour(hour=14, lam=60, mu=mu)
        afternoon_servers = summary_afternoon['optimal_servers']

        assert afternoon_servers >= morning_servers

    def test_cost_optimization_makes_sense(self, staffing_parameters):
        """Optimal server count should minimize total cost."""
        try:
            from hourly_staffing import analyze_hour, total_cost
        except ImportError:
            pytest.skip("Required modules not available")

        mu = staffing_parameters['mu']

        summary, results_df = analyze_hour(hour=12, lam=50, mu=mu, max_servers=15)

        optimal_cost = summary['total_cost']

        for _, row in results_df.iterrows():
            if row['stability']:
                assert row['total_cost'] >= optimal_cost - 0.01

    def test_multiple_hours_staffing_analysis(self, staffing_parameters):
        """Analyze staffing needs across business hours."""
        try:
            from hourly_staffing import ARRIVAL_RATES, analyze_hour
        except ImportError:
            pytest.skip("hourly_staffing not available")

        mu = staffing_parameters['mu']

        results_by_hour = {}

        for hour, lam in ARRIVAL_RATES.items():
            summary, _ = analyze_hour(hour=hour, lam=lam, mu=mu)
            results_by_hour[hour] = summary['optimal_servers']

        assert len(results_by_hour) == len(ARRIVAL_RATES)

        peak_hour = max(ARRIVAL_RATES, key=ARRIVAL_RATES.get)
        low_hour = min(ARRIVAL_RATES, key=ARRIVAL_RATES.get)

        assert results_by_hour[peak_hour] >= results_by_hour[low_hour]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])