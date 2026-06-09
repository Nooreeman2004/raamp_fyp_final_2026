import asyncio
import os
from infrastructure.database.database import connect_to_mongo, init_db
from infrastructure.database.models.trend_detection_model import TrendDetectionModel
from infrastructure.database.models.trend_signal_model import TrendSignalModel

async def check_db():
    await connect_to_mongo()
    await init_db()
    
    detection_count = await TrendDetectionModel.count()
    signal_count = await TrendSignalModel.count()
    
    print(f"TrendDetectionModel count: {detection_count}")
    print(f"TrendSignalModel count: {signal_count}")
    
    if detection_count > 0:
        latest_detection = await TrendDetectionModel.find_all().sort("-detected_at").limit(1).to_list()
        print(f"Latest Detection: {latest_detection[0].keyword} at {latest_detection[0].detected_at}")
        
    if signal_count > 0:
        latest_signal = await TrendSignalModel.find_all().sort("-created_at").limit(1).to_list()
        print(f"Latest Signal: {latest_signal[0].keywords} at {latest_signal[0].created_at}")

if __name__ == "__main__":
    asyncio.run(check_db())
