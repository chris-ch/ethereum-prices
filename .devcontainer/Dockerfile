FROM  python:3.12.1-bullseye

ARG USER_NAME=python
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN \
    apt-get update && apt-get install -y procps \
        lsb-release \
        findutils \
        vim \
        sudo \
        jq \
        curl \
        git

RUN curl https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
RUN echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list
RUN apt update && apt install terraform

RUN /usr/sbin/groupadd --gid ${USER_GID} ${USER_NAME} \
    && /usr/sbin/useradd --uid ${USER_UID} --gid ${USER_GID} --no-log-init --create-home -m ${USER_NAME} -s /usr/bin/bash \
    && /bin/echo ${USER_NAME} ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/${USER_NAME} \
    && chmod 0440 /etc/sudoers.d/${USER_NAME}

USER ${USER_NAME}

WORKDIR /home/${USER_NAME}

RUN curl --remote-name https://bootstrap.pypa.io/get-pip.py
RUN python get-pip.py
RUN pip install poetry

RUN /bin/echo -e "\nexport PATH=$PATH:/home/${USER_NAME}/.local/bin/\n" >> /home/${USER_NAME}/.bashrc

RUN /usr/bin/curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" --output "awscliv2.zip" \
    && unzip awscliv2.zip \
    && sudo ./aws/install --bin-dir /usr/local/bin --install-dir /usr/local/aws-cli --update \
    && rm -fr awscliv2.zip \
    && rm -fr ./aws
    
CMD [ "sleep", "infinity" ]
