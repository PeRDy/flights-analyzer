import time

from getgauge.python import step


@step("Wait <seconds> seconds")
def wait_seconds(seconds):
    time.sleep(int(seconds))
