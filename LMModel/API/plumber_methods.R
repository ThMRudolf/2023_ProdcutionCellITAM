library(plumber)
library(randomForest)
library(dbplyr)
library(dplyr)
library(RPostgreSQL)

model <- readRDS("modelo_entrenado.rds")
# dotenv::load_dot_env(file='.env')
#* @apiTitle RF API
#* @apiDescription Plumber API for "Monitore de Manufactura"


#* Returns the expected value of the energy for a set of given machining parameters
#* @param tool Tool used
#* @param cutting_depth_ai Cutting depth
#* @param tool_diameter_d Tool diameter
#* @param diameter_ae Diameter ai
#* @param feed_vel_f Feed velocity
#* @param revol_n Revolutions
#* @param num_of_inserts_z Number of inserts
#* @param feet_per_insert_fz Feet per insert
#* @param cut_vel_vc Cutting velocity
#* @param time Time
#* @param distance Distance
#* @post energy
function(tool, cutting_depth_ai, tool_diameter_d, diameter_ae, feed_vel_f, 
         revol_n, num_of_inserts_z, feet_per_insert_fz, cut_vel_vc, 
         time, distance){
  new_data <- data.frame(tool = as.character(tool),
                         cutting_depth_ai = as.numeric(cutting_depth_ai),
                         tool_diameter_d = as.numeric(tool_diameter_d), 
                         diameter_ae = as.numeric(diameter_ae), 
                         feed_vel_f = as.numeric(feed_vel_f), 
                         revol_n = as.numeric(revol_n), 
                         num_of_inserts_z = as.numeric(num_of_inserts_z),
                         feet_per_insert_fz = as.numeric(feet_per_insert_fz),
                         cut_vel_vc = as.numeric(cut_vel_vc),
                         time = as.numeric(time),
                         distance = as.numeric(distance)
  )
  prediction <- predict(model, new_data)
  return(prediction)
}

#* Returns the expected historical energy
#* @get /energy_dist
function(){
  con <- DBI::dbConnect(RPostgreSQL::PostgreSQL(),
                        host = "db", # db as a service in Docker
                        user = Sys.getenv("DB_USER"),
                        password = Sys.getenv("DB_PASSWORD")
  )
  # read DB
  df <- tbl(con, in_schema("public", "monitoreo"))
  energy <- df %>% select(energy) %>% collect() 
  return(energy$energy)
}
