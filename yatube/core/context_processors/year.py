from django.utils import timezone


def year(request):
    local_time = timezone.localtime()
    return {'year': local_time.year}
