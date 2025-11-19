"""Seed instruments database with coverage list."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.models.instrument import Instrument


def seed_instruments():
    """Seed instruments with initial coverage list."""
    db = SessionLocal()

    instruments = [
        # Quantum computing
        {
            'id': 'IONQ:NASDAQ',
            'symbol': 'IONQ',
            'venue': 'NASDAQ',
            'asset_class': 'equity',
            'display_name_en': 'IonQ Inc',
            'display_name_cn': '艾恩Q',
            'meta': {
                'sector': 'Technology',
                'industry': 'Quantum Computing',
                'themes': ['quantum', 'quantum_computing'],
                'catalysts': ['subsidy', 'government_funding'],
                'geo': 'US',
                'stage': 'development'
            }
        },
        {
            'id': 'RGTI:NASDAQ',
            'symbol': 'RGTI',
            'venue': 'NASDAQ',
            'asset_class': 'equity',
            'display_name_en': 'Rigetti Computing',
            'display_name_cn': '里盖蒂计算',
            'meta': {
                'sector': 'Technology',
                'industry': 'Quantum Computing',
                'themes': ['quantum', 'quantum_computing'],
                'catalysts': ['subsidy', 'partnerships'],
                'geo': 'US',
                'stage': 'development'
            }
        },

        # Rare earths
        {
            'id': 'MP:NYSE',
            'symbol': 'MP',
            'venue': 'NYSE',
            'asset_class': 'equity',
            'display_name_en': 'MP Materials Corp',
            'display_name_cn': 'MP材料',
            'meta': {
                'sector': 'Materials',
                'industry': 'Rare Earths Mining',
                'themes': ['rare_earths', 'critical_minerals'],
                'catalysts': ['export_controls', 'supply_chain'],
                'geo': 'US',
                'stage': 'producer',
                'supply_chain_role': 'upstream_miner'
            }
        },
        {
            'id': 'LYC:ASX',
            'symbol': 'LYC',
            'venue': 'ASX',
            'asset_class': 'equity',
            'display_name_en': 'Lynas Rare Earths',
            'display_name_cn': '莱纳斯稀土',
            'meta': {
                'sector': 'Materials',
                'industry': 'Rare Earths Mining',
                'themes': ['rare_earths', 'critical_minerals'],
                'catalysts': ['export_controls', 'supply_chain'],
                'geo': 'AU',
                'stage': 'producer',
                'supply_chain_role': 'upstream_miner'
            }
        },

        # Graphite
        {
            'id': 'SYR:ASX',
            'symbol': 'SYR',
            'venue': 'ASX',
            'asset_class': 'equity',
            'display_name_en': 'Syrah Resources',
            'display_name_cn': '希拉资源',
            'meta': {
                'sector': 'Materials',
                'industry': 'Graphite Mining',
                'themes': ['graphite', 'battery_materials'],
                'catalysts': ['EV_demand', 'supply_chain'],
                'geo': 'AU',
                'stage': 'producer',
                'supply_chain_role': 'upstream_miner'
            }
        },
        {
            'id': 'NGC:TSX',
            'symbol': 'NGC',
            'venue': 'TSX',
            'asset_class': 'equity',
            'display_name_en': 'Northern Graphite',
            'display_name_cn': '北方石墨',
            'meta': {
                'sector': 'Materials',
                'industry': 'Graphite Mining',
                'themes': ['graphite', 'battery_materials'],
                'catalysts': ['EV_demand', 'permitting'],
                'geo': 'CA',
                'stage': 'development',
                'supply_chain_role': 'upstream_miner'
            }
        },

        # ETFs
        {
            'id': 'GLD:NYSE',
            'symbol': 'GLD',
            'venue': 'NYSE',
            'asset_class': 'etf',
            'display_name_en': 'SPDR Gold Shares',
            'display_name_cn': '黄金ETF',
            'meta': {
                'sector': 'Commodities',
                'industry': 'Gold',
                'themes': ['gold', 'precious_metals'],
                'catalysts': ['inflation', 'rates'],
                'geo': 'Global'
            }
        },
    ]

    count = 0

    for inst_data in instruments:
        # Check if exists
        existing = db.query(Instrument).filter(Instrument.id == inst_data['id']).first()

        if not existing:
            instrument = Instrument(**inst_data)
            db.add(instrument)
            count += 1

    db.commit()
    db.close()

    print(f"✓ Seeded {count} instruments")


if __name__ == "__main__":
    seed_instruments()
