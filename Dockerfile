FROM python:2.7
MAINTAINER mrsixw

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /usr/src/app
ENV FLASK_APP=net_rm.py
WORKDIR /usr/src/app
RUN flask initdb
EXPOSE 5000
ENTRYPOINT ["flask"]
CMD ["run","--host=0.0.0.0"]
