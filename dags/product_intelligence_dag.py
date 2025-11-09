# In dags/product_intelligence_dag.py

from __future__ import annotations
import pendulum
import os
from airflow.models.dag import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount

HOST_PROJECT_PATH = os.environ.get("HOST_PROJECT_PATH")

with DAG(
    dag_id="product_intelligence_pipeline",
    start_date=pendulum.datetime(2025, 8, 7, tz="UTC"),
    schedule=None,
    catchup=False,
    doc_md="""
    ### Product Intelligence Pipeline
    This DAG runs the data collection pipeline.
    """,
) as dag:
    run_gsmarena_crawler = DockerOperator(
        task_id="run_gsmarena_crawler",
        image="product-intelligence-crawler:latest",
        pool="docker_tasks",
        command="scrapy crawl gsmarena",
        docker_url="unix://var/run/docker.sock",
        network_mode="product-net", # Use the simple, predictable name
        auto_remove='success',
        mounts=[
            Mount(
                source=f"{HOST_PROJECT_PATH}/crawler/product_intelligence",
                target="/usr/src/app",
                type="bind"
            )
        ],
    )