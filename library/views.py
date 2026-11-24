
from datetime import datetime, time, timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, F, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    AdminMemberCreationForm,
    AdminUserCreationForm,
    AuthorForm,
    BookForm,
    StudentRegistrationForm,
)
from .models import Author, Book, BorrowRequest, Category, Loan, Member


def staff_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden("Staff access is required.")
        return view_func(request, *args, **kwargs)

    return wrapped


@login_required
def dashboard(request):
    if request.user.is_staff:
        return redirect("admin_dashboard")
    return redirect("student_dashboard")


def student_register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = StudentRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                user = form.save()
                Member.objects.create(
                    name=form.cleaned_data["name"],
                    email=user.email,
                    phone=form.cleaned_data["phone"],
                )
        except IntegrityError:
            form.add_error(
                "username",
                "An account or member with this email already exists.",
            )
        else:
            login(request, user)
            return redirect("student_dashboard")

    return render(request, "registration/student_register.html", {"form": form})


def about_us(request):
    return render(request, "library/about_us.html")


@login_required
def admin_user_create(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Superuser access is required.")

    form = AdminUserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Admin user created successfully.")
        return redirect("admin_user_create")

    return render(
        request,
        "library/admin_user_form.html",
        {
            "form": form,
            "page_title": "Add Admin User",
            "form_heading": "Create an admin account",
            "form_intro": "The new account will be able to access the library admin dashboard.",
            "submit_label": "Create Admin User",
        },
    )


@staff_required
def member_user_create(request):
    form = AdminMemberCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                user = form.save()
                Member.objects.create(
                    name=f"{user.first_name} {user.last_name}",
                    email=user.email,
                    phone=form.cleaned_data["phone"],
                )
        except IntegrityError:
            form.add_error(
                "username",
                "An account or member with this email already exists.",
            )
        else:
            messages.success(request, "User account created successfully.")
            return redirect("member_user_create")

    return render(
        request,
        "library/admin_user_form.html",
        {
            "form": form,
            "page_title": "Add User",
            "form_heading": "Create a user account",
            "form_intro": "Add a library user and their member profile.",
            "submit_label": "Create User Account",
        },
    )


@staff_required
def admin_dashboard(request):
    today = timezone.localdate()
    pending_requests = BorrowRequest.objects.filter(
        status=BorrowRequest.Status.PENDING
    ).select_related("book", "member", "book__author")
    pending_requests = pending_requests.annotate(
        book_active_loan_count=Count(
            "book__loans",
            filter=Q(book__loans__return_date__isnull=True),
            distinct=True,
        ),
        book_pending_request_count=Count(
            "book__borrow_requests",
            filter=Q(
                book__borrow_requests__status=BorrowRequest.Status.PENDING
            ),
            distinct=True,
        ),
    )
    for borrow_request in pending_requests:
        borrow_request.available_quantity = max(
            0,
            borrow_request.book.quantity
            - borrow_request.book_active_loan_count
            - borrow_request.book_pending_request_count,
        )
    active_loans = Loan.objects.filter(
        return_date__isnull=True
    ).select_related("book", "member").order_by("due_date")
    context = {
        "today": today,
        "total_books": Book.objects.count(),
        "total_authors": Author.objects.count(),
        "total_categories": Category.objects.count(),
        "total_members": Member.objects.count(),
        "total_books_quantity": sum(Book.objects.values_list("quantity", flat=True)),
        "recent_books": Book.objects.select_related("author", "category").order_by("-created_at")[:5],
        "issued_books": Loan.objects.filter(return_date__isnull=True).count(),
        "students_with_loans": Loan.objects.values("member_id").distinct().count(),
        "active_students": (
            Loan.objects.filter(return_date__isnull=True)
            .values("member_id")
            .distinct()
            .count()
        ),
        "popular_books": (
            Book.objects.filter(loans__isnull=False)
            .select_related("author", "category")
            .annotate(
                student_count=Count("loans__member", distinct=True),
                active_loan_count=Count(
                    "loans",
                    filter=Q(loans__return_date__isnull=True),
                ),
            )
            .order_by("-student_count", "-active_loan_count", "title")[:8]
        ),
        "overdue_loans": Loan.objects.filter(
            return_date__isnull=True,
            due_date__lt=today,
        ).count(),
        "pending_requests": pending_requests,
        "pending_request_count": pending_requests.count(),
        "active_loans_list": active_loans,
    }
    return render(request, "library/dashboard.html", context)


@staff_required
def member_list(request):
    members = Member.objects.order_by("name")
    return render(
        request,
        "library/member_list.html",
        {"members": members},
    )


@staff_required
def author_list(request):
    authors = Author.objects.order_by("name")
    return render(
        request,
        "library/author_list.html",
        {"authors": authors},
    )


@staff_required
def author_update(request, pk):
    author = get_object_or_404(Author, pk=pk)
    form = AuthorForm(request.POST or None, instance=author)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Author details updated successfully.")
        return redirect("author_list")

    return render(
        request,
        "library/author_form.html",
        {"form": form, "author": author},
    )


@staff_required
def category_list(request):
    categories = Category.objects.order_by("name")
    return render(
        request,
        "library/category_list.html",
        {"categories": categories},
    )


@login_required
def student_dashboard(request):
    if request.user.is_staff:
        return redirect("admin_dashboard")

    member = Member.objects.filter(email__iexact=request.user.username).first()
    if member is None:
        return HttpResponseForbidden(
            "Your account is not linked to a library member. "
            "Contact the library administrator."
        )

    today = timezone.localdate()
    active_loans = member.loans.filter(return_date__isnull=True).select_related(
        "book",
        "book__author",
    ).order_by("due_date")
    next_due_loan = active_loans.first()
    next_due_at = None
    if next_due_loan is not None:
        next_due_at = timezone.make_aware(
            datetime.combine(next_due_loan.due_date + timedelta(days=1), time.min)
        ).isoformat()
    borrow_requests = member.borrow_requests.select_related(
        "book",
        "book__author",
    ).order_by("-requested_at")
    context = {
        "member": member,
        "today": today,
        "active_loans": active_loans,
        "next_due_loan": next_due_loan,
        "next_due_at": next_due_at,
        "clock_timestamp": int(timezone.now().timestamp() * 1000),
        "display_timezone": settings.TIME_ZONE,
        "active_loan_count": active_loans.count(),
        "overdue_loans": active_loans.filter(due_date__lt=today).count(),
        "available_titles": (
            Book.objects.annotate(
                active_loan_count=Count(
                    "loans",
                    filter=Q(loans__return_date__isnull=True),
                    distinct=True,
                ),
                pending_request_count=Count(
                    "borrow_requests",
                    filter=Q(
                        borrow_requests__status=BorrowRequest.Status.PENDING
                    ),
                    distinct=True,
                ),
            )
            .filter(
                quantity__gt=F("active_loan_count") + F("pending_request_count")
            )
            .count()
        ),
        "borrow_requests": borrow_requests,
    }
    return render(request, "library/student_dashboard.html", context)


def book_list(request):
    query = request.GET.get("q", "").strip()
    selected_category = request.GET.get("category", "")
    books = Book.objects.select_related("author", "category").annotate(
        active_loan_count=Count(
            "loans",
            filter=Q(loans__return_date__isnull=True),
            distinct=True,
        ),
        pending_request_count=Count(
            "borrow_requests",
            filter=Q(borrow_requests__status=BorrowRequest.Status.PENDING),
            distinct=True,
        ),
    ).order_by("-created_at")

    if query:
        books = books.filter(
            Q(title__icontains=query)
            | Q(isbn__icontains=query)
            | Q(author__name__icontains=query)
        )

    if selected_category:
        books = books.filter(category_id=selected_category)

    paginator = Paginator(books, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    member = None
    active_book_ids = set()
    pending_book_ids = set()
    if request.user.is_authenticated and not request.user.is_staff:
        member = Member.objects.filter(email__iexact=request.user.username).first()
        if member:
            active_book_ids = set(
                member.loans.filter(return_date__isnull=True)
                .values_list("book_id", flat=True)
            )
            pending_book_ids = set(
                member.borrow_requests.filter(status=BorrowRequest.Status.PENDING)
                .values_list("book_id", flat=True)
            )
    for book in page_obj.object_list:
        book.available_quantity = max(
            0,
            book.quantity - book.active_loan_count - book.pending_request_count,
        )
        book.borrow_status = (
            "borrowed" if book.pk in active_book_ids
            else "pending" if book.pk in pending_book_ids
            else ""
        )

    return render(
        request,
        "library/book_list.html",
        {
            "books": page_obj.object_list,
            "page_obj": page_obj,
            "query": query,
            "selected_category": selected_category,
            "categories": Category.objects.all(),
            "member": member,
        },
    )


@login_required
@require_POST
def request_book(request, pk):
    if request.user.is_staff:
        return HttpResponseForbidden("Student accounts are required to request books.")

    member = Member.objects.filter(email__iexact=request.user.username).first()
    if member is None:
        return HttpResponseForbidden(
            "Your account is not linked to a library member. "
            "Contact the library administrator."
        )

    with transaction.atomic():
        book = get_object_or_404(Book.objects.select_for_update(), pk=pk)
        if member.loans.filter(book=book, return_date__isnull=True).exists():
            messages.info(request, "You already have this book checked out.")
        elif member.borrow_requests.filter(
            book=book,
            status=BorrowRequest.Status.PENDING,
        ).exists():
            messages.info(request, "Your request for this book is already pending.")
        else:
            active_loans = Loan.objects.filter(
                book=book,
                return_date__isnull=True,
            ).count()
            pending_requests = BorrowRequest.objects.filter(
                book=book,
                status=BorrowRequest.Status.PENDING,
            ).count()
            if active_loans + pending_requests >= book.quantity:
                messages.error(request, "There are no copies available to request.")
            else:
                BorrowRequest.objects.create(book=book, member=member)
                messages.success(
                    request,
                    "Your borrow request was sent to the library administrator.",
                )
    return redirect("book_list")


@staff_required
@require_POST
def review_borrow_request(request, pk, decision):
    if decision not in ("approve", "reject"):
        return HttpResponseForbidden("Invalid request action.")

    today = timezone.localdate()
    with transaction.atomic():
        borrow_request = get_object_or_404(
            BorrowRequest.objects.select_for_update().select_related("book", "member"),
            pk=pk,
        )
        if borrow_request.status != BorrowRequest.Status.PENDING:
            messages.error(request, "This request has already been reviewed.")
            return redirect("admin_dashboard")

        if decision == "approve":
            book = Book.objects.select_for_update().get(pk=borrow_request.book_id)
            active_loans = Loan.objects.filter(
                book=book,
                return_date__isnull=True,
            ).count()
            other_pending_requests = BorrowRequest.objects.filter(
                book=book,
                status=BorrowRequest.Status.PENDING,
            ).exclude(pk=borrow_request.pk).count()
            if active_loans + other_pending_requests >= book.quantity:
                messages.error(
                    request,
                    f"No copies of {book.title} are currently available to approve.",
                )
                return redirect("admin_dashboard")

            Loan.objects.create(
                book=book,
                member=borrow_request.member,
                issue_date=today,
                due_date=today + timedelta(days=14),
            )
            borrow_request.status = BorrowRequest.Status.APPROVED
            due_date = today + timedelta(days=14)
            messages.success(
                request,
                f"Request approved. {borrow_request.member.name} should return "
                f"{book.title} by {due_date:%b %d, %Y}.",
            )
        else:
            borrow_request.status = BorrowRequest.Status.REJECTED
            messages.success(request, "Borrow request rejected.")
        borrow_request.reviewed_at = timezone.now()
        borrow_request.save(update_fields=("status", "reviewed_at"))

    return redirect("admin_dashboard")


@staff_required
@require_POST
def return_loan(request, pk):
    with transaction.atomic():
        loan = get_object_or_404(Loan.objects.select_for_update(), pk=pk)
        if loan.return_date is not None:
            messages.info(request, "This book has already been returned.")
        else:
            loan.return_date = timezone.localdate()
            loan.save(update_fields=("return_date",))
            messages.success(request, f"{loan.book.title} marked as returned.")
    return redirect("admin_dashboard")


@staff_required
def book_create(request):
    form = BookForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("book_list")

    return render(
        request,
        "library/book_form.html",
        {"form": form, "page_title": "Add Book"},
    )


@staff_required
def book_update(request, pk):
    book = get_object_or_404(Book, pk=pk)
    form = BookForm(request.POST or None, request.FILES or None, instance=book)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("book_list")

    return render(
        request,
        "library/book_form.html",
        {"form": form, "book": book, "page_title": "Edit Book"},
    )


@staff_required
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)

    if request.method == "POST":
        book.delete()
        return redirect("book_list")

    return render(
        request,
        "library/book_confirm_delete.html",
        {"book": book, "page_title": "Delete Book"},
    )