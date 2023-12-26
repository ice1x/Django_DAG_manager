import uuid
import django
from django.test import Client
django.setup()

from dag_storage.dag.models import Dags, Nodes, Edges


def test_edge_insert():
    data = {"name": "test_dags_insert"}
    new_dag = Dags.objects.create(**data)
    assert new_dag.name == data["name"]
    new_dag_uuid = uuid.UUID(new_dag.uuid)
    node1 = Nodes.objects.create(name="node1", dag=new_dag_uuid)
    assert node1.name == "node1"

    node2 = Nodes.objects.create(name="node2", dag=new_dag_uuid)
    assert node2.name == "node2"

    edge = Edges.objects.create(node_from=uuid.UUID(node1.uuid), node_to=uuid.UUID(node2.uuid))
    assert edge.node_from == node1
    assert edge.node_to == node2

    new_dag.delete()
    assert Edges.objects.filter(uuid=edge.uuid).exists() is False
    assert Nodes.objects.filter(uuid=node1.uuid).exists() is False
    assert Nodes.objects.filter(uuid=node2.uuid).exists() is False
    assert new_dag.uuid is None


def test_dag_download_as_json():
    c = Client()
    data = {"name": "test_dags_insert"}
    new_dag = Dags.objects.create(**data)
    assert new_dag.name == data["name"]
    new_dag_uuid = uuid.UUID(new_dag.uuid)
    node1 = Nodes.objects.create(name="node1", dag=new_dag_uuid)
    assert node1.name == "node1"
    node2 = Nodes.objects.create(name="node2", dag=new_dag_uuid)
    assert node2.name == "node2"
    edge = Edges.objects.create(node_from=uuid.UUID(node1.uuid), node_to=uuid.UUID(node2.uuid))
    assert edge.node_from == node1
    assert edge.node_to == node2
    response = c.get(f"/download_dag_json/{new_dag.uuid}/")
    assert response.status_code == 200
    assert response.json() == {node1.uuid: [node2.uuid]}
    assert response.headers["Content-Disposition"] == "attachment; filename=\"test_dags_insert_dag.json\""
    new_dag.delete()
    assert Edges.objects.filter(uuid=edge.uuid).exists() is False
    assert Nodes.objects.filter(uuid=node1.uuid).exists() is False
    assert Nodes.objects.filter(uuid=node2.uuid).exists() is False


def test_metadata_download_as_json():
    c = Client()
    data = {"name": "test_dags_insert"}
    new_dag = Dags.objects.create(**data)
    assert new_dag.name == data["name"]
    new_dag_uuid = uuid.UUID(new_dag.uuid)
    node1 = Nodes.objects.create(name="node1", dag=new_dag_uuid, data={"image": "pytorch/pytorch", "version": 1.0})
    assert node1.name == "node1"
    node2 = Nodes.objects.create(
        name="node2", dag=new_dag_uuid, data={"image": "pytorch/pytorch:2.1.2-cuda11.8-cudnn8-devel", "version": 2.1}
    )
    assert node2.name == "node2"
    edge = Edges.objects.create(node_from=uuid.UUID(node1.uuid), node_to=uuid.UUID(node2.uuid))
    assert edge.node_from == node1
    assert edge.node_to == node2
    response = c.get(f"/download_metadata_json/{new_dag.uuid}/")
    assert response.status_code == 200
    result = response.json()
    assert node1.data == {"image": "pytorch/pytorch", "version": 1.0} == result[node1.uuid]
    assert node2.data == {"image": "pytorch/pytorch:2.1.2-cuda11.8-cudnn8-devel", "version": 2.1} == result[node2.uuid]
    assert response.headers["Content-Disposition"] == "attachment; filename=\"test_dags_insert_metadata.json\""
    new_dag.delete()


if __name__ == '__main__':
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dag_storage.dag.settings')
