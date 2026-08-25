import pytest
from app.repositories.coupon_repository import coupon_repository
from app.repositories.customer_segments_repository import customer_segments_repository


@pytest.mark.asyncio
async def test_coupon_segments_overlap_and_multi_select():
    # 1. Create segment A
    segment_a_data = {"name": "Test Segment A", "type": "retail", "userIds": ["user_1", "user_3"]}
    segment_a = await customer_segments_repository.create(segment_a_data)
    segment_a_id = str(segment_a["_id"])

    # 2. Create segment B
    segment_b_data = {"name": "Test Segment B", "type": "retail", "userIds": ["user_2", "user_3"]}
    segment_b = await customer_segments_repository.create(segment_b_data)
    segment_b_id = str(segment_b["_id"])

    # 3. Create a comma-separated behavior string matching segment A and B
    behavior_str = f"segment_{segment_a_id},segment_{segment_b_id}"

    try:
        # Test evaluation of user_1 (only in segment A)
        res_1 = await coupon_repository._user_matches_behavior("user_1", behavior_str)
        assert res_1 is True

        # Test evaluation of user_2 (only in segment B)
        res_2 = await coupon_repository._user_matches_behavior("user_2", behavior_str)
        assert res_2 is True

        # Test evaluation of user_3 (overlapping, in both segment A and B)
        res_3 = await coupon_repository._user_matches_behavior("user_3", behavior_str)
        assert res_3 is True

        # Test evaluation of user_4 (in neither segment)
        res_4 = await coupon_repository._user_matches_behavior("user_4", behavior_str)
        assert res_4 is False

    finally:
        # Cleanup
        await customer_segments_repository.delete(segment_a_id)
        await customer_segments_repository.delete(segment_b_id)
