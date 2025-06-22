from apscheduler.schedulers.background import BackgroundScheduler
import time

def job():
    print("Hello")

sched = BackgroundScheduler()
sched.add_job(job, 'interval', seconds=5)
sched.start()

while True:
    time.sleep(1)
