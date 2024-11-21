import pytest

from models import Offer


pytestmark = pytest.mark.asyncio


@pytest.mark.db
async def test_filter_new_offers():
    offers = [
        Offer(offer_id=1),
        Offer(offer_id=2),
        Offer(offer_id=3),
    ]
    await Offer.add_all(offers)

    offer_ids = await Offer.filter_new_offers({2, 3, 4, 5})
    assert offer_ids == [4, 5]
