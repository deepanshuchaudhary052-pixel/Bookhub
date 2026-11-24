
from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("about-us/", views.about_us, name="about_us"),
    path("accounts/register/", views.student_register, name="student_register"),
    path("admin-users/add/", views.admin_user_create, name="admin_user_create"),
    path("library-users/add/", views.member_user_create, name="member_user_create"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-dashboard/members/", views.member_list, name="member_list"),
    path("admin-dashboard/authors/", views.author_list, name="author_list"),
    path(
        "admin-dashboard/authors/<int:pk>/edit/",
        views.author_update,
        name="author_update",
    ),
    path("admin-dashboard/categories/", views.category_list, name="category_list"),
    path("student-dashboard/", views.student_dashboard, name="student_dashboard"),
    path("books/<int:pk>/borrow/", views.request_book, name="request_book"),
    path(
        "borrow-requests/<int:pk>/<str:decision>/",
        views.review_borrow_request,
        name="review_borrow_request",
    ),
    path("loans/<int:pk>/return/", views.return_loan, name="return_loan"),
    path("books/", views.book_list, name="book_list"),
    path("books/add/", views.book_create, name="book_create"),
    path("books/<int:pk>/edit/", views.book_update, name="book_update"),
    path("books/<int:pk>/delete/", views.book_delete, name="book_delete"),
]