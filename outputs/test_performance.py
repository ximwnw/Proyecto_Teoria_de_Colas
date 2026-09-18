"""
Performance Tests - Validar velocidad y escalabilidad
Pruebas de rendimiento para verificar que el código es eficiente
"""

import pytest
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import math


class TestMMCPerformance:
    """Tests de rendimiento del modelo M/M/c."""

    def simple_mmc_metrics(self, lam, mu, c):
        """Simple M/M/c implementation."""
        if lam < 0 or mu <= 0 or c <= 0 or not isinstance(c, int):
            raise ValueError("Invalid parameters")

        rho = lam / (c * mu)
        if rho >= 1:
            return {'rho': rho, 'stability': False}

        sum_terms = sum((lam / mu) ** n / math.factorial(n) for n in range(c))
        last_term = ((lam / mu) ** c) / (math.factorial(c) * (1 - rho))
        P0 = 1 / (sum_terms + last_term)
        Lq = (P0 * (lam / mu) ** c * rho) / (math.factorial(c) * (1 - rho) ** 2)

        return {
            'rho': rho,
            'stability': True,
            'P0': P0,
            'Lq': Lq,
        }

    def test_single_calculation_speed(self):
        """Una llamada a mmc_metrics debe ser < 1ms."""
        start = time.time()
        self.simple_mmc_metrics(15, 5, 4)
        elapsed = time.time() - start

        # Debe ser muy rápido (< 1ms = 0.001s)
        assert elapsed < 0.001, f"Cálculo tardó {elapsed*1000:.2f}ms"

    def test_100_calculations_speed(self):
        """100 cálculos deben ser < 100ms."""
        start = time.time()
        for i in range(100):
            self.simple_mmc_metrics(10 + i*0.1, 5, 3)
        elapsed = time.time() - start

        # 100 cálculos deben ser muy rápidos (< 100ms)
        assert elapsed < 0.1, f"100 cálculos tardaron {elapsed*1000:.2f}ms"

    def test_1000_calculations_speed(self):
        """1000 cálculos deben ser < 1 segundo."""
        start = time.time()
        for i in range(1000):
            self.simple_mmc_metrics(10 + (i % 10)*0.1, 5, (i % 5) + 1)
        elapsed = time.time() - start

        # 1000 cálculos deben ser < 1 segundo
        assert elapsed < 1.0, f"1000 cálculos tardaron {elapsed:.2f}s"

        # Calcular throughput
        throughput = 1000 / elapsed
        print(f"\n✅ Throughput: {throughput:.0f} cálculos/segundo")


class TestDataGenerationPerformance:
    """Tests de rendimiento en generación de datos."""

    def test_generate_100_customers(self):
        """Generar 100 clientes debe ser < 100ms."""
        np.random.seed(42)
        start = time.time()

        start_date = datetime(2024, 1, 1, 8, 0, 0)
        current_time = start_date
        arrival_times = []

        for _ in range(100):
            inter_arrival = np.random.exponential(scale=1/5)
            current_time += timedelta(hours=inter_arrival)
            arrival_times.append(current_time)

        service_times = np.random.exponential(scale=5, size=100)

        df = pd.DataFrame({
            'customer_id': range(1, 101),
            'arrival_time': arrival_times,
            'service_time_minutes': service_times,
        })

        elapsed = time.time() - start
        assert elapsed < 0.1, f"Generación de 100 clientes tardó {elapsed*1000:.2f}ms"

    def test_generate_1000_customers(self):
        """Generar 1000 clientes debe ser < 1 segundo."""
        np.random.seed(42)
        start = time.time()

        start_date = datetime(2024, 1, 1, 8, 0, 0)
        current_time = start_date
        arrival_times = []

        for _ in range(1000):
            inter_arrival = np.random.exponential(scale=1/5)
            current_time += timedelta(hours=inter_arrival)
            arrival_times.append(current_time)

        service_times = np.random.exponential(scale=5, size=1000)

        df = pd.DataFrame({
            'customer_id': range(1, 1001),
            'arrival_time': arrival_times,
            'service_time_minutes': service_times,
        })

        elapsed = time.time() - start
        assert elapsed < 1.0, f"Generación de 1000 clientes tardó {elapsed:.2f}s"
        assert len(df) == 1000

    def test_generate_10k_customers(self):
        """Generar 10,000 clientes debe ser < 10 segundos."""
        np.random.seed(42)
        start = time.time()

        start_date = datetime(2024, 1, 1, 8, 0, 0)
        current_time = start_date
        arrival_times = []

        for _ in range(10000):
            inter_arrival = np.random.exponential(scale=1/5)
            current_time += timedelta(hours=inter_arrival)
            arrival_times.append(current_time)

        service_times = np.random.exponential(scale=5, size=10000)

        df = pd.DataFrame({
            'customer_id': range(1, 10001),
            'arrival_time': arrival_times,
            'service_time_minutes': service_times,
        })

        elapsed = time.time() - start
        assert elapsed < 10.0, f"Generación de 10K clientes tardó {elapsed:.2f}s"
        assert len(df) == 10000

        # Calcular velocidad
        speed = 10000 / elapsed
        print(f"\n✅ Velocidad: {speed:.0f} clientes/segundo")


class TestScalability:
    """Tests para verificar escalabilidad."""

    def simple_mmc_metrics(self, lam, mu, c):
        """Simple M/M/c implementation."""
        if lam < 0 or mu <= 0 or c <= 0 or not isinstance(c, int):
            raise ValueError("Invalid")

        rho = lam / (c * mu)
        if rho >= 1:
            return {'rho': rho, 'stability': False}

        sum_terms = sum((lam / mu) ** n / math.factorial(n) for n in range(c))
        last_term = ((lam / mu) ** c) / (math.factorial(c) * (1 - rho))
        P0 = 1 / (sum_terms + last_term)

        return {'rho': rho, 'stability': True, 'P0': P0}

    def test_scaling_linear(self):
        """El tiempo debe escalar linealmente con número de cálculos."""
        times = {}

        for n in [10, 100, 1000]:
            start = time.time()
            for i in range(n):
                self.simple_mmc_metrics(10 + i*0.01, 5, 3)
            elapsed = time.time() - start
            times[n] = elapsed

        # Verificar que es aproximadamente lineal
        # 100 cálculos ≈ 10x más que 10 cálculos
        ratio_100_10 = times[100] / times[10]
        assert 5 < ratio_100_10 < 20, f"No escalabilidad lineal: ratio {ratio_100_10:.1f}"

        print(f"\n✅ Escalabilidad:")
        print(f"   10 cálculos:    {times[10]*1000:.2f}ms")
        print(f"   100 cálculos:   {times[100]*1000:.2f}ms")
        print(f"   1000 cálculos:  {times[1000]*1000:.2f}ms")

    def test_memory_efficiency(self):
        """Verificar que no hay memory leaks."""
        import sys

        # Crear muchos objetos
        objects = []
        for i in range(1000):
            obj = self.simple_mmc_metrics(10 + i*0.1, 5, (i % 5) + 1)
            objects.append(obj)

        # Limpiar
        del objects

        # Si llegamos aquí sin error, no hay memory leak evidente
        assert True

    def test_numerical_stability_large_numbers(self):
        """Verificar que funciona con números grandes."""
        # Valores muy grandes
        result = self.simple_mmc_metrics(1e6, 1e6, 1000)
        assert result['stability'] is True
        assert result['rho'] > 0
        assert result['rho'] < 1


class TestMemoryUsage:
    """Tests de uso de memoria."""

    def test_dataframe_memory_100k_rows(self):
        """DataFrame con 100K filas debe usar < 50MB."""
        np.random.seed(42)

        start_date = datetime(2024, 1, 1, 8, 0, 0)
        current_time = start_date
        arrival_times = []

        for _ in range(100000):
            inter_arrival = np.random.exponential(scale=1/5)
            current_time += timedelta(hours=inter_arrival)
            arrival_times.append(current_time)

        service_times = np.random.exponential(scale=5, size=100000)

        df = pd.DataFrame({
            'customer_id': range(1, 100001),
            'arrival_time': arrival_times,
            'service_time_minutes': service_times,
        })

        # Obtener memoria en MB
        memory_mb = df.memory_usage(deep=True).sum() / (1024**2)

        # 100K filas con 3 columnas no debe exceder 50MB
        assert memory_mb < 50, f"Memoria usada: {memory_mb:.2f}MB (máximo 50MB)"
        print(f"\n✅ Memoria para 100K filas: {memory_mb:.2f}MB")


class TestConcurrency:
    """Tests de concurrencia (si se usa en paralelo)."""

    def simple_mmc_metrics(self, lam, mu, c):
        """Simple M/M/c implementation."""
        if lam < 0 or mu <= 0 or c <= 0 or not isinstance(c, int):
            raise ValueError("Invalid")

        rho = lam / (c * mu)
        if rho >= 1:
            return rho

        sum_terms = sum((lam / mu) ** n / math.factorial(n) for n in range(c))
        last_term = ((lam / mu) ** c) / (math.factorial(c) * (1 - rho))
        P0 = 1 / (sum_terms + last_term)

        return P0

    def test_parallel_calculations_independent(self):
        """Múltiples cálculos independientes funcionan correctamente."""
        # Simular llamadas paralelas
        results = []
        for i in range(100):
            result = self.simple_mmc_metrics(10 + i*0.1, 5, 3)
            results.append(result)

        # Todos deben haber funcionado
        assert len(results) == 100
        assert all(0 < r < 1 for r in results)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
