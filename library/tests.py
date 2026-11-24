from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Author, Book, BorrowRequest, Category, Loan, Member


class LibraryViewTests(TestCase):
    def setUp(self):
        self.author = Author.objects.create(name="Jane Austen", email="jane@example.com")
        self.category = Category.objects.create(name="Classic", description="Classic literature")
        self.book = Book.objects.create(
            title="Pride and Prejudice",
            isbn="9780141199078",
            author=self.author,
            category=self.category,
            price="12.50",
            quantity=5,
        )

    def test_dashboard_page_loads(self):
        response = self.client.get(reverse("dashboard"), follow=True)
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_login_choice_offers_user_and_admin_in_english(self):
        response = self.client.get(reverse("login"))

        self.assertContains(response, "User Login")
        self.assertContains(response, "Admin Login")
        self.assertNotContains(response, "> Dashboard")
        self.assertNotContains(response, "> Books")
        self.assertNotContains(response, "Create account")
        self.assertNotContains(response, "Create an account")
        self.assertContains(response, 'href="/about-us/">About Us</a>')
        self.assertContains(response, 'aria-label="Current date and time"')
        self.assertNotContains(response, ">Navigation</div>")
        self.assertRegex(
            response.content.decode(),
            r"[A-Z][a-z]{2} \d{1,2}, \d{4} · \d{1,2}:\d{2} [AP]M",
        )

    def test_signed_in_users_see_dashboard_and_books_navigation(self):
        user = get_user_model().objects.create_user(
            username="nav-user@example.com",
            password="A-strong-test-password-42",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("book_list"))

        self.assertContains(response, "> Dashboard")
        self.assertContains(response, "> Books")
        self.assertContains(response, ">Navigation</div>")
        self.assertNotContains(response, 'aria-label="Current date and time"')
        self.assertNotContains(response, ">About Us</a>")

    def test_about_us_page_shows_project_owner(self):
        response = self.client.get(reverse("about_us"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Deepanshu Chaudhary")

    def test_user_and_admin_login_pages_only_accept_matching_accounts(self):
        user = get_user_model().objects.create_user(
            username="user@example.com",
            password="A-strong-test-password-42",
        )
        Member.objects.create(name="Test User", email=user.username)
        admin = get_user_model().objects.create_user(
            username="library-admin",
            password="A-strong-test-password-42",
            is_staff=True,
        )
        password = "A-strong-test-password-42"

        user_login = self.client.post(
            reverse("user_login"),
            {"username": user.username, "password": password},
        )
        self.assertRedirects(
            user_login,
            reverse("dashboard"),
            fetch_redirect_response=False,
        )

        self.client.logout()
        wrong_user_login = self.client.post(
            reverse("user_login"),
            {"username": admin.username, "password": password},
        )
        self.assertEqual(wrong_user_login.status_code, 200)
        self.assertContains(wrong_user_login, "Please use the Admin Login option")

        admin_login = self.client.post(
            reverse("admin_login"),
            {"username": admin.username, "password": password},
        )
        self.assertRedirects(
            admin_login,
            reverse("dashboard"),
            fetch_redirect_response=False,
        )

        self.client.logout()
        wrong_admin_login = self.client.post(
            reverse("admin_login"),
            {"username": user.username, "password": password},
        )
        self.assertEqual(wrong_admin_login.status_code, 200)
        self.assertContains(wrong_admin_login, "Please use the User Login option")

    def test_admin_dashboard_shows_library_stats(self):
        today = timezone.localdate()
        first_member = Member.objects.create(
            name="First Student",
            email="first@example.com",
        )
        second_member = Member.objects.create(
            name="Second Student",
            email="second@example.com",
        )
        pending_member = Member.objects.create(
            name="Waiting Student",
            email="waiting@example.com",
        )
        Loan.objects.create(
            book=self.book,
            member=first_member,
            issue_date=today - timedelta(days=10),
            due_date=today - timedelta(days=3),
            return_date=today - timedelta(days=2),
        )
        Loan.objects.create(
            book=self.book,
            member=first_member,
            issue_date=today - timedelta(days=1),
            due_date=today + timedelta(days=6),
        )
        Loan.objects.create(
            book=self.book,
            member=second_member,
            issue_date=today,
            due_date=today + timedelta(days=7),
        )
        BorrowRequest.objects.create(book=self.book, member=pending_member)
        admin = get_user_model().objects.create_user(
            username="admin",
            password="password",
            is_staff=True,
        )
        self.client.force_login(admin)

        response = self.client.get(reverse("dashboard"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "library/dashboard.html")
        self.assertContains(response, "Admin Dashboard")
        self.assertContains(response, "Pride and Prejudice")
        self.assertContains(response, "Students Who Borrowed")
        self.assertEqual(response.context["students_with_loans"], 2)
        self.assertEqual(response.context["active_students"], 2)
        self.assertEqual(response.context["pending_request_count"], 1)
        self.assertEqual(response.context["popular_books"][0].student_count, 2)
        self.assertEqual(response.context["popular_books"][0].active_loan_count, 2)
        self.assertContains(response, "Waiting Student")
        self.assertContains(response, "Approve")

    def test_staff_navigation_pages_show_members_authors_and_categories(self):
        Member.objects.create(name="Navigation Member", email="nav@example.com")
        staff = get_user_model().objects.create_user(
            username="navigation-admin",
            password="A-strong-test-password-42",
            is_staff=True,
        )
        self.client.force_login(staff)

        pages = (
            ("member_list", "Navigation Member"),
            ("author_list", "Jane Austen"),
            ("category_list", "Classic"),
        )
        for route_name, expected_text in pages:
            with self.subTest(route=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, expected_text)

        for login_route in ("user_login", "admin_login"):
            with self.subTest(login_route=login_route):
                login_response = self.client.get(reverse(login_route))
                self.assertNotContains(login_response, "Create an account")

        dashboard = self.client.get(reverse("admin_dashboard"))
        self.assertContains(dashboard, "Issue &amp; Return")
        self.assertContains(dashboard, "borrow-requests")

    def test_students_cannot_access_staff_navigation_pages(self):
        student = get_user_model().objects.create_user(
            username="navigation-student@example.com",
            password="A-strong-test-password-42",
        )
        self.client.force_login(student)

        for route_name in ("member_list", "author_list", "category_list"):
            with self.subTest(route=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 403)

    def test_staff_can_update_author_details(self):
        staff = get_user_model().objects.create_user(
            username="author-editor",
            password="A-strong-test-password-42",
            is_staff=True,
        )
        self.client.force_login(staff)

        response = self.client.post(
            reverse("author_update", args=[self.author.pk]),
            {
                "name": "Updated Author",
                "email": "updated@example.com",
                "bio": "Updated biography.",
            },
        )

        self.assertRedirects(response, reverse("author_list"))
        self.author.refresh_from_db()
        self.assertEqual(self.author.name, "Updated Author")
        self.assertEqual(self.author.email, "updated@example.com")
        self.assertEqual(self.author.bio, "Updated biography.")

    def test_students_cannot_update_author_details(self):
        student = get_user_model().objects.create_user(
            username="author-student@example.com",
            password="A-strong-test-password-42",
        )
        self.client.force_login(student)

        response = self.client.post(
            reverse("author_update", args=[self.author.pk]),
            {
                "name": "Unauthorized Change",
                "email": "unauthorized@example.com",
                "bio": "Should not be saved.",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.author.refresh_from_db()
        self.assertEqual(self.author.name, "Jane Austen")

    def test_staff_can_add_book_with_existing_or_new_author_and_category(self):
        existing_author = Author.objects.create(name="Form Test Author")
        existing_category = Category.objects.create(name="Form Test Category")
        staff = get_user_model().objects.create_user(
            username="book-editor",
            password="A-strong-test-password-42",
            is_staff=True,
        )
        self.client.force_login(staff)

        form_response = self.client.get(reverse("book_create"))
        self.assertContains(form_response, 'list="author-options"')
        self.assertContains(form_response, 'list="category-options"')
        self.assertContains(form_response, '<option value="Form Test Author">')
        self.assertContains(form_response, '<option value="Form Test Category">')

        existing_response = self.client.post(
            reverse("book_create"),
            {
                "title": "Sense and Sensibility",
                "isbn": "9780141199671",
                "author_name": "Form Test Author",
                "category_name": "Form Test Category",
                "price": "12.50",
                "quantity": "1",
            },
        )
        self.assertRedirects(existing_response, reverse("book_list"))
        existing_book = Book.objects.get(isbn="9780141199671")
        self.assertEqual(existing_book.author_id, existing_author.pk)
        self.assertEqual(existing_book.category_id, existing_category.pk)

        custom_response = self.client.post(
            reverse("book_create"),
            {
                "title": "A New Adventure",
                "isbn": "9780000000001",
                "author_name": "New Author",
                "category_name": "New Category",
                "price": "9.99",
                "quantity": "2",
            },
        )
        self.assertRedirects(custom_response, reverse("book_list"))
        custom_book = Book.objects.get(isbn="9780000000001")
        self.assertEqual(custom_book.author.name, "New Author")
        self.assertEqual(custom_book.category.name, "New Category")

    def test_student_dashboard_shows_only_their_current_loans(self):
        today = timezone.localdate()
        member = Member.objects.create(
            name="Alex Student",
            email="alex@example.com",
        )
        Loan.objects.create(
            book=self.book,
            member=member,
            issue_date=today - timedelta(days=7),
            due_date=today - timedelta(days=1),
        )
        another_member = Member.objects.create(
            name="Other Student",
            email="other@example.com",
        )
        Loan.objects.create(
            book=self.book,
            member=another_member,
            issue_date=today,
            due_date=today + timedelta(days=7),
        )
        BorrowRequest.objects.create(book=self.book, member=member)
        student = get_user_model().objects.create_user(
            username="alex@example.com",
            password="password",
        )
        self.client.force_login(student)

        response = self.client.get(reverse("dashboard"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "library/student_dashboard.html")
        self.assertContains(response, "Alex Student")
        self.assertContains(response, "loan-status overdue")
        self.assertEqual(response.context["active_loan_count"], 1)
        self.assertEqual(response.context["overdue_loans"], 1)
        self.assertEqual(len(response.context["active_loans"]), 1)
        self.assertContains(response, "Pending approval")
        self.assertContains(response, "student-clock-time")
        self.assertContains(response, "student-clock-date")
        self.assertContains(response, "Time left to return")
        self.assertEqual(
            response.context["next_due_loan"].book.title,
            self.book.title,
        )
        self.assertTrue(
            response.context["next_due_at"].startswith(
                today.isoformat()
            )
        )

    def test_student_dashboard_shows_countdown_for_upcoming_due_date(self):
        today = timezone.localdate()
        member = Member.objects.create(
            name="Upcoming Student",
            email="upcoming@example.com",
        )
        due_date = today + timedelta(days=12)
        Loan.objects.create(
            book=self.book,
            member=member,
            issue_date=today,
            due_date=due_date,
        )
        student = get_user_model().objects.create_user(
            username="upcoming@example.com",
            password="A-strong-test-password-42",
        )
        self.client.force_login(student)

        response = self.client.get(reverse("student_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Time left to return")
        self.assertContains(response, "Due by")
        self.assertContains(response, "data-next-due")
        self.assertEqual(
            response.context["next_due_at"][:10],
            (due_date + timedelta(days=1)).isoformat(),
        )

    def test_student_without_a_matching_member_is_forbidden(self):
        student = get_user_model().objects.create_user(
            username="unlinked@example.com",
            password="password",
        )
        self.client.force_login(student)

        response = self.client.get(reverse("dashboard"), follow=True)

        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "not linked to a library member", status_code=403)

    def test_student_registration_creates_member_and_signs_student_in(self):
        registration_page = self.client.get(reverse("student_register"))
        self.assertEqual(registration_page.status_code, 200)

        response = self.client.post(
            reverse("student_register"),
            {
                "name": "New Student",
                "username": "new.student@example.com",
                "phone": "555-0100",
                "password1": "A-strong-test-password-42",
                "password2": "A-strong-test-password-42",
            },
        )

        self.assertRedirects(response, reverse("student_dashboard"))
        user = get_user_model().objects.get(username="new.student@example.com")
        self.assertTrue(user.check_password("A-strong-test-password-42"))
        self.assertEqual(user.email, "new.student@example.com")
        self.assertEqual(user.username, "new.student@example.com")
        self.assertNotEqual(user.password, "A-strong-test-password-42")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(
            Member.objects.get(email="new.student@example.com").name,
            "New Student",
        )
        self.assertEqual(
            Member.objects.get(email="new.student@example.com").phone,
            "555-0100",
        )
        dashboard_response = self.client.get(reverse("student_dashboard"))
        self.assertEqual(dashboard_response.status_code, 200)

    def test_student_registration_rejects_existing_member_email(self):
        Member.objects.create(name="Existing Student", email="existing@example.com")

        response = self.client.post(
            reverse("student_register"),
            {
                "name": "Someone Else",
                "username": "existing@example.com",
                "password1": "A-strong-test-password-42",
                "password2": "A-strong-test-password-42",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already registered as a library member")
        self.assertFalse(
            get_user_model().objects.filter(username="existing@example.com").exists()
        )

    def test_staff_can_create_user_account_and_member_profile(self):
        staff = get_user_model().objects.create_user(
            username="existing-admin",
            password="A-strong-test-password-42",
            is_staff=True,
        )
        self.client.force_login(staff)

        dashboard_response = self.client.get(reverse("admin_dashboard"))
        self.assertContains(dashboard_response, "Add User")
        self.assertNotContains(dashboard_response, "Add Admin User")

        form_response = self.client.get(reverse("member_user_create"))
        self.assertContains(form_response, 'name="first_name"')
        self.assertContains(form_response, 'name="last_name"')
        self.assertNotContains(form_response, 'name="name"')

        response = self.client.post(
            reverse("member_user_create"),
            {
                "first_name": "New",
                "last_name": "Library User",
                "username": "new-user@example.com",
                "phone": "555-0199",
                "password1": "A-different-strong-password-42",
                "password2": "A-different-strong-password-42",
            },
        )

        self.assertRedirects(response, reverse("member_user_create"))
        new_user = get_user_model().objects.get(username="new-user@example.com")
        self.assertEqual(new_user.email, "new-user@example.com")
        self.assertEqual(new_user.first_name, "New")
        self.assertEqual(new_user.last_name, "Library User")
        self.assertFalse(new_user.is_staff)
        self.assertFalse(new_user.is_superuser)
        self.assertTrue(new_user.check_password("A-different-strong-password-42"))
        self.assertNotEqual(new_user.password, "A-different-strong-password-42")
        member = Member.objects.get(email="new-user@example.com")
        self.assertEqual(member.name, "New Library User")
        self.assertEqual(member.phone, "555-0199")

    def test_staff_can_see_add_user_option(self):
        staff = get_user_model().objects.create_user(
            username="existing-admin",
            password="A-strong-test-password-42",
            is_staff=True,
        )
        self.client.force_login(staff)

        dashboard_response = self.client.get(reverse("admin_dashboard"))
        self.assertContains(dashboard_response, "Add User")
        self.assertNotContains(dashboard_response, "Add Admin User")

    def test_superuser_can_create_admin_account(self):
        superuser = get_user_model().objects.create_user(
            username="existing-superuser",
            password="A-strong-test-password-42",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(superuser)

        dashboard_response = self.client.get(reverse("admin_dashboard"))
        self.assertContains(dashboard_response, "Add Admin User")
        self.assertContains(dashboard_response, "Add User")

        response = self.client.post(
            reverse("admin_user_create"),
            {
                "first_name": "New",
                "last_name": "Admin",
                "username": "new-admin",
                "email": "new-admin@example.com",
                "password1": "A-different-strong-password-42",
                "password2": "A-different-strong-password-42",
            },
        )

        self.assertRedirects(response, reverse("admin_user_create"))
        new_admin = get_user_model().objects.get(username="new-admin")
        self.assertEqual(new_admin.first_name, "New")
        self.assertEqual(new_admin.last_name, "Admin")
        self.assertTrue(new_admin.is_staff)
        self.assertFalse(new_admin.is_superuser)
        self.assertTrue(new_admin.check_password("A-different-strong-password-42"))
        self.assertFalse(Member.objects.filter(email="new-admin@example.com").exists())

    def test_staff_cannot_create_admin_account(self):
        staff = get_user_model().objects.create_user(
            username="existing-admin",
            password="A-strong-test-password-42",
            is_staff=True,
        )
        self.client.force_login(staff)

        response = self.client.post(
            reverse("admin_user_create"),
            {
                "username": "new-admin",
                "email": "new-admin@example.com",
                "password1": "A-different-strong-password-42",
                "password2": "A-different-strong-password-42",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            get_user_model().objects.filter(username="new-admin").exists()
        )

    def test_student_cannot_create_user_account_from_admin_page(self):
        student = get_user_model().objects.create_user(
            username="student@example.com",
            password="A-strong-test-password-42",
        )
        self.client.force_login(student)

        response = self.client.post(
            reverse("member_user_create"),
            {
                "name": "New User",
                "username": "new-user@example.com",
                "password1": "A-different-strong-password-42",
                "password2": "A-different-strong-password-42",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            get_user_model().objects.filter(username="new-user@example.com").exists()
        )
        self.assertFalse(Member.objects.filter(email="new-user@example.com").exists())

    def test_students_cannot_manage_books(self):
        student = get_user_model().objects.create_user(
            username="student@example.com",
            password="password",
        )
        self.client.force_login(student)

        response = self.client.get(reverse("book_create"))

        self.assertEqual(response.status_code, 403)

    def test_student_can_request_book_and_staff_can_approve_it(self):
        member = Member.objects.create(
            name="Borrowing Student",
            email="borrower@example.com",
        )
        student = get_user_model().objects.create_user(
            username=member.email,
            password="password",
        )
        self.client.force_login(student)

        response = self.client.post(reverse("request_book", args=[self.book.pk]))

        self.assertRedirects(response, reverse("book_list"))
        borrow_request = BorrowRequest.objects.get(member=member, book=self.book)
        self.assertEqual(borrow_request.status, BorrowRequest.Status.PENDING)
        self.client.post(reverse("request_book", args=[self.book.pk]))
        self.assertEqual(
            BorrowRequest.objects.filter(member=member, book=self.book).count(),
            1,
        )
        catalog_response = self.client.get(reverse("book_list"))
        self.assertContains(catalog_response, "Request pending")
        self.assertContains(catalog_response, "4 available")
        self.assertEqual(
            self.client.post(
                reverse(
                    "review_borrow_request",
                    args=[borrow_request.pk, "approve"],
                )
            ).status_code,
            403,
        )

        admin = get_user_model().objects.create_user(
            username="library-admin",
            password="password",
            is_staff=True,
        )
        self.client.force_login(admin)
        response = self.client.post(
            reverse(
                "review_borrow_request",
                args=[borrow_request.pk, "approve"],
            )
        )

        today = timezone.localdate()
        self.assertRedirects(response, reverse("admin_dashboard"))
        borrow_request.refresh_from_db()
        self.assertEqual(borrow_request.status, BorrowRequest.Status.APPROVED)
        self.assertIsNotNone(borrow_request.reviewed_at)
        loan = Loan.objects.get(member=member, book=self.book)
        self.assertEqual(loan.issue_date, today)
        self.assertEqual(loan.due_date, today + timedelta(days=14))

        self.client.force_login(student)
        student_dashboard = self.client.get(reverse("student_dashboard"))
        self.assertContains(student_dashboard, "Approved")
        self.assertContains(student_dashboard, "Pride and Prejudice")

        self.client.force_login(admin)
        dashboard_response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertContains(dashboard_response, "Currently Borrowed Books")
        self.assertContains(dashboard_response, "Mark returned")

    def test_staff_can_reject_request_and_student_sees_status(self):
        member = Member.objects.create(
            name="Requesting Student",
            email="requesting@example.com",
        )
        borrow_request = BorrowRequest.objects.create(
            book=self.book,
            member=member,
        )
        admin = get_user_model().objects.create_user(
            username="library-admin",
            password="password",
            is_staff=True,
        )
        self.client.force_login(admin)

        response = self.client.post(
            reverse(
                "review_borrow_request",
                args=[borrow_request.pk, "reject"],
            )
        )

        self.assertRedirects(response, reverse("admin_dashboard"))
        borrow_request.refresh_from_db()
        self.assertEqual(borrow_request.status, BorrowRequest.Status.REJECTED)
        self.assertFalse(Loan.objects.filter(member=member, book=self.book).exists())

    def test_student_cannot_request_book_without_available_copies(self):
        self.book.quantity = 1
        self.book.save(update_fields=("quantity",))
        existing_member = Member.objects.create(
            name="Existing Borrower",
            email="existing-borrower@example.com",
        )
        Loan.objects.create(
            book=self.book,
            member=existing_member,
            issue_date=timezone.localdate(),
            due_date=timezone.localdate() + timedelta(days=14),
        )
        member = Member.objects.create(
            name="Waiting Student",
            email="waiting@example.com",
        )
        student = get_user_model().objects.create_user(
            username=member.email,
            password="password",
        )
        self.client.force_login(student)

        response = self.client.post(reverse("request_book", args=[self.book.pk]))

        self.assertRedirects(response, reverse("book_list"))
        self.assertFalse(
            BorrowRequest.objects.filter(member=member, book=self.book).exists()
        )

    def test_staff_can_mark_active_loan_returned(self):
        member = Member.objects.create(
            name="Returning Student",
            email="returning@example.com",
        )
        today = timezone.localdate()
        loan = Loan.objects.create(
            book=self.book,
            member=member,
            issue_date=today - timedelta(days=5),
            due_date=today + timedelta(days=9),
        )
        admin = get_user_model().objects.create_user(
            username="library-admin",
            password="password",
            is_staff=True,
        )
        self.client.force_login(admin)

        response = self.client.post(reverse("return_loan", args=[loan.pk]))

        self.assertRedirects(response, reverse("admin_dashboard"))
        loan.refresh_from_db()
        self.assertEqual(loan.return_date, today)

    def test_book_list_page_loads(self):
        response = self.client.get(reverse("book_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pride and Prejudice")

    def test_sample_books_are_available_in_catalogue(self):
        expected_titles = (
            "Pride and Prejudice",
            "Frankenstein",
            "The Adventures of Sherlock Holmes",
            "Dracula",
            "Alice's Adventures in Wonderland",
        )
        for title in expected_titles:
            with self.subTest(title=title):
                self.assertTrue(Book.objects.filter(title=title).exists())

        self.assertEqual(
            Book.objects.filter(isbn__in=[
                "9780141439518",
                "9780141439471",
                "9780199536955",
                "9780141439846",
                "9780141439761",
            ]).count(),
            5,
        )
