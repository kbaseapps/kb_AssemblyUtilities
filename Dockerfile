FROM kbase/sdkbase2:python
MAINTAINER KBase Developer
# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.


# needed for python3 base image
RUN apt-get update && apt-get install -y wget gcc

# needed for certs to work
RUN apt-get upgrade -y
RUN sed -i 's/\(.*DST_Root_CA_X3.crt\)/!\1/' /etc/ca-certificates.conf
RUN update-ca-certificates


# add SAMTools (don't need yet)
#RUN apt-get update && apt-get install -y samtools

# -----------------------------------------

COPY ./ /kb/module
RUN mkdir -p /kb/module/work
RUN chmod -R a+rw /kb/module

WORKDIR /kb/module
RUN make all

# install BBTools
RUN BBMAP_VERSION=$(cat /kb/module/bbmap_version) \
    && BBMAP=BBMap_$BBMAP_VERSION.tar.gz \
    && wget -O $BBMAP https://sourceforge.net/projects/bbmap/files/$BBMAP/download \
    && tar -xf $BBMAP \
    && rm $BBMAP
#RUN BBMAP_VERSION=$(cat /kb/module/bbmap_version) \
#    && BBMAP=BBMap_$BBMAP_VERSION.tar.gz \
#    && tar -xf $BBMAP

# build BBTools small C-lib
RUN cd /kb/module/bbmap/jni \
    && make -f makefile.linux


ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
