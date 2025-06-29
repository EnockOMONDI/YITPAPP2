from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User, auth


def home(request):
    
    return render(request, 'yitp/index.html')

def web_courses_list(request):
    
    return render(request, 'yitp/web_courses_list.html')

def about(request):
    
    return render(request, 'yitp/about.html')

def team(request):
    
    return render(request, 'yitp/ourteam.html')

def registration(request):
    
    return render(request, 'yitp/registration.html')

def registration2(request):
    
    return render(request, 'yitp/registration2.html')


def events(request):
    
    return render(request, 'yitp/events.html')

def faqs(request):
    
    return render(request, 'yitp/faqs.html')

def contact(request):
    # Add a test message to verify messages framework is working
    if request.method == 'GET':
        messages.info(request, 'Welcome to our contact page! Feel free to reach out to us.')

    return render(request, 'yitp/contact.html')
    

def coursedetail1(request):
    
    return render(request, 'yitp/coursedetail1.html')   

def coursedetail2(request):
    
    return render(request, 'yitp/coursedetail2.html')

def coursedetail3(request):
    
    return render(request, 'yitp/coursedetail3.html')  

def coursedetail4(request):
    
    return render(request, 'yitp/coursedetail4.html')      

def coursedetail5(request):
    
    return render(request, 'yitp/coursedetail5.html')

def coursedetail6(request):
    
    return render(request, 'yitp/coursedetail6.html')