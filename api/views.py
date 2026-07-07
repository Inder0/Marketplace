from django.utils import timezone
from rest_framework.generics import RetrieveAPIView, get_object_or_404
from .serializers import *
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet,ReadOnlyModelViewSet
from .pagination import ProductPagination
from rest_framework.filters import SearchFilter, OrderingFilter 
from django_filters.rest_framework import DjangoFilterBackend
from marketplace.models import Order, Product, Review
from .permissions import IsOwnerOrReadOnly,IsSellerOrReadOnly
from django.db import models
from django.db.models import Count, Sum, Value, FloatField,Q
from django.db.models.functions import Coalesce,TruncDate
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
import razorpay
from datetime import timedelta

# Create your views here.

class ProductViewSet(ModelViewSet):
    permission_classes = [IsSellerOrReadOnly]
    pagination_class = ProductPagination
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'created_at']
    filterset_fields = ['product_type']

    def get_queryset(self):
        return Product.objects.select_related('seller').prefetch_related('images','reviews__user').annotate(review_count=models.Count('reviews'),
                                                                                                            avg_rating=Coalesce(models.Avg('reviews__rating'), Value(0), output_field=FloatField()),
                                                                                                            total_orders=models.Count('order',filter=models.Q(order__paid=True)),
                                                                                                            total_sales=Coalesce(models.Sum('order__amount',filter=models.Q(order__paid=True)),Value(0),output_field=models.FloatField())) 
    
    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        if self.action == "retrieve":
            return ProductDetailSerializer
        if self.action == "my_products":
            return SellerProductSerializer
        return ProductDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_products(self, request):
        queryset = self.get_queryset().filter(seller=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class ReviewViewSet(ModelViewSet):
    permission_classes = [IsOwnerOrReadOnly]
    serializer_class = ReviewSerializer
    pagination_class = ProductPagination

    def get_queryset(self):
        return Review.objects.select_related('user','product')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrderViewSet(ReadOnlyModelViewSet):
    permission_classes = [IsOwnerOrReadOnly]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related('user','product')

class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data['product']
        amount = int(product.price * 100)

        client = razorpay.Client(auth=(settings.RAZORPAY_ID, settings.RAZORPAY_SECRET))
        razorpay_order = client.order.create({'amount': amount, 'currency': 'INR', 'payment_capture': '1'})

        return Response({
            "product":product.id,
            'razorpay_order_id': razorpay_order['id'],
            'amount': amount,
            "currency": razorpay_order["currency"],
            "razorpay_key": settings.RAZORPAY_ID,
            "product_type": product.product_type,
            },
            status=status.HTTP_201_CREATED)

class PaymentVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PaymentVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        product = data['product']
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')

        client = razorpay.Client(auth=(settings.RAZORPAY_ID, settings.RAZORPAY_SECRET))
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        try:
            client.utility.verify_payment_signature(params_dict)
            if Order.objects.filter(razorpay_payment_id=razorpay_payment_id).exists():
                return Response({"detail": "Payment has already been verified."}, status=status.HTTP_400_BAD_REQUEST)
            Order.objects.create(
                product=product,
                user=request.user,
                amount=product.price,
                razorpay_order_id=data["razorpay_order_id"],
                razorpay_payment_id=data["razorpay_payment_id"],
                paid=True,
                shipping_name=data.get("shipping_name", ""),
                shipping_phone=data.get("shipping_phone", ""),
                shipping_address_line_1=data.get("shipping_address_line_1", ""),
                shipping_address_line_2=data.get("shipping_address_line_2", ""),
                shipping_city=data.get("shipping_city", ""),
                shipping_state=data.get("shipping_state", ""),
                shipping_postal_code=data.get("shipping_postal_code", ""),
                shipping_country=data.get("shipping_country", ""),
            )
            return Response({"success": True, "message": "Payment verified successfully."}, status=status.HTTP_201_CREATED)
        except (razorpay.errors.SignatureVerificationError):
            return Response({"success": False, "error": "Payment verification failed."}, status=status.HTTP_400_BAD_REQUEST)
        

class AnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    
    def get_orders(self):
        return Order.objects.filter(product__seller=self.request.user,paid=True)
    
    def get_lifetime_revenue(self):
        return self.get_orders().aggregate(total=Coalesce(Sum("amount"),0,output_field=FloatField()))["total"]
    
    def get_last_30days_revenue(self):
        return self.get_orders().filter(created_at__gte=timezone.now()-timedelta(days=30)).aggregate(total=Coalesce(Sum("amount"),0,output_field=FloatField()))["total"]
    
    def get_last_7days_revenue(self):
        return self.get_orders().filter(created_at__gte=timezone.now()-timedelta(days=7)).aggregate(total=Coalesce(Sum("amount"),0,output_field=FloatField()))["total"]
    
    
    def get_chart(self):
        start_date=timezone.now().date()-timedelta(days=6)
        chart_data=self.get_orders().filter(created_at__date__gte=start_date).annotate(day=TruncDate
                                                                                ("created_at")).values("day").annotate(total=Sum("amount"))
        revenue_dict={
            item["day"]:float(item["total"]) for item in chart_data
        }
        labels,values=[],[]
        for i in range(7):
            day=start_date+timedelta(days=i)
            labels.append(day.strftime("%a"))
            values.append(revenue_dict.get(day,0))
        return {
            "labels":labels,
            "values":values
        }
    def get_recent_orders(self):
        q= self.get_orders().select_related("user","product").order_by("-created_at")[:10]
        return RecentOrderSerializer(q, many=True).data

    def get_top_selling_products(self):
        return Product.objects.filter(seller=self.request.user).annotate(total_orders=Count("order",filter=Q(order__paid=True)),
                                                                         total_sales=Coalesce(Sum("order__amount",filter=Q(order__paid=True)),Value(0),output_field=FloatField()
                                                                                              )).order_by("-total_sales","-total_orders")[:5]
        
    

    def get(self, request):
        return Response({
            "summary":{
                "lifetime_revenue": self.get_lifetime_revenue(),
                "last_30_days_revenue": self.get_last_30days_revenue(),
                "last_7_days_revenue": self.get_last_7days_revenue(),
                "total_orders": self.get_orders().count(),},
            "chart": self.get_chart(),
            "recent_orders": self.get_recent_orders(),
            "top_selling_products": SellerProductSerializer(self.get_top_selling_products(), many=True).data

        })
    
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    def get(self, request):
        serializer = ProfileSerializer(self.request.user.profile,context={'request': request})
        return Response(serializer.data)
    
    def patch(self, request):
        serializer = ProfileSerializer(self.request.user.profile,data=request.data,partial=True,context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
class PublicProfileView(RetrieveAPIView):
    queryset = Profile.objects.select_related('user')
    serializer_class = PublicProfileSerializer
    

    def get_object(self):
        
        return get_object_or_404(self.queryset, user__username=self.kwargs["username"])
    
class GoogleJWTView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(request.user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })