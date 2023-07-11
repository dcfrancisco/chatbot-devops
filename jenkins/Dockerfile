# Base image
FROM jenkins/jenkins:latest

# Install Jenkins plugins
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli -f /usr/share/jenkins/ref/plugins.txt

USER root

# Add necessary repositories and keys
RUN apt-get update && \
    apt-get install -y wget software-properties-common && \
    wget -qO - https://adoptopenjdk.jfrog.io/adoptopenjdk/api/gpg/key/public | apt-key add - && \
    add-apt-repository --yes https://adoptopenjdk.jfrog.io/adoptopenjdk/deb/
RUN apt-get update

# Install Maven
RUN apt-get install -y maven

# Install JDKs
RUN apt-get install -y openjdk-11-jdk openjdk-17-jdk

# Clean up
RUN apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

USER jenkins
