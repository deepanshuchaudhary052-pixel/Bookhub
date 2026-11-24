
from django.contrib import admin
from .models import Author, Category, Book, BorrowRequest, Member, Loan


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email")
    search_fields = ("name", "email")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        "id", "title", "isbn", "author",
        "category", "price", "quantity",
    )
    search_fields = ("title", "isbn", "author__name")
    list_filter = ("category", "author")
    list_select_related = ("author", "category")


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "phone")
    search_fields = ("name", "email")


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = (
        "id", "book", "member", "issue_date",
        "due_date", "return_date",
    )
    list_filter = ("issue_date", "return_date")


@admin.register(BorrowRequest)
class BorrowRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "book", "member", "status", "requested_at", "reviewed_at")
    list_filter = ("status", "requested_at")
    search_fields = ("book__title", "member__name", "member__email")
    list_select_related = ("book", "member")
    readonly_fields = ("status", "requested_at", "reviewed_at")