FROM ubuntu:16.04
MAINTAINER Ryan Parrish <ryan@stickystyle.net>

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y python3 git build-essential libargtable2-dev autoconf \
    libtool-bin ffmpeg libsdl1.2-dev libavutil-dev libavformat-dev libavcodec-dev \
    mkvtoolnix software-properties-common python-pip sudo

RUN add-apt-repository ppa:stebbins/handbrake-releases && \
    apt-get update && \
    apt-get install -y handbrake-cli

RUN useradd -U -d /config -s /bin/false plex && \
    usermod -G users plex && \
    mkdir -p /data && \
    mkdir -p /opt/plexdvr

# Clone Comskip
RUN cd /opt && \
    git clone git://github.com/erikkaashoek/Comskip && \
    cd Comskip && \
    ./autogen.sh && \
    ./configure && \
    make

# Clone PlexComskip
RUN cd /opt && \
    git clone https://github.com/ekim1337/PlexComskip.git && \
    chmod -R 777 /opt/ /tmp/ /root/ && \
    touch /var/log/PlexComskip.log && \
    chmod 777 /var/log/PlexComskip.log

# Cleanup
RUN apt-get -y autoremove && \
    apt-get -y clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp/* && \
    rm -rf /var/tmp/*

ADD plexdvr/setup.sh /opt/setup.sh
ADD plexdvr/requirements.txt /opt/requirements.txt

RUN /opt/setup.sh

RUN pip install --no-cache-dir -r /opt/requirements.txt

VOLUME /data /opt/plexdvr

#ENTRYPOINT ["rq"]
