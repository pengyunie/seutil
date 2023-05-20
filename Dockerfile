FROM texlive/texlive:TL2022-historic
ARG PYTHON_VERSION
WORKDIR /app

RUN apt-get update && apt-get install wget

# install miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh && \
    bash /tmp/miniconda.sh -b -p /opt/miniconda && \
    rm /tmp/miniconda.sh
RUN /opt/miniconda/bin/conda init bash
