from octopus.modules.es.testindex import ESTestCase
from service import licences

class TestModels(ESTestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_01_variations(self):
        vars = licences.make_variations(["a", "b", "c"])
        assert "a b c" in vars
        assert "a b-c" in vars
        assert "a-b c" in vars
        assert "a-b-c" in vars
        assert len(vars) == 4

    def test_02_variant_map(self):
        vmap = licences.make_variation_map(["a", "b", "c"], "abc")
        vars = vmap.keys()
        assert "a b c" in vars
        assert "a b-c" in vars
        assert "a-b c" in vars
        assert "a-b-c" in vars
        assert "A B C" in vars
        assert "A B-C" in vars
        assert "A-B C" in vars
        assert "A-B-C" in vars

        assert len(vars) == 8

        vals = vmap.values()
        for v in vals:
            assert v == "abc"




