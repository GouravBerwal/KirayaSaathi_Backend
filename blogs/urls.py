from django.urls import path
from .views import (
    BlogPostPublicListView,
    BlogPostPublicDetailView,
    BlogPostCategoriesView,
    AdminBlogPostListCreateView,
    AdminBlogPostDetailView,
    AdminBlogImageUploadView,
)

urlpatterns = [
    # Public endpoints
    path("", BlogPostPublicListView.as_view(), name="blog-list"),
    path("categories/", BlogPostCategoriesView.as_view(), name="blog-categories"),
    path("<slug:slug>/", BlogPostPublicDetailView.as_view(), name="blog-detail"),

    # Admin endpoints
    path("admin/manage/", AdminBlogPostListCreateView.as_view(), name="admin-blog-list-create"),
    path("admin/manage/<int:pk>/", AdminBlogPostDetailView.as_view(), name="admin-blog-detail"),
    path("admin/upload-image/", AdminBlogImageUploadView.as_view(), name="admin-blog-upload-image"),
]
