from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone

from accounts.models import User
from categories.models import Category
from tags.models import Tag

from .manager import JobManager


class JobType(models.TextChoices):
    FULL_TIME = "1", "Full time"
    PART_TIME = "2", "Part time"
    INTERNSHIP = "3", "Internship"


class CompanySize(models.TextChoices):
    SIZE_1_10 = "1", "1-10 employees"
    SIZE_11_50 = "2", "11-50 employees"
    SIZE_51_200 = "3", "51-200 employees"
    SIZE_201_500 = "4", "201-500 employees"
    SIZE_501_1000 = "5", "501-1000 employees"
    SIZE_1000_PLUS = "6", "1000+ employees"


class WorkplaceType(models.TextChoices):
    ON_SITE = "on_site", "On-site"
    REMOTE = "remote", "Remote"
    HYBRID = "hybrid", "Hybrid"


class ExperienceLevel(models.TextChoices):
    ENTRY = "entry", "Entry level"
    MID = "mid", "Mid level"
    SENIOR = "senior", "Senior level"
    LEAD = "lead", "Lead/Staff"


class SalaryPeriod(models.TextChoices):
    MONTH = "month", "Per month"
    YEAR = "year", "Per year"
    HOUR = "hour", "Per hour"


class JobStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    CLOSED = "closed", "Closed"


class Company(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="companies")
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    tagline = models.CharField(max_length=160, blank=True, null=True)
    description = models.TextField(max_length=1000, blank=True, null=True)
    website = models.URLField(max_length=200, blank=True, null=True)
    logo = models.ImageField(upload_to="company_logos/", blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    headquarters = models.CharField(max_length=150, blank=True, null=True)
    size = models.CharField(choices=CompanySize.choices, max_length=20, blank=True)
    culture_benefits = models.TextField(blank=True, null=True, help_text="Describe company culture, benefits, and perks")
    is_verified = models.BooleanField(default=False)
    featured = models.BooleanField(default=False, help_text="Feature this company on the homepage")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    linkedin_url = models.URLField(max_length=200, blank=True, null=True)
    facebook_url = models.URLField(max_length=200, blank=True, null=True)
    cover_image = models.ImageField(upload_to="company_covers/", blank=True, null=True)

    class Meta:
        verbose_name_plural = "Companies"
        ordering = ["-featured", "-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "name"], name="uniq_company_name_per_owner"),
        ]

    def get_absolute_url(self):
        return reverse("jobs:company-detail", args=[self.id])

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.user_id}")
        super().save(*args, **kwargs)


class Job(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posted_jobs")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="jobs")
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="jobs",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=340, blank=True)
    description = models.TextField()
    responsibilities = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    location = models.CharField(max_length=200)
    type = models.CharField(choices=JobType.choices, max_length=10)
    workplace_type = models.CharField(choices=WorkplaceType.choices, max_length=20, default=WorkplaceType.ON_SITE)
    experience_level = models.CharField(choices=ExperienceLevel.choices, max_length=20, default=ExperienceLevel.ENTRY)
    application_deadline = models.DateTimeField()
    website = models.URLField(max_length=300, null=True, blank=True, help_text="Optional external apply URL")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    filled = models.BooleanField(default=False)
    status = models.CharField(choices=JobStatus.choices, max_length=20, default=JobStatus.PUBLISHED)
    salary = models.IntegerField(default=0, blank=True)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=5, default="BDT")
    salary_period = models.CharField(choices=SalaryPeriod.choices, max_length=10, default=SalaryPeriod.MONTH)
    tags = models.ManyToManyField(Tag)
    vacancy = models.IntegerField(default=1)
    is_featured = models.BooleanField(default=False)

    objects = JobManager()

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["status", "filled"]),
            models.Index(fields=["type", "workplace_type"]),
            models.Index(fields=["category"], name="jobsapp_job_category_idx"),
            models.Index(fields=["created_at"]),
            models.Index(fields=["application_deadline"]),
        ]

    def get_absolute_url(self):
        return reverse("jobs:jobs-detail", args=[self.id])

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.title}-{self.company_id}-{self.user_id}")
        super().save(*args, **kwargs)


class Applicant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applicants")
    created_at = models.DateTimeField(default=timezone.now)
    comment = models.TextField(blank=True, null=True)
    status = models.SmallIntegerField(default=1)

    class Meta:
        ordering = ["id"]
        unique_together = ["user", "job"]

    def __str__(self):
        return self.user.get_full_name()

    @property
    def get_status(self):
        if self.status == 1:
            return "Pending"
        elif self.status == 2:
            return "Accepted"
        else:
            return "Rejected"


class Interview(models.Model):
    """A scheduled recruitment interview belonging to one application."""

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        NO_SHOW = "no_show", "No show"

    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name="interviews")
    stage = models.CharField(max_length=80, default="Initial interview")
    scheduled_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["scheduled_at", "id"]
        indexes = [models.Index(fields=["status", "scheduled_at"])]

    def __str__(self):
        return f"{self.stage} — {self.applicant}"


class Hiring(models.Model):
    """A confirmed hire; separate from an application merely being accepted."""

    applicant = models.OneToOneField(Applicant, on_delete=models.CASCADE, related_name="hiring")
    hired_at = models.DateTimeField(default=timezone.now)
    start_date = models.DateField(null=True, blank=True)
    agreed_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=5, default="BDT")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-hired_at", "id"]

    def clean(self):
        # Acceptance is a prerequisite for a confirmed hire, not the same event.
        if not self.applicant_id:
            return
        if self.applicant.status != 2:
            raise ValidationError({"applicant": "Only an accepted application can be recorded as hired."})
        if self.hired_at and self.hired_at < self.applicant.created_at:
            raise ValidationError({"hired_at": "Hire date cannot be earlier than the application date."})

    def save(self, *args, **kwargs):
        # Model.save() does not call validation by itself; enforce it for admin,
        # scripts, and other callers so invalid hires cannot enter the database.
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Hire: {self.applicant.user} → {self.applicant.job}"


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="favorites")
    created_at = models.DateTimeField(default=timezone.now)
    soft_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.job.title
