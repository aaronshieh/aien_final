from django.shortcuts import render
from django.http import HttpResponse
from opencvkeras import classify

# Create your views here.
def security(request):
    #classify.run()

    return render(request,"./security/security.html")

def run(request):
    classify.run()

    return render(request, './website/voicebot.html')