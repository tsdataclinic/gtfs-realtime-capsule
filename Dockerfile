FROM python:3.10
WORKDIR /local
COPY ./requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
CMD ["tail", "-f", "/dev/null"]