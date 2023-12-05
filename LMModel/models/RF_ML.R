library(RPostgreSQL)
library(dotenv)
library(tidyverse)
library(randomForest)

# Load environment variables from .env file
dotenv::load_dot_env(".env")

# Establish a connection to your Postgres database
con <- DBI::dbConnect(
  RPostgreSQL::PostgreSQL(),
  dbname = Sys.getenv("DB_NAME"),
  host = Sys.getenv("DB_HOST"),
  port = as.integer(Sys.getenv("DB_PORT")),
  user = Sys.getenv("DB_USER"),
  password = Sys.getenv("DB_PASSWORD")
)

# Query to fetch data from the 'monitoreo' table
query <- "SELECT * FROM monitoreo"

# Fetch data from the table
result <- DBI::dbGetQuery(con, query)

# Close the connection
DBI::dbDisconnect(con)

# Guardar el resultado en un archivo CSV
write.csv(result, file = "./resultados.csv", row.names = FALSE)

# Detailed view of data types in the dataframe
result <- result %>%
  select(-filename, -power)
str(result)


# Splitting the data into training and testing sets (70% training, 30% testing)
set.seed(123) # Set seed for reproducibility
n_obs <- nrow(result)
train_indices <- sample(1:n_obs, 0.7 * n_obs, replace = FALSE)
train_data <- result[train_indices, ]
test_data <- result[-train_indices, ]

# Creating a random forest model
rf_model <- randomForest(energy ~ ., data = train_data)

# Predicting on the test set
predictions <- predict(rf_model, test_data)

# Extract actual energy values from the test data
actual_values <- test_data$energy

# Evaluate the model
# (You can use metrics like RMSE, MAE, etc. to evaluate the model's performance)
# Calculate the Mean Squared Error (MSE)
mse <- mean((predictions - actual_values)^2)


# Calculate the Root Mean Squared Error (RMSE)
rmse <- sqrt(mse)

# Display MSE and RMSE
cat("Mean Squared Error (MSE):", mse, "\n")
cat("Root Mean Squared Error (RMSE):", rmse, "\n")

# Create a dataframe with actual and predicted values
evaluation <- data.frame(Actual = actual_values, Predicted = predictions)

# Create a scatter plot
ggplot(evaluation, aes(x = Actual, y = Predicted)) +
  geom_point() +
  geom_abline(intercept = 0, slope = 1, color = "red", linetype = "dashed") +
  labs(x = "Actual Energy", y = "Predicted Energy", title = "Actual vs. Predicted Energy") +
  theme_minimal()

#Save the model to and .rds file
saveRDS(rf_model, file = "modelo_entrenado.rds")
