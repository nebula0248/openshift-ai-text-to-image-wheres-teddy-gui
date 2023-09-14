FROM registry.access.redhat.com/ubi8/nodejs-16:latest as build-step

WORKDIR /projects
ENV PATH /projects/node_modules/.bin:$PATH
COPY --chown=default:root ./frontend/* ./
COPY --chown=default:root ./frontend/src ./src
COPY --chown=default:root ./frontend/stories ./stories
COPY --chown=default:root ./frontend/.storybook .storybook
COPY --chown=default:root ./frontend/__mocks__ ./__mocks__
RUN npm install
RUN npm run build

FROM registry.access.redhat.com/ubi9/python-39:1-108
WORKDIR /projects
#RUN mkdir -p frontend
COPY --from=build-step /projects/dist ./frontend/dist

# By default, listen on port 8081
EXPOSE 8081/tcp
ENV FLASK_PORT=8081

# Set the working directory in the container
#WORKDIR /projects

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies
RUN pip install -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY . .

# Specify the command to run on container start
CMD ["gunicorn","--config", "python:gunicorn_config", "app:app"]
