FROM  python:3.12.1-bullseye

ARG USER_NAME=python
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN \
    apt-get update && apt-get install -y procps \
        findutils \
        vim \
        sudo \
        jq \
        curl \
        git


RUN /usr/sbin/groupadd --gid ${USER_GID} ${USER_NAME} \
    && /usr/sbin/useradd --uid ${USER_UID} --gid ${USER_GID} --no-log-init --create-home -m ${USER_NAME} -s /usr/bin/bash \
    && /bin/echo ${USER_NAME} ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/${USER_NAME} \
    && chmod 0440 /etc/sudoers.d/${USER_NAME}

USER ${USER_NAME}

WORKDIR /home/${USER_NAME}

RUN curl --remote-name https://bootstrap.pypa.io/get-pip.py
RUN python get-pip.py
RUN pip install poetry

CMD [ "sleep", "infinity" ]
