from django.contrib import admin
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage

# Register your models here.
from jobsapp.models import Company, Hiring, Interview, Job


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "user",
        "industry",
        "size",
        "featured",
        "created_at",
    ]
    list_filter = ["featured", "industry", "size", "created_at"]
    search_fields = ["name", "industry", "description"]
    date_hierarchy = "created_at"
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        ("Basic Information", {"fields": ("user", "name", "description", "website")}),
        ("Branding", {"fields": ("logo",)}),
        ("Company Details", {"fields": ("industry", "size", "culture_benefits")}),
        ("Settings", {"fields": ("featured",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "salary",
        "location",
        "type",
        "company",
        "application_deadline",
        "created_at",
        "filled",
        "user",
    ]
    list_filter = ["salary", "application_deadline", "created_at", "user", "filled"]
    date_hierarchy = "created_at"
    search_fields = ["title", "company__name"]


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ["applicant", "stage", "scheduled_at", "status"]
    list_filter = ["status", "scheduled_at"]
    search_fields = ["applicant__user__email", "applicant__job__title", "stage"]
    date_hierarchy = "scheduled_at"


@admin.register(Hiring)
class HiringAdmin(admin.ModelAdmin):
    list_display = ["applicant", "hired_at", "start_date", "agreed_salary", "currency"]
    list_filter = ["currency", "hired_at"]
    search_fields = ["applicant__user__email", "applicant__job__title"]
    date_hierarchy = "hired_at"
