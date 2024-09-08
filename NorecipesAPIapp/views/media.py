import os
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, Http404
from django.conf import settings
from rest_framework.views import APIView


class ServeStaticView(APIView):
    def get(self, _, path):        
        full_path = os.path.abspath(os.path.join(settings.MEDIA_ROOT, path))
        media_full_path = os.path.abspath(settings.MEDIA_ROOT)
        if not full_path.startswith(media_full_path):
            raise PermissionDenied()
        if os.path.exists(full_path):
            with open(full_path, 'rb') as file:
                response = HttpResponse(file.read(), content_type="application/octet-stream")
                response['Content-Disposition'] = f'inline; filename={os.path.basename(full_path)}'
                return response
        else:
            raise Http404()
