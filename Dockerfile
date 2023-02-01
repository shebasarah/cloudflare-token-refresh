FROM public.ecr.aws/lambda/python:3.9

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["lambda_function.lambda_handler"]
