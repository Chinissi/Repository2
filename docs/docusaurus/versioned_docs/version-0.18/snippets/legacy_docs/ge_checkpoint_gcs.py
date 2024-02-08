# TODO: Delete Me
# This is a temporary workaround for legacy docs which reference a broken snippet.
# The reference fails, and was being silently resolved here, which broke when we
# moved snippets out of tests. This can be deleted once we remove support for 0.15/0/16 docs.

# <snippet name="version-0.18 tests/integration/fixtures/gcp_deployment/ge_checkpoint_gcs.py full">
from datetime import timedelta

import airflow
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "start_date": airflow.utils.dates.days_ago(0),
    "retries": 1,
    "retry_delay": timedelta(days=1),
}

dag = DAG(
    "GX_checkpoint_run",
    default_args=default_args,
    description="running GX checkpoint",
    schedule_interval=None,
    dagrun_timeout=timedelta(minutes=5),
)

# priority_weight has type int in Airflow DB, uses the maximum.
t1 = BashOperator(
    task_id="checkpoint_run",
    bash_command="(cd /home/airflow/gcsfuse/great_expectations/ ; great_expectations checkpoint run gcs_checkpoint ) ",
    dag=dag,
    depends_on_past=False,
    priority_weight=2**31 - 1,
)
# </snippet>
