from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.contrib.sites.shortcuts import get_current_site
from .mixin import LikeCommentMixin, PaginationHandlerMixin, BaseFilterMixin, TagMixin
from .serializers import CommentSerializer, LikeSerializer, CreateBlogSerializer


class CrudViewset(PaginationHandlerMixin, BaseFilterMixin, TagMixin):
    pagination_class    = PageNumberPagination
    def list(self, request):
        queryset = self.search_tag(request, self.filter_queryset(self.model_class.objects.filter(user = request.user) ))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_paginated_response(self.serializer_class(page, many=True).data)
        else:
            serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = self.filter_queryset(self.model_class.objects.filter(user = request.user) )
        blog = get_object_or_404(queryset, pk=pk)
        serializer = self.serializer_class(blog)
        return Response(serializer.data)

    def create(self, request):
        file_uploaded = request.FILES.get('file_uploaded')
        serializer = self.serializer_class(data={
            **{
                "title": request.data["title"],
                "content": request.data["content"],
                "media":file_uploaded,
                "user": request.user.uid,
            }
        })
        serializer.is_valid(raise_exception=True)
        blog = serializer.save()
        self.add_tag(request, blog)
        _data = serializer.data
        absurl = get_current_site(request).domain
        _data["media"] = 'http://' + absurl + _data["media"]
        return Response({
            'status': True,
            'message': 'object creation Successful',
            'data': _data
        })  

    def update(self, request, pk):
        blog = self.model_class.objects.get(uid = pk)
        if(request.data.get("title", []) != []):
            blog.title = request.data.get("title")
        if(request.data.get("content", []) != []):
            blog.content = request.data.get("content")  
        if(request.data.get("tags", []) != []):
            blog.tags.through.objects.filter(blogs_id = pk).delete()
            self.add_tag(request, blog)

        blog.save()
        serializer = self.serializer_class(blog)
        return Response({
            'status': True,
            'message': 'update Successful',
            'data': serializer.data
        })

    def delete(self, request, pk):
        self.model_class.objects.get(uid = pk).delete()
        return Response({
            'status': True,
            'message': 'Delete Successful',
            'data': []
        })

    @action(methods=["GET"],detail=False,url_path="get-blogs/all",url_name="get-all")
    def get_all(self, request, *args, **kwargs):
        queryset = self.model_class.objects.all()  
        queryset = self.filter_queryset(queryset)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)      



class CommentViewset(LikeCommentMixin):
    @action(methods=["POST"],detail=False,url_path="comment/(?P<blog_id>[^/.]+)",url_name="comment")
    def comment(self, request, *args, **kwargs):
        try:
            self.serializer_class = CommentSerializer
            return self.like_comment_function(request.user.uid, "Comment Successful", *args, **kwargs)
        except Exception:
            return Response({"Failed"}, status.HTTP_400_BAD_REQUEST)




class LikeViewset(LikeCommentMixin):
    @action(methods=["GET"],detail=False,url_path="like/(?P<blog_id>[^/.]+)",url_name="like")
    def like(self, request, *args, **kwargs):
        try:
            self.serializer_class = LikeSerializer
            import pdb; pdb.set_trace()
            return self.like_comment_function(request.user.uid, "liked Successful", *args, **kwargs)
        except Exception:
            return Response({"Failed"}, status.HTTP_400_BAD_REQUEST)


