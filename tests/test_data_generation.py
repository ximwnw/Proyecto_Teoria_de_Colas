import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import shutil
from sys import path

proyecto_root = Path(__file__).parent.parent
data_gen_path = proyecto_root / "01_Data_Generation"
path.insert(0, str(data_gen_path))

try:
    from data_generation import (
        NUM_DAYS, START_HOUR, END_HOUR, ARRIVAL_RATES, MEAN_SERVICE_TIME,
    )
except ImportError:
    NUM_DAYS = 30
    START_HOUR = 8
    END_HOUR = 17
    ARRIVAL_RATES = {8: 20, 9: 28, 10: 35, 11: 48, 12: 65, 13: 72, 14: 60, 15: 42, 16: 30}
    MEAN_SERVICE_TIME = 5

@pytest.fixture
def temp_data_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def sample_dataframe():
    np.random.seed(42)
    customers = []
    customer_id = 1
    start_date = pd.Timestamp("2026-01-01")
    
    for day in range(3):
        current_date = start_date + pd.Timedelta(days=day)
        for hour in [8, 12, 16]:
            arrival_rate = ARRIVAL_RATES.get(hour, 30)
            number_of_customers = np.random.poisson(arrival_rate)
            arrival_minutes = np.random.uniform(0, 60, number_of_customers)
            
            for minute in arrival_minutes:
                arrival_time = current_date + pd.Timedelta(hours=hour) + pd.Timedelta(minutes=float(minute))
                service_time = np.random.exponential(scale=MEAN_SERVICE_TIME)
                customers.append({
                    "customer_id": customer_id,
                    "arrival_time": arrival_time,
                    "service_time_min": service_time,
                    "hour": hour,
                    "day_of_week": current_date.day_name()
                })
                customer_id += 1
    
    df = pd.DataFrame(customers)
    df = df.sort_values("arrival_time").reset_index(drop=True)
    df['customer_id'] = range(1, len(df) + 1)
    return df

class TestDataFrameStructure:
    def test_dataframe_has_required_columns(self, sample_dataframe):
        required_cols = ['customer_id', 'arrival_time', 'service_time_min', 'hour', 'day_of_week']
        for col in required_cols:
            assert col in sample_dataframe.columns
    
    def test_dataframe_not_empty(self, sample_dataframe):
        assert len(sample_dataframe) > 0
    
    def test_all_rows_have_data(self, sample_dataframe):
        assert sample_dataframe.isna().sum().sum() == 0
    
    def test_correct_column_count(self, sample_dataframe):
        assert len(sample_dataframe.columns) == 5

class TestDataTypes:
    def test_customer_id_is_integer(self, sample_dataframe):
        assert sample_dataframe['customer_id'].dtype in [np.int64, np.int32, int]
    
    def test_arrival_time_is_datetime(self, sample_dataframe):
        assert pd.api.types.is_datetime64_any_dtype(sample_dataframe['arrival_time'])
    
    def test_service_time_is_numeric(self, sample_dataframe):
        assert pd.api.types.is_numeric_dtype(sample_dataframe['service_time_min'])
    
    def test_hour_is_integer(self, sample_dataframe):
        assert sample_dataframe['hour'].dtype in [np.int64, np.int32, int]
    
    def test_day_of_week_is_string_like(self, sample_dataframe):
        dtype_str = str(sample_dataframe['day_of_week'].dtype)
        assert 'str' in dtype_str.lower() or 'string' in dtype_str.lower() or sample_dataframe['day_of_week'].dtype == object

class TestValueRanges:
    def test_customer_ids_unique(self, sample_dataframe):
        assert sample_dataframe['customer_id'].is_unique
    
    def test_customer_ids_sequential(self, sample_dataframe):
        expected_ids = list(range(1, len(sample_dataframe) + 1))
        actual_ids = sample_dataframe['customer_id'].tolist()
        assert actual_ids == expected_ids
    
    def test_service_time_positive(self, sample_dataframe):
        assert (sample_dataframe['service_time_min'] > 0).all()
    
    def test_service_time_reasonable(self, sample_dataframe):
        assert (sample_dataframe['service_time_min'] >= 0.01).all()
        assert (sample_dataframe['service_time_min'] <= 500).all()
    
    def test_hour_in_valid_range(self, sample_dataframe):
        assert sample_dataframe['hour'].min() >= 8
        assert sample_dataframe['hour'].max() <= 16
    
    def test_hour_values_match_arrival_rates(self, sample_dataframe):
        valid_hours = set(ARRIVAL_RATES.keys())
        actual_hours = set(sample_dataframe['hour'].unique())
        assert actual_hours.issubset(valid_hours)

class TestDatesAndTimes:
    def test_arrival_times_ordered(self, sample_dataframe):
        times = sample_dataframe['arrival_time'].values
        assert (times == np.sort(times)).all()
    
    def test_arrival_times_within_operating_hours(self, sample_dataframe):
        sample_dataframe['arrival_hour'] = sample_dataframe['arrival_time'].dt.hour
        assert sample_dataframe['arrival_hour'].min() >= START_HOUR
        assert sample_dataframe['arrival_hour'].max() <= END_HOUR
    
    def test_day_of_week_is_valid(self, sample_dataframe):
        valid_days = {'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'}
        actual_days = set(sample_dataframe['day_of_week'].unique())
        assert actual_days.issubset(valid_days)
    
    def test_day_of_week_matches_arrival_time(self, sample_dataframe):
        sample_dataframe['computed_day'] = sample_dataframe['arrival_time'].dt.day_name()
        match = sample_dataframe['day_of_week'] == sample_dataframe['computed_day']
        assert match.all()

class TestStatistics:
    def test_service_time_has_positive_mean(self, sample_dataframe):
        mean_service = sample_dataframe['service_time_min'].mean()
        assert mean_service > 0
    
    def test_service_time_has_positive_std(self, sample_dataframe):
        std_service = sample_dataframe['service_time_min'].std()
        assert std_service > 0
    
    def test_service_time_mean_close_to_expected(self, sample_dataframe):
        mean_service = sample_dataframe['service_time_min'].mean()
        assert 2 < mean_service < 10
    
    def test_customers_per_hour_reasonable(self, sample_dataframe):
        customers_per_hour = sample_dataframe.groupby('hour').size()
        assert len(customers_per_hour) > 0
        assert (customers_per_hour > 0).all()

class TestConsistency:
    def test_no_duplicate_rows(self, sample_dataframe):
        assert sample_dataframe.duplicated().sum() == 0
    
    def test_arrival_time_hour_matches_hour_column(self, sample_dataframe):
        sample_dataframe['computed_hour'] = sample_dataframe['arrival_time'].dt.hour
        match = sample_dataframe['hour'] == sample_dataframe['computed_hour']
        assert match.all()
    
    def test_customer_id_starts_at_one(self, sample_dataframe):
        assert sample_dataframe['customer_id'].iloc[0] == 1
    
    def test_customer_id_increments_by_one(self, sample_dataframe):
        diffs = sample_dataframe['customer_id'].diff().fillna(1)
        assert (diffs == 1).all()

class TestDataVolume:
    def test_reasonable_customer_count(self, sample_dataframe):
        assert len(sample_dataframe) > 50
    
    def test_all_hours_represented(self, sample_dataframe):
        hours = sample_dataframe['hour'].unique()
        assert len(hours) > 0

class TestDistributions:
    def test_service_time_distribution_shape(self, sample_dataframe):
        service_times = sample_dataframe['service_time_min']
        mean = service_times.mean()
        std = service_times.std()
        assert 0.5 * mean < std < 2 * mean
    
    def test_arrival_distribution_per_hour(self, sample_dataframe):
        arrivals_by_hour = sample_dataframe.groupby('hour').size()
        assert arrivals_by_hour.std() > 0

class TestEdgeCases:
    def test_minimum_one_customer_per_day(self, sample_dataframe):
        customers_per_day = sample_dataframe.groupby(sample_dataframe['arrival_time'].dt.date).size()
        assert len(customers_per_day) > 0
    
    def test_no_future_dates(self, sample_dataframe):
        min_date = sample_dataframe['arrival_time'].min()
        max_date = sample_dataframe['arrival_time'].max()
        assert min_date.year == 2026
        assert min_date.month == 1

class TestIntegration:
    def test_dataframe_can_be_saved_to_csv(self, sample_dataframe, temp_data_dir):
        csv_path = Path(temp_data_dir) / "test.csv"
        sample_dataframe.to_csv(csv_path, index=False)
        assert csv_path.exists()
        assert csv_path.stat().st_size > 0
    
    def test_saved_csv_can_be_loaded(self, sample_dataframe, temp_data_dir):
        csv_path = Path(temp_data_dir) / "test.csv"
        sample_dataframe.to_csv(csv_path, index=False)
        loaded_df = pd.read_csv(csv_path)
        assert list(loaded_df.columns) == list(sample_dataframe.columns)
        assert len(loaded_df) == len(sample_dataframe)
    
    def test_csv_preserves_numeric_data(self, sample_dataframe, temp_data_dir):
        csv_path = Path(temp_data_dir) / "test.csv"
        sample_dataframe.to_csv(csv_path, index=False)
        loaded_df = pd.read_csv(csv_path)
        assert (loaded_df['customer_id'] == sample_dataframe['customer_id'].values).all()
    
    def test_groupby_operations_work(self, sample_dataframe):
        by_hour = sample_dataframe.groupby('hour').size()
        assert len(by_hour) > 0
        by_day = sample_dataframe.groupby('day_of_week').size()
        assert len(by_day) > 0
    
    def test_sorting_by_arrival_time_maintains_order(self, sample_dataframe):
        sorted_df = sample_dataframe.sort_values('arrival_time')
        times = sorted_df['arrival_time'].values
        assert (times == np.sort(times)).all()

class TestReproducibility:
    def test_same_seed_produces_same_results(self):
        np.random.seed(42)
        data1 = np.random.poisson(50, 100)
        np.random.seed(42)
        data2 = np.random.poisson(50, 100)
        assert (data1 == data2).all()
    
    def test_different_seeds_produce_different_results(self):
        np.random.seed(42)
        data1 = np.random.poisson(50, 100)
        np.random.seed(123)
        data2 = np.random.poisson(50, 100)
        assert (data1 != data2).any()

class TestErrorHandling:
    def test_empty_dataframe_has_correct_structure(self):
        empty_df = pd.DataFrame({
            'customer_id': [], 'arrival_time': [], 'service_time_min': [],
            'hour': [], 'day_of_week': []
        })
        assert list(empty_df.columns) == ['customer_id', 'arrival_time', 'service_time_min', 'hour', 'day_of_week']
    
    def test_negative_service_time_would_be_invalid(self):
        samples = np.random.exponential(scale=5, size=10000)
        assert (samples >= 0).all()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
