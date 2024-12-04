"""User authentication routes"""

import json
from sqlalchemy.orm import Session
import faker

from app.purchases.transaction_model import Transaction


fake = faker.Faker()

def create_fake_data(db: Session, user_id: int):
    new_purchases = []
    for _ in range(100):
        new_purchase = Transaction(
            items=", ".join([fake.word() for _ in range(fake.random_int(min=1, max=5))]),
            price=fake.random_digit(),
            currency="TWD",
            location=fake.address(),
            purchase_time=fake.date_time_this_year(),
            transaction_type="purchase",
            payment_method="card",
            note=fake.sentence(),
            user_id=user_id
        )

        new_purchases.append(new_purchase)

    db.add_all(new_purchases)
    db.commit()


