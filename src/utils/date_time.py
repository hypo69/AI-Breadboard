# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Time interval checking and timeout utilities
# =============================================================================
# Description:
#   Provides utilities for time interval checking including functions to verify if current
#   time falls within specified interval (useful for scheduled operations). Supports intervals
#   spanning midnight and includes input waiting with timeout functionality.
#
# File: date_time.py
# Project: ai-breadboard
# Package: src.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from datetime import datetime, time
import threading

class TimeoutCheck:
    def __init__(self):
        self.result = None

    def interval(self, start: time = time(23, 0), end: time = time(6, 0)) -> bool:
        """Check if the current time is within the specified interval.
        
        Args:
            start (time): Start of the interval (default is 23:00).
            end (time): End of the interval (default is 06:00).

        Returns:
            bool: True if the current time is within the interval, False otherwise.
        """
        current_time = datetime.now().time()

        if start < end:
            # Interval within the same day (e.g., 08:00 to 17:00)
            self.result = start <= current_time <= end
        else:
            # Interval spanning midnight (e.g., 23:00 to 06:00)
            self.result = current_time >= start or current_time <= end

    def interval_with_timeout(self, timeout: int = 5, start: time = time(23, 0), end: time = time(6, 0)) -> bool:
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
            print(f"Timeout occurred after {timeout} seconds, continuing execution.")
            thread.join()  # Ensures thread stops after timeout
            return False  # Timeout occurred, so returning False
        return self.result

    def get_input(self):
        """Request input from user."""
        self.user_input = input("U:> ")

    def input_with_timeout(self, timeout: int = 5) -> str | None:
        """Wait for input with timeout.

        Args:
            timeout (int): Input wait time in seconds.

        Returns:
            str | None: Entered data or None if timeout occurred.
        """
        # Start thread to get input from user
        thread = threading.Thread(target=self.get_input)
        thread.start()

        # Wait for thread completion or timeout
        thread.join(timeout)

        if thread.is_alive():
            print(f"Timeout occurred after {timeout} seconds.")
            return  # Return None if timeout occurred

        return self.user_input

if __name__ == '__main__':
    # Example usage
    timeout_check = TimeoutCheck()
    
    # Check interval with a timeout of 5 seconds
    if timeout_check.interval_with_timeout(timeout=5):
        print("Current time is within the interval.")
    else:
        print("Current time is outside the interval or timeout occurred.")
