import re
import sys
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


if __name__ == "__main__":
    unittest.main()
