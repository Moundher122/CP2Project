# Use a base Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install pip dependencies using BuildKit for caching
RUN pip install -r requirements.txt


# Expose the port your app will run on
EXPOSE 8000

# Copy the rest of your application files into the container
COPY . /app/

# Define the command to run your app using gunicorn
CMD ["gunicorn", "ProjectCore.wsgi:application", "--bind", "0.0.0.0:8000"]
