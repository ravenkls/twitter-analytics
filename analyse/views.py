from django.http import HttpResponse
from django.template import loader
from . import twitter


def index(request):
    template = loader.get_template('analyse/index.html')
    return HttpResponse(template.render(request=request))


def search(request, query):
    template = loader.get_template('analyse/search.html')
    print("test")
    response = twitter.scrape(query)
    print("Test")
    context = {"information": response}
    return HttpResponse(template.render(context=context, request=request))
