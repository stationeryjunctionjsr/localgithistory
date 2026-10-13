import pytest
from unittest.mock import AsyncMock
from app.repositories.coupon_repository import coupon_repository
from app.repositories.customer_segments_repository import customer_segments_repository


@pytest.mark.asyncio
async def test_coupon_segments_overlap_and_multi_select():
    # Segment 1 has users 101 and 103
    # Segment 2 has users 102 and 103
    async def mock_has_user(seg_id: int, uid: int) -> bool:
        if seg_id == 1 and uid in (101, 103):
            return True
        if seg_id == 2 and uid in (102, 103):
            return True
        return False

    orig_has_user = customer_segments_repository.has_user
    customer_segments_repository.has_user = AsyncMock(side_effect=mock_has_user)

    behavior_str = "segment_1,segment_2"

    try:
        # Test evaluation of user 101 (only in segment 1)
        res_1 = await coupon_repository._user_matches_behavior(101, behavior_str)
        assert res_1 is True

        # Test evaluation of user 102 (only in segment 2)
        res_2 = await coupon_repository._user_matches_behavior(102, behavior_str)
        assert res_2 is True

        # Test evaluation of user 103 (overlapping, in both segment 1 and 2)
        res_3 = await coupon_repository._user_matches_behavior(103, behavior_str)
        assert res_3 is True

        # Test evaluation of user 104 (in neither segment)
        res_4 = await coupon_repository._user_matches_behavior(104, behavior_str)
        assert res_4 is False

    finally:
        customer_segments_repository.has_user = orig_has_user