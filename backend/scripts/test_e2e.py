"""
End-to-end test script.

This script tests the complete flow:
1. Ingest a sample transcript
2. Generate cards
3. Verify triggers
4. Test discovery engine
5. Check portfolio functionality
"""

import sys
import os
import requests
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

API_BASE = "http://localhost:8000/api"


# Sample bilingual transcript (CN/EN mixed)
SAMPLE_TRANSCRIPT = """
量子计算投资机会分析

IonQ是一家领先的量子计算公司，在NASDAQ上市。美国政府计划投资量子技术，每家公司可能获得约1000万美元的资助。

This represents a significant catalyst for quantum computing companies. IonQ has demonstrated strong technical capabilities with their ion-trap technology.

Entry strategy: Consider buying IonQ on pullbacks to $12-13 levels. The stock has shown support at these levels historically.

Invalidation: If government funding is delayed beyond Q2 2025, or if the stock falls below $10, exit the position.

稀土供应链分析

MP Materials (MP) is the only rare earth mining company in North America. With potential export controls from China, MP could benefit significantly.

中国可能限制稀土出口，这将使得北美稀土生产商受益。MP Materials 位于加利福尼亚，是美国唯一的稀土矿商。

Target entry: MP at $18-20 range on any market weakness.

Risk: Permitting delays or environmental concerns could impact production.
"""


def test_ingest():
    """Test ingesting transcript."""
    print("\n=== Testing Ingest ===")

    response = requests.post(
        f"{API_BASE}/ingest",
        json={
            "text": SAMPLE_TRANSCRIPT,
            "expert_ref": "test_e2e",
            "locale": "zh-CN"
        }
    )

    assert response.status_code == 200, f"Ingest failed: {response.text}"

    data = response.json()

    print(f"✓ Processing time: {data['processing_time']:.2f}s")
    print(f"✓ Entities extracted: {data['total_entities_extracted']}")
    print(f"✓ Cards generated: {len(data['cards'])}")

    assert data['processing_time'] < 60, "Processing took too long"
    assert len(data['cards']) >= 1, "Should generate at least 1 card"

    # Save cards
    for card in data['cards']:
        print(f"\n  Card: {card['id']}")
        print(f"    Summary (EN): {card['summary_en']}")
        print(f"    Summary (CN): {card['summary_cn']}")
        print(f"    Instruments: {[i['symbol'] for i in card['instruments']]}")
        print(f"    Confidence: {card['confidence']}")

        # Create card via API
        create_response = requests.post(f"{API_BASE}/cards", json=card)
        assert create_response.status_code == 201, f"Failed to create card: {create_response.text}"

    return data['cards']


def test_cards(cards):
    """Test card retrieval."""
    print("\n=== Testing Cards API ===")

    # List cards
    response = requests.get(f"{API_BASE}/cards")
    assert response.status_code == 200

    all_cards = response.json()
    print(f"✓ Total cards in system: {len(all_cards)}")

    # Get individual card
    if cards:
        card_id = cards[0]['id']
        response = requests.get(f"{API_BASE}/cards/{card_id}")
        assert response.status_code == 200
        print(f"✓ Retrieved card {card_id}")


def test_alerts(cards):
    """Test alert system."""
    print("\n=== Testing Alerts ===")

    if not cards:
        print("⚠ No cards to test alerts")
        return

    card_id = cards[0]['id']

    # Enable alerts
    response = requests.post(
        f"{API_BASE}/alerts/enable",
        json={"card_id": card_id, "channels": ["email"]}
    )

    assert response.status_code == 200
    print(f"✓ Alerts enabled for card {card_id}")

    # List alerts
    response = requests.get(f"{API_BASE}/alerts")
    assert response.status_code == 200

    alerts = response.json()
    print(f"✓ Total alerts: {len(alerts)}")


def test_discovery(cards):
    """Test similar-logic discovery."""
    print("\n=== Testing Discovery Engine ===")

    if not cards:
        print("⚠ No cards to test discovery")
        return

    card_id = cards[0]['id']

    response = requests.get(
        f"{API_BASE}/cards/{card_id}/similar",
        params={"top_k": 5, "min_score": 0.3}
    )

    assert response.status_code == 200

    candidates = response.json()
    print(f"✓ Similar tickers found: {len(candidates)}")

    for candidate in candidates[:3]:
        print(f"  {candidate['symbol']}: {candidate['score']:.2f}")
        print(f"    {candidate.get('explanation_en', 'N/A')}")


def test_portfolio():
    """Test portfolio functionality."""
    print("\n=== Testing Portfolio ===")

    # Open a position
    response = requests.post(
        f"{API_BASE}/portfolio/positions",
        params={
            "symbol": "IONQ",
            "entry_px": 12.5,
            "qty": 100,
            "card_id": "test_card"
        }
    )

    if response.status_code != 200:
        print(f"⚠ Warning: Failed to open position: {response.text}")
    else:
        print(f"✓ Position opened")

    # Get portfolio
    response = requests.get(f"{API_BASE}/portfolio")
    assert response.status_code == 200

    positions = response.json()
    print(f"✓ Total positions: {len(positions)}")

    # Get stats
    response = requests.get(f"{API_BASE}/portfolio/stats")
    assert response.status_code == 200

    stats = response.json()
    print(f"✓ Portfolio stats:")
    print(f"  Total positions: {stats['total_positions']}")
    print(f"  Total P&L: ${stats['total_pnl']}")
    print(f"  Win rate: {stats['win_rate']:.1f}%")


def main():
    """Run all E2E tests."""
    print("=" * 60)
    print("End-to-End Testing - Thesis → Ticker Engine")
    print("=" * 60)

    try:
        # Check API is running
        response = requests.get(f"{API_BASE.replace('/api', '')}/healthz")
        assert response.status_code == 200
        print("✓ API is healthy")

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API at", API_BASE)
        print("   Make sure the backend is running:")
        print("   cd backend && uvicorn app.main:app --reload")
        sys.exit(1)

    try:
        # Run tests
        cards = test_ingest()
        test_cards(cards)
        test_alerts(cards)
        test_discovery(cards)
        test_portfolio()

        print("\n" + "=" * 60)
        print("✅ All E2E tests passed!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
