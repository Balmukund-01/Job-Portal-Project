"""Print a small, explainable recruitment analytics report from portal data.

Run with: python manage.py recruitment_analytics
The command is deliberately read-only: it aggregates existing Django models
and never creates, updates, or deletes portal records.
"""

from django.core.management.base import BaseCommand
from django.db.models import Avg, Count, Q

from jobsapp.models import Applicant, Company, Hiring, Interview, Job, JobStatus


class Command(BaseCommand):
    help = "Summarize job demand, skills, companies, applications, and salary."

    def handle(self, *args, **options):
        # Each helper returns plain values so the calculations are easy to read
        # and the output can be checked against the corresponding database rows.
        self._print_overview()
        self._print_demanded_skills()
        self._print_locations()
        self._print_company_activity()
        self._print_application_outcomes()
        self._print_interviews_and_hiring()
        self._print_salary_trends()

    def _print_overview(self):
        total_jobs = Job.objects.count()
        active_jobs = Job.objects.filter(status=JobStatus.PUBLISHED, filled=False).count()
        self.stdout.write(self.style.MIGRATE_HEADING("Recruitment analytics overview"))
        self.stdout.write(f"Companies: {Company.objects.count()}")
        self.stdout.write(f"Jobs: {total_jobs} (active published: {active_jobs})")
        self.stdout.write(f"Applications: {Applicant.objects.count()}")

    def _print_demanded_skills(self):
        # A tag is the portal's normalized skill/category keyword. Distinct job
        # count prevents a repeated join row from overstating demand.
        skills = (
            Job.objects.values("tags__name")
            .annotate(job_count=Count("id", distinct=True))
            .exclude(tags__name__isnull=True)
            .order_by("-job_count", "tags__name")[:10]
        )
        self.stdout.write("\nTop demanded skills (tags)")
        self._print_rows(skills, "tags__name", "job_count")

    def _print_locations(self):
        locations = (
            Job.objects.values("location")
            .annotate(job_count=Count("id"))
            .order_by("-job_count", "location")[:10]
        )
        self.stdout.write("\nJobs by location")
        self._print_rows(locations, "location", "job_count")

    def _print_company_activity(self):
        # Active means a verified company with at least one published, unfilled job.
        active = Company.objects.filter(
            is_verified=True,
            jobs__status=JobStatus.PUBLISHED,
            jobs__filled=False,
        ).distinct().count()
        self.stdout.write(f"\nActive verified companies: {active}")

    def _print_application_outcomes(self):
        total = Applicant.objects.count()
        # Applicant.status uses 1=Pending, 2=Accepted, and other values=Rejected.
        accepted = Applicant.objects.filter(status=2).count()
        success_percent = (accepted / total * 100) if total else 0
        self.stdout.write("\nApplication outcomes")
        self.stdout.write(f"Accepted applications: {accepted}")
        self.stdout.write(f"Application success rate: {success_percent:.1f}% (accepted / all applications)")

    def _print_interviews_and_hiring(self):
        total_applications = Applicant.objects.count()
        hire_records = list(Hiring.objects.select_related("applicant"))
        hire_count = len(hire_records)
        hiring_rate = (hire_count / total_applications * 100) if total_applications else 0
        interview_count = Interview.objects.count()

        self.stdout.write("\nInterview and hiring funnel")
        self.stdout.write(f"Interview records: {interview_count}")
        self.stdout.write(f"Confirmed hires: {hire_count}")
        self.stdout.write(f"Hiring rate: {hiring_rate:.1f}% (confirmed hires / all applications)")

        if not hire_records:
            self.stdout.write("Average time to hire: unavailable (no confirmed hires recorded)")
            return

        # Calculate elapsed days per confirmed hire. Python timedelta arithmetic
        # keeps this portable across SQLite and PostgreSQL database backends.
        elapsed_days = [
            (hire.hired_at - hire.applicant.created_at).total_seconds() / 86400
            for hire in hire_records
        ]
        average_days = sum(elapsed_days) / len(elapsed_days)
        self.stdout.write(f"Average time to hire: {average_days:.1f} days (application date to hire date)")

    def _print_salary_trends(self):
        # Salary ranges are optional. Aggregate only rows with at least one
        # range value; currency and period are shown as separate group keys.
        salary_groups = (
            Job.objects.filter(Q(salary_min__isnull=False) | Q(salary_max__isnull=False))
            .values("salary_currency", "salary_period")
            .annotate(
                jobs=Count("id"),
                average_min=Avg("salary_min"),
                average_max=Avg("salary_max"),
            )
            .order_by("salary_currency", "salary_period")
        )
        self.stdout.write("\nSalary trends (grouped by currency and pay period)")
        if not salary_groups:
            self.stdout.write("No salary range data is available yet.")
            return
        for row in salary_groups:
            low = f"{row['average_min']:.2f}" if row["average_min"] is not None else "not provided"
            high = f"{row['average_max']:.2f}" if row["average_max"] is not None else "not provided"
            self.stdout.write(
                f"{row['salary_currency']} / {row['salary_period']}: "
                f"{row['jobs']} jobs, average range {low} to {high}"
            )

    def _print_rows(self, rows, label_key, value_key):
        if not rows:
            self.stdout.write("No data available.")
            return
        for row in rows:
            self.stdout.write(f"- {row[label_key] or 'Unspecified'}: {row[value_key]}")
