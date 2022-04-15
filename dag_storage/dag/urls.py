from django.urls import path, include
from rest_framework import routers

from dag_storage.dag.views import DagViewSet, NodesViewSet, EdgesViewSet, DagDownloadAsJSONViewSet


router = routers.DefaultRouter()
router.register(r"dags", DagViewSet)
router.register(r"nodes", NodesViewSet)
router.register(r"edges", EdgesViewSet)
router.register(r"download_as_json", DagDownloadAsJSONViewSet)


urlpatterns = [
    path("", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework"))
]
