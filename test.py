import unittest
from bus import *

class TestBus(unittest.TestCase):
    def test_direct_supplied_by(self):
        self.assertTrue(direct_supplied_by("Electronic Circuit", frozenset({"Iron Plate", "Copper Wire"})))
        self.assertFalse(direct_supplied_by("Electronic Circuit", frozenset({"Iron Plate"})))
        self.assertTrue(direct_supplied_by("Electronic Circuit", frozenset({"Iron Plate", "Copper Wire", "Iron Gear Wheel"})))

    def test_r_supplied_by(self):
        self.assertTrue(r_supplied_by("Electronic Circuit", frozenset({"Iron Ore", "Copper Plate"})))
        self.assertFalse(r_supplied_by("Electronic Circuit", frozenset({"Iron Ore"})))
        self.assertTrue(r_supplied_by("Electronic Circuit", frozenset({"Iron Ore", "Copper Wire", "Iron Gear Wheel"})))
        
    def test_list_supplied_by(self):
        self.assertTrue(list_supplied_by(["Electronic Circuit","Steel Plate"], frozenset({"Iron Ore", "Copper Plate"})))
        self.assertFalse(list_supplied_by(["Electronic Circuit","Steel Plate"], frozenset({"Iron Ore"})))
        self.assertTrue(list_supplied_by(["Electronic Circuit","Steel Plate"], frozenset({"Iron Ore", "Copper Wire", "Iron Gear Wheel"})))
        
    def test_valid(self):
        Bi = set(find_roots(D))
        G0 = frozenset(["Science Pack 1", "Science Pack 2", "Science Pack 3", "Production Science Pack", "Military Science Pack", "High Tech Science Pack"])
        self.assertTrue(valid(G0, frozenset(Bi)))
        self.assertFalse(valid(G0, frozenset(Bi.difference({"Iron Ore"}))))
        self.assertTrue(valid(G0, frozenset(Bi.union({"Uranium Ore"}))))
        self.assertFalse(valid(G0, frozenset([])))
        
    def test_test_b(self):
        G0 = frozenset(["Science Pack 1", "Science Pack 2", "Science Pack 3", "Production Science Pack", "Military Science Pack", "High Tech Science Pack"])
        self.assertTrue(test_b(G0, frozenset(["Science Pack 1", "Science Pack 2", "Science Pack 3", "Production Science Pack", "Military Science Pack", "High Tech Science Pack"])))
        self.assertTrue(test_b(G0, frozenset(["Science Pack 1", "Science Pack 2", "Science Pack 3", "Production Science Pack", "Military Science Pack", "High Tech Science Pack", "Electronic Circuit"])))
        self.assertFalse(test_b(G0, frozenset(["Science Pack 1", "Science Pack 2", "Science Pack 3", "Production Science Pack", "Military Science Pack"])))

    def test_possible_to_create(self):
        Bi = frozenset(["Grenade", "Piercing Rounds Magazine", "Gun Turret"])
        for b in Bi:
            assert b in D.nodes(), "Test Setup Error: {} not in D".format(b)
        out = possible_to_create(Bi)
        self.assertEqual(out, frozenset(["Military Science Pack"]))

        Bi = frozenset(["Advanced Circuit", "Electric Mining Drill", "Lubricant", "Electronic Circuit", "Engine Unit"])
        for b in Bi:
            assert b in D.nodes(), "Test Setup Error: {} not in D".format(b)
        out = possible_to_create(Bi)
        self.assertEqual(out, frozenset(["Science Pack 3", "Speed Module", "Electric Engine Unit"]))

        Bi = frozenset(["Battery", "Sulfuric Acid", "Advanced Circuit", "Electric Mining Drill", "Lubricant", "Electronic Circuit", "Engine Unit"])
        for b in Bi:
            assert b in D.nodes(), "Test Setup Error: {} not in D".format(b)
        out = possible_to_create(Bi)
        self.assertEqual(out, frozenset(["Processing Unit", "Science Pack 3", "Speed Module", "Electric Engine Unit"]))

    def test_creation_hypotheses(self):
        Bi = ["Grenade", "Piercing Rounds Magazine", "Gun Turret"]
        for b in Bi:
            assert b in D.nodes(), "Test Setup Error: {} not in D".format(b)
        out = creation_hypotheses(frozenset(Bi))
        h1 = frozenset(Bi+["Military Science Pack"])
        self.assertEqual(out, {h1})

        Bi = ["Advanced Circuit", "Electric Mining Drill", "Lubricant", "Electronic Circuit", "Engine Unit"]
        for b in Bi:
            assert b in D.nodes(), "Test Setup Error: {} not in D".format(b)
        out = creation_hypotheses(frozenset(Bi))
        h1 = frozenset(Bi+["Science Pack 3"])
        h2 = frozenset(Bi+["Electric Engine Unit"])
        h3 = frozenset(Bi+["Speed Module"])
        self.assertEqual(out, {h1, h2, h3})
        
    def test_removal_hypothesis(self):
        Bi = ["Grenade", "Gun Turret"]
        for b in Bi:
            assert b in D.nodes(), "Test Setup Error: {} not in D".format(b)
        out = removal_hypotheses(frozenset(Bi))
        self.assertEqual(out, {frozenset(["Grenade"]), frozenset(["Gun Turret"])})
        
        Bi = ["Gun Turret"]
        for b in Bi:
            assert b in D.nodes(), "Test Setup Error: {} not in D".format(b)
        out = removal_hypotheses(frozenset(Bi))
        self.assertEqual(out, set())
        
        Bi = []
        for b in Bi:
            assert b in D.nodes(), "Test Setup Error: {} not in D".format(b)
        self.assertEqual(out, set())
        
    def test_trim_path(self):
        # If this fails normal operation has failed
        test_path = [["Iron Plate", "Water", "Petrolium Gas"],
                     ["Iron Plate", "Water", "Petrolium Gas","Sulfur"],
                     ["Iron Plate", "Water", "Petrolium Gas","Sulfur","Sulfuric Acid"]]
        test_path = [frozenset(p) for p in test_path]
        
        goal_path = [["Iron Plate", "Water", "Petrolium Gas"],
                     ["Iron Plate", "Water", "Sulfur"],
                     ["Sulfuric Acid"]]
        goal_path = [frozenset(p) for p in goal_path]
        G0 = frozenset(goal_path[-1])
        
        out = trim_path(test_path, G0)
        self.assertListEqual(out, goal_path, "Abnormal Operation")
        
        # If this fails, it has failed to detect the input does not actually reach goal
        test_path = [["Copper Wire", "Water", "Petrolium Gas","Copper Plate"],
                     ["Copper Wire", "Water", "Petrolium Gas","Sulfur"],
                     ["Copper Wire", "Water", "Petrolium Gas","Sulfur","Sulfuric Acid"]]
        test_path = [frozenset(p) for p in test_path]
        
        with self.assertRaises(AssertionError):
            trim_path(test_path, G0)
        
        # If this fails it can not seem to remove totally unnecessary items
        test_path = [["Iron Plate", "Water", "Petrolium Gas","Copper Plate"],
                     ["Iron Plate", "Water", "Petrolium Gas","Copper Plate","Sulfur"],
                     ["Iron Plate", "Water", "Petrolium Gas","Copper Plate","Sulfur","Sulfuric Acid"]]
        test_path = [frozenset(p) for p in test_path]
        
        out = trim_path(test_path, ["Sulfuric Acid"])
        self.assertListEqual(out, goal_path, "Failed to remove original unneccesary item Copper Plate")
                     
if __name__ == '__main__':
    unittest.main()