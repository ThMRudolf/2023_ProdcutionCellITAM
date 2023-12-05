library(shiny)
library(httr)

# Specify the application port
# options(shiny.host = "0.0.0.0")
# options(shiny.port = 6789)

# Define la UI de la aplicación Shiny
ui <- fluidPage(
  titlePanel("Energy Predictor"),
  sidebarLayout(
    sidebarPanel(
      # Entradas para los parámetros de predicción
      selectInput("tool", "Tool Used", choices = c("wsp1030", "wsp4240")),
      sliderInput("cutting_depth_ai", "Cutting Depth (in m)", min = 0.0007, max = 0.003, value = 0.001, step = 0.0001),
      selectInput("tool_diameter_d", "Tool Diameter (in m)", choices = c("0.04", "0.05")),
      sliderInput("diameter_ae", "Diameter (effective cutting diameter in m)", min = 0.026, max = 0.04, value = 0.032, step = 0.002),
      selectInput("feed_vel_f", "Feed Velocity (in m/s)", choices = c(30.336, 30.3552, 45.5328, 25.296, 0.0158166666666667, 63.24, 37.92, 41.7384, 34.1496, 37.944, 45.504, 41.712, 34.128)),
      selectInput("revol_n", "Revs", choices = c(28.1066666666667, 35.1333333333333, 33.8204254070278, 33.8166666666667, 2108.0, 31.62, 42.16, 38.6466666666667, 35.8166666666667, 35.5)),
      selectInput("num_of_inserts_z", "Num. of Inserts", choices = c(2, 3)),
      selectInput("feet_per_insert_fz", "Feet per Insert (in m)", choices = c(0.0001798861480075, 0.0001323406235458, 0.0001199240986717, 0.000171315919172, 0.0001349146110056, 0.0001557244358485, 0.00015, 0.0001631924882629, 0.0001, 0.00025, 0.0001499051233396)),
      selectInput("cut_vel_vc", "Cutting Velocity", choices = c(15300.0, 14304.5509977373, 16203.0782701547, 17483.3401083456, 0.265, 19072.7346636498, 15298.2995859209, 16059.821645151, 12715.1564424332, 15893.9455530415)),
      sliderInput("time", "Time (in s)", min = 6.432, max = 23.718, value = 15.104, step = 0.001),
      sliderInput("distance", "distance (in m)", min = 0.0001, max = 572.74368, value = 543.92448, step = 0.01),
      # Agrega más entradas según los parámetros necesarios
      actionButton("predictButton", "Predict")
    ),
    mainPanel(
      h1("Manufactura"),
      # Resultado de la predicción
      h3("predicción"),
      verbatimTextOutput("prediction"),
      # gráfica
      h3("Energía"),
      plotOutput("distPlot")
    )
  )
)

# Define el servidor
server <- function(input, output) {
  # gráfica
  output$distPlot <- renderPlot({
    response <- GET('http://web:8080/energy_dist', encode = "json") # web as a service in docker
    data <- unlist(content(response,"parsed"))
    # draw the histogram with the specified number of bins
    hist(data, breaks = 30, col = 'darkgray', border = 'white',
          main = 'Energy Dist')

    })


  observeEvent(input$predictButton, {
    # Crear el cuerpo de la solicitud con los datos ingresados por el usuario
    req_body <- list(
      tool = input$tool,
      cutting_depth_ai = input$cutting_depth_ai,
      tool_diameter_d = input$tool_diameter_d,
      diameter_ae = input$diameter_ae,
      feed_vel_f = input$feed_vel_f,
      revol_n = input$revol_n,
      num_of_inserts_z = input$num_of_inserts_z,
      feet_per_insert_fz = input$feet_per_insert_fz,
      cut_vel_vc = input$cut_vel_vc,
      time = input$time,
      distance = input$distance
      # Agrega más parámetros según corresponda
    )
    
    # Realizar la solicitud POST a la API Plumber
    response <- POST("http://web:8080/energy", body = req_body, encode = "json")
    
    # Obtener y mostrar la respuesta
    if (http_status(response)$category == "Success") {
      output$prediction <- renderText({
        content(response, "text")
      })
    } else {
      output$prediction <- renderText({
        "Error en la solicitud."
      })
    }
  })
}

# Ejecutar la aplicación Shiny
shinyApp(ui = ui, server = server)

