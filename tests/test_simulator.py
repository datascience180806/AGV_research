import os
import json
import unittest
from utils import get_distance, iterate_position
from config import get_config

class TestSimulator(unittest.TestCase):
    def test_distance_calculation(self):
        # Test distance formula
        dist = get_distance(0, 0, 3, 4)
        self.assertEqual(dist, 5.0)

    def test_iterate_position(self):
        # Test incremental movement step towards a target
        # Moving from (0, 0) to (10, 0) with step size (speed) = 2.0
        new_x, new_y, theta = iterate_position(0.0, 0.0, 10.0, 0.0, 2.0)
        self.assertEqual(new_x, 2.0)
        self.assertEqual(new_y, 0.0)
        self.assertEqual(theta, 0.0)

    def test_load_layout_files(self):
        # Verify that layouts exist and are valid JSON
        layouts_dir = "factory_layouts"
        self.assertTrue(os.path.exists(layouts_dir))
        layout_files = [f for f in os.listdir(layouts_dir) if f.endswith(".json")]
        self.assertGreater(len(layout_files), 0)
        
        for file_name in layout_files:
            with open(os.path.join(layouts_dir, file_name), "r", encoding="utf-8") as f:
                data = json.load(f)
                self.assertIn("layout_id", data)
                self.assertIn("nodes", data)
                self.assertIn("edges", data)

    def test_load_scenario_files(self):
        # Verify that scenarios exist and are valid JSON
        scenarios_dir = "scenarios"
        self.assertTrue(os.path.exists(scenarios_dir))
        
        found_scenarios = 0
        for root, dirs, files in os.walk(scenarios_dir):
            for file in files:
                if file.endswith(".json"):
                    found_scenarios += 1
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self.assertIn("scenario_id", data)
                        self.assertIn("factory_layout", data)
                        self.assertIn("agvs", data)
        self.assertGreater(found_scenarios, 0)

if __name__ == "__main__":
    unittest.main()
