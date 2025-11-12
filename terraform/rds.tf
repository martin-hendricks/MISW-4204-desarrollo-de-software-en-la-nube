# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "anb-db-subnet-group"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]

  tags = {
    Name = "anb-db-subnet-group"
  }
}

# RDS PostgreSQL Instance
resource "aws_db_instance" "main" {
  identifier             = "anb-database"
  engine                 = "postgres"
  engine_version         = "15.4"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  storage_type           = "gp3"
  storage_encrypted      = false
  db_name                = "anbdb"
  username               = "postgres"
  password               = var.rds_password
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false
  skip_final_snapshot    = true
  backup_retention_period = 0

  tags = {
    Name = "anb-database"
  }
}

# Null resource para inicializar la base de datos con init.sql
resource "null_resource" "rds_init" {
  depends_on = [aws_db_instance.main]

  provisioner "local-exec" {
    command = <<-EOT
      # Esperar a que RDS esté disponible
      echo "Esperando a que RDS esté disponible..."
      until PGPASSWORD='${var.rds_password}' psql -h ${aws_db_instance.main.address} -p ${aws_db_instance.main.port} -U postgres -d anbdb -c '\q' 2>/dev/null; do
        echo "Esperando conexión a RDS..."
        sleep 10
      done
      
      # Ejecutar init.sql
      echo "Inicializando base de datos con init.sql..."
      PGPASSWORD='${var.rds_password}' psql -h ${aws_db_instance.main.address} -p ${aws_db_instance.main.port} -U postgres -d anbdb -f ${path.module}/../source/database/init.sql
      
      if [ $? -eq 0 ]; then
        echo "Base de datos inicializada exitosamente"
      else
        echo "Error al inicializar la base de datos"
        exit 1
      fi
    EOT
  }

  triggers = {
    rds_endpoint = aws_db_instance.main.endpoint
    init_sql     = filemd5("${path.module}/../source/database/init.sql")
  }
}

