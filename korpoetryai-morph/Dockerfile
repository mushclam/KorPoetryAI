FROM public.ecr.aws/lambda/python:3.7

COPY lambda_function.py ${LAMBDA_TASK_ROOT}

RUN yum install -y gcc-c++ java-1.8.0-openjdk-devel python3-devel make diffutils
COPY requirements.txt .
RUN pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

RUN yum install -y curl git automake
COPY ldconfig /usr/local/bin
RUN curl -s https://raw.githubusercontent.com/konlpy/konlpy/master/scripts/mecab.sh > mecab.sh
RUN bash mecab.sh

CMD [ "lambda_function.lambda_handler" ]
