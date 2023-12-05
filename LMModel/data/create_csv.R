library(tidyverse)
library(dbplyr)
library(utils)
# dotenv::load_dot_env(file='.env')
#get data
url <- "https://docs.google.com/spreadsheets/d/11QyMYrydf7UlFXuNT7DjI_s1vF7Jd2erppHEFdwgVuY/export?format=csv"
df <- read.csv(url)
write_csv(df, './data/monitoreo.csv')