# Data source para obtener la AMI de Ubuntu 22.04 LTS
data "aws_ami" "ubuntu" {
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

# Launch Template
resource "aws_launch_template" "backend" {
  name_prefix   = "anb-backend-"
  image_id      = data.aws_ami.ubuntu.id
  instance_type = "t3.small"
  key_name      = aws_key_pair.clavemac.key_name

  vpc_security_group_ids = [aws_security_group.backend.id]

  iam_instance_profile {
    name = aws_iam_instance_profile.lab_role_profile.name
  }

  user_data = base64encode(<<-EOF
    #!/bin/bash
    # Placeholder - se actualizará manualmente
    echo "Backend instance initialized"
  EOF
  )

  tag_specifications {
    resource_type = "instance"

    tags = {
      Name = "backend"
    }
  }

  tags = {
    Name = "anb-backend-lt"
  }
}

# Auto Scaling Group
resource "aws_autoscaling_group" "backend" {
  name                = "anb-backend-asg"
  vpc_zone_identifier = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  target_group_arns   = [aws_lb_target_group.backend.arn]
  health_check_type   = "ELB"
  health_check_grace_period = 300

  min_size         = 1
  max_size         = 3
  desired_capacity = 1

  launch_template {
    id      = aws_launch_template.backend.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "backend"
    propagate_at_launch = true
  }

  tag {
    key                 = "Component"
    value               = "backend"
    propagate_at_launch = true
  }
}

# Política de escalado basada en RequestCountPerTarget
resource "aws_autoscaling_policy" "request_count" {
  name                   = "anb-backend-request-count-policy"
  autoscaling_group_name = aws_autoscaling_group.backend.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ALBRequestCountPerTarget"
      resource_label          = "app/${aws_lb.main.name}/${aws_lb.main.arn_suffix}/targetgroup/${aws_lb_target_group.backend.name}/${aws_lb_target_group.backend.arn_suffix}"
    }
    target_value = 40.0
  }
}

# Política de escalado basada en CPU
resource "aws_autoscaling_policy" "cpu" {
  name                   = "anb-backend-cpu-policy"
  autoscaling_group_name = aws_autoscaling_group.backend.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 50.0
  }
}

