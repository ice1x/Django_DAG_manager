import uuid
from graphlib import TopologicalSorter
from copy import deepcopy
from django.db import transaction
from django.db.models import Model, CharField, JSONField, DateTimeField, Manager, ForeignKey, CASCADE
from rest_framework.exceptions import ValidationError


def hex_uuid():
    return uuid.uuid4().hex


def get_serialized_to_dict(dag_uuid: str):
    nodes = Nodes.objects.filter(dag=dag_uuid)
    json_dag = {}
    for node in nodes:
        if not node.successors and not node.predecessors and node.uuid not in json_dag:
            json_dag[node.uuid] = []
        elif node.successors and node.uuid in json_dag and node.uuid not in json_dag[node.uuid]:
            json_dag[node.uuid] += node.successors
        elif node.successors and node.uuid not in json_dag:
            json_dag[node.uuid] = node.successors
    return json_dag


def is_valid_dag(dag_dict: dict[str, list]) -> bool:
    print(f"is_valid_dag: {dag_dict}")
    try:
        TopologicalSorter(dag_dict).prepare()
    except ValueError:
        return False
    return True


class Dags(Model):
    uuid = CharField(primary_key=True, default=hex_uuid, editable=False, max_length=32)
    name = CharField(max_length=255)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        app_label = "dag"
        db_table = "dags"


class NodesManager(Manager):

    def create(self, **kwargs):
        request = deepcopy(kwargs)
        dag_uuid, predecessors, successors = (
            request.get("dag"),
            request.pop("predecessors", ()),
            request.pop("successors", ()),
        )
        with transaction.atomic():
            dag_table = Dags.objects.get(uuid=dag_uuid.hex)
            request["dag"] = dag_table
            instance = super().create(**request)

            predecessor_objects = Nodes.objects.filter(uuid__in=predecessors)
            if predecessor_objects:
                for predecessor in predecessor_objects:
                    edge = Edges.objects.create(node_from=predecessor, node_to=instance)
                    edge.save()

            successors_objects = Nodes.objects.filter(uuid__in=successors)
            if successors_objects:
                for successor in successors_objects:
                    edge = Edges.objects.create(node_from=instance, node_to=successor)
                    edge.save()

            if not is_valid_dag(get_serialized_to_dict(dag_uuid.hex)):
                raise ValidationError("Cycle detected, graph should be DAG.")

        return instance


class Nodes(Model):
    uuid = CharField(primary_key=True, default=hex_uuid, editable=False, max_length=32)
    name = CharField(max_length=255)
    data = JSONField(null=True, blank=True)
    dag = ForeignKey(Dags, on_delete=CASCADE)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    objects = NodesManager()

    class Meta:
        app_label = "dag"
        db_table = "nodes"

    @property
    def predecessors(self):
        return [edge.node_from.uuid for edge in Edges.objects.filter(node_to=self)]

    @property
    def successors(self):
        return [edge.node_to.uuid for edge in Edges.objects.filter(node_from=self)]


class EdgesManager(Manager):

    def create(self, **kwargs):
        request = deepcopy(kwargs)
        with transaction.atomic():
            request["node_from"] = Nodes.objects.get(uuid=request.get("node_from").hex)
            request["node_to"] = Nodes.objects.get(uuid=request.get("node_to").hex)
            instance = super().create(**request)

        return instance


class Edges(Model):
    uuid = CharField(primary_key=True, default=hex_uuid, editable=False, max_length=32)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    node_from = ForeignKey(Nodes, on_delete=CASCADE, related_name="node_from", unique=False)
    node_to = ForeignKey(Nodes, on_delete=CASCADE, related_name="node_to", unique=False)
    objects = EdgesManager()

    class Meta:
        app_label = "dag"
        db_table = "edges"

    @property
    def dag(self):
        if self.node_from.dag != self.node_to.dag:
            raise ValidationError("Edge cannot have different source and destination DAG.")
        return self.node_from.dag

    def save(self, **kwargs) -> None:
        self.validate()
        super().save(**kwargs)

    def validate(self) -> None:
        if self.node_from == self.node_to:
            raise ValidationError("Edge cannot have the same source and destination node.")
        if self.node_from.dag != self.node_to.dag:
            raise ValidationError("Edge cannot have different source and destination DAG.")
        if not is_valid_dag(get_serialized_to_dict(self.node_from.dag)):
            raise ValidationError("Cycle detected, graph should be DAG.")
