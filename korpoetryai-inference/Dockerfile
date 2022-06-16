FROM public.ecr.aws/lambda/python:3.7

COPY lambda_function.py ${LAMBDA_TASK_ROOT}
COPY model ${LAMBDA_TASK_ROOT}
COPY utils ${LAMBDA_TASK_ROOT}
COPY vocab ${LAMBDA_TASK_ROOT}
COPY checkpoint ${LAMBDA_TASK_ROOT}
COPY generate.py ${LAMBDA_TASK_ROOT}

COPY requirements.txt .
RUN pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

CMD [ "lambda_function.lambda_handler" ]
