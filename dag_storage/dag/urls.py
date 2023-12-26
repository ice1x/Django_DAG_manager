from django.urls import path, include
from rest_framework import routers

from dag_storage.dag.views import (
    DagViewSet, NodesViewSet, EdgesViewSet, DownloadDagJSONViewSet, DownloadMetadataJSONViewSet
)


router = routers.DefaultRouter()
router.register(r"dags", DagViewSet)
router.register(r"nodes", NodesViewSet)
router.register(r"edges", EdgesViewSet)
router.register(r"download_dag_json", DownloadDagJSONViewSet)
router.register(r"download_metadata_json", DownloadMetadataJSONViewSet)


urlpatterns = [
    path("", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework"))
]
