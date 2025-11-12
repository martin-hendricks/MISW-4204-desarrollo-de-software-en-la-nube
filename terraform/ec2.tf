# Data source para obtener la AMI de Ubuntu 22.04 LTS
data "aws_ami" "ubuntu_ec2" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Instancia Performance
resource "aws_instance" "performance" {
  ami                    = data.aws_ami.ubuntu_ec2.id
  instance_type          = "t3.small"
  key_name               = aws_key_pair.clavemac.key_name
  subnet_id              = aws_subnet.public_1.id
  vpc_security_group_ids = [aws_security_group.performance.id]

  iam_instance_profile = aws_iam_instance_profile.lab_role_profile.name

  tags = {
    Name = "performance"
  }
}

# Instancia Worker
resource "aws_instance" "worker" {
  ami                    = data.aws_ami.ubuntu_ec2.id
  instance_type          = "t3.small"
  key_name               = aws_key_pair.clavemac.key_name
  subnet_id              = aws_subnet.public_2.id
  vpc_security_group_ids = [aws_security_group.worker.id]

  iam_instance_profile = aws_iam_instance_profile.lab_role_profile.name

  tags = {
    Name = "worker"
  }
}

