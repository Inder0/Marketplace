
from django.shortcuts import redirect, render,get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Product,Order,Review
from django.views.generic import FormView, ListView,DetailView,CreateView,UpdateView,DeleteView,TemplateView
from django.conf import settings
from django.utils import timezone
from django.db.models import FloatField
from datetime import timedelta
import razorpay
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import HttpResponse
from django.urls import reverse_lazy
from .forms import CheckoutForm, ProductForm,ReviewForm
from django.db.models import Count, Sum,Q,Value,DecimalField,Avg
from django.db.models.functions import Coalesce,TruncDate
from django.contrib.messages.views import SuccessMessageMixin
from django.template.response import TemplateResponse
from django.contrib import messages
from .formsets import ProductImageFormSet
# Create your views here.

class HomeView(ListView):
    model=Product
    template_name='marketplace/index.html'
    context_object_name='products'
    
    paginate_by=8

    def get_queryset(self):
        queryset=Product.objects.annotate(average_rating=Avg("reviews__rating"),review_count=Count("reviews"))
        query=self.request.GET.get("q")
        if query:
            queryset=queryset.filter(
                Q(name__icontains=query)|
                Q(description__icontains=query)
            )
        sort=self.request.GET.get("sort")
        if sort == "price_low":
            queryset = queryset.order_by("price")
        elif sort == "price_high":
            queryset = queryset.order_by("-price")
        else:
            queryset = queryset.order_by("-id")

        return queryset
    
    def render_to_response(self, context, **response_kwargs):
        if self.request.htmx:
            return TemplateResponse(
                self.request,
                "marketplace/partials/product_grid.html",
                context
            )

        return super().render_to_response(context, **response_kwargs)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            profile = getattr(request.user, 'profile', None)
            if profile and not profile.onboarding_completed:
                return redirect("profile-onboarding")
        return super().dispatch(request, *args, **kwargs)
    
class ProductDetail(DetailView):
    model=Product
    template_name='marketplace/product_detail.html'
    context_object_name='product'
    extra_context={'razorpay_key':settings.RAZORPAY_ID}

    def get_context_data(self, **kwargs):
        context= super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['order']=Order.objects.filter(user=self.request.user,
                                                       product=self.object,
                                                       paid=True).order_by('-created_at').first()
            has_purchased=Order.objects.filter(user=self.request.user,product=self.object,paid=True).exists() or False
            context["has_purchased"] = has_purchased
            if has_purchased:
                review=Review.objects.filter(user=self.request.user,product=self.object).first() or None
                context["user_review"] = review
        else:
            context['order']=None

        
        if self.request.user.is_authenticated:
            context["reviews"] = self.object.reviews.select_related("user").exclude(user=self.request.user)[:10]
        else:
            context["reviews"] = self.object.reviews.select_related("user")[:10]
        context["review_count"] = self.object.reviews.count()
        context["average_rating"] = self.object.reviews.aggregate(Avg("rating"))["rating__avg"]
                                                                  
        return context

@login_required
def create_order(request,pk):
    product=Product.objects.get(pk=pk)
    client=razorpay.Client(auth=(settings.RAZORPAY_ID,settings.RAZORPAY_SECRET))
    order=client.order.create({
        "amount":int(product.price*100),
        "currency":"INR",
        "payment_capture":"1"
    })
    return JsonResponse({
        "order_id":order['id'],
        'amount':order['amount'],
    })

class CheckoutView(LoginRequiredMixin, FormView):
    form_class = CheckoutForm
    template_name = "marketplace/checkout.html"

    def get_initial(self):
        profile = self.request.user.profile

        return {
            "shipping_name": profile.displayname if profile.displayname else self.request.user.username,
            "shipping_phone": profile.phone_number,
            "shipping_address_line_1": profile.address_line_1,
            "shipping_address_line_2": profile.address_line_2,
            "shipping_city": profile.city,
            "shipping_state": profile.state,
            "shipping_postal_code": profile.postal_code,
            "shipping_country": profile.country,
        }
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = get_object_or_404(Product,pk=self.kwargs["pk"])
        context["product"]=product
        return context
    
    def form_valid(self, form):
        self.request.session["checkout"] = form.cleaned_data
        return redirect("checkout-payment",pk=self.kwargs["pk"])
    
    def dispatch(self, request, *args, **kwargs):
        product = get_object_or_404(Product, pk=kwargs["pk"])

        if product.product_type == "digital":
            return redirect("checkout-payment", pk=product.pk)

        self.product = product
        return super().dispatch(request, *args, **kwargs)
    
class CheckoutPaymentView(LoginRequiredMixin, TemplateView):
    template_name = "marketplace/checkout_payment.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["product"] = get_object_or_404(Product,pk=self.kwargs["pk"])
        context["checkout"] = self.request.session.get("checkout")
        context["razorpay_key"] = settings.RAZORPAY_ID

        return context
    

@login_required
@csrf_exempt
def verify_payment(request):
    data=json.loads(request.body)
    client=razorpay.Client(auth=(settings.RAZORPAY_ID,settings.RAZORPAY_SECRET))
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id":data['razorpay_order_id'],
            "razorpay_payment_id":data['razorpay_payment_id'],
            "razorpay_signature": data["razorpay_signature"],

        })
        product=Product.objects.get(pk=data['product_id'])
        checkout = request.session.pop("checkout", None)
        shipping_data = {}

        if checkout:
            shipping_data = {
                "shipping_name": checkout["shipping_name"],
                "shipping_phone": checkout["shipping_phone"],

                "shipping_address_line_1": checkout["shipping_address_line_1"],
                "shipping_address_line_2": checkout["shipping_address_line_2"],

                "shipping_city": checkout["shipping_city"],
                "shipping_state": checkout["shipping_state"],
                "shipping_postal_code": checkout["shipping_postal_code"],
                "shipping_country": checkout["shipping_country"],
            }
        Order.objects.create(
            product=product,
            user=request.user,
            amount=product.price,
            razorpay_order_id=data['razorpay_order_id'],
            razorpay_payment_id=data['razorpay_payment_id'],
            paid=True,
            **shipping_data
        )
        if product.product_type == "digital":
            messages.success(request, "Order placed successfully. You can download your digital product from your purchases.")
        else:
            messages.success(request, "Order placed successfully.The seller will contact you on the registered phone number for Delivery.")
        return JsonResponse({
            'success':True
        })
    except Exception as e:
        return JsonResponse({
            'success':False
        })
    

def payment_success(request):
    return render(request,'marketplace/payment_success.html')

def payment_failed(request):
    return render(request,'marketplace/payment_failed.html')

class ProductCreateView(LoginRequiredMixin,CreateView):
    model=Product
    form_class=ProductForm
    template_name='marketplace/create_product.html'
    success_url=reverse_lazy('home')
    
    def form_valid(self, form):
        context=self.get_context_data()
        image_formset=context['image_formset']
        form.instance.seller = self.request.user
        if image_formset.is_valid():
            self.object=form.save()
            image_formset.instance=self.object
            image_formset.save()
            messages.success(self.request, "Product created successfully.")
            return redirect(self.get_success_url())
            

        return self.render_to_response(self.get_context_data(form=form))
    
    def get_context_data(self, **kwargs):
        context=super().get_context_data(**kwargs)
        if self.request.POST:
            context['image_formset']=ProductImageFormSet(self.request.POST,self.request.FILES)
        else:
            context['image_formset']=ProductImageFormSet()
        return context


class ProductUpdateView(LoginRequiredMixin,UpdateView):
    model=Product
    form_class=ProductForm
    template_name='marketplace/create_product.html'
    success_url=reverse_lazy('home')
    extra_context={'update':True}

    def form_valid(self, form):
        context=self.get_context_data()
        image_formset=context['image_formset']
        if not form.has_changed() and not image_formset.has_changed():
            return redirect('home')
        if image_formset.is_valid():
            self.object=form.save()
            image_formset.instance=self.object
            image_formset.save()
            messages.success(self.request, "Product updated successfully.")
            return redirect(self.get_success_url())
    
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["image_formset"] = ProductImageFormSet(self.request.POST,self.request.FILES,instance=self.object)
        else:
            context["image_formset"] = ProductImageFormSet(instance=self.object)

        return context
        
    def get_queryset(self):
        return Product.objects.filter(seller=self.request.user)

class ProductDeleteView(LoginRequiredMixin,SuccessMessageMixin,DeleteView):
    model=Product
    success_message='Product deleted successfully'
    success_url=reverse_lazy('home')

    def get_queryset(self):
        return Product.objects.filter(seller=self.request.user)

    def form_valid(self, form):
        self.object.delete()
        response=HttpResponse()
        response['HX-Redirect']=self.success_url
        return response


class DashboardView(LoginRequiredMixin,ListView):
    model=Product
    template_name='marketplace/dashboard.html'
    context_object_name='products'
    paginate_by=9

    def get_queryset(self):
        return Product.objects.filter(seller=self.request.user).order_by("-created_at").annotate(
            total_orders=Count("order",filter=Q(order__paid=True)),
            total_sales=Coalesce(Sum("order__amount",filter=Q(order__paid=True)),Value(0),output_field=DecimalField(decimal_places=2))
        )
    
class PurchaseView(LoginRequiredMixin,ListView):
    model=Order
    template_name='marketplace/purchases.html'
    context_object_name='orders'
    paginate_by=9

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related("product", "product__seller").order_by("-created_at")
    
class AnalyticsView(LoginRequiredMixin,TemplateView):
    template_name='marketplace/analytics.html'

    def get_orders(self):
        return Order.objects.filter(product__seller=self.request.user,paid=True)
    
    def get_lifetime_revenue(self):
        return self.get_orders().aggregate(total=Coalesce(Sum("amount"),0,output_field=FloatField()))["total"]
    
    def get_last_30days_revenue(self):
        return self.get_orders().filter(created_at__gte=timezone.now()-timedelta(days=30)).aggregate(total=Coalesce(Sum("amount"),0,output_field=FloatField()))["total"]
    
    def get_last_7days_revenue(self):
        return self.get_orders().filter(created_at__gte=timezone.now()-timedelta(days=7)).aggregate(total=Coalesce(Sum("amount"),0,output_field=FloatField()))["total"]
    
    def get_context_data(self, **kwargs):
        context= super().get_context_data(**kwargs)
        chart=self.get_chart()
        context.update({
            "lifetime_revenue": self.get_lifetime_revenue(),
            "last_30_days_revenue": self.get_last_30days_revenue(),
            "last_7_days_revenue": self.get_last_7days_revenue(),
            "total_orders": self.get_orders().count(),
            "recent_orders":self.get_recent_orders(),
            "top_products":self.get_top_selling_products()
        })
        context.update({
            "chart_labels": json.dumps(chart["labels"]),
            "chart_values": json.dumps(chart["values"]),
        })
        return context
    
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
        return self.get_orders().select_related("user","product").order_by("-created_at")[:10]
    def get_top_selling_products(self):
        return Product.objects.filter(seller=self.request.user).annotate(total_orders=Count("order",filter=Q(order__paid=True)),
                                                                         total_sales=Coalesce(Sum("order__amount",filter=Q(order__paid=True)),Value(0),output_field=FloatField()
                                                                                              )).order_by("-total_sales","-total_orders")[:5]
class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = "marketplace/review_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, pk=self.kwargs["pk"])

        has_purchased = Order.objects.filter(
            user=request.user,
            product=self.product,
            paid=True,
        ).exists()

        already_reviewed = Review.objects.filter(
            user=request.user,
            product=self.product,
        ).exists()

        if not has_purchased or already_reviewed:
            messages.error(self.request,"Cannot review this product now")
            return redirect("home")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.product = self.product

        messages.success(self.request, "Review added successfully.")

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "product-detail",
            kwargs={"pk": self.product.pk},
        )   
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["product"] = self.product
        return context

class ReviewUpdateView(LoginRequiredMixin, UpdateView):
    model = Review
    form_class = ReviewForm
    template_name = "marketplace/review_form.html"

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Review updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "product-detail",
            kwargs={"pk": self.object.product.pk},
        )                                                                  
    
class ReviewDeleteView(LoginRequiredMixin, DeleteView):
    model = Review

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)

    def form_valid(self, form):
        self.object.delete()
        messages.success(self.request, "Review deleted successfully.")
        response=HttpResponse()
        response["HX-Redirect"]=reverse_lazy("product-detail",kwargs={"pk":self.object.product.pk})
        return response
