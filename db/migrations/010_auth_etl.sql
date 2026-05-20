-- ================================================================ ## ================================================================
--  ===== FIFA World Cup Platform ===== 
-- AUTH Refresh Tokens | ETL & Log | Password 
-- RESTRICT: " La cláusula ON DELETE RESTRICT en SQL es una regla de integridad referencial que impide la eliminación de una fila 
--   en una tabla padre si existen filas relacionadas en una tabla hija.  Esta restricción protege la consistencia de los datos al evitar 
--   que se eliminen registros principales mientras sean referenciados por otros registros secundarios".
-- INET: "El tipo de dato INET en bases de datos como PostgreSQL se utiliza para almacenar direcciones de red, específicamente:"
-- DISTINCT: "La cláusula DISTINCT en SQL se utiliza junto con el comando SELECT para eliminar filas duplicadas y devolver únicamente valores únicos 
-- en el conjunto de resultados"
-- uq_token_hash: "Esta parte define una restricción de unicidad (unique constraint) sobre el campo" | "debe ser único en toda la tabla."
-- CASCADE: " CASCADE en el contexto de tablas se refiere a una acción referencial que se define en una restricción de clave 
--    foránea (foreign key).  Su propósito es propagar automáticamente las operaciones de eliminación o actualización desde una 
--    tabla padre a sus filas relacionadas en tablas hijas "
-- TIMESTAMPTZ: "En PostgreSQL es un tipo de dato que almacena fecha y hora con información de zona horaria"
-- ================================================================ ## ================================================================

-- Auth Refresh Token --
CREATE TABLE IF NOT EXISTS public.auth_refresh_tokens(
  token_id      BIGSERIAL     PRIMARY KEY, 
  token_hash    VARCHAR(64)   NOT NULL,
  user_id       UUID          NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE, 
  issued_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  expired_at    TIMESTAMPTZ   NOT NULL,
  revoked_at    TIMESTAMPTZ,
  revoke_reason VARCHAR(50),
  issued_from_ip INET, 
  CONSTRAINT    uq_token_hash UNIQUE (token_hash)
); 

-- Auth Password Reset --


-- ETL Run Log --