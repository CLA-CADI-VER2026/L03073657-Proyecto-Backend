-- ============================================
--  Base de datos: tienda_simple
--  Descripción: Base de datos de una tienda
--  con clientes, productos y pedidos.
-- ============================================

USE tienda_simple;

-- --------------------------------------------
-- Tabla 1: clientes
-- --------------------------------------------
CREATE TABLE clientes (
  id_cliente   INT          NOT NULL AUTO_INCREMENT,
  nombre       VARCHAR(100) NOT NULL,
  email        VARCHAR(150) NOT NULL UNIQUE,
  telefono     VARCHAR(20)      NULL,
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_cliente)
);

-- --------------------------------------------
-- Tabla 2: productos
-- --------------------------------------------
CREATE TABLE productos (
  id_producto  INT            NOT NULL AUTO_INCREMENT,
  nombre       VARCHAR(150)   NOT NULL,
  descripcion  TEXT               NULL,
  precio       DECIMAL(10, 2) NOT NULL,
  stock        INT            NOT NULL DEFAULT 0,
  PRIMARY KEY (id_producto)
);

-- --------------------------------------------
-- Tabla 3: pedidos
-- --------------------------------------------
CREATE TABLE pedidos (
  id_pedido    INT            NOT NULL AUTO_INCREMENT,
  id_cliente   INT            NOT NULL,
  id_producto  INT            NOT NULL,
  cantidad     INT            NOT NULL DEFAULT 1,
  total        DECIMAL(10, 2) NOT NULL,
  fecha        DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_pedido),
  CONSTRAINT fk_pedido_cliente
    FOREIGN KEY (id_cliente)  REFERENCES clientes (id_cliente)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_pedido_producto
    FOREIGN KEY (id_producto) REFERENCES productos (id_producto)
    ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ============================================
--  Datos de ejemplo
-- ============================================

INSERT INTO clientes (nombre, email, telefono) VALUES
  ('Ana García',    'ana.garcia@email.com',  '555-1001'),
  ('Luis Pérez',    'luis.perez@email.com',  '555-1002'),
  ('María López',   'maria.lopez@email.com', NULL);

INSERT INTO productos (nombre, descripcion, precio, stock) VALUES
  ('Laptop Pro 15',  'Laptop de alto rendimiento, 16 GB RAM', 1299.99, 10),
  ('Mouse Inalámbrico', 'Mouse ergonómico con receptor USB',    29.99, 50),
  ('Teclado Mecánico',  'Teclado retroiluminado RGB',           89.99, 25);

INSERT INTO pedidos (id_cliente, id_producto, cantidad, total) VALUES
  (1, 1, 1, 1299.99),
  (1, 2, 2,   59.98),
  (2, 3, 1,   89.99),
  (3, 2, 1,   29.99);
