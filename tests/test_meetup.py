import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import nuovo_evento_da_meetup as meetup


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "meetup.ics"
TITOLO = "Argus SBOM Guard: gestione delle vulnerabilità a partire dagli SBOM"
CARTELLA = "2026-11-12-argus-sbom-guard-gestione-delle-vulnerabilita-a-partire"


class ParseIcsTest(unittest.TestCase):
    def setUp(self):
        self.eventi = meetup.parse_ics(FIXTURE.read_text(encoding="utf-8"))
        self.evento = next(
            evento for evento in self.eventi if evento["title"] == TITOLO
        )

    def test_titolo_riga_ripiegata(self):
        self.assertEqual(self.evento["title"], TITOLO)

    def test_data_aware_europa_roma(self):
        self.assertEqual(
            self.evento["date"],
            datetime(2026, 11, 12, 20, 0, tzinfo=ZoneInfo("Europe/Rome")),
        )

    def test_speaker_dalla_descrizione(self):
        self.assertEqual(self.evento["speaker"], "Matteo Vitali")

    def test_meetup_url(self):
        self.assertEqual(
            self.evento["meetup_url"],
            "https://www.meetup.com/devromagna/events/317143074/",
        )

    def test_escape_della_descrizione(self):
        self.assertIn("consolidata, ma", self.evento["abstract"])
        self.assertNotIn("\\,", self.evento["abstract"])
        self.assertNotIn("Speaker:", self.evento["abstract"])


class MainTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_due_esecuzioni_creano_un_solo_bundle(self):
        primo = meetup.main(str(FIXTURE), self.root)
        secondo = meetup.main(str(FIXTURE), self.root)

        self.assertEqual(len(primo), 1)
        self.assertEqual(secondo, [])
        bundle = self.root / CARTELLA / "index.md"
        self.assertTrue(bundle.is_file())
        testo = bundle.read_text(encoding="utf-8")
        self.assertIn('title: "' + TITOLO + '"', testo)
        self.assertIn("date: 2026-11-12T20:00:00+01:00", testo)
        self.assertIn('name: "Matteo Vitali"', testo)
        self.assertIn(
            'meetup_url: "https://www.meetup.com/devromagna/events/317143074/"',
            testo,
        )

    def test_bundle_esistente_non_viene_riscritto(self):
        cartella = self.root / CARTELLA
        cartella.mkdir(parents=True)
        indice = cartella / "index.md"
        indice.write_text("MARKER", encoding="utf-8")

        creati = meetup.main(str(FIXTURE), self.root)

        self.assertEqual(creati, [])
        self.assertEqual(indice.read_text(encoding="utf-8"), "MARKER")

    def test_content_reale_non_crea_nulla(self):
        content = Path(__file__).resolve().parents[1] / "content" / "eventi"
        creati = meetup.main(str(FIXTURE), content)
        self.assertEqual(creati, [])


if __name__ == "__main__":
    unittest.main()
