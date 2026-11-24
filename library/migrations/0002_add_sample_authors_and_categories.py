from django.db import migrations


def add_sample_catalog_data(apps, schema_editor):
    Author = apps.get_model("library", "Author")
    Category = apps.get_model("library", "Category")

    authors = [
        ("Alex Morgan", "alex.morgan@example.com", "Sample author"),
        ("Jamie Taylor", "jamie.taylor@example.com", "Sample author"),
        ("Sam Rivera", "sam.rivera@example.com", "Sample author"),
    ]
    categories = [
        ("Fiction", "Sample category"),
        ("Science", "Sample category"),
        ("History", "Sample category"),
        ("Technology", "Sample category"),
        ("Mystery", "Sample category"),
    ]

    for name, email, bio in authors:
        Author.objects.using(schema_editor.connection.alias).get_or_create(
            name=name,
            defaults={"email": email, "bio": bio},
        )

    for name, description in categories:
        Category.objects.using(schema_editor.connection.alias).get_or_create(
            name=name,
            defaults={"description": description},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("library", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            add_sample_catalog_data,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
