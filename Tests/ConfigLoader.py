import os
import unittest

from Core.CFLoader import CFLoader


class MyTestCase(unittest.TestCase):
    config_loader = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.config_loader = CFLoader("config.json")
        cls.config_loader.set_config("test", "test")

    @classmethod
    def tearDownClass(cls) -> None:
        # delete the config file
        os.remove("config.json")

    def test_get_config(self):
        self.assertEqual(self.config_loader.get_config("test"), "test")

    def test_set_config(self):
        self.config_loader.set_config("test", "new_test")
        self.assertEqual(self.config_loader.get_config("test"), "new_test")


if __name__ == '__main__':
    unittest.main()
