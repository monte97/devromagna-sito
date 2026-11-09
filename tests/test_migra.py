import json
import re
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import migra


SLUG_RE = re.compile(r"^[a-z0-9-]{1,60}$")


class SlugifyTest(unittest.TestCase):
    def test_apostrofo_e_due_punti(self):
        self.assertEqual(
            migra.slugify("TypeScript: introduzione e casi d'uso"),
            "typescript-introduzione-e-casi-duso",
        )

    def test_limite_e_regex(self):
        slug = migra.slugify(
            "Kafka Unleashed: Introduzione, Confronti e Integrazione con .NET Core"
        )
        self.assertLessEqual(len(slug), 60)
        self.assertRegex(slug, SLUG_RE)

    def test_accenti_rimossi(self):
        self.assertEqual(migra.slugify("Perché è così"), "perche-e-cosi")

    def test_spazi_multipli_e_simboli(self):
        slug = migra.slugify("  Ciao -- mondo!!!  ")
        self.assertEqual(slug, "ciao-mondo")
        self.assertRegex(slug, SLUG_RE)


class ParseFolderDateTest(unittest.TestCase):
    def test_aaaammgg(self):
        self.assertEqual(
            migra.parse_folder_date("20190117-Data-Visualization-con-D3"),
            date(2019, 1, 17),
        )

    def test_ggmmaaaa(self):
        self.assertEqual(
            migra.parse_folder_date("26032020-Neo4jGDBMS"), date(2020, 3, 26)
        )

    def test_non_data(self):
        self.assertIsNone(
            migra.parse_folder_date("TypeScript- JavaScript-on-steroids.pdf")
        )

    def test_nome_non_valido(self):
        self.assertIsNone(migra.parse_folder_date("AUTHORS.md"))

    def test_fuori_intervallo(self):
        self.assertIsNone(migra.parse_folder_date("20100101-Troppo-vecchio"))


class CartelleRealiTest(unittest.TestCase):
    CASES = [
        ("20170330-JestFramework", date(2017, 3, 30), "JestFramework"),
        ("20170420-GitBranchingModels", date(2017, 4, 20), "GitBranchingModels"),
        ("20171116-GolangIntro", date(2017, 11, 16), "GolangIntro"),
        (
            "20180118-Frameworkless-Frontend-Development",
            date(2018, 1, 18),
            "Frameworkless-Frontend-Development",
        ),
        ("20180215-Chatbots-cosa-sono", date(2018, 2, 15), "Chatbots-cosa-sono"),
        (
            "20180221-ElasticSearch4Dummies",
            date(2018, 2, 21),
            "ElasticSearch4Dummies",
        ),
        (
            "20180418-Machine-Learning-per-comuni-mortali",
            date(2018, 4, 18),
            "Machine-Learning-per-comuni-mortali",
        ),
        ("20180525-Inotroduzione-a-docker", date(2018, 5, 25), "Inotroduzione-a-docker"),
        (
            "20190117-Data-Visualization-con-D3",
            date(2019, 1, 17),
            "Data-Visualization-con-D3",
        ),
        ("20190320-cqrs-event-sourcing-ddd", date(2019, 3, 20), "cqrs-event-sourcing-ddd"),
        ("20190516-TypeScript-introduzione-e-casi-d'uso", date(2019, 5, 16), "TypeScript-introduzione-e-casi-d'uso"),
        ("20200610-php-next-generation", date(2020, 6, 10), "php-next-generation"),
        ("20201217-Smart-Working", date(2020, 12, 17), "Smart-Working"),
        ("20230322-WebPerformance", date(2023, 3, 22), "WebPerformance"),
        ("26032020-Neo4jGDBMS", date(2020, 3, 26), "Neo4jGDBMS"),
    ]

    def test_date(self):
        for name, expected, _ in self.CASES:
            with self.subTest(name=name):
                self.assertEqual(migra.parse_folder_date(name), expected)

    def test_slug_del_titolo(self):
        for name, _, title in self.CASES:
            with self.subTest(name=name):
                slug = migra.slugify(title)
                self.assertRegex(slug, SLUG_RE)
                self.assertNotEqual(slug[0], "-")
                self.assertNotEqual(slug[-1], "-")
                self.assertNotIn("--", slug)


class MainTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.out = self.root / "out"
        self.out.mkdir()
        self.repo = self.root / "eventi"
        self.repo.mkdir()
        self.live = self.root / "index.html"
        self.meetup = self.root / "meetup.json"
        self.live.write_text("", encoding="utf-8")
        self.meetup.write_text("[]", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def write_live(self, entries):
        voci = "\n".join(
            '<li><a href="https://www.meetup.com//it-IT/devromagna/events/%s/">%s</a></li>'
            % (event_id, titolo)
            for event_id, titolo in entries
        )
        self.live.write_text(
            "<h2 id=\"incontri-passati\">Incontri passati</h2><ul>%s</ul>"
            "<h2 id=\"link-veloci\">Link veloci</h2><ul>"
            '<li><a href="https://meetup.com/DevRomagna">community</a></li></ul>'
            % voci,
            encoding="utf-8",
        )

    def write_meetup(self, eventi):
        self.meetup.write_text(json.dumps(eventi), encoding="utf-8")

    def evento(
        self,
        event_id="111",
        titolo="Talk Uno",
        data="2019-01-01T20:00:00+01:00",
        description="http://photos1.meetupstatic.com/photos/x.jpeg\n\nAbstract bello.",
    ):
        return {
            "id": event_id,
            "title": titolo,
            "dateTime": data,
            "description": description,
            "venue": "Studio",
            "city": "Imola",
            "isOnline": None,
            "going": None,
            "url": "https://www.meetup.com/devromagna/events/%s/" % event_id,
        }

    def bundle(self, nome):
        return self.out / "content" / "eventi" / nome / "index.md"

    def test_unisce_live_meetup_e_cartella(self):
        self.write_live([("111", "Talk Uno")])
        self.write_meetup([self.evento()])
        cartella = self.repo / "20190101-Talk"
        cartella.mkdir()
        (cartella / "README.md").write_text("# Talk Uno\n\nCorpo del readme.\n", encoding="utf-8")

        migra.main(self.live, self.repo, self.meetup, self.out)

        page = self.bundle("2019-01-01-talk-uno").read_text(encoding="utf-8")
        self.assertIn('title: "Talk Uno"', page)
        self.assertIn("date: 2019-01-01T20:00:00+01:00", page)
        self.assertIn('city: "Imola"', page)
        self.assertIn('host: "Studio"', page)
        self.assertIn('meetup_url: "https://www.meetup.com/devromagna/events/111/"', page)
        self.assertIn("Abstract bello.", page)
        self.assertIn("Corpo del readme.", page)
        self.assertNotIn("photos1.meetupstatic", page)

    def test_speaker_dalla_descrizione(self):
        self.write_meetup(
            [
                self.evento(
                    description="Testo introduttivo.\n\nSpeaker:\n\n- Mario Rossi. Bio lunga.\n"
                    "- Anna Bianchi e Luca Verdi.\n\nPS: ciao"
                )
            ]
        )
        migra.main(self.live, self.repo, self.meetup, self.out)

        page = self.bundle("2019-01-01-talk-uno").read_text(encoding="utf-8")
        self.assertIn('name: "Mario Rossi"', page)
        self.assertIn('name: "Anna Bianchi"', page)
        self.assertIn('name: "Luca Verdi"', page)
        self.assertNotIn("Bio lunga", page)

    def test_speaker_separati_da_riga_vuota(self):
        self.write_meetup(
            [
                self.evento(
                    description="Testo.\n\nSpeaker:\n\n- Mario Rossi. Bio.\n\n"
                    "- Anna Bianchi. Bio.\n\nPS: fine"
                )
            ]
        )
        migra.main(self.live, self.repo, self.meetup, self.out)
        page = self.bundle("2019-01-01-talk-uno").read_text(encoding="utf-8")
        self.assertIn('name: "Mario Rossi"', page)
        self.assertIn('name: "Anna Bianchi"', page)

    def test_cartella_senza_meetup(self):
        cartella = self.repo / "20200610-php-next-generation"
        cartella.mkdir()
        (cartella / "readme.md").write_text(
            "PHP Next Generation\n===\n\n## Abstract\nTesto del readme.\n",
            encoding="utf-8",
        )

        migra.main(self.live, self.repo, self.meetup, self.out)

        page = self.bundle("2020-06-10-php-next-generation").read_text(encoding="utf-8")
        self.assertIn('title: "PHP Next Generation"', page)
        self.assertIn("date: 2020-06-10", page)
        self.assertIn("Testo del readme.", page)
        report = (self.out / "MIGRAZIONE-DA-VERIFICARE.md").read_text(encoding="utf-8")
        self.assertIn("php-next-generation", report)

    def test_pdf_copiato_e_link_riscritto(self):
        self.write_live([("111", "Talk Uno")])
        self.write_meetup([self.evento()])
        cartella = self.repo / "20190101-Talk"
        cartella.mkdir()
        (cartella / "vecchio.pdf").write_bytes(b"%PDF-1.4")
        (cartella / "esempio.py").write_text("print('ciao')\n", encoding="utf-8")
        (cartella / "README.md").write_text(
            "# Talk Uno\n\n[slide](./vecchio.pdf)\n", encoding="utf-8"
        )

        migra.main(self.live, self.repo, self.meetup, self.out)

        base = self.out / "content" / "eventi" / "2019-01-01-talk-uno"
        self.assertTrue((base / "slide.pdf").is_file())
        page = (base / "index.md").read_text(encoding="utf-8")
        self.assertIn('slides: "slide.pdf"', page)
        self.assertIn("[slide](./slide.pdf)", page)
        self.assertIn(
            "https://github.com/DevRomagna/eventi/tree/master/20190101-Talk", page
        )

    def test_non_sovrascrive(self):
        self.write_live([("111", "Talk Uno")])
        self.write_meetup([self.evento()])
        cartella = self.out / "content" / "eventi" / "2019-01-01-talk-uno"
        cartella.mkdir(parents=True)
        esistente = cartella / "index.md"
        esistente.write_text("MARKER", encoding="utf-8")

        migra.main(self.live, self.repo, self.meetup, self.out)

        self.assertEqual(esistente.read_text(encoding="utf-8"), "MARKER")

    def test_eventi_futuri_esclusi(self):
        self.write_meetup(
            [self.evento(event_id="333", titolo="Futuro", data="2099-01-01T20:00:00+01:00")]
        )
        migra.main(self.live, self.repo, self.meetup, self.out)
        self.assertFalse(self.bundle("2099-01-01-futuro").exists())

    def test_abstract_senza_markdown(self):
        self.write_meetup(
            [
                self.evento(
                    description="**Guida pratica** delle interazioni lente."
                )
            ]
        )
        migra.main(self.live, self.repo, self.meetup, self.out)
        page = self.bundle("2019-01-01-talk-uno").read_text(encoding="utf-8")
        self.assertIn("Guida pratica delle interazioni lente.", page)
        self.assertNotIn("**", page)

    def test_report_contiene_nota_intervallo(self):
        migra.main(self.live, self.repo, self.meetup, self.out)
        report = (self.out / "MIGRAZIONE-DA-VERIFICARE.md").read_text(encoding="utf-8")
        self.assertIn(
            "Nessun evento trovato fra ottobre 2024 e settembre 2025", report
        )


if __name__ == "__main__":
    unittest.main()
