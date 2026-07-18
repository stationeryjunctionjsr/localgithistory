import random
import string


def generate_referral_code(length: int = 6) -> str:
    """Generate a random alphanumeric referral code with capital letters and numbers."""
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))


async def get_unique_referral_code(user_repository) -> str:
    """Generate a unique referral code by checking against existing users."""
    while True:
        code = generate_referral_code()
        existing = await user_repository.findOne({"referralCode": code})
        if not existing:
            return code
