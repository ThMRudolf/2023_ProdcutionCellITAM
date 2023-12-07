# Parent image
FROM rocker/r-ver

# system libraries of general use
## install debian packages
RUN apt-get update -qq && apt-get -y --no-install-recommends install \
    libxml2-dev \
    libcairo2-dev \
    libsqlite3-dev \
    libmariadbd-dev \
    libpq-dev \
    libssh2-1-dev \
    unixodbc-dev \
    libcurl4-openssl-dev \
    libssl-dev

## update system libraries
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get clean

# install renv & restore packages
#RUN Rscript -e 'install.packages("renv")'
#RUN Rscript -e 'renv::restore()'
RUN R -e 'install.packages("tidyverse")'
RUN R -e 'install.packages("plumber")'
RUN R -e 'install.packages("randomForest")'
RUN R -e 'install.packages("dplyr")'
RUN R -e 'install.packages("dbplyr")'
RUN R -e 'install.packages("RPostgreSQL")'

# Copy the current directory contents into the container at /usr/local/src/app
COPY . /app
# port
EXPOSE 8080
# Run plumber
CMD ["Rscript", "/app/plumber.R"]