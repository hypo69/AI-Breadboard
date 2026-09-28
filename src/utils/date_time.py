from datetime import datetime, time
import threading
from src.utils.printer import pprint as print

class TimeoutCheck:

    def __init__(self):
        self.result = None

    def interval(self, start: time=time(23, 0), end: time=time(6, 0)) -> bool:
        """Check if the current time is within the specified interval.
        
        Args:
            start (time): Start of the interval (default is 23:00).
            end (time): End of the interval (default is 06:00).

        Returns:
            bool: True if the current time is within the interval, False otherwise.
        """
        current_time = datetime.now().time()
        if start < end:
            self.result = start <= current_time <= end
        else:
            self.result = current_time >= start or current_time <= end

    def interval_with_timeout(self, timeout: int=5, start: time=time(23, 0), end: time=time(6, 0)) -> bool:
        """Check if the current time is within the specified interval with a timeout.

        Args:
            timeout (int): Time in seconds to wait for the interval check.
            start (time): Start of the interval (default is 23:00).
            end (time): End of the interval (default is 06:00).

        Returns:
            bool: True if the current time is within the interval and response within timeout, False if not or timeout occurs.
        """
        thread = threading.Thread(target=self.interval, args=(start, end))
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            print(f'Timeout occurred after {timeout} seconds, continuing execution.')
            thread.join()
            return False
        return self.result

    def get_input(self):
        """Request input from user."""
        self.user_input = input('U:> ')

    def input_with_timeout(self, timeout: int=5) -> str | None:
        """Wait for input with timeout.

        Args:
            timeout (int): Input wait time in seconds.

        Returns:
            str | None: Entered data or None if timeout occurred.
        """
        thread = threading.Thread(target=self.get_input)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            print(f'Timeout occurred after {timeout} seconds.')
            return
        return self.user_input
if __name__ == '__main__':
    timeout_check = TimeoutCheck()
    if timeout_check.interval_with_timeout(timeout=5):
        print('Current time is within the interval.')
    else:
        print('Current time is outside the interval or timeout occurred.')