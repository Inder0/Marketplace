from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from .models import Product,Order
from django.views.generic import ListView,DetailView,CreateView,UpdateView,DeleteView
from django.conf import settings
import razorpay
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import HttpResponse
from django.urls import reverse_lazy
from .forms import ProductForm
from django.contrib.messages.views import SuccessMessageMixin
# Create your views here.

class HomeView(ListView):
    model=Product
    template_name='marketplace/index.html'
    context_object_name='products'

    
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

class ProductCreateView(SuccessMessageMixin,CreateView):
    model=Product
    form_class=ProductForm
    success_message='Product created successfully'
    template_name='marketplace/create_product.html'
    success_url=reverse_lazy('home')

class ProductUpdateView(SuccessMessageMixin,UpdateView):
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

class ProductDeleteView(SuccessMessageMixin,DeleteView):
    model=Product
    success_message='Product deleted successfully'
    success_url=reverse_lazy('home')

    def form_valid(self, form):
        self.object.delete()
        response=HttpResponse()
        response['HX-Redirect']=self.success_url
        return response


