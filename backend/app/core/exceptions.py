"""
  Custom exceptions and FastAPI exception handlers.
  Handle (Manejo de Errores) | API
    "FastAPI simplifica el manejo de errores mediante manejadores de excepciones personalizados registrados con el decorador @app.exception_handler, permitiendo respuestas JSON consistentes y estructuradas.  Para errores específicos, se pueden crear clases de excepciones personalizadas (heredando de Exception) que facilitan la lógica de negocio y el registro de auditoría, mientras que para errores genéricos se utiliza un manejador global que captura excepciones no previstas y devuelve un código '500' seguro sin filtrar información sensible" 

"""  # noqa: E501
