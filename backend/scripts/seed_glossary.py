"""Seed glossary with financial terms."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.models.glossary import Glossary


def seed_glossary():
    """Seed glossary with CN/EN financial terms."""
    db = SessionLocal()

    glossary_terms = [
        # Margin
        {
            'key': 'margin',
            'cn': '保证金',
            'en': 'margin',
            'pinned': True,
            'aliases': ['保證金', '保证金率', 'margin requirement']
        },
        {
            'key': 'margin_increase',
            'cn': '保证金上调',
            'en': 'margin increase',
            'pinned': True,
            'aliases': []
        },
        {
            'key': 'margin_decrease',
            'cn': '保证金下调',
            'en': 'margin decrease',
            'pinned': True,
            'aliases': []
        },

        # Rating
        {
            'key': 'rating',
            'cn': '评级',
            'en': 'rating',
            'pinned': True,
            'aliases': ['信用评级', 'credit rating']
        },
        {
            'key': 'rating_downgrade',
            'cn': '评级下调',
            'en': 'rating downgrade',
            'pinned': True,
            'aliases': ['降级']
        },
        {
            'key': 'rating_upgrade',
            'cn': '评级上调',
            'en': 'rating upgrade',
            'pinned': True,
            'aliases': ['升级']
        },
        {
            'key': 'outlook',
            'cn': '展望',
            'en': 'outlook',
            'pinned': True,
            'aliases': []
        },
        {
            'key': 'negative_outlook',
            'cn': '负面展望',
            'en': 'negative outlook',
            'pinned': True,
            'aliases': []
        },

        # Policy
        {
            'key': 'subsidy',
            'cn': '补贴',
            'en': 'subsidy',
            'pinned': True,
            'aliases': ['政府补贴']
        },
        {
            'key': 'grant',
            'cn': '资助',
            'en': 'grant',
            'pinned': True,
            'aliases': ['拨款']
        },
        {
            'key': 'equity_stake',
            'cn': '入股',
            'en': 'equity stake',
            'pinned': True,
            'aliases': ['股权投资']
        },
        {
            'key': 'export_controls',
            'cn': '出口管制',
            'en': 'export controls',
            'pinned': True,
            'aliases': ['出口限制']
        },

        # Trading
        {
            'key': 'buy_the_dip',
            'cn': '逢低买入',
            'en': 'buy the dip',
            'pinned': True,
            'aliases': ['逢低']
        },
        {
            'key': 'pullback',
            'cn': '回调',
            'en': 'pullback',
            'pinned': True,
            'aliases': ['调整']
        },
        {
            'key': 'correction',
            'cn': '阶段性调整',
            'en': 'correction',
            'pinned': True,
            'aliases': ['修正']
        },

        # Commodities
        {
            'key': 'rare_earths',
            'cn': '稀土',
            'en': 'rare earths',
            'pinned': True,
            'aliases': ['稀土元素', 'REE']
        },
        {
            'key': 'graphite',
            'cn': '石墨',
            'en': 'graphite',
            'pinned': True,
            'aliases': ['天然石墨']
        },
        {
            'key': 'graphite_anode',
            'cn': '石墨负极',
            'en': 'graphite anode',
            'pinned': True,
            'aliases': ['负极材料']
        },

        # General
        {
            'key': 'price',
            'cn': '价格',
            'en': 'price',
            'pinned': True,
            'aliases': []
        },
        {
            'key': 'level',
            'cn': '水平',
            'en': 'level',
            'pinned': True,
            'aliases': []
        },
        {
            'key': 'trigger',
            'cn': '触发',
            'en': 'trigger',
            'pinned': True,
            'aliases': []
        },
        {
            'key': 'invalidate',
            'cn': '失效',
            'en': 'invalidate',
            'pinned': True,
            'aliases': []
        },
    ]

    count = 0

    for term in glossary_terms:
        # Check if exists
        existing = db.query(Glossary).filter(Glossary.key == term['key']).first()

        if not existing:
            glossary_entry = Glossary(**term)
            db.add(glossary_entry)
            count += 1

    db.commit()
    db.close()

    print(f"✓ Seeded {count} glossary terms")


if __name__ == "__main__":
    seed_glossary()
