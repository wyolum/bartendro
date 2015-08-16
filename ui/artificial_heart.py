import time
from bartendro.router import driver
import logging
import logging.handlers
import os

LOG_SIZE = 1024 * 500  # 500k maximum log file size
LOG_FILES_SAVED = 3    # number of log files to compress and save

software_only = False

handler = logging.handlers.RotatingFileHandler(os.path.join("logs", "artificial_heart.log"), 
                                               maxBytes=LOG_SIZE, 
                                               backupCount=LOG_FILES_SAVED)
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
logger = logging.getLogger('artificial_heart')
logger.addHandler(handler)
logger.info("Heart start up sequence (clear!):")

router = driver.RouterDriver("/dev/ttyAMA0", software_only);
router.open()
logging.info("Found %d dispensers." % router.count())
if router.count() < 2:
    raise ValueError("Only %d of 3 dispensers found" % router.count())
# raw_input('return to continue')

if software_only:
    logging.info("Running SOFTWARE ONLY VERSION. No communication between software and hardware chain will happen!")
logging.info("artificial_heart started")

ticks_per_pulse = 4
FAST = 255
SLOW = 180
speed = FAST

def align():
    for i in [0, 2]:
        try:
            n_tick = int(raw_input('%d steps?' % i))
            target_tick = router.get_saved_tick_count(i) + n_tick
            router.dispense_ticks(i, n_tick, SLOW)
            while router.get_saved_tick_count(i) < target_tick:
                pass
            router.stop(i)
            time.sleep(1)
            print router.get_saved_tick_count(i), target_tick
        except ValueError:
            pass

class Pump:
    def __init__(self, router, pid):
        self.router = router
        self.pid = pid
        self.last_start = None
        self.target = self.ticks

    def align(self):
        for target in range(3, -1, -1):
            while self.hall != target:
                self.dispense_ticks(1, SLOW)
                time.sleep(.5)

    def dispense_ticks(self, n_tick, speed):
        print n_tick, self.ticks, self.target
        actual_n_tick = n_tick - (self.ticks - self.target)
        print '   ', actual_n_tick
        if actual_n_tick > 0:
            self.target = self.ticks + actual_n_tick
            self.router.dispense_ticks(self.pid, actual_n_tick, speed)
        else:
            self.target += n_tick 
        
    @property
    def hall(self):
        return self.router.get_last_hall(self.pid)

    @property
    def ticks(self):
        return self.router.get_saved_tick_count(self.pid)
try:
    push = 2
    pull = 0
    cycles = 0
    push = Pump(router, push)
    pull = Pump(router, pull)
    ## align pumps
    
    push.align()
    pull.align()
    raw_input('...')
    while 1:
        try:
            push.dispense_ticks(ticks_per_pulse, speed)
            time.sleep(.25)
            pull.dispense_ticks(ticks_per_pulse, speed)
            time.sleep(.75)
            print push.ticks,
            print pull.ticks
            cycles += 1
        except KeyboardInterrupt:
            logging.info("artificial_heart stopped by user.")
            logging.info("cycled %d times" % cycles)
            break
finally:
    for i in range(3):
        router.stop(i)
    router.close()
