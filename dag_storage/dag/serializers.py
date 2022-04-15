from rest_framework import serializers
from action_serializer import ModelActionSerializer
from rest_flex_fields import FlexFieldsModelSerializer
from dag_storage.dag.models import Dags, Nodes, Edges


class DagSerializer(ModelActionSerializer, FlexFieldsModelSerializer):
    uuid = serializers.UUIDField(read_only=True)
    name = serializers.CharField(required=False, allow_blank=True, max_length=255)

    class Meta:
        model = Dags
        fields = "__all__"
        ordering_fields = ("updated_at",)
        action_fields = {
            "create": {"fields": ("name",)},
            "retrieve": {"fields": ("uuid", "name")},
            "list": {"fields": ("uuid", "name")},
            "update": {"fields": ("name",)},
        }

    def create(self, validated_data):
        return Dags.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.save()
        return instance


class NodesSerializer(ModelActionSerializer, FlexFieldsModelSerializer):
    uuid = serializers.UUIDField(read_only=True)
    name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    data = serializers.JSONField(required=False, default={}, allow_null=True)
    dag = serializers.UUIDField()
    predecessors = serializers.ListField(child=serializers.UUIDField(), allow_empty=True)
    successors = serializers.ListField(child=serializers.UUIDField(), allow_empty=True)
    expandable_fields = {"dag": DagSerializer}

    class Meta:
        model = Nodes
        fields = "__all__"
        ordering_fields = ("updated_at",)
        action_fields = {
            "create": {"fields": ("name", "data", "dag", "predecessors", "successors")},
            "retrieve": {"fields": (
                "uuid", "name", "data", "created_at", "updated_at", "dag", "predecessors", "successors"
            )},
            "list": {"fields": (
                "uuid", "name", "data", "created_at", "updated_at", "dag", "predecessors", "successors"
            )},
        }
        expandable_fields = {"dag": DagSerializer}

    def create(self, validated_data):
        return Nodes.objects.create(**validated_data)


class NodesSerializerRet(NodesSerializer):
    dag = DagSerializer()


class NodesSerializerUpdate(NodesSerializer):
    uuid = serializers.UUIDField(read_only=True)
    name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    data = serializers.JSONField(required=False, default={}, allow_null=True)
    dag = serializers.UUIDField(read_only=True)
    predecessors = serializers.ListField(read_only=True, child=serializers.UUIDField(), allow_empty=True)
    successors = serializers.ListField(read_only=True, child=serializers.UUIDField(), allow_empty=True)
    expandable_fields = {"dag": DagSerializer}

    class Meta:
        model = Nodes
        fields = "__all__"
        action_fields = {"update": {"fields": ("name", "data")}}
        expandable_fields = {"dag": DagSerializer}

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.data = validated_data.get("data", instance.data)
        instance.save()
        return instance


class EdgesSerializer(ModelActionSerializer, FlexFieldsModelSerializer):
    uuid = serializers.UUIDField(read_only=True)
    node_from = serializers.UUIDField()
    node_to = serializers.UUIDField()

    class Meta:
        model = Edges
        fields = "__all__"
        ordering_fields = ("updated_at",)
        action_fields = {
            "create": {"fields": (
                "node_from", "node_to"
            )},
            "update": {"fields": (
                "node_from", "node_to"
            )},
            "retrieve": {"fields": (
                "uuid", "created_at", "updated_at", "node_from", "node_to"
            )},
            "list": {"fields": (
                "uuid", "created_at", "updated_at", "node_from", "node_to"
            )},
        }

    def create(self, validated_data):
        return Edges.objects.create(**validated_data)
