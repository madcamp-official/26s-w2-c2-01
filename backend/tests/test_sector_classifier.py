from unittest import TestCase

from app.seed.seed_data import SECTORS
from app.services.sector_classifier import INDUSTRY_TO_SECTOR


class SectorClassifierTest(TestCase):
    def test_every_finnhub_mapping_points_to_a_seeded_sector(self) -> None:
        seeded_names = {name_ko for name_ko, _name_en in SECTORS}
        self.assertTrue(set(INDUSTRY_TO_SECTOR.values()).issubset(seeded_names))

    def test_representative_finnhub_industries(self) -> None:
        self.assertEqual("반도체·AI", INDUSTRY_TO_SECTOR["Semiconductors"])
        self.assertEqual("금융", INDUSTRY_TO_SECTOR["Banking"])
        self.assertEqual("헬스케어", INDUSTRY_TO_SECTOR["Biotechnology"])
        self.assertEqual("산업재", INDUSTRY_TO_SECTOR["Airlines"])
        self.assertEqual("산업재", INDUSTRY_TO_SECTOR["Electrical Equipment"])
        self.assertEqual("통신", INDUSTRY_TO_SECTOR["Communications"])
