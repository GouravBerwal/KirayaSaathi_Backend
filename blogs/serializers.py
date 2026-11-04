from rest_framework import serializers
from .models import BlogPost


class BlogPostListSerializer(serializers.ModelSerializer):
    """Public lightweight serializer for blog list & search results."""
    formatted_date = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "category",
            "excerpt",
            "cover_image",
            "author_name",
            "author_role",
            "read_time",
            "tags",
            "is_featured",
            "views_count",
            "created_at",
            "formatted_date",
        ]

    def get_formatted_date(self, obj):
        return obj.created_at.strftime("%b %d, %Y")


class BlogPostDetailSerializer(serializers.ModelSerializer):
    """Public comprehensive serializer for single blog view."""
    formatted_date = serializers.SerializerMethodField()
    related_posts = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "category",
            "excerpt",
            "content",
            "cover_image",
            "author_name",
            "author_role",
            "read_time",
            "tags",
            "is_featured",
            "views_count",
            "created_at",
            "updated_at",
            "formatted_date",
            "related_posts",
        ]

    def get_formatted_date(self, obj):
        return obj.created_at.strftime("%B %d, %Y")

    def get_related_posts(self, obj):
        related = (
            BlogPost.objects.filter(is_published=True)
            .exclude(pk=obj.pk)
            .filter(category=obj.category)[:3]
        )
        if not related.exists():
            related = BlogPost.objects.filter(is_published=True).exclude(pk=obj.pk)[:3]
        return BlogPostListSerializer(related, many=True).data


class BlogPostAdminSerializer(serializers.ModelSerializer):
    """Admin serializer for creating, updating, and viewing full blog records."""
    formatted_date = serializers.SerializerMethodField(read_only=True)
    slug = serializers.SlugField(required=False, allow_blank=True)

    class Meta:
        model = BlogPost
        fields = "__all__"

    def get_formatted_date(self, obj):
        return obj.created_at.strftime("%b %d, %Y")

    def validate(self, attrs):
        from django.utils.text import slugify
        slug = attrs.get("slug")
        title = attrs.get("title") or (self.instance.title if self.instance else "")
        if not slug and title:
            base_slug = slugify(title) or "kirayasaathi-blog"
            candidate = base_slug
            count = 1
            qs = BlogPost.objects.filter(slug=candidate)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            while qs.exists():
                candidate = f"{base_slug}-{count}"
                count += 1
                qs = BlogPost.objects.filter(slug=candidate)
                if self.instance:
                    qs = qs.exclude(pk=self.instance.pk)
            attrs["slug"] = candidate
        return attrs
