#Dockerfile for building Bitcoin SV
FROM centos:latest
LABEL maintainer=p.foster@nchain.com
RUN yum update -y && yum install -y dnf-plugins-core && dnf update -y 
RUN dnf config-manager -y --set-enabled PowerTools
RUN dnf update -y && dnf install     -y  \
       which            \
       autoconf         \
       boost-devel      \
       gcc-c++          \
       libdb-devel      \
       libdb-cxx-devel  \  
       libdb-cxx        \
       make             \
       libtool          \
       automake         \
       pkgconfig        \
       openssl-devel    \
       libevent-devel   \
       gupnp            \
       git              \
       perl             \
       gzip             \
       zlib-devel       \
       perl-App-cpanminus \
       wget             \
       bzip2-devel      \
       python3 python3-libs python3-devel python3-pip 
       

RUN cpanm Test::More && cpanm PerlIO::gzip && cpanm JSON


COPY ./entrypoint.py .
RUN  chmod +x /entrypoint.py
RUN  useradd -G users jenkins
USER jenkins


