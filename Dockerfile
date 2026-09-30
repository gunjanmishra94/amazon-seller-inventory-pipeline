FROM jupyter/pyspark-notebook:spark-3.5.0

# uv manages Python dependencies for this project (see pyproject.toml / uv.lock).
# The base image bundles Spark's own pyspark source under $SPARK_HOME/python, but
# PYTHONPATH isn't set by default, so a plain `python script.py` can't see it,
# installing pyspark via uv/pip (matched to $SPARK_HOME's Spark version) is what
# actually makes `import pyspark` work.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /tmp/deps
COPY pyproject.toml uv.lock ./
RUN uv export --frozen --no-hashes -o requirements.txt \
    && uv pip install --system --no-cache -r requirements.txt \
    && rm -rf /tmp/deps
