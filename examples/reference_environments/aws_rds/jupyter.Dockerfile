FROM jupyter/minimal-notebook:python-3.10

WORKDIR /gx

COPY ./aws_rds_example.ipynb ./
COPY ./aws_rds_example_rds_stores.ipynb ./

RUN pip install 'great_expectations[s3, postgresql]'
