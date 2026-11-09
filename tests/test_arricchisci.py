import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import arricchisci_da_meetup as arr


def pagina(event_id: str, descrizione: str) -> str:
    stato = {
        f"Event:{event_id}": {
            "description": descrizione,
            "venue": {"__ref": "Venue:1"},
            "featuredEventPhoto": {"__ref": "PhotoInfo:9"},
        },
        "Venue:1": {"address": "Via Roma, 1", "googleMapsUrl": "https://www.google.com/maps/search/?api=1&query=44,11"},
        "PhotoInfo:9": {"highResUrl": "https://example.invalid/highres_9.jpeg"},
    }
    dati = {"props": {"pageProps": {"__APOLLO_STATE__": stato}}}
    return f'<html><script id="__NEXT_DATA__" type="application/json">{json.dumps(dati)}</script></html>'


class ArricchisciTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.pagine = root / "pagine"
        self.pagine.mkdir()
        self.eventi = root / "eventi"
        self.eventi.mkdir()
        (self.pagine / "123.html").write_text(
            pagina("123", "http://photos1.meetupstatic.com/photos/event/a.jpeg\n\nPrimo paragrafo.\n\n\n\nSecondo paragrafo."),
            encoding="utf-8",
        )

    def tearDown(self):
        self._tmp.cleanup()

    def bundle(self, nome: str, corpo: str = "") -> Path:
        cartella = self.eventi / nome
        cartella.mkdir()
        (cartella / "index.md").write_text(
            '---\ntitle: "T"\ndate: 2020-01-01T20:00:00+01:00\nmeetup_url: "https://www.meetup.com/devromagna/events/123/"\n---\n' + corpo,
            encoding="utf-8",
        )
        return cartella / "index.md"

    def test_corpo_vuoto_riceve_la_descrizione_completa(self):
        indice = self.bundle("2020-01-01-a")
        arr.main(self.pagine, self.eventi)
        testo = indice.read_text(encoding="utf-8")
        self.assertIn("Primo paragrafo.\n\nSecondo paragrafo.", testo)
        self.assertNotIn("photos1.meetupstatic.com", testo)
        self.assertIn('address: "Via Roma, 1"', testo)
        self.assertIn("map_url:", testo)

    def test_corpo_esistente_non_viene_toccato(self):
        indice = self.bundle("2020-01-01-b", "\nScritto a mano.\n")
        arr.main(self.pagine, self.eventi)
        testo = indice.read_text(encoding="utf-8")
        self.assertIn("Scritto a mano.", testo)
        self.assertNotIn("Primo paragrafo", testo)
        self.assertIn('address: "Via Roma, 1"', testo)

    def test_idempotente(self):
        indice = self.bundle("2020-01-01-c")
        arr.main(self.pagine, self.eventi)
        prima = indice.read_text(encoding="utf-8")
        self.assertEqual(arr.main(self.pagine, self.eventi), {})
        self.assertEqual(indice.read_text(encoding="utf-8"), prima)


if __name__ == "__main__":
    unittest.main()
