CREATE DATABASE IF NOT EXISTS directorio;
USE directorio;

CREATE TABLE materias (
  id       INT AUTO_INCREMENT PRIMARY KEY,
  clave    VARCHAR(20) UNIQUE NOT NULL,
  nombre   VARCHAR(100) NOT NULL,
  creditos INT
);

CREATE TABLE docentes (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  nombre     VARCHAR(100) NOT NULL,
  email      VARCHAR(100) UNIQUE NOT NULL,
  materia_id INT,
  FOREIGN KEY (materia_id) REFERENCES materias(id)
);

-- Datos iniciales
INSERT INTO materias (clave, nombre, creditos) VALUES
  ('TC1028', 'Programación en Python', 5),
  ('TC1004B', 'Implementación de IoT', 4),
  ('TC2005B', 'Construcción de Software', 5);
