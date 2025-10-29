from models.simluation_engine.statistics_manager import StatisticsManager
from models.simluation_engine.time_manager import TimeManager

time_manager = TimeManager('day')
print(time_manager.days_per_step)

statistics_manager = StatisticsManager()
df = statistics_manager.create_dataframe()
statistics_manager.save_to_csv(df)