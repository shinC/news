# Development/Production Dockerfile
FROM python:3.14-slim

# Prevent Python from writing pyc files and keep stdout unbuffered
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install essential system packages
# ca-certificates and tzdata are important for network connections and time
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    procps \
    ca-certificates \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set timezone (Korea)
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set Working Directory
WORKDIR /workspaces/news

# Create a non-root user 'tripod'
ARG USERNAME=tripod
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m -s /bin/bash $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Configure custom terminal prompt (PS1)
RUN echo "parse_git_branch() { git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/ (\1)/'; }" >> /home/$USERNAME/.bashrc \
    && echo 'export PS1="\[\\033[01;32m\]\u\[\\033[00m\] ➜ \[\\033[01;34m\]\\w\[\\033[00m\]\[\\033[01;32m\]\$(parse_git_branch)\[\\033[00m\] \$ "' >> /home/$USERNAME/.bashrc

# (Production) Copy requirements and install
COPY requirements.txt /workspaces/news/
RUN pip install --no-cache-dir -r requirements.txt

# (Production) Copy source code
# COPY . /workspaces/news/

# CMD for production would go here. 
# For dev container, docker-compose will override this with `sleep infinity`
CMD ["python", "-m", "http.server", "8000"]
