FROM texlive/texlive:TL2022-historic
ARG PYTHON_VERSION

RUN apt-get update && apt-get install wget

# install miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh && \
    bash /tmp/miniconda.sh -b -p /opt/miniconda && \
    rm /tmp/miniconda.sh

# setup Python environment
RUN ./prepare-env.sh ${PYTHON_VERSION} seutil /opt/miniconda/etc/profile.d/conda.sh
