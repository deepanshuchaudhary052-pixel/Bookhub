
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Author, Book, Category, Member


class RoleLoginForm(AuthenticationForm):
    expected_staff = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "autocomplete": "username"}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "form-control", "autocomplete": "current-password"}
        )

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if user.is_staff != self.expected_staff:
            login_type = "Admin Login" if user.is_staff else "User Login"
            raise forms.ValidationError(
                f"Please use the {login_type} option for this account.",
                code="incorrect_account_type",
            )


class UserLoginForm(RoleLoginForm):
    expected_staff = False


class AdminLoginForm(RoleLoginForm):
    expected_staff = True


class StudentRegistrationForm(UserCreationForm):
    username = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "autocomplete": "email",
            }
        ),
    )
    name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": "name",
            }
        ),
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": "tel",
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username",)

    def clean_username(self):
        email = self.cleaned_data["username"].strip().lower()
        User = get_user_model()
        if User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        if Member.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "This email is already registered as a library member. "
                "Please contact the library administrator."
            )
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["username"]
        if commit:
            user.save()
        return user


class AdminMemberCreationForm(StudentRegistrationForm):
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": "form-control", "autocomplete": "given-name"}
        ),
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": "form-control", "autocomplete": "family-name"}
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("name")
        self.order_fields(
            (
                "first_name",
                "last_name",
                "username",
                "phone",
                "password1",
                "password2",
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get("first_name", "").strip()
        last_name = cleaned_data.get("last_name", "").strip()
        if first_name and last_name and len(f"{first_name} {last_name}") > 150:
            self.add_error(
                "last_name",
                "First and last name together cannot exceed 150 characters.",
            )
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        if commit:
            user.save()
        return user


class AdminUserCreationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": "form-control", "autocomplete": "given-name"}
        ),
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": "form-control", "autocomplete": "family-name"}
        ),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control"})
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("first_name", "last_name", "username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "autocomplete": "username"}
        )
        self.fields["first_name"].widget.attrs.update(
            {"class": "form-control", "autocomplete": "given-name"}
        )
        self.fields["last_name"].widget.attrs.update(
            {"class": "form-control", "autocomplete": "family-name"}
        )
        self.fields["password1"].widget.attrs.update(
            {"class": "form-control", "autocomplete": "new-password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "form-control", "autocomplete": "new-password"}
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.is_staff = True
        if commit:
            user.save()
        return user


class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ("name", "email", "bio")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
        }


class BookForm(forms.ModelForm):
    author_name = forms.CharField(
        label="Author",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "list": "author-options",
                "placeholder": "Select or type an author name",
            }
        ),
    )
    category_name = forms.CharField(
        label="Category",
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "list": "category-options",
                "placeholder": "Select or type a category",
            }
        ),
    )

    class Meta:
        model = Book
        fields = [
            "title",
            "isbn",
            "author_name",
            "category_name",
            "publisher",
            "published_date",
            "price",
            "quantity",
            "description",
            "cover",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Book title"}
            ),
            "isbn": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "ISBN"}
            ),
            "publisher": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "published_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "price": forms.NumberInput(
                attrs={"class": "form-control", "min": "0", "step": "0.01"}
            ),
            "quantity": forms.NumberInput(
                attrs={"class": "form-control", "min": "0"}
            ),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 4}
            ),
            "cover": forms.ClearableFileInput(
                attrs={"class": "form-control"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.author_options = Author.objects.order_by("name", "pk")
        self.category_options = Category.objects.order_by("name", "pk")
        if self.instance.pk and not self.is_bound:
                self.initial.setdefault("author_name", self.instance.author.name)
                self.initial.setdefault("category_name", self.instance.category.name)

    def save(self, commit=True):
        book = super().save(commit=False)
        author_name = self.cleaned_data["author_name"].strip()
        category_name = self.cleaned_data["category_name"].strip()

        author = Author.objects.filter(name__iexact=author_name).order_by(
                "pk"
        ).first()
        if author is None:
                author = Author.objects.create(name=author_name)
        book.author = author

        category = Category.objects.filter(
                name__iexact=category_name
        ).first()
        if category is None:
                category, _ = Category.objects.get_or_create(name=category_name)
        book.category = category

        if commit:
                book.save()
                self.save_m2m()
        return book

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price