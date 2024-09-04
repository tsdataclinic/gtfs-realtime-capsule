FROM python:3.10
WORKDIR /local
COPY ./requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
CMD ["python3", "src/srcaper/scrape.py", "-f", "mdb-1630"]