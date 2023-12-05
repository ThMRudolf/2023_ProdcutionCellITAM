library(plumber)
library(randomForest)
library(dbplyr)
library(dplyr)
library(RPostgreSQL)

pr <- plumb("app/plumber_methods.R")
pr$run(port=8080, host = "0.0.0.0")

