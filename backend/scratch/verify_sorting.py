import asyncio
from app.repositories.analytics_repository import analytics_repository

async def main():
    print("Testing get_sales_by_product...")
    products = await analytics_repository.get_sales_by_product(limit=10)
    print("Returned top products:")
    for idx, p in enumerate(products):
        print(f"{idx+1}. Product: {p.get('productName')} | Qty Sold: {p.get('quantity')} | Revenue: {p.get('revenue')}")
        
    quantities = [p.get('quantity') for p in products]
    is_descending = all(quantities[i] >= quantities[i+1] for i in range(len(quantities)-1))
    print(f"\nQuantities: {quantities}")
    print(f"Is strictly descending: {is_descending}")

if __name__ == '__main__':
    asyncio.run(main())
