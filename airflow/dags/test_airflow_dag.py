from datetime import datetime

from airflow.sdk import dag, task


@dag(
    dag_id="test_airflow",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["wanderwise", "test"],
)
def test_airflow_dag():

    @task
    def create_message():
        print("The first Airflow task is running.")
        return "Airflow works"

    @task
    def print_message(message):
        print(f"Received from the previous task: {message}")

    message = create_message()
    print_message(message)


test_airflow_dag()