import json
from django.http import HttpResponse

from rest_framework.decorators import action
from rest_framework import viewsets, status, renderers
from rest_framework.response import Response

from dag_storage.dag.models import Dags, Nodes, Edges, get_serialized_to_dict
from dag_storage.dag.serializers import DagSerializer, NodesSerializer, NodesSerializerRet, EdgesSerializer, NodesSerializerUpdate


UUID = "uuid"


class DagViewSet(viewsets.ModelViewSet):
    queryset = Dags.objects.all()
    serializer_class = DagSerializer
    lookup_url_kwarg = UUID

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"uuid": serializer.instance.uuid, "name": serializer.instance.name},
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        instance = Dags.objects.get(uuid=kwargs.get(self.lookup_url_kwarg))
        serializer = self.get_serializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"uuid": serializer.instance.uuid, "name": serializer.instance.name},
            status=status.HTTP_200_OK,
            headers=headers
        )

    def destroy(self, request, *args, **kwargs):
        uuid = kwargs.get(self.lookup_url_kwarg)
        dag = Dags.objects.filter(uuid=uuid)
        if dag.exists():
            dag.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)


class NodesViewSet(viewsets.ModelViewSet):
    queryset = Nodes.objects.select_related("dag").all()
    serializer_class = NodesSerializer
    lookup_url_kwarg = UUID

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return NodesSerializerRet
        elif self.action in ("update", "partial_update"):
            return NodesSerializerUpdate
        return self.serializer_class

    def update(self, request, *args, **kwargs):
        instance = Nodes.objects.get(uuid=kwargs.get(self.lookup_url_kwarg))
        serializer = self.get_serializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
            headers=headers
        )

    def destroy(self, request, *args, **kwargs):
        uuid = kwargs.get(self.lookup_url_kwarg)
        node = Nodes.objects.filter(uuid=uuid)
        if node.exists():
            node.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)


class EdgesViewSet(viewsets.ModelViewSet):
    queryset = Edges.objects.all()
    serializer_class = EdgesSerializer
    lookup_url_kwarg = UUID

    def destroy(self, request, *args, **kwargs):
        uuid = kwargs.get(self.lookup_url_kwarg)
        edge = Edges.objects.filter(uuid=uuid)
        if edge.exists():
            edge.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)


class DagDownloadAsJSONViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Dags.objects.all()
    serializer_class = DagSerializer

    def retrieve(self, *args, **kwargs):
        instance = self.get_object()
        file_handle = json.dumps(get_serialized_to_dict(instance.uuid))
        response = HttpResponse(file_handle, content_type="application/json")
        response["Content-Length"] = len(response.content)
        response["Content-Disposition"] = f"attachment; filename=\"{instance.name}.json\""
        return response
