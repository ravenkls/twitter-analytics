from django.http import HttpResponse
from django.template import loader
from . import twitter


def index(request):
    template = loader.get_template('analyse/index.html')
    return HttpResponse(template.render(request=request))


def search(request):
    template = loader.get_template('analyse/search.html')
    query = request.POST.get("q")
    response = twitter.scrape(query)
    context = {"information": response}
    return HttpResponse(template.render(context=context, request=request))
