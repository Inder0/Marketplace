from django.shortcuts import redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Product,Order
from django.views.generic import ListView,DetailView,CreateView,UpdateView,DeleteView,TemplateView
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
from .forms import ProductForm
from django.db.models import Count, Sum,Q,Value,DecimalField
from django.db.models.functions import Coalesce,TruncDate
from django.contrib.messages.views import SuccessMessageMixin
from django.template.response import TemplateResponse
# Create your views here.

class HomeView(ListView):
    model=Product
    template_name='marketplace/index.html'
    context_object_name='products'
    
    paginate_by=5

    def get_queryset(self):
        queryset=Product.objects.all()
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
        else:
            context['order']=None
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
        Order.objects.create(
            product=product,
            user=request.user,
            amount=product.price,
            razorpay_order_id=data['razorpay_order_id'],
            razorpay_payment_id=data['razorpay_payment_id'],
            paid=True
        )

        return JsonResponse({
            'success':True
        })
    except Exception as e:
        print(e)
        return JsonResponse({
            'success':False
        })
    

def payment_success(request):
    return render(request,'marketplace/payment_success.html')

def payment_failed(request):
    return render(request,'marketplace/payment_failed.html')

class ProductCreateView(LoginRequiredMixin,SuccessMessageMixin,CreateView):
    model=Product
    form_class=ProductForm
    success_message='Product created successfully'
    template_name='marketplace/create_product.html'
    success_url=reverse_lazy('home')
    
    def form_valid(self, form):
        form.instance.seller = self.request.user
        return super().form_valid(form)

class ProductUpdateView(LoginRequiredMixin,SuccessMessageMixin,UpdateView):
    model=Product
    form_class=ProductForm
    template_name='marketplace/create_product.html'
    success_url=reverse_lazy('home')
    success_message='Product updated successfully'
    extra_context={'update':True}

    def form_valid(self, form):
        if not form.has_changed():
            return redirect('home')
        return super().form_valid(form)
    
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
        return Product.objects.filter(seller=self.request.user).annotate(
            total_orders=Count("order",filter=Q(order__paid=True)),
            total_sales=Coalesce(Sum("order__amount",filter=Q(order__paid=True)),Value(0),output_field=DecimalField(decimal_places=2))
        )
    
class PurchaseView(LoginRequiredMixin,ListView):
    model=Order
    template_name='marketplace/purchases.html'
    context_object_name='orders'

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
    
                                                                                