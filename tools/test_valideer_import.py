import unittest
from valideer_import import valideer

BASIS = {
    'artikelnummer': 'HS-RVS-M6-40', 'product': 'Houtschroef RVS platkop',
    'categorie': 'schroeven', 'naam': 'Houtschroef RVS platkop M6x40',
    'prijs_incl_btw': '12,95', 'btw': '21', 'materiaal': 'RVS',
    'verpakkingsaantal': '100',
}

class TestValideer(unittest.TestCase):
    def test_geldige_rij_geeft_geen_fouten(self):
        self.assertEqual(valideer([BASIS]), [])

    def test_dubbel_artikelnummer(self):
        fouten = valideer([BASIS, dict(BASIS)])
        self.assertTrue(any('dubbel' in f for f in fouten))

    def test_prijs_nul_is_fout(self):
        fouten = valideer([{**BASIS, 'prijs_incl_btw': '0'}])
        self.assertTrue(any('groter dan 0' in f for f in fouten))

    def test_prijs_geen_getal(self):
        fouten = valideer([{**BASIS, 'prijs_incl_btw': 'op aanvraag'}])
        self.assertTrue(any('geen getal' in f for f in fouten))

    def test_leeg_verplicht_veld(self):
        fouten = valideer([{**BASIS, 'naam': '  '}])
        self.assertTrue(any("'naam'" in f for f in fouten))

    def test_onbekende_categorie(self):
        fouten = valideer([{**BASIS, 'categorie': 'tuinmeubels'}])
        self.assertTrue(any('onbekende categorie' in f for f in fouten))

if __name__ == '__main__':
    unittest.main()
