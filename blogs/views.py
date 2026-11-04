import os
import uuid
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.db.models import F, Q
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from accounts.authentication import ADMIN_SIGNER_SALT
from .models import BlogPost
from .serializers import (
    BlogPostListSerializer,
    BlogPostDetailSerializer,
    BlogPostAdminSerializer,
)

User = get_user_model()


def verify_admin_token(request) -> bool:
    """Validate X-Admin-Token, Bearer token, X-Auth-Token, or superuser session."""
    if request.user and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return True

    # 1. Dedicated Admin Token
    admin_token = request.headers.get("X-Admin-Token") or request.META.get("HTTP_X_ADMIN_TOKEN")
    if admin_token:
        signer = TimestampSigner(salt=ADMIN_SIGNER_SALT)
        try:
            data = signer.unsign_object(admin_token, max_age=86400 * 7)
            user_id = data.get("user_id")
            user = User.objects.filter(id=user_id, is_active=True).first()
            if user and (user.is_staff or user.is_superuser):
                return True
        except (BadSignature, SignatureExpired):
            pass

    # 2. Main Auth Token (Owner/Superuser from localStorage)
    auth_token = request.headers.get("X-Auth-Token") or request.META.get("HTTP_X_AUTH_TOKEN")
    if not auth_token:
        auth_header = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION")
        if auth_header and auth_header.startswith("Bearer "):
            auth_token = auth_header[7:].strip()

    if auth_token:
        from accounts.authentication import OWNER_SIGNER_SALT
        signer = TimestampSigner(salt=OWNER_SIGNER_SALT)
        try:
            data = signer.unsign_object(auth_token, max_age=86400 * 30)
            user_id = data.get("user_id")
            user = User.objects.filter(id=user_id, is_active=True).first()
            if user and (user.is_staff or user.is_superuser):
                return True
        except (BadSignature, SignatureExpired):
            pass

    return False


# =========================================================================
# PUBLIC BLOG APIS
# =========================================================================

class BlogPostPublicListView(APIView):
    """
    Public listing of published blog posts with category and search filtering.
    GET /api/blogs/
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        qs = BlogPost.objects.filter(is_published=True)

        category = request.query_params.get("category", "").strip()
        if category and category.lower() != "all":
            qs = qs.filter(category__iexact=category)

        search = request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(title__icontains=search)
                | Q(excerpt__icontains=search)
                | Q(content__icontains=search)
                | Q(tags__icontains=search)
            )

        serializer = BlogPostListSerializer(qs, many=True)
        return Response({
            "count": qs.count(),
            "results": serializer.data,
        })


class BlogPostPublicDetailView(APIView):
    """
    Public retrieval of a single published blog post by slug.
    GET /api/blogs/<slug>/
    Automatically increments views_count.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, slug):
        post = BlogPost.objects.filter(slug=slug, is_published=True).first()
        if not post:
            # Check if user is staff/admin previewing a draft/hidden article
            if verify_admin_token(request):
                post = BlogPost.objects.filter(slug=slug).first()

        if not post:
            return Response(
                {"detail": "Blog article not found or has been removed."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Increment view count
        BlogPost.objects.filter(pk=post.pk).update(views_count=F("views_count") + 1)
        post.refresh_from_db()

        serializer = BlogPostDetailSerializer(post)
        return Response(serializer.data)


class BlogPostCategoriesView(APIView):
    """
    List distinct categories with post counts.
    GET /api/blogs/categories/
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        posts = BlogPost.objects.filter(is_published=True)
        categories = {}
        for p in posts:
            categories[p.category] = categories.get(p.category, 0) + 1

        category_list = [{"name": "All", "count": posts.count()}]
        for name, count in sorted(categories.items()):
            category_list.append({"name": name, "count": count})

        return Response(category_list)


# =========================================================================
# ADMIN BLOG APIS
# =========================================================================

class AdminBlogPostListCreateView(APIView):
    """
    Admin listing (including drafts) and creation of blog posts.
    GET /api/admin/blogs/
    POST /api/admin/blogs/
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        if not verify_admin_token(request):
            return Response({"detail": "Admin authorization required."}, status=status.HTTP_401_UNAUTHORIZED)

        qs = BlogPost.objects.all().order_by("-created_at")
        serializer = BlogPostAdminSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not verify_admin_token(request):
            return Response({"detail": "Admin authorization required."}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = BlogPostAdminSerializer(data=request.data)
        if serializer.is_valid():
            post = serializer.save()
            return Response(
                {
                    "detail": "Blog post created successfully!",
                    "blog": BlogPostAdminSerializer(post).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminBlogPostDetailView(APIView):
    """
    Admin retrieve, update, and delete single blog post.
    GET /api/admin/blogs/<id>/
    PUT/PATCH /api/admin/blogs/<id>/
    DELETE /api/admin/blogs/<id>/
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, pk):
        if not verify_admin_token(request):
            return Response({"detail": "Admin authorization required."}, status=status.HTTP_401_UNAUTHORIZED)

        post = BlogPost.objects.filter(pk=pk).first()
        if not post:
            return Response({"detail": "Blog not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(BlogPostAdminSerializer(post).data)

    def put(self, request, pk):
        if not verify_admin_token(request):
            return Response({"detail": "Admin authorization required."}, status=status.HTTP_401_UNAUTHORIZED)

        post = BlogPost.objects.filter(pk=pk).first()
        if not post:
            return Response({"detail": "Blog not found."}, status=status.HTTP_404_NOT_FOUND)

        # Allow direct fast partial update of boolean flags like is_published or is_featured
        if "is_published" in request.data and len(request.data) == 1:
            val = bool(request.data["is_published"])
            post.is_published = val
            post.save(update_fields=["is_published", "updated_at"])
            return Response({
                "detail": "Blog visibility updated successfully!",
                "blog": BlogPostAdminSerializer(post).data,
            })

        if "is_featured" in request.data and len(request.data) == 1:
            val = bool(request.data["is_featured"])
            post.is_featured = val
            post.save(update_fields=["is_featured", "updated_at"])
            return Response({
                "detail": "Blog featured status updated successfully!",
                "blog": BlogPostAdminSerializer(post).data,
            })

        serializer = BlogPostAdminSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()
            return Response({
                "detail": "Blog post updated successfully!",
                "blog": BlogPostAdminSerializer(updated).data,
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        return self.put(request, pk)

    def delete(self, request, pk):
        if not verify_admin_token(request):
            return Response({"detail": "Admin authorization required."}, status=status.HTTP_401_UNAUTHORIZED)

        post = BlogPost.objects.filter(pk=pk).first()
        if not post:
            return Response({"detail": "Blog not found."}, status=status.HTTP_404_NOT_FOUND)

        title = post.title
        post.delete()
        return Response({"detail": f"Blog '{title}' has been deleted successfully."})


class AdminBlogImageUploadView(APIView):
    """
    Upload cover photos or inline images for blog articles.
    POST /api/admin/blogs/upload-image/
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        if not verify_admin_token(request):
            return Response({"detail": "Admin authorization required."}, status=status.HTTP_401_UNAUTHORIZED)

        file_obj = request.FILES.get("image") or request.FILES.get("file")
        if not file_obj:
            return Response({"detail": "No image file provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate file extension
        ext = os.path.splitext(file_obj.name)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp", ".svg"]:
            return Response(
                {"detail": "Invalid image format. Allowed formats: JPG, PNG, WEBP, SVG."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Save to media/blog_images/
        clean_name = f"blog_images/{uuid.uuid4().hex[:12]}_{file_obj.name.replace(' ', '_')}"
        saved_path = default_storage.save(clean_name, file_obj)
        image_url = f"{settings.MEDIA_URL.rstrip('/')}/{saved_path}"

        return Response({
            "detail": "Image uploaded successfully!",
            "url": image_url,
        }, status=status.HTTP_201_CREATED)
