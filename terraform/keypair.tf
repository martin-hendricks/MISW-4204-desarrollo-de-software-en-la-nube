# Generar clave privada
resource "tls_private_key" "clavemac" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# Crear key pair en AWS
resource "aws_key_pair" "clavemac" {
  key_name   = "clavemac"
  public_key = tls_private_key.clavemac.public_key_openssh

  tags = {
    Name = "clavemac"
  }
}

# Guardar clave privada localmente
resource "local_file" "clavemac_private_key" {
  content         = tls_private_key.clavemac.private_key_pem
  filename        = "${path.module}/clavemac.pem"
  file_permission = "0400"
}

