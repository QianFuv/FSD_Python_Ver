import os
import unittest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.models.student import Student
from src.models.subject import Subject
from src.models.database import Database
from src.controllers.university_controller import UniversityController
from src.controllers.student_controller import StudentController
from src.controllers.admin_controller import AdminController
from src.controllers.subject_controller import SubjectController
from src.core.constants import EMAIL_PATTERN, PASSWORD_PATTERN


class TestStudent(unittest.TestCase):
    """Test cases for Student model."""

    def setUp(self):
        """Set up test environment."""
        self.student = Student(
            name="Test Student",
            email="test.student@university.com",
            password="Password123"
        )

    def test_initialization(self):
        """Test student initialization."""
        self.assertEqual(self.student.name, "Test Student")
        self.assertEqual(self.student.email, "test.student@university.com")
        self.assertEqual(self.student.password, "Password123")
        self.assertEqual(len(self.student.subjects), 0)
        self.assertTrue(len(self.student.id) == 6)
        self.assertTrue(self.student.id.isdigit())

    def test_enrol_subject(self):
        """Test subject enrollment."""
        # Test successful enrollment
        subject = Subject()
        self.assertTrue(self.student.enrol_subject(subject))
        self.assertEqual(len(self.student.subjects), 1)

        # Test max enrollment limit
        for _ in range(Student.MAX_SUBJECTS):
            self.student.enrol_subject(Subject())
        self.assertFalse(self.student.enrol_subject(Subject()))
        self.assertEqual(len(self.student.subjects), Student.MAX_SUBJECTS)

    def test_remove_subject(self):
        """Test subject removal."""
        subject = Subject()
        self.student.enrol_subject(subject)
        self.assertTrue(self.student.remove_subject(subject.id))
        self.assertEqual(len(self.student.subjects), 0)
        self.assertFalse(self.student.remove_subject("nonexistent"))

    def test_average_mark(self):
        """Test average mark calculation."""
        # Test with no subjects
        self.assertEqual(self.student.get_average_mark(), 0.0)

        # Test with one subject
        subject = Subject(mark=75.0)
        self.student.enrol_subject(subject)
        self.assertEqual(self.student.get_average_mark(), 75.0)

        # Test with multiple subjects
        subject2 = Subject(mark=85.0)
        self.student.enrol_subject(subject2)
        self.assertEqual(self.student.get_average_mark(), 80.0)

    def test_passing_status(self):
        """Test passing/failing status."""
        # Test passing
        self.student.enrol_subject(Subject(mark=75.0))
        self.assertTrue(self.student.is_passing())

        # Test failing
        self.student.subjects = []
        self.student.enrol_subject(Subject(mark=45.0))
        self.assertFalse(self.student.is_passing())

    def test_serialization(self):
        """Test student serialization."""
        subject = Subject()
        self.student.enrol_subject(subject)

        # Test to_dict
        student_dict = self.student.to_dict()
        self.assertEqual(student_dict["name"], "Test Student")
        self.assertEqual(student_dict["email"], "test.student@university.com")
        self.assertEqual(len(student_dict["subjects"]), 1)

        # Test from_dict
        new_student = Student.from_dict(student_dict)
        self.assertEqual(new_student.name, self.student.name)
        self.assertEqual(new_student.email, self.student.email)
        self.assertEqual(len(new_student.subjects), 1)


class TestSubject(unittest.TestCase):
    """Test cases for Subject model."""

    def setUp(self):
        """Set up test environment."""
        self.subject = Subject()

    def test_initialization(self):
        """Test subject initialization."""
        self.assertTrue(len(self.subject.id) == 3)
        self.assertTrue(self.subject.id.isdigit())
        self.assertTrue(25 <= self.subject.mark <= 100)
        self.assertIn(self.subject.grade, ["HD", "D", "C", "P", "Z"])

    def test_grade_calculation(self):
        """Test grade calculation."""
        grade_tests = [
            (85, "HD"),
            (75, "D"),
            (65, "C"),
            (50, "P"),
            (45, "Z")
        ]

        for mark, expected_grade in grade_tests:
            subject = Subject(mark=mark)
            self.assertEqual(subject.grade, expected_grade)

    def test_custom_initialization(self):
        """Test initialization with custom values."""
        subject = Subject("999", 95.5)
        self.assertEqual(subject.id, "999")
        self.assertEqual(subject.mark, 95.5)
        self.assertEqual(subject.grade, "HD")

    def test_serialization(self):
        """Test subject serialization."""
        subject_dict = self.subject.to_dict()
        self.assertEqual(len(subject_dict["id"]), 3)
        self.assertTrue(25 <= subject_dict["mark"] <= 100)
        self.assertIn(subject_dict["grade"], ["HD", "D", "C", "P", "Z"])

        new_subject = Subject.from_dict(subject_dict)
        self.assertEqual(new_subject.id, self.subject.id)
        self.assertEqual(new_subject.mark, self.subject.mark)
        self.assertEqual(new_subject.grade, self.subject.grade)


class TestDatabase(unittest.TestCase):
    """Test cases for Database model."""

    def setUp(self):
        """Set up test environment."""
        self.test_file = "test_students.data"
        self.database = Database(self.test_file)
        self.student = Student(
            name="Test Student",
            email="test.student@university.com",
            password="Password123"
        )

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_file_creation(self):
        """Test database file creation."""
        self.assertTrue(os.path.exists(self.test_file))
        with open(self.test_file, 'r') as f:
            data = json.load(f)
            self.assertEqual(data, [])

    def test_add_student(self):
        """Test adding students."""
        # Test successful addition
        self.assertTrue(self.database.add_student(self.student))

        # Test duplicate prevention
        self.assertFalse(self.database.add_student(self.student))

    def test_get_student(self):
        """Test retrieving students."""
        self.database.add_student(self.student)

        # Test successful retrieval
        found_student = self.database.get_student_by_email(self.student.email)
        self.assertEqual(found_student.name, self.student.name)

        # Test nonexistent student
        self.assertIsNone(self.database.get_student_by_email("nonexistent@university.com"))

    def test_update_student(self):
        """Test updating students."""
        self.database.add_student(self.student)

        # Modify student and update
        self.student.name = "Updated Name"
        self.assertTrue(self.database.update_student(self.student))

        # Verify update
        updated = self.database.get_student_by_email(self.student.email)
        self.assertEqual(updated.name, "Updated Name")

        # Test updating nonexistent student
        nonexistent = Student("New", "new@university.com", "Password123")
        self.assertFalse(self.database.update_student(nonexistent))

    def test_remove_student(self):
        """Test removing students."""
        self.database.add_student(self.student)

        # Test successful removal
        self.assertTrue(self.database.remove_student(self.student.id))
        self.assertIsNone(self.database.get_student_by_email(self.student.email))

        # Test removing nonexistent student
        self.assertFalse(self.database.remove_student("nonexistent"))

    def test_clear_all(self):
        """Test clearing all students."""
        self.database.add_student(self.student)
        self.database.clear_all()
        self.assertEqual(self.database.load_all_students(), [])


class TestStudentController(unittest.TestCase):
    """Test cases for StudentController."""

    def setUp(self):
        """Set up test environment."""
        # Create mock view
        self.view = Mock()
        self.controller = StudentController(self.view)

        # Create mock database
        self.mock_db = Mock()
        self.controller.database = self.mock_db

        # Create mock subject controller to prevent run loop
        self.mock_subject_controller = Mock()
        self.controller.subject_controller = self.mock_subject_controller

        # Create a test student for reuse
        self.test_student = Student(
            name="Test Student",
            email="test.student@university.com",
            password="Password123"
        )

    def test_email_validation_valid_emails(self):
        """Test email validation with valid email addresses."""
        valid_emails = [
            "test@university.com",
            "test.name@university.com",
            "test123@university.com",
            "firstname.lastname@university.com",  # From requirements doc
            "student.name@university.com"
        ]

        for email in valid_emails:
            with self.subTest(email=email):
                self.assertTrue(
                    self.controller._validate_email(email),
                    f"Email {email} should be valid"
                )
                self.view.display_error.assert_not_called()
                self.view.display_error.reset_mock()

    def test_email_validation_invalid_emails(self):
        """Test email validation with invalid email addresses."""
        invalid_emails = [
            "test@gmail.com",  # Wrong domain
            "test@university",  # From requirements doc
            "@university.com",  # Missing local part
            "test@",  # Incomplete
            "",  # Empty string
            "test@other.com",  # Wrong domain
            "test@university.org"  # Wrong domain
        ]

        for email in invalid_emails:
            with self.subTest(email=email):
                self.assertFalse(
                    self.controller._validate_email(email),
                    f"Email {email} should be invalid"
                )
                self.view.display_error.assert_called_with(
                    "Invalid email format. Must end with @university.com"
                )
                self.view.display_error.reset_mock()

    def test_password_validation_valid_passwords(self):
        """Test password validation with valid passwords."""
        # According to requirements:
        # (i) Starts with upper-case character
        # (ii) Contains at least five (5) letters
        # (iii) Followed by three (3) or more digits
        valid_passwords = [
            "Password123",  # Basic valid password
            "Student123",  # Another valid format
            "Abcdef123",  # More letters
            "Testing123",  # More complex
            "Simple123"  # Minimal valid
        ]

        for password in valid_passwords:
            with self.subTest(password=password):
                result = self.controller._validate_password(password)
                self.assertTrue(
                    result,
                    f"Password {password} should be valid"
                )
                self.view.display_error.reset_mock()

    def test_password_validation_invalid_passwords(self):
        """Test password validation with invalid passwords."""
        invalid_passwords = [
            "password123",  # No uppercase
            "Pass12",  # Not enough numbers
            "Password",  # No numbers
            "Pass123!",  # Special character
            "123Password",  # Starts with number
            "Ab123",  # Not enough letters
            "password",  # No numbers, no uppercase
            "12345678",  # Only numbers
            "abcdef123",  # No uppercase
            "PASSword12"  # Numbers not at end
        ]

        for password in invalid_passwords:
            with self.subTest(password=password):
                self.assertFalse(
                    self.controller._validate_password(password),
                    f"Password {password} should be invalid"
                )
                self.view.display_error.assert_called_with(
                    "Invalid password format. Must start with uppercase, "
                    "contain at least 5 letters followed by 3+ digits"
                )
                self.view.display_error.reset_mock()

    def test_register_success(self):
        """Test successful student registration."""
        form_data = {
            "name": "Test Student",
            "email": "new.student@university.com",
            "password": "Password123"
        }
        self.view.display_registration_form.return_value = form_data
        self.mock_db.get_student_by_email.return_value = None
        self.mock_db.add_student.return_value = True

        self.controller.register()

        self.mock_db.get_student_by_email.assert_called_once_with(form_data["email"])
        self.mock_db.add_student.assert_called_once()
        self.view.display_success.assert_called_once_with("Registration successful!")

    def test_register_existing_email(self):
        """Test registration with existing email."""
        form_data = {
            "name": "Test Student",
            "email": "existing@university.com",
            "password": "Password123"
        }
        self.view.display_registration_form.return_value = form_data
        self.mock_db.get_student_by_email.return_value = self.test_student

        self.controller.register()

        self.mock_db.get_student_by_email.assert_called_once_with(form_data["email"])
        self.mock_db.add_student.assert_not_called()
        self.view.display_error.assert_called_once_with("Student already exists!")

    def test_register_invalid_email(self):
        """Test registration with invalid email."""
        form_data = {
            "name": "Test Student",
            "email": "invalid@gmail.com",
            "password": "Password123"
        }
        self.view.display_registration_form.return_value = form_data

        self.controller.register()

        self.mock_db.get_student_by_email.assert_not_called()
        self.mock_db.add_student.assert_not_called()
        self.view.display_error.assert_called_once()

    def test_login_success(self):
        """Test successful login."""
        # Setup form data
        form_data = {
            "email": "test@university.com",
            "password": "Password123"
        }

        # Setup mocks
        self.view.display_login_form.return_value = form_data
        self.mock_db.get_student_by_email.return_value = self.test_student

        # Execute login
        self.controller.login()

        # Verify
        self.mock_db.get_student_by_email.assert_called_once_with(form_data["email"])
        self.view.display_success.assert_called_once_with("Login successful!")
        self.mock_subject_controller.run.assert_called_once_with(self.test_student)

        def test_login_nonexistent_email(self):
            """Test login with nonexistent email."""
            # Setup form data
            form_data = {
                "email": "nonexistent@university.com",
                "password": "Password123"
            }

            # Setup mocks
            self.view.display_login_form.return_value = form_data
            self.mock_db.get_student_by_email.return_value = None

            # Execute login
            self.controller.login()

            # Verify
            self.mock_db.get_student_by_email.assert_called_once_with(form_data["email"])
            self.view.display_error.assert_called_once_with("Invalid credentials!")
            self.mock_subject_controller.run.assert_not_called()

        def test_login_wrong_password(self):
            """Test login with wrong password."""
            # Setup form data
            form_data = {
                "email": "test@university.com",
                "password": "WrongPassword123"
            }

            # Setup mocks
            self.view.display_login_form.return_value = form_data
            self.mock_db.get_student_by_email.return_value = self.test_student

            # Execute login
            self.controller.login()

            # Verify
            self.mock_db.get_student_by_email.assert_called_once_with(form_data["email"])
            self.view.display_error.assert_called_once_with("Invalid credentials!")
            self.mock_subject_controller.run.assert_not_called()

        def test_handle_choice_login(self):
            """Test handle_choice with login option."""
            with patch.object(self.controller, 'login') as mock_login:
                result = self.controller.handle_choice('L')
                mock_login.assert_called_once()
                self.assertTrue(result)

        def test_handle_choice_register(self):
            """Test handle_choice with register option."""
            with patch.object(self.controller, 'register') as mock_register:
                result = self.controller.handle_choice('R')
                mock_register.assert_called_once()
                self.assertTrue(result)

        def test_handle_choice_exit(self):
            """Test handle_choice with exit option."""
            result = self.controller.handle_choice('X')
            self.assertFalse(result)

        def test_handle_choice_invalid(self):
            """Test handle_choice with invalid option."""
            result = self.controller.handle_choice('invalid')
            self.view.display_error.assert_called_once_with("Invalid option")
            self.assertTrue(result)

    class TestAdminController(unittest.TestCase):
        """Test cases for AdminController."""

        def setUp(self):
            """Set up test environment."""
            self.view = Mock()
            self.controller = AdminController(self.view)
            # Create mock database
            self.mock_db = Mock()
            self.controller.database = self.mock_db

            # Setup test students
            self.students = [
                Student("Test1", "test1@university.com", "Password123"),
                Student("Test2", "test2@university.com", "Password123")
            ]
            # Add subjects with different grades
            self.students[0].enrol_subject(Subject(mark=85))  # HD
            self.students[1].enrol_subject(Subject(mark=45))  # Z

        def test_group_students(self):
            """Test grouping students by grade."""
            # Setup mock
            self.mock_db.load_all_students.return_value = self.students

            # Execute
            self.controller.group_students()

            # Verify
            self.mock_db.load_all_students.assert_called_once()
            self.view.display_grade_groups.assert_called_once()
            # Verify that the argument is a dictionary
            args, _ = self.view.display_grade_groups.call_args
            self.assertIsInstance(args[0], dict)

        def test_partition_students(self):
            """Test partitioning students by pass/fail."""
            # Setup mock
            self.mock_db.load_all_students.return_value = self.students

            # Execute
            self.controller.partition_students()

            # Verify
            self.mock_db.load_all_students.assert_called_once()
            self.view.display_partitioned_students.assert_called_once()
            # Verify arguments
            args = self.view.display_partitioned_students.call_args[0]
            self.assertTrue(len(args) == 2)
            self.assertIsInstance(args[0], list)  # passing students
            self.assertIsInstance(args[1], list)  # failing students

        def test_remove_student(self):
            """Test removing a student."""
            # Setup
            student_id = "123456"
            self.mock_db.remove_student.return_value = True

            # Execute
            result = self.controller.remove_student(student_id)

            # Verify
            self.assertTrue(result)
            self.mock_db.remove_student.assert_called_once_with(student_id)
            self.view.display_success.assert_called_once_with(f"Student {student_id} removed successfully!")

        def test_remove_student_not_found(self):
            """Test removing a non-existent student."""
            # Setup
            student_id = "999999"
            self.mock_db.remove_student.return_value = False

            # Execute
            result = self.controller.remove_student(student_id)

            # Verify
            self.assertFalse(result)
            self.mock_db.remove_student.assert_called_once_with(student_id)
            self.view.display_error.assert_called_once_with(f"Student {student_id} not found!")

        def test_clear_database(self):
            """Test clearing the database."""
            # Setup
            self.view.confirm_action.return_value = True

            # Execute
            result = self.controller.clear_database()

            # Verify
            self.assertTrue(result)
            self.mock_db.clear_all.assert_called_once()
            self.view.display_success.assert_called_once_with("Database cleared successfully!")

        def test_clear_database_cancelled(self):
            """Test cancelling database clearing."""
            # Setup
            self.view.confirm_action.return_value = False

            # Execute
            result = self.controller.clear_database()

            # Verify
            self.assertTrue(result)  # Returns True to keep menu running
            self.mock_db.clear_all.assert_not_called()
            self.view.display_success.assert_called_once_with("Operation cancelled")

    def run_tests():
        """Run all tests."""
        unittest.main(verbosity=2)

    if __name__ == '__main__':
        run_tests()