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
if router.count() != 3:
    raise ValueError("Only %d of 3 dispensers found" % router.count())
router.pattern_define(1, 128)
router.pattern_add_segment(1, 255, 0, 0, 255)
router.pattern_add_segment(1, 0, 255, 0, 255)
router.pattern_add_segment(1, 0, 0, 255, 255)
router.pattern_finish(1)
router._send_packet8(1, 128, 0)
raw_input('return to continue')

if software_only:
    logging.info("Running SOFTWARE ONLY VERSION. No communication between software and hardware chain will happen!")
logging.info("artificial_heart started")

ticks_per_pulse = 4
speed = 255
SLOW = 200

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
try:
    push = 2
    pull = 0
    while 1:
        try:
            router.dispense_ticks(push, ticks_per_pulse - router.get_saved_tick_count(push) % ticks_per_pulse, speed)
            time.sleep(.25)
            router.dispense_ticks(pull, ticks_per_pulse - router.get_saved_tick_count(pull) % ticks_per_pulse, speed)
            time.sleep(.75)
            print router.get_saved_tick_count(push), 
            print router.get_saved_tick_count(pull) 
        except KeyboardInterrupt:
            logging.info("artificial_heart stopped by user.")
            break
finally:
    for i in range(3):
        router.stop(i)
    router.close()
