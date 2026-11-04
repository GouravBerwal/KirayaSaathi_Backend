import re
from django.db import models
from django.utils.text import slugify


class BlogPost(models.Model):
    """
    Blog post model for KirayaSaathi public blog and SEO content marketing.
    """
    CATEGORY_CHOICES = [
        ("Tenant Management", "Tenant Management"),
        ("Electricity Submetering", "Electricity Submetering"),
        ("Rent Laws & Agreements", "Rent Laws & Agreements"),
        ("PG & Hostel Guide", "PG & Hostel Guide"),
        ("Property Investment", "Property Investment"),
        ("General Tips", "General Tips"),
    ]

    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    category = models.CharField(max_length=100, default="General Tips", db_index=True)
    excerpt = models.TextField(help_text="Short SEO meta description and summary for cards")
    content = models.TextField(help_text="Full blog post content with HTML / Markdown formatting")
    cover_image = models.TextField(
        blank=True,
        default="",
        help_text="URL or path to high-res article cover image",
    )
    author_name = models.CharField(max_length=100, default="KirayaSaathi Editorial Team")
    author_role = models.CharField(max_length=100, default="Real Estate & Rental Specialist")
    read_time = models.CharField(max_length=50, default="5 min read")
    tags = models.CharField(max_length=255, blank=True, default="", help_text="Comma-separated tags")
    is_published = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_featured", "-created_at"]
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "kirayasaathi-blog"
            candidate = base_slug
            idx = 1
            while BlogPost.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base_slug}-{idx}"
                idx += 1
            self.slug = candidate
        super().save(*args, **kwargs)
