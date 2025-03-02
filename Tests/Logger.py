import unittest

from Core.Logger import Logger, get_logger
from Core.Priority import Priority


class MyTestCase(unittest.TestCase):
    logger: Logger = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.logger = Logger()

    def test_logger(self):
        self.logger.log("Test message", priority=Priority.DEBUG)
        self.logger.log("Test message", priority=Priority.LOW)
        self.logger.log("Test message", priority=Priority.NORMAL)
        self.logger.log("Test message", priority=Priority.HIGH)
        self.logger.log("Test message", priority=Priority.CRITICAL)

    def test_logger_already_initialized(self):
        logger = Logger()

    def test_get_logger(self):
        logger = get_logger()
        logger.log("Test message", priority=Priority.DEBUG)
        logger.log("Test message", priority=Priority.LOW)
        logger.log("Test message", priority=Priority.NORMAL)
        logger.log("Test message", priority=Priority.HIGH)
        logger.log("Test message", priority=Priority.CRITICAL)



if __name__ == '__main__':
    unittest.main()
