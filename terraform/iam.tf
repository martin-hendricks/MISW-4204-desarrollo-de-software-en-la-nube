# Data source para obtener LabRole existente
data "aws_iam_role" "lab_role" {
  name = "LabRole"
}

# IAM Instance Profile para LabRole
resource "aws_iam_instance_profile" "lab_role_profile" {
  name = "LabRole-InstanceProfile"
  role = data.aws_iam_role.lab_role.name

  tags = {
    Name = "LabRole-InstanceProfile"
  }
}

