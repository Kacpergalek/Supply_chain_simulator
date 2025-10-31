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