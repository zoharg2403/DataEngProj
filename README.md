# My Project



## roadmap
1. Call your API on a schedule (using python scripts?)
1. Store raw data in PostgreSQL / DuckDB 
1. Orchestration - Apache Airflow
    - Create a DAG that calls your API every hour
    - Store the raw data in your database
    - Add logging + retry logic
1. Data processing - dbt Core / Apache Spark
    - Create staging -> intermediate -> final models
1. Data modeling - Design a simple warehouse schema:
    - Raw (API dumps) -> Staging (cleaned) -> Mart (business-ready tables)
    - Concepts: Star schema, Slowly changing dimensions, Fact tables 
1. Analytics + Dashboard
1. Containerization - Package everything with Docker:
    - Airflow container
    - dbt container
    - PostgreSQL container
    - API ingestion container
1. Monitoring & Logging
    - Logging - if needed to add
    - Alerts (Airflow email/SMS)
    - Data quality checks (dbt tests)






## Feuture implementation notes
### API ingestion
 - make it resumable

