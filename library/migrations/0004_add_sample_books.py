from datetime import date

from django.db import migrations


SAMPLE_BOOKS = [
    {
        "title": "Pride and Prejudice",
        "isbn": "9780141439518",
        "author": "Jane Austen",
        "category": "Fiction",
        "publisher": "Penguin Classics",
        "published_date": date(1813, 1, 28),
        "price": "399.00",
        "quantity": 3,
        "description": (
            "Elizabeth Bennet navigates family expectations, first impressions, "
            "and questions of love and social class in Regency England."
        ),
    },
    {
        "title": "Frankenstein",
        "isbn": "9780141439471",
        "author": "Mary Shelley",
        "category": "Fiction",
        "publisher": "Penguin Classics",
        "published_date": date(1818, 1, 1),
        "price": "349.00",
        "quantity": 3,
        "description": (
            "Victor Frankenstein creates a living being and must face the "
            "consequences of abandoning his creation."
        ),
    },
    {
        "title": "The Adventures of Sherlock Holmes",
        "isbn": "9780199536955",
        "author": "Arthur Conan Doyle",
        "category": "Mystery",
        "publisher": "Oxford World's Classics",
        "published_date": date(1892, 10, 14),
        "price": "299.00",
        "quantity": 3,
        "description": (
            "A collection of cases featuring Sherlock Holmes and Dr. Watson, "
            "including investigations solved through observation and deduction."
        ),
    },
    {
        "title": "Dracula",
        "isbn": "9780141439846",
        "author": "Bram Stoker",
        "category": "Mystery",
        "publisher": "Penguin Classics",
        "published_date": date(1897, 5, 26),
        "price": "379.00",
        "quantity": 3,
        "description": (
            "A group of people confronts Count Dracula as his influence "
            "spreads from Transylvania to England."
        ),
    },
    {
        "title": "Alice's Adventures in Wonderland",
        "isbn": "9780141439761",
        "author": "Lewis Carroll",
        "category": "Fiction",
        "publisher": "Penguin Classics",
        "published_date": date(1865, 11, 26),
        "price": "279.00",
        "quantity": 3,
        "description": (
            "Alice follows a white rabbit into a fantastical world of curious "
            "creatures, wordplay, and unexpected adventures."
        ),
    },
]


def add_sample_books(apps, schema_editor):
    Author = apps.get_model("library", "Author")
    Book = apps.get_model("library", "Book")
    Category = apps.get_model("library", "Category")
    database = schema_editor.connection.alias

    for book_data in SAMPLE_BOOKS:
        author, _ = Author.objects.using(database).get_or_create(
            name=book_data["author"],
            defaults={"email": "", "bio": ""},
        )
        category, _ = Category.objects.using(database).get_or_create(
            name=book_data["category"],
            defaults={"description": ""},
        )
        Book.objects.using(database).get_or_create(
            isbn=book_data["isbn"],
            defaults={
                "title": book_data["title"],
                "author": author,
                "category": category,
                "publisher": book_data["publisher"],
                "published_date": book_data["published_date"],
                "price": book_data["price"],
                "quantity": book_data["quantity"],
                "description": book_data["description"],
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("library", "0003_borrowrequest"),
    ]

    operations = [
        migrations.RunPython(
            add_sample_books,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
