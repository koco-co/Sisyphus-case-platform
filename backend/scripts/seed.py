"""Seed initial data: default admin user, checklist templates, test case templates."""

import asyncio


async def seed() -> None:
    print("Seeding database...")
    # TODO: Add seed data
    #   - Default admin user
    #   - Industry checklists (6 categories, 32 items)
    #   - Test case templates (7 types)
    #   - Sample product/iteration for demo
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
