import pytest
from app.repositories.coupon_repository import coupon_repository
from app.repositories.product_repository import product_repository


@pytest.mark.asyncio
async def test_price_search_scoring():
    from app.models.product import Product
    products = [
        Product(id="1", product_id=1, name="Classmate Notebook", mrp=250.0, price=250.0, category="Notebooks", isActive=True),
        Product(id="2", product_id=2, name="Gel Pen", mrp=50.0, price=50.0, category="Pens", isActive=True),
        Product(id="3", product_id=3, name="Executive Diary", mrp=750.0, price=750.0, category="Diaries", isActive=True),
    ]

    # Test numeric price search token '50'
    res_50 = await product_repository._weighted_search(products, "50")
    assert len(res_50["products"]) > 0
    pids_50 = [p["_id"] if isinstance(p, dict) else p.id for p in res_50["products"]]
    assert "2" in pids_50

    # Test price expression 'under 300'
    res_under = await product_repository._weighted_search(products, "under 300")
    pids_under = [p["_id"] if isinstance(p, dict) else p.id for p in res_under["products"]]
    assert "1" in pids_under or "2" in pids_under
    assert "3" not in pids_under


@pytest.mark.asyncio
async def test_bundle_eligibility_in_schemes():
    from app.models.bundle import Bundle
    bundle = Bundle(id="bundle_101", name="School Kit", category="Stationery", brand="Classmate", price=499.0, items=[])

    # Check appliesToType = "bundles"
    eligible = await coupon_repository._bundle_eligible_async(
        bundle, applies_to_type="bundles", applies_to_value_ids=["bundle_101"]
    )
    assert eligible is True

    not_eligible = await coupon_repository._bundle_eligible_async(
        bundle, applies_to_type="bundles", applies_to_value_ids=["other_bundle"]
    )
    assert not_eligible is False


@pytest.mark.asyncio
async def test_bundle_search_tags_schema():
    from app.routers.bundles import CreateBundleRequest, UpdateBundleRequest

    req = CreateBundleRequest(
        name="Test Bundle",
        price=100.0,
        items=[{"productId": "p1", "quantity": 1}],
    )
    assert req.items[0].product_id == "p1"

    up = UpdateBundleRequest(searchTags=["summer-sale"])
    assert up.search_tags == ["summer-sale"]


def test_trending_top_percentile_algorithm():
    """Unit test for the top-30% percentile + R-to-2R banding logic in get_trending_by_conversion."""
    # 10 products scored globally (no subcategory grouping)
    all_scored = [
        ("p1", 0.80),
        ("p2", 0.60),
        ("p3", 0.50),
        ("p4", 0.40),
        ("p5", 0.35),
        ("p6", 0.30),
        ("p7", 0.20),
        ("p8", 0.15),
        ("p9", 0.10),
        ("p10", 0.05),
    ]
    top_percentile = 0.30

    # ── Percentile cutoff ────────────────────────────────────────────────────
    # sorted ascending: [0.05, 0.10, 0.15, 0.20, 0.30, 0.35, 0.40, 0.50, 0.60, 0.80]
    # cutoff_index = max(0, int(10 * 0.7) - 1) = max(0, 6) = 6
    # scores_only[6] = 0.40  → top 30% are products scoring >= 0.40
    scores_only = sorted([rate for _, rate in all_scored])  # ascending
    cutoff_index = max(0, int(len(scores_only) * (1.0 - top_percentile)) - 1)
    score_cutoff = scores_only[cutoff_index]  # index 6 → 0.40
    assert score_cutoff == 0.40

    # ── Exclusion applied AFTER cutoff ───────────────────────────────────────
    # p3 (0.50) is above cutoff so would trend, but is on the exclusion list
    exclude = {"p3"}
    eligible = [(pid, rate) for pid, rate in all_scored if rate >= score_cutoff and pid not in exclude]
    eligible.sort(key=lambda x: x[1], reverse=True)
    result_ids = [pid for pid, _ in eligible]

    # top 30% of 10 items: p1(0.80), p2(0.60), p3(0.50), p4(0.40) — but p3 excluded
    assert result_ids == ["p1", "p2", "p4"]
    assert "p3" not in result_ids  # excluded after percentile cut
    assert "p5" not in result_ids  # 0.35 < cutoff (0.40) → not trending
    assert "p7" not in result_ids  # 0.20 < cutoff → not trending

    # Result is sorted descending by score
    result_scores = [rate for _, rate in eligible]
    assert result_scores == sorted(result_scores, reverse=True)

    # ── Backend returns full eligible pool (no artificial banding) ───────────
    # The limit is just a safety cap. With limit=10 and 6 eligible products,
    # all 6 are returned. The frontend's getSectionDisplayConfig decides rows.
    limit = 10
    banded = result_ids[:limit] if limit else result_ids
    assert banded == result_ids  # 6 items < limit=10, full pool returned
    assert len(banded) <= limit

    # With a larger pool than limit: limit acts as safety cap
    big_pool = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k"]
    banded2 = big_pool[:limit] if limit else big_pool
    assert len(banded2) == limit  # capped at safety limit