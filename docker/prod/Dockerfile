FROM python:3.10
WORKDIR /local
COPY ./requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
CMD ["sh", "-c", "python3 /local/src/scraper/scrape.py -f mdb-1630"]