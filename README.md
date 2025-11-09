# Product Intelligence Data Pipeline

This project is a data engineering pipeline designed to gather product intelligence from various web sources. It uses Apache Airflow to orchestrate the collection of mobile phone specifications from GSMArena and related discussions from Reddit. The entire application is containerized using Docker for easy deployment and scalability.

## Table of Contents

- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Usage](#usage)
- [Configuration](#configuration)

## Architecture

The pipeline is orchestrated by Apache Airflow and consists of two main data gathering components:

1.  **GSMArena Crawler**: A Scrapy spider that crawls `gsmarena.com` to extract detailed specifications for mobile devices.
2.  **Reddit Consumer**: A Python script that uses the PRAW library to connect to the Reddit API and fetch posts and comments from specific subreddits related to mobile phones.

These components are run as tasks within an Airflow DAG, and the entire environment is managed by Docker Compose.

## Tech Stack

-   **Orchestration**: [Apache Airflow](https://airflow.apache.org/)
-   **Web Scraping**: [Scrapy](https://scrapy.org/)
-   **Data Consumption**: Python with [PRAW (Python Reddit API Wrapper)](https://praw.readthedocs.io/en/latest/)
-   **Containerization**: [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/)

## Project Structure

```
.
├── .env                  # Environment variables for configuration
├── docker-compose.yaml   # Docker Compose file to define and run multi-container applications
├── Dockerfile.airflow    # Dockerfile for the Airflow services
├── consumer/             # Contains the Reddit data consumer
│   ├── Dockerfile
│   ├── get_reddit_data.py
│   ├── praw.ini          # Configuration for the PRAW library
│   └── requirements.txt
├── crawler/              # Contains the Scrapy web crawler
│   └── product_intelligence/
│       └── spiders/
│           └── gsmarena_spider.py
├── dags/                 # Airflow DAG definitions
│   └── product_intelligence_dag.py
└── ...
```

-   **`consumer/`**: Houses the logic for fetching data from the Reddit API.
-   **`crawler/`**: Contains the Scrapy project for crawling websites.
-   **`dags/`**: Stores the Airflow DAG files that define the pipeline's workflow.
-   **`docker-compose.yaml`**: The main entry point for starting all services (Airflow webserver, scheduler, worker, and Postgres).
-   **`.env`**: Used to store sensitive information and environment-specific configurations.

## Prerequisites

-   [Docker](https://www.docker.com/get-started)
-   [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)
-   Reddit API Credentials (Client ID, Client Secret, etc.)

## Setup

1.  **Clone the Repository**
    ```bash
    git clone <your-repository-url>
    cd <your-repository-name>
    ```

2.  **Configure Environment Variables**
    Create a `.env` file in the project root. You may need to create this from a template if one is provided. At a minimum, you need to set the Airflow user ID to avoid permission issues with files created in the `dags`, `logs`, and `plugins` directories.
    ```ini
    # .env
    AIRFLOW_UID=50000
    ```

3.  **Configure Reddit API Credentials**
    Update the `consumer/praw.ini` file with your Reddit API credentials.
    ```ini
    # consumer/praw.ini
    [DEFAULT]
    client_id=YOUR_CLIENT_ID
    client_secret=YOUR_CLIENT_SECRET
    user_agent=YOUR_USER_AGENT
    username=YOUR_REDDIT_USERNAME
    password=YOUR_REDDIT_PASSWORD
    ```

4.  **Build and Start the Docker Containers**
    This command will build the images for the services and start them in detached mode.
    ```bash
    docker-compose up --build -d
    ```
    The initial startup might take a few minutes as Airflow needs to initialize its database.

## Usage

1.  **Access the Airflow UI**
    Once the containers are running, you can access the Airflow web UI by navigating to `http://localhost:8080` in your web browser.

2.  **Login**
    The default credentials for Airflow are:
    -   **Username**: `airflow`
    -   **Password**: `airflow`

3.  **Enable and Trigger the DAG**
    -   In the Airflow UI, you will see a DAG named `product_intelligence_pipeline`.
    -   By default, it will be paused. Toggle the switch to unpause/enable it.
    -   To run the pipeline manually, click the "Play" button under the "Actions" column.

## Configuration

-   **Airflow**: The core Airflow configuration is located in `airflow.cfg` (generated upon startup). You can override settings using environment variables in the `docker-compose.yaml` file.
-   **Crawler**: The Scrapy spider settings can be modified in `crawler/product_intelligence/product_intelligence/settings.py`.
-   **Consumer**: The Reddit consumer is configured via `consumer/praw.ini`. You can specify different subreddits or data extraction parameters in `consumer/get_reddit_data.py`.
