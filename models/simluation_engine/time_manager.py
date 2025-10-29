class TimeManager:
    def __init__(self, time_resolution: str):
        self.resolution = time_resolution
        self.resolution_mapping = {
            'day': 1,
            'week': 7,
            'month': 30
        }

        if time_resolution not in self.resolution_mapping:
            raise ValueError(f"Invalid time resolution: {time_resolution}")

        self.days_per_step = self.resolution_mapping[time_resolution]

    def convert_to_simulation_time(self, real_time_days: float) -> int:
        return int(real_time_days / self.days_per_step)

    def convert_to_real_time(self, simulation_steps: int) -> float:
        return simulation_steps * self.days_per_step

    # def get_temporal_weights(self, t: int) -> dict:
    #     """Get temporal weights for seasonal/cyclical effects."""
    #
    #     # Convert to day of year
    #     day_of_year = (t * self.days_per_step) % 365
    #
    #     # Seasonal weights (example: agriculture seasonality)
    #     seasonal_weight = 1.0 + 0.3 * np.sin(2 * np.pi * day_of_year / 365)
    #
    #     return {
    #         'seasonal': seasonal_weight,
    #         'trend': 1.0,  # Long-term trend factor
    #         'cyclical': 1.0  # Business cycle factor
    #     }