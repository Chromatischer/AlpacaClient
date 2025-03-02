# Different priority levels for the logging system
from enum import Enum

from Core import Colors

class Priority(Enum):
    """
    Priority levels for the logging system
    """
    DEBUG = -1      # Use for debugging purposes and fine details
    LOW = 0         # Use for low priority messages or information that is not critical
    NORMAL = 1      # Use for normal priority messages which are non critical
    HIGH = 2        # Use for irregularities
    CRITICAL = 3    # Use for critical errors or failures

    def __str__(self):
        return self.name

def get_color(priority: Priority) -> str:
    if priority == Priority.DEBUG:
        return Colors.gray
    elif priority == Priority.LOW:
        return Colors.green
    elif priority == Priority.NORMAL:
        return Colors.yellow
    elif priority == Priority.HIGH:
        return Colors.cyan
    elif priority == Priority.CRITICAL:
        return Colors.bold + Colors.red
    else:
        return Colors.reset