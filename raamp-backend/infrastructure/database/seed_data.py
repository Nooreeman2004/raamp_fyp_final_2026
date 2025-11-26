# Seed data for Business Domains
from infrastructure.database.models.business_domain_model import BusinessDomainModel


BUSINESS_DOMAINS = [
    {
        "business": "Restaurants",
        "description": "Food and beverage establishments, cafes, fine dining, fast food chains"
    },
    {
        "business": "Fashion",
        "description": "Clothing brands, apparel, accessories, footwear, fashion retail"
    },
    {
        "business": "E-commerce",
        "description": "Online retail, marketplaces, direct-to-consumer brands, dropshipping"
    },
    {
        "business": "Tech Startup",
        "description": "SaaS products, mobile apps, software development, tech services"
    },
    {
        "business": "Healthcare",
        "description": "Medical services, wellness, fitness, health products, telehealth"
    },
    {
        "business": "Education",
        "description": "Online courses, e-learning platforms, tutoring, educational content"
    }
]


async def seed_business_domains():
    """Seed the database with initial business domain categories"""
    existing_count = await BusinessDomainModel.count()
    
    if existing_count == 0:
        print("🌱 Seeding business domains...")
        for domain_data in BUSINESS_DOMAINS:
            domain = BusinessDomainModel(**domain_data)
            await domain.insert()
        print(f"✅ Seeded {len(BUSINESS_DOMAINS)} business domains")
    else:
        print(f"✓ Business domains already seeded ({existing_count} categories)")
