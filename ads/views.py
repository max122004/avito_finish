from django.contrib.auth.decorators import login_required
from django.shortcuts import render

import json

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, ListView, CreateView, UpdateView, DeleteView
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ads.models import Category, Ad, Like
from ads.serializer import CategoryListSerializer, AdListSerializer, AdDetailSerializer, LikeSerializer
from authentication.models import User


def root(request):
    return JsonResponse({
        "status": "ok"
    })


class CategoryListView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategoryListSerializer


class CategoryDetailView(DetailView):
    model = Category

    def get(self, request, *args, **kwargs):
        category = self.get_object()

        return JsonResponse({
            "id": category.id,
            "name": category.name,
        })


@login_required
@method_decorator(csrf_exempt, name='dispatch')
class CategoryCreateView(CreateView):
    model = Category
    fields = ["name"]

    def post(self, request, *args, **kwargs):
        category_data = json.loads(request.body)

        category = Category.objects.create(
            name=category_data["name"],
        )

        return JsonResponse({
            "id": category.id,
            "name": category.name,
        })


@method_decorator(csrf_exempt, name='dispatch')
class CategoryUpdateView(UpdateView):
    model = Category
    fields = ["name"]

    def patch(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)

        category_data = json.loads(request.body)
        self.object.name = category_data["name"]

        self.object.save()
        return JsonResponse({
            "id": self.object.id,
            "name": self.object.name
        })


@method_decorator(csrf_exempt, name='dispatch')
class CategoryDeleteView(DeleteView):
    model = Category
    success_url = "/"

    def delete(self, request, *args, **kwargs):
        super().delete(request, *args, **kwargs)

        return JsonResponse({"status": "ok"}, status=200)


class AdListView(ListAPIView):
    queryset = Ad.objects.all()
    serializer_class = AdListSerializer

    def get(self, request, *args, **kwargs):
        categories = request.GET.getlist('cat', [])

        if categories:
            self.queryset = self.queryset.filter(
                category_id__in=categories
            )

        if request.GET.get('text', None):
            self.queryset = self.queryset.filter(
                name__icontains=request.GET.get('text')
            )
        if request.GET.get('location', None):
            locations_q = None
            for location in request.GET.get('location'):
                if locations_q is None:
                    locations_q = Q(author__locations__name__icontains=location)
                else:
                    locations_q |= Q(author__locations__name__icontains=location)
            if locations_q:
                self.queryset = self.queryset.filter(locations_q)

        if request.GET.get('price_to', None):
            self.queryset = self.queryset.filter(
                price__gte=request.GET.get('price_to')
            )

        if request.GET.get('price_from', None):
            self.queryset = self.queryset.filter(
                price__lte=request.GET.get('price_from')
            )

        return super().get(request, *args, **kwargs)


# class AdListView(ListView):
#     models = Ad
#     queryset = Ad.objects.all()
#
#     def get(self, request, *args, **kwargs):
#         super().get(request, *args, **kwargs)
#
#         categories = request.GET.getlist("cat", [])
#         if categories:
#             self.object_list = self.object_list.filter(category_id__in=categories)
#
#         if request.GET.get("text", None):
#             self.object_list = self.object_list.filter(name__icontains=request.GET.get("text"))
#
#         if request.GET.get("location", None):
#             self.object_list = self.object_list.filter(author__locations__name__icontains=request.GET.get("location"))
#
#         if request.GET.get("price_from", None):
#             self.object_list = self.object_list.filter(price__gte=request.GET.get("price_from"))
#
#         if request.GET.get("price_to", None):
#             self.object_list = self.object_list.filter(price__lte=request.GET.get("price_to"))
#
#         self.object_list = self.object_list.select_related('author').order_by("-price")
#         paginator = Paginator(self.object_list, settings.TOTAL_ON_PAGE)
#         page_number = request.GET.get('page')
#         page_obj = paginator.get_page(page_number)
#
#         ads = []
#         for ad in page_obj:
#             ads.append({
#                 "id": ad.id,
#                 "name": ad.name,
#                 "author_id": ad.author_id,
#                 "author": ad.author.first_name,
#                 "price": ad.price,
#                 "description": ad.description,
#                 "is_published": ad.is_published,
#                 "category_id": ad.category_id,
#                 "image": ad.image.url if ad.image else None,
#             })
#
#         response = {
#             "items": ads,
#             "num_pages": page_obj.paginator.num_pages,
#             "total": page_obj.paginator.count,
#         }
#
#         return JsonResponse(response, safe=False)


# class AdDetailView(DetailView):
#     model = Ad
#
#     def get(self, request, *args, **kwargs):
#         ad = self.get_object()
#
#         return JsonResponse({
#             "id": ad.id,
#             "name": ad.name,
#             "author_id": ad.author_id,
#             "author": ad.author.first_name,
#             "price": ad.price,
#             "description": ad.description,
#             "is_published": ad.is_published,
#             "category_id": ad.category_id,
#             "category": ad.category.name,
#             "image": ad.image.url if ad.image else None,
#         })


class AdDetailView(RetrieveAPIView):
    queryset = Ad.objects.all()
    serializer_class = AdDetailSerializer
    permission_classes = [IsAuthenticated]

    def perform_create_like(self, ad):
        # Создаем сериализатор для объекта лайка, используя данные из запроса
        serializer_like = Like(data=self.request.data)
        # Проверяем, что данные валидны
        serializer_like.is_valid(raise_exception=True)
        # Сохраняем лайк, связывая его с пользователем и статьей
        serializer_like.save(user=self.request.user, ad=ad)

    def get(self, request, *args, **kwargs):
        # Вызываем метод get() суперкласса для получения статьи
        response = super().get(request, *args, **kwargs)
        # Получаем объект статьи
        ad = self.get_object()
        # Получаем все лайки, связанные со статьей
        likes = ad.likes.all()
        # Создаем сериализатор для списка лайков
        like_serializer = LikeSerializer(likes, many=True)
        # Получаем данные статьи, используя сериализатор для детального представления
        response_data = self.serializer_class(ad).data
        # Добавляем данные о лайках в объект ответа
        response_data['likes'] = like_serializer.data
        # Возвращаем объект ответа, содержащий данные о статье и ее лайках
        return Response(response_data)


@login_required
@method_decorator(csrf_exempt, name='dispatch')
class AdCreateView(CreateView):
    model = Ad
    fields = ["name", "author", "price", "description", "is_published", "category"]

    def post(self, request, *args, **kwargs):
        ad_data = json.loads(request.body)

        author = get_object_or_404(User, ad_data["author_id"])
        category = get_object_or_404(Category, ad_data["category_id"])

        ad = Ad.objects.create(
            name=ad_data["name"],
            author=author,
            price=ad_data["price"],
            description=ad_data["description"],
            is_published=ad_data["is_published"],
            category=category,
        )

        return JsonResponse({
            "id": ad.id,
            "name": ad.name,
            "author_id": ad.author_id,
            "author": ad.author.first_name,
            "price": ad.price,
            "description": ad.description,
            "is_published": ad.is_published,
            "category_id": ad.category_id,
            "image": ad.image.url if ad.image else None,
        })


@method_decorator(csrf_exempt, name='dispatch')
class AdUpdateView(UpdateView):
    model = Ad
    fields = ["name", "author", "price", "description", "category"]

    def patch(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)

        ad_data = json.loads(request.body)
        self.object.name = ad_data["name"]
        self.object.price = ad_data["price"]
        self.object.description = ad_data["description"]

        self.object.author = get_object_or_404(User, ad_data["author_id"])
        self.object.category = get_object_or_404(Category, ad_data["category_id"])

        self.object.save()
        return JsonResponse({
            "id": self.object.id,
            "name": self.object.name,
            "author_id": self.object.author_id,
            "author": self.object.author.first_name,
            "price": self.object.price,
            "description": self.object.description,
            "is_published": self.object.is_published,
            "category_id": self.object.category_id,
            "image": self.object.image.url if self.object.image else None,
        })


@method_decorator(csrf_exempt, name='dispatch')
class AdUploadImageView(UpdateView):
    model = Ad
    fields = ["image"]

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        self.object.image = request.FILES.get("image", None)
        self.object.save()

        return JsonResponse({
            "id": self.object.id,
            "name": self.object.name,
            "author_id": self.object.author_id,
            "author": self.object.author.first_name,
            "price": self.object.price,
            "description": self.object.description,
            "is_published": self.object.is_published,
            "category_id": self.object.category_id,
            "image": self.object.image.url if self.object.image else None,
        })


@method_decorator(csrf_exempt, name='dispatch')
class AdDeleteView(DeleteView):
    model = Ad
    success_url = "/"

    def delete(self, request, *args, **kwargs):
        super().delete(request, *args, **kwargs)

        return JsonResponse({"status": "ok"}, status=200)


class LikeCreateView(CreateAPIView):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer

    def perform_create(self, serializer):
        ad_id = self.request.data.get('ad')
        ad = Ad.objects.get(id=ad_id)
        serializer.save(
            user=self.request.user,
            ad=ad
        )


class LikedAdAPIView(ListAPIView):
    serializer_class = AdListSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        liked_articles = Ad.objects.filter(likes__user=self.request.user)
        serializer = self.serializer_class(liked_articles, many=True)
        return Response(serializer.data)

