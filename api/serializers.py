import attrs
from rest_framework import serializers
from marketplace.models import Product,ProductImage,Review,Order
from django.contrib.auth.models import User
from users.models import Profile
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields=['id','username']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']

class ProductListSerializer(serializers.ModelSerializer):
    seller=UserSerializer(read_only=True)
    primary_image=serializers.ReadOnlyField()
    avg_rating=serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields=['id','name','description','price','product_type','seller','primary_image','avg_rating','created_at']


class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Review
        fields ='__all__'
        read_only_fields = ['user', 'created_at','updated_at']

    
    def validate(self, attrs):
        request = self.context.get('request')
        product = attrs.get('product',self.instance.product if self.instance else None)
        queryset = Review.objects.filter(user=request.user, product=product)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("You have already reviewed this product.")
        
        purchased=Order.objects.filter(user=request.user, product=product, paid=True).exists()
        if not purchased:
            raise serializers.ValidationError("You can only review products you have purchased.")
        return attrs

class ProductDetailSerializer(serializers.ModelSerializer):
    seller=UserSerializer(read_only=True)
    images=ProductImageSerializer(many=True,read_only=True)
    reviews=ReviewSerializer(many=True,read_only=True)
    review_count=serializers.ReadOnlyField()
    average_rating=serializers.ReadOnlyField()
    class Meta:
        model = Product
        fields='__all__'
        read_only_fields=['seller','created_at']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'image']

class OrderSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['user', 'razorpay_order_id', 'razorpay_payment_id', 'paid', 'created_at', 'updated_at']

class CheckoutSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    shipping_name = serializers.CharField(required=False)
    shipping_phone = serializers.CharField(required=False)
    shipping_address_line_1 = serializers.CharField(required=False)
    shipping_address_line_2 = serializers.CharField(required=False)
    shipping_city = serializers.CharField(required=False)
    shipping_state = serializers.CharField(required=False)
    shipping_postal_code = serializers.CharField(required=False)
    shipping_country = serializers.CharField(required=False)

    def validate(self, attrs):
        request = self.context['request']
        
        product = attrs.get('product')
        if product.seller == request.user:
            raise serializers.ValidationError("You cannot purchase your own product.")
        if product.product_type == 'physical':
            required_fields = [
                "shipping_name",
                "shipping_phone",
                "shipping_address_line_1",
                "shipping_city",
                "shipping_state",
                "shipping_postal_code",
                "shipping_country",
            ]
            errors = {}

            for field in required_fields:
                if not attrs.get(field):
                    errors[field] = "This field is required."

            if errors:
                raise serializers.ValidationError(errors)
        else:
            if Order.objects.filter(user=request.user, product=product, paid=True).exists():
                raise serializers.ValidationError("You have already purchased this digital product.")        
        return attrs
    
class PaymentVerificationSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(),source='product')
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()
    shipping_name = serializers.CharField(required=False)
    shipping_phone = serializers.CharField(required=False)
    shipping_address_line_1 = serializers.CharField(required=False)
    shipping_address_line_2 = serializers.CharField(required=False)
    shipping_city = serializers.CharField(required=False)
    shipping_state = serializers.CharField(required=False)
    shipping_postal_code = serializers.CharField(required=False)
    shipping_country = serializers.CharField(required=False)

    def validate(self, attrs):
        product = attrs["product"]

        if product.product_type == "physical":

            required_fields = [
                "shipping_name",
                "shipping_phone",
                "shipping_address_line_1",
                "shipping_city",
                "shipping_state",
                "shipping_postal_code",
                "shipping_country",
            ]

            errors = {}
            for field in required_fields:
                if not attrs.get(field):
                    errors[field] = "This field is required."

            if errors:
                raise serializers.ValidationError(errors)
        return attrs
    
class SellerProductSerializer(serializers.ModelSerializer):
    total_orders = serializers.IntegerField(read_only=True)
    total_sales = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    avg_rating = serializers.FloatField(read_only=True)
    primary_image = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price','primary_image', 'product_type', 'total_orders', 'total_sales', 'avg_rating']

class RecentOrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    product = ProductListSerializer(read_only=True)
    class Meta:
        model = Order
        fields = ['id', 'user', 'product', 'amount', 'paid', 'created_at']

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["image","displayname","info","phone_number","address_line_1","address_line_2","city","state","postal_code","country",]

class PublicProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ReadOnlyField()
    class Meta:
        model = Profile
        fields = ["avatar","displayname","info"]