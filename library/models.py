
from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    isbn = models.CharField(max_length=20, unique=True)
    author = models.ForeignKey(
        Author,
        on_delete=models.PROTECT,
        related_name="books",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="books",
    )
    publisher = models.CharField(max_length=150, blank=True)
    published_date = models.DateField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True)
    cover = models.ImageField(upload_to="book_covers/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Member(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Loan(models.Model):
    book = models.ForeignKey(
        Book,
        on_delete=models.PROTECT,
        related_name="loans",
    )
    member = models.ForeignKey(
        Member,
        on_delete=models.PROTECT,
        related_name="loans",
    )
    issue_date = models.DateField()
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)

    @property
    def is_returned(self):
        return self.return_date is not None

    def __str__(self):
        return f"{self.book.title} - {self.member.name}"


class BorrowRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="borrow_requests",
    )
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="borrow_requests",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["requested_at"]

    def __str__(self):
        return f"{self.book.title} - {self.member.name} ({self.status})"
        