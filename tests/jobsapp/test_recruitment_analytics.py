from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from jobsapp.models import Applicant, Hiring, Interview, Job
from tests.factories.job_factory import JobFactory
from tests.factories.user_factory import UserFactory


class RecruitmentAnalyticsTests(TestCase):
    def setUp(self):
        self.job = JobFactory()
        self.candidate = UserFactory()

    def test_hiring_requires_an_accepted_application(self):
        application = Applicant.objects.create(user=self.candidate, job=self.job, status=1)

        with self.assertRaises(ValidationError):
            Hiring.objects.create(applicant=application)

    def test_report_uses_confirmed_hires_and_application_to_hire_days(self):
        now = timezone.now()
        application = Applicant.objects.create(
            user=self.candidate,
            job=self.job,
            status=2,
            created_at=now - timedelta(days=12),
        )
        Interview.objects.create(
            applicant=application,
            stage="Technical interview",
            scheduled_at=now - timedelta(days=11),
            status=Interview.Status.COMPLETED,
        )
        Hiring.objects.create(
            applicant=application,
            hired_at=now - timedelta(days=2),
        )

        output = StringIO()
        call_command("recruitment_analytics", stdout=output)
        report = output.getvalue()

        self.assertIn("Interview records: 1", report)
        self.assertIn("Confirmed hires: 1", report)
        self.assertIn("Hiring rate: 100.0%", report)
        self.assertIn("Average time to hire: 10.0 days", report)
