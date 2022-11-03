FROM python:3.10-slim-buster

WORKDIR /app

RUN apt-get update && apt-get install -y git

RUN git clone https://github.com/benoitberanger/nifti2database.git

RUN pip install -e /app/nifti2database

CMD [ "python", "-m" , "flask", "--app", "nifti2database.api.main", "--debug", "run", "--host=0.0.0.0" ]
