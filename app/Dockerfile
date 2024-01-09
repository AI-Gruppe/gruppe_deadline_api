FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11

COPY ./requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY ./deadlines.py /app/deadlines.py
CMD ["uvicorn", "deadlines:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]