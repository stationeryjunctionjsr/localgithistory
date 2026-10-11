import ast
import inspect
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.db.mysql_order_dao import MySQLOrderDAO
from app.db.mysql_product_dao import MySQLProductDAO
from app.repositories.recommendation_repository import RecommendationRepository
from app.models.recommendation_config import FavouritesRankedResult


def test_zero_lambdas_and_zero_defaultdict_in_recommendation_repository():
    """Assert AST contains zero Lambda nodes and zero defaultdict references."""
    import app.repositories.recommendation_repository as rec_module
    source = inspect.getsource(rec_module)
    tree = ast.parse(source)

    for node in ast.walk(tree):
        assert not isinstance(node, ast.Lambda), f"Found lambda at line {getattr(node, 'lineno', '?')}"
        if isinstance(node, ast.Name):
            assert node.id != "defaultdict", f"Found defaultdict reference at line {node.lineno}"


@pytest.mark.asyncio
async def test_dao_get_user_purchased_subcategories_mocked():
    dao = MySQLOrderDAO()
    mock_session = AsyncMock()
    mock_row1 = MagicMock()
    mock_row1.subcat = "Stationery"
    mock_row1.total_qty = 5
    mock_row2 = MagicMock()
    mock_row2.subcat = "Office Supplies"
    mock_row2.total_qty = 12

    mock_result = MagicMock()
    mock_result.fetchall.return_value = [mock_row1, mock_row2]
    mock_session.execute.return_value = mock_result

    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session

    with patch.object(dao, "_factory", return_value=mock_factory):
        res = await dao.get_user_purchased_subcategories("123", datetime.now(timezone.utc))
        assert res == [("Stationery", 5), ("Office Supplies", 12)]
        mock_session.execute.assert_called_once()
        query_text = str(mock_session.execute.call_args[0][0])
        assert "GROUP BY subcat" in query_text
        assert "ORDER BY total_qty ASC" in query_text


@pytest.mark.asyncio
async def test_dao_get_bestsellers_in_subcategories_mocked():
    dao = MySQLOrderDAO()
    mock_session = AsyncMock()
    mock_row = MagicMock()
    mock_row.product_id = "101"
    mock_row.subcat = "Pens"
    mock_row.sales = 45

    mock_result = MagicMock()
    mock_result.fetchall.return_value = [mock_row]
    mock_session.execute.return_value = mock_result

    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session

    with patch.object(dao, "_factory", return_value=mock_factory):
        res = await dao.get_bestsellers_in_subcategories(["Pens", "Notebooks"], datetime.now(timezone.utc))
        assert res == [("101", "Pens", 45)]
        mock_session.execute.assert_called_once()
        query_text = str(mock_session.execute.call_args[0][0])
        assert ":sc_0" in query_text and ":sc_1" in query_text
        assert "GROUP BY product_id, subcat" in query_text
        assert "ORDER BY sales DESC" in query_text


@pytest.mark.asyncio
async def test_dao_get_favourites_by_subcategory_mocked():
    dao = MySQLOrderDAO()
    mock_session = AsyncMock()
    mock_row = MagicMock()
    mock_row.pid = "55"
    mock_row.subcat = "Art"
    mock_row.order_count = 10
    mock_row.total_qty = 25

    mock_result = MagicMock()
    mock_result.fetchall.return_value = [mock_row]
    mock_session.execute.return_value = mock_result

    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session

    with patch.object(dao, "_factory", return_value=mock_factory):
        res = await dao.get_favourites_by_subcategory("customer", datetime.now(timezone.utc), city="Mumbai")
        assert res == [("55", "Art", 10, 25)]
        mock_session.execute.assert_called_once()
        query_text = str(mock_session.execute.call_args[0][0])
        assert "HAVING total_qty > 1" in query_text
        assert "LOWER(TRIM(o.ship_city)) = :city" in query_text


@pytest.mark.asyncio
async def test_dao_get_favourites_ranked_data_mocked():
    dao = MySQLOrderDAO()
    mock_session = AsyncMock()

    mock_geo_res = MagicMock()
    geo_row = MagicMock()
    geo_row.state = "Maharashtra"
    geo_row.city = "Mumbai"
    mock_geo_res.fetchall.return_value = [geo_row]

    mock_stats_res = MagicMock()
    stats_row = MagicMock()
    stats_row.pid = "88"
    stats_row.order_count = 8
    stats_row.total_qty = 20
    mock_stats_res.fetchall.return_value = [stats_row]

    mock_session.execute.side_effect = [mock_geo_res, mock_stats_res]

    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session

    with patch.object(dao, "_factory", return_value=mock_factory):
        stats, states, cities = await dao.get_favourites_ranked_data("customer", datetime.now(timezone.utc))
        assert stats == [("88", 8, 20)]
        assert states == ["Maharashtra"]
        assert cities == ["Mumbai"]


@pytest.mark.asyncio
async def test_recommendation_repository_explore_pushdown():
    repo = RecommendationRepository()
    mock_order_dao = AsyncMock()
    mock_order_dao.get_user_purchased_subcategories.return_value = [
        ("SubcatA", 2),
        ("SubcatB", 5),
        ("SubcatC", 10),
    ]
    mock_order_dao.get_bestsellers_in_subcategories.return_value = [
        ("Prod1", "SubcatA", 100),
        ("Prod2", "SubcatA", 80),
        ("Prod3", "SubcatA", 50),
    ]
    repo.order_storage = mock_order_dao

    res = await repo.get_best_selling_from_least_bought_categories("user1", limit=2)
    assert res == ["Prod1", "Prod2"]
    mock_order_dao.get_user_purchased_subcategories.assert_called_once()
    mock_order_dao.get_bestsellers_in_subcategories.assert_called_once()


@pytest.mark.asyncio
async def test_recommendation_repository_favourites_ranked_pushdown():
    repo = RecommendationRepository()
    mock_order_dao = AsyncMock()
    mock_order_dao.get_favourites_ranked_data.return_value = (
        [("P1", 10, 50), ("P2", 5, 10)],
        ["State1"],
        ["City1"],
    )
    repo.order_storage = mock_order_dao

    result = await repo.get_favourites_ranked(kind="customer", days=30)
    assert isinstance(result, FavouritesRankedResult)
    assert len(result.ranked_ids) == 2
    assert result.states == ["State1"]
    assert result.cities == ["City1"]
    # P1 score > P2 score
    assert result.ranked_ids[0][0] == "P1"
    assert result.ranked_ids[1][0] == "P2"


@pytest.mark.asyncio
async def test_recommendation_repository_favourites_by_subcat_clean_ranking():
    repo = RecommendationRepository()
    mock_order_dao = AsyncMock()
    # SubcatA has P1 (score: 0.7*10 + 0.3*20 = 13.0) and P2 (score: 0.7*5 + 0.3*10 = 6.5) -> P1 wins SubcatA
    # SubcatB has P3 (score: 0.7*20 + 0.3*50 = 29.0) -> P3 wins SubcatB
    mock_order_dao.get_favourites_by_subcategory.return_value = [
        ("P1", "SubcatA", 10, 20),
        ("P2", "SubcatA", 5, 10),
        ("P3", "SubcatB", 20, 50),
    ]
    repo.order_storage = mock_order_dao

    res = await repo.get_customer_favourites_by_subcategory(days=60)
    # P3 score (29.0) > P1 score (13.0)
    assert res == ["P3", "P1"]
    mock_order_dao.get_favourites_by_subcategory.assert_called_once_with(
        kind="customer", start_date=mock_order_dao.get_favourites_by_subcategory.call_args[1]["start_date"], city=None
    )
